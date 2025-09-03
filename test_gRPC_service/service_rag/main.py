import asyncio
import grpc
from concurrent import futures
import sys
import os
from typing import List, Dict, Any
import json
import numpy as np

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

from fastmcp import FastMCP
from pymilvus import Collection, connections
import redis
import pymongo
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGServiceImpl(mcp_service_pb2_grpc.RAGServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("RAGService")
        self.setup_databases()
        self.setup_embedding_model()
    
    def setup_databases(self):
        """Initialize database connections"""
        try:
            connections.connect("default", host="localhost", port="19530")
            self.milvus_connected = True
            logger.info("Connected to Milvus")
        except Exception as e:
            logger.warning(f"Could not connect to Milvus: {e}")
            self.milvus_connected = False
        
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.redis_client = None
        
        try:
            self.mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
            self.mongo_db = self.mongo_client['document_store']
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB: {e}")
            self.mongo_client = None
        
        try:
            self.neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.warning(f"Could not connect to Neo4j: {e}")
            self.neo4j_driver = None
    
    def setup_embedding_model(self):
        """Setup embedding model for query encoding"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded embedding model")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            self.embedding_model = None
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="RAG Service is healthy"
        )
    
    async def SearchDocuments(self, request, context):
        """Search documents across multiple databases"""
        try:
            query = request.query
            top_k = request.top_k or 10
            index_types = list(request.index_types) or ["vector", "document"]
            search_config = dict(request.search_config)
            
            logger.info(f"Searching for query: '{query}' across {index_types}")
            
            all_results = []
            
            # Search across specified index types
            for index_type in index_types:
                if index_type == "vector":
                    results = await self._search_vector(query, top_k, search_config)
                elif index_type == "document":
                    results = await self._search_document(query, top_k, search_config)
                elif index_type == "key_value":
                    results = await self._search_key_value(query, top_k, search_config)
                elif index_type == "graph":
                    results = await self._search_graph(query, top_k, search_config)
                else:
                    continue
                
                all_results.extend(results)
            
            # Sort results by score and limit to top_k
            all_results.sort(key=lambda x: x.score, reverse=True)
            final_results = all_results[:top_k]
            
            logger.info(f"Found {len(final_results)} results")
            
            return mcp_service_pb2.RAGSearchResponse(
                results=final_results,
                success=True,
                message=f"Found {len(final_results)} results"
            )
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return mcp_service_pb2.RAGSearchResponse(
                results=[],
                success=False,
                message=f"Error searching documents: {str(e)}"
            )
    
    async def _search_vector(self, query, top_k, config):
        """Search in Milvus vector database"""
        if not self.milvus_connected or not self.embedding_model:
            return []
        
        try:
            collection_name = config.get('collection', 'documents')
            collection = Collection(collection_name)
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Search
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "content", "metadata"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    doc = mcp_service_pb2.Document(
                        id=hit.entity.get('id'),
                        content=hit.entity.get('content'),
                        metadata=json.loads(hit.entity.get('metadata', '{}'))
                    )
                    
                    embedding = mcp_service_pb2.Embedding(
                        values=query_embedding,
                        model='all-MiniLM-L6-v2',
                        dimension=len(query_embedding)
                    )
                    
                    result = mcp_service_pb2.SearchResult(
                        id=hit.entity.get('id'),
                        score=1.0 / (1.0 + hit.distance),  # Convert distance to similarity
                        document=doc,
                        embedding=embedding
                    )
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def _search_document(self, query, top_k, config):
        """Search in MongoDB document store"""
        if not self.mongo_client:
            return []
        
        try:
            collection_name = config.get('collection', 'documents')
            collection = self.mongo_db[collection_name]
            
            # Text search
            results = collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(top_k)
            
            search_results = []
            for doc in results:
                document = mcp_service_pb2.Document(
                    id=doc['_id'],
                    content=doc.get('content', ''),
                    content_type=doc.get('content_type', ''),
                    metadata=doc.get('metadata', {}),
                    timestamp=doc.get('timestamp', 0)
                )
                
                result = mcp_service_pb2.SearchResult(
                    id=doc['_id'],
                    score=doc.get('score', 0.0),
                    document=document
                )
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            return []
    
    async def _search_key_value(self, query, top_k, config):
        """Search in Redis key-value store"""
        if not self.redis_client:
            return []
        
        try:
            prefix = config.get('prefix', 'doc:')
            
            # Simple key pattern matching
            pattern = f"{prefix}*{query.lower()}*"
            keys = self.redis_client.keys(pattern)
            
            search_results = []
            for key in keys[:top_k]:
                value_str = self.redis_client.get(key)
                if value_str:
                    value = json.loads(value_str)
                    doc_id = key.decode().replace(prefix, '')
                    
                    document = mcp_service_pb2.Document(
                        id=doc_id,
                        content=value.get('content', ''),
                        content_type=value.get('content_type', ''),
                        metadata=value.get('metadata', {}),
                        timestamp=value.get('timestamp', 0)
                    )
                    
                    result = mcp_service_pb2.SearchResult(
                        id=doc_id,
                        score=0.8,  # Fixed score for key-value matches
                        document=document
                    )
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in key-value search: {e}")
            return []
    
    async def _search_graph(self, query, top_k, config):
        """Search in Neo4j graph database"""
        if not self.neo4j_driver:
            return []
        
        try:
            with self.neo4j_driver.session() as session:
                # Search documents containing query terms
                cypher_query = """
                MATCH (d:Document)
                WHERE toLower(d.content) CONTAINS toLower($query)
                RETURN d.id as id, d.content as content, d.content_type as content_type,
                       d.timestamp as timestamp, properties(d) as metadata
                LIMIT $limit
                """
                
                results = session.run(cypher_query, query=query, limit=top_k)
                
                search_results = []
                for record in results:
                    metadata = dict(record['metadata'])
                    # Remove standard fields from metadata
                    for field in ['id', 'content', 'content_type', 'timestamp']:
                        metadata.pop(field, None)
                    
                    document = mcp_service_pb2.Document(
                        id=record['id'],
                        content=record['content'] or '',
                        content_type=record['content_type'] or '',
                        metadata=metadata,
                        timestamp=record['timestamp'] or 0
                    )
                    
                    result = mcp_service_pb2.SearchResult(
                        id=record['id'],
                        score=0.7,  # Fixed score for graph matches
                        document=document
                    )
                    search_results.append(result)
                
                return search_results
                
        except Exception as e:
            logger.error(f"Error in graph search: {e}")
            return []

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_RAGServiceServicer_to_server(
        RAGServiceImpl(), server
    )
    
    listen_addr = '[::]:50055'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting RAG Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
