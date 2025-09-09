import redis
import json
import pickle
from typing import Any, Dict, List, Optional, Union


class RedisClient:
    """Redisを使用したキーバリューストア操作クラス"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False  # バイナリデータ対応
        )
        
    def set_cache(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """キャッシュデータを設定"""
        try:
            serialized_value = pickle.dumps(value)
            return self.client.set(key, serialized_value, ex=expire_seconds)
        except Exception as e:
            print(f"キャッシュ設定エラー: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """キャッシュデータを取得"""
        try:
            cached_data = self.client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
            return None
        except Exception as e:
            print(f"キャッシュ取得エラー: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """キャッシュを削除"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"キャッシュ削除エラー: {e}")
            return False
    
    def set_document_embeddings(self, document_id: str, embeddings: List[List[float]], 
                               expire_seconds: int = 3600) -> bool:
        """ドキュメントの埋め込みベクトルをキャッシュ"""
        key = f"embeddings:{document_id}"
        return self.set_cache(key, embeddings, expire_seconds)
    
    def get_document_embeddings(self, document_id: str) -> Optional[List[List[float]]]:
        """ドキュメントの埋め込みベクトルを取得"""
        key = f"embeddings:{document_id}"
        return self.get_cache(key)
    
    def set_search_results(self, query_hash: str, results: List[Dict[str, Any]], 
                          expire_seconds: int = 1800) -> bool:
        """検索結果をキャッシュ"""
        key = f"search:{query_hash}"
        return self.set_cache(key, results, expire_seconds)
    
    def get_search_results(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """検索結果を取得"""
        key = f"search:{query_hash}"
        return self.get_cache(key)
    
    def cache_llm_response(self, prompt_hash: str, response: str, 
                          expire_seconds: int = 3600) -> bool:
        """LLMレスポンスをキャッシュ"""
        key = f"llm:{prompt_hash}"
        return self.set_cache(key, response, expire_seconds)
    
    def get_llm_response(self, prompt_hash: str) -> Optional[str]:
        """LLMレスポンスを取得"""
        key = f"llm:{prompt_hash}"
        return self.get_cache(key)
    
    def add_to_processing_queue(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """処理キューにタスクを追加"""
        try:
            queue_key = "processing_queue"
            task_item = {
                "task_id": task_id,
                "data": task_data,
                "created_at": str(self.client.time()[0])
            }
            return bool(self.client.lpush(queue_key, pickle.dumps(task_item)))
        except Exception as e:
            print(f"キュー追加エラー: {e}")
            return False
    
    def get_from_processing_queue(self) -> Optional[Dict[str, Any]]:
        """処理キューからタスクを取得"""
        try:
            queue_key = "processing_queue"
            task_data = self.client.brpop(queue_key, timeout=1)
            if task_data:
                return pickle.loads(task_data[1])
            return None
        except Exception as e:
            print(f"キュー取得エラー: {e}")
            return None
    
    def set_session_data(self, session_id: str, data: Dict[str, Any], 
                        expire_seconds: int = 7200) -> bool:
        """セッションデータを保存"""
        key = f"session:{session_id}"
        return self.set_cache(key, data, expire_seconds)
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータを取得"""
        key = f"session:{session_id}"
        return self.get_cache(key)
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """パターンに一致するキーを取得"""
        try:
            keys = self.client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            print(f"キー検索エラー: {e}")
            return []
    
    def flush_all(self) -> bool:
        """全データを削除（開発用）"""
        try:
            return self.client.flushall()
        except Exception as e:
            print(f"全削除エラー: {e}")
            return False
    
    def close(self):
        """接続を閉じる"""
        self.client.close()