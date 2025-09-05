import asyncio
import grpc
from concurrent import futures
import sys
import os
from typing import List, Dict, Any
from jinja2 import Template

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

from fastmcp import FastMCP
from langchain.schema import Document as LangchainDocument
from langchain.prompts import PromptTemplate
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core import get_response_synthesizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextBuilderServiceImpl(mcp_service_pb2_grpc.ContextBuilderServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("ContextBuilderService")
        self.setup_templates()
    
    def setup_templates(self):
        """Initialize prompt templates"""
        self.templates = {
            'simple': Template("""
Based on the following context, please answer the question:

Context:
{% for result in search_results %}
Document {{ loop.index }}:
{{ result.document.content }}

{% endfor %}

Question: {{ query }}

Answer:"""),
            
            'rag': Template("""
You are a helpful AI assistant. Use the following pieces of context to answer the user's question.
If you don't know the answer based on the context, just say that you don't know.

Context:
{% for result in search_results %}
## Source {{ loop.index }} (Score: {{ "%.3f"|format(result.score) }})
{{ result.document.content }}

{% endfor %}

Question: {{ query }}

Based on the above context, please provide a comprehensive answer:"""),
            
            'detailed': Template("""
Context Information:
===================
{% for result in search_results %}
Document ID: {{ result.id }}
Relevance Score: {{ "%.3f"|format(result.score) }}
Content Type: {{ result.document.content_type }}

Content:
{{ result.document.content }}

Metadata:
{% for key, value in result.document.metadata.items() %}
- {{ key }}: {{ value }}
{% endfor %}

---

{% endfor %}

Query: {{ query }}

Instructions:
1. Analyze all provided documents
2. Extract relevant information 
3. Synthesize a comprehensive response
4. Cite sources where appropriate

Response:"""),
            
            'summary': Template("""
Please summarize the following documents in relation to the query: "{{ query }}"

Documents:
{% for result in search_results %}
{{ loop.index }}. {{ result.document.content[:500] }}...

{% endfor %}

Summary:""")
        }
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="Context Builder Service is healthy"
        )
    
    async def BuildContext(self, request, context):
        """Build context and prompt from search results"""
        try:
            query = request.query
            search_results = list(request.search_results)
            context_config = dict(request.context_config)
            
            template_type = context_config.get('template', 'rag')
            max_context_length = int(context_config.get('max_length', 4000))
            include_metadata = context_config.get('include_metadata', 'true').lower() == 'true'
            
            logger.info(f"Building context for query: '{query}' with {len(search_results)} results")
            
            # Filter and sort results
            filtered_results = self._filter_results(search_results, context_config)
            
            # Build context string
            context = self._build_context_string(filtered_results, max_context_length, include_metadata)
            
            # Generate prompt
            prompt = self._generate_prompt(query, filtered_results, template_type, context_config)
            
            logger.info(f"Built context of length {len(context)} and prompt of length {len(prompt)}")
            
            return mcp_service_pb2.ContextBuildResponse(
                context=context,
                prompt=prompt,
                success=True,
                message=f"Successfully built context from {len(filtered_results)} results"
            )
            
        except Exception as e:
            logger.error(f"Error building context: {str(e)}")
            return mcp_service_pb2.ContextBuildResponse(
                context="",
                prompt="",
                success=False,
                message=f"Error building context: {str(e)}"
            )
    
    def _filter_results(self, search_results, config):
        """Filter and sort search results"""
        # Sort by score (descending)
        sorted_results = sorted(search_results, key=lambda x: x.score, reverse=True)
        
        # Apply score threshold
        min_score = float(config.get('min_score', 0.0))
        filtered_results = [r for r in sorted_results if r.score >= min_score]
        
        # Limit number of results
        max_results = int(config.get('max_results', 10))
        return filtered_results[:max_results]
    
    def _build_context_string(self, search_results, max_length, include_metadata):
        """Build a context string from search results"""
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(search_results):
            doc = result.document
            
            # Build document context
            doc_context = f"Document {i+1}:\n{doc.content}\n"
            
            if include_metadata and doc.metadata:
                metadata_str = "\n".join([f"{k}: {v}" for k, v in doc.metadata.items()])
                doc_context += f"Metadata:\n{metadata_str}\n"
            
            doc_context += f"Relevance Score: {result.score:.3f}\n\n"
            
            # Check length limit
            if current_length + len(doc_context) > max_length:
                if current_length == 0:  # First document is too long, truncate it
                    remaining_length = max_length - 200  # Leave some space for metadata
                    doc_context = doc_context[:remaining_length] + "...\n\n"
                    context_parts.append(doc_context)
                break
            
            context_parts.append(doc_context)
            current_length += len(doc_context)
        
        return "".join(context_parts)
    
    def _generate_prompt(self, query, search_results, template_type, config):
        """Generate a prompt using the specified template"""
        if template_type not in self.templates:
            template_type = 'rag'  # Default fallback
        
        template = self.templates[template_type]
        
        try:
            # Render template
            prompt = template.render(
                query=query,
                search_results=search_results,
                config=config
            )
            
            # Apply any post-processing
            max_prompt_length = int(config.get('max_prompt_length', 8000))
            if len(prompt) > max_prompt_length:
                prompt = prompt[:max_prompt_length] + "\n\n[Content truncated due to length limits]"
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            # Fallback to simple template
            return f"Context: {self._build_context_string(search_results, 2000, False)}\n\nQuestion: {query}\n\nAnswer:"

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_ContextBuilderServiceServicer_to_server(
        ContextBuilderServiceImpl(), server
    )
    
    listen_addr = '[::]:50056'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Context Builder Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
