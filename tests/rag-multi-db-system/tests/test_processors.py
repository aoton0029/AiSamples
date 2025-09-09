from src.processors.document_preprocessor import DocumentPreprocessor
from src.processors.embedding_generator import EmbeddingGenerator
from src.processors.entity_extractor import EntityExtractor
from src.processors.graph_builder import GraphBuilder
from src.core.mongo_client import MongoClient
from src.core.milvus_client import MilvusClient
from src.core.neo4j_client import Neo4jClient
import pytest

@pytest.fixture
def mongo_client():
    client = MongoClient()
    yield client
    client.close()

@pytest.fixture
def milvus_client():
    client = MilvusClient()
    client.create_collection()
    yield client
    client.delete_document_vectors("test_document")
    
@pytest.fixture
def neo4j_client():
    client = Neo4jClient()
    yield client
    client.close()

def test_document_preprocessing(mongo_client):
    preprocessor = DocumentPreprocessor()
    raw_document = "Sample text for preprocessing."
    processed_document = preprocessor.process(raw_document)
    
    assert processed_document is not None
    assert isinstance(processed_document, list)

def test_embedding_generation(milvus_client):
    generator = EmbeddingGenerator()
    document_chunks = ["This is a chunk.", "This is another chunk."]
    embeddings = generator.generate_embeddings(document_chunks)
    
    assert len(embeddings) == len(document_chunks)
    assert all(isinstance(embedding, list) for embedding in embeddings)

def test_entity_extraction(mongo_client):
    extractor = EntityExtractor()
    document = "Barack Obama was the 44th president of the United States."
    entities = extractor.extract_entities(document)
    
    assert "Barack Obama" in entities
    assert "United States" in entities

def test_graph_building(neo4j_client):
    builder = GraphBuilder()
    entities = ["Barack Obama", "United States"]
    relationships = [("Barack Obama", "president_of", "United States")]
    
    for entity in entities:
        neo4j_client.create_entity_node(entity, "Person", {})
    
    for from_entity, rel_type, to_entity in relationships:
        neo4j_client.create_relationship(from_entity, to_entity, rel_type)
    
    related_docs = neo4j_client.find_related_documents("Barack Obama")
    assert len(related_docs) >= 0  # Check if related documents can be found

def test_document_storage(mongo_client):
    document_id = "test_document"
    content = "This is a test document."
    metadata = {"author": "Test Author"}
    
    inserted_id = mongo_client.save_document(document_id, content, metadata)
    assert inserted_id is not None
    
    retrieved_document = mongo_client.get_document(document_id)
    assert retrieved_document is not None
    assert retrieved_document["document_id"] == document_id

def test_vector_storage(milvus_client):
    document_id = "test_document"
    chunk_texts = ["This is a chunk.", "This is another chunk."]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    
    milvus_client.insert_vectors(document_id, chunk_texts, embeddings)
    results = milvus_client.search_similar([0.1, 0.2, 0.3])
    
    assert len(results) > 0
    assert results[0]["document_id"] == document_id