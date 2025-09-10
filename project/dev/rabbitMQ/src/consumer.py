from __future__ import annotations
import json
import signal
import sys
import pika
from typing import Callable, Any
from .connection import create_connection
from . import config

_shutdown = False

def _signal_handler(signum, frame):  # noqa
    global _shutdown
    _shutdown = True


def consume(callback: Callable[[dict], None]):
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    with create_connection() as conn:
        ch = conn.channel()
        ch.queue_declare(queue=config.QUEUE_NAME, durable=True)
        ch.basic_qos(prefetch_count=config.PREFETCH_COUNT)

        def _on_message(channel: pika.channel.Channel, method, properties, body):  # noqa
            try:
                data = json.loads(body.decode("utf-8"))
                callback(data)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:  # noqa
                # 異常時は NACK (再キュー可)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        ch.basic_consume(queue=config.QUEUE_NAME, on_message_callback=_on_message, auto_ack=False)
        print(f" [*] Waiting for messages in {config.QUEUE_NAME}. To exit press CTRL+C")
        while not _shutdown:
            try:
                conn.process_data_events(time_limit=1)
            except KeyboardInterrupt:
                break
        print("Shutdown requested. Exiting...")


if __name__ == "__main__":
    def handler(msg: dict):
        print("received:", msg)
    consume(handler)
