# RabbitMQ Local Dev Setup

## 起動方法
```
docker compose up -d
```

管理UI: http://localhost:15672  (user: devuser / pass: devpass)
AMQP: amqp://devuser:devpass@localhost:5672/dev_vhost
Prometheus メトリクス (有効時): http://localhost:15692/metrics

## ファイル構成
- `docker-compose.yml` : RabbitMQサービス定義
- `.env` : 環境変数(デフォルトユーザなど) ※本番では値を変更
- `config/enabled_plugins` : 有効化するプラグイン (management, prometheus)
- `config/definitions.json` : 初期ロードするユーザ/キュー/Exchange等の定義
- `data/` : 永続化データ(初回起動後に生成)

## 定義ファイルを変更したい場合
1. コンテナを停止: `docker compose down`
2. `config/definitions.json` を編集
3. データをリセットしたい場合は `data/` ディレクトリを削除
4. 再起動: `docker compose up -d --build`

## 便利コマンド
コンテナログ表示:
```
docker compose logs -f rabbitmq
```

ヘルスチェック:
```
docker inspect --format='{{json .State.Health}}' rabbitmq
```

シェルに入る:
```
docker exec -it rabbitmq bash
```

キュー一覧 (コンテナ内で):
```
rabbitmqctl list_queues name messages consumers
```

## 注意
- `definitions.json` 内の `password` フィールドはプレーンテキスト利用。初回ロード後にハッシュへ変換されます。
- 本番用ではユーザ名/パスワード/クッキーを強固な値へ変更してください。
