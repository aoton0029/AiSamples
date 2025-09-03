import asyncio
import grpc
from concurrent import futures
import sys
import os
from typing import List, Dict, Any
import numpy as np

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

from fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingServiceImpl(mcp_service_pb2_grpc.EmbeddingServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("EmbeddingService")
        self.setup_embedding_models()
    
    def setup_embedding_models(self):
        """Initialize various embedding models"""
        self.models = {}
        
        # Load default sentence transformer models
        try:
            self.models['all-MiniLM-L6-v2'] = SentenceTransformer('all-MiniLM-L6-v2')
            self.models['all-mpnet-base-v2'] = SentenceTransformer('all-mpnet-base-v2')
        except Exception as e:
            logger.warning(f"Could not load sentence transformer models: {e}")
        
        # Setup LangChain embeddings
        try:
            self.langchain_embeddings = {
                'huggingface': HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2'),
            }
            # OpenAI embeddings require API key
            if os.getenv('OPENAI_API_KEY'):
                self.langchain_embeddings['openai'] = OpenAIEmbeddings()
        except Exception as e:
            logger.warning(f"Could not setup LangChain embeddings: {e}")
        
        # Setup LlamaIndex embeddings
        try:
            self.llama_embeddings = {
                'huggingface': HuggingFaceEmbedding(model_name='all-MiniLM-L6-v2'),
            }
            if os.getenv('OPENAI_API_KEY'):
                self.llama_embeddings['openai'] = OpenAIEmbedding()
        except Exception as e:
            logger.warning(f"Could not setup LlamaIndex embeddings: {e}")
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="Embedding Service is healthy"
        )
    
    async def GenerateEmbeddings(self, request, context):
        """Generate embeddings for texts"""
        try:
            texts = list(request.texts)
            model_name = request.model or 'all-MiniLM-L6-v2'
            embedding_config = dict(request.embedding_config)
            provider = embedding_config.get('provider', 'sentence_transformers')
            
            logger.info(f"Generating embeddings for {len(texts)} texts using {model_name}")
            
            embeddings = []
            
            if provider == 'sentence_transformers' and model_name in self.models:
                # Use sentence transformers
                model = self.models[model_name]
                vectors = model.encode(texts)
                
                for vector in vectors:
                    embedding = mcp_service_pb2.Embedding(
                        values=vector.tolist(),
                        model=model_name,
                        dimension=len(vector)
                    )
                    embeddings.append(embedding)
            
            elif provider == 'langchain' and hasattr(self, 'langchain_embeddings'):
                # Use LangChain embeddings
                if model_name in self.langchain_embeddings:
                    model = self.langchain_embeddings[model_name]
                    vectors = await asyncio.to_thread(model.embed_documents, texts)
                    
                    for vector in vectors:
                        embedding = mcp_service_pb2.Embedding(
                            values=vector,
                            model=model_name,
                            dimension=len(vector)
                        )
                        embeddings.append(embedding)
            
            elif provider == 'llama_index' and hasattr(self, 'llama_embeddings'):
                # Use LlamaIndex embeddings
                if model_name in self.llama_embeddings:
                    model = self.llama_embeddings[model_name]
                    
                    for text in texts:
                        vector = await asyncio.to_thread(model.get_text_embedding, text)
                        embedding = mcp_service_pb2.Embedding(
                            values=vector,
                            model=model_name,
                            dimension=len(vector)
                        )
                        embeddings.append(embedding)
            
            else:
                # Default to sentence transformers if model exists
                if model_name in self.models:
                    model = self.models[model_name]
                    vectors = model.encode(texts)
                    
                    for vector in vectors:
                        embedding = mcp_service_pb2.Embedding(
                            values=vector.tolist(),
                            model=model_name,
                            dimension=len(vector)
                        )
                        embeddings.append(embedding)
                else:
                    raise ValueError(f"Model {model_name} not found")
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            
            return mcp_service_pb2.EmbeddingResponse(
                embeddings=embeddings,
                success=True,
                message=f"Successfully generated {len(embeddings)} embeddings"
            )
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return mcp_service_pb2.EmbeddingResponse(
                embeddings=[],
                success=False,
                message=f"Error generating embeddings: {str(e)}"
            )

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_EmbeddingServiceServicer_to_server(
        EmbeddingServiceImpl(), server
    )
    
    listen_addr = '[::]:50053'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Embedding Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
