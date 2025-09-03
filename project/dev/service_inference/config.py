import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "inference-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    mcp_server_port: int = 8005
    mcp_server_host: str = "0.0.0.0"
    
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model settings
    default_model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    
    log_level: str = "INFO"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
