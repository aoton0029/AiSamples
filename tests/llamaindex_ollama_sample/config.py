import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()

@dataclass
class Config:
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # Vector store settings
    vector_store_type: str = "chroma"
    persist_dir: str = "./storage"
    
    # Index settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Query settings
    top_k: int = 3
    similarity_threshold: float = 0.7

config = Config()
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
