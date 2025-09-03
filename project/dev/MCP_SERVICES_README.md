# MCP Microservices Architecture

## Overview

この プロジェクトは、ModelContextProtocol (MCP) を使用したマイクロサービス アーキテクチャを実装しています。各サービスは独立して動作し、FastMCP、LangChain、LlamaIndexを活用してAI/ML機能を提供します。

## Services

### 1. Tokenize Service (Port: 8001)
- **機能**: テキストのトークン化
- **フレームワーク**: tiktoken, transformers
- **ツール**:
  - `tokenize_text`: テキストをトークン化
  - `count_tokens`: トークン数をカウント
  - `create_text_chunks`: テキストをチャンクに分割

### 2. Embedding Service (Port: 8002)
- **機能**: テキストの埋め込み生成
- **フレームワーク**: sentence-transformers, openai, langchain, llama-index
- **ツール**:
  - `create_embeddings`: 埋め込み生成
  - `compute_similarity`: 類似度計算
  - `find_most_similar`: 最も類似した埋め込みを検索

### 3. Chunking Service (Port: 8003)
- **機能**: ドキュメントのチャンキング
- **フレームワーク**: langchain, llama-index, nltk
- **ツール**:
  - `chunk_text`: テキストをチャンク化
  - `chunk_document`: ドキュメントファイルをチャンク化
  - `smart_chunk`: インテリジェントなチャンキング

### 4. RAG Service (Port: 8004)
- **機能**: 検索拡張生成
- **フレームワーク**: milvus, redis, mongodb, neo4j
- **ツール**:
  - `search_similar`: 類似ドキュメント検索
  - `retrieve_and_generate`: RAG実行
  - `add_documents`: ドキュメント追加

### 5. Inference Service (Port: 8005)
- **機能**: AI推論
- **フレームワーク**: openai, anthropic, transformers, ollama
- **ツール**:
  - `generate_text`: テキスト生成
  - `chat_completion`: チャット応答
  - `analyze_sentiment`: 感情分析

### 6. Indexing Service (Port: 8006)
- **機能**: データのインデックス化
- **ツール**:
  - `index_documents`: ドキュメントのインデックス化
  - `create_index`: インデックス作成

### 7. Context Builder Service (Port: 8007)
- **機能**: コンテキスト構築
- **ツール**:
  - `build_context`: コンテキスト構築
  - `create_prompt`: プロンプト作成

### 8. Tuning Service (Port: 8008)
- **機能**: モデルのファインチューニング
- **ツール**:
  - `prepare_training_data`: 訓練データ準備
  - `start_fine_tuning`: ファインチューニング開始
  - `evaluate_model`: モデル評価

## Quick Start

### 1. 依存関係のインストール

各サービスディレクトリで：

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

各サービスの `.env.example` を `.env` にコピーして設定：

```bash
cp .env.example .env
```

### 3. サービス起動

#### Windowsの場合：
```cmd
start_services.bat
```

#### Linux/macOSの場合：
```bash
chmod +x start_services.sh
./start_services.sh
```

### 4. 個別サービス起動

```bash
cd service_tokenize
python main.py
```

## Docker使用

各サービスはDockerコンテナとして実行可能：

```bash
cd service_tokenize
docker build -t tokenize-service .
docker run -p 8001:8001 tokenize-service
```

## API使用例

### Tokenize Service
```python
import requests

response = requests.post('http://localhost:8001/tokenize', json={
    'text': 'Hello world',
    'method': 'tiktoken',
    'model_name': 'gpt-3.5-turbo'
})
```

### Embedding Service
```python
response = requests.post('http://localhost:8002/embed', json={
    'text': 'Sample text to embed',
    'method': 'sentence_transformers'
})
```

## Configuration

各サービスは環境変数で設定可能：

- `SERVICE_NAME`: サービス名
- `MCP_SERVER_PORT`: サーバーポート
- `MCP_SERVER_HOST`: サーバーホスト
- `LOG_LEVEL`: ログレベル
- `OPENAI_API_KEY`: OpenAI APIキー（必要な場合）

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Tokenize       │    │  Embedding      │    │  Chunking       │
│  Service        │    │  Service        │    │  Service        │
│  (Port: 8001)   │    │  (Port: 8002)   │    │  (Port: 8003)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │            MCP Protocol Bus                     │
         └─────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  RAG            │    │  Inference      │    │  Indexing       │
│  Service        │    │  Service        │    │  Service        │
│  (Port: 8004)   │    │  (Port: 8005)   │    │  (Port: 8006)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Development

### サービス追加

1. 新しいディレクトリ作成: `service_new/`
2. 必要なファイルを作成:
   - `main.py` - MCPサーバーのエントリーポイント
   - `requirements.txt` - 依存関係
   - `config.py` - 設定管理
   - `handlers/` - ビジネスロジック
   - `models/` - データモデル
   - `Dockerfile` - Docker設定

### Testing

```bash
cd service_tokenize
python -m pytest tests/
```

## Troubleshooting

### よくある問題

1. **Import Errors**: 依存関係が不足している場合は `pip install -r requirements.txt` を実行
2. **Port Conflicts**: ポートが既に使用されている場合は、設定ファイルでポートを変更
3. **API Key Errors**: 必要なAPIキーが環境変数に設定されているか確認

### ログ

各サービスは `logs/` ディレクトリにログを出力します。

## Contributing

1. フォークしてブランチを作成
2. 変更を実装
3. テストを追加/実行
4. プルリクエストを送信

## License

MIT License
