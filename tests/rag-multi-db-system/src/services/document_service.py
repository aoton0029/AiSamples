from typing import List, Dict, Any, Optional
from src.core.mongo_client import MongoClient
from src.core.milvus_client import MilvusClient
from src.core.neo4j_client import Neo4jClient
from src.processors.embedding_generator import generate_embeddings
from src.processors.document_preprocessor import preprocess_document

class DocumentService:
    """Service for managing documents across multiple databases."""
    
    def __init__(self, mongo_client: MongoClient, milvus_client: MilvusClient, neo4j_client: Neo4jClient):
        self.mongo_client = mongo_client
        self.milvus_client = milvus_client
        self.neo4j_client = neo4j_client

    def save_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> str:
        """Preprocess, embed, and save the document."""
        # Preprocess the document
        processed_content = preprocess_document(content)
        
        # Generate embeddings
        embeddings = generate_embeddings(processed_content)
        
        # Save document to MongoDB
        document_id = self.mongo_client.save_document(document_id, processed_content, metadata)
        
        # Store embeddings in Milvus
        self.milvus_client.insert_vectors(document_id, [processed_content], [embeddings])
        
        # Register document in Neo4j
        self.neo4j_client.create_document_node(document_id, metadata.get("title", ""), metadata)
        
        return document_id

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document from MongoDB."""
        return self.mongo_client.get_document(document_id)

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from all databases."""
        # Delete from MongoDB
        deleted_from_mongo = self.mongo_client.delete_document(document_id)
        
        # Delete from Milvus
        self.milvus_client.delete_document_vectors(document_id)
        
        # Delete from Neo4j
        deleted_from_neo4j = self.neo4j_client.delete_document_graph(document_id)
        
        return deleted_from_mongo and deleted_from_neo4j

    def search_documents(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for documents based on metadata."""
        return self.mongo_client.search_by_metadata(query)