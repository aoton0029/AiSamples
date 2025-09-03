import asyncio
from typing import Any, Dict, List, Union
from fastmcp import FastMCP
from loguru import logger

from .config import settings
from .models import ChunkingRequest, ChunkingResponse
from .handlers import ChunkingHandler


# Initialize MCP server
mcp = FastMCP("Chunking Service")

# Initialize handlers
chunking_handler = ChunkingHandler()


@mcp.tool()
async def chunk_text(
    content: Union[str, bytes],
    method: str = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    document_type: str = "text",
    separators: List[str] = None,
    preserve_structure: bool = True,
    min_chunk_size: int = 100
) -> Dict[str, Any]:
    """
    Chunk content using specified method and parameters.
    
    Args:
        content: Content to chunk (text or bytes)
        method: Chunking method (fixed_size, recursive, semantic, sentence_based, paragraph_based, token_based, document_based)
        chunk_size: Target size of each chunk
        chunk_overlap: Overlap between chunks
        document_type: Type of document (text, pdf, docx, html, markdown)
        separators: Custom separators for chunking
        preserve_structure: Whether to preserve document structure
        min_chunk_size: Minimum chunk size
    
    Returns:
        Dictionary with chunks, metadata, and processing information
    """
    try:
        request = ChunkingRequest(
            content=content,
            method=method,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            document_type=document_type,
            separators=separators,
            preserve_structure=preserve_structure,
            min_chunk_size=min_chunk_size
        )
        
        response = await chunking_handler.chunk_content(request)
        
        return {
            "chunks": response.chunks,
            "metadata": [meta.dict() for meta in response.metadata],
            "total_chunks": response.total_chunks,
            "total_characters": response.total_characters,
            "method_used": response.method_used,
            "processing_info": response.processing_info
        }
    except Exception as e:
        logger.error(f"Error in chunk_text tool: {e}")
        raise


@mcp.tool()
async def chunk_document(
    file_content: bytes,
    document_type: str,
    method: str = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 100
) -> Dict[str, Any]:
    """
    Chunk document content from various file formats.
    
    Args:
        file_content: Binary content of the document
        document_type: Type of document (pdf, docx, html, markdown, text)
        method: Chunking method
        chunk_size: Target size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        Dictionary with chunks and metadata
    """
    try:
        request = ChunkingRequest(
            content=file_content,
            method=method,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            document_type=document_type
        )
        
        response = await chunking_handler.chunk_content(request)
        
        return {
            "chunks": response.chunks,
            "metadata": [meta.dict() for meta in response.metadata],
            "total_chunks": response.total_chunks,
            "total_characters": response.total_characters,
            "extracted_text_length": response.total_characters,
            "document_type": document_type
        }
    except Exception as e:
        logger.error(f"Error in chunk_document tool: {e}")
        raise


@mcp.tool()
async def smart_chunk(
    content: Union[str, bytes],
    target_size: int = 1000,
    document_type: str = "text",
    preserve_sentences: bool = True,
    preserve_paragraphs: bool = True
) -> Dict[str, Any]:
    """
    Intelligently chunk content using the best method for the content type.
    
    Args:
        content: Content to chunk
        target_size: Target chunk size
        document_type: Document type
        preserve_sentences: Whether to preserve sentence boundaries
        preserve_paragraphs: Whether to preserve paragraph boundaries
    
    Returns:
        Dictionary with chunks and metadata
    """
    try:
        # Choose best method based on content type and preferences
        if preserve_paragraphs:
            method = "paragraph_based"
        elif preserve_sentences:
            method = "sentence_based"
        else:
            method = "recursive"
        
        request = ChunkingRequest(
            content=content,
            method=method,
            chunk_size=target_size,
            chunk_overlap=min(target_size // 10, 100),  # 10% overlap or 100 chars
            document_type=document_type,
            preserve_structure=True
        )
        
        response = await chunking_handler.chunk_content(request)
        
        return {
            "chunks": response.chunks,
            "metadata": [meta.dict() for meta in response.metadata],
            "method_selected": response.method_used,
            "total_chunks": response.total_chunks,
            "average_chunk_size": response.total_characters / response.total_chunks if response.total_chunks > 0 else 0,
            "processing_info": response.processing_info
        }
    except Exception as e:
        logger.error(f"Error in smart_chunk tool: {e}")
        raise


@mcp.tool()
async def analyze_chunks(
    chunks: List[str]
) -> Dict[str, Any]:
    """
    Analyze chunk statistics and quality.
    
    Args:
        chunks: List of text chunks to analyze
    
    Returns:
        Dictionary with chunk analysis results
    """
    try:
        if not chunks:
            return {"error": "No chunks provided"}
        
        chunk_sizes = [len(chunk) for chunk in chunks]
        total_chars = sum(chunk_sizes)
        
        analysis = {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "average_chunk_size": total_chars / len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "median_chunk_size": sorted(chunk_sizes)[len(chunk_sizes) // 2],
            "size_distribution": {
                "very_small": len([s for s in chunk_sizes if s < 100]),
                "small": len([s for s in chunk_sizes if 100 <= s < 500]),
                "medium": len([s for s in chunk_sizes if 500 <= s < 1000]),
                "large": len([s for s in chunk_sizes if 1000 <= s < 2000]),
                "very_large": len([s for s in chunk_sizes if s >= 2000])
            },
            "quality_metrics": {
                "size_consistency": 1.0 - (max(chunk_sizes) - min(chunk_sizes)) / max(chunk_sizes),
                "empty_chunks": len([c for c in chunks if not c.strip()]),
                "single_word_chunks": len([c for c in chunks if len(c.split()) == 1])
            }
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Error in analyze_chunks tool: {e}")
        raise


@mcp.resource()
async def get_supported_methods() -> str:
    """Get list of supported chunking methods."""
    methods = {
        "fixed_size": "Fixed character size chunks",
        "recursive": "Recursive character splitting with smart separators",
        "semantic": "Semantic-based chunking using sentence boundaries",
        "sentence_based": "Sentence-boundary preserving chunks",
        "paragraph_based": "Paragraph-boundary preserving chunks",
        "token_based": "Token-count based chunks",
        "document_based": "Document structure-aware chunking"
    }
    return f"Supported chunking methods: {methods}"


@mcp.resource()
async def get_supported_formats() -> str:
    """Get list of supported document formats."""
    formats = {
        "text": "Plain text files",
        "pdf": "PDF documents",
        "docx": "Microsoft Word documents",
        "html": "HTML web pages",
        "markdown": "Markdown documents",
        "csv": "CSV files",
        "json": "JSON documents",
        "xml": "XML documents"
    }
    return f"Supported document formats: {formats}"


@mcp.resource()
async def get_service_info() -> str:
    """Get service information and configuration."""
    return f"""
Chunking Service Information:
- Service Name: {settings.service_name}
- Version: {settings.service_version}
- Default Method: {settings.default_chunking_method}
- Default Chunk Size: {settings.default_chunk_size}
- Default Overlap: {settings.default_overlap}
- Max Content Size: {settings.max_content_size} characters
"""


async def main():
    """Run the MCP server"""
    logger.add(
        "logs/chunking_service.log",
        rotation="1 day",
        retention="30 days",
        format=settings.log_format,
        level=settings.log_level
    )
    
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    try:
        # Run MCP server
        await mcp.run(
            transport_type="stdio",
            host=settings.mcp_server_host,
            port=settings.mcp_server_port
        )
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
