import asyncio
from typing import Any, Dict, List
from fastmcp import FastMCP
from loguru import logger

from .config import settings
from .models import TokenizeRequest, TokenizeResponse
from .handlers import TokenizeHandler


# Initialize MCP server
mcp = FastMCP("Tokenize Service")

# Initialize handlers
tokenize_handler = TokenizeHandler()


@mcp.tool()
async def tokenize_text(
    text: str,
    method: str = "tiktoken",
    model_name: str = None,
    max_tokens: int = None,
    chunk_overlap: int = 0
) -> Dict[str, Any]:
    """
    Tokenize text using specified method and model.
    
    Args:
        text: Text to tokenize
        method: Tokenization method (tiktoken, huggingface, spacy, custom)
        model_name: Model name for tokenization
        max_tokens: Maximum number of tokens
        chunk_overlap: Chunk overlap for splitting
    
    Returns:
        Dictionary with tokens, token_count, chunks, and metadata
    """
    try:
        request = TokenizeRequest(
            text=text,
            method=method,
            model_name=model_name,
            max_tokens=max_tokens,
            chunk_overlap=chunk_overlap
        )
        
        response = await tokenize_handler.tokenize_text(request)
        
        return {
            "tokens": response.tokens,
            "token_count": response.token_count,
            "chunks": response.chunks,
            "metadata": response.metadata
        }
    except Exception as e:
        logger.error(f"Error in tokenize_text tool: {e}")
        raise


@mcp.tool()
async def count_tokens(
    text: str,
    method: str = "tiktoken",
    model_name: str = None
) -> Dict[str, Any]:
    """
    Count tokens in text without returning the actual tokens.
    
    Args:
        text: Text to count tokens for
        method: Tokenization method
        model_name: Model name for tokenization
    
    Returns:
        Dictionary with token count and metadata
    """
    try:
        request = TokenizeRequest(
            text=text,
            method=method,
            model_name=model_name
        )
        
        response = await tokenize_handler.tokenize_text(request)
        
        return {
            "token_count": response.token_count,
            "text_length": len(text),
            "metadata": response.metadata
        }
    except Exception as e:
        logger.error(f"Error in count_tokens tool: {e}")
        raise


@mcp.tool()
async def create_text_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    method: str = "tiktoken",
    model_name: str = None
) -> Dict[str, Any]:
    """
    Split text into chunks with specified size and overlap.
    
    Args:
        text: Text to split
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Number of overlapping tokens
        method: Tokenization method
        model_name: Model name for tokenization
    
    Returns:
        Dictionary with chunks and metadata
    """
    try:
        request = TokenizeRequest(
            text=text,
            method=method,
            model_name=model_name,
            max_tokens=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        response = await tokenize_handler.tokenize_text(request)
        
        return {
            "chunks": response.chunks,
            "chunk_count": len(response.chunks) if response.chunks else 0,
            "total_tokens": response.token_count,
            "metadata": response.metadata
        }
    except Exception as e:
        logger.error(f"Error in create_text_chunks tool: {e}")
        raise


@mcp.resource()
async def get_supported_models() -> str:
    """Get list of supported tokenization models."""
    models = {
        "tiktoken": ["gpt-3.5-turbo", "gpt-4", "text-davinci-003"],
        "huggingface": ["bert-base-uncased", "distilbert-base-uncased", "roberta-base"]
    }
    return f"Supported models: {models}"


@mcp.resource()
async def get_service_info() -> str:
    """Get service information and configuration."""
    return f"""
Tokenize Service Information:
- Service Name: {settings.service_name}
- Version: {settings.service_version}
- Default Tokenizer: {settings.default_tokenizer}
- Max Text Length: {settings.max_text_length}
- Default Chunk Size: {settings.chunk_size}
- Default Chunk Overlap: {settings.chunk_overlap}
"""


async def main():
    """Run the MCP server"""
    logger.add(
        "logs/tokenize_service.log",
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
