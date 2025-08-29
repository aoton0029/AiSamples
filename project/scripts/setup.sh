# Pull all required Docker images for the project
echo "Pulling Docker images for the project..."

echo "1. Pulling Milvus..."
docker pull milvusdb/milvus:latest

echo "2. Pulling MongoDB..."
docker pull mongo:latest

echo "3. Pulling Neo4j..."
docker pull neo4j:latest

echo "4. Pulling Redis..."
docker pull redis:latest

echo "5. Pulling n8n..."
docker pull n8nio/n8n:latest

echo "6. Pulling ollama..."
docker pull ollama/ollama:latest

echo "7. Pulling python3.13-slim..."
docker pull python:3.13-slim

echo "All Docker images have been pulled successfully!"