from neo4j_client import Neo4jClient
from mongo_client import MongoClient
from milvus_client import MilvusClient
from typing import List, Dict, Any

class GraphBuilder:
    """GraphBuilder class to create and manage graph structures from documents and their relationships."""
    
    def __init__(self, neo4j_client: Neo4jClient, mongo_client: MongoClient, milvus_client: MilvusClient):
        self.neo4j_client = neo4j_client
        self.mongo_client = mongo_client
        self.milvus_client = milvus_client

    def build_graph(self, document_id: str, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> bool:
        """Builds a graph structure from entities and their relationships."""
        try:
            # Create document node
            document_metadata = self.mongo_client.get_document(document_id)
            if not document_metadata:
                print(f"Document with ID {document_id} not found.")
                return False
            
            title = document_metadata.get("metadata", {}).get("title", "Untitled Document")
            if not self.neo4j_client.create_document_node(document_id, title, document_metadata.get("metadata", {})):
                print(f"Failed to create document node for {document_id}.")
                return False
            
            # Create entity nodes
            for entity in entities:
                entity_id = entity.get("entity_id")
                entity_type = entity.get("entity_type")
                properties = entity.get("properties", {})
                if not self.neo4j_client.create_entity_node(entity_id, entity_type, properties):
                    print(f"Failed to create entity node for {entity_id}.")
                    return False
            
            # Create relationships
            for relationship in relationships:
                from_entity_id = relationship.get("from_entity_id")
                to_entity_id = relationship.get("to_entity_id")
                relationship_type = relationship.get("relationship_type")
                properties = relationship.get("properties", {})
                if not self.neo4j_client.create_relationship(from_entity_id, to_entity_id, relationship_type, properties):
                    print(f"Failed to create relationship from {from_entity_id} to {to_entity_id}.")
                    return False
            
            return True
        except Exception as e:
            print(f"Error building graph: {e}")
            return False

    def register_document_vectors(self, document_id: str, chunk_texts: List[str], embeddings: List[List[float]]):
        """Registers document vectors in the Milvus vector database."""
        self.milvus_client.insert_vectors(document_id, chunk_texts, embeddings)

    def close(self):
        """Closes the connections to the databases."""
        self.neo4j_client.close()
        self.mongo_client.close()
        self.milvus_client.close()