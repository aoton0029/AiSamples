import logging
import json
import pickle
from typing import Any, Optional
import aioredis
from models import CacheRepository
from config import db_config

logger = logging.getLogger(__name__)

class RedisRepository(CacheRepository):
    """Redisキャッシュリポジトリ"""
    
    def __init__(self):
        self.host = db_config.REDIS_HOST
        self.port = db_config.REDIS_PORT
        self.db = db_config.REDIS_DB
        self.expire_time = db_config.REDIS_EXPIRE_TIME
        self.redis = None
    
    async def connect(self) -> bool:
        """Redisに接続"""
        try:
            self.redis = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                encoding="utf-8",
                decode_responses=False  # バイナリデータ対応
            )
            
            # 接続確認
            await self.redis.ping()
            
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Redisから切断"""
        try:
            if self.redis:
                await self.redis.close()
            logger.info("Disconnected from Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Redis: {e}")
            return False
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """キャッシュ取得"""
        try:
            if not self.redis:
                await self.connect()
            
            # データ取得
            data = await self.redis.get(key)
            if data is None:
                return None
            
            # デシリアライズ
            try:
                # まずJSONでデコードを試行
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # JSONでない場合はpickleでデコード
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire_time: int = None) -> bool:
        """キャッシュ設定"""
        try:
            if not self.redis:
                await self.connect()
            
            # シリアライズ
            try:
                # まずJSONでエンコードを試行
                serialized_value = json.dumps(value, default=str).encode('utf-8')
            except (TypeError, ValueError):
                # JSONでエンコードできない場合はpickleを使用
                serialized_value = pickle.dumps(value)
            
            # 有効期限設定
            if expire_time is None:
                expire_time = self.expire_time
            
            # データ設定
            await self.redis.setex(key, expire_time, serialized_value)
            
            logger.debug(f"Set cache: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """キャッシュ削除"""
        try:
            if not self.redis:
                await self.connect()
            
            result = await self.redis.delete(key)
            logger.debug(f"Deleted cache: {key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """キャッシュ存在確認"""
        try:
            if not self.redis:
                await self.connect()
            
            result = await self.redis.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to check cache existence: {e}")
            return False
    
    async def set_hash(self, key: str, mapping: dict, expire_time: int = None) -> bool:
        """ハッシュ設定"""
        try:
            if not self.redis:
                await self.connect()
            
            # ハッシュ設定
            await self.redis.hset(key, mapping=mapping)
            
            # 有効期限設定
            if expire_time is None:
                expire_time = self.expire_time
            await self.redis.expire(key, expire_time)
            
            logger.debug(f"Set hash: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set hash: {e}")
            return False
    
    async def get_hash(self, key: str, field: str = None) -> Optional[Any]:
        """ハッシュ取得"""
        try:
            if not self.redis:
                await self.connect()
            
            if field:
                # 特定フィールド取得
                result = await self.redis.hget(key, field)
                return result.decode('utf-8') if result else None
            else:
                # 全フィールド取得
                result = await self.redis.hgetall(key)
                return {k.decode('utf-8'): v.decode('utf-8') for k, v in result.items()}
                
        except Exception as e:
            logger.error(f"Failed to get hash: {e}")
            return None
    
    async def add_to_set(self, key: str, value: str, expire_time: int = None) -> bool:
        """セットに追加"""
        try:
            if not self.redis:
                await self.connect()
            
            await self.redis.sadd(key, value)
            
            # 有効期限設定
            if expire_time is None:
                expire_time = self.expire_time
            await self.redis.expire(key, expire_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to set: {e}")
            return False
    
    async def get_set_members(self, key: str) -> list:
        """セットメンバー取得"""
        try:
            if not self.redis:
                await self.connect()
            
            members = await self.redis.smembers(key)
            return [member.decode('utf-8') for member in members]
            
        except Exception as e:
            logger.error(f"Failed to get set members: {e}")
            return []
    
    async def remove_from_set(self, key: str, value: str) -> bool:
        """セットから削除"""
        try:
            if not self.redis:
                await self.connect()
            
            result = await self.redis.srem(key, value)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to remove from set: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1, expire_time: int = None) -> int:
        """カウンタ増加"""
        try:
            if not self.redis:
                await self.connect()
            
            result = await self.redis.incrby(key, amount)
            
            # 有効期限設定（初回のみ）
            if result == amount and expire_time:
                await self.redis.expire(key, expire_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to increment counter: {e}")
            return 0
    
    async def get_cache_stats(self) -> dict:
        """キャッシュ統計取得"""
        try:
            if not self.redis:
                await self.connect()
            
            info = await self.redis.info()
            
            return {
                "total_keys": info.get("db0", {}).get("keys", 0),
                "memory_used": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    async def clear_cache_pattern(self, pattern: str) -> int:
        """パターンマッチでキャッシュクリア"""
        try:
            if not self.redis:
                await self.connect()
            
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern: {e}")
            return 0