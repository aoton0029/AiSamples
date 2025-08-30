import os

class Settings:
    # Database settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}")
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    MILVUS_URI = os.getenv("MILVUS_URI", "tcp://milvus:19530")
    
    # Ollama service settings
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    
    # Other settings
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")