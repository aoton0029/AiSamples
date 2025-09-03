import asyncio
from typing import Any, Dict, List, Union
from fastmcp import FastMCP
from loguru import logger

from .config import settings
from .models import EmbeddingRequest, EmbeddingResponse
from .handlers import EmbeddingHandler


# Initialize MCP server
mcp = FastMCP("Embedding Service")

# Initialize handlers
embedding_handler = EmbeddingHandler()


@mcp.tool()
async def create_embeddings(
    text: Union[str, List[str]],
    method: str = "sentence_transformers",
    model_name: str = None,
    batch_size: int = 32,
    normalize: bool = True
) -> Dict[str, Any]:
    """
    Create embeddings for text(s) using specified method and model.
    
    Args:
        text: Text or list of texts to embed
        method: Embedding method (openai, sentence_transformers, huggingface, langchain, llamaindex)
        model_name: Model name for embedding
        batch_size: Batch size for processing
        normalize: Whether to normalize embeddings
    
    Returns:
        Dictionary with embeddings, dimensions, and metadata
    """
    try:
        request = EmbeddingRequest(
            text=text,
            method=method,
            model_name=model_name,
            batch_size=batch_size,
            normalize=normalize
        )
        
        response = await embedding_handler.create_embeddings(request)
        
        return {
            "embeddings": response.embeddings,
            "dimensions": response.dimensions,
            "model_name": response.model_name,
            "metadata": response.metadata
        }
    except Exception as e:
        logger.error(f"Error in create_embeddings tool: {e}")
        raise


@mcp.tool()
async def compute_similarity(
    embedding1: List[float],
    embedding2: List[float]
) -> Dict[str, Any]:
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        Dictionary with similarity score
    """
    try:
        similarity = await embedding_handler.compute_similarity(embedding1, embedding2)
        
        return {
            "similarity": similarity,
            "embedding1_dim": len(embedding1),
            "embedding2_dim": len(embedding2)
        }
    except Exception as e:
        logger.error(f"Error in compute_similarity tool: {e}")
        raise


@mcp.tool()
async def find_most_similar(
    query_embedding: List[float],
    candidate_embeddings: List[List[float]],
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Find most similar embeddings to query embedding.
    
    Args:
        query_embedding: Query embedding vector
        candidate_embeddings: List of candidate embedding vectors
        top_k: Number of top similar embeddings to return
    
    Returns:
        Dictionary with most similar embeddings and their indices
    """
    try:
        results = await embedding_handler.find_most_similar(
            query_embedding, candidate_embeddings, top_k
        )
        
        return {
            "results": results,
            "query_dim": len(query_embedding),
            "candidate_count": len(candidate_embeddings),
            "top_k": top_k
        }
    except Exception as e:
        logger.error(f"Error in find_most_similar tool: {e}")
        raise


@mcp.tool()
async def embed_and_compare(
    query_text: str,
    candidate_texts: List[str],
    method: str = "sentence_transformers",
    model_name: str = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Embed texts and find most similar to query.
    
    Args:
        query_text: Query text
        candidate_texts: List of candidate texts
        method: Embedding method
        model_name: Model name for embedding
        top_k: Number of top similar texts to return
    
    Returns:
        Dictionary with similar texts and their similarities
    """
    try:
        # Create embeddings for all texts
        all_texts = [query_text] + candidate_texts
        request = EmbeddingRequest(
            text=all_texts,
            method=method,
            model_name=model_name
        )
        
        response = await embedding_handler.create_embeddings(request)
        
        # Separate query and candidate embeddings
        query_embedding = response.embeddings[0]
        candidate_embeddings = response.embeddings[1:]
        
        # Find most similar
        results = await embedding_handler.find_most_similar(
            query_embedding, candidate_embeddings, top_k
        )
        
        # Add text content to results
        enriched_results = []
        for result in results:
            enriched_results.append({
                "index": result["index"],
                "text": candidate_texts[result["index"]],
                "similarity": result["similarity"]
            })
        
        return {
            "query_text": query_text,
            "results": enriched_results,
            "model_name": response.model_name,
            "dimensions": response.dimensions
        }
    except Exception as e:
        logger.error(f"Error in embed_and_compare tool: {e}")
        raise


@mcp.resource()
async def get_supported_models() -> str:
    """Get list of supported embedding models."""
    models = {
        "sentence_transformers": [
            "all-MiniLM-L6-v2",
            "all-mpnet-base-v2",
            "paraphrase-multilingual-MiniLM-L12-v2"
        ],
        "openai": ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
        "huggingface": ["sentence-transformers/all-MiniLM-L6-v2", "bert-base-uncased"]
    }
    return f"Supported models: {models}"


@mcp.resource()
async def get_service_info() -> str:
    """Get service information and configuration."""
    return f"""
Embedding Service Information:
- Service Name: {settings.service_name}
- Version: {settings.service_version}
- Default Method: {settings.default_embedding_method}
- Default Model: {settings.default_embedding_model}
- Max Batch Size: {settings.max_batch_size}
- Max Text Length: {settings.max_text_length}
"""


async def main():
    """Run the MCP server"""
    logger.add(
        "logs/embedding_service.log",
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
