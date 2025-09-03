from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import numpy as np


class EmbeddingMethod(str, Enum):
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    HUGGINGFACE = "huggingface"
    LLAMAINDEX = "llamaindex"
    LANGCHAIN = "langchain"


class EmbeddingRequest(BaseModel):
    text: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")
    method: EmbeddingMethod = Field(default=EmbeddingMethod.SENTENCE_TRANSFORMERS, description="Embedding method")
    model_name: Optional[str] = Field(default=None, description="Model name for embedding")
    batch_size: Optional[int] = Field(default=32, description="Batch size for processing")
    normalize: bool = Field(default=True, description="Whether to normalize embeddings")


class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimensions: int = Field(..., description="Embedding dimensions")
    model_name: str = Field(..., description="Model used for embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        arbitrary_types_allowed = True


class EmbeddingConfig(BaseModel):
    default_method: EmbeddingMethod = EmbeddingMethod.SENTENCE_TRANSFORMERS
    default_model: str = "all-MiniLM-L6-v2"
    openai_model: str = "text-embedding-ada-002"
    max_batch_size: int = 100
    max_text_length: int = 8192
    supported_models: List[str] = Field(default_factory=lambda: [
        "all-MiniLM-L6-v2",
        "all-mpnet-base-v2",
        "text-embedding-ada-002",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ])
