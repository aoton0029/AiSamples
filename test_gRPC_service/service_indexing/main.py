import asyncio
import grpc
from concurrent import futures
import sys
import os
from typing import List, Dict, Any
import json

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

from fastmcp import FastMCP
from pymilvus import Collection, connections, FieldSchema, CollectionSchema, DataType, utility
import redis
import pymongo
from neo4j import GraphDatabase
import psycopg2
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexingServiceImpl(mcp_service_pb2_grpc.IndexingServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("IndexingService")
        self.setup_databases()
    
    def setup_databases(self):
        """Initialize database connections"""
        try:
            # Milvus connection
            connections.connect("default", host="localhost", port="19530")
            self.milvus_connected = True
            logger.info("Connected to Milvus")
        except Exception as e:
            logger.warning(f"Could not connect to Milvus: {e}")
            self.milvus_connected = False
        
        try:
            # Redis connection
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.redis_client = None
        
        try:
            # MongoDB connection
            self.mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
            self.mongo_db = self.mongo_client['document_store']
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB: {e}")
            self.mongo_client = None
        
        try:
            # Neo4j connection
            self.neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.warning(f"Could not connect to Neo4j: {e}")
            self.neo4j_driver = None
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="Indexing Service is healthy"
        )
    
    async def IndexDocuments(self, request, context):
        """Index documents in various databases"""
        try:
            documents = list(request.documents)
            embeddings = list(request.embeddings)
            index_type = request.index_type
            index_config = dict(request.index_config)
            
            logger.info(f"Indexing {len(documents)} documents to {index_type}")
            
            indexed_ids = []
            
            if index_type == "vector" and self.milvus_connected:
                indexed_ids = await self._index_to_milvus(documents, embeddings, index_config)
            
            elif index_type == "key_value" and self.redis_client:
                indexed_ids = await self._index_to_redis(documents, index_config)
            
            elif index_type == "document" and self.mongo_client:
                indexed_ids = await self._index_to_mongodb(documents, index_config)
            
            elif index_type == "graph" and self.neo4j_driver:
                indexed_ids = await self._index_to_neo4j(documents, index_config)
            
            else:
                raise ValueError(f"Index type {index_type} not supported or database not connected")
            
            logger.info(f"Successfully indexed {len(indexed_ids)} documents")
            
            return mcp_service_pb2.IndexResponse(
                indexed_ids=indexed_ids,
                success=True,
                message=f"Successfully indexed {len(indexed_ids)} documents to {index_type}"
            )
            
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            return mcp_service_pb2.IndexResponse(
                indexed_ids=[],
                success=False,
                message=f"Error indexing documents: {str(e)}"
            )
    
    async def _index_to_milvus(self, documents, embeddings, config):
        """Index to Milvus vector database"""
        collection_name = config.get('collection', 'documents')
        
        try:
            # Check if collection exists, create if not
            if not utility.has_collection(collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=500),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embeddings[0].dimension if embeddings else 384),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
                ]
                schema = CollectionSchema(fields, f"Collection for {collection_name}")
                collection = Collection(collection_name, schema)
                
                # Create index
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                collection.create_index("embedding", index_params)
            else:
                collection = Collection(collection_name)
            
            # Prepare data for insertion
            data = []
            for doc, emb in zip(documents, embeddings):
                data.append([
                    doc.id,
                    emb.values,
                    doc.content[:65000],  # Truncate if too long
                    json.dumps(dict(doc.metadata))[:65000]
                ])
            
            # Insert data
            collection.insert(data)
            collection.load()
            
            return [doc.id for doc in documents]
            
        except Exception as e:
            logger.error(f"Error indexing to Milvus: {e}")
            return []
    
    async def _index_to_redis(self, documents, config):
        """Index to Redis key-value store"""
        prefix = config.get('prefix', 'doc:')
        
        try:
            indexed_ids = []
            for doc in documents:
                key = f"{prefix}{doc.id}"
                value = {
                    'content': doc.content,
                    'content_type': doc.content_type,
                    'metadata': dict(doc.metadata),
                    'timestamp': doc.timestamp
                }
                self.redis_client.set(key, json.dumps(value))
                indexed_ids.append(doc.id)
            
            return indexed_ids
            
        except Exception as e:
            logger.error(f"Error indexing to Redis: {e}")
            return []
    
    async def _index_to_mongodb(self, documents, config):
        """Index to MongoDB document store"""
        collection_name = config.get('collection', 'documents')
        
        try:
            collection = self.mongo_db[collection_name]
            
            docs_to_insert = []
            for doc in documents:
                mongo_doc = {
                    '_id': doc.id,
                    'content': doc.content,
                    'content_type': doc.content_type,
                    'metadata': dict(doc.metadata),
                    'timestamp': doc.timestamp
                }
                docs_to_insert.append(mongo_doc)
            
            # Insert or update documents
            for mongo_doc in docs_to_insert:
                collection.replace_one(
                    {'_id': mongo_doc['_id']}, 
                    mongo_doc, 
                    upsert=True
                )
            
            return [doc.id for doc in documents]
            
        except Exception as e:
            logger.error(f"Error indexing to MongoDB: {e}")
            return []
    
    async def _index_to_neo4j(self, documents, config):
        """Index to Neo4j graph database"""
        try:
            with self.neo4j_driver.session() as session:
                indexed_ids = []
                
                for doc in documents:
                    # Create document node
                    result = session.run(
                        "MERGE (d:Document {id: $id}) "
                        "SET d.content = $content, d.content_type = $content_type, "
                        "d.timestamp = $timestamp "
                        "RETURN d.id",
                        id=doc.id,
                        content=doc.content,
                        content_type=doc.content_type,
                        timestamp=doc.timestamp
                    )
                    
                    # Add metadata as properties
                    for key, value in doc.metadata.items():
                        session.run(
                            "MATCH (d:Document {id: $id}) SET d[$key] = $value",
                            id=doc.id, key=key, value=value
                        )
                    
                    indexed_ids.append(doc.id)
                
                return indexed_ids
                
        except Exception as e:
            logger.error(f"Error indexing to Neo4j: {e}")
            return []

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_IndexingServiceServicer_to_server(
        IndexingServiceImpl(), server
    )
    
    listen_addr = '[::]:50054'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Indexing Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
