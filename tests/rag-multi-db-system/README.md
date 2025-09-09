# RAG Multi-DB System

This project implements a system for associating documents with a vector database, document database, and graph database. It follows a structured approach to preprocess documents, generate embeddings, and manage data across multiple databases.

## Project Structure

```
rag-multi-db-system
├── src
│   ├── main.py                # Entry point for the application
│   ├── config                 # Configuration files
│   │   ├── settings.py        # Application settings
│   │   └── database_config.py  # Database connection configurations
│   ├── core                   # Core functionality
│   │   ├── redis_client.py    # Redis client for caching
│   │   ├── ollama_connector.py # Connector for Ollama server
│   │   ├── neo4j_client.py    # Neo4j client for graph operations
│   │   ├── multi_format_loader.py # Loader for various document formats
│   │   ├── mongo_client.py     # MongoDB client for document storage
│   │   └── milvus_client.py    # Milvus client for vector storage
│   ├── processors              # Document processing modules
│   │   ├── document_preprocessor.py # Functions for document preprocessing
│   │   ├── embedding_generator.py   # Functions for generating embeddings
│   │   ├── entity_extractor.py      # Functions for extracting entities
│   │   └── graph_builder.py         # Functions for building graph structures
│   ├── services                # Service layer for business logic
│   │   ├── document_service.py  # Services for document management
│   │   ├── vector_service.py    # Services for vector management
│   │   ├── graph_service.py     # Services for graph management
│   │   └── integration_service.py # Services for integrating databases
│   ├── api                     # API layer
│   │   ├── routes              # API routes
│   │   │   ├── documents.py    # Document management routes
│   │   │   ├── search.py       # Search routes
│   │   │   └── admin.py        # Administrative routes
│   │   └── middleware          # Middleware for API
│   │       └── auth.py         # Authentication middleware
│   ├── models                  # Data models
│   │   ├── document.py         # Document model
│   │   ├── entity.py           # Entity model
│   │   └── search_result.py     # Search result model
│   └── utils                   # Utility functions
│       ├── logger.py           # Logging utilities
│       ├── validators.py        # Validation functions
│       └── helpers.py          # Helper functions
├── tests                       # Test suite
│   ├── test_processors.py      # Tests for processors
│   ├── test_services.py        # Tests for services
│   ├── test_api.py             # Tests for API
│   └── fixtures                # Sample documents for testing
│       └── sample_documents
├── docker                      # Docker configuration
│   ├── docker-compose.yml      # Docker Compose file
│   ├── Dockerfile              # Dockerfile for building the application
│   └── init-scripts           # Initialization scripts for databases
│       ├── neo4j-init.cypher  # Neo4j initialization script
│       └── mongo-init.js      # MongoDB initialization script
├── requirements.txt            # Project dependencies
├── pytest.ini                  # Pytest configuration
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore file
└── README.md                  # Project documentation
```

## Features

- **Document Loading**: Supports multiple document formats (PDF, DOCX, JSON, etc.) through the `MultiFormatLoader`.
- **Preprocessing**: Documents are preprocessed to normalize and segment text.
- **Embedding Generation**: Generates embeddings for document chunks using the Ollama model.
- **Database Integration**: Manages documents in MongoDB, vectors in Milvus, and relationships in Neo4j.
- **API Access**: Provides RESTful API endpoints for document management and search functionalities.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd rag-multi-db-system
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your environment variables in a `.env` file based on the `.env.example` provided.

4. Start the application:
   ```
   python src/main.py
   ```

5. Access the API at `http://localhost:<port>`.

## Usage

- **Document Management**: Use the `/documents` endpoint to upload and retrieve documents.
- **Search**: Use the `/search` endpoint to perform searches on documents and vectors.
- **Admin Tasks**: Use the `/admin` endpoint for monitoring and managing the application.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.