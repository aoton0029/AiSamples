PostgreSQLコンテナが不健康な状態です。これは通常、データベースの初期化や接続の問題が原因です。以下の手順で解決しましょう：

**1. まず現在の状況を確認:**

```bash
# PostgreSQLコンテナのログを確認
docker logs postgres

# コンテナの状態を確認
docker ps -a

# ヘルスチェックの詳細を確認
docker inspect postgres | grep -A 10 Health
```

**2. PostgreSQLコンテナの問題を修正:**

````yaml
  postgres:
    image: postgres:16-alpine
    container_name: postgres
    networks: ['demo']
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=${POSTGRES_DATABASE}
      - POSTGRES_USER=${POSTGRES_USERNAME}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS="--encoding=UTF8 --lc-collate=C --lc-ctype=C"
    volumes:
      - postgres_storage:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h localhost -p 5432 -U ${POSTGRES_USERNAME} -d ${POSTGRES_DATABASE}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    env_file:
      - path: .env
        required: true
````

**3. .envファイルの確認:**

````env
# PostgreSQL設定を確認
POSTGRES_DATABASE=n8n_db
POSTGRES_USERNAME=n8n_user
POSTGRES_PASSWORD=your_secure_password_here

# その他の設定...
````

**4. 問題解決の手順:**

```bash
# 既存のコンテナとボリュームを削除（データが消えます）
docker compose down -v

# PostgreSQLボリュームを明示的に削除
docker volume rm dev_postgres_storage 2>/dev/null || true

# ネットワークをクリーンアップ
docker network prune -f

# 再起動
docker compose up -d postgres

# PostgreSQLの起動を待つ
docker compose logs -f postgres
```

**5. 問題が続く場合は、より詳細なログを有効にする:**

````yaml
  postgres:
    image: postgres:16-alpine
    container_name: postgres
    networks: ['demo']
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=${POSTGRES_DATABASE}
      - POSTGRES_USER=${POSTGRES_USERNAME}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS="--encoding=UTF8"
      - POSTGRES_HOST_AUTH_METHOD=md5
    volumes:
      - postgres_storage:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h localhost -p 5432 -U ${POSTGRES_USERNAME}"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    env_file:
      - path: .env
        required: true
    command: ["postgres", "-c", "log_statement=all", "-c", "log_destination=stderr"]
````

PostgreSQLのログを確認して、具体的なエラーメッセージを教えてください。それに基づいてより具体的な解決策を提示できます。