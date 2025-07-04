# LIB for Fast API AND gcloud
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import tempfile
import shutil
from datetime import datetime
import traceback
from google.cloud import storage 

# LIB for inference 
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

app = FastAPI(title="nnU-Net Inference API with GCS")

# Predictor initialization
predictor = None

def initialize_predictor():
    """Initializes the nnU-Net predictor."""
    global predictor
    if predictor is None:
        print("Initializing nnU-Net predictor...")
        model_path = "/app/dataset/nnUNet_trained_models/Dataset001_LUMIERE/"
        if not os.path.exists(model_path):
            raise RuntimeError(f"Model path does not exist: {model_path}")

        predictor = nnUNetPredictor(
            tile_step_size=0.5,
            use_gaussian=True,
            use_mirroring=True,
            device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
            verbose=False, 
        )
        predictor.initialize_from_trained_model_folder(
            model_training_output_dir=model_path,
            use_folds=(0,),
        )
        print("Predictor initialized successfully")
        print(f"Using device: {predictor.device}")

@app.on_event("startup")
async def startup_event():
    initialize_predictor()

# Health check of the endpoint
@app.get("/health", status_code=200)
async def health():
    return {"status": "healthy"}

# Pydantic model for the core prediction request parameters
class PredictRequestCore(BaseModel):
    input_gcs_uri: str # Ex: "gs://my-input-bucket/LUMIERE_001_0000.nii.gz"
    output_gcs_prefix: str # Ex: "gs://my-output-bucket/results/"

# NEW: Pydantic model for the Vertex AI prediction request format
# Vertex AI wraps your input JSON inside an 'instances' array.
class VertexAIPredictRequest(BaseModel):
    instances: list[PredictRequestCore] # Expects a list where each item is a PredictRequestCore

def parse_gcs_uri(gcs_uri: str) -> (str, str):
    """Separates a GCS URI into bucket name and blob name."""
    if not gcs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS URI. Must start with 'gs://'")
    parts = gcs_uri.replace("gs://", "").split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1] if len(parts) > 1 else ""
    return bucket_name, blob_name

# Adjusted /predict endpoint to accept the VertexAIPredictRequest
@app.post("/predict")
async def predict(request_payload: VertexAIPredictRequest): # Renamed `request` to `request_payload` for clarity
    """
    Launches inference from a file in GCS and saves the result to GCS.
    This endpoint is designed to accept requests formatted for Vertex AI custom prediction.
    """
    
    # Vertex AI sends a list of instances. For this API, we expect one instance.
    if not request_payload.instances:
        raise HTTPException(status_code=400, detail="No instances provided in the request payload.")
    
    # Extract the actual prediction request from the first instance
    # This is the original structure your FastAPI app was designed to handle
    request: PredictRequestCore = request_payload.instances[0] 

    temp_dir = tempfile.mkdtemp()
    try:
        # Ensure 'gemma-hcls25par-722' is your correct Google Cloud Project ID
        storage_client = storage.Client(project='gemma-hcls25par-722')

        # --- 1. Download file from GCS ---
        input_bucket_name, input_blob_name = parse_gcs_uri(request.input_gcs_uri)
        input_filename = os.path.basename(input_blob_name)

        input_dir = os.path.join(temp_dir, "input")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        local_input_path = os.path.join(input_dir, input_filename)
        
        print(f"Downloading {request.input_gcs_uri} to {local_input_path}...")
        bucket = storage_client.bucket(input_bucket_name)
        blob = bucket.blob(input_blob_name)
        blob.download_to_filename(local_input_path)
        print("Download complete.")

        # --- 2. Execute nnU-Net inference ---
        print(f"Processing file: {local_input_path}")
        predictor.predict_from_files(
            input_dir, # nnU-Net expects an input folder here if multiple files are to be processed
            output_dir,
            save_probabilities=False,
            overwrite=True,
            num_processes_preprocessing=1,
            num_processes_segmentation_export=1
        )
        print("Inference complete.")

        # --- 3. Upload results to GCS ---
        output_files = os.listdir(output_dir)
        if not output_files:
            raise HTTPException(status_code=500, detail="Inference did not produce any output file.")
        
        uploaded_files_uris = [] # To store the URIs of all uploaded files

        output_bucket_name, output_prefix = parse_gcs_uri(request.output_gcs_prefix)
        output_bucket = storage_client.bucket(output_bucket_name)

        for filename in output_files:
            local_output_path = os.path.join(output_dir, filename)

            # Clean up the input filename for use in the output folder name
            input_file_base_name = os.path.splitext(input_filename)[0]
            
            # Create a specific output folder for this prediction run
            output_folder_for_this_run = os.path.join(output_prefix.strip("/"), f"{input_file_base_name}_nnunet_output")
            output_blob_name = os.path.join(output_folder_for_this_run, filename)


            print(f"Uploading {local_output_path} to gs://{output_bucket_name}/{output_blob_name}...")
            output_blob = output_bucket.blob(output_blob_name)
            output_blob.upload_from_filename(local_output_path)
            print(f"Upload of {filename} complete.")
            uploaded_files_uris.append(f"gs://{output_bucket_name}/{output_blob_name}")

        final_output_uris = uploaded_files_uris # The response will contain a list of URIs
        
        return {
            "predictions": [  # <- Ceci est requis par Vertex AI
                {
                    "status": "success",
                    "input_gcs_uri": request.input_gcs_uri,
                    "output_gcs_uris": final_output_uris,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
    
    except Exception as e:
        error_msg = f"Prediction failed: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.get("/")
async def root():
    return {"message": "nnU-Net Inference API with GCS", "version": "1.1.0"}