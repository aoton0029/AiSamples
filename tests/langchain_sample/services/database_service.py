import redis
import logging
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import json
import asyncio

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 mongodb_url: str = "mongodb://localhost:27017",
                 milvus_host: str = "localhost",
                 milvus_port: int = 19530):
        # Redis (Key-Value DB)
        self.redis_url = redis_url
        self.redis_client = None
        
        # MongoDB (Document DB)
        self.mongodb_url = mongodb_url
        self.mongo_client = None
        self.mongo_db = None
        
        # Milvus (Vector DB)
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.milvus_collection = None
        
    async def initialize(self):
        """Initialize all database connections"""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await asyncio.to_thread(self.redis_client.ping)
            logger.info("Redis connection established")
            
            # Initialize MongoDB
            self.mongo_client = AsyncIOMotorClient(self.mongodb_url)
            self.mongo_db = self.mongo_client.ai_documents
            # Test connection
            await self.mongo_client.admin.command('ping')
            logger.info("MongoDB connection established")
            
            # Initialize Milvus
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port
            )
            await self._setup_milvus_collection()
            logger.info("Milvus connection established")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    async def _setup_milvus_collection(self):
        """Setup Milvus collection for document embeddings"""
        collection_name = "document_embeddings"
        
        # Check if collection exists
        if utility.has_collection(collection_name):
            self.milvus_collection = Collection(collection_name)
            logger.info(f"Using existing Milvus collection: {collection_name}")
        else:
            # Create collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="chunk_id", dtype=DataType.INT64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),  # MiniLM embedding dimension
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
            ]
            
            schema = CollectionSchema(fields, "Document embeddings collection")
            self.milvus_collection = Collection(collection_name, schema)
            
            # Create index
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            self.milvus_collection.create_index("embedding", index_params)
            logger.info(f"Created new Milvus collection: {collection_name}")
        
        # Load collection
        self.milvus_collection.load()
    
    # Redis operations (Key-Value DB)
    async def redis_set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = await asyncio.to_thread(
                self.redis_client.set, key, value, ex=expire
            )
            return result
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            raise
    
    async def redis_get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = await asyncio.to_thread(self.redis_client.get, key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            raise
    
    async def redis_delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            result = await asyncio.to_thread(self.redis_client.delete, key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            raise
    
    # MongoDB operations (Document DB)
    async def mongo_insert_document(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert document into MongoDB"""
        try:
            collection = self.mongo_db[collection_name]
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"MongoDB insert error: {e}")
            raise
    
    async def mongo_find_documents(self, collection_name: str, query: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find documents in MongoDB"""
        try:
            collection = self.mongo_db[collection_name]
            cursor = collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
                documents.append(doc)
            return documents
        except Exception as e:
            logger.error(f"MongoDB find error: {e}")
            raise
    
    async def mongo_update_document(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """Update document in MongoDB"""
        try:
            collection = self.mongo_db[collection_name]
            result = await collection.update_one(query, {"$set": update})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"MongoDB update error: {e}")
            raise
    
    async def mongo_delete_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """Delete documents from MongoDB"""
        try:
            collection = self.mongo_db[collection_name]
            result = await collection.delete_many(query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"MongoDB delete error: {e}")
            raise
    
    # Milvus operations (Vector DB)
    async def milvus_insert_vectors(self, vectors_data: List[Dict[str, Any]]) -> List[str]:
        """Insert vectors into Milvus"""
        try:
            data = [
                [item["id"] for item in vectors_data],
                [item["doc_id"] for item in vectors_data],
                [item["chunk_id"] for item in vectors_data],
                [item["embedding"] for item in vectors_data],
                [item["text"] for item in vectors_data]
            ]
            
            result = await asyncio.to_thread(self.milvus_collection.insert, data)
            await asyncio.to_thread(self.milvus_collection.flush)
            return result.primary_keys
        except Exception as e:
            logger.error(f"Milvus insert error: {e}")
            raise
    
    async def milvus_search_vectors(self, query_vector: List[float], top_k: int = 5, expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search similar vectors in Milvus"""
        try:
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = await asyncio.to_thread(
                self.milvus_collection.search,
                [query_vector],
                "embedding",
                search_params,
                limit=top_k,
                expr=expr,
                output_fields=["doc_id", "chunk_id", "text"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "id": hit.id,
                        "doc_id": hit.entity.get("doc_id"),
                        "chunk_id": hit.entity.get("chunk_id"),
                        "text": hit.entity.get("text"),
                        "distance": hit.distance,
                        "similarity": 1 - hit.distance
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Milvus search error: {e}")
            raise
    
    async def milvus_delete_vectors(self, expr: str) -> bool:
        """Delete vectors from Milvus"""
        try:
            result = await asyncio.to_thread(self.milvus_collection.delete, expr)
            await asyncio.to_thread(self.milvus_collection.flush)
            return True
        except Exception as e:
            logger.error(f"Milvus delete error: {e}")
            raise
    
    async def close_connections(self):
        """Close all database connections"""
        try:
            if self.redis_client:
                await asyncio.to_thread(self.redis_client.close)
            
            if self.mongo_client:
                self.mongo_client.close()
            
            connections.disconnect("default")
            
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
