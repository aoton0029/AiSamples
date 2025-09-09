from fastapi import APIRouter, HTTPException
from src.services.integration_service import IntegrationService

router = APIRouter()
integration_service = IntegrationService()

@router.get("/status")
async def get_status():
    return {"status": "running"}

@router.post("/reindex")
async def reindex_documents():
    try:
        integration_service.reindex_all_documents()
        return {"message": "Reindexing started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics():
    try:
        metrics = integration_service.get_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))