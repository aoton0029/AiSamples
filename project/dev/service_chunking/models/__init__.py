from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ChunkingMethod(str, Enum):
    FIXED_SIZE = "fixed_size"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    DOCUMENT_BASED = "document_based"
    SENTENCE_BASED = "sentence_based"
    PARAGRAPH_BASED = "paragraph_based"
    TOKEN_BASED = "token_based"


class DocumentType(str, Enum):
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"
    JSON = "json"
    XML = "xml"


class ChunkingRequest(BaseModel):
    content: Union[str, bytes] = Field(..., description="Content to chunk")
    method: ChunkingMethod = Field(default=ChunkingMethod.RECURSIVE, description="Chunking method")
    chunk_size: int = Field(default=1000, description="Target size of each chunk")
    chunk_overlap: int = Field(default=100, description="Overlap between chunks")
    document_type: DocumentType = Field(default=DocumentType.TEXT, description="Type of document")
    separators: Optional[List[str]] = Field(default=None, description="Custom separators for chunking")
    preserve_structure: bool = Field(default=True, description="Whether to preserve document structure")
    min_chunk_size: int = Field(default=100, description="Minimum chunk size")
    max_chunk_size: Optional[int] = Field(default=None, description="Maximum chunk size")


class ChunkMetadata(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    start_index: int = Field(..., description="Starting character index")
    end_index: int = Field(..., description="Ending character index")
    chunk_size: int = Field(..., description="Size of chunk in characters")
    token_count: Optional[int] = Field(default=None, description="Token count if calculated")
    section_title: Optional[str] = Field(default=None, description="Section title if available")
    page_number: Optional[int] = Field(default=None, description="Page number for document types")
    hierarchy_level: Optional[int] = Field(default=None, description="Hierarchy level in document")


class ChunkingResponse(BaseModel):
    chunks: List[str] = Field(..., description="List of text chunks")
    metadata: List[ChunkMetadata] = Field(..., description="Metadata for each chunk")
    total_chunks: int = Field(..., description="Total number of chunks")
    total_characters: int = Field(..., description="Total characters processed")
    method_used: ChunkingMethod = Field(..., description="Chunking method used")
    processing_info: Dict[str, Any] = Field(default_factory=dict, description="Processing information")


class ChunkingConfig(BaseModel):
    default_method: ChunkingMethod = ChunkingMethod.RECURSIVE
    default_chunk_size: int = 1000
    default_overlap: int = 100
    max_content_size: int = 10000000  # 10MB
    supported_formats: List[DocumentType] = Field(default_factory=lambda: [
        DocumentType.TEXT,
        DocumentType.PDF,
        DocumentType.DOCX,
        DocumentType.HTML,
        DocumentType.MARKDOWN
    ])
