# HL Education API - IELTS Assessment Service

AI-powered IELTS Writing and Speaking assessment service built with FastAPI.

## Features

- **AI-Powered Scoring**: Automated IELTS Writing and Speaking assessment using multiple AI providers
- **Multi-Provider Support**: OpenAI, Google GenAI, and Mistral AI integration with failover
- **OTP Authentication**: Secure 8-digit TOTP authentication system
- **Provider Management**: Dynamic AI provider switching and configuration
- **RESTful API**: Comprehensive endpoints for assessment operations
- **Auto Documentation**: Interactive Swagger/OpenAPI documentation

## Quick Start

### Prerequisites
- Python 3.11+
- MySQL Database
- AI Provider API Keys (OpenAI/Google/Mistral)

### Installation

1. **Clone and setup environment**
```bash
git clone https://github.com/CoderFake/ai-hledu.git
cd HleduApi
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the service**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables
```env
# Application
ENV=dev
NAME=Hledu API
VERSION=0.0.1

# Database
DB__DSN=mysql+aiomysql://user:password@yourhost/hledu

# OTP Authentication (32 characters)
OTP__SECRET_KEY=your-32-character-secret-key-here
OTP__PERIOD=30
OTP__DIGITS=8

# Documentation
DOCS__USERNAME=admin
DOCS__PASSWORD=admin123

# CORS
CORS__ORIGINS=https://yourdomain.com,http://yourhost:3000
```

## API Endpoints

### Provider Management
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/provider/current` | Get active AI provider | Optional |
| PUT | `/provider/update` | Switch AI provider | Required |

### Authentication
- **Header**: `X-OTP-Token: 12345678`
- **Format**: 8-digit TOTP code
- **Validity**: 30 seconds

## Development

### Project Structure
```
HleduApi/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── model/            # Database models
│   ├── service/          # Business logic
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI app
├── config/               # Configuration files
├── requirements.txt      # Dependencies
└── docker-compose.yml    # Docker setup
```

### Running with Docker
```bash
# Development with hot reload
docker-compose up -d --build

# Production build
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### API Documentation
- **Swagger UI**: `http://localhost:12001/docs`
- **ReDoc**: `http://localhost:12001/redoc`

## Docker Setup

### Docker Commands
```bash
# Start services
docker-compose up -d

# Build and start (after code changes)
docker-compose up -d --build

# View running containers
docker-compose ps

# Access API container shell
docker-compose exec api bash

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

### Production Docker Setup
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d --build
```

## Database Setup

### Models
- **Provider**: AI service providers (OpenAI, Google, Mistral)
- **AIModels**: Available models per provider
- **Assessment**: IELTS test results and scores

### Migration
```sql
-- Create providers table
CREATE TABLE provider (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(150) UNIQUE,
    api_key VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT FALSE
);

-- Create AI models table
CREATE TABLE ai_models (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(150) UNIQUE,
    provider_id CHAR(36),
    is_active BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (provider_id) REFERENCES provider(id)
);
```

## Deployment

### Production Setup
```bash
# Using Gunicorn
ENV=prod gunicorn app.main:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker
```

### Environment-Specific Configuration
- **Development**: Auto-reload, open docs, CORS=*
- **Staging**: Basic auth docs, limited CORS
- **Production**: Secure auth, production CORS

## AI Provider Integration

### Supported Providers
- **OpenAI**: GPT models for assessment
- **Google GenAI**: Gemini models
- **Mistral AI**: Mistral models

### Provider Management
1. Add provider via database
2. Configure API keys
3. Set active status
4. Switch providers via API

## Security

- **OTP Authentication**: Time-based 8-digit codes
- **Basic Auth**: Documentation protection
- **CORS**: Configurable origin restrictions
- **API Key**: Secure AI provider authentication

## License

MIT License - HL Education

---

**HL Education API** - Empowering IELTS assessment through AI technology