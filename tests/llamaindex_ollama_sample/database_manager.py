from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.storage.kvstore.redis import RedisKVStore
from config import Config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.vector_store = None
        self.document_store = None
        self.graph_store = None
        self.kv_store = None
        
    def setup_vector_store(self):
        """Setup Milvus vector store"""
        try:
            self.vector_store = MilvusVectorStore(
                host=Config.MILVUS_HOST,
                port=Config.MILVUS_PORT,
                collection_name="llamaindex_collection",
                dim=768,  # dimension for nomic-embed-text
                overwrite=False
            )
            logger.info("Milvus vector store connected")
            return self.vector_store
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return None
    
    def setup_document_store(self):
        """Setup MongoDB document store"""
        try:
            self.document_store = MongoDocumentStore.from_uri(
                uri=Config.MONGODB_URI,
                db_name=Config.MONGODB_DB,
                namespace="documents"
            )
            logger.info("MongoDB document store connected")
            return self.document_store
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return None
    
    def setup_graph_store(self):
        """Setup Neo4j graph store"""
        try:
            self.graph_store = Neo4jGraphStore(
                url=Config.NEO4J_URI,
                username=Config.NEO4J_USERNAME,
                password=Config.NEO4J_PASSWORD,
                database="neo4j"
            )
            logger.info("Neo4j graph store connected")
            return self.graph_store
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return None
    
    def setup_kv_store(self):
        """Setup Redis key-value store"""
        try:
            self.kv_store = RedisKVStore(
                redis_host=Config.REDIS_HOST,
                redis_port=Config.REDIS_PORT,
                redis_db=Config.REDIS_DB
            )
            logger.info("Redis KV store connected")
            return self.kv_store
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None
    
    def setup_all_stores(self):
        """Setup all database stores"""
        return {
            "vector_store": self.setup_vector_store(),
            "document_store": self.setup_document_store(),
            "graph_store": self.setup_graph_store(),
            "kv_store": self.setup_kv_store()
        }
