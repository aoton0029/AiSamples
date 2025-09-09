from pymongo import MongoClient as PyMongoClient
from typing import Dict, List, Any, Optional
import datetime
from bson import ObjectId


class MongoClient:
    """MongoDBを使用したドキュメントメタデータ管理クラス"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017", database_name: str = "rag_system"):
        self.client = PyMongoClient(connection_string)
        self.db = self.client[database_name]
        self.documents = self.db.documents
        self.metadata = self.db.metadata
        
    def save_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> str:
        """ドキュメントとメタデータを保存"""
        doc = {
            "document_id": document_id,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        result = self.documents.insert_one(doc)
        return str(result.inserted_id)
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """ドキュメントを取得"""
        return self.documents.find_one({"document_id": document_id})
    
    def update_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """メタデータを更新"""
        result = self.documents.update_one(
            {"document_id": document_id},
            {
                "$set": {
                    "metadata": metadata,
                    "updated_at": datetime.datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    def search_by_metadata(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """メタデータで検索"""
        mongo_query = {}
        for key, value in query.items():
            mongo_query[f"metadata.{key}"] = value
        
        return list(self.documents.find(mongo_query))
    
    def delete_document(self, document_id: str) -> bool:
        """ドキュメントを削除"""
        result = self.documents.delete_one({"document_id": document_id})
        return result.deleted_count > 0
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """全ドキュメントを取得"""
        return list(self.documents.find())
    
    def close(self):
        """接続を閉じる"""
        self.client.close()