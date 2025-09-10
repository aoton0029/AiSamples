# LlamaIndex Multi-Database Architecture (Enhanced)

## 概要

このプロジェクトは、LlamaIndex専用パッケージ、Ollama、および複数のデータベース（Milvus、MongoDB、Neo4j、Redis）を統合した**次世代ドキュメント管理・検索システム**です。

## 🚀 新機能・最適化

### LlamaIndex専用パッケージ統合
- `llama-index-vector-stores-milvus`: 最適化されたMilvusベクトルストア
- `llama-index-embeddings-ollama`: Ollama専用エンベディング
- `llama-index-llms-ollama`: Ollama LLM統合
- `llama-index-embeddings-langchain`: LangChainエンベディング統合
- `llama-index-tools-neo4j`: Neo4jクエリツール
- `llama-index-graph-stores-neo4j`: Neo4jグラフストア
- `llama-index-packs-neo4j-query-engine`: Neo4j自然言語クエリエンジン

### 拡張機能

#### 🧠 知的検索システム
- **ハイブリッド検索**: ベクトル + テキスト + グラフ検索の統合
- **プロンプトベース検索**: 自然言語プロンプトによる直感的検索
- **自動リランキング**: AI駆動の結果順位最適化
- **メタデータ強化**: エンティティ抽出・感情分析の自動付与
- **キャッシュ最適化**: 多層キャッシュによる高速化

#### 🤖 AI強化処理
- **感情分析**: ドキュメントの感情スコア自動分析
- **エンティティ抽出**: 人名、組織名、場所の自動抽出
- **自動要約**: AIによる内容要約生成
- **関係性分析**: ドキュメント間関係の自動発見

#### 🕸️ グラフ強化機能
- **タグベース検索**: セマンティックタグによる検索
- **ドキュメントネットワーク**: 関係性ネットワーク可視化
- **自然言語グラフクエリ**: 自然言語でのグラフ検索
- **フルテキストインデックス**: 高速テキスト検索

#### ⚡ パフォーマンス最適化
- **バッチエンベディング**: 並列処理による高速化
- **キャッシュ統計**: ヒット率・性能監視
- **接続プーリング**: データベース接続最適化
- **非同期処理**: 全処理の非同期化

## アーキテクチャ

### コンポーネント構成

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LlamaIndex    │    │      Ollama      │    │ Document Service │
│  (Orchestration)│◄──►│   (LLM & Embed) │◄──►│  (Main Logic)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
              ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
              │                                          │                                          │
              ▼                                          ▼                                          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Milvus      │    │     MongoDB     │    │      Neo4j      │    │      Redis      │
│ (Vector Search) │    │   (Documents)   │    │  (Relationships)│    │    (Cache)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### データベース役割

- **Milvus**: ドキュメントチャンクのベクトル埋め込みを保存し、セマンティック検索を提供
- **MongoDB**: ドキュメントの原本とメタデータを保存
- **Neo4j**: ドキュメント間の関係性をグラフ構造で管理
- **Redis**: 検索結果とセッションデータのキャッシング
- **Ollama**: ローカルLLMによるエンベディング生成と関係性分析

## 主な機能

### 1. ドキュメント処理
- ファイル読み込み（.txt, .pdf, .docx, .md）
- 自動チャンク分割
- ベクトル埋め込み生成
- メタデータ抽出
- キーワード抽出

### 2. 検索機能
- ベクトル検索（セマンティック検索）
- テキスト検索（キーワード検索）
- ハイブリッド検索
- フィルタリング機能

### 3. 関係性管理
- ドキュメント間関係の自動分析
- 関係強度の計算
- 関連ドキュメント推薦

### 4. キャッシング
- 検索結果キャッシュ
- ドキュメントキャッシュ
- セッション管理

## セットアップ

### 必要なソフトウェア

1. **Python 3.8+**
2. **Docker & Docker Compose**
3. **Ollama**

### データベースセットアップ

1. **Docker Composeでデータベース起動**:
```bash
# docker-compose.yml ファイルを作成し、以下のサービスを定義
# - Milvus
# - MongoDB
# - Neo4j
# - Redis

docker-compose up -d
```

2. **Ollama setup**:
```bash
# Ollamaインストール
curl -fsSL https://ollama.ai/install.sh | sh

# 必要なモデルをダウンロード
ollama pull llama2
ollama pull nomic-embed-text
```

### Python依存関係

```bash
# 基本パッケージ
pip install llama-index
pip install llama-index-core

# 専用ベクトルストア
pip install llama-index-vector-stores-milvus

# Ollama統合
pip install llama-index-embeddings-ollama
pip install llama-index-llms-ollama

# LangChain統合
pip install llama-index-embeddings-langchain
pip install langchain
pip install langchain-community

# Neo4j統合
pip install llama-index-tools-neo4j
pip install llama-index-graph-stores-neo4j
pip install llama-index-packs-neo4j-query-engine

# データベースドライバー
pip install pymilvus
pip install motor  # MongoDB async driver
pip install neo4j
pip install aioredis
pip install httpx

# その他
pip install python-dotenv
pip install numpy
pip install pandas
```

または一括インストール：
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用例

```python
import asyncio
from enhanced_document_service import EnhancedDocumentService

async def main():
    # 拡張サービス初期化
    service = EnhancedDocumentService()
    await service.initialize()
    
    # 拡張ドキュメント処理（感情分析・エンティティ抽出付き）
    document_id = await service.process_file_enhanced(
        "document.pdf",
        metadata={"category": "research"},
        extract_entities=True,
        analyze_sentiment=True
    )
    
    # 知的検索（リランキング・メタデータ強化付き）
    results = await service.intelligent_search(
        "機械学習の最新動向",
        search_type="hybrid",
        include_metadata=True,
        rerank=True
    )
    
    # 自然言語クエリ
    response = await service.natural_language_query(
        "AIと量子コンピューティングの関係について教えてください"
    )
    
    # 拡張統計取得
    stats = await service.get_enhanced_system_stats()
    
    # クリーンアップ
    await service.shutdown()

asyncio.run(main())
```

### 拡張デモ実行

```bash
# 基本デモ
python main.py

# 拡張機能デモ
python enhanced_demo.py

# プロンプト検索専用デモ
python prompt_search_demo.py

# 検索性能ベンチマーク
python prompt_search_benchmark.py
```

### プロンプト検索の実用例

```python
# 1. 基本的なプロンプト検索
results = await service.search_by_prompt(
    "Pythonでデータ分析を始めたい初心者向けの情報",
    similarity_threshold=0.7,
    max_results=5
)

# 2. 類似ドキュメント検索
similar_docs = await service.find_similar_documents_advanced(
    "機械学習プロジェクトの進め方",
    similarity_threshold=0.8,
    max_results=3
)

# 3. 検索結果の活用
for result in results:
    print(f"タイトル: {result['title']}")
    print(f"類似度: {result['similarity_score']:.2%}")
    print(f"タグ: {', '.join(result['tags'])}")
    print(f"内容: {result['content_snippet'][:100]}...")
```

### 検索機能の特徴

#### プロンプトベース検索の利点
- **直感的**: 自然言語でそのまま検索可能
- **高精度**: セマンティック理解による関連性の高い結果
- **柔軟性**: キーワードマッチングを超えた概念検索
- **文脈理解**: プロンプトの意図を理解した検索

#### 類似度計算の仕組み
1. **エンベディング生成**: プロンプトをベクトル化
2. **コサイン類似度**: ドキュメントベクトルとの類似度計算
3. **閾値フィルタリング**: 設定した類似度以上の結果のみ返却
4. **スコア正規化**: 0-1の範囲で類似度を表示

## 設定

### config.py での設定

```python
@dataclass
class DatabaseConfig:
    # Milvus設定
    MILVUS_HOST = "localhost"
    MILVUS_PORT = 19530
    
    # MongoDB設定
    MONGODB_URI = "mongodb://localhost:27017"
    
    # Neo4j設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "password"
    
    # Redis設定
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    
    # Ollama設定
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama2"
    OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
```

### 環境変数

以下の環境変数で設定を上書き可能：
- `MILVUS_HOST`
- `MONGODB_URI`
- `NEO4J_URI`
- `REDIS_HOST`
- `OLLAMA_BASE_URL`

## API リファレンス

### EnhancedDocumentService

#### 拡張メソッド

- `process_file_enhanced(file_path, metadata, extract_entities, analyze_sentiment)`: 拡張ファイル処理
- `intelligent_search(query, search_type, include_metadata, rerank, limit)`: 知的検索
- `natural_language_query(question)`: 自然言語クエリ処理
- `get_enhanced_system_stats()`: 拡張システム統計取得

#### 検索オプション

- **search_type**: 
  - `"vector"`: ベクトル検索のみ
  - `"text"`: テキスト検索のみ  
  - `"hybrid"`: 統合検索（推奨）
- **include_metadata**: メタデータ強化ON/OFF
- **rerank**: AIリランキングON/OFF

### EnhancedOllamaClient

#### パフォーマンス機能

- `generate_embedding(text, use_cache)`: キャッシュ対応エンベディング
- `generate_embeddings_batch(texts, batch_size)`: バッチ処理
- `analyze_sentiment(text)`: 感情分析
- `extract_entities(text)`: エンティティ抽出
- `get_performance_stats()`: 性能統計
- `clear_cache()`: キャッシュクリア

### EnhancedNeo4jRepository

#### グラフ機能

- `find_documents_by_tag(tag)`: タグ検索
- `get_document_network(document_id, depth)`: ネットワーク取得
- `natural_language_query(question)`: 自然言語グラフクエリ
- `get_enhanced_graph_stats()`: 拡張グラフ統計

## パフォーマンス最適化

### キャッシュ戦略（強化版）

- **エンベディングキャッシュ**: LRU（最大1000エントリ）
- **検索結果キャッシュ**: 5分間保持
- **ドキュメントキャッシュ**: 1時間保持
- **統計キャッシュ**: 10分間保持

### バッチ処理最適化

```python
# バッチサイズ調整
embeddings = await ollama_client.generate_embeddings_batch(
    texts, 
    batch_size=10  # 並列処理数
)
```

### インデックス最適化（強化版）

#### MongoDB
- テキストインデックス強化
- 複合インデックス追加
- エンティティインデックス

#### Neo4j
- フルテキストインデックス
- タグインデックス
- 関係性強度インデックス

#### Milvus
- IVF_FLAT最適化
- コサイン類似度計算
- 自動インデックス管理

## トラブルシューティング

### よくある問題

1. **Ollamaモデルが見つからない**:
   ```bash
   ollama list  # モデル確認
   ollama pull llama2  # モデルダウンロード
   ```

2. **Milvus接続エラー**:
   - Docker Composeでサービス起動確認
   - ポート19530が使用可能か確認

3. **MongoDB接続エラー**:
   - MongoDBサービス起動確認
   - 認証設定確認

4. **Neo4j接続エラー**:
   - デフォルトパスワード変更確認
   - ポート7687が使用可能か確認

### ログレベル設定

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 拡張可能性

### 新しいデータベース追加

1. `models.py`に新しいリポジトリインターフェース定義
2. 実装クラス作成
3. `DocumentService`に統合

### 新しいファイル形式サポート

1. `sys_config.SUPPORTED_FILE_TYPES`に拡張子追加
2. LlamaIndexのLoaderを設定

### カスタムエンベディングモデル

1. `ollama_client.py`でモデル設定変更
2. `config.py`でモデル名更新

## ライセンス

MIT License

## 貢献

1. フォーク
2. フィーチャーブランチ作成
3. コミット
4. プルリクエスト作成

## サポート

質問やissueは、GitHubリポジトリまでお願いします。