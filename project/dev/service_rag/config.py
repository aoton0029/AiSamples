import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "rag-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    mcp_server_port: int = 8004
    mcp_server_host: str = "0.0.0.0"
    
    # Database connections
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    redis_host: str = "localhost" 
    redis_port: int = 6379
    mongodb_url: str = "mongodb://localhost:27017"
    neo4j_url: str = "bolt://localhost:7687"
    
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    log_level: str = "INFO"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
