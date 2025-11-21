# Voice-Enabled AI Agent System

A comprehensive voice-enabled AI agent system with RAG capabilities, multi-agent orchestration, and dynamic function calls. The system allows users to interact via voice or text, retrieve information from documents, and receive real-time responses.

## 🌟 Features

### Core Capabilities
- **Voice Interaction**: Speech-to-text (STT) and text-to-speech (TTS) using OpenAI's Whisper and TTS models
- **Multi-Agent System**: 5 specialized agents + 1 orchestrator for intelligent routing
- **RAG Pipeline**: Document embedding and retrieval using FAISS vector database
- **Dynamic Function Calls**: Weather API, calculator, timezone, and more
- **Real-time Metrics**: Comprehensive logging and performance monitoring

### Specialized Agents
1. **Real Estate Agent**: Property information, market analysis, investment advice
2. **Medical Agent**: Health information, symptom checking (with disclaimers)
3. **AI/ML Agent**: Technical AI/ML topics, code examples, model recommendations
4. **Sales Agent**: Sales strategies, CRM insights, business development
5. **Education Agent**: Learning resources, study plans, educational guidance
6. **Orchestrator**: Automatically routes queries to the best agent

## 🚀 Quick Start

### Prerequisites
- Python 3.12
- OpenAI API Key
- WeatherAPI.com API Key (free tier available)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd voice-ai-agent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY=your_openai_api_key
# - WEATHER_API_KEY=your_weather_api_key
```

5. **Run the application**
```bash
python main.py
```

The application will be available at `http://localhost:8000`

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop the application
docker-compose down
```

### Using Docker directly
```bash
# Build image
docker build -t voice-ai-agent .

# Run container
docker run -p 8000:8000 --env-file .env voice-ai-agent
```

## 📁 Project Structure

```
voice-ai-agent/
├── app/
│   ├── config.py              # Configuration and settings
│   ├── routers/               # API endpoints
│   │   ├── audio.py           # STT/TTS endpoints
│   │   ├── chat.py            # Chat interaction endpoints
│   │   └── rag.py             # Document upload/retrieval
│   └── services/              # Core services
│       ├── document_loader.py # Document processing
│       ├── vector_store.py    # FAISS vector store management
│       ├── orchestrator.py    # Agent routing logic
│       ├── specialized_agents.py # Domain-specific agents
│       ├── tools.py           # Dynamic function tools
│       └── metrics_logger.py  # Performance metrics
├── dataset/                   # Document storage (organized by agent)
│   ├── real_estate/          # Real estate documents
│   ├── medical/              # Medical documents
│   ├── ai_ml/                # AI/ML documents
│   ├── sales/                # Sales documents
│   └── education/            # Education documents
├── static/                    # Frontend assets
│   ├── css/
│   └── js/
├── templates/                 # HTML templates
├── vector_stores/             # FAISS index storage
├── logs/                      # Application logs
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
└── README.md                  # This file
```

## 📚 Document Management

### Uploading Documents
1. Select the target agent in the upload section
2. Choose a document (PDF, TXT, DOCX, MD, CSV)
3. Click upload - the document will be processed and indexed

### Supported Formats
- PDF (.pdf)
- Text (.txt)
- Word (.docx, .doc)
- Markdown (.md)
- CSV (.csv)

### Document Organization
Place documents in the appropriate folder under `dataset/`:
- `dataset/real_estate/` - Real estate related documents
- `dataset/medical/` - Medical and health documents
- `dataset/ai_ml/` - AI/ML technical documents
- `dataset/sales/` - Sales and business documents
- `dataset/education/` - Educational materials

## 🔧 API Endpoints

### Audio Processing
- `POST /api/audio/transcribe` - Convert speech to text
- `POST /api/audio/tts` - Convert text to speech
- `GET /api/audio/voices` - Get available TTS voices

### Chat Interaction
- `POST /api/chat/send` - Send message and get response
- `GET /api/chat/sessions` - List active sessions
- `POST /api/chat/clear-session` - Clear a session
- `GET /api/chat/agents` - List available agents

### Document Management
- `POST /api/rag/upload` - Upload and process document
- `POST /api/rag/retrieve` - Retrieve relevant documents
- `GET /api/rag/agents/{agent}/documents` - List agent documents
- `DELETE /api/rag/agents/{agent}/documents/{filename}` - Delete document

### Metrics
- `GET /api/audio/metrics` - Audio processing metrics
- `GET /api/chat/metrics` - Chat interaction metrics
- `GET /api/rag/metrics` - RAG system metrics

## 📊 Performance Metrics

The system tracks and logs the following metrics:
- **STT Performance**: Transcription time, file size, accuracy
- **TTS Performance**: Generation time, text length, audio size
- **Chat Response Time**: Agent processing, token usage
- **Document Retrieval**: Query time, relevance scores
- **Document Processing**: Chunking time, vector embedding

Access metrics via:
- Web UI: Click the metrics button in the header
- API: Call the metrics endpoints
- Logs: Check `logs/metrics.jsonl`

## 🔐 Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **File Uploads**: Validate file types and sizes
3. **Rate Limiting**: Implement rate limiting in production
4. **HTTPS**: Use HTTPS in production deployments
5. **Authentication**: Add authentication for production use

## 🛠️ Configuration

### Environment Variables
```env
# Required
OPENAI_API_KEY=your_key
WEATHER_API_KEY=your_key

# Optional
API_KEY=custom_api_key
HOST=0.0.0.0
PORT=8000
```

### Agent Configuration
Edit `app/config.py` to customize:
- Agent system prompts
- Tool availability
- Model parameters
- Chunk sizes for document processing

## 📈 Scaling Considerations

### For Multiple Users
1. **Session Management**: Use Redis for session storage
2. **Vector Store**: Consider Pinecone or Weaviate for cloud deployment
3. **Load Balancing**: Deploy multiple instances behind a load balancer
4. **Caching**: Implement response caching for common queries

### For Large Document Sets
1. **Batch Processing**: Process documents in batches
2. **Async Processing**: Use Celery for background tasks
3. **Optimized Embeddings**: Use smaller embedding models if needed
4. **Index Sharding**: Split vector stores by domain

## 🧪 Testing

### Running Tests
```bash
pytest tests/ -v
```

### Test Coverage
```bash
pytest --cov=app tests/
```

## 📝 Google Colab Notebook

For testing without local setup, use the provided Colab notebook:

1. Open `voice_ai_agent_demo.ipynb` in Google Colab
2. Replace API keys in the designated cells
3. Run all cells to start the system
4. Access the web interface via ngrok URL

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 and Whisper models
- LangChain for the agent framework
- FAISS for vector similarity search
- WeatherAPI.com for weather data

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review the API documentation at `/docs` endpoint


