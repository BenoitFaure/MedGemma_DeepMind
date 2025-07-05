# Google
PROJECT_ID = 'gemma-hcls25par-722' # Google Cloud Project ID
REGION = 'us-central1' # Google Cloud Region

# MedGemma Endpoint
MEDGEMMA_ENDPOINT_ID = "7253594756670816256" # MedGemma Endpoint ID
MEDGEMMA_ENDPOINT_REGION = "europe-west4" # MedGemma Endpoint Region
MEDGEMMA_ENDPOINT = f"projects/{PROJECT_ID}/{REGION}/{MEDGEMMA_ENDPOINT_REGION}/endpoints/{MEDGEMMA_ENDPOINT_ID}"

# MedGemma Finetuned Endpoint
MEDGEMMA_FT_ENDPOINT_ID = "1219240747459411968" # MedGemma Endpoint ID
MEDGEMMA_FT_ENDPOINT_REGION = "us-central1" # MedGemma Endpoint Region

# NnUnet Endpoint
NNUNET_ENDPOINT_ID = "59844218876592128" # NnUnet Endpoint ID
NNUNET_ENDPOINT_REGION = "us-central1" # NnUnet Endpoint Region

# RAG Corpus
RAG_CORPUS        = (
    f"projects/{PROJECT_ID}"
    f"/locations/{REGION}"
    "/ragCorpora/4611686018427387904"
)