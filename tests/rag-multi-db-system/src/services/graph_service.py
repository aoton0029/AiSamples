from src.core.neo4j_client import Neo4jClient
from src.core.mongo_client import MongoClient
from src.core.milvus_client import MilvusClient
from src.processors.embedding_generator import generate_embeddings
from src.processors.entity_extractor import extract_entities

class GraphService:
    """Service for managing graph data and relationships."""

    def __init__(self, neo4j_client: Neo4jClient, mongo_client: MongoClient, milvus_client: MilvusClient):
        self.neo4j_client = neo4j_client
        self.mongo_client = mongo_client
        self.milvus_client = milvus_client

    def register_document(self, document_id: str, content: str, metadata: dict):
        """Register a document in the graph database."""
        # Save document in MongoDB
        self.mongo_client.save_document(document_id, content, metadata)

        # Generate embeddings for the document
        embeddings = generate_embeddings(content)

        # Store embeddings in Milvus
        self.milvus_client.insert_vectors(document_id, [content], [embeddings])

        # Extract entities from the document
        entities = extract_entities(content)

        # Create nodes and relationships in Neo4j
        for entity in entities:
            self.neo4j_client.create_entity_node(entity['id'], entity['type'], entity['properties'])
            self.neo4j_client.create_relationship(document_id, entity['id'], "CONTAINS")

    def find_related_documents(self, entity_id: str):
        """Find documents related to a specific entity."""
        return self.neo4j_client.find_related_documents(entity_id)

    def delete_document(self, document_id: str):
        """Delete a document and its associated data."""
        self.neo4j_client.delete_document_graph(document_id)
        self.milvus_client.delete_document_vectors(document_id)
        self.mongo_client.delete_document(document_id)