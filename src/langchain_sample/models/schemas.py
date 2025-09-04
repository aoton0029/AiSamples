from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    success: bool
    error: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    success: bool
    message: str

class QueryRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    success: bool

class MCPRequest(BaseModel):
    id: str
    method: str
    params: Dict[str, Any]

class MCPResponse(BaseModel):
    id: str
    result: Optional[Any] = None
    error: Optional[str] = None
    success: bool

class TokenizeRequest(BaseModel):
    text: str
    method: str = "tiktoken"  # "tiktoken" or "transformers"

class TokenizeResponse(BaseModel):
    tokens: List[Any]
    decoded_tokens: List[str]
    token_count: int
    method: str
    success: bool

class ChunkRequest(BaseModel):
    text: str
    method: str = "sentence"  # "sentence" or "token"
    chunk_size: Optional[int] = 512
    chunk_overlap: Optional[int] = 50

class ChunkResponse(BaseModel):
    chunks: List[Dict[str, Any]]
    total_chunks: int
    method: str
    success: bool

class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    dimensions: int
    count: int
    model: str
    success: bool

class SimilaritySearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    document_ids: Optional[List[str]] = None

class SimilaritySearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    top_k: int
    success: bool

class DocumentAnalysisResponse(BaseModel):
    doc_id: str
    metadata: Dict[str, Any]
    vector_store_info: Dict[str, Any]
    success: bool
