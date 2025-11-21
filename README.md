# Multi-Agent Voice AI Platform

A production-ready, enterprise-grade voice-enabled AI agent system featuring intelligent multi-agent orchestration, retrieval-augmented generation (RAG), and seamless voice interactions. Built with FastAPI and powered by OpenAI's GPT-4, this system provides domain-specific expertise through specialized AI agents.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img width="1501" height="936" alt="image" src="https://github.com/user-attachments/assets/4175e674-6132-43c0-be47-2d93dade5ea9" />


## Overview

This system implements a sophisticated multi-agent architecture that intelligently routes user queries to specialized domain experts. Each agent maintains its own knowledge base through RAG pipelines, enabling accurate, context-aware responses backed by domain-specific documentation.

### Key Features

- **🎙️ Voice-First Interface** - Natural voice interactions with real-time speech-to-text and text-to-speech capabilities
- **🤖 Multi-Agent Architecture** - Six specialized agents with intelligent query routing
- **📚 RAG Pipeline** - Context-aware responses powered by FAISS vector search
- **⚡ Real-Time Processing** - Optimized for low-latency responses
- **📊 Comprehensive Metrics** - Built-in performance monitoring and analytics
- **🔧 Dynamic Function Calling** - Extensible tool system for real-time data integration
- **🐳 Docker Ready** - Containerized deployment with Docker Compose support

## Architecture

### Agent Ecosystem

The system consists of six specialized agents, each trained for specific domains:

| Agent | Domain | Capabilities |
|-------|--------|-------------|
| **Real Estate** | Property & Markets | Property analysis, market trends, investment insights |
| **Medical** | Healthcare & Wellness | Health information, symptom guidance (with medical disclaimers) |
| **AI/ML** | Artificial Intelligence | Technical guidance, model recommendations, code examples |
| **Sales** | Business Development | CRM strategies, sales methodologies, pipeline management |
| **Education** | Learning & Development | Study plans, curriculum design, educational resources |
| **Orchestrator** | Query Routing | Intelligent agent selection and query distribution |

### Technology Stack

- **Backend**: FastAPI, Python 3.12
- **AI Models**: OpenAI GPT-4, Whisper (STT), TTS
- **Vector Database**: FAISS
- **Document Processing**: LangChain, PyPDF2, python-docx
- **Embeddings**: OpenAI text-embedding-3-small
- **External APIs**: WeatherAPI, timezone services

## Getting Started

### Prerequisites

- Python 3.12 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- WeatherAPI key ([Free tier available](https://www.weatherapi.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Saifulislamsayem19/MultiAgent-Voice-Intelligence.git
   cd voice-ai-agent
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   WEATHER_API_KEY=your_weather_api_key_here
   HOST=0.0.0.0
   PORT=8000
   ```

5. **Launch the application**
   ```bash
   python main.py
   ```

   Access the web interface at `http://localhost:8000`

### Docker Deployment

For containerized deployment:

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t voice-ai-agent .
docker run -p 8000:8000 --env-file .env voice-ai-agent
```

## Usage Guide

### Web Interface

1. **Select an Agent** - Choose a specialized agent or let the orchestrator route automatically
2. **Voice or Text Input** - Click the microphone for voice input or type your message
3. **Upload Documents** - Enhance agent knowledge by uploading domain-specific documents
4. **Review Metrics** - Monitor system performance through the metrics dashboard

### API Integration

#### Chat Completion
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/send",
    json={
        "message": "What are the latest trends in commercial real estate?",
        "agent": "real_estate",
        "session_id": "user_123"
    }
)
```

#### Document Upload
```python
files = {"file": open("document.pdf", "rb")}
data = {"agent": "real_estate"}

response = requests.post(
    "http://localhost:8000/api/rag/upload",
    files=files,
    data=data
)
```

#### Voice Transcription
```python
with open("audio.wav", "rb") as audio:
    response = requests.post(
        "http://localhost:8000/api/audio/transcribe",
        files={"file": audio}
    )
```

## Project Structure

```
voice-ai-agent/
├── app/
│   ├── config.py                 # System configuration
│   ├── routers/                  # API route handlers
│   │   ├── audio.py              # Speech processing endpoints
│   │   ├── chat.py               # Conversation management
│   │   └── rag.py                # Document operations
│   └── services/                 # Core business logic
│       ├── orchestrator.py       # Agent routing engine
│       ├── specialized_agents.py # Domain-specific agents
│       ├── vector_store.py       # Vector database management
│       ├── tools.py              # Dynamic function library
│       └── metrics_logger.py     # Performance analytics
├── dataset/                      # Document repository
│   ├── real_estate/
│   ├── medical/
│   ├── ai_ml/
│   ├── sales/
│   └── education/
├── vector_stores/                # FAISS indices
├── static/                       # Frontend assets
├── templates/                    # HTML templates
├── logs/                         # Application logs
├── main.py                       # Application entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## API Reference

### Chat Endpoints

- `POST /api/chat/send` - Send message to agent
- `GET /api/chat/sessions` - Retrieve active sessions
- `POST /api/chat/clear-session` - Clear conversation history
- `GET /api/chat/agents` - List available agents

### Audio Endpoints

- `POST /api/audio/transcribe` - Convert speech to text
- `POST /api/audio/tts` - Generate speech from text
- `GET /api/audio/voices` - Available voice models

### Document Endpoints

- `POST /api/rag/upload` - Upload and index documents
- `POST /api/rag/retrieve` - Semantic document search
- `GET /api/rag/agents/{agent}/documents` - List documents
- `DELETE /api/rag/agents/{agent}/documents/{filename}` - Remove document

### Metrics Endpoints

- `GET /api/audio/metrics` - Audio processing statistics
- `GET /api/chat/metrics` - Conversation analytics
- `GET /api/rag/metrics` - RAG pipeline performance

## Configuration

### Agent Customization

Edit `app/config.py` to customize agent behavior:

```python
AGENT_CONFIGS = {
    "real_estate": {
        "system_prompt": "You are an expert real estate advisor...",
        "model": "gpt-4",
        "temperature": 0.7,
        "tools": ["weather", "calculator"]
    }
}
```

### Document Processing

Configure chunking and embedding parameters:

```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"
```

## Performance & Scalability

### Current Performance

- **STT Latency**: < 2s for 30s audio clips
- **LLM Response**: 1-3s average
- **Document Retrieval**: < 500ms for 10K chunks
- **Concurrent Users**: Tested up to 50 simultaneous sessions

### Scaling Recommendations

#### Horizontal Scaling
- Deploy behind NGINX or HAProxy load balancer
- Use Redis for distributed session management
- Implement request queuing with Celery/RabbitMQ

#### Vertical Optimization
- Switch to Pinecone or Weaviate for vector storage
- Implement response caching with Redis
- Use async processing for document uploads

#### Production Deployment
```yaml
# docker-compose.production.yml
services:
  app:
    replicas: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Security Best Practices

- ✅ Store API keys in environment variables
- ✅ Validate and sanitize all file uploads
- ✅ Implement rate limiting (recommended: 100 req/min per user)
- ✅ Use HTTPS in production environments
- ✅ Add authentication middleware for sensitive deployments
- ✅ Regularly rotate API keys
- ✅ Enable CORS only for trusted domains

## Testing

Run the test suite:

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Full test suite with coverage
pytest --cov=app --cov-report=html tests/
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Roadmap

- [ ] Multi-language support for voice interactions
- [ ] Integration with enterprise knowledge bases (SharePoint, Confluence)
- [ ] Advanced analytics dashboard with Grafana
- [ ] Mobile application (iOS/Android)
- [ ] WebSocket support for real-time streaming responses
- [ ] Custom agent training interface
- [ ] Enhanced security with OAuth2/JWT authentication

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI](https://openai.com/) - GPT-4, Whisper, and TTS models
- [LangChain](https://langchain.com/) - Agent framework and tooling
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework

## Support

- 📖 [Documentation](https://github.com/yourusername/voice-ai-agent/wiki)
- 🐛 [Report Issues](https://github.com/yourusername/voice-ai-agent/issues)
- 💬 [Discussions](https://github.com/yourusername/voice-ai-agent/discussions)
- 📧 Email: support@yourproject.com

---

**Built with ❤️ by Multi AI agent orchestration**
