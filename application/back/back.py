import os
import json
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from vertexai import rag

from back_segmentation import run_segmentation
from ..front.public.mri.slice import extract_files

from back_report import generate_client_report, generate_html, save_html, save_json, load_json, save_pdf

from back_environment import PROJECT_ID, REGION, MEDGEMMA_ENDPOINT, RAG_CORPUS
from back_chat import SYSTEM_PROMPT_CHAT, FIRST_USER_MESSAGE

# --- Configuration ---
app = FastAPI(title="MedGemma API", description="Medical imaging and chat API")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatStartRequest(BaseModel):
    client_name: str

class ChatSendRequest(BaseModel):
    message: str

class ReportRequest(BaseModel):
    client_name: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    messages: List[ChatMessage]

class SegmentationResponse(BaseModel):
    response: str

class ReportResponse(BaseModel):
    response: str

# Global variables for mock chat state
last_client: str = ""
chat_history: List[ChatMessage] = []

@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "message": "MedGemma API",
        "version": "1.0.0",
        "endpoints": ["/seg", "/report", "/chat/start", "/chat/send"]
    }

# Generate Segmentations
@app.post("/seg", response_model=SegmentationResponse)
async def segmentation():
    """
    Segmentation endpoint
    Input: nothing
    Output: status confirmation
    """

    try:
        # Run segmentation for both MRI IDs (0 and 1)
        print("Starting segmentation process...")
        
        # Run segmentation for ID "0"
        success_0 = run_segmentation("0")
        if not success_0:
            raise HTTPException(status_code=500, detail="Segmentation failed for ID 0")
        
        # Run segmentation for ID "1"
        success_1 = run_segmentation("1")
        if not success_1:
            raise HTTPException(status_code=500, detail="Segmentation failed for ID 1")
        
        # Extract files after segmentation
        print("Starting file extraction...")
        extract_success = extract_files()
        if not extract_success:
            raise HTTPException(status_code=500, detail="File extraction failed")
        
        print("Segmentation and extraction completed successfully!")
        
        # Segmentation done send ok response
        return SegmentationResponse(
            response="Segmentation and extraction completed successfully."
        )
    
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in segmentation endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Generate Info file and Report
@app.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Report generation endpoint
    Input: client name
    Output: status confirmation
    """
    client_name = request.client_name
    
    # Check if the segmentation has been done
    seg_file = f"./front/public/mri/0.seg/mri_file.nii"
    if not os.path.exists(seg_file):
        print("Starting segmentation process...")
        
        # Run segmentation for ID "0"
        success_0 = run_segmentation("0")
        if not success_0:
            raise HTTPException(status_code=500, detail="Segmentation failed for ID 0")
        
        # Run segmentation for ID "1"
        success_1 = run_segmentation("1")
        if not success_1:
            raise HTTPException(status_code=500, detail="Segmentation failed for ID 1")
        
        # Extract files after segmentation
        print("Starting file extraction...")
        extract_success = extract_files()
        if not extract_success:
            raise HTTPException(status_code=500, detail="File extraction failed")
        
        print("Segmentation and extraction completed successfully!")

    # Generate the report
    print(f"Generating report for client: {client_name}")
    info_json = generate_client_report(client_name)
    save_json(info_json)
    html_content = generate_html(info_json)
    save_html(html_content)
    save_pdf(html_content)

    return ReportResponse(
        response=f"Report generated for client: {client_name}"
    )

last_client = ""
chat_history = []
gemma_model = None
gemma_chat = None

@app.post("/chat/start", response_model=ChatResponse)
async def start_chat(request: ChatStartRequest):
    """
    Start chat session
    Input: client name
    Output: all chat messages for this client
    """
    global last_client, chat_history, gemma_model, gemma_chat, rag_tool, SYSTEM_PROMPT_CHAT, FIRST_USER_MESSAGE
    
    client_name = request.client_name
    
    if client_name != last_client:
        chat_history = []
        last_client = client_name
        json_data = load_json()
        
        gemma_model = GenerativeModel(
            model_name=MEDGEMMA_ENDPOINT,
            system_instruction=SYSTEM_PROMPT_CHAT,
            tools=[rag_tool],
        )
        gemma_chat = gemma_model.start_chat()

        initial_message = ChatMessage(
            role="user",
            content=FIRST_USER_MESSAGE.format(client_name=client_name, json_data=json_data)
        )
        response = gemma_chat.send_message(initial_message.content, tools=[])

        chat_history.append(ChatMessage(role="assistant", content=response.text))
    
    return ChatResponse(messages=chat_history)

@app.post("/chat/send", response_model=ChatMessage)
async def send_chat_message(request: ChatSendRequest):
    """
    Send message in chat
    Input: message
    Output: new response (updated chat history)
    """
    global chat_history, gemma_chat, gemma_model, rag_tool
    
    if not gemma_chat:
        return ChatMessage(
            role="assistant",
            content="There was an error. Please start a new chat session."
        )

    # Add user message to history
    user_message = ChatMessage(role="user", content=request.message)
    chat_history.append(user_message)
    
    response = gemma_chat.send_message(
        user_message.content, tools=[rag_tool]
    )
    msg_content = response.text # cite_json_like(response.text)
    message = ChatMessage(role="assistant", content=msg_content)
    # print(response)
    # with open("dumpresp.txt", "w") as f:
    #     f.write(str(response))
    chat_history.append(message)

    return message

if __name__ == "__main__":
    import uvicorn

    vertexai.init(project=PROJECT_ID, location=REGION)

    # 1. Create a RAG retrieval tool.
    # This tool connects to your RAG Corpus and handles the search.
    # The model will call this tool automatically when it needs external knowledge.
    rag_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(rag_corpus=RAG_CORPUS),
                ],
            )
        )
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)