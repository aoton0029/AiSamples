from src.core.redis_client import RedisClient
from src.core.mongo_client import MongoClient
from src.core.neo4j_client import Neo4jClient
from src.core.milvus_client import MilvusClient
from src.core.ollama_connector import OllamaConnector
from src.processors.document_preprocessor import preprocess_documents
from src.processors.embedding_generator import generate_embeddings
from src.services.document_service import DocumentService
from src.services.vector_service import VectorService
from src.services.graph_service import GraphService
from src.services.integration_service import IntegrationService
from fastapi import FastAPI

app = FastAPI()

# Initialize clients
redis_client = RedisClient()
mongo_client = MongoClient()
neo4j_client = Neo4jClient()
milvus_client = MilvusClient()
ollama_connector = OllamaConnector()

# Initialize services
document_service = DocumentService(mongo_client)
vector_service = VectorService(milvus_client)
graph_service = GraphService(neo4j_client)
integration_service = IntegrationService(document_service, vector_service, graph_service)

@app.post("/upload-document/")
async def upload_document(file_path: str):
    # Preprocess the document
    documents = preprocess_documents(file_path)
    
    # Generate embeddings
    embeddings = generate_embeddings(documents)
    
    # Save documents and embeddings
    for doc, embedding in zip(documents, embeddings):
        document_id = document_service.save_document(doc)
        vector_service.insert_vectors(document_id, doc.chunk_texts, embedding)
        graph_service.create_graph_from_document(doc)
    
    return {"message": "Document uploaded successfully."}

@app.get("/search/")
async def search(query: str):
    results = integration_service.search(query)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)