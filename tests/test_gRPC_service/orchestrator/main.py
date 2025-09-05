import asyncio
import grpc
from typing import List, Dict, Any, Optional
import json
import logging
from fastmcp import FastMCP, Context
from pydantic import BaseModel
import sys
import os

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for MCP tools
class DocumentInput(BaseModel):
    id: str
    content: str
    content_type: str = "text/plain"
    metadata: Dict[str, str] = {}

class ChunkConfig(BaseModel):
    strategy: str = "recursive"
    chunk_size: int = 1000
    chunk_overlap: int = 200

class EmbeddingConfig(BaseModel):
    model: str = "all-MiniLM-L6-v2"
    provider: str = "sentence_transformers"

class SearchConfig(BaseModel):
    top_k: int = 10
    index_types: List[str] = ["vector", "document"]
    min_score: float = 0.0

class RAGWorkflowConfig(BaseModel):
    chunking: ChunkConfig = ChunkConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    search: SearchConfig = SearchConfig()
    context_template: str = "rag"
    inference_model: str = "llama2"
    inference_provider: str = "ollama"

class MCPOrchestrator:
    def __init__(self):
        self.app = FastMCP("MCPOrchestrator")
        self.service_channels = {}
        self.setup_service_connections()
        self.register_tools()
    
    def setup_service_connections(self):
        """Setup gRPC connections to all microservices"""
        services = {
            'chunking': 'localhost:50051',
            'tokenize': 'localhost:50052', 
            'embedding': 'localhost:50053',
            'indexing': 'localhost:50054',
            'rag': 'localhost:50055',
            'context_builder': 'localhost:50056',
            'inference': 'localhost:50057',
            'tuning': 'localhost:50058'
        }
        
        for service_name, address in services.items():
            try:
                channel = grpc.aio.insecure_channel(address)
                self.service_channels[service_name] = channel
                logger.info(f"Connected to {service_name} service at {address}")
            except Exception as e:
                logger.error(f"Failed to connect to {service_name}: {e}")
    
    def register_tools(self):
        """Register MCP tools"""
        
        @self.app.tool()
        async def chunk_document(
            ctx: Context,
            document: DocumentInput,
            config: ChunkConfig = ChunkConfig()
        ) -> Dict[str, Any]:
            """Chunk a document into smaller pieces"""
            try:
                if 'chunking' not in self.service_channels:
                    return {"error": "Chunking service not available"}
                
                channel = self.service_channels['chunking']
                stub = mcp_service_pb2_grpc.ChunkingServiceStub(channel)
                
                # Prepare request
                doc_pb = mcp_service_pb2.Document(
                    id=document.id,
                    content=document.content,
                    content_type=document.content_type,
                    metadata=document.metadata
                )
                
                request = mcp_service_pb2.ChunkRequest(
                    document=doc_pb,
                    chunk_config={
                        'strategy': config.strategy,
                        'chunk_size': str(config.chunk_size),
                        'chunk_overlap': str(config.chunk_overlap)
                    }
                )
                
                # Call service
                response = await stub.ChunkDocument(request)
                
                if response.success:
                    chunks = []
                    for chunk in response.chunks:
                        chunks.append({
                            'id': chunk.id,
                            'content': chunk.content,
                            'metadata': dict(chunk.metadata)
                        })
                    return {"chunks": chunks, "count": len(chunks)}
                else:
                    return {"error": response.message}
                
            except Exception as e:
                logger.error(f"Error in chunk_document: {e}")
                return {"error": str(e)}
        
        @self.app.tool()
        async def generate_embeddings(
            ctx: Context,
            texts: List[str],
            config: EmbeddingConfig = EmbeddingConfig()
        ) -> Dict[str, Any]:
            """Generate embeddings for a list of texts"""
            try:
                if 'embedding' not in self.service_channels:
                    return {"error": "Embedding service not available"}
                
                channel = self.service_channels['embedding']
                stub = mcp_service_pb2_grpc.EmbeddingServiceStub(channel)
                
                request = mcp_service_pb2.EmbeddingRequest(
                    texts=texts,
                    model=config.model,
                    embedding_config={
                        'provider': config.provider
                    }
                )
                
                response = await stub.GenerateEmbeddings(request)
                
                if response.success:
                    embeddings = []
                    for emb in response.embeddings:
                        embeddings.append({
                            'values': list(emb.values),
                            'model': emb.model,
                            'dimension': emb.dimension
                        })
                    return {"embeddings": embeddings, "count": len(embeddings)}
                else:
                    return {"error": response.message}
                
            except Exception as e:
                logger.error(f"Error in generate_embeddings: {e}")
                return {"error": str(e)}
        
        @self.app.tool()
        async def search_documents(
            ctx: Context,
            query: str,
            config: SearchConfig = SearchConfig()
        ) -> Dict[str, Any]:
            """Search documents using RAG"""
            try:
                if 'rag' not in self.service_channels:
                    return {"error": "RAG service not available"}
                
                channel = self.service_channels['rag']
                stub = mcp_service_pb2_grpc.RAGServiceStub(channel)
                
                request = mcp_service_pb2.RAGSearchRequest(
                    query=query,
                    top_k=config.top_k,
                    index_types=config.index_types,
                    search_config={
                        'min_score': str(config.min_score)
                    }
                )
                
                response = await stub.SearchDocuments(request)
                
                if response.success:
                    results = []
                    for result in response.results:
                        results.append({
                            'id': result.id,
                            'score': result.score,
                            'content': result.document.content,
                            'metadata': dict(result.document.metadata)
                        })
                    return {"results": results, "count": len(results)}
                else:
                    return {"error": response.message}
                
            except Exception as e:
                logger.error(f"Error in search_documents: {e}")
                return {"error": str(e)}
        
        @self.app.tool()
        async def rag_workflow(
            ctx: Context,
            documents: List[DocumentInput],
            query: str,
            config: RAGWorkflowConfig = RAGWorkflowConfig()
        ) -> Dict[str, Any]:
            """Complete RAG workflow: chunk, embed, index, search, and generate response"""
            try:
                logger.info(f"Starting RAG workflow with {len(documents)} documents")
                
                # Step 1: Chunk documents
                all_chunks = []
                for doc in documents:
                    chunk_result = await chunk_document(ctx, doc, config.chunking)
                    if 'error' in chunk_result:
                        return {"error": f"Chunking failed: {chunk_result['error']}"}
                    all_chunks.extend(chunk_result['chunks'])
                
                logger.info(f"Created {len(all_chunks)} chunks")
                
                # Step 2: Generate embeddings
                chunk_texts = [chunk['content'] for chunk in all_chunks]
                embedding_result = await generate_embeddings(ctx, chunk_texts, config.embedding)
                if 'error' in embedding_result:
                    return {"error": f"Embedding failed: {embedding_result['error']}"}
                
                # Step 3: Index documents (placeholder - would call indexing service)
                # For now, assume documents are already indexed
                
                # Step 4: Search
                search_result = await search_documents(ctx, query, config.search)
                if 'error' in search_result:
                    return {"error": f"Search failed: {search_result['error']}"}
                
                # Step 5: Build context and generate response
                if 'context_builder' in self.service_channels and 'inference' in self.service_channels:
                    # Build context
                    context_channel = self.service_channels['context_builder']
                    context_stub = mcp_service_pb2_grpc.ContextBuilderServiceStub(context_channel)
                    
                    # Convert search results to protobuf format
                    search_results_pb = []
                    for result in search_result['results']:
                        doc_pb = mcp_service_pb2.Document(
                            id=result['id'],
                            content=result['content'],
                            metadata=result['metadata']
                        )
                        result_pb = mcp_service_pb2.SearchResult(
                            id=result['id'],
                            score=result['score'],
                            document=doc_pb
                        )
                        search_results_pb.append(result_pb)
                    
                    context_request = mcp_service_pb2.ContextBuildRequest(
                        query=query,
                        search_results=search_results_pb,
                        context_config={'template': config.context_template}
                    )
                    
                    context_response = await context_stub.BuildContext(context_request)
                    if not context_response.success:
                        return {"error": f"Context building failed: {context_response.message}"}
                    
                    # Generate inference
                    inference_channel = self.service_channels['inference']
                    inference_stub = mcp_service_pb2_grpc.InferenceServiceStub(inference_channel)
                    
                    inference_request = mcp_service_pb2.InferenceRequest(
                        prompt=context_response.prompt,
                        model=config.inference_model,
                        inference_config={'provider': config.inference_provider}
                    )
                    
                    inference_response = await inference_stub.GenerateResponse(inference_request)
                    if not inference_response.success:
                        return {"error": f"Inference failed: {inference_response.message}"}
                    
                    return {
                        "query": query,
                        "chunks_created": len(all_chunks),
                        "search_results": search_result['results'],
                        "context": context_response.context,
                        "response": inference_response.response,
                        "workflow_success": True
                    }
                
                else:
                    # Return search results if context/inference services not available
                    return {
                        "query": query,
                        "chunks_created": len(all_chunks),
                        "search_results": search_result['results'],
                        "workflow_success": True,
                        "note": "Context building and inference services not available"
                    }
                
            except Exception as e:
                logger.error(f"Error in RAG workflow: {e}")
                return {"error": str(e)}
        
        @self.app.tool()
        async def health_check_all_services(ctx: Context) -> Dict[str, Any]:
            """Check health of all microservices"""
            health_status = {}
            
            service_stubs = {
                'chunking': mcp_service_pb2_grpc.ChunkingServiceStub,
                'tokenize': mcp_service_pb2_grpc.TokenizationServiceStub,
                'embedding': mcp_service_pb2_grpc.EmbeddingServiceStub,
                'indexing': mcp_service_pb2_grpc.IndexingServiceStub,
                'rag': mcp_service_pb2_grpc.RAGServiceStub,
                'context_builder': mcp_service_pb2_grpc.ContextBuilderServiceStub,
                'inference': mcp_service_pb2_grpc.InferenceServiceStub,
                'tuning': mcp_service_pb2_grpc.TuningServiceStub
            }
            
            for service_name, stub_class in service_stubs.items():
                try:
                    if service_name in self.service_channels:
                        channel = self.service_channels[service_name]
                        stub = stub_class(channel)
                        request = mcp_service_pb2.HealthCheckRequest()
                        response = await stub.HealthCheck(request)
                        health_status[service_name] = {
                            "healthy": response.healthy,
                            "message": response.message
                        }
                    else:
                        health_status[service_name] = {
                            "healthy": False,
                            "message": "Service channel not available"
                        }
                except Exception as e:
                    health_status[service_name] = {
                        "healthy": False,
                        "message": f"Error: {str(e)}"
                    }
            
            return {"services": health_status}

async def main():
    """Main function to run the MCP orchestrator"""
    orchestrator = MCPOrchestrator()
    
    # Run the FastMCP server
    import uvicorn
    from fastapi import FastAPI
    
    # Create FastAPI app from FastMCP
    app = orchestrator.app.create_app()
    
    logger.info("Starting MCP Orchestrator on port 3000")
    await uvicorn.run(app, host="0.0.0.0", port=3000)

if __name__ == "__main__":
    asyncio.run(main())
