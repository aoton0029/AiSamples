import asyncio
import grpc
from concurrent import futures
import sys
import os
from typing import List, Dict, Any

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

from fastmcp import FastMCP
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    SpacyTextSplitter
)
from llama_index.core.node_parser import SimpleNodeParser, SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChunkingServiceImpl(mcp_service_pb2_grpc.ChunkingServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("ChunkingService")
        self.setup_chunkers()
    
    def setup_chunkers(self):
        """Initialize various chunking strategies"""
        self.chunkers = {
            'recursive': RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            ),
            'token': TokenTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            ),
            'sentence': SentenceSplitter(
                chunk_size=1000,
                chunk_overlap=200
            ),
            'simple': SimpleNodeParser.from_defaults()
        }
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="Chunking Service is healthy"
        )
    
    async def ChunkDocument(self, request, context):
        """Chunk a document using specified strategy"""
        try:
            document = request.document
            chunk_config = dict(request.chunk_config)
            
            # Get chunking strategy
            strategy = chunk_config.get('strategy', 'recursive')
            chunk_size = int(chunk_config.get('chunk_size', 1000))
            chunk_overlap = int(chunk_config.get('chunk_overlap', 200))
            
            logger.info(f"Chunking document {document.id} with strategy {strategy}")
            
            # Prepare chunker
            if strategy == 'recursive':
                chunker = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                chunks = chunker.split_text(document.content)
                
            elif strategy == 'token':
                chunker = TokenTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                chunks = chunker.split_text(document.content)
                
            elif strategy == 'sentence':
                chunker = SentenceSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                llama_doc = LlamaDocument(text=document.content)
                nodes = chunker.get_nodes_from_documents([llama_doc])
                chunks = [node.text for node in nodes]
                
            else:
                # Default to simple splitting
                chunker = SimpleNodeParser.from_defaults()
                llama_doc = LlamaDocument(text=document.content)
                nodes = chunker.get_nodes_from_documents([llama_doc])
                chunks = [node.text for node in nodes]
            
            # Create response chunks
            response_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk_doc = mcp_service_pb2.Document(
                    id=f"{document.id}_chunk_{i}",
                    content=chunk_text,
                    content_type=document.content_type,
                    metadata=dict(document.metadata),
                    timestamp=document.timestamp
                )
                # Add chunk metadata
                chunk_doc.metadata.update({
                    'chunk_index': str(i),
                    'parent_document_id': document.id,
                    'chunking_strategy': strategy
                })
                response_chunks.append(chunk_doc)
            
            logger.info(f"Successfully chunked document {document.id} into {len(response_chunks)} chunks")
            
            return mcp_service_pb2.ChunkResponse(
                chunks=response_chunks,
                success=True,
                message=f"Successfully chunked into {len(response_chunks)} chunks"
            )
            
        except Exception as e:
            logger.error(f"Error chunking document: {str(e)}")
            return mcp_service_pb2.ChunkResponse(
                chunks=[],
                success=False,
                message=f"Error chunking document: {str(e)}"
            )

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_ChunkingServiceServicer_to_server(
        ChunkingServiceImpl(), server
    )
    
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Chunking Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
