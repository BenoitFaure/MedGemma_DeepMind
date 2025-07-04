import os
import time
import json
import requests
from google.cloud import storage
from google.cloud import aiplatform 

# --- Vertex AI Configuration ---
PROJECT_ID = 'gemma-hcls25par-722'  
REGION = 'europe-west1'            
ENDPOINT_ID = '8337460333983563776' 

# --- GCS Bucket Configuration ---
LOCAL_FILE_PATH = "data/LUMIERE_001_0000.nii.gz"
INPUT_BUCKET = "nnunet-input-bucket"   
OUTPUT_BUCKET = "nnunet-output-bucket" 

GCS_INPUT_BLOB_NAME = f"tests/{os.path.basename(LOCAL_FILE_PATH)}"
GCS_OUTPUT_PREFIX = "test-results/" 

LOCAL_DOWNLOAD_DIR = "downloaded_inference_results"

# --- GCS Utility Functions ---
def upload_to_gcs(local_path, gcs_uri):
    """Uploads a local file to GCS."""
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    storage_client = storage.Client(project=PROJECT_ID) 
    print(f"Uploading {local_path} to {gcs_uri}...")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    print("Upload complete.")

def download_from_gcs(gcs_uri, local_path):
    """Downloads a file from GCS to a local path."""
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    storage_client = storage.Client(project=PROJECT_ID) 
    print(f"Downloading {gcs_uri} to {local_path}...")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print("Download complete.")

# --- Main script starts here ---
if __name__ == "__main__":
    
    os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)

    # 1. Upload the test file to GCS
    upload_to_gcs(LOCAL_FILE_PATH, f"gs://{INPUT_BUCKET}/{GCS_INPUT_BLOB_NAME}")

    # --- 2. Send the request to the API deployed on Vertex AI ---
    print(f"\nInitializing Vertex AI client for project {PROJECT_ID} in region {REGION}...")
    aiplatform.init(project=PROJECT_ID, location=REGION)
    endpoint = aiplatform.Endpoint(endpoint_name=ENDPOINT_ID)
    print(f"Connected to Vertex AI Endpoint: {endpoint.resource_name}")

    instances = [
        {
            "input_gcs_uri": f"gs://{INPUT_BUCKET}/{GCS_INPUT_BLOB_NAME}",
            "output_gcs_prefix": f"gs://{OUTPUT_BUCKET}/{GCS_OUTPUT_PREFIX}"
        }
    ]

    print(f"Sending prediction request to Vertex AI Endpoint {ENDPOINT_ID}...")
    try:

        response = endpoint.predict(instances=instances)

        predictions = response.predictions
        
        if predictions and len(predictions) > 0:

            result = predictions[0]
            
            print("API Response from Vertex AI:")
            print(json.dumps(result, indent=2))
            
            # --- 3. Download output files from GCS ---
            if result.get("status") == "success" and "output_gcs_uris" in result:
                print(f"\n--- Downloading output files to {LOCAL_DOWNLOAD_DIR} ---")
                
                for gcs_output_uri in result["output_gcs_uris"]:

                    if GCS_OUTPUT_PREFIX in gcs_output_uri:

                        prefix_index = gcs_output_uri.find(GCS_OUTPUT_PREFIX)
                        relative_gcs_path = gcs_output_uri[prefix_index + len(GCS_OUTPUT_PREFIX):].lstrip('/')
                    else:

                        relative_gcs_path = gcs_output_uri.replace(f"gs://{OUTPUT_BUCKET}/", "")
                    

                    local_output_path_full = os.path.join(LOCAL_DOWNLOAD_DIR, GCS_OUTPUT_PREFIX, relative_gcs_path)
                    

                    os.makedirs(os.path.dirname(local_output_path_full), exist_ok=True)
                    

                    download_from_gcs(gcs_output_uri, local_output_path_full)
                
                print("All output files downloaded successfully.")
            else:
                print("No output URIs found or prediction was not successful.")
                print(f"Result status: {result.get('status')}")
                print(f"Full result: {result}")
        else:
            print("No predictions returned from Vertex AI")
            
    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()