import pika
import ssl
from typing import Optional
from . import config

_connection_params_cache: Optional[pika.ConnectionParameters] = None


def get_connection_parameters(ssl_enable: bool = False) -> pika.ConnectionParameters:
    global _connection_params_cache
    if _connection_params_cache and not ssl_enable:
        return _connection_params_cache

    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS)

    if ssl_enable:
        context = ssl.create_default_context()
        params = pika.ConnectionParameters(
            host=config.RABBITMQ_HOST,
            port=5671,
            virtual_host=config.RABBITMQ_VHOST,
            credentials=credentials,
            ssl_options=pika.SSLOptions(context)
        )
        return params

    _connection_params_cache = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        virtual_host=config.RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=300,
    )
    return _connection_params_cache


def create_connection(ssl_enable: bool = False) -> pika.BlockingConnection:
    return pika.BlockingConnection(get_connection_parameters(ssl_enable=ssl_enable))
