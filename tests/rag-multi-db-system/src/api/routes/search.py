from fastapi import APIRouter, HTTPException
from typing import List
from src.services.document_service import DocumentService
from src.services.vector_service import VectorService
from src.services.graph_service import GraphService
from src.models.search_result import SearchResult

router = APIRouter()

document_service = DocumentService()
vector_service = VectorService()
graph_service = GraphService()

@router.get("/search/documents", response_model=List[SearchResult])
async def search_documents(query: str):
    try:
        documents = document_service.search_by_query(query)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/vectors", response_model=List[SearchResult])
async def search_vectors(query: str):
    try:
        vectors = vector_service.search_vectors(query)
        return vectors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/graph", response_model=List[SearchResult])
async def search_graph(query: str):
    try:
        graph_results = graph_service.search_graph(query)
        return graph_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))