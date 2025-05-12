# News RAG Chatbot - Backend

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115.12-blue.svg)

The backend component of the News RAG Chatbot application, built with FastAPI and providing a powerful RAG (Retrieval-Augmented Generation) pipeline for answering questions about news articles.

## Features

- **🔍 Advanced RAG Pipeline**: Leverages Jina embeddings and Groq API for accurate news-based responses
- **📰 Automatic News Ingestion**: Fetches and processes articles from FirstPost RSS feed
- **⚡ FastAPI Backend**: High-performance API with WebSocket support for real-time messaging
- **💾 Flexible Storage**: Redis for chat history with in-memory fallback, Qdrant for vector storage
- **👤 Session Management**: User interactions tracked with unique session IDs
- **🔄 Real-time Responses**: Token-by-token streaming for a responsive user experience

## Architecture

The backend consists of several key components:

1. **FastAPI Server**: Handles HTTP and WebSocket requests
2. **News Ingestion Service**: Fetches and processes news articles from RSS feeds
3. **Embedding Service**: Generates vector embeddings for articles and queries using Jina AI
4. **Vector Store**: Qdrant for storing and retrieving vector embeddings
5. **LLM Integration**: Groq API for generating contextually relevant responses
6. **Chat History Manager**: Redis-based storage for conversation history

## Prerequisites

- **Python 3.9+**
- **Redis** (optional, will fallback to in-memory storage)
- **Qdrant** (optional, will fallback to in-memory storage)
- **API Keys**:
  - [Groq API Key](https://console.groq.com/) for LLM access
  - [Jina AI API Key](https://jina.ai/) for embeddings

## Installation

1. Create and activate a Python virtual environment:

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory (copy from `.env.example`):

```bash
cp .env.example .env
```

4. Edit the `.env` file to add your API keys and configuration:

```
GROQ_API_KEY=your-groq-api-key
JINA_API_KEY=your-jina-api-key
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `GROQ_API_KEY` | Groq API key for LLM access | None (Required) |
| `JINA_API_KEY` | Jina AI API key for embeddings | None (Required) |
| `REDIS_HOST` | Redis server hostname | localhost |
| `REDIS_PORT` | Redis server port | 6379 |
| `QDRANT_HOST` | Qdrant server hostname | localhost |
| `QDRANT_PORT` | Qdrant server port | 6333 |
| `QDRANT_MODE` | Qdrant mode (memory or server) | memory |
| `CORS_ORIGINS` | Allowed origins for CORS | * |

## Usage

Start the backend server:

```bash
uvicorn app.main:app --reload --port 8000
```

The server will be available at http://localhost:8000.

## API Documentation

The API is documented using OpenAPI (Swagger). When the backend server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/session` | POST | Create a new chat session |
| `/api/refresh` | POST | Refresh news articles |
| `/ws/{session_id}` | WebSocket | Real-time chat communication |

## Docker Deployment

You can build and run the backend using Docker:

```bash
docker build -t news-rag-backend .
docker run -p 8000:8000 news-rag-backend
```

For more detailed deployment instructions, refer to the main project repository.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
