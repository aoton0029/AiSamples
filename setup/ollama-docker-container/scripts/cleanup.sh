#!/bin/bash

# Ollama Model Containerizer - Cleanup Script
# Author: aoton0029
# Date: 2025-08-19

echo "======================================"
echo "Ollama Container Cleanup"
echo "======================================"

echo "This will remove:"
echo "- All stopped ollama-* containers"
echo "- All ollama-* images (except base)"
echo "- Unused volumes and networks"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "🧹 Stopping running ollama containers..."
docker ps --filter "name=ollama-*" -q | xargs -r docker stop

echo ""
echo "🗑️  Removing stopped ollama containers..."
docker ps -a --filter "name=ollama-*" -q | xargs -r docker rm

echo ""
echo "🖼️  Removing ollama model images..."
# ベースイメージ以外のollamaイメージを削除
docker images --filter "reference=ollama-*" --format "{{.Repository}}:{{.Tag}}" | grep -v "ollama-base" | xargs -r docker rmi

echo ""
echo "💾 Cleaning up unused volumes..."
docker volume prune -f

echo ""
echo "🌐 Cleaning up unused networks..."
docker network prune -f

echo ""
echo "📊 Current storage usage:"
docker system df

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "Remaining ollama images:"
docker images --filter "reference=ollama-*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"