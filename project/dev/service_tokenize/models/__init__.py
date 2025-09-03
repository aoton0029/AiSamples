from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TokenizeMethod(str, Enum):
    TIKTOKEN = "tiktoken"
    HUGGINGFACE = "huggingface" 
    SPACY = "spacy"
    CUSTOM = "custom"


class TokenizeRequest(BaseModel):
    text: str = Field(..., description="Text to tokenize")
    method: TokenizeMethod = Field(default=TokenizeMethod.TIKTOKEN, description="Tokenization method")
    model_name: Optional[str] = Field(default=None, description="Model name for tokenization")
    max_tokens: Optional[int] = Field(default=None, description="Maximum number of tokens")
    chunk_overlap: Optional[int] = Field(default=0, description="Chunk overlap for splitting")


class TokenizeResponse(BaseModel):
    tokens: List[str] = Field(..., description="List of tokens")
    token_count: int = Field(..., description="Number of tokens")
    chunks: Optional[List[str]] = Field(default=None, description="Text chunks if splitting was requested")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TokenizeConfig(BaseModel):
    default_method: TokenizeMethod = TokenizeMethod.TIKTOKEN
    default_model: str = "gpt-3.5-turbo"
    max_text_length: int = 1000000
    supported_models: List[str] = Field(default_factory=lambda: [
        "gpt-3.5-turbo",
        "gpt-4",
        "text-davinci-003",
        "bert-base-uncased",
        "distilbert-base-uncased"
    ])
