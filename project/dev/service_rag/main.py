import asyncio
from typing import Any, Dict, List, Union, Optional
from fastmcp import FastMCP
from loguru import logger

from .config import settings
from .handlers import RAGHandler


# Initialize MCP server
mcp = FastMCP("RAG Service")

# Initialize handlers
rag_handler = RAGHandler()


@mcp.tool()
async def search_similar(
    query: str,
    database_type: str = "vector",
    collection_name: str = "documents",
    top_k: int = 5,
    similarity_threshold: float = 0.7,
    filters: Dict[str, Any] = None,
    hybrid_search: bool = False
) -> Dict[str, Any]:
    """
    Search for similar documents across different database types.
    
    Args:
        query: Search query text
        database_type: Type of database (vector, document, graph, keyvalue)
        collection_name: Collection/table name to search
        top_k: Number of top results to return
        similarity_threshold: Minimum similarity score
        filters: Additional filters for search
        hybrid_search: Whether to use hybrid search across multiple DBs
    
    Returns:
        Dictionary with search results and metadata
    """
    try:
        results = await rag_handler.search_similar(
            query=query,
            database_type=database_type,
            collection_name=collection_name,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            filters=filters or {},
            hybrid_search=hybrid_search
        )
        
        return {
            "query": query,
            "results": results,
            "database_type": database_type,
            "total_results": len(results),
            "search_metadata": {
                "top_k": top_k,
                "threshold": similarity_threshold,
                "hybrid": hybrid_search
            }
        }
    except Exception as e:
        logger.error(f"Error in search_similar tool: {e}")
        raise


@mcp.tool()
async def retrieve_and_generate(
    query: str,
    context_databases: List[str] = ["vector"],
    max_context_length: int = 4000,
    generation_model: str = "gpt-3.5-turbo",
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Retrieve relevant context and generate response using RAG.
    
    Args:
        query: User query
        context_databases: List of database types to search for context
        max_context_length: Maximum context length in tokens
        generation_model: Model to use for generation
        include_sources: Whether to include source documents
    
    Returns:
        Dictionary with generated response and sources
    """
    try:
        response = await rag_handler.retrieve_and_generate(
            query=query,
            context_databases=context_databases,
            max_context_length=max_context_length,
            generation_model=generation_model,
            include_sources=include_sources
        )
        
        return response
    except Exception as e:
        logger.error(f"Error in retrieve_and_generate tool: {e}")
        raise


@mcp.tool()
async def add_documents(
    documents: List[Dict[str, Any]],
    database_type: str = "vector",
    collection_name: str = "documents",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_documents: bool = True,
    chunk_size: int = 1000
) -> Dict[str, Any]:
    """
    Add documents to the RAG system.
    
    Args:
        documents: List of documents to add
        database_type: Target database type
        collection_name: Collection name
        embedding_model: Model to use for embeddings
        chunk_documents: Whether to chunk documents
        chunk_size: Size of chunks
    
    Returns:
        Dictionary with operation results
    """
    try:
        result = await rag_handler.add_documents(
            documents=documents,
            database_type=database_type,
            collection_name=collection_name,
            embedding_model=embedding_model,
            chunk_documents=chunk_documents,
            chunk_size=chunk_size
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in add_documents tool: {e}")
        raise


@mcp.resource()
async def get_supported_databases() -> str:
    """Get list of supported database types."""
    databases = {
        "vector": "Vector databases (Milvus, Pinecone, ChromaDB, etc.)",
        "document": "Document databases (MongoDB, etc.)",
        "graph": "Graph databases (Neo4j, etc.)",
        "keyvalue": "Key-value databases (Redis, etc.)",
        "relational": "Relational databases (PostgreSQL, etc.)"
    }
    return f"Supported databases: {databases}"


async def main():
    """Run the MCP server"""
    logger.add(
        "logs/rag_service.log",
        rotation="1 day",
        retention="30 days",
        format=settings.log_format,
        level=settings.log_level
    )
    
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    try:
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
