# Ollama Model Containerizer

Ollamaの各種モデルを簡単にコンテナ化して管理するためのツールです。

## 概要

このプロジェクトは以下を可能にします：
- Ollama公式イメージをベースとしたコンテナの作成
- ホストのモデルファイルをコンテナに組み込み
- モデル毎の専用コンテナの生成
- 設定ファイルベースでの簡単なモデル管理

## ディレクトリ構成

```
ollama-model-containerizer/
├── README.md                 # このファイル
├── docker-compose.yml        # 開発用Docker Compose設定
├── Dockerfile.base          # ベースコンテナ用Dockerfile
├── Dockerfile.model         # モデル特化コンテナ用Dockerfile
├── scripts/                 # 自動化スクリプト
├── models/                  # モデルファイル配置ディレクトリ
├── configs/                 # 設定ファイル
└── .env.example            # 環境変数テンプレート
```

## セットアップ

### 1. 環境設定
```bash
cp .env.example .env
# 必要に応じて.envを編集
```

### 2. ベースコンテナの作成
```bash
chmod +x scripts/*.sh
./scripts/build-base.sh
```

### 3. モデルファイルの配置
```bash
# models/ディレクトリ配下にモデルファイルを配置
mkdir -p models/llama2
# モデルファイルをコピー...
```

## 使用方法

### モデル特化コンテナの作成
```bash
# llama2用コンテナを作成
./scripts/create-model-container.sh llama2

# codellama用コンテナを作成
./scripts/create-model-container.sh codellama
```

### コンテナの実行
```bash
# llama2コンテナを実行
docker run -d --name ollama-llama2 -p 11434:11434 ollama-llama2:latest

# APIテスト
curl http://localhost:11434/api/generate -d '{"model":"llama2","prompt":"Hello"}'
```

### 管理コマンド
```bash
# 作成済みコンテナ一覧
./scripts/list-containers.sh

# クリーンアップ
./scripts/cleanup.sh
```

## モデル設定

`models/models.yml`でモデル設定を管理：

```yaml
models:
  llama2:
    file: "models/llama2/model.bin"
    config: "llama2-7b-chat"
    port: 11434
  codellama:
    file: "models/codellama/model.bin"
    config: "codellama-7b-instruct"
    port: 11435
```

## トラブルシューティング

### よくある問題
1. **モデルファイルが見つからない**
   - `models/`ディレクトリにファイルが存在することを確認
   - `models.yml`のパス設定を確認

2. **ポート競合**
   - `models.yml`で各モデルに異なるポートを設定
   - 実行中のコンテナを確認: `docker ps`

3. **メモリ不足**
   - Dockerに十分なメモリを割り当て
   - 大きなモデルの場合は最低8GB推奨

## 貢献

1. このリポジトリをフォーク
2. フィーチャーブランチを作成
3. 変更をコミット
4. プルリクエストを作成

## ライセンス

MIT License
```


このdocker-compose.ymlファイルのタグと設定について詳しく解説します。

## 全体構造

```yaml
version: '3.8'  # Docker Compose ファイルフォーマットバージョン
```

## サービス定義

### 1. ollama-base サービス

```yaml
services:
  ollama-base:
    build:
      context: .              # ビルドコンテキスト（カレントディレクトリ）
      dockerfile: Dockerfile.base  # 使用するDockerfile
    image: ollama-base:latest    # 作成されるイメージ名とタグ
    container_name: ollama-base-dev  # コンテナ名
```

**ポイント:**
- `build`セクションでローカルビルドを指定
- `image`で作成後のイメージ名を明示的に指定
- `container_name`で実行時のコンテナ名を固定

### 2. ポート設定

```yaml
    ports:
      - "${DEFAULT_PORT:-11434}:11434"
```

**解説:**
- 環境変数`DEFAULT_PORT`が設定されていればその値を使用
- 未設定の場合は`11434`をデフォルトとして使用
- ホストポート:コンテナポートの形式

### 3. ボリューム設定

```yaml
    volumes:
      - ollama_data:/root/.ollama  # 名前付きボリューム
```

**目的:**
- Ollamaのデータ（モデルファイル等）を永続化
- コンテナが削除されてもデータが保持される

### 4. 環境変数

```yaml
    environment:
      - OLLAMA_HOST=${DEFAULT_HOST:-0.0.0.0}
```

**設定:**
- `.env`ファイルの`DEFAULT_HOST`を使用
- 未設定時は`0.0.0.0`（全インターフェースでリッスン）

### 5. リソース制限

```yaml
    deploy:
      resources:
        limits:
          memory: ${MEMORY_LIMIT:-8g}  # メモリ上限
        reservations:
          memory: 2g                   # 最低保証メモリ
```

**効果:**
- メモリ使用量の制御
- OOMキラーによる突然の終了を防止
- システムリソースの適切な管理

## ollama-llama2 サービス（開発用例）

### 1. ビルド設定

```yaml
    build:
      context: .
      dockerfile: Dockerfile.model
      args:
        MODEL_NAME: llama2        # ビルド時引数
```

**特徴:**
- 別のDockerfile（Dockerfile.model）を使用
- `MODEL_NAME`をビルド引数として渡す

### 2. 依存関係

```yaml
    depends_on:
      - ollama-base
```

**動作:**
- `ollama-base`サービスが先に起動
- 依存関係による順序制御

### 3. 環境変数設定

```yaml
    environment:
      - OLLAMA_HOST=0.0.0.0
      - MODEL_NAME=llama2       # モデル固有の環境変数
```

## グローバル設定

### 1. ボリューム定義

```yaml
volumes:
  ollama_data:
    driver: local             # ローカルストレージドライバー
  ollama_llama2_data:
    driver: local
```

**管理:**
- Docker が管理する名前付きボリューム
- `docker volume ls`で確認可能
- データの永続化とバックアップが容易

### 2. ネットワーク設定

```yaml
networks:
  ollama-network:
    driver: bridge            # ブリッジネットワーク
```

**利点:**
- サービス間の内部通信が可能
- 外部からの直接アクセスを制御
- DNSベースのサービス名解決

## 実際の使用例

### 1. 開発環境での起動
```bash
# 全サービス起動
docker-compose up -d

# 特定のサービスのみ起動
docker-compose up -d ollama-base

# ログ確認
docker-compose logs -f ollama-base
```

### 2. 環境変数のカスタマイズ
```bash
# .envファイルで設定
DEFAULT_PORT=11434
MEMORY_LIMIT=16g
DEFAULT_HOST=0.0.0.0
```

### 3. スケーリング
```bash
# 複数インスタンス起動（ポート競合に注意）
docker-compose up -d --scale ollama-llama2=2
```

## セキュリティと運用上の考慮点

### 1. メモリ制限
- 大きなモデルでは8GB以上必要
- システム全体のメモリ使用量を監視

### 2. ポート管理
- 各モデルサービスに異なるポートを割り当て
- ファイアウォール設定との整合性

### 3. データ永続化
- 定期的なボリュームバックアップ
- モデルファイルの適切な管理

この設定により、開発環境での効率的なOllamaモデル管理と、本番環境への展開準備が可能になります。