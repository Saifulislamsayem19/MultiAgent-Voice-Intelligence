# API Documentation

## Base URL

```
http://localhost:8000
```

For production deployments, replace with your domain.

## Table of Contents
- [Authentication](#authentication)
- [Chat API](#chat-api)
- [Audio API](#audio-api)
- [RAG API](#rag-api)
- [Metrics API](#metrics-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Authentication

Currently, the API does not require authentication. For production use, implement JWT-based authentication:

```bash
# Future implementation
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/chat/send
```

## Chat API

### Send Message

Send a message to a specific agent or let the orchestrator route it automatically.

**Endpoint**: `POST /api/chat/send`

**Request Body**:
```json
{
  "message": "What are the current trends in commercial real estate?",
  "agent": "real_estate",
  "session_id": "user_123",
  "include_context": true
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message | string | Yes | User's query or message |
| agent | string | No | Specific agent to use (real_estate, medical, ai_ml, sales, education). If omitted, orchestrator selects |
| session_id | string | Yes | Unique session identifier for conversation continuity |
| include_context | boolean | No | Whether to include RAG context (default: true) |

**Response**:
```json
{
  "response": "Based on recent market data, commercial real estate is experiencing...",
  "agent": "real_estate",
  "session_id": "user_123",
  "timestamp": "2025-11-22T10:30:00Z",
  "confidence": 0.92,
  "sources_used": ["document1.pdf", "document2.pdf"],
  "tokens_used": 450
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the symptoms of flu?",
    "agent": "medical",
    "session_id": "session_001"
  }'
```

**Response Codes**:
- `200`: Success
- `400`: Invalid request parameters
- `429`: Rate limit exceeded
- `500`: Internal server error

---

### Get Chat Sessions

Retrieve all active chat sessions.

**Endpoint**: `GET /api/chat/sessions`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Maximum number of sessions to return (default: 50) |
| offset | integer | No | Pagination offset (default: 0) |

**Response**:
```json
{
  "sessions": [
    {
      "session_id": "user_123",
      "agent": "real_estate",
      "message_count": 15,
      "created_at": "2025-11-22T09:00:00Z",
      "last_activity": "2025-11-22T10:30:00Z"
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl http://localhost:8000/api/chat/sessions?limit=10
```

---

### Clear Session

Clear conversation history for a specific session.

**Endpoint**: `POST /api/chat/clear-session`

**Request Body**:
```json
{
  "session_id": "user_123"
}
```

**Response**:
```json
{
  "message": "Session cleared successfully",
  "session_id": "user_123"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/chat/clear-session \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user_123"}'
```

---

### Get Available Agents

List all available specialized agents.

**Endpoint**: `GET /api/chat/agents`

**Response**:
```json
{
  "agents": [
    {
      "id": "real_estate",
      "name": "Real Estate Agent",
      "description": "Expert in property markets, real estate trends, and investment",
      "capabilities": ["market_analysis", "property_valuation", "investment_advice"],
      "status": "active"
    },
    {
      "id": "medical",
      "name": "Medical Agent",
      "description": "Healthcare information and wellness guidance",
      "capabilities": ["symptom_checker", "health_info", "wellness_tips"],
      "status": "active"
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/chat/agents
```

---

## Audio API

### Transcribe Audio

Convert speech to text using OpenAI Whisper.

**Endpoint**: `POST /api/audio/transcribe`

**Request**: Multipart form data

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | Audio file (wav, mp3, m4a, etc.) |
| language | string | No | Language code (e.g., 'en', 'es'). Auto-detect if omitted |

**Supported Formats**: WAV, MP3, M4A, FLAC, OGG

**Max File Size**: 25 MB

**Response**:
```json
{
  "text": "What are the latest trends in artificial intelligence?",
  "language": "en",
  "duration": 3.5,
  "confidence": 0.96
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/audio/transcribe \
  -F "file=@recording.wav" \
  -F "language=en"
```

**Response Codes**:
- `200`: Success
- `400`: Invalid file format or size
- `500`: Transcription failed

---

### Text-to-Speech

Convert text to natural speech.

**Endpoint**: `POST /api/audio/tts`

**Request Body**:
```json
{
  "text": "Hello, this is a test of the text to speech system.",
  "voice": "alloy",
  "speed": 1.0
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | Yes | Text to convert (max 4096 characters) |
| voice | string | No | Voice model (alloy, echo, fable, onyx, nova, shimmer) |
| speed | float | No | Speech speed (0.25 to 4.0, default: 1.0) |

**Response**: Binary audio data (MP3)

**Example**:
```bash
curl -X POST http://localhost:8000/api/audio/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to the voice AI system",
    "voice": "nova",
    "speed": 1.0
  }' \
  --output response.mp3
```

---

### Get Available Voices

List all available TTS voices.

**Endpoint**: `GET /api/audio/voices`

**Response**:
```json
{
  "voices": [
    {
      "id": "alloy",
      "name": "Alloy",
      "description": "Neutral and balanced voice"
    },
    {
      "id": "echo",
      "name": "Echo",
      "description": "Male voice with clarity"
    },
    {
      "id": "nova",
      "name": "Nova",
      "description": "Female voice with warmth"
    }
  ]
}
```

---

## RAG API

### Upload Document

Upload and index a document for an agent's knowledge base.

**Endpoint**: `POST /api/rag/upload`

**Request**: Multipart form data

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | Document file (PDF, DOCX, TXT, MD) |
| agent | string | Yes | Target agent (real_estate, medical, ai_ml, sales, education) |
| metadata | json | No | Additional document metadata |

**Supported Formats**: PDF, DOCX, TXT, MD

**Max File Size**: 10 MB

**Response**:
```json
{
  "message": "Document uploaded successfully",
  "filename": "market_report_2025.pdf",
  "agent": "real_estate",
  "chunks_created": 45,
  "processing_time": 2.3
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/rag/upload \
  -F "file=@report.pdf" \
  -F "agent=real_estate" \
  -F 'metadata={"category":"market_analysis","year":2025}'
```

---

### Retrieve Documents

Perform semantic search across an agent's knowledge base.

**Endpoint**: `POST /api/rag/retrieve`

**Request Body**:
```json
{
  "query": "What are the key factors affecting property values?",
  "agent": "real_estate",
  "top_k": 5
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Search query |
| agent | string | Yes | Agent to search within |
| top_k | integer | No | Number of results to return (default: 5, max: 20) |

**Response**:
```json
{
  "results": [
    {
      "content": "Property values are primarily influenced by location, market demand...",
      "source": "market_report_2025.pdf",
      "score": 0.89,
      "metadata": {
        "page": 12,
        "category": "market_analysis"
      }
    }
  ],
  "query": "What are the key factors affecting property values?",
  "total_results": 5
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes management",
    "agent": "medical",
    "top_k": 3
  }'
```

---

### List Agent Documents

Get all documents indexed for a specific agent.

**Endpoint**: `GET /api/rag/agents/{agent}/documents`

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| agent | string | Agent identifier |

**Response**:
```json
{
  "agent": "real_estate",
  "documents": [
    {
      "filename": "market_report_2025.pdf",
      "uploaded_at": "2025-11-22T08:00:00Z",
      "size_kb": 523,
      "chunks": 45,
      "metadata": {
        "category": "market_analysis"
      }
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl http://localhost:8000/api/rag/agents/real_estate/documents
```

---

### Delete Document

Remove a document from an agent's knowledge base.

**Endpoint**: `DELETE /api/rag/agents/{agent}/documents/{filename}`

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| agent | string | Agent identifier |
| filename | string | Document filename |

**Response**:
```json
{
  "message": "Document deleted successfully",
  "filename": "market_report_2025.pdf",
  "agent": "real_estate"
}
```

**Example**:
```bash
curl -X DELETE \
  http://localhost:8000/api/rag/agents/real_estate/documents/market_report_2025.pdf
```

---

## Metrics API

### Audio Metrics

Get audio processing performance metrics.

**Endpoint**: `GET /api/audio/metrics`

**Response**:
```json
{
  "total_transcriptions": 1523,
  "total_tts_requests": 891,
  "average_transcription_time": 1.8,
  "average_tts_time": 0.9,
  "total_audio_duration": 12345.6,
  "most_used_voice": "nova"
}
```

---

### Chat Metrics

Get conversation and agent usage metrics.

**Endpoint**: `GET /api/chat/metrics`

**Response**:
```json
{
  "total_messages": 5432,
  "total_sessions": 234,
  "average_response_time": 2.1,
  "agent_usage": {
    "real_estate": 1234,
    "medical": 987,
    "ai_ml": 876,
    "sales": 654,
    "education": 543,
    "orchestrator": 1138
  },
  "average_message_length": 85,
  "total_tokens_used": 234567
}
```

---

### RAG Metrics

Get document processing and retrieval metrics.

**Endpoint**: `GET /api/rag/metrics`

**Response**:
```json
{
  "total_documents": 145,
  "total_chunks": 12345,
  "documents_by_agent": {
    "real_estate": 35,
    "medical": 28,
    "ai_ml": 42,
    "sales": 20,
    "education": 20
  },
  "average_retrieval_time": 0.35,
  "total_queries": 3456,
  "cache_hit_rate": 0.67
}
```

---

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "agent",
      "issue": "Agent 'invalid_agent' does not exist"
    }
  },
  "timestamp": "2025-11-22T10:30:00Z",
  "path": "/api/chat/send"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request parameters |
| AUTHENTICATION_ERROR | 401 | Missing or invalid authentication |
| AUTHORIZATION_ERROR | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | External service unavailable |

---

## Rate Limiting

**Current Limits**:
- 100 requests per minute per IP address
- 1000 requests per hour per IP address

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1637582400
```

When rate limit is exceeded:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45
  }
}
```

---

## Webhooks

**Coming Soon**: Webhook support for asynchronous document processing and long-running queries.

---

## SDKs and Client Libraries

### Python
```python
from voice_ai_client import VoiceAIClient

client = VoiceAIClient(base_url="http://localhost:8000")

# Send message
response = client.chat.send(
    message="What are the latest AI trends?",
    agent="ai_ml",
    session_id="session_001"
)

# Upload document
client.rag.upload(
    file_path="document.pdf",
    agent="real_estate"
)
```

### JavaScript
```javascript
import { VoiceAIClient } from 'voice-ai-client';

const client = new VoiceAIClient({ baseUrl: 'http://localhost:8000' });

// Send message
const response = await client.chat.send({
  message: 'What are the latest AI trends?',
  agent: 'ai_ml',
  sessionId: 'session_001'
});

// Upload document
await client.rag.upload({
  file: documentFile,
  agent: 'real_estate'
});
```

---

## API Versioning

The API uses URL-based versioning. Current version: `v1` (default)

Future versions will be accessible via:
```
http://localhost:8000/api/v2/chat/send
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Support

For API support and questions:
- GitHub Issues: [Report Issue](https://github.com/Saifulislamsayem19/MultiAgent-Voice-Intelligence/issues)
- Documentation: [README.md](../README.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
