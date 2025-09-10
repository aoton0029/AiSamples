import logging
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from models import DocumentRepository, Document
from config import db_config

logger = logging.getLogger(__name__)

class MongoRepository(DocumentRepository):
    """MongoDBドキュメントリポジトリ"""
    
    def __init__(self):
        self.uri = db_config.MONGODB_URI
        self.database_name = db_config.MONGODB_DATABASE
        self.collection_name = db_config.MONGODB_COLLECTION
        self.client = None
        self.database = None
        self.collection = None
    
    async def connect(self) -> bool:
        """MongoDBに接続"""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # 接続確認
            await self.client.admin.command('ping')
            
            # インデックス作成
            await self._create_indexes()
            
            logger.info(f"Connected to MongoDB at {self.uri}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """MongoDBから切断"""
        try:
            if self.client:
                self.client.close()
            logger.info("Disconnected from MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from MongoDB: {e}")
            return False
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    async def _create_indexes(self):
        """インデックス作成"""
        try:
            # テキスト検索用インデックス
            await self.collection.create_index([
                ("title", "text"),
                ("content", "text"),
                ("tags", "text")
            ])
            
            # その他のインデックス
            await self.collection.create_index("file_type")
            await self.collection.create_index("created_at")
            await self.collection.create_index("tags")
            
            logger.info("Created MongoDB indexes")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def save_document(self, document: Document) -> str:
        """ドキュメント保存"""
        try:
            if not self.collection:
                await self.connect()
            
            # ドキュメントをDict形式に変換
            doc_dict = {
                "_id": document.id,
                "title": document.title,
                "content": document.content,
                "file_path": document.file_path,
                "file_type": document.file_type,
                "metadata": document.metadata,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "tags": document.tags
            }
            
            # Upsert操作
            result = await self.collection.replace_one(
                {"_id": document.id},
                doc_dict,
                upsert=True
            )
            
            logger.info(f"Saved document: {document.id}")
            return document.id
            
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return ""
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """ドキュメント取得"""
        try:
            if not self.collection:
                await self.connect()
            
            doc_dict = await self.collection.find_one({"_id": document_id})
            
            if doc_dict:
                return Document(
                    id=doc_dict["_id"],
                    title=doc_dict["title"],
                    content=doc_dict["content"],
                    file_path=doc_dict["file_path"],
                    file_type=doc_dict["file_type"],
                    metadata=doc_dict["metadata"],
                    created_at=doc_dict["created_at"],
                    updated_at=doc_dict["updated_at"],
                    tags=doc_dict.get("tags", [])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    async def search_documents(self, query: Dict[str, Any]) -> List[Document]:
        """ドキュメント検索"""
        try:
            if not self.collection:
                await self.connect()
            
            # クエリ構築
            mongo_query = {}
            
            # テキスト検索
            if "text" in query:
                mongo_query["$text"] = {"$search": query["text"]}
            
            # ファイルタイプフィルタ
            if "file_type" in query:
                mongo_query["file_type"] = query["file_type"]
            
            # タグフィルタ
            if "tags" in query:
                mongo_query["tags"] = {"$in": query["tags"]}
            
            # 日付範囲フィルタ
            if "date_from" in query or "date_to" in query:
                date_filter = {}
                if "date_from" in query:
                    date_filter["$gte"] = query["date_from"]
                if "date_to" in query:
                    date_filter["$lte"] = query["date_to"]
                mongo_query["created_at"] = date_filter
            
            # メタデータフィルタ
            if "metadata" in query:
                for key, value in query["metadata"].items():
                    mongo_query[f"metadata.{key}"] = value
            
            # 検索実行
            cursor = self.collection.find(mongo_query)
            
            # リミット設定
            if "limit" in query:
                cursor = cursor.limit(query["limit"])
            
            # 結果変換
            documents = []
            async for doc_dict in cursor:
                document = Document(
                    id=doc_dict["_id"],
                    title=doc_dict["title"],
                    content=doc_dict["content"],
                    file_path=doc_dict["file_path"],
                    file_type=doc_dict["file_type"],
                    metadata=doc_dict["metadata"],
                    created_at=doc_dict["created_at"],
                    updated_at=doc_dict["updated_at"],
                    tags=doc_dict.get("tags", [])
                )
                documents.append(document)
            
            logger.info(f"Found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    async def update_document(self, document: Document) -> bool:
        """ドキュメント更新"""
        try:
            if not self.collection:
                await self.connect()
            
            # 更新時刻を設定
            document.updated_at = datetime.now()
            
            # 更新実行
            result = await self.collection.update_one(
                {"_id": document.id},
                {
                    "$set": {
                        "title": document.title,
                        "content": document.content,
                        "file_path": document.file_path,
                        "file_type": document.file_type,
                        "metadata": document.metadata,
                        "updated_at": document.updated_at,
                        "tags": document.tags
                    }
                }
            )
            
            logger.info(f"Updated document: {document.id}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """ドキュメント削除"""
        try:
            if not self.collection:
                await self.connect()
            
            result = await self.collection.delete_one({"_id": document_id})
            
            logger.info(f"Deleted document: {document_id}")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def get_documents_by_ids(self, document_ids: List[str]) -> List[Document]:
        """複数ドキュメントID取得"""
        try:
            if not self.collection:
                await self.connect()
            
            cursor = self.collection.find({"_id": {"$in": document_ids}})
            
            documents = []
            async for doc_dict in cursor:
                document = Document(
                    id=doc_dict["_id"],
                    title=doc_dict["title"],
                    content=doc_dict["content"],
                    file_path=doc_dict["file_path"],
                    file_type=doc_dict["file_type"],
                    metadata=doc_dict["metadata"],
                    created_at=doc_dict["created_at"],
                    updated_at=doc_dict["updated_at"],
                    tags=doc_dict.get("tags", [])
                )
                documents.append(document)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get documents by IDs: {e}")
            return []
    
    async def get_collection_stats(self) -> dict:
        """コレクション統計取得"""
        try:
            if not self.collection:
                await self.connect()
            
            total_count = await self.collection.count_documents({})
            
            # ファイルタイプ別統計
            file_type_stats = await self.collection.aggregate([
                {"$group": {"_id": "$file_type", "count": {"$sum": 1}}}
            ]).to_list(None)
            
            return {
                "total_documents": total_count,
                "file_type_distribution": {stat["_id"]: stat["count"] for stat in file_type_stats}
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}