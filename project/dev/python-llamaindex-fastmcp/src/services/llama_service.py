from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from llama_index import LlamaIndex
from fastmcp import FastMCP

class LlamaService:
    def __init__(self, db_session: Session, async_db_session: AsyncSession):
        self.db_session = db_session
        self.async_db_session = async_db_session
        self.llama_index = LlamaIndex()
        self.fast_mcp = FastMCP()

    def add_data_to_index(self, data):
        # Logic to add data to LlamaIndex
        self.llama_index.add(data)

    def query_index(self, query):
        # Logic to query the LlamaIndex
        return self.llama_index.query(query)

    async def async_add_data_to_index(self, data):
        # Asynchronous logic to add data to LlamaIndex
        await self.llama_index.async_add(data)

    async def async_query_index(self, query):
        # Asynchronous logic to query the LlamaIndex
        return await self.llama_index.async_query(query)

    def process_data_with_fastmcp(self, data):
        # Logic to process data using FastMCP
        return self.fast_mcp.process(data)