from __future__ import annotations
import json
import time
import pika
from typing import Any, Dict
from .connection import create_connection
from . import config


def _ensure_queue(channel: pika.channel.Channel):
    channel.queue_declare(queue=config.QUEUE_NAME, durable=True, arguments={
        # メッセージ TTL や DLX を設定したい場合はここに追加
        # 'x-message-ttl': 60000
    })


def publish(message: Dict[str, Any], routing_key: str | None = None, retry: int | None = None):
    if routing_key is None:
        routing_key = config.QUEUE_NAME
    if retry is None:
        retry = config.PUBLISH_RETRY

    attempt = 0
    body = json.dumps(message, ensure_ascii=False).encode("utf-8")

    while True:
        try:
            with create_connection() as conn:
                ch = conn.channel()
                _ensure_queue(ch)
                ch.basic_publish(
                    exchange="",
                    routing_key=routing_key,
                    body=body,
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=2,  # persistent
                    )
                )
            return
        except Exception as e:  # noqa
            attempt += 1
            if attempt > retry:
                raise
            time.sleep(config.PUBLISH_RETRY_WAIT * attempt)


if __name__ == "__main__":
    # 単体実行テスト
    publish({"event": "hello", "value": 123})
    print("published")
