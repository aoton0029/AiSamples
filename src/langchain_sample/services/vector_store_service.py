import logging
from typing import List, Dict, Any, Optional
import uuid
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
        
    async def initialize(self):
        """Initialize vector store (handled by DatabaseService)"""
        logger.info("Vector store service initialized with Milvus")
    
    async def add_documents(self, processed_chunks: List[Dict[str, Any]]) -> List[str]:
        """Add processed document chunks to Milvus vector store"""
        try:
            vectors_data = []
            
            for chunk in processed_chunks:
                vector_id = str(uuid.uuid4())
                
                vector_data = {
                    "id": vector_id,
                    "doc_id": chunk["doc_id"],
                    "chunk_id": chunk["chunk_id"],
                    "embedding": chunk["embedding"],
                    "text": chunk["text"][:65535]  # Milvus VARCHAR limit
                }
                vectors_data.append(vector_data)
            
            # Insert into Milvus
            result_ids = await self.db.milvus_insert_vectors(vectors_data)
            
            logger.info(f"Added {len(vectors_data)} chunks to Milvus vector store")
            return result_ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    async def search(self, query_embedding: List[float], top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search vector store with embedding"""
        try:
            # Build Milvus expression for filtering
            expr = None
            if filters and "doc_id" in filters:
                if "$in" in filters["doc_id"]:
                    doc_ids = filters["doc_id"]["$in"]
                    expr = f"doc_id in {doc_ids}"
                else:
                    expr = f"doc_id == '{filters['doc_id']}'"
            
            # Search in Milvus
            results = await self.db.milvus_search_vectors(
                query_vector=query_embedding,
                top_k=top_k,
                expr=expr
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            raise
    
    async def query_with_llm(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Query using vector search (LLM integration handled separately)"""
        try:
            # This method would need the text processor to generate embeddings
            # For now, return placeholder structure
            return {
                "answer": "LLM integration pending - use search method with external LLM",
                "sources": [],
                "query": query
            }
            
        except Exception as e:
            logger.error(f"LLM query error: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector store statistics from Milvus"""
        try:
            # Use Redis to cache stats if available
            stats_key = "milvus:collection_stats"
            cached_stats = await self.db.redis_get(stats_key)
            
            if cached_stats:
                return cached_stats
            
            # Get fresh stats (would require direct Milvus API calls)
            stats = {
                "total_documents": "N/A",  # Would need utility.get_entity_num()
                "collection_name": "document_embeddings",
                "database_type": "Milvus"
            }
            
            # Cache for 5 minutes
            await self.db.redis_set(stats_key, stats, expire=300)
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise
    
    async def delete_documents(self, doc_ids: List[str]) -> int:
        """Delete documents by doc_id from Milvus"""
        try:
            # Build expression for deletion
            expr = f"doc_id in {doc_ids}"
            
            # Delete from Milvus
            await self.db.milvus_delete_vectors(expr)
            
            logger.info(f"Deleted chunks for doc_ids: {doc_ids}")
            return len(doc_ids)  # Approximate count
                
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
            )
            
            # Execute query
            response = query_engine.query(query)
            
            # Extract source information
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        "node_id": node.id_,
                        "text": node.text,
                        "metadata": node.metadata,
                        "score": getattr(node, 'score', 0.0)
                    })
            
            return {
                "answer": str(response),
                "sources": sources,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"LLM query error: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            count = self.collection.count()
            
            # Get sample of documents for analysis
            if count > 0:
                sample = self.collection.peek(limit=min(10, count))
                sample_metadata = sample["metadatas"] if sample["metadatas"] else []
            else:
                sample_metadata = []
            
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "sample_metadata": sample_metadata[:5],  # First 5 samples
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise
    
    async def delete_documents(self, doc_ids: List[str]) -> int:
        """Delete documents by doc_id"""
        try:
            # Query for documents with matching doc_ids
            results = self.collection.get(
                where={"doc_id": {"$in": doc_ids}},
                include=["metadatas"]
            )
            
            if results["ids"]:
                # Delete by IDs
                self.collection.delete(ids=results["ids"])
                deleted_count = len(results["ids"])
                logger.info(f"Deleted {deleted_count} chunks for doc_ids: {doc_ids}")
                return deleted_count
            else:
                logger.warning(f"No documents found for doc_ids: {doc_ids}")
                return 0
                
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
