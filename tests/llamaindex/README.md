# RAG Multi-Database System

LlamaIndex、Ollama、複数データベース（Milvus、MongoDB、Neo4j、Redis）を使用したRAGシステム

## システム構成

- **LLM/埋め込み**: Ollama
- **ベクトルDB**: Milvus (類似検索)
- **ドキュメントDB**: MongoDB (メタデータ・テキスト保存)
- **グラフDB**: Neo4j (関係性管理)
- **キーバリューDB**: Redis (キャッシュ・セッション)

## ファイル構成

```
llamaindex/
├── ollama_connector.py      # Ollama接続管理
├── mongo_client.py          # MongoDB操作
├── milvus_client.py         # Milvus操作
├── neo4j_client.py          # Neo4j操作
├── redis_client.py          # Redis操作
├── multi_format_loader.py   # 複数フォーマット読み込み
├── index_manager.py         # 統合管理クラス
├── main.py                  # サンプル実行
└── requirements.txt         # 依存パッケージ
```

## セットアップ

### 1. 依存パッケージインストール
```bash
pip install -r requirements.txt
```

### 2. Dockerコンテナ起動（前提条件）
```bash
# Ollama
docker run -d -p 11434:11434 --name ollama ollama/ollama

# MongoDB
docker run -d -p 27017:27017 --name mongodb mongo

# Milvus
docker run -d -p 19530:19530 --name milvus milvusdb/milvus:latest

# Neo4j
docker run -d -p 7474:7474 -p 7687:7687 --name neo4j \
  -e NEO4J_AUTH=neo4j/password neo4j

# Redis
docker run -d -p 6379:6379 --name redis redis:alpine
```

### 3. Ollamaモデルセットアップ
```bash
# LLMモデル
docker exec ollama ollama pull llama3.2:3b

# 埋め込みモデル
docker exec ollama ollama pull nomic-embed-text
```

## 使用方法

### 基本的な使用例
```python
from index_manager import IndexManager

# 設定
config = {
    "ollama_url": "http://localhost:11434",
    "llm_model": "llama3.2:3b",
    "embedding_model": "nomic-embed-text",
    # ... その他DB設定
}

# 初期化
manager = IndexManager(config)

# ドキュメント追加
doc_id = manager.add_document("document.pdf", {"category": "research"})

# 類似検索
results = manager.search_similar("質問内容", top_k=5)

# RAG質問応答
answer = manager.query_with_rag("AIについて教えて")

# 関連ドキュメント検索
related = manager.find_related_documents(doc_id)
```

### サンプル実行
```bash
python main.py
```

## 主要機能

### ドキュメント管理
- 複数フォーマット対応（PDF, DOCX, TXT, HTML, JSON, CSV等）
- メタデータ保存・検索
- バッチ処理対応

### 検索機能
- ベクトル類似検索（Milvus）
- メタデータフィルタリング（MongoDB）
- 関係性検索（Neo4j）
- キャッシュ高速化（Redis）

### RAG機能
- コンテキスト構築
- LLM回答生成
- レスポンスキャッシュ

## 各DBの役割

### MongoDB
- ドキュメント本文保存
- メタデータ管理
- 構造化データ検索

### Milvus
- 埋め込みベクトル保存
- 高速類似検索
- ベクトルインデックス管理

### Neo4j
- エンティティ関係管理
- グラフ検索
- 関連性発見

### Redis
- 埋め込みベクトルキャッシュ
- 検索結果キャッシュ
- LLMレスポンスキャッシュ
- セッション管理

## カスタマイズ

### 設定変更
`main.py`のCONFIG辞書で各種設定を変更可能

### 新しいファイル形式対応
`multi_format_loader.py`に新しいローダー関数を追加

### カスタムフィルタリング
`index_manager.py`の`_match_metadata_filter`をカスタマイズ

## トラブルシューティング

### 接続エラー
各DBコンテナが起動していることを確認

### メモリ不足
Milvusのインデックスパラメータを調整

### 文字化け
ドキュメントのエンコーディング設定を確認

## パフォーマンス最適化

- Redisキャッシュの活用
- Milvusインデックス調整
- バッチ処理でのメモリ管理
- 並列処理対応

## 注意事項

- 大量データ処理時はメモリ使用量に注意
- ベクトル次元数は埋め込みモデルと一致させる
- バックアップとリストア戦略を検討
- セキュリティ設定（本番環境）


---


GitHub Copilot

以下、ドキュメントをベクトルDB／ドキュメントDB／グラフDBに関連づけて「追加（インデックス化）」するフローと、検索フローを簡潔に説明する。

追加（インデックス化）フロー（順序付き）
1. 前処理
   - 正規化、言語分割、チャンク化（長文は意味的単位で分割）。
   - メタデータ抽出（title, author, date, tags, source, doc_id など）。
2. 埋め込み生成（Vector）
   - 各チャンク／ドキュメントに対して埋め込みベクトルを生成（モデル：embedding model）。
3. ドキュメントDB保存（Document DB）
   - 元文／全文やチャンク、メタデータ、doc_id を保存。
   - 検索に使うフィールドに対して inverted index（全文索引）を作成。
4. ベクトルDB保存（Vector DB / ANN Index）
   - 埋め込みベクトルを doc_id と一緒に保存。ANN インデックス（例：HNSW, FAISS, Milvus）を作成して高速近傍検索を有効化。
5. グラフDB登録（Graph DB）
   - 抽出したエンティティ（人名・組織・製品等）と関係（出典・参照・引用）をノード／エッジとして保存。
   - 各ノードやエッジに doc_id を紐付け（参照用プロパティ）。
   - 必要なプロパティに対してインデックスを付与（entity_id, type, timestamp など）。
6. 連携（ID と索引の整合）
   - doc_id を共通キーにして三者を紐付ける（ベクトルエントリ ⇄ ドキュメントDBレコード ⇄ グラフノード/エッジ）。
   - トランザクション的に失敗時のロールバックやバージョニングを考慮。
7. 運用処理
   - 重複検出／マージ、バッチ更新、再インデックス化、メトリクス収集。

検索フロー（ユーザークエリから結果まで）
1. クエリ入力と前処理
   - クエリ正規化、必要なら意図解析（intent）、フィルタ条件抽出（time range, tags）。
2. ベクトル検索（Semantic retrieval）
   - クエリを埋め込み化し、ベクトルDBで近傍検索（k-NN）を実行して候補 doc_id のリストを取得。
3. キーワード／フィルタ検索（Precision）
   - ドキュメントDBの inverted index を使い、必要な条件（必須キーワード、メタフィルタ）で候補を絞る。
   - ベクトル候補とキーワード候補を合成（和集合／交差）して候補集合を作成。
4. グラフ拡張（関係性補強）
   - 候補 doc_id に関連するエンティティやリンクを graph DB で辿り、関連文書やコンテキストを取得（例：同じ著者の別文書、参照元）。
   - 関係性をスコアに組み込み（引用の有無、リンク距離などでブースト）。
5. 再ランキング（Rerank）
   - 候補を BM25、ベクトル距離、メタデータスコア、グラフスコア等の重み付けで統合しランク付け。必要ならクロスエンコーダで精密スコア算出。
6. 結果合成と返却
   - 上位 N 件のドキュメント本文（または抜粋）、ハイライト、関連エンティティ、トレーサビリティ（どのDBから来たか）を返す。
7. フィードバック取り込み
   - ユーザーのクリックや評価を蓄積してリランキングモデルや重みを学習させる。

実装上の注意点（要点）
- ID の一貫性: doc_id をシングルソースキーにすることで各DBの連携を簡潔に保つ。
- インデックス種別: ベクトルは ANN（HNSW 等）、全文は inverted index、グラフはノード/エッジプロパティインデックス。
- 一貫性とレイテンシ: インデックス作成は非同期バッチ化することが多い。整合性のためにイベントソース（変更イベント → ワーカーで各DB更新）を使う。
- スケーリング: ベクトルはシャーディング／分散ANN、ドキュメントは分割・レプリカ、グラフはサブグラフ分割を検討。
- ハイブリッド検索: ベクトル＋BM25 のハイブリッドが精度・説明性で現実的に有用。
- セキュリティ/ガバナンス: メタデータレベルでアクセス制御、PII マスク、監査ログ。

簡単な疑似コード（検索パイプラインのイメージ）
````python
# query -> candidates -> rerank
query = "製品Xの導入事例"
q_emb = embed(query)                                # 埋め込み
vec_hits = vector_db.search(q_emb, top_k=100)       # [(doc_id, vec_score), ...]
text_hits = doc_db.search_text(query, filters=...)  # [(doc_id, text_score), ...]
candidates = merge_candidates(vec_hits, text_hits)  # 合成（例：score合算）
graph_boosts = graph_db.compute_boosts([id for id,_ in candidates])
final_scores = rerank(candidates, graph_boosts)
results = doc_db.fetch_documents([id for id,_ in topN(final_scores,10)])
return results
````

この流れを基本に、要件（応答速度、精度、運用コスト、データ量）に合わせてインデックス設計や重み付け、非同期処理の粒度を調整する。


---

以下、ドキュメントの追加（インデックス化）機能を実装します。

## 主な機能
1. **前処理**: ドキュメントの正規化、メタデータ抽出、チャンク化
2. **埋め込み生成**: Ollamaを使用したベクトル生成
3. **マルチDB保存**: Milvus（ベクトル）、MongoDB（ドキュメント）、Neo4j（グラフ）
4. **エンティティ抽出**: グラフDB用のエンティティと関係性の抽出
5. **統合管理**: doc_idによる三つのDBの連携
6. **エラーハンドリング**: 各段階での失敗処理とロールバック対応
7. **バッチ処理**: 複数ドキュメントの一括処理

## 技術仕様
- **LlamaIndex**: すべてのDB操作でStoreクラスを使用
- **Ollama**: LLMと埋め込みモデルに使用
- **トランザクション**: 各段階の成功/失敗を追跡
- **メタデータ管理**: 豊富なメタデータ抽出と管理
- **スケーラビリティ**: バッチ処理とエラー復旧機能

---

ドキュメントの類似検索・RAG機能を実装します。

## 主な機能

1. **クエリ前処理**: 正規化、意図解析、フィルタ条件処理
2. **ベクトル検索**: Milvusでの意味的類似検索
3. **キーワード検索**: MongoDBでの精密検索とフィルタリング
4. **グラフ拡張**: Neo4jでの関係性ベースの検索拡張
5. **再ランキング**: 複数スコアによる統合ランキング
6. **RAG応答**: LLMによる質問応答
7. **フィードバック**: ユーザー評価の記録

## 技術仕様

- **LlamaIndex**: 全てのDB操作でStoreクラスを使用
- **Ollama**: LLMと埋め込みモデルに使用
- **マルチDB統合**: ベクトル・ドキュメント・グラフDBの連携
- **スコアリング**: ベクトル距離、メタデータ、グラフ関係の統合
- **フィルタリング**: 多様な検索条件に対応

