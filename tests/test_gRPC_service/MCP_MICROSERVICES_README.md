# MCP Microservices Architecture

このプロジェクトは、FastMCP、LlamaIndex、LangChain、gRPCを使用したModelContextProtocol（MCP）ベースのマイクロサービス・アーキテクチャを実装しています。

## アーキテクチャ概要

### マイクロサービス構成

1. **Chunking Service** (port: 50051)
   - ドキュメントのチャンキング処理
   - 複数のチャンキング戦略をサポート

2. **Tokenization Service** (port: 50052)
   - テキストのトークン化
   - BERT、GPT、spaCy、NLTKトークナイザーをサポート

3. **Embedding Service** (port: 50053)
   - テキストの埋め込み生成
   - Sentence Transformers、OpenAI、HuggingFaceをサポート

4. **Indexing Service** (port: 50054)
   - 複数データベースへのインデックス化
   - Milvus、Redis、MongoDB、Neo4jをサポート

5. **RAG Service** (port: 50055)
   - 統合検索サービス
   - 複数データベースからの検索結果を統合

6. **Context Builder Service** (port: 50056)
   - 検索結果からコンテキスト構築
   - 複数のプロンプトテンプレートをサポート

7. **Inference Service** (port: 50057)
   - AI推論サービス
   - Ollama、OpenAI、ローカルモデルをサポート

8. **Tuning Service** (port: 50058)
   - モデルファインチューニング
   - LoRAベースの効率的なチューニング

9. **MCP Orchestrator** (port: 3000)
   - 全サービスを統合するMCPサーバー
   - ワークフローの自動化

### データベース構成

- **Vector DB**: Milvus (ベクトル検索)
- **Key-Value DB**: Redis (高速キャッシュ)
- **Document DB**: MongoDB (ドキュメント保存)
- **Graph DB**: Neo4j (関係データ)
- **Relational DB**: PostgreSQL (構造化データ)

## セットアップ

### 必要な環境

- Docker & Docker Compose
- Python 3.11+
- Node.js (N8N用)

### 環境変数設定

`.env`ファイルを作成し、以下の変数を設定：

```bash
# Database credentials
POSTGRES_DATABASE=n8n
POSTGRES_USERNAME=n8n
POSTGRES_PASSWORD=n8n

# API Keys (optional)
OPENAI_API_KEY=your_openai_api_key

# N8N
N8N_ENCRYPTION_KEY=your_n8n_encryption_key
N8N_USER_MANAGEMENT_JWT_SECRET=your_jwt_secret
```

### ビルドと起動

```bash
# Windowsの場合
build.bat

# Linux/Macの場合
chmod +x build.sh
./build.sh

# サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

## 使用方法

### MCPクライアントとしての利用

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    # MCPオーケストレーターに接続
    async with stdio_client(["python", "orchestrator/main.py"]) as client:
        # ドキュメントチャンキング
        result = await client.call_tool("chunk_document", {
            "document": {
                "id": "doc1",
                "content": "Your document content here...",
                "content_type": "text/plain"
            },
            "config": {
                "strategy": "recursive",
                "chunk_size": 1000
            }
        })
        print(result)
        
        # RAGワークフロー実行
        rag_result = await client.call_tool("rag_workflow", {
            "documents": [{"id": "doc1", "content": "Document content..."}],
            "query": "What is this document about?",
            "config": {
                "inference_model": "llama2",
                "inference_provider": "ollama"
            }
        })
        print(rag_result)

asyncio.run(main())
```

### REST API経由での利用

```bash
# ヘルスチェック
curl http://localhost:3000/health

# ドキュメントチャンキング
curl -X POST http://localhost:3000/tools/chunk_document \
  -H "Content-Type: application/json" \
  -d '{
    "document": {
      "id": "doc1", 
      "content": "Your document content..."
    }
  }'

# RAGワークフロー
curl -X POST http://localhost:3000/tools/rag_workflow \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{"id": "doc1", "content": "Document content..."}],
    "query": "What is this about?"
  }'
```

### N8N Workflow統合

1. N8Nダッシュボード（http://localhost:5678）にアクセス
2. HTTPリクエストノードを作成
3. MCPオーケストレーター（http://mcp-orchestrator:3000）を呼び出し
4. ワークフローを自動化

## 開発

### 新しいサービスの追加

1. `service_*`ディレクトリを作成
2. `proto/mcp_service.proto`にサービス定義を追加
3. `main.py`、`Dockerfile`、`requirements.txt`を実装
4. `docker-compose.yml`にサービスを追加
5. `orchestrator/main.py`にツールを追加

### プロトコルバッファの更新

```bash
python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/mcp_service.proto
```

## モニタリング

### ログ確認

```bash
# 全サービスのログ
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f service-chunking
```

### ヘルスチェック

```bash
# 全サービスの状態確認
curl http://localhost:3000/tools/health_check_all_services
```

## トラブルシューティング

### よくある問題

1. **プロトコルバッファエラー**
   - `build.bat`または`build.sh`を実行してprotoファイルを再生成

2. **データベース接続エラー**
   - データベースサービスが起動しているか確認
   - `docker-compose logs [database_service]`でログを確認

3. **メモリ不足**
   - Tuning Serviceは大量のメモリを使用
   - Docker設定でメモリ制限を調整

4. **ポート競合**
   - 他のサービスがポートを使用していないか確認
   - `docker-compose.yml`でポート番号を変更

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告をお待ちしています。開発ガイドラインについては、CONTRIBUTINGをご確認ください。
