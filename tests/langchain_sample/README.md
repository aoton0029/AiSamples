# AI Server with MCP Support

This server provides AI capabilities using LangChain, LlamaIndex, and Ollama, designed for integration with n8n workflows.

## Features

- **LLM Chat**: Direct interaction with Ollama models via LangChain
- **Document RAG**: Upload and query documents using LlamaIndex
- **MCP Support**: Model Context Protocol for advanced n8n integration
- **RESTful API**: Standard HTTP endpoints for easy integration

## Quick Start

1. **Start the services**:
   ```bash
   docker-compose up -d
   ```

2. **Pull an Ollama model**:
   ```bash
   docker exec ollama ollama pull llama2
   ```

3. **Test the API**:
   ```bash
   curl http://localhost:8000/health
   ```

## API Endpoints

### Chat
```http
POST /chat
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "context": "You are a helpful assistant"
}
```

### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

file: [your-document.txt]
```

### Query Documents
```http
POST /documents/query
Content-Type: application/json

{
  "query": "What is the main topic?",
  "top_k": 5
}
```

### MCP Endpoint (for n8n)
```http
POST /mcp
Content-Type: application/json

{
  "id": "req-123",
  "method": "chat",
  "params": {
    "message": "Hello world"
  }
}
```

## n8n Integration

Use the HTTP Request node in n8n to call these endpoints. The MCP endpoint provides a unified interface for all AI operations.

## Configuration

- Ollama URL: `http://ollama:11434` (in Docker) or `http://localhost:11434` (local)
- Default model: `llama2`
- Server port: `8000`
