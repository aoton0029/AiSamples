import pytest
from src.services.document_service import DocumentService
from src.services.vector_service import VectorService
from src.services.graph_service import GraphService
from src.core.mongo_client import MongoClient
from src.core.milvus_client import MilvusClient
from src.core.neo4j_client import Neo4jClient

@pytest.fixture
def mongo_client():
    client = MongoClient()
    yield client
    client.close()

@pytest.fixture
def milvus_client():
    client = MilvusClient()
    yield client

@pytest.fixture
def neo4j_client():
    client = Neo4jClient()
    yield client
    client.close()

@pytest.fixture
def document_service(mongo_client):
    return DocumentService(mongo_client)

@pytest.fixture
def vector_service(milvus_client):
    return VectorService(milvus_client)

@pytest.fixture
def graph_service(neo4j_client):
    return GraphService(neo4j_client)

def test_save_document(document_service):
    document_id = "doc_1"
    content = "This is a test document."
    metadata = {"author": "Test Author"}
    result = document_service.save_document(document_id, content, metadata)
    assert result is not None

def test_insert_vector(vector_service):
    document_id = "doc_1"
    chunk_texts = ["This is a chunk of the document."]
    embeddings = [[0.1, 0.2, 0.3]]
    vector_service.insert_vectors(document_id, chunk_texts, embeddings)
    # Add assertions to verify the vectors were inserted correctly

def test_create_entity(graph_service):
    entity_id = "entity_1"
    entity_type = "TestEntity"
    properties = {"name": "Test Name"}
    result = graph_service.create_entity_node(entity_id, entity_type, properties)
    assert result is True

def test_find_related_documents(graph_service):
    entity_id = "entity_1"
    results = graph_service.find_related_documents(entity_id)
    assert isinstance(results, list)  # Ensure results are returned as a list

def test_search_vectors(vector_service):
    query_embedding = [0.1, 0.2, 0.3]
    results = vector_service.search_similar(query_embedding)
    assert isinstance(results, list)  # Ensure results are returned as a list