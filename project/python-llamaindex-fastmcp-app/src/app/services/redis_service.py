from redis import Redis
import os

class RedisService:
    def __init__(self):
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_client = Redis(host=self.redis_host, port=self.redis_port)

    def set_value(self, key, value):
        """Set a value in Redis."""
        self.redis_client.set(key, value)

    def get_value(self, key):
        """Get a value from Redis."""
        return self.redis_client.get(key)

    def delete_value(self, key):
        """Delete a value from Redis."""
        self.redis_client.delete(key)

    def exists(self, key):
        """Check if a key exists in Redis."""
        return self.redis_client.exists(key) > 0