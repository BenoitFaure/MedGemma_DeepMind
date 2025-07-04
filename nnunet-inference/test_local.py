import requests
import os
import time
from google.cloud import storage
import json 

# --- Configuration ---
LOCAL_FILE_PATH = "data/LUMIERE_001_0000.nii.gz"
INPUT_BUCKET = "nnunet-input-bucket"   
OUTPUT_BUCKET = "nnunet-output-bucket" 
PROJECT_ID = 'gemma-hcls25par-722' 

GCS_INPUT_BLOB_NAME = f"tests/{os.path.basename(LOCAL_FILE_PATH)}"
GCS_OUTPUT_PREFIX = "test-results/" 

LOCAL_API_URL = "http://localhost:8080/predict"
LOCAL_DOWNLOAD_DIR = "downloaded_inference_results"

# --- Utils functions for GCS ---
def upload_to_gcs(local_path, gcs_uri):
    """Téléverse un fichier local vers GCS."""
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    storage_client = storage.Client(project=PROJECT_ID) 
    print(f"Uploading {local_path} to {gcs_uri}...")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    print("Upload complete.")

def download_from_gcs(gcs_uri, local_path):
    """ Download from GCS to local """
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    storage_client = storage.Client(project=PROJECT_ID) 
    print(f"Downloading {gcs_uri} to {local_path}...")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print("Download complete.")


if __name__ == "__main__":
   
    os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)
    upload_to_gcs(LOCAL_FILE_PATH, f"gs://{INPUT_BUCKET}/{GCS_INPUT_BLOB_NAME}")

    print("\nLunch Docker container in an other terminal and click on Enter ")
    print(" Docker  Command : docker run --rm -p 8080:8080 -v ~/.config/gcloud:/root/.config/gcloud:ro --gpus all -e GOOGLE_CLOUD_PROJECT='YOUR_PROJECT_ID' my-nnunet-app")
    input()

    instances = [ # Wrap your payload in an 'instances' list
    {
        "input_gcs_uri": f"gs://{INPUT_BUCKET}/{GCS_INPUT_BLOB_NAME}",
        "output_gcs_prefix": f"gs://{OUTPUT_BUCKET}/{GCS_OUTPUT_PREFIX}"
    }
]

    print(f"Sending request to {LOCAL_API_URL}...")
    try:
        response = requests.post(LOCAL_API_URL, json={"instances": instances})
        response.raise_for_status()  
        result = response.json()
        print("API Response:")
        print(json.dumps(result, indent=2))
        if 'predictions' in result:
            result = result['predictions'][0]  # Accès au contenu
        # --- 3. Download output file from GCS ---
        if result.get("status") == "success" and "output_gcs_uris" in result:
            print(f"\n--- Downloading output files to {LOCAL_DOWNLOAD_DIR} ---")
            input_file_base_name = os.path.splitext(os.path.basename(LOCAL_FILE_PATH))[0]
            
            for gcs_output_uri in result["output_gcs_uris"]:
                # Recreate the GCS architecture to the local storage
                relative_path_start_index = gcs_output_uri.find(f"{GCS_OUTPUT_PREFIX.replace('gs://', '')}")
                if relative_path_start_index != -1:
                    relative_gcs_path = gcs_output_uri[gcs_output_uri.find(GCS_OUTPUT_PREFIX.replace("gs://", "")) + len(GCS_OUTPUT_PREFIX.replace("gs://", "")):].lstrip('/')
                else:
                    relative_gcs_path = gcs_output_uri.replace(f"gs://{OUTPUT_BUCKET}/", "") 

                local_output_path_full = os.path.join(LOCAL_DOWNLOAD_DIR, relative_gcs_path)
                os.makedirs(os.path.dirname(local_output_path_full), exist_ok=True)
                download_from_gcs(gcs_output_uri, local_output_path_full)
            print("All output files downloaded successfully.")
        else:
            print("No output URIs found in the API response or prediction was not successful.")

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from response: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")