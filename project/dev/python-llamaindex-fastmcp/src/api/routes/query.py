from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from src.database.connections import get_db
from src.services.llama_service import LlamaService
from src.services.mcp_service import MCPService

router = APIRouter()

@router.post("/query")
async def query_endpoint(query: str, db: Session = next(get_db())):
    try:
        llama_service = LlamaService(db)
        mcp_service = MCPService(db)

        # Process the query using LlamaIndex
        llama_response = await llama_service.process_query(query)

        # Further processing with FastMCP if needed
        mcp_response = await mcp_service.process_response(llama_response)

        return {"llama_response": llama_response, "mcp_response": mcp_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))