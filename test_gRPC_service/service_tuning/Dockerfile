FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and generate gRPC code
COPY ../proto ./proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/mcp_service.proto

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p ./models

# Expose port
EXPOSE 50058

# Run the service
CMD ["python", "main.py"]
