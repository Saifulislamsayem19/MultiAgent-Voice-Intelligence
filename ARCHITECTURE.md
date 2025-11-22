# System Architecture

## Overview

MultiAgent Voice Intelligence is a production-ready, voice-enabled AI system built on a microservices-inspired architecture. This document provides a comprehensive overview of the system's design, components, and data flow.

## Table of Contents
- [High-Level Architecture](#high-level-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Patterns](#design-patterns)
- [Scalability Considerations](#scalability-considerations)
- [Security Architecture](#security-architecture)

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web Browser, Mobile App, API Clients)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                     API Gateway Layer                        │
│                      (FastAPI)                               │
│  ┌──────────┬──────────┬──────────┬──────────────────┐     │
│  │ Audio    │  Chat    │  RAG     │  Metrics         │     │
│  │ Router   │  Router  │  Router  │  Router          │     │
│  └──────────┴──────────┴──────────┴──────────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Service Layer                              │
│  ┌─────────────────┬──────────────┬───────────────────┐    │
│  │ Orchestrator    │ Vector Store │ Tools/Functions   │    │
│  │ Service         │ Service      │ Service           │    │
│  └────────┬────────┴──────────────┴───────────────────┘    │
│           │                                                  │
│  ┌────────▼──────────────────────────────────────────┐     │
│  │         Specialized Agents (6)                     │     │
│  │  Real Estate │ Medical │ AI/ML │ Sales │ Education│     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  External Services Layer                     │
│  ┌──────────┬──────────┬──────────┬────────────────┐       │
│  │ OpenAI   │ Weather  │ FAISS    │ File Storage   │       │
│  │ API      │ API      │ DB       │ System         │       │
│  └──────────┴──────────┴──────────┴────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Gateway Layer (FastAPI)

**Responsibility**: Entry point for all client requests, routing, authentication, and rate limiting.

**Key Components**:
- **Audio Router** (`app/routers/audio.py`)
  - Speech-to-Text (STT) endpoint
  - Text-to-Speech (TTS) endpoint
  - Audio format validation
  - Real-time transcription

- **Chat Router** (`app/routers/chat.py`)
  - Message handling
  - Session management
  - Agent selection
  - Response formatting

- **RAG Router** (`app/routers/rag.py`)
  - Document upload
  - Document retrieval
  - Index management
  - Search operations

- **Metrics Router**
  - Performance monitoring
  - Usage analytics
  - System health checks

**Design Patterns**:
- Router pattern for endpoint organization
- Dependency injection for service access
- Middleware for cross-cutting concerns

### 2. Orchestrator Service

**File**: `app/services/orchestrator.py`

**Responsibility**: Intelligent routing of user queries to appropriate specialized agents.

**Architecture**:
```python
┌─────────────────────────────────────────┐
│        AgentOrchestrator                │
├─────────────────────────────────────────┤
│  - select_agent(query)                  │
│  - route_with_context(query, history)   │
│  - fallback_handling()                  │
└─────────────────────────────────────────┘
            │
            ▼
    ┌───────────────┐
    │  LLM-based    │
    │  Classification│
    └───────────────┘
```

**Key Features**:
- Context-aware routing using GPT-4
- Confidence scoring for agent selection
- Multi-agent consultation for complex queries
- Fallback mechanisms

**Routing Algorithm**:
1. Analyze query intent and keywords
2. Score each agent's relevance
3. Select highest-scoring agent (threshold: 0.7)
4. If ambiguous, route to multiple agents
5. Synthesize responses if needed

### 3. Specialized Agents

**File**: `app/services/specialized_agents.py`

Each agent follows a consistent architecture:

```python
class BaseAgent:
    """Base class for all specialized agents."""
    
    def __init__(self):
        self.system_prompt: str
        self.model: str
        self.temperature: float
        self.tools: List[str]
        self.vector_store: VectorStore
        
    async def process_query(self, query: str, context: dict) -> str:
        """Process user query with agent-specific logic."""
        pass
```

**Agent Specifications**:

| Agent | Temperature | Tools | RAG Enabled |
|-------|------------|-------|-------------|
| Real Estate | 0.7 | Weather, Calculator | Yes |
| Medical | 0.3 | None (strict accuracy) | Yes |
| AI/ML | 0.6 | Code execution | Yes |
| Sales | 0.7 | CRM integration | Yes |
| Education | 0.6 | Resource search | Yes |

**Agent Lifecycle**:
1. **Initialization**: Load system prompt and configuration
2. **Context Retrieval**: Query vector store for relevant documents
3. **Tool Selection**: Determine which tools to use
4. **LLM Invocation**: Generate response with context
5. **Response Formatting**: Structure output for client
6. **Metrics Logging**: Record performance data

### 4. Vector Store Service

**File**: `app/services/vector_store.py`

**Architecture**:
```
┌─────────────────────────────────────────┐
│          VectorStore                    │
├─────────────────────────────────────────┤
│  Document Processing                    │
│  ┌─────────────────────────────────┐   │
│  │ 1. Load (PDF, DOCX, TXT)        │   │
│  │ 2. Chunk (size: 1000, overlap:  │   │
│  │    200)                          │   │
│  │ 3. Embed (text-embedding-3-small)│   │
│  │ 4. Index (FAISS)                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Query Processing                       │
│  ┌─────────────────────────────────┐   │
│  │ 1. Embed query                   │   │
│  │ 2. Similarity search (k=5)       │   │
│  │ 3. Re-rank results               │   │
│  │ 4. Return contexts               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Key Features**:
- Multi-format document support (PDF, DOCX, TXT, MD)
- Chunking with overlap for context preservation
- Agent-specific vector stores
- Persistent index storage
- Efficient similarity search (< 500ms for 10K chunks)

**Index Structure**:
```
vector_stores/
├── real_estate_agent.index
├── medical_agent.index
├── ai_ml_agent.index
├── sales_agent.index
└── education_agent.index
```

### 5. Tools/Functions Service

**File**: `app/services/tools.py`

**Dynamic Function Registry**:
```python
AVAILABLE_TOOLS = {
    "weather": {
        "function": get_weather,
        "description": "Get current weather for a location",
        "parameters": {"location": "string"}
    },
    "calculator": {
        "function": calculate,
        "description": "Perform mathematical calculations",
        "parameters": {"expression": "string"}
    },
    "timezone": {
        "function": get_timezone,
        "description": "Get timezone information",
        "parameters": {"location": "string"}
    }
}
```

**Tool Execution Flow**:
1. Agent identifies need for tool use
2. Tool registry validates availability
3. Parameters extracted from query
4. Tool executed with error handling
5. Result formatted and returned to agent
6. Agent incorporates result in response

### 6. Session Management

**In-Memory Storage** (Current):
```python
sessions: Dict[str, List[Message]] = {}
```

**Production Recommendation**:
```python
# Redis-based session storage
class SessionStore:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour
    
    async def save_message(self, session_id: str, message: dict):
        key = f"session:{session_id}"
        await self.redis.lpush(key, json.dumps(message))
        await self.redis.expire(key, self.ttl)
```

## Data Flow

### 1. Text Query Flow

```
User Input
    │
    ▼
API Gateway (Chat Router)
    │
    ▼
Orchestrator
    │
    ├─> Analyze Query Intent
    ├─> Select Agent(s)
    └─> Route to Agent
        │
        ▼
    Specialized Agent
        │
        ├─> Retrieve Context (Vector Store)
        ├─> Select Tools (if needed)
        ├─> Generate Response (LLM)
        └─> Return Response
            │
            ▼
    Format & Log Metrics
        │
        ▼
    Return to Client
```

### 2. Voice Query Flow

```
Voice Input (Audio File)
    │
    ▼
Audio Router (STT Endpoint)
    │
    ├─> Validate Format
    ├─> Transcribe (OpenAI Whisper)
    └─> Return Text
        │
        ▼
[Follow Text Query Flow]
    │
    ▼
Response Text
    │
    ▼
Audio Router (TTS Endpoint)
    │
    ├─> Generate Audio (OpenAI TTS)
    └─> Return Audio File
        │
        ▼
    Client Playback
```

### 3. Document Upload Flow

```
Document Upload
    │
    ▼
RAG Router
    │
    ├─> Validate File
    ├─> Extract Agent Context
    └─> Process Document
        │
        ▼
    Vector Store Service
        │
        ├─> Load Content
        ├─> Chunk Text
        ├─> Generate Embeddings
        ├─> Update Index
        └─> Save to Disk
            │
            ▼
    Return Success
```

## Technology Stack

### Core Framework
- **FastAPI**: Async web framework
  - Built-in OpenAPI documentation
  - Automatic request validation
  - Dependency injection
  - WebSocket support

### AI/ML
- **OpenAI GPT-4**: Language model
- **OpenAI Whisper**: Speech-to-text
- **OpenAI TTS**: Text-to-speech
- **OpenAI Embeddings**: text-embedding-3-small

### Vector Database
- **FAISS**: Facebook AI Similarity Search
  - In-memory index
  - Fast approximate nearest neighbor search
  - Supports 1536-dimensional vectors

### Document Processing
- **LangChain**: Document loaders and text splitters
- **PyPDF2**: PDF parsing
- **python-docx**: DOCX parsing

### External APIs
- **WeatherAPI**: Real-time weather data
- **Timezone APIs**: Location-based time information

## Design Patterns

### 1. Strategy Pattern
Used in agent selection and routing:
```python
class RoutingStrategy(ABC):
    @abstractmethod
    def select_agent(self, query: str) -> str:
        pass

class LLMBasedRouting(RoutingStrategy):
    def select_agent(self, query: str) -> str:
        # Use LLM to determine best agent
        pass

class KeywordBasedRouting(RoutingStrategy):
    def select_agent(self, query: str) -> str:
        # Use keyword matching
        pass
```

### 2. Factory Pattern
Agent creation and initialization:
```python
class AgentFactory:
    @staticmethod
    def create_agent(agent_type: str) -> BaseAgent:
        agents = {
            "real_estate": RealEstateAgent,
            "medical": MedicalAgent,
            "ai_ml": AIMLAgent
        }
        return agents[agent_type]()
```

### 3. Observer Pattern
Metrics and logging:
```python
class MetricsObserver:
    def update(self, event: str, data: dict):
        # Log metrics
        pass

class Agent:
    def __init__(self):
        self.observers = []
    
    def notify(self, event: str, data: dict):
        for observer in self.observers:
            observer.update(event, data)
```

### 4. Repository Pattern
Vector store abstraction:
```python
class VectorStoreRepository:
    def save(self, documents: List[Document]):
        pass
    
    def search(self, query: str, k: int) -> List[Document]:
        pass
    
    def delete(self, ids: List[str]):
        pass
```

### Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| API Response Time | 1-3s | < 500ms |
| STT Latency | < 2s | < 1s |
| Document Indexing | Sync | Async (< 10s) |
| Concurrent Users | 50 | 500+ |
| Vector Search | < 500ms | < 100ms |


## Conclusion

This architecture provides a solid foundation for a production-ready AI agent system. The modular design allows for easy extension and scaling as requirements grow. Key strengths include clear separation of concerns, well-defined interfaces, and thoughtful use of design patterns.

For questions or suggestions about the architecture, please open an issue or discussion on GitHub.
