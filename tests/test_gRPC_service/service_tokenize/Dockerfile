FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy proto files and generate gRPC code
COPY ../proto ./proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/mcp_service.proto

# Copy application code
COPY . .

# Expose port
EXPOSE 50052

# Run the service
CMD ["python", "main.py"]
