from typing import List
import numpy as np
from core.ollama_connector import OllamaConnector

class EmbeddingGenerator:
    """Embedding generation for document chunks using a specified model."""
    
    def __init__(self, model_name: str = "nomic-embed-text"):
        self.connector = OllamaConnector()
        self.embedding_model = self.connector.initialize_embedding(model_name)
    
    def generate_embeddings(self, document_chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document chunks."""
        embeddings = []
        for chunk in document_chunks:
            embedding = self.embedding_model.embed(chunk)
            embeddings.append(embedding)
        return embeddings