from fastapi import APIRouter
from src.database.connections import get_postgres_session, get_mongodb_session

router = APIRouter()

# Include your route definitions here
# Example: 
# @router.get("/health")
# def health_check():
#     return {"status": "healthy"}

# You can also define routes that interact with the database sessions
# Example:
# @router.get("/data")
# def get_data():
#     with get_postgres_session() as session:
#         # Fetch data from PostgreSQL
#         pass
#     with get_mongodb_session() as session:
#         # Fetch data from MongoDB
#         pass
#     return {"data": "your data here"}