from redis import Redis
import pickle
from typing import Any, Dict, List, Optional


class RedisClient:
    """Redis client for key-value store operations."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.client = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False  # Support for binary data
        )
        
    def set_cache(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Set cache data."""
        try:
            serialized_value = pickle.dumps(value)
            return self.client.set(key, serialized_value, ex=expire_seconds)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache data."""
        try:
            cached_data = self.client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete cache."""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def set_document_embeddings(self, document_id: str, embeddings: List[List[float]], 
                               expire_seconds: int = 3600) -> bool:
        """Cache document embeddings."""
        key = f"embeddings:{document_id}"
        return self.set_cache(key, embeddings, expire_seconds)
    
    def get_document_embeddings(self, document_id: str) -> Optional[List[List[float]]]:
        """Get document embeddings."""
        key = f"embeddings:{document_id}"
        return self.get_cache(key)
    
    def set_search_results(self, query_hash: str, results: List[Dict[str, Any]], 
                          expire_seconds: int = 1800) -> bool:
        """Cache search results."""
        key = f"search:{query_hash}"
        return self.set_cache(key, results, expire_seconds)
    
    def get_search_results(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Get search results."""
        key = f"search:{query_hash}"
        return self.get_cache(key)
    
    def cache_llm_response(self, prompt_hash: str, response: str, 
                          expire_seconds: int = 3600) -> bool:
        """Cache LLM response."""
        key = f"llm:{prompt_hash}"
        return self.set_cache(key, response, expire_seconds)
    
    def get_llm_response(self, prompt_hash: str) -> Optional[str]:
        """Get LLM response."""
        key = f"llm:{prompt_hash}"
        return self.get_cache(key)
    
    def add_to_processing_queue(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Add task to processing queue."""
        try:
            queue_key = "processing_queue"
            task_item = {
                "task_id": task_id,
                "data": task_data,
                "created_at": str(self.client.time()[0])
            }
            return bool(self.client.lpush(queue_key, pickle.dumps(task_item)))
        except Exception as e:
            print(f"Queue add error: {e}")
            return False
    
    def get_from_processing_queue(self) -> Optional[Dict[str, Any]]:
        """Get task from processing queue."""
        try:
            queue_key = "processing_queue"
            task_data = self.client.brpop(queue_key, timeout=1)
            if task_data:
                return pickle.loads(task_data[1])
            return None
        except Exception as e:
            print(f"Queue get error: {e}")
            return None
    
    def set_session_data(self, session_id: str, data: Dict[str, Any], 
                        expire_seconds: int = 7200) -> bool:
        """Save session data."""
        key = f"session:{session_id}"
        return self.set_cache(key, data, expire_seconds)
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        key = f"session:{session_id}"
        return self.get_cache(key)
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get keys matching a pattern."""
        try:
            keys = self.client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            print(f"Key search error: {e}")
            return []
    
    def flush_all(self) -> bool:
        """Delete all data (for development use)."""
        try:
            return self.client.flushall()
        except Exception as e:
            print(f"Flush all error: {e}")
            return False
    
    def close(self):
        """Close connection."""
        self.client.close()