"""
Configuration settings for the Voice-Enabled AI Agent System
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default="gpt-4")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    
    # Weather API Configuration
    weather_api_key: str = Field(default=os.getenv("WEATHER_API_KEY", ""))
    weather_api_url: str = Field(default="http://api.weatherapi.com/v1")
    
    # Vector Store Configuration
    vector_store_path: str = Field(default="vector_stores")
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    
    # Agent Configuration
    max_iterations: int = Field(default=5)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000)
    
    # Audio Configuration
    audio_sample_rate: int = Field(default=16000)
    audio_channels: int = Field(default=1)
    
    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    
    # Performance Configuration
    max_concurrent_requests: int = Field(default=10)
    request_timeout: int = Field(default=60)
    cache_ttl: int = Field(default=3600)
    
    # Security Configuration
    enable_api_key: bool = Field(default=False)
    api_key: Optional[str] = Field(default=None)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()

# Agent-specific configurations
AGENT_CONFIGS = {
    "general": {
        "name": "General Assistant",
        "description": "Handles general queries, weather, calculations, and everyday questions",
        "system_prompt": """You are a helpful general assistant with access to various tools. You can:
        - Answer general knowledge questions
        - Provide weather information for any location
        - Perform calculations
        - Get current time for any timezone
        - Help with everyday queries
        Use the available tools when appropriate. For weather queries, ALWAYS use the weather tool.
        For calculations, ALWAYS use the calculator tool.""",
        "tools": ["weather", "calculator", "current_time", "web_search"]
    },
    "real_estate": {
        "name": "Real Estate Expert",
        "description": "Specializes in property listings, market analysis, and real estate investments",
        "system_prompt": """You are a real estate expert assistant. You have deep knowledge about:
        - Property types and valuations
        - Market trends and analysis
        - Investment strategies
        - Legal aspects of real estate
        - Mortgage and financing options
        Provide accurate and helpful information based on the documents provided.
        You also have access to weather and calculator tools when needed.""",
        "tools": ["property_search", "market_analysis", "mortgage_calculator", "weather", "calculator"]
    },
    "medical": {
        "name": "Medical Assistant",
        "description": "Provides medical information and health-related guidance",
        "system_prompt": """You are a medical information assistant. You can provide:
        - General medical information
        - Symptom explanations
        - Treatment options overview
        - Health and wellness tips
        Note: Always remind users to consult healthcare professionals for medical advice.
        You also have access to calculator tools when needed.""",
        "tools": ["symptom_checker", "drug_interactions", "health_tips", "calculator"]
    },
    "ai_ml": {
        "name": "AI/ML Expert",
        "description": "Expert in artificial intelligence and machine learning topics",
        "system_prompt": """You are an AI/ML expert assistant. You specialize in:
        - Machine learning algorithms and techniques
        - Deep learning and neural networks
        - Natural language processing
        - Computer vision
        - AI ethics and best practices
        Provide technical and accurate information based on the latest developments.
        You also have access to calculator tools when needed.""",
        "tools": ["code_examples", "model_recommendations", "performance_metrics", "calculator"]
    },
    "sales": {
        "name": "Sales Strategist",
        "description": "Helps with sales strategies, customer relations, and business development",
        "system_prompt": """You are a sales strategy expert. You provide guidance on:
        - Sales techniques and methodologies
        - Customer relationship management
        - Lead generation and qualification
        - Sales metrics and KPIs
        - Negotiation strategies
        Help users improve their sales performance with practical advice.
        You also have access to calculator tools when needed.""",
        "tools": ["crm_insights", "sales_metrics", "lead_scoring", "calculator"]
    },
    "education": {
        "name": "Education Advisor",
        "description": "Provides educational guidance and learning resources",
        "system_prompt": """You are an education advisor. You help with:
        - Learning strategies and techniques
        - Curriculum planning
        - Educational resources
        - Study tips and exam preparation
        - Career guidance in education
        Support learners and educators with evidence-based approaches.
        You also have access to calculator tools when needed.""",
        "tools": ["study_planner", "resource_finder", "quiz_generator", "calculator"]
    }
}

# Orchestrator configuration
ORCHESTRATOR_CONFIG = {
    "name": "Master Orchestrator",
    "description": "Routes queries to the appropriate specialized agent",
    "system_prompt": """You are the master orchestrator for a multi-agent system. Your role is to:
    1. Analyze the user's query to understand the intent and domain
    2. Determine which specialized agent is best suited to handle the query
    3. Route the query to the appropriate agent
    
    Available agents:
    - general: Weather, time, calculations, general knowledge, everyday questions
    - real_estate: Property, housing, real estate investments
    - medical: Health, symptoms, medical information
    - ai_ml: Artificial intelligence, machine learning, data science
    - sales: Sales strategies, customer relations, business development
    - education: Learning, teaching, educational resources
    
    Routing guidelines:
    - Use 'general' for weather queries, time queries, calculations, or general questions
    - Use 'medical' ONLY for health-related queries
    - Use 'ai_ml' ONLY for AI/ML technical topics
    - Use other agents for their specific domains
    - When in doubt, use 'general' agent
    """
}
