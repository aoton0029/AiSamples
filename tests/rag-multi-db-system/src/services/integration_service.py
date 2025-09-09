from core.mongo_client import MongoClient
from core.milvus_client import MilvusClient
from core.neo4j_client import Neo4jClient
from core.redis_client import RedisClient
from processors.embedding_generator import generate_embeddings
from processors.document_preprocessor import preprocess_document
from typing import List, Dict, Any

class IntegrationService:
    """Integration service for managing document, vector, and graph database interactions."""
    
    def __init__(self, mongo_client: MongoClient, milvus_client: MilvusClient, 
                 neo4j_client: Neo4jClient, redis_client: RedisClient):
        self.mongo_client = mongo_client
        self.milvus_client = milvus_client
        self.neo4j_client = neo4j_client
        self.redis_client = redis_client

    def process_and_store_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Preprocess the document, generate embeddings, and store in respective databases."""
        # Preprocess the document
        chunks = preprocess_document(content)
        
        # Generate embeddings for the document chunks
        embeddings = generate_embeddings(chunks)
        
        # Store the document in MongoDB
        self.mongo_client.save_document(document_id, content, metadata)
        
        # Store the embeddings in Milvus
        self.milvus_client.insert_vectors(document_id, chunks, embeddings)
        
        # Register the document in Neo4j
        self.neo4j_client.create_document_node(document_id, metadata.get("title", ""), metadata)
        
        # Optionally cache the document in Redis
        self.redis_client.set_cache(f"document:{document_id}", content)

    def search_document(self, query: str) -> List[Dict[str, Any]]:
        """Search for documents based on a query."""
        # Here you can implement a search logic that integrates with MongoDB and Milvus
        # For example, you could search in MongoDB and then use Milvus for vector similarity
        pass

    def delete_document(self, document_id: str) -> None:
        """Delete a document and its associated data from all databases."""
        self.mongo_client.delete_document(document_id)
        self.milvus_client.delete_document_vectors(document_id)
        self.neo4j_client.delete_document_graph(document_id)
        self.redis_client.delete_cache(f"document:{document_id}")