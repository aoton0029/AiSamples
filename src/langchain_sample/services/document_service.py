import os
import uuid
import logging
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
import aiofiles
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.llms.ollama import Ollama
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from .text_processing_service import TextProcessingService
from .vector_store_service import VectorStoreService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.documents_dir = "uploaded_documents"
        self.index = None
        self.documents = {}  # Store document metadata
        self.text_processor = TextProcessingService()
        self.vector_store = VectorStoreService()
        self.db = None
        
    async def initialize(self):
        """Initialize the document service"""
        try:
            # Create documents directory
            os.makedirs(self.documents_dir, exist_ok=True)
            
            # Initialize database service
            self.db = DatabaseService()
            await self.db.initialize()
            
            # Initialize text processor and vector store with database service
            await self.text_processor.initialize()
            self.vector_store = VectorStoreService(self.db)
            await self.vector_store.initialize()
            
            logger.info("Document service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize document service: {e}")
            raise
    
    async def upload_document(self, file: UploadFile) -> str:
        """Upload and process a document with full text processing pipeline"""
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Save file
            file_path = os.path.join(self.documents_dir, f"{doc_id}_{file.filename}")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Read and process document
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                text_content = await f.read()
            
            # Process document with text processing service
            processed_data = await self.text_processor.process_document(text_content, doc_id)
            
            # Add to vector store (Milvus)
            node_ids = await self.vector_store.add_documents(processed_data["chunks"])
            
            # Store document metadata in MongoDB
            document_metadata = {
                "doc_id": doc_id,
                "filename": file.filename,
                "file_path": file_path,
                "processing_summary": processed_data["processing_summary"],
                "node_ids": node_ids,
                "total_chunks": processed_data["total_chunks"],
                "upload_timestamp": datetime.utcnow().isoformat()
            }
            
            mongo_id = await self.db.mongo_insert_document("documents", document_metadata)
            
            # Cache document info in Redis
            cache_key = f"doc:{doc_id}"
            await self.db.redis_set(cache_key, document_metadata, expire=3600)  # 1 hour cache
            
            logger.info(f"Document processed: {file.filename} (ID: {doc_id}, Chunks: {processed_data['total_chunks']})")
            return doc_id
            
        except Exception as e:
            logger.error(f"Document upload error: {e}")
            raise
    
    async def query(self, query: str, document_ids: Optional[List[str]] = None, top_k: int = 5) -> Dict[str, Any]:
        """Enhanced query with vector similarity search"""
        try:
            # Generate query embedding
            query_embedding_result = await self.text_processor.generate_embeddings([query])
            query_embedding = query_embedding_result["embeddings"][0]
            
            # Prepare filters if document_ids specified
            filters = None
            if document_ids:
                filters = {"doc_id": {"$in": document_ids}}
            
            # Search in vector store (Milvus)
            search_results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters
            )
            
            # Use LLM to generate answer based on search results
            context = "\n\n".join([result["text"] for result in search_results])
            llm_response = await self.llm_service.chat(
                message=query,
                context=f"Based on the following information:\n{context}"
            )
            
            return {
                "answer": llm_response,
                "sources": search_results,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Document query error: {e}")
            raise
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all uploaded documents from MongoDB"""
        try:
            documents = await self.db.mongo_find_documents("documents", {})
            return documents
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID"""
        try:
            # Try Redis cache first
            cache_key = f"doc:{doc_id}"
            cached_doc = await self.db.redis_get(cache_key)
            if cached_doc:
                return cached_doc
            
            # Fallback to MongoDB
            documents = await self.db.mongo_find_documents("documents", {"doc_id": doc_id})
            if documents:
                doc = documents[0]
                # Update cache
                await self.db.redis_set(cache_key, doc, expire=3600)
                return doc
            
            return None
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            raise
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document and all related data"""
        try:
            # Delete from vector store (Milvus)
            await self.vector_store.delete_documents([doc_id])
            
            # Delete from MongoDB
            deleted_count = await self.db.mongo_delete_documents("documents", {"doc_id": doc_id})
            
            # Delete from Redis cache
            cache_key = f"doc:{doc_id}"
            await self.db.redis_delete(cache_key)
            
            # Delete physical file if exists
            documents = await self.db.mongo_find_documents("documents", {"doc_id": doc_id})
            if documents:
                file_path = documents[0].get("file_path")
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            
            logger.info(f"Deleted document: {doc_id}")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise
    
    async def analyze_document(self, doc_id: str) -> Dict[str, Any]:
        """Get detailed analysis of a document"""
        try:
            doc_metadata = await self.get_document(doc_id)
            if not doc_metadata:
                raise ValueError(f"Document {doc_id} not found")
            
            # Get vector store stats
            vector_stats = await self.vector_store.get_collection_stats()
            
            return {
                "doc_id": doc_id,
                "metadata": doc_metadata,
                "vector_store_info": vector_stats
            }
            
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            raise
