from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Load database configurations from environment variables
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE')
POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')

# PostgreSQL connection
POSTGRES_URL = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DATABASE}"
postgres_engine = create_engine(POSTGRES_URL)
PostgresSession = sessionmaker(bind=postgres_engine)

# MongoDB connection (using SQLAlchemy's MongoDB dialect)
MONGODB_URL = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@mongodb:27017/{POSTGRES_DATABASE}"
mongodb_engine = create_engine(MONGODB_URL)
MongoDBSession = sessionmaker(bind=mongodb_engine)

def get_postgres_session():
    """Create a new PostgreSQL session."""
    return PostgresSession()

def get_mongodb_session():
    """Create a new MongoDB session."""
    return MongoDBSession()