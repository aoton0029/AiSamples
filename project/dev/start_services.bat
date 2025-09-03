@echo off
echo Starting MCP Microservices...

echo Starting Tokenize Service...
start /b cmd /c "cd service_tokenize && python main.py"

echo Starting Embedding Service...
start /b cmd /c "cd service_embedding && python main.py"

echo Starting Chunking Service...
start /b cmd /c "cd service_chunking && python main.py"

echo Starting RAG Service...
start /b cmd /c "cd service_rag && python main.py"

echo Starting Inference Service...
start /b cmd /c "cd service_inference && python main.py"

echo Starting Indexing Service...
start /b cmd /c "cd service_indexing && python main.py"

echo Starting Context Builder Service...
start /b cmd /c "cd service_context_builder && python main.py"

echo Starting Tuning Service...
start /b cmd /c "cd service_tuning && python main.py"

echo All services started!
echo Check logs in each service directory for status.
pause
