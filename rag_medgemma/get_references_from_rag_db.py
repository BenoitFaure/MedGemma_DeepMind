from google.cloud import storage
import json

# ─── CONFIG ─────────────────────────────────────────────
GCP_PROJECT = "gemma-hcls25par-722"
GCS_BUCKET = "medgemma_rag_db"
PREFIX = "anti_amyloid_chunks/"  
# ───────────────────────────────────────────────────────

def list_jsonl_files(bucket_name, prefix):
    """List all JSONL files in the bucket under the given prefix."""
    client = storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    return [blob.name for blob in blobs if blob.name.endswith(".jsonl")]

def extract_metadata_from_jsonl(bucket_name, blob_name):
    """Download and parse a JSONL blob, returning unique document-level metadata."""
    client = storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    content = blob.download_as_text()

    for line in content.splitlines():
        data = json.loads(line)
        return {
            "document_title": data.get("document_title"),
            "jsonl_file": blob_name
        }
    return None

def get_reference_list():
    jsonl_files = list_jsonl_files(GCS_BUCKET, PREFIX)
    all_metadata = []
    final_list = []

    for file in jsonl_files:
        metadata = extract_metadata_from_jsonl(GCS_BUCKET, file)
        if metadata:
            all_metadata.append(metadata)

    # Output the metadata
    for doc in all_metadata:
        final_list.append((doc['jsonl_file'].split('/')[1], doc['document_title']))

    return final_list

if __name__ == "__main__":
    print(get_reference_list())
