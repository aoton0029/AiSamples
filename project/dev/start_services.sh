#!/bin/bash

# Start all MCP services
echo "Starting MCP Microservices..."

# Start services in background
echo "Starting Tokenize Service..."
cd service_tokenize && python main.py &
TOKENIZE_PID=$!

echo "Starting Embedding Service..."
cd ../service_embedding && python main.py &
EMBEDDING_PID=$!

echo "Starting Chunking Service..."
cd ../service_chunking && python main.py &
CHUNKING_PID=$!

echo "Starting RAG Service..."
cd ../service_rag && python main.py &
RAG_PID=$!

echo "Starting Inference Service..."
cd ../service_inference && python main.py &
INFERENCE_PID=$!

echo "Starting Indexing Service..."
cd ../service_indexing && python main.py &
INDEXING_PID=$!

echo "Starting Context Builder Service..."
cd ../service_context_builder && python main.py &
CONTEXT_PID=$!

echo "Starting Tuning Service..."
cd ../service_tuning && python main.py &
TUNING_PID=$!

echo "All services started!"
echo "PIDs: Tokenize=$TOKENIZE_PID, Embedding=$EMBEDDING_PID, Chunking=$CHUNKING_PID"
echo "      RAG=$RAG_PID, Inference=$INFERENCE_PID, Indexing=$INDEXING_PID"
echo "      Context=$CONTEXT_PID, Tuning=$TUNING_PID"

# Wait for all services
wait
