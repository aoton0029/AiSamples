from typing import Dict, Any

class DatabaseConfig:
    """Database connection configurations for MongoDB, Neo4j, Milvus, and Redis."""
    
    def __init__(self):
        self.mongo_config = {
            "connection_string": "mongodb://localhost:27017",
            "database_name": "rag_system"
        }
        
        self.neo4j_config = {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password"
        }
        
        self.milvus_config = {
            "host": "localhost",
            "port": "19530",
            "collection_name": "document_vectors"
        }
        
        self.redis_config = {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None
        }
    
    def get_mongo_config(self) -> Dict[str, Any]:
        return self.mongo_config
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        return self.neo4j_config
    
    def get_milvus_config(self) -> Dict[str, Any]:
        return self.milvus_config
    
    def get_redis_config(self) -> Dict[str, Any]:
        return self.redis_config