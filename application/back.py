from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import time
import asyncio
from datetime import datetime
from back_segmentation import run_segmentation
from front.public.mri.slice import extract_files

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
    # Simulate report generation time
    await asyncio.sleep(1.5)
    return ReportResponse(
        response=f"Report generated for client: {client_name}"
    )

@app.post("/chat/start", response_model=ChatResponse)
async def start_chat(request: ChatStartRequest):
    """
    Start chat session
    Input: client name
    Output: all chat messages for this client
    """
    global last_client, chat_history
    
    client_name = request.client_name
    
    # Initialize chat session if it's a new client
    if client_name != last_client:
        chat_history = []
        last_client = client_name
        
        # Add initial system message
        initial_message = ChatMessage(
            role="assistant", 
            content=f"Hello! I'm MedGemma, your AI medical assistant. I've loaded the medical data for {client_name}. How can I help you analyze this case today?"
        )
        chat_history.append(initial_message)
    
    return ChatResponse(messages=chat_history)

@app.post("/chat/send", response_model=ChatMessage)
async def send_chat_message(request: ChatSendRequest):
    """
    Send message in chat
    Input: message
    Output: new response (updated chat history)
    """
    global chat_history
    
    # Add user message to history
    user_message = ChatMessage(role="user", content=request.message)
    chat_history.append(user_message)

    # Simulate processing time
    await asyncio.sleep(1)
    
    # Generate mock response based on user input
    import random
    
    # Simple keyword-based responses for demo
    user_input = request.message.lower()
    if "mri" in user_input or "scan" in user_input:
        response_content = "The MRI scan shows clear anatomical structures. The T1 and T2 weighted images provide excellent contrast for analysis. Would you like me to focus on any specific region?"
    elif "lesion" in user_input or "abnormal" in user_input:
        response_content = "I can help analyze potential lesions or abnormalities. Based on the imaging data, I can provide detailed measurements and characteristics. What specific findings are you interested in?"
    elif "report" in user_input:
        response_content = "I can help generate a comprehensive report based on the imaging findings. The report will include measurements, observations, and clinical correlations. What sections would you like me to prioritize?"
    elif "treatment" in user_input or "therapy" in user_input:
        response_content = "Based on the imaging findings, I can suggest treatment considerations. However, please remember that final treatment decisions should always involve the clinical team and patient history."
    else:
        response_content = 'boo'
    
    assistant_message = ChatMessage(role="assistant", content=response_content)
    chat_history.append(assistant_message)

    return assistant_message

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)