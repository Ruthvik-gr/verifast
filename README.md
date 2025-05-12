# News RAG Chatbot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![React](https://img.shields.io/badge/react-18.2.0-blue.svg)

A modern chatbot application that uses RAG (Retrieval-Augmented Generation) to answer questions about recent news articles. The application fetches news from FirstPost RSS feed, processes them, and uses a combination of Jina embeddings and Groq API to provide accurate, contextually relevant responses.

## Project Components

This project is divided into two main components, each with its own detailed documentation:

- **[Backend](./backend/README.md)**: FastAPI application handling the RAG pipeline, news ingestion, and API endpoints
- **[Frontend](./frontend/README.md)**: React application providing the user interface

## Quick Start with Docker

The easiest way to run the entire application stack is using Docker Compose:

```bash
docker-compose up -d
```

This will start the frontend, backend, Redis, and Qdrant services. The application will be available at http://localhost.

## Prerequisites

- **Docker** and **Docker Compose** (for containerized deployment)
- **API Keys**:
  - [Groq API Key](https://console.groq.com/) for LLM access
  - [Jina AI API Key](https://jina.ai/) for embeddings

## Project Structure

```
./
├── backend/           # FastAPI backend application
├── frontend/          # React frontend application
├── docker-compose.yml # Docker Compose configuration
└── LICENSE            # MIT License
```

## Data Persistence

The Docker Compose setup includes volume mounts for Redis and Qdrant to ensure data persistence:

- `redis-data`: Stores chat history
- `qdrant-data`: Stores vector embeddings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
- Could be extended with:
  - Multi-source news integration
  - User authentication
  - Saved conversations
  - Fine-tuning for news-specific responses

## Troubleshooting

- If Redis connection fails, the application will automatically use in-memory storage
- If API keys are missing, mock services will be used with limited functionality
- Check logs for detailed error messages and connection issues
