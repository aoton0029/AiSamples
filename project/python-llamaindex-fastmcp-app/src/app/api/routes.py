from fastapi import APIRouter
from app.services.ollama_service import OllamaService
from app.services.milvus_service import MilvusService
from app.services.neo4j_service import Neo4jService
from app.services.redis_service import RedisService
from app.services.mongodb_service import MongoDBService
from app.services.postgres_service import PostgresService

router = APIRouter()

@router.get("/ollama")
async def get_ollama_response(query: str):
    response = await OllamaService.get_response(query)
    return {"response": response}

@router.post("/milvus")
async def insert_milvus_data(data: dict):
    result = await MilvusService.insert_data(data)
    return {"result": result}

@router.get("/neo4j")
async def execute_neo4j_query(query: str):
    result = await Neo4jService.execute_query(query)
    return {"result": result}

@router.get("/redis/{key}")
async def get_redis_value(key: str):
    value = await RedisService.get_value(key)
    return {"value": value}

@router.post("/mongodb")
async def create_mongodb_document(document: dict):
    result = await MongoDBService.create_document(document)
    return {"result": result}

@router.post("/postgres")
async def execute_postgres_query(query: str):
    result = await PostgresService.execute_query(query)
    return {"result": result}