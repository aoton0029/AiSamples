import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service configuration
    service_name: str = "chunking-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # MCP Server configuration
    mcp_server_port: int = 8003
    mcp_server_host: str = "0.0.0.0"
    
    # Chunking settings
    default_chunking_method: str = "recursive"
    default_chunk_size: int = 1000
    default_overlap: int = 100
    min_chunk_size: int = 100
    max_content_size: int = 10000000  # 10MB
    
    # Document processing settings
    preserve_structure: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
