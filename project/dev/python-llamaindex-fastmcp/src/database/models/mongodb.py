from sqlalchemy import Column, String, ObjectId
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from bson import ObjectId as BsonObjectId

Base = declarative_base()

class MongoDBModel(Base):
    __abstract__ = True

    id: Mapped[BsonObjectId] = mapped_column(ObjectId, primary_key=True)

class User(MongoDBModel):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

class Product(MongoDBModel):
    __tablename__ = 'products'

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)