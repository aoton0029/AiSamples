import os

# 基本設定（環境変数で上書き可能）
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE", "sample_queue")
PREFETCH_COUNT = int(os.getenv("RABBITMQ_PREFETCH", "10"))

# publish 再試行設定
PUBLISH_RETRY = int(os.getenv("PUBLISH_RETRY", "5"))
PUBLISH_RETRY_WAIT = float(os.getenv("PUBLISH_RETRY_WAIT", "0.5"))
