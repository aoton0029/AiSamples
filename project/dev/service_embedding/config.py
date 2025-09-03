import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service configuration
    service_name: str = "embedding-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # MCP Server configuration
    mcp_server_port: int = 8002
    mcp_server_host: str = "0.0.0.0"
    
    # Embedding settings
    default_embedding_method: str = "sentence_transformers"
    default_embedding_model: str = "all-MiniLM-L6-v2"
    max_batch_size: int = 100
    max_text_length: int = 8192
    
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_embedding_model: str = "text-embedding-ada-002"
    
    # HuggingFace settings
    hf_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
