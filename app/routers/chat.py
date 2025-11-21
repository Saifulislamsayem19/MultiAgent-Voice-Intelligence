"""
Chat Router - Handles chat interactions and agent orchestration
"""
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage

from app.services.orchestrator import OrchestratorAgent
from app.services.specialized_agents import SpecializedAgentFactory
from app.services.metrics_logger import MetricsLogger
from app.config import settings

# Initialize router
chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize logger
logger = logging.getLogger(__name__)
metrics_logger = MetricsLogger()

# Initialize orchestrator and agents
orchestrator = OrchestratorAgent()
agent_factory = SpecializedAgentFactory()

# Session storage (in production, use Redis or similar)
sessions: Dict[str, Dict[str, Any]] = {}

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = None
    agent_override: Optional[str] = None
    include_sources: bool = True

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    agent_used: str
    sources: Optional[List[Dict[str, Any]]] = None
    metrics: Dict[str, Any]
    timestamp: str

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    created_at: str
    message_count: int
    agents_used: List[str]

@chat_router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Process chat message through agent system
    
    Args:
        request: Chat request with message and optional parameters
        
    Returns:
        Agent response with sources and metrics
    """
    start_time = time.time()
    
    try:
        # Create or retrieve session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = {
                "memory": ConversationBufferMemory(return_messages=True),
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "agents_used": []
            }
        
        session = sessions[session_id]
        session["message_count"] += 1
        
        logger.info(f"Processing message for session {session_id}: {request.message[:100]}...")
        
        # Determine which agent to use
        if request.agent_override:
            # Use specified agent
            selected_agent = request.agent_override
            logger.info(f"Using override agent: {selected_agent}")
        else:
            # Use orchestrator to determine best agent
            routing_start = time.time()
            selected_agent = await orchestrator.route_query(request.message)
            routing_time = (time.time() - routing_start) * 1000
            logger.info(f"Orchestrator selected agent: {selected_agent} (routing took {routing_time:.2f}ms)")
        
        # Track agent usage
        if selected_agent not in session["agents_used"]:
            session["agents_used"].append(selected_agent)
        
        # Get specialized agent
        agent = agent_factory.get_agent(selected_agent)
        
        # Process query with agent
        agent_start = time.time()
        result = await agent.process_query(
            query=request.message,
            memory=session["memory"],
            include_sources=request.include_sources
        )
        agent_time = (time.time() - agent_start) * 1000
        
        # Calculate total processing time
        total_time = (time.time() - start_time) * 1000
        
        # Log metrics
        metrics = {
            "total_time_ms": total_time,
            "agent_time_ms": agent_time,
            "routing_time_ms": routing_time if not request.agent_override else 0,
            "tokens_used": result.get("tokens_used", 0),
            "sources_count": len(result.get("sources", [])) if request.include_sources else 0
        }
        
        metrics_logger.log_chat_metrics(
            session_id=session_id,
            agent=selected_agent,
            response_time_ms=total_time,
            tokens_used=metrics["tokens_used"]
        )
        
        logger.info(f"Message processed successfully in {total_time:.2f}ms")
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            agent_used=selected_agent,
            sources=result.get("sources") if request.include_sources else None,
            metrics=metrics,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@chat_router.post("/clear-session")
async def clear_session(session_id: str):
    """
    Clear a specific chat session
    
    Args:
        session_id: Session ID to clear
        
    Returns:
        Success status
    """
    try:
        if session_id in sessions:
            del sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return {"status": "success", "message": f"Session {session_id} cleared"}
        else:
            return {"status": "not_found", "message": f"Session {session_id} not found"}
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

@chat_router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions():
    """Get list of active sessions"""
    try:
        session_list = []
        for session_id, session_data in sessions.items():
            session_list.append(SessionInfo(
                session_id=session_id,
                created_at=session_data["created_at"],
                message_count=session_data["message_count"],
                agents_used=session_data["agents_used"]
            ))
        return session_list
    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sessions: {str(e)}")

@chat_router.get("/agents")
async def get_available_agents():
    """Get list of available specialized agents"""
    try:
        agents = agent_factory.get_available_agents()
        return {
            "agents": agents,
            "orchestrator": {
                "name": "orchestrator",
                "description": "Automatically routes queries to the best agent"
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {str(e)}")

@chat_router.post("/feedback")
async def submit_feedback(
    session_id: str,
    message_id: str,
    rating: int,
    comment: Optional[str] = None
):
    """Submit feedback for a chat interaction"""
    try:
        # Log feedback
        metrics_logger.log_feedback(
            session_id=session_id,
            message_id=message_id,
            rating=rating,
            comment=comment
        )
        
        logger.info(f"Feedback received for session {session_id}, message {message_id}: rating={rating}")
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

@chat_router.get("/metrics")
async def get_chat_metrics():
    """Get chat system metrics"""
    try:
        return metrics_logger.get_chat_metrics()
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")
