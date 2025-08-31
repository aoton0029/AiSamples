from .base import BaseRepository
from sqlalchemy.orm import Session
from ..models.postgres import YourPostgresModel
from ..models.mongodb import YourMongoModel

class PostgresRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_all(self):
        return self.db.query(YourPostgresModel).all()

    def get_by_id(self, id: int):
        return self.db.query(YourPostgresModel).filter(YourPostgresModel.id == id).first()

    def create(self, obj: YourPostgresModel):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

class MongoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)

    def get_all(self):
        return self.db.find()

    def get_by_id(self, id: str):
        return self.db.find_one({"_id": id})

    def create(self, obj):
        self.db.insert_one(obj)
        return obj