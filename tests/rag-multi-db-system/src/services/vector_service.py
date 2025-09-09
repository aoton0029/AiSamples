from src.core.milvus_client import MilvusClient
from src.core.mongo_client import MongoClient
from src.core.neo4j_client import Neo4jClient
from src.processors.embedding_generator import generate_embeddings
from src.processors.document_preprocessor import preprocess_document
from typing import List, Dict, Any

class VectorService:
    """Service for managing vector storage and operations."""

    def __init__(self, milvus_client: MilvusClient, mongo_client: MongoClient, neo4j_client: Neo4jClient):
        self.milvus_client = milvus_client
        self.mongo_client = mongo_client
        self.neo4j_client = neo4j_client

    def process_and_store_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Preprocess document, generate embeddings, and store in databases."""
        # Preprocess the document
        chunks = preprocess_document(content)

        # Generate embeddings for the document chunks
        embeddings = generate_embeddings(chunks)

        # Store the document in MongoDB
        self.mongo_client.save_document(document_id, content, metadata)

        # Store the embeddings in Milvus
        self.milvus_client.insert_vectors(document_id, chunks, embeddings)

        # Register the document in Neo4j
        for chunk in chunks:
            self.neo4j_client.create_document_node(document_id, chunk, metadata)

    def search_vectors(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors in the vector database."""
        return self.milvus_client.search_similar(query_embedding, top_k)

    def delete_document_vectors(self, document_id: str) -> None:
        """Delete vectors associated with a document."""
        self.milvus_client.delete_document_vectors(document_id)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics of the vector collection."""
        return self.milvus_client.get_collection_stats()