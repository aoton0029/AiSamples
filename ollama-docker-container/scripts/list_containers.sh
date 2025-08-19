#!/bin/bash

# Ollama Model Containerizer - Container Lister
# Author: aoton0029
# Date: 2025-08-19

echo "======================================"
echo "Ollama Container List"
echo "======================================"

echo ""
echo "🔧 Base Images:"
docker images --filter "reference=ollama-base*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "🤖 Model Images:"
docker images --filter "reference=ollama-*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep -v "ollama-base" || echo "No model images found"

echo ""
echo "🏃 Running Containers:"
docker ps --filter "name=ollama-*" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" || echo "No running containers"

echo ""
echo "💤 Stopped Containers:"
docker ps -a --filter "name=ollama-*" --filter "status=exited" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" || echo "No stopped containers"

echo ""
echo "📊 Storage Usage:"
echo "Total Docker images size:"
docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}"

echo ""
echo "💾 Available Models:"
if [ -d "./models" ]; then
    find ./models -maxdepth 1 -type d | grep -v "^./models$" | sed 's|./models/||' | sort || echo "No models found"
else
    echo "Models directory not found"
fi