from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
import asyncio
from datetime import datetime
import json

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LlamaIndex FastAPI Server",
    description="AI-powered document processing and query API using LlamaIndex and Ollama",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DATA_PATH = os.getenv("DATA_PATH", "/app/data")
CACHE_PATH = os.getenv("CACHE_PATH", "/app/cache")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="The query to process")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens for response")
    temperature: Optional[float] = Field(0.7, description="Temperature for response generation")

class QueryResponse(BaseModel):
    response: str
    sources: List[str]
    timestamp: datetime

class DocumentInfo(BaseModel):
    filename: str
    size: int
    upload_time: datetime
    processed: bool

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    ollama_available: bool
    index_loaded: bool

# Global variables
llm = None
embed_model = None
index = None
chroma_client = None

async def initialize_components():
    """Initialize LlamaIndex components"""
    global llm, embed_model, index, chroma_client
    
    try:
        # Initialize Ollama LLM
        llm = Ollama(
            model="llama2",
            base_url=OLLAMA_BASE_URL,
            request_timeout=30.0
        )
        logger.info("Ollama LLM initialized")
        
        # Initialize embedding model
        embed_model = HuggingFaceEmbedding(
            model_name=EMBEDDING_MODEL,
            cache_folder=CACHE_PATH
        )
        logger.info("Embedding model initialized")
        
        # Initialize ChromaDB
        chroma_client = chromadb.PersistentClient(path=f"{CACHE_PATH}/chroma")
        collection = chroma_client.get_or_create_collection("documents")
        vector_store = ChromaVectorStore(chroma_collection=collection)
        
        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Load existing index or create new one
        if os.path.exists(f"{DATA_PATH}/documents"):
            documents = SimpleDirectoryReader(f"{DATA_PATH}/documents").load_data()
            if documents:
                index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    embed_model=embed_model
                )
                logger.info(f"Index created with {len(documents)} documents")
            else:
                index = VectorStoreIndex([], storage_context=storage_context, embed_model=embed_model)
                logger.info("Empty index created")
        else:
            os.makedirs(f"{DATA_PATH}/documents", exist_ok=True)
            index = VectorStoreIndex([], storage_context=storage_context, embed_model=embed_model)
            logger.info("New empty index created")
            
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    await initialize_components()
    logger.info("Application startup completed")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    ollama_available = False
    try:
        if llm:
            # Test Ollama connection
            await llm.acomplete("test")
            ollama_available = True
    except:
        pass
    
    return HealthResponse(
        status="healthy" if ollama_available and index is not None else "degraded",
        timestamp=datetime.now(),
        ollama_available=ollama_available,
        index_loaded=index is not None
    )

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if llm is None or embed_model is None or index is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents using LlamaIndex"""
    if index is None:
        raise HTTPException(status_code=503, detail="Index not initialized")
    
    try:
        # Create query engine
        query_engine = index.as_query_engine(
            llm=llm,
            similarity_top_k=5,
            response_mode="tree_summarize"
        )
        
        # Execute query
        response = await query_engine.aquery(request.query)
        
        # Extract sources
        sources = []
        if hasattr(response, 'source_nodes'):
            sources = [node.node.metadata.get('file_name', 'Unknown') 
                      for node in response.source_nodes]
        
        return QueryResponse(
            response=str(response),
            sources=sources,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a document"""
    if not file.filename.endswith(('.txt', '.pdf', '.docx', '.md')):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    try:
        # Save uploaded file
        file_path = f"{DATA_PATH}/documents/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Add background task to process the document
        background_tasks.add_task(process_document, file_path)
        
        return {
            "message": f"File {file.filename} uploaded successfully",
            "filename": file.filename,
            "size": len(content),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

async def process_document(file_path: str):
    """Background task to process uploaded document"""
    global index
    
    try:
        logger.info(f"Processing document: {file_path}")
        
        # Load and parse the document
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
        
        if documents and index is not None:
            # Add documents to existing index
            for doc in documents:
                index.insert(doc)
            
            logger.info(f"Document processed successfully: {os.path.basename(file_path)}")
        
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {str(e)}")

@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents"""
    documents = []
    docs_path = f"{DATA_PATH}/documents"
    
    if os.path.exists(docs_path):
        for filename in os.listdir(docs_path):
            file_path = os.path.join(docs_path, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                documents.append(DocumentInfo(
                    filename=filename,
                    size=stat.st_size,
                    upload_time=datetime.fromtimestamp(stat.st_ctime),
                    processed=True  # Assuming all files in the directory are processed
                ))
    
    return documents

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document"""
    file_path = f"{DATA_PATH}/documents/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        os.remove(file_path)
        logger.info(f"Document deleted: {filename}")
        return {"message": f"Document {filename} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    docs_path = f"{DATA_PATH}/documents"
    doc_count = 0
    total_size = 0
    
    if os.path.exists(docs_path):
        for filename in os.listdir(docs_path):
            file_path = os.path.join(docs_path, filename)
            if os.path.isfile(file_path):
                doc_count += 1
                total_size += os.path.getsize(file_path)
    
    return {
        "document_count": doc_count,
        "total_size_bytes": total_size,
        "index_initialized": index is not None,
        "ollama_url": OLLAMA_BASE_URL,
        "data_path": DATA_PATH,
        "cache_path": CACHE_PATH
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
