import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DatabaseConfig:
    """データベース設定クラス"""
    
    # Milvus設定
    MILVUS_HOST = "localhost"
    MILVUS_PORT = 19530
    MILVUS_COLLECTION_NAME = "document_vectors"
    MILVUS_DIMENSION = 1536  # text-embedding-ada-002の次元数
    
    # MongoDB設定
    MONGODB_URI = "mongodb://localhost:27017"
    MONGODB_DATABASE = "document_store"
    MONGODB_COLLECTION = "documents"
    
    # Neo4j設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "password"
    
    # Redis設定
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_EXPIRE_TIME = 3600  # 1時間
    
    # Ollama設定
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama2"
    OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
    
    # その他設定
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_RESULTS = 10

@dataclass
class SystemConfig:
    """システム全体設定"""
    
    # ログ設定
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ファイル処理設定
    SUPPORTED_FILE_TYPES = [".txt", ".pdf", ".docx", ".md"]
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # 検索設定
    SIMILARITY_THRESHOLD = 0.7
    VECTOR_SEARCH_TOP_K = 20
    RERANK_TOP_K = 5

# 環境変数から設定を上書き
def load_config_from_env():
    """環境変数から設定を読み込み"""
    config = DatabaseConfig()
    
    # 環境変数があれば上書き
    if os.getenv("MILVUS_HOST"):
        config.MILVUS_HOST = os.getenv("MILVUS_HOST")
    if os.getenv("MONGODB_URI"):
        config.MONGODB_URI = os.getenv("MONGODB_URI")
    if os.getenv("NEO4J_URI"):
        config.NEO4J_URI = os.getenv("NEO4J_URI")
    if os.getenv("REDIS_HOST"):
        config.REDIS_HOST = os.getenv("REDIS_HOST")
    if os.getenv("OLLAMA_BASE_URL"):
        config.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
    
    return config

# グローバル設定インスタンス
db_config = load_config_from_env()
sys_config = SystemConfig()