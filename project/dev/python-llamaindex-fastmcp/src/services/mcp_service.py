from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastmcp import FastMCP
from config.database import get_postgres_session, get_mongodb_session

class MCPService:
    def __init__(self):
        self.postgres_session = get_postgres_session()
        self.mongodb_session = get_mongodb_session()
        self.fastmcp = FastMCP()

    def process_data(self, data):
        # Process data using FastMCP
        processed_data = self.fastmcp.process(data)
        return processed_data

    def save_to_postgres(self, model):
        with self.postgres_session() as session:
            session.add(model)
            session.commit()

    def save_to_mongodb(self, document):
        with self.mongodb_session() as session:
            session.insert_one(document)

    def close_sessions(self):
        self.postgres_session.remove()
        self.mongodb_session.close()