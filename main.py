"""
Main application file for Voice-Enabled AI Agent System
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from dotenv import load_dotenv

# Import routers
from app.routers.audio import audio_router
from app.routers.chat import chat_router
from app.routers.rag import rag_router
from app.services.document_loader import DocumentLoader
from app.services.vector_store import VectorStoreService
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Voice-Enabled AI Agent System",
    description="Multi-agent RAG system with voice capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
Path("logs").mkdir(exist_ok=True)
Path("dataset").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("vector_stores").mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(audio_router)
app.include_router(chat_router)
app.include_router(rag_router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting Voice-Enabled AI Agent System...")
        
        # Initialize document loader and vector stores
        doc_loader = DocumentLoader()
        vector_service = VectorStoreService()
        
        # Load documents from dataset folder
        dataset_path = Path("dataset")
        if dataset_path.exists():
            for agent_folder in dataset_path.iterdir():
                if agent_folder.is_dir():
                    agent_name = agent_folder.name
                    logger.info(f"Loading documents for {agent_name} agent...")
                    
                    documents = doc_loader.load_documents(str(agent_folder))
                    if documents:
                        vector_service.create_vector_store(agent_name, documents)
                        logger.info(f"Created vector store for {agent_name} with {len(documents)} documents")
        
        logger.info("System initialization complete")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/system-info")
async def system_info():
    """Get system information"""
    return {
        "agents": [
            "real_estate",
            "medical",
            "ai_ml",
            "sales",
            "education"
        ],
        "capabilities": {
            "voice_input": True,
            "voice_output": True,
            "document_retrieval": True,
            "dynamic_functions": ["weather", "time", "calculator"],
            "multi_agent": True
        },
        "models": {
            "llm": "gpt-4",
            "embeddings": "text-embedding-3-small",
            "stt": "whisper-1",
            "tts": "tts-1"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )
