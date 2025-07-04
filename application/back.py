from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import time
import asyncio
from datetime import datetime

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

# Mock responses for different medical scenarios
MOCK_RESPONSES = [
    "Based on the medical data, I can see the patient's imaging results. How can I help you analyze this case?",
    "The MRI shows some interesting findings. Would you like me to elaborate on any specific region?",
    "I notice there are some areas that require attention. Let me provide more details about the observations.",
    "The segmentation analysis reveals several key points. What specific aspect would you like to discuss?",
    "From the clinical data provided, I can offer insights about the patient's condition. What questions do you have?"
] 

@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "message": "MedGemma API",
        "version": "1.0.0",
        "endpoints": ["/seg", "/report", "/chat/start", "/chat/send"]
    }

@app.post("/seg", response_model=SegmentationResponse)
async def segmentation():
    """
    Segmentation endpoint
    Input: nothing
    Output: status confirmation
    """
<<<<<<< Updated upstream

    


    # Segmentation done send ok response
=======
    # Simulate processing time
    await asyncio.sleep(2)
>>>>>>> Stashed changes
    return SegmentationResponse(
        response="Ok."
    )

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
        response_content = random.choice(MOCK_RESPONSES)
    
    assistant_message = ChatMessage(role="assistant", content=response_content)
    chat_history.append(assistant_message)

    return assistant_message

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)