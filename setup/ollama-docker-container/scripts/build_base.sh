#!/bin/bash

# Ollama Model Containerizer - Base Container Builder
# Author: aoton0029
# Date: 2025-08-19

set -e

# 設定読み込み
if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# デフォルト値
OLLAMA_BASE_IMAGE=${OLLAMA_BASE_IMAGE:-"ollama/ollama:latest"}
OLLAMA_BASE_TAG=${OLLAMA_BASE_TAG:-"ollama-base:latest"}

echo "======================================"
echo "Ollama Base Container Builder"
echo "======================================"
echo "Base Image: $OLLAMA_BASE_IMAGE"
echo "Target Tag: $OLLAMA_BASE_TAG"
echo "======================================"

# 既存のイメージを確認
if docker images | grep -q "ollama-base"; then
    echo "Existing ollama-base image found."
    read -p "Rebuild? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# ベースイメージをプル
echo "Pulling base image: $OLLAMA_BASE_IMAGE"
docker pull "$OLLAMA_BASE_IMAGE"

# ベースコンテナをビルド
echo "Building base container..."
docker build \
    --file Dockerfile.base \
    --tag "$OLLAMA_BASE_TAG" \
    --build-arg BASE_IMAGE="$OLLAMA_BASE_IMAGE" \
    .

# ビルド結果を確認
if docker images | grep -q "ollama-base"; then
    echo "✅ Base container built successfully!"
    echo "Image: $OLLAMA_BASE_TAG"
    
    # イメージ詳細を表示
    echo ""
    echo "Image details:"
    docker images ollama-base:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # テスト実行
    echo ""
    read -p "Run test container? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting test container..."
        docker run -d --name ollama-base-test -p 11434:11434 "$OLLAMA_BASE_TAG"
        echo "Waiting for container to start..."
        sleep 10
        
        # ヘルスチェック
        if curl -s http://localhost:11434/api/tags >/dev/null; then
            echo "✅ Base container is working correctly!"
        else
            echo "❌ Base container test failed"
        fi
        
        # テストコンテナを停止・削除
        docker stop ollama-base-test
        docker rm ollama-base-test
    fi
    
else
    echo "❌ Base container build failed!"
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Place model files in models/{model_name}/ directory"
echo "2. Run: ./scripts/create-model-container.sh {model_name}"
echo ""