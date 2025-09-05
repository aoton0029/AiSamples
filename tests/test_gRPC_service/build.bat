@echo off

REM Build and generate protobuf files for all services
echo Building MCP Microservices...

REM Generate protobuf files
echo Generating protobuf files...
python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/mcp_service.proto

REM Copy generated files to each service
set services=service_chunking service_tokenize service_embedding service_indexing service_rag service_context_builder service_inference service_tuning orchestrator

for %%s in (%services%) do (
    echo Copying proto files to %%s...
    if not exist ".\%%s\proto" mkdir ".\%%s\proto"
    copy ".\proto\*.py" ".\%%s\proto\"
)

REM Build all services
echo Building all services...
docker-compose build

echo MCP Microservices build completed!
echo.
echo To start all services:
echo docker-compose up -d
echo.
echo To check service health:
echo curl http://localhost:3000/health
