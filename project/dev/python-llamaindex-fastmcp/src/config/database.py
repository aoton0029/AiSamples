from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection settings
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE')
POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = 'postgres'
POSTGRES_PORT = '5432'

MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_HOST = 'mongodb'
MONGODB_PORT = '27017'
MONGODB_DATABASE = 'n8n'

# SQLAlchemy PostgreSQL connection
postgres_url = f'postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}'
postgres_engine = create_engine(postgres_url)
PostgresSession = sessionmaker(bind=postgres_engine)

# MongoDB connection (using SQLAlchemy)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String

Base = declarative_base()

class MongoDBModel(Base):
    __tablename__ = 'your_mongodb_collection_name'  # Replace with your actual collection name
    id = Column(String, primary_key=True)
    # Define other fields as needed

# Function to create a new PostgreSQL session
def get_postgres_session():
    return PostgresSession()

# Function to connect to MongoDB (using pymongo or similar)
def get_mongodb_connection():
    from pymongo import MongoClient
    mongo_client = MongoClient(f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/')
    return mongo_client[MONGODB_DATABASE]  # Return the database instance