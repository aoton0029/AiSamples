#!/bin/bash

# Ollama Model Containerizer - Model Container Creator
# Author: aoton0029
# Date: 2025-08-19

set -e

# 引数チェック
if [ $# -ne 1 ]; then
    echo "Usage: $0 <model_name>"
    echo "Example: $0 llama2"
    exit 1
fi

MODEL_NAME="$1"

# 設定読み込み
if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# デフォルト値
OLLAMA_BASE_TAG=${OLLAMA_BASE_TAG:-"ollama-base:latest"}
MODELS_PATH=${MODELS_PATH:-"./models"}

echo "======================================"
echo "Ollama Model Container Creator"
echo "======================================"
echo "Model Name: $MODEL_NAME"
echo "Base Image: $OLLAMA_BASE_TAG"
echo "Models Path: $MODELS_PATH"
echo "======================================"

# ベースイメージの存在確認
if ! docker images | grep -q "ollama-base"; then
    echo "❌ Base image not found!"
    echo "Please run: ./scripts/build-base.sh"
    exit 1
fi

# モデルディレクトリの存在確認
MODEL_DIR="$MODELS_PATH/$MODEL_NAME"
if [ ! -d "$MODEL_DIR" ]; then
    echo "❌ Model directory not found: $MODEL_DIR"
    echo "Please create the directory and place model files."
    exit 1
fi

# models.ymlから設定を読み込み
MODEL_CONFIG=""
MODEL_FILE=""
if [ -f "$MODELS_PATH/models.yml" ]; then
    echo "Reading model configuration..."
    # yqがある場合は使用、なければシンプルなgrepを使用
    if command -v yq >/dev/null 2>&1; then
        MODEL_FILE=$(yq eval ".models.$MODEL_NAME.file" "$MODELS_PATH/models.yml")
        MODEL_CONFIG=$(yq eval ".models.$MODEL_NAME.config" "$MODELS_PATH/models.yml")
    else
        echo "yq not found, using default configuration"
        MODEL_FILE="$MODEL_DIR/model.bin"
        MODEL_CONFIG="$MODEL_NAME"
    fi
fi

# Modelfileの存在確認
MODELFILE="$MODEL_DIR/Modelfile"
if [ ! -f "$MODELFILE" ]; then
    echo "⚠️  Modelfile not found: $MODELFILE"
    echo "Creating default Modelfile..."
    
    # デフォルトのModelfileを作成
    cat > "$MODELFILE" << EOF
FROM ./$MODEL_NAME

# Model configuration
TEMPLATE """{{ .Prompt }}"""

# Parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "</s>"

# System message
SYSTEM """You are a helpful AI assistant."""
EOF
    echo "✅ Default Modelfile created"
fi

# イメージ名とタグを設定
IMAGE_TAG="ollama-$MODEL_NAME:latest"

echo "Building model container: $IMAGE_TAG"

# モデル特化コンテナをビルド
docker build \
    --file Dockerfile.model \
    --tag "$IMAGE_TAG" \
    --build-arg BASE_IMAGE="$OLLAMA_BASE_TAG" \
    --build-arg MODEL_NAME="$MODEL_NAME" \
    --build-arg MODEL_FILE="$MODEL_FILE" \
    --build-arg MODEL_CONFIG="$MODEL_CONFIG" \
    .

# ビルド結果を確認
if docker images | grep -q "ollama-$MODEL_NAME"; then
    echo "✅ Model container built successfully!"
    echo "Image: $IMAGE_TAG"
    
    # イメージ詳細を表示
    echo ""
    echo "Image details:"
    docker images "ollama-$MODEL_NAME:latest" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # 使用方法を表示
    echo ""
    echo "Usage:"
    echo "  docker run -d --name ollama-$MODEL_NAME -p 11434:11434 $IMAGE_TAG"
    echo "  curl http://localhost:11434/api/generate -d '{\"model\":\"$MODEL_NAME\",\"prompt\":\"Hello\"}'"
    echo ""
    
    # テスト実行オプション
    read -p "Run test container? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting test container..."
        docker run -d --name "ollama-$MODEL_NAME-test" -p 11435:11434 "$IMAGE_TAG"
        echo "Waiting for container to start..."
        sleep 15
        
        # ヘルスチェック
        if curl -s http://localhost:11435/api/tags >/dev/null; then
            echo "✅ Model container is working correctly!"
            
            # モデル一覧を確認
            echo "Available models:"
            curl -s http://localhost:11435/api/tags | jq -r '.models[].name' 2>/dev/null || echo "Model list unavailable"
        else
            echo "❌ Model container test failed"
        fi
        
        # テストコンテナを停止・削除
        docker stop "ollama-$MODEL_NAME-test"
        docker rm "ollama-$MODEL_NAME-test"
    fi
else
    echo "❌ Model container build failed!"
    exit 1
fi

echo ""
echo "Model container '$MODEL_NAME' created successfully!"