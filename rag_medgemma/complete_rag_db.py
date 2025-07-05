import os
import requests
import datetime
import json
import tempfile
import re
import hashlib

from google.cloud import storage

import fitz  # PyMuPDF: pip install PyMuPDF
import xml.etree.ElementTree as ET
from google.cloud import storage, aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content


# ───── CONFIG ────────────────────────────────────────────────────────────────
# Fill these in or set as environment variables
GCP_PROJECT    = os.environ.get("GCP_PROJECT", "gemma-hcls25par-722")
GCP_BUCKET     = os.environ.get("GCP_BUCKET", "medgemma_rag_db")
REGION         = os.environ.get("GCP_REGION", "europe-west1")
UNPAYWALL_EMAIL = "medevstar7221@gcplab.me"
GEMINI_MODEL_ID = "gemini-2.5-pro"



# Vertex AI models
GEMINI_MODEL   = "models/text-bison@001"       # for chunking
# (you could also fine-tune a Gemini variant)
# ──────────────────────────────────────────────────────────────────────────────

def last_week_dates():
    """Return strings YYYY/MM/DD for a week-ago and today."""
    today    = datetime.date.today()
    week_ago = today - datetime.timedelta(days=366)
    return week_ago.strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d")

# ───── STEP 1: QUERY PUBMED ───────────────────────────────────────────────────
def query_pubmed(query, start_date, end_date):
    """
    Search PubMed for 'query' between start_date and end_date,
    then fetch titles, abstracts, DOIs.
    """
    # 1a) Get list of PubMed IDs
    esearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params  = {
        "db": "pubmed", "term": query,
        "mindate": start_date, "maxdate": end_date,
        "datetype": "pdat", "retmode": "json", "retmax": 200
    }
    ids = requests.get(esearch, params=params).json()["esearchresult"].get("idlist", [])
    if not ids:
        return []

    # 1b) Fetch article details in XML
    efetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    resp   = requests.get(efetch, params={"db":"pubmed","id":",".join(ids),"retmode":"xml"})
    import xml.etree.ElementTree as ET
    root = ET.fromstring(resp.content)

    articles = []
    for art in root.findall(".//PubmedArticle"):
        title   = art.findtext(".//ArticleTitle")
        abstract= art.findtext(".//AbstractText")
        doi     = None
        for el in art.findall(".//ArticleId"):
            if el.attrib.get("IdType")=="doi":
                doi = el.text
        articles.append({
            "title": title,
            "abstract": abstract,
            "doi": doi,
            "source": "PubMed"
        })
    return articles

# ───── STEP 2: QUERY medRxiv ──────────────────────────────────────────────────
def query_medrxiv(query, start_date, end_date):
    """
    Query medRxiv for papers between dates (YYYY-MM-DD),
    filter those matching 'query' in title/abstract.
    """
    url  = f"https://api.biorxiv.org/details/medrxiv/{start_date}/{end_date}/0"
    resp = requests.get(url).json()
    out  = []
    for item in resp.get("collection", []):
        txt = (item.get("title","")+" "+item.get("abstract","")).lower()
        if query.lower() in txt:
            out.append({
                "title": item.get("title"),
                "abstract": item.get("abstract"),
                "doi": item.get("doi"),
                "source": "medRxiv",
                "url":  item.get("rel_link")
            })
    return out

# ───── STEP 3: RESOLVE PDF LINK ────────────────────────────────────────────────
def get_pdf_link(doi):
    """Use Unpaywall API to find a free PDF link for the DOI."""
    if not doi:
        return None
    url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": UNPAYWALL_EMAIL}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        # print(r.status_code, r.text)
        return None
    data = r.json().get("best_oa_location", {})
    if not data:
        return None
    return data.get("url_for_pdf")

# ───── STEP 4: DOWNLOAD & EXTRACT TEXT ────────────────────────────────────────

def extract_from_epmc(doi: str) -> str:
    """
    Try to pull full text XML from Europe PMC given a DOI.
    If successful, strips XML tags and returns plain text.
    """
    # 1) Search by DOI
    search_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": f"DOI:{doi}",
        "format": "json",
        "resultType": "core",
        "pageSize": 1
    }
    r = requests.get(search_url, params=params, timeout=30)
    if r.status_code != 200:
        print(f"EuropePMC search failed: {r.status_code}")
        return ""
    results = r.json().get("resultList", {}).get("result", [])
    if not results:
        print("No EuropePMC record for DOI.")
        return ""

    pmcid = results[0].get("pmcid")
    if not pmcid:
        print("Record has no PMCID.")
        return ""

    # 2) Fetch full-text XML
    xml_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    r2 = requests.get(xml_url, timeout=30)
    if r2.status_code != 200:
        print(f"Failed to fetch fullTextXML: {r2.status_code}")
        return ""

    # 3) Strip XML tags
    try:
        root = ET.fromstring(r2.content)
        # Collect all text nodes
        text = "".join(root.itertext())
        return text
    except ET.ParseError:
        print("Error parsing EuropePMC XML.")
        return ""

def download_and_extract(pdf_url: str, doi: str = None, abstract: str = "") -> str:
    """
    Download a PDF, extract text via PyMuPDF, falling back to Europe PMC or abstract.
    - Sends a browser-like User-Agent + Referer.
    - If PDF download is blocked (403), attempts Europe PMC.
    - If that fails, returns the abstract.
    """
    # --- Attempt direct PDF download ---
    if pdf_url:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            ),
            "Referer": f"https://doi.org/{doi}" if doi else pdf_url
        }
        try:
            print(f"Fetching PDF → {pdf_url}")
            resp = requests.get(pdf_url, headers=headers, timeout=60, allow_redirects=True)
            print(f"  → status code: {resp.status_code}")
            if resp.status_code == 200:
                # Save and extract
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp_path = tmp.name
                text = ""
                try:
                    doc = fitz.open(tmp_path)
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                except Exception as e:
                    print(f"Error extracting PDF text: {e}")
                finally:
                    os.remove(tmp_path)
                return text
            else:
                print(f"PDF download blocked ({resp.status_code}), falling back.")
        except Exception as e:
            print(f"Exception downloading PDF: {e}")

    # --- Fallback to Europe PMC full text ---
    if doi:
        print("Trying Europe PMC full-text XML…")
        epmc_text = extract_from_epmc(doi)
        if epmc_text:
            return epmc_text

    # --- Final fallback: abstract only ---
    print("Falling back to abstract only.")
    return abstract or ""

# ───── STEP 5: CHUNK & SUMMARIZE WITH GEMINI ──────────────────────────────────

def process_paper_with_gemini(text: str) -> dict:
    """
    Sends the full paper text to a Gemini model on Vertex AI to generate
    a comprehensive summary and structured chunks with metadata.

    Args:
        text: The full text content of the research paper.

    Returns:
        A dictionary containing the full paper summary and a list of chunk dictionaries,
        or an empty dict/error message if processing fails.
        Expected format:
        {
            "full_paper_summary": "...",
            "chunks": [
                {"chunk_id": "...", "chunk_text": "...", "summary_of_chunk": "...", "keywords": [], "relevance_to_anti_amyloid_therapy": "..."},
                ...
            ]
        }
    """
    vertexai.init(project=GCP_PROJECT, location=REGION)
    model = GenerativeModel(GEMINI_MODEL_ID)

    # The sophisticated prompt we discussed
    prompt_template = f"""
    You are an expert AI assistant specializing in anti-amyloid therapy research and highly skilled in condensing complex scientific literature. Your task is to process the provided medical research paper text.

    First, provide a comprehensive summary of the entire paper, focusing on the core objectives, methodologies, key findings, and conclusions related to anti-amyloid therapies. This summary should be concise yet capture all critical information a researcher would need to understand the paper's main contribution.

    Second, break down the full text of the paper into semantically coherent, concise chunks. Each chunk should represent a single, distinct idea, concept, or logical section of the paper, relevant to anti-amyloid therapy. Aim for chunks that are self-contained and provide enough context to be understood independently when retrieved.
    Prioritize chunking based on:
    - **Major sections:** Introduction, Methods, Results, Discussion, Conclusion.
    - **Specific anti-amyloid agents:** Information about particular drugs or compounds.
    - **Clinical trial details:** Study design, patient cohorts, outcomes.
    - **Mechanisms of action:** How therapies work at a biological level.
    - **Side effects or safety profiles.**
    - **Future directions or implications.**

    Each chunk should be between 200 and 500 words, optimizing for dense information and semantic completeness. If a section is very long, break it into multiple coherent chunks. Ensure there is minimal redundancy between chunks.

    For each chunk, extract the following metadata:
    - `chunk_id`: A unique identifier (e.g., `paper_title_chunk_X`).
    - `chunk_text`: The extracted text of the chunk.
    - `summary_of_chunk`: A 1-2 sentence summary of the specific chunk's content.
    - `keywords`: 3-5 relevant keywords for the chunk.
    - `relevance_to_anti_amyloid_therapy`: A brief explanation (1-2 sentences) of how this chunk specifically relates to anti-amyloid therapy.

    Output the results as a JSON object with two main keys:
    1.  `full_paper_summary`: (string) The comprehensive summary of the entire paper.
    2.  `chunks`: (array of objects) An array where each object represents a chunk and contains the fields: `chunk_id`, `chunk_text`, `summary_of_chunk`, `keywords`, `relevance_to_anti_amyloid_therapy`.

    IMPORTANT: Ensure the entire output is a valid JSON object. Do not include any text before or after the JSON.

    Here is the text of the research paper:

    \"\"\"
    {text}
    \"\"\"
    """

    # For large texts, Gemini 1.5 Pro (or later versions with large context) is preferred.
    # Ensure your text fits within the model's context window.
    # For gemini-1.0-pro, the context window is ~32k tokens. For gemini-1.5-pro, it's 1M tokens.

    try:
        # Create a Content object from the prompt string
        # Using generate_content is the standard way to call Gemini models
        response = model.generate_content(
            prompt_template,
            generation_config={
                "temperature": 0.2,  # A bit higher to allow for creativity in summarization/chunking, but still focused
                "max_output_tokens": 8192, # Significantly increase this, as the output will be a large JSON
                                          # Max for gemini-1.5-pro is 8192 tokens.
                                          # For gemini-1.0-pro, max is 2048.
                "response_mime_type": "application/json" # Request JSON directly if supported by model version
            },
            # safety_settings and tools can also be added here if needed
        )

        # Access the text from the response
        # If response_mime_type is set to "application/json", the response.text will be the JSON string
        raw_json_output = response.text.strip()
        print(f"Gemini raw output (first 500 chars): {raw_json_output[:500]}...")

        # Parse JSON from the model's output
        parsed_data = json.loads(raw_json_output)
        print("Successfully parsed JSON output from Gemini.")
        return parsed_data

    except Exception as e:
        print(f"Error processing paper with Gemini: {e}")
        print(f"Problematic text might be: {text[:500]}...") # Log beginning of text for debugging
        # Fallback: Return empty dict or raise error based on your error handling strategy
        return {} # Or raise an exception, depending on how you want to handle failures

# ───── STEP 6: UPLOAD JSON TO GCS ─────────────────────────────────────────────

def _upload_string_to_gcs(content_string: str, gcs_path: str, content_type: str = "text/plain"):
    """
    Uploads a string 'content_string' to GCS at 'gcs_path'.

    Args:
        content_string: The string content to upload (e.g., JSONL content).
        gcs_path: The full path in GCS (e.g., "folder/file.jsonl").
        content_type: The MIME type of the content (default: "text/plain").
    """

    try:
        client = storage.Client(project=GCP_PROJECT)
        bucket = client.bucket(GCP_BUCKET)
        blob   = bucket.blob(gcs_path)
        blob.upload_from_string(content_string, content_type=content_type)
        print(f"Uploaded → gs://{GCP_BUCKET}/{gcs_path} with content type {content_type}")
    except Exception as e:
        print(f"Failed to upload to GCS at {gcs_path}: {e}")
        raise # Re-raise the exception after print


def build_and_upload_paper_jsonl(paper: dict, gemini_output_chunks: dict):
    """
    Builds a JSONL string for a single paper, combining paper-level metadata
    with chunk-level metadata, and uploads it to Google Cloud Storage.

    Args:
        paper: A dictionary containing paper metadata (e.g., "title", "authors",
               "date", "source", "doi", "url").
        gemini_output_chunks: The dictionary output from the Gemini call,
                              expected to have "full_paper_summary" and "chunks" keys.
    """
    if not gemini_output_chunks or "chunks" not in gemini_output_chunks:
        print(f"No chunks found in Gemini output for paper: {paper.get('title', 'Untitled')}. Skipping upload.")
        return

    jsonl_lines = []
    
    # Extract paper-level metadata, providing fallbacks
    # Prioritize DOI, then URL, then a sanitized title for a stable source_id
    source_id = paper.get("doi")
    if not source_id:
        source_id = paper.get("url")
    if not source_id:
        # Sanitize title for a basic ID, add a hash to reduce collision risk
        sanitized_title = re.sub(r'[^a-zA-Z0-9_ -]', '', paper.get("title", "untitled_paper").replace(' ', '_'))[:50]
        title_hash = hashlib.md5(paper.get("title", "").encode('utf-8')).hexdigest()[:8]
        source_id = f"{sanitized_title}_{title_hash}"

    document_title = paper.get("title", "Untitled Paper")
    document_authors = paper.get("authors", []) # Expecting a list of strings
    document_publication_date = paper.get("date", "") # Assuming YYYY-MM-DD or similar
    document_source = paper.get("source", "Unknown Source")
    full_paper_summary = gemini_output_chunks.get("full_paper_summary", "")

    # Iterate through each chunk generated by Gemini
    for i, chunk_data in enumerate(gemini_output_chunks["chunks"]):
        # Create a unique chunk_id if not already present from Gemini
        chunk_id = chunk_data.get("chunk_id", f"{source_id}_chunk_{i+1}")

        # Combine chunk-specific and paper-level metadata
        combined_chunk = {
            "chunk_id": chunk_id,
            "chunk_text": chunk_data.get("chunk_text", ""),
            "summary_of_chunk": chunk_data.get("summary_of_chunk", ""),
            "keywords": chunk_data.get("keywords", []),
            "relevance_to_anti_amyloid_therapy": chunk_data.get("relevance_to_anti_amyloid_therapy", ""),
            # Add paper-level metadata to each chunk
            "document_source_id": source_id, # Using a distinct name to avoid confusion with chunk_id
            "document_title": document_title,
            "document_authors": document_authors,
            "document_publication_date": document_publication_date,
            "document_source": document_source,
            "full_paper_summary": full_paper_summary # Repeat the full paper summary for each chunk
        }
        jsonl_lines.append(json.dumps(combined_chunk))

    # Join all JSON objects with newline characters to form the JSONL content
    jsonl_content = "\n".join(jsonl_lines)

    # Define the GCS path for this paper's JSONL file
    # Ensure the source_id is safe for file names
    safe_source_id = re.sub(r'[^a-zA-Z0-9_.-]', '_', source_id) # Allow dots and dashes for DOIs/URLs
    gcs_file_path = f"anti_amyloid_chunks/{safe_source_id}.jsonl"

    # Upload the JSONL content to GCS
    _upload_string_to_gcs(jsonl_content, gcs_file_path, content_type="application/x-jsonlines")

# ───── MAIN PIPELINE ─────────────────────────────────────────────────────────
def main():
    # 1) Date range
    start_d, end_d = last_week_dates()

    # 2) Search both sources
    pubmed    = query_pubmed("Anti-amyloid therapy", start_d, end_d)
    medrxiv   = query_medrxiv("Anti-amyloid", start_d.replace('/', '-'), end_d.replace('/', '-'))
    all_papers= pubmed + medrxiv

    for i, paper in enumerate(all_papers):
        doi = paper.get("doi")
        print(f"Processing DOI={doi or '[no DOI]'}")

        # 3) Get PDF & extract text
        print(f"[INFO] Paper {i+1} - Getting link for DOI={doi}")
        pdf_url = get_pdf_link(doi)

        if not (pdf_url):
            print(f'[INFO] paper {i+1} - No PDF link found.')
            continue

        print(f"[INFO] Paper {i+1} - Extracting PDF")
        fulltxt = download_and_extract(pdf_url, doi)

        if not fulltxt:
            print(f'[INFO] paper {i+1} - No text found.')
            continue

        # 4) Chunk via Gemini
        print(f"[INFO] Paper {i+1} - Processing chunks with gemini")
        chunks  = process_paper_with_gemini(fulltxt)

        # 6) Upload to GCS under rag_corpus/
        build_and_upload_paper_jsonl(paper, chunks)


if __name__ == "__main__":
    main()
