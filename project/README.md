Collecting workspace informationこのプロジェクトは、k3s、kubectl、nerdctlを使ったKubernetes本番環境でのポッド管理、バージョン管理、オーケストレーション、スケーリング対応の本格的なAIプロジェクトです。

## プロジェクト概要

現在のDocker Composeベースの開発環境を本番用Kubernetes環境に移行し、以下の機能を提供します：

### アーキテクチャ
- **開発環境**: docker-compose.yml - Docker Composeベース
- **本番環境**: k3s-production-app - Kubernetesベース
- **データベース**: PostgreSQL、Redis、MongoDB、Milvus、Neo4j
- **AI/ML**: n8n、Ollama、各種Pythonライブラリ

## 使い方

### 1. 開発環境の起動

````bash
cd project/dev
# 環境設定
cp .env.example .env  # 必要に応じて設定を変更

# CPU環境でのサービス起動
docker compose --profile cpu up -d

# GPU環境でのサービス起動  
docker compose --profile gpu-nvidia up -d

# 特定サービスのみ起動
docker compose up -d postgres n8n redis
````

### 2. バックアップとリストア

````bash
# 全データベースのバックアップ
docker compose --profile backup up

# 最新バックアップからのリストア
docker compose --profile restore up

# 特定ファイルからのリストア
BACKUP_FILE=postgres_backup_20250831_120000.sql docker compose up postgres-restore
BACKUP_DIR=mongodb_backup_20250831_120000 docker compose up mongodb-restore
````

### 3. 本番環境への移行

Kubernetesクラスターの準備：
````bash
# k3sのインストール (Ubuntu/Linux)
curl -sfL https://get.k3s.io | sh -

# 本番環境のデプロイ
cd project/prod
./deploy.sh
````

### 4. サービス管理

````bash
# サービス状況確認
kubectl get pods -n production
kubectl get services -n production

# ログ確認
kubectl logs -f deployment/n8n -n production
kubectl logs -f deployment/ollama -n production

# スケーリング
kubectl scale deployment n8n --replicas=3 -n production
````

## 主要コンポーネント

### データベース設計
- **KV_STORAGE**: Redis - キャッシュとセッション管理
- **GRAPH_STORAGE**: Neo4j - 関係データとナレッジグラフ  
- **VECTOR_STORAGE**: Milvus - ベクトル検索とRAG
- **DOC_STATUS_STORAGE**: MongoDB - ドキュメント状態管理

### AIワークフロー
- **n8n**: ワークフロー自動化とAIエージェント
- **Ollama**: ローカルLLM実行環境
- **各種Pythonサンプル**: 
  - langchain_sample - LangChainでのRAGシステム
  - pdf_vectorize_sample - PDFベクトル化
  - yomitoku_sample - OCR処理

### 本番環境の特徴
- **高可用性**: 複数レプリカとロードバランシング
- **自動復旧**: ヘルスチェックと自動リスタート
- **リソース管理**: CPU/メモリ制限とスケーリング
- **セキュリティ**: RBAC、Secrets管理、ネットワークポリシー

## 開発フロー

1. **ローカル開発**: devでDocker Composeを使用
2. **テスト**: 各サンプルコードで機能検証
3. **本番準備**: Kubernetesマニフェストの調整
4. **デプロイ**: deploy.shで本番環境構築

このプロジェクトにより、AI/MLワークロードの開発から本番運用まで一貫した環境を提供します。