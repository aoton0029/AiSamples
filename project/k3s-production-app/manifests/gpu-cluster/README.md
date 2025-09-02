# LlamaIndex FastAPI Server

このディレクトリには、LlamaIndexとFastAPIを使用したAIドキュメント処理APIサーバーのKubernetesマニフェストとアプリケーションコードが含まれています。

## 概要

- **LlamaIndex**: ドキュメントのインデックス化と検索機能
- **FastAPI**: 高性能なWeb APIフレームワーク
- **Ollama統合**: ローカルLLMとの連携
- **GPU支援**: GPUリソースを活用した高速処理
- **ChromaDB**: ベクトルデータベースによる効率的な検索

## 機能

### APIエンドポイント

- `POST /query` - ドキュメントに対する質問応答
- `POST /upload` - ドキュメントのアップロード
- `GET /documents` - アップロード済みドキュメント一覧
- `DELETE /documents/{filename}` - ドキュメントの削除
- `GET /health` - ヘルスチェック
- `GET /ready` - レディネスチェック
- `GET /stats` - システム統計情報
- `GET /docs` - API仕様書（Swagger UI）

### 対応ファイル形式

- テキストファイル（.txt）
- PDFファイル（.pdf）
- Word文書（.docx）
- Markdownファイル（.md）

## デプロイメント手順

### 前提条件

1. K3sクラスターが稼働していること
2. GPUドライバーとNVIDIA Container Runtimeがインストールされていること
3. Ollamaがデプロイされていること（`ollama-deployment.yaml`）
4. `ai-services`ネームスペースが存在していること

### 1. マニフェストの適用

```bash
# ネームスペースの作成（必要に応じて）
kubectl apply -f ../namespace.yaml

# LlamaIndex APIサーバーのデプロイ
kubectl apply -f llamaindex-api-deployment.yaml
```

### 2. 自動ビルドとデプロイ（推奨）

```bash
# 実行権限を付与
chmod +x build-and-deploy.sh

# ビルドとデプロイの実行
./build-and-deploy.sh
```

### 3. APIキーの設定（OpenAI使用時）

```bash
# OpenAI APIキーの設定（必要に応じて）
echo -n "your-openai-api-key-here" | base64
kubectl patch secret api-keys -n ai-services -p '{"data":{"openai-api-key":"<base64-encoded-key>"}}'
```

## 使用方法

### 基本的なAPIの使用

```bash
# ヘルスチェック
curl http://localhost:31800/health

# ドキュメントのアップロード
curl -X POST "http://localhost:31800/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"

# ドキュメントへの質問
curl -X POST "http://localhost:31800/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "このドキュメントの要約を教えてください",
    "max_tokens": 1000,
    "temperature": 0.7
  }'
```

### Python クライアント例

```python
import requests
import json

# APIベースURL
BASE_URL = "http://localhost:31800"

# ドキュメントのアップロード
def upload_document(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
        return response.json()

# 質問の送信
def query_documents(query, max_tokens=1000, temperature=0.7):
    data = {
        "query": query,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    response = requests.post(f"{BASE_URL}/query", json=data)
    return response.json()

# 使用例
upload_result = upload_document("sample.pdf")
print(f"Upload result: {upload_result}")

query_result = query_documents("このドキュメントの主要なポイントは何ですか？")
print(f"Query result: {query_result['response']}")
```

## 設定

### 環境変数

- `OLLAMA_BASE_URL`: OllamaサーバーのURL（デフォルト: http://ollama-service:11434）
- `DATA_PATH`: ドキュメント保存パス（デフォルト: /app/data）
- `CACHE_PATH`: キャッシュ保存パス（デフォルト: /app/cache）
- `EMBEDDING_MODEL`: 埋め込みモデル（デフォルト: sentence-transformers/all-MiniLM-L6-v2）

### リソース要件

- **GPU**: 1 GPU（NVIDIA）
- **Memory**: 2-4 GiB
- **CPU**: 1-2 cores
- **Storage**: 70 GiB（データ: 50GB、キャッシュ: 20GB）

## モニタリング

### ヘルスチェック

```bash
# アプリケーションヘルス
kubectl get pods -n ai-services -l app=llamaindex-api

# サービス状態
kubectl describe svc llamaindex-api-service -n ai-services

# ログの確認
kubectl logs -n ai-services -l app=llamaindex-api -f
```

### メトリクス

アプリケーションは以下のメトリクスを公開します：
- プロメテウス互換メトリクス（/metrics）
- アプリケーション統計（/stats）
- システム状態（/health）

## トラブルシューティング

### よくある問題

1. **GPUが認識されない**
   ```bash
   # GPUドライバーの確認
   nvidia-smi
   
   # k3sでのGPU設定確認
   kubectl describe node
   ```

2. **Ollamaとの接続エラー**
   ```bash
   # Ollamaサービスの状態確認
   kubectl get svc ollama-service -n ai-services
   
   # ネットワーク接続テスト
   kubectl exec -it deployment/llamaindex-api -n ai-services -- curl http://ollama-service:11434
   ```

3. **メモリ不足**
   ```bash
   # リソース使用状況の確認
   kubectl top pods -n ai-services
   
   # ログの確認
   kubectl logs -n ai-services -l app=llamaindex-api --tail=100
   ```

## 開発

### ローカル開発

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
export OLLAMA_BASE_URL="http://localhost:11434"
export DATA_PATH="./data"
export CACHE_PATH="./cache"

# アプリケーションの起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### カスタマイズ

- `main.py`: メインアプリケーションロジック
- `requirements.txt`: Python依存関係
- `llamaindex-api-deployment.yaml`: Kubernetesマニフェスト
- `Dockerfile`: コンテナイメージの定義

## ライセンス

このプロジェクトは[ライセンス名]の下で公開されています。
