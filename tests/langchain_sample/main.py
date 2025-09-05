from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from services.llm_service import LLMService
from services.document_service import DocumentService
from models.schemas import (
    ChatRequest, ChatResponse, 
    DocumentUploadResponse, QueryRequest, QueryResponse,
    MCPRequest, MCPResponse,
    TokenizeRequest, TokenizeResponse, ChunkRequest, ChunkResponse,
    EmbeddingRequest, EmbeddingResponse, SimilaritySearchRequest, 
    SimilaritySearchResponse, DocumentAnalysisResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
llm_service = None
document_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global llm_service, document_service
    logger.info("Initializing services...")
    
    llm_service = LLMService(ollama_url="http://ollama:11434")
    document_service = DocumentService(llm_service)
    
    await llm_service.initialize()
    await document_service.initialize()
    
    logger.info("Services initialized successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    if document_service and document_service.db:
        await document_service.db.close_connections()

app = FastAPI(
    title="AI Server with MCP Support",
    description="Server for n8n integration using LangChain, LlamaIndex, and Ollama",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for n8n integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Server with MCP Support", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": "ready"}

# Chat endpoint for basic LLM interaction
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await llm_service.chat(request.message, request.context)
        return ChatResponse(
            response=response,
            model=llm_service.model_name,
            success=True
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document upload and indexing
@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        doc_id = await document_service.upload_document(file)
        return DocumentUploadResponse(
            document_id=doc_id,
            filename=file.filename,
            success=True,
            message="Document uploaded and indexed successfully"
        )
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Query documents with RAG
@app.post("/documents/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        response = await document_service.query(
            request.query, 
            request.document_ids,
            request.top_k
        )
        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"],
            success=True
        )
    except Exception as e:
        logger.error(f"Document query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Text processing endpoints
@app.post("/text/tokenize", response_model=TokenizeResponse)
async def tokenize_text(request: TokenizeRequest):
    try:
        result = await document_service.text_processor.tokenize(request.text, request.method)
        return TokenizeResponse(**result, success=True)
    except Exception as e:
        logger.error(f"Tokenization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text/chunk", response_model=ChunkResponse)
async def chunk_text(request: ChunkRequest):
    try:
        chunks = await document_service.text_processor.chunk_text(request.text, request.method)
        return ChunkResponse(
            chunks=chunks,
            total_chunks=len(chunks),
            method=request.method,
            success=True
        )
    except Exception as e:
        logger.error(f"Chunking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    try:
        result = await document_service.text_processor.generate_embeddings(request.texts)
        return EmbeddingResponse(**result, success=True)
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/search", response_model=SimilaritySearchResponse)
async def similarity_search(request: SimilaritySearchRequest):
    try:
        # Generate query embedding
        query_embedding_result = await document_service.text_processor.generate_embeddings([request.query])
        query_embedding = query_embedding_result["embeddings"][0]
        
        # Prepare filters
        filters = None
        if request.document_ids:
            filters = {"doc_id": {"$in": request.document_ids}}
        
        # Search vector store
        results = await document_service.vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filters=filters
        )
        
        return SimilaritySearchResponse(
            results=results,
            query=request.query,
            top_k=request.top_k,
            success=True
        )
    except Exception as e:
        logger.error(f"Similarity search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(doc_id: str):
    try:
        result = await document_service.analyze_document(doc_id)
        return DocumentAnalysisResponse(**result, success=True)
    except Exception as e:
        logger.error(f"Document analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# MCP (Model Context Protocol) endpoint for advanced n8n integration
@app.post("/mcp", response_model=MCPResponse)
async def mcp_handler(request: MCPRequest):
    try:
        if request.method == "chat":
            result = await llm_service.chat(request.params.get("message", ""))
        elif request.method == "query_documents":
            result = await document_service.query(
                request.params.get("query", ""),
                request.params.get("document_ids"),
                request.params.get("top_k", 5)
            )
        elif request.method == "list_documents":
            result = await document_service.list_documents()
        elif request.method == "tokenize":
            result = await document_service.text_processor.tokenize(
                request.params.get("text", ""),
                request.params.get("method", "tiktoken")
            )
        elif request.method == "chunk":
            result = await document_service.text_processor.chunk_text(
                request.params.get("text", ""),
                request.params.get("method", "sentence")
            )
        elif request.method == "generate_embeddings":
            result = await document_service.text_processor.generate_embeddings(
                request.params.get("texts", [])
            )
        elif request.method == "similarity_search":
            query_embedding_result = await document_service.text_processor.generate_embeddings([request.params.get("query", "")])
            query_embedding = query_embedding_result["embeddings"][0]
            result = await document_service.vector_store.search(
                query_embedding=query_embedding,
                top_k=request.params.get("top_k", 5),
                filters=request.params.get("filters")
            )
        else:
            raise ValueError(f"Unknown method: {request.method}")
        
        return MCPResponse(
            id=request.id,
            result=result,
            success=True
        )
    except Exception as e:
        logger.error(f"MCP error: {e}")
        return MCPResponse(
            id=request.id,
            error=str(e),
            success=False
        )

# Add new endpoint for document deletion
@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        success = await document_service.delete_document(doc_id)
        if success:
            return {"message": f"Document {doc_id} deleted successfully", "success": True}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    try:
        document = await document_service.get_document(doc_id)
        if document:
            return {"document": document, "success": True}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
