from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from src.services.document_service import DocumentService
from src.services.vector_service import VectorService
from src.services.graph_service import GraphService
from src.processors.document_preprocessor import preprocess_document
from src.processors.embedding_generator import generate_embeddings

router = APIRouter()

document_service = DocumentService()
vector_service = VectorService()
graph_service = GraphService()

@router.post("/documents/upload", response_model=str)
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    document_id = document_service.save_document(file.filename, content.decode())
    
    # Preprocess the document
    chunks = preprocess_document(content.decode())
    
    # Generate embeddings for the chunks
    embeddings = generate_embeddings(chunks)
    
    # Store vectors in the vector database
    vector_service.insert_vectors(document_id, chunks, embeddings)
    
    # Register document in the graph database
    graph_service.register_document(document_id, chunks)
    
    return document_id

@router.get("/documents/{document_id}", response_model=dict)
def get_document(document_id: str):
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/documents/{document_id}", response_model=bool)
def delete_document(document_id: str):
    success = document_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    vector_service.delete_document_vectors(document_id)
    graph_service.delete_document(document_id)
    
    return True