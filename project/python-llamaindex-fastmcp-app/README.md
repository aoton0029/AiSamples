# Python LlamaIndex and FastMCP Application

This project sets up a Python application using FastAPI, LlamaIndex, and FastMCP, which interacts with various databases and services defined in a Docker Compose setup.

## Project Structure

```
python-llamaindex-fastmcp-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── app
│   │   ├── __init__.py        # Marks the app directory as a package
│   │   ├── api
│   │   │   ├── __init__.py    # Marks the api directory as a package
│   │   │   └── routes.py      # Defines API routes for the application
│   │   ├── services
│   │   │   ├── __init__.py    # Marks the services directory as a package
│   │   │   ├── ollama_service.py  # Interacts with the Ollama service
│   │   │   ├── milvus_service.py   # Interacts with the Milvus database
│   │   │   ├── neo4j_service.py     # Interacts with the Neo4j database
│   │   │   ├── redis_service.py      # Interacts with the Redis database
│   │   │   ├── mongodb_service.py    # Interacts with the MongoDB database
│   │   │   └── postgres_service.py   # Interacts with the PostgreSQL database
│   │   └── config
│   │       ├── __init__.py        # Marks the config directory as a package
│   │       └── settings.py        # Configuration settings for the application
├── docker-compose.yml            # Defines services, networks, and volumes for Docker
├── Dockerfile                     # Instructions to build the Docker image
├── requirements.txt               # Lists Python dependencies
├── .env                           # Contains environment variables
└── README.md                      # Documentation for the project
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd python-llamaindex-fastmcp-app
   ```

2. **Build the Docker Image**
   ```bash
   docker-compose build
   ```

3. **Run the Application**
   ```bash
   docker-compose up
   ```

4. **Access the API**
   The FastAPI application will be available at `http://localhost:5678`.

## Usage Examples

- **Interacting with Ollama Service**
  - Endpoint: `/ollama`
  - Method: `POST`
  - Description: Send requests to the Ollama service.

- **Interacting with Milvus Database**
  - Endpoint: `/milvus`
  - Method: `GET`
  - Description: Retrieve data from the Milvus database.

## Dependencies

- FastAPI
- LlamaIndex
- FastMCP
- Database drivers for PostgreSQL, MongoDB, Neo4j, Redis, and Milvus.

## Environment Variables

Make sure to set the necessary environment variables in the `.env` file for database connections and API keys.

## License

This project is licensed under the MIT License.