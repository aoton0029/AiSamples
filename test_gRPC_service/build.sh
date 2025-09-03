#!/bin/bash

# Build and generate protobuf files for all services
echo "Building MCP Microservices..."

# Generate protobuf files
echo "Generating protobuf files..."
python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/mcp_service.proto

# Copy generated files to each service
services=("service_chunking" "service_tokenize" "service_embedding" "service_indexing" "service_rag" "service_context_builder" "service_inference" "service_tuning" "orchestrator")

for service in "${services[@]}"; do
    echo "Copying proto files to $service..."
    mkdir -p "./$service/proto"
    cp ./proto/*.py "./$service/proto/"
done

# Build all services
echo "Building all services..."
docker-compose build

echo "MCP Microservices build completed!"
echo ""
echo "To start all services:"
echo "docker-compose up -d"
echo ""
echo "To check service health:"
echo "curl http://localhost:3000/health"
