from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from typing import Optional
import requests
import logging

logger = logging.getLogger(__name__)

class OllamaConnector:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self._llm = None
        self._embedding = None
    
    def get_llm(self) -> Ollama:
        if self._llm is None:
            self._llm = Ollama(
                model=self.model,
                base_url=self.base_url,
                request_timeout=120.0
            )
        return self._llm
    
    def get_embedding(self) -> OllamaEmbedding:
        if self._embedding is None:
            self._embedding = OllamaEmbedding(
                model_name=self.model,
                base_url=self.base_url
            )
        return self._embedding
    
    def is_model_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            models = response.json().get("models", [])
            return any(model["name"].startswith(self.model) for model in models)
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
