import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from vertexai import rag
import logging

# --- Configuration ---
PROJECT_ID        = "gemma-hcls25par-722"
REGION            = "us-central1" # Must match the region of your resources
# IMPORTANT: Update this with the resource name of your NEW STANDARD (not dedicated) endpoint.
MEDGEMMA_ENDPOINT = "projects/gemma-hcls25par-722/locations/us-central1/endpoints/1235003346155208704"
RAG_CORPUS        = (
    "projects/gemma-hcls25par-722"
    "/locations/us-central1"
    "/ragCorpora/4611686018427387904"
)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Example Usage ---
if __name__ == "__main__":
    # Initialize the Vertex AI SDK once when the script starts.
    # For a standard endpoint used with the RAG Engine, you do NOT specify
    # an api_endpoint. The SDK will route requests correctly.
    vertexai.init(project=PROJECT_ID, location=REGION)

    # 1. Create a RAG retrieval tool.
    # This tool connects to your RAG Corpus and handles the search.
    # The model will call this tool automatically when it needs external knowledge.
    rag_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(rag_corpus=RAG_CORPUS),
                ]
            )
        )
    )

    # 2. Instantiate your deployed MedGemma model.
    # Pass the full endpoint resource name and the RAG tool.
    medgemma_model = GenerativeModel(
        model_name=MEDGEMMA_ENDPOINT,
        tools=[rag_tool],
    )

    # 3. Start a chat session. This allows the model to maintain context.
    chat = medgemma_model.start_chat()

    print("\n--- Starting MedGemma RAG Chat ---")
    print("--- Type 'quit' or 'exit' to end the session. ---")

    while True:
        user_query = input("\nYou: ")
        if user_query.lower() in ["quit", "exit"]:
            print("Ending chat session. Goodbye!")
            break

        logging.info(f"Sending message to MedGemma chat: '{user_query}'")
        # By passing the tool on each send_message call, we strongly hint
        # to the model that it should consider using RAG for this specific turn.
        response = chat.send_message(user_query, tools=[rag_tool])
        logging.info("Received response from MedGemma chat.")
        print(f"\nMedGemma: {response.text}")