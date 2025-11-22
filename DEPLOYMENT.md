# Deployment Guide

## Overview

This guide covers deploying MultiAgent Voice Intelligence to production environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployments](#cloud-deployments)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)

## Prerequisites

### System Requirements

**Minimum**:
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space
- Python 3.12+

**Recommended**:
- 4+ CPU cores
- 8+ GB RAM
- 50+ GB SSD storage
- Load balancer
- Redis for session management

### Required Services

- OpenAI API access
- WeatherAPI key (optional)
- Domain name (for production)
- SSL certificate

## Environment Setup

### 1. Environment Variables

Create production `.env`:

```bash
# API Keys
OPENAI_API_KEY=sk-proj-your-production-key
WEATHER_API_KEY=your-weather-api-key

# Application
HOST=0.0.0.0
PORT=8000
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-super-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Database (if using)
DATABASE_URL=postgresql://user:pass@host:5432/voiceai

# Redis (recommended for production)
REDIS_URL=redis://redis:6379/0

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=30
MAX_FILE_SIZE=10485760  # 10MB

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Monitoring
SENTRY_DSN=your-sentry-dsn  # Optional
```

### 2. Security Configuration

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set restrictive permissions on .env
chmod 600 .env

# Never commit .env to version control
echo ".env" >> .gitignore
```

## Deployment Options

### Option 1: Direct Python Deployment

```bash
# Clone repository
git clone https://github.com/Saifulislamsayem19/MultiAgent-Voice-Intelligence.git
cd MultiAgent-Voice-Intelligence

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with production values

# Run with Gunicorn (production WSGI server)
pip install gunicorn uvicorn[standard]

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/voice-ai/access.log \
  --error-logfile /var/log/voice-ai/error.log
```

### Option 2: Systemd Service

Create `/etc/systemd/system/voice-ai.service`:

```ini
[Unit]
Description=Voice AI Agent Service
After=network.target

[Service]
Type=notify
User=voiceai
Group=voiceai
WorkingDirectory=/opt/voice-ai
Environment="PATH=/opt/voice-ai/venv/bin"
EnvironmentFile=/opt/voice-ai/.env

ExecStart=/opt/voice-ai/venv/bin/gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-ai
sudo systemctl start voice-ai
sudo systemctl status voice-ai
```

## Docker Deployment

### Single Container

```bash
# Build image
docker build -t voice-ai:latest .

# Run container
docker run -d \
  --name voice-ai \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/vector_stores:/app/vector_stores \
  --restart unless-stopped \
  voice-ai:latest
```

### Docker Compose (Recommended)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    image: voice-ai:latest
    container_name: voice-ai-app
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./vector_stores:/app/vector_stores
      - ./dataset:/app/dataset
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  redis:
    image: redis:7-alpine
    container_name: voice-ai-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    container_name: voice-ai-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: voice-ai-network
```

Deploy:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream voice_ai {
        server app:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;

    server {
        listen 80;
        server_name yourdomain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/certificate.crt;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Max upload size
        client_max_body_size 10M;

        # Proxy settings
        location / {
            proxy_pass http://voice_ai;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # API rate limiting
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://voice_ai;
        }

        # Health check endpoint (no rate limit)
        location /health {
            proxy_pass http://voice_ai;
            access_log off;
        }
    }
}
```

## Cloud Deployments

### AWS Deployment

#### Using EC2

1. **Launch EC2 Instance**:
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t3.medium (or larger)
   - Storage: 30 GB GP3
   - Security Group: Allow ports 22, 80, 443

2. **Setup**:
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Clone and deploy
git clone https://github.com/Saifulislamsayem19/MultiAgent-Voice-Intelligence.git
cd MultiAgent-Voice-Intelligence
cp .env.example .env
# Edit .env with production values
docker-compose -f docker-compose.prod.yml up -d
```

#### Using ECS (Fargate)

Create `task-definition.json`:

```json
{
  "family": "voice-ai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "voice-ai-app",
      "image": "your-ecr-repo/voice-ai:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENV", "value": "production"},
        {"name": "HOST", "value": "0.0.0.0"},
        {"name": "PORT", "value": "8000"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/voice-ai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/voice-ai

# Deploy
gcloud run deploy voice-ai \
  --image gcr.io/YOUR_PROJECT/voice-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENV=production \
  --set-secrets OPENAI_API_KEY=openai-key:latest \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300
```

### Azure

#### Using Azure Container Instances

```bash
# Create resource group
az group create --name voice-ai-rg --location eastus

# Create container
az container create \
  --resource-group voice-ai-rg \
  --name voice-ai \
  --image your-registry.azurecr.io/voice-ai:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    ENV=production \
    HOST=0.0.0.0 \
  --secure-environment-variables \
    OPENAI_API_KEY=$OPENAI_KEY
```

## Monitoring & Logging

### Application Logging

Configure structured logging in `app/config.py`:

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# JSON formatter
formatter = jsonlogger.JsonFormatter(
    '%(timestamp)s %(level)s %(name)s %(message)s'
)

# Console handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

# File handler
file_handler = logging.FileHandler('/var/log/voice-ai/app.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
```

### Health Check Endpoint

Add to `main.py`:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### Prometheus Metrics

Install metrics library:

```bash
pip install prometheus-client
```

Add metrics endpoint:

```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### Error Tracking with Sentry

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    environment=os.getenv("ENV", "production"),
    traces_sample_rate=1.0,
)
```

## Backup & Recovery

### Database Backups

```bash
# Vector stores
tar -czf vector_stores_backup_$(date +%Y%m%d).tar.gz vector_stores/

# Upload to S3
aws s3 cp vector_stores_backup_*.tar.gz s3://your-backup-bucket/
```

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup vector stores
tar -czf $BACKUP_DIR/vectors_$DATE.tar.gz vector_stores/

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Upload to cloud storage
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Schedule with cron:

```bash
0 2 * * * /opt/voice-ai/backup.sh
```

## Scaling

### Horizontal Scaling

#### Docker Compose Scaling

```bash
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

#### Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voice-ai
  template:
    metadata:
      labels:
        app: voice-ai
    spec:
      containers:
      - name: voice-ai
        image: your-registry/voice-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENV
          value: "production"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: voice-ai-service
spec:
  selector:
    app: voice-ai
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Apply:

```bash
kubectl apply -f k8s-deployment.yaml
```

### Performance Optimization

1. **Enable caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    # Cache embeddings
    pass
```

2. **Use connection pooling**:
```python
from aiohttp import ClientSession

async with ClientSession() as session:
    # Reuse connections
    pass
```

3. **Optimize vector search**:
```python
# Use GPU-accelerated FAISS if available
import faiss
index = faiss.index_cpu_to_gpu(res, 0, index)
```

## Troubleshooting

### Common Issues

**Port already in use**:
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Out of memory**:
```bash
# Check memory usage
docker stats

# Increase container memory limits
docker update --memory 8g voice-ai
```

**SSL certificate errors**:
```bash
# Renew Let's Encrypt certificate
certbot renew --nginx
```

## Post-Deployment Checklist

- [ ] SSL/TLS configured and working
- [ ] Environment variables secured
- [ ] Backups automated and tested
- [ ] Monitoring and alerts configured
- [ ] Rate limiting enabled
- [ ] Health checks working
- [ ] Logs centralized
- [ ] Documentation updated
- [ ] Load testing completed
- [ ] Disaster recovery plan documented

---

For deployment support, open an issue on GitHub.
