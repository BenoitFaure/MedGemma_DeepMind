# Project README

This README documents the end-to-end pipeline you implemented to build a RAG-enhanced clinical chatbot for anti‑amyloid therapy.

The project has two main parts:

1. **RAG Database Creation**

   - Query PubMed, medRxiv, Europe PMC
   - Download & extract PDF text
   - Chunk & summarize via Gemini 2.5 Pro
   - Export chunks to JSONL and upload to Google Cloud Storage

2. **Vertex AI RAG Engine Setup**

   - Configure a Vector Search Index over the RAG corpus
   - Deploy the index to an Index Endpoint in Vertex AI

---

## Prerequisites

- **Google Cloud SDK** installed (`gcloud`, `gsutil`):
  ```bash
  gcloud auth login
  gcloud config set project gemma-hcls25par-722
  gcloud config set compute/region europe-west1
  ```
- **Python 3.9+** environment with dependencies:
  ```bash
  pip install requests google-cloud-storage google-auth PyMuPDF vertexai
  ```
- A GCS bucket for the RAG database, e.g. `medgemma_rag_db`.
- Service account or ADC with roles:
  - Storage Admin (`roles/storage.admin`)
  - Vertex AI Admin (`roles/aiplatform.admin`)

---

## 1. RAG Database Creation

All code lives in `pipeline.py` (or split into `scripts/*.py`). Key steps:

### 1.1. Environment & Configuration

The script reads:

```python
GCP_PROJECT    = os.environ.get("GCP_PROJECT", "gemma-hcls25par-722")
GCP_BUCKET     = os.environ.get("GCP_BUCKET", "medgemma_rag_db")
REGION         = os.environ.get("GCP_REGION", "europe-west1")
UNPAYWALL_EMAIL= "medevstar7221@gcplab.me"
GEMINI_MODEL_ID= "gemini-2.5-pro"
```

Export these or edit defaults:

```bash
export GCP_PROJECT=gemma-hcls25par-722
export GCP_BUCKET=medgemma_rag_db
export GCP_REGION=europe-west1
```

### 1.2. Query Literature APIs

The script runs:

```python
pubmed = query_pubmed("Anti-amyloid therapy", start_date, end_date)
medrxiv= query_medrxiv("Anti-amyloid", start_date, end_date)
all_papers = pubmed + medrxiv
```

- **PubMed**: E-utilities (`esearch` + `efetch`)
- **medRxiv**: `api.biorxiv.org`
- **Europe PMC**: fallback for full-text XML

### 1.3. PDF Download & Text Extraction

Function `download_and_extract(pdf_url, doi, abstract)`:

- Attempts direct PDF download with browser‑like headers
- Falls back to Europe PMC fullTextXML
- Final fallback: abstract text

### 1.4. Chunking & Summarization

Function `process_paper_with_gemini(text)`:

- Calls `GenerativeModel(GEMINI_MODEL_ID).generate_content(...)`
- Uses a prompt to produce JSON with:
  - `full_paper_summary`
  - `chunks[]`: each with `chunk_id`, `chunk_text`, `summary_of_chunk`, `keywords`, `relevance_to_anti_amyloid_therapy`

### 1.5. JSONL Export & GCS Upload

Function `build_and_upload_paper_jsonl(paper, gemini_output)` does:

```python
# Combine metadata + each chunk into one JSON line
jsonl_lines = [ json.dumps(chunk_dict) for chunk_dict in parsed_chunks ]
# Upload to GCS:
bucket.blob(f"anti_amyloid_chunks/{source_id}.jsonl").upload_from_string(..., content_type="application/x-jsonlines")
```

Run the full pipeline via:

```bash
python pipeline.py
```

Each paper’s JSONL file lands in `gs://medgemma_rag_db/anti_amyloid_chunks/`.

---

## 2. Vertex AI RAG Engine Setup

### 2.1. Create & Deploy Vector Search Index (Console)

> **Note:** Managed RAG corpora require the Cloud Console UI; CLI support for managed stores is limited.

1. Go to **Vertex AI → Vector Search → Indexes → Create Index**
2. **Display name**: `anti-amyloid-index`
3. **Input vector dimension**: determine via:
   ```bash
   python - << 'EOF'
   import vertexai
   from vertexai.preview.language_models import TextEmbeddingModel
   vertexai.init(project="${GCP_PROJECT}", location="${GCP_REGION}")
   resp = TextEmbeddingModel.from_pretrained("text-embedding-004").get_embeddings(["Hello"])
   print(len(resp.embeddings[0].values))
   EOF
   ```
4. **Shard size**: Small
5. **Approximate neighbor count**: 30
6. **Managed vector store**: select `ragCorpora/4611686018427387904`
7. Click **Next → Create and deploy**
8. In **Deploy index**, choose **Create new endpoint** → **anti-amyloid-endpoint** → **Create**

### 2.2. Retrieve IDs

When status is **Ready**, note:

- **IndexEndpointId**: last segment of `projects/.../indexEndpoints/853047300316987392`
- **DeployedIndexId**: `index_v2_endpoint_1751642973735` under Deployed indexes

---

## 3. Sample Integration Code

A light‐weight Python client handles:

1. Retrieving top‑K snippets from your deployed RAG index.
2. Assembling the user question with those snippets into a prompt.
3. Calling the MedGemma endpoint to generate the final answer.

For detailed implementation and exact code, please refer to the `scripts/pipeline.py` file in this repository.

