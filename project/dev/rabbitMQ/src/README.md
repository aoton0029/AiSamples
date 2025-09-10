# RabbitMQ Python Sample

構成:
- config.py: 環境変数読み込み & 基本設定
- connection.py: 接続パラメータ生成/接続ヘルパ
- producer.py: メッセージ送信 (JSON, 再試行ロジックあり)
- consumer.py: メッセージ受信 (Graceful shutdown, prefetch)
- requirements.txt: 依存 (pika)

環境変数 (任意):
RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_VHOST,
RABBITMQ_QUEUE, RABBITMQ_PREFETCH, PUBLISH_RETRY, PUBLISH_RETRY_WAIT

インストール:
python -m venv .venv
. .venv/Scripts/activate  (Windows PowerShell は . .venv/Scripts/Activate.ps1)
pip install -r requirements.txt

起動例:
# 送信
python -m src.producer

# 受信 (別ターミナル)
python -m src.consumer

アプリから送信例:
from src.producer import publish
publish({"type": "event", "payload": 1})

独自 callback 実装 (consumer):
from src.consumer import consume

def handle(msg: dict):
    print(msg)

consume(handle)

SSL 接続 (例): connection.create_connection(ssl_enable=True)
