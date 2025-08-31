from fastapi import APIRouter
from sqlalchemy.orm import Session
from src.config.database import get_db

router = APIRouter()

@router.get("/health")
def health_check(db: Session = next(get_db())):
    return {"status": "healthy"}