import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service configuration
    service_name: str = "tokenize-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # MCP Server configuration
    mcp_server_port: int = 8001
    mcp_server_host: str = "0.0.0.0"
    
    # Tokenization settings
    default_tokenizer: str = "tiktoken"
    max_text_length: int = 1000000
    chunk_size: int = 1000
    chunk_overlap: int = 100
    
    # Model settings
    openai_model: str = "gpt-3.5-turbo"
    huggingface_model: str = "bert-base-uncased"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
