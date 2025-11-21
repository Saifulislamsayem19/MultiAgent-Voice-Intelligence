"""
RAG Router - Handles document upload, indexing, and retrieval
"""
import os
import time
import logging
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel

from app.services.document_loader import DocumentLoader
from app.services.vector_store import VectorStoreService
from app.services.metrics_logger import MetricsLogger
from app.config import settings

# Initialize router
rag_router = APIRouter(prefix="/api/rag", tags=["rag"])

# Initialize services
logger = logging.getLogger(__name__)
document_loader = DocumentLoader()
vector_store_service = VectorStoreService()
metrics_logger = MetricsLogger()

class DocumentUploadResponse(BaseModel):
    """Document upload response model"""
    filename: str
    agent: str
    chunks_created: int
    processing_time_ms: float
    status: str

class RetrievalRequest(BaseModel):
    """Document retrieval request model"""
    query: str
    agent: str
    top_k: int = 5
    similarity_threshold: float = 0.7

class RetrievalResponse(BaseModel):
    """Document retrieval response model"""
    query: str
    agent: str
    documents: List[dict]
    retrieval_time_ms: float
    total_results: int

@rag_router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    agent: str = Form(...)
):
    """
    Upload and process a document for a specific agent
    
    Args:
        file: Document file to upload
        agent: Agent name (real_estate, medical, ai_ml, sales, education)
        
    Returns:
        Upload status and processing metrics
    """
    start_time = time.time()
    temp_file_path = None
    
    try:
        # Validate agent
        valid_agents = ["real_estate", "medical", "ai_ml", "sales", "education"]
        if agent not in valid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent. Must be one of: {', '.join(valid_agents)}"
            )
        
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.docx', '.md', '.csv']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create agent directory if it doesn't exist
        agent_dir = Path(f"dataset/{agent}")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = agent_dir / file.filename
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved document {file.filename} for agent {agent}")
        
        # Process document
        processing_start = time.time()
        documents = document_loader.load_single_document(str(file_path))
        
        # Create/update vector store
        chunks_created = vector_store_service.add_documents(agent, documents)
        processing_time = (time.time() - processing_start) * 1000
        
        # Log metrics
        file_size_mb = len(content) / (1024 * 1024)
        metrics_logger.log_document_processing(
            agent=agent,
            filename=file.filename,
            chunks=chunks_created,
            processing_time_ms=processing_time,
            file_size_mb=file_size_mb
        )
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Document processed successfully in {total_time:.2f}ms, created {chunks_created} chunks")
        
        return DocumentUploadResponse(
            filename=file.filename,
            agent=agent,
            chunks_created=chunks_created,
            processing_time_ms=total_time,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@rag_router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(request: RetrievalRequest):
    """
    Retrieve relevant documents for a query
    
    Args:
        request: Retrieval request with query and parameters
        
    Returns:
        Retrieved documents with relevance scores
    """
    start_time = time.time()
    
    try:
        logger.info(f"Retrieving documents for query: {request.query[:100]}... from agent: {request.agent}")
        
        # Perform retrieval
        results = vector_store_service.search(
            agent=request.agent,
            query=request.query,
            k=request.top_k,
            threshold=request.similarity_threshold
        )
        
        retrieval_time = (time.time() - start_time) * 1000
        
        # Format results
        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score)
            })
        
        # Log metrics
        metrics_logger.log_retrieval_metrics(
            agent=request.agent,
            query_length=len(request.query),
            results_count=len(documents),
            retrieval_time_ms=retrieval_time
        )
        
        logger.info(f"Retrieved {len(documents)} documents in {retrieval_time:.2f}ms")
        
        return RetrievalResponse(
            query=request.query,
            agent=request.agent,
            documents=documents,
            retrieval_time_ms=retrieval_time,
            total_results=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@rag_router.get("/agents/{agent}/documents")
async def list_agent_documents(agent: str):
    """
    List all documents for a specific agent
    
    Args:
        agent: Agent name
        
    Returns:
        List of documents with metadata
    """
    try:
        agent_dir = Path(f"dataset/{agent}")
        
        if not agent_dir.exists():
            return {"agent": agent, "documents": [], "total": 0}
        
        documents = []
        for file_path in agent_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                documents.append({
                    "filename": file_path.name,
                    "size_mb": stat.st_size / (1024 * 1024),
                    "modified": stat.st_mtime,
                    "type": file_path.suffix
                })
        
        return {
            "agent": agent,
            "documents": documents,
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@rag_router.delete("/agents/{agent}/documents/{filename}")
async def delete_document(agent: str, filename: str):
    """
    Delete a document from an agent's dataset
    
    Args:
        agent: Agent name
        filename: Document filename to delete
        
    Returns:
        Deletion status
    """
    try:
        file_path = Path(f"dataset/{agent}/{filename}")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove from vector store
        vector_store_service.remove_document(agent, filename)
        
        # Delete file
        file_path.unlink()
        
        logger.info(f"Deleted document {filename} from agent {agent}")
        
        return {
            "status": "success",
            "message": f"Document {filename} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@rag_router.post("/reindex/{agent}")
async def reindex_agent_documents(agent: str):
    """
    Reindex all documents for a specific agent
    
    Args:
        agent: Agent name
        
    Returns:
        Reindexing status
    """
    start_time = time.time()
    
    try:
        agent_dir = Path(f"dataset/{agent}")
        
        if not agent_dir.exists():
            raise HTTPException(status_code=404, detail="Agent directory not found")
        
        # Clear existing vector store
        vector_store_service.clear_store(agent)
        
        # Reload all documents
        total_chunks = 0
        processed_files = 0
        
        for file_path in agent_dir.iterdir():
            if file_path.is_file():
                documents = document_loader.load_single_document(str(file_path))
                chunks = vector_store_service.add_documents(agent, documents)
                total_chunks += chunks
                processed_files += 1
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Reindexed {processed_files} files with {total_chunks} chunks in {processing_time:.2f}ms")
        
        return {
            "status": "success",
            "agent": agent,
            "files_processed": processed_files,
            "total_chunks": total_chunks,
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Error reindexing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reindex documents: {str(e)}")

@rag_router.get("/metrics")
async def get_rag_metrics():
    """Get RAG system metrics"""
    try:
        return metrics_logger.get_rag_metrics()
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")
