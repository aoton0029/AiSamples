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
import ollama
import openai
from langchain.llms import Ollama
from langchain.chat_models import ChatOpenAI
from llama_index.llms.ollama import Ollama as LlamaOllama
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InferenceServiceImpl(mcp_service_pb2_grpc.InferenceServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("InferenceService")
        self.setup_models()
    
    def setup_models(self):
        """Initialize various inference models"""
        self.models = {}
        
        # Setup Ollama models
        try:
            # Test Ollama connection
            available_models = ollama.list()
            self.ollama_available = True
            self.ollama_models = [model['name'] for model in available_models['models']]
            logger.info(f"Ollama available with models: {self.ollama_models}")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self.ollama_available = False
            self.ollama_models = []
        
        # Setup OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                openai.api_key = os.getenv('OPENAI_API_KEY')
                self.openai_available = True
                logger.info("OpenAI API available")
            except Exception as e:
                logger.warning(f"OpenAI not available: {e}")
                self.openai_available = False
        else:
            self.openai_available = False
        
        # Setup LangChain models
        self.langchain_models = {}
        if self.ollama_available:
            self.langchain_models['ollama'] = Ollama(model="llama2")
        if self.openai_available:
            self.langchain_models['openai'] = ChatOpenAI()
        
        # Setup LlamaIndex models
        self.llama_models = {}
        if self.ollama_available:
            self.llama_models['ollama'] = LlamaOllama(model="llama2")
        if self.openai_available:
            self.llama_models['openai'] = LlamaOpenAI()
        
        # Setup local transformers models (optional)
        try:
            self.local_models = {
                'gpt2': pipeline('text-generation', model='gpt2')
            }
            logger.info("Local models loaded")
        except Exception as e:
            logger.warning(f"Could not load local models: {e}")
            self.local_models = {}
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="Inference Service is healthy"
        )
    
    async def GenerateResponse(self, request, context):
        """Generate response using specified model"""
        try:
            prompt = request.prompt
            model = request.model or 'llama2'
            inference_config = dict(request.inference_config)
            provider = inference_config.get('provider', 'ollama')
            
            logger.info(f"Generating response using {provider}:{model}")
            
            response = ""
            
            if provider == 'ollama' and self.ollama_available:
                response = await self._generate_ollama(prompt, model, inference_config)
            
            elif provider == 'openai' and self.openai_available:
                response = await self._generate_openai(prompt, model, inference_config)
            
            elif provider == 'langchain':
                response = await self._generate_langchain(prompt, model, inference_config)
            
            elif provider == 'llama_index':
                response = await self._generate_llama_index(prompt, model, inference_config)
            
            elif provider == 'local':
                response = await self._generate_local(prompt, model, inference_config)
            
            else:
                # Default to Ollama
                if self.ollama_available:
                    response = await self._generate_ollama(prompt, model, inference_config)
                else:
                    raise ValueError(f"Provider {provider} not available")
            
            logger.info(f"Generated response of length {len(response)}")
            
            return mcp_service_pb2.InferenceResponse(
                response=response,
                success=True,
                message="Response generated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return mcp_service_pb2.InferenceResponse(
                response="",
                success=False,
                message=f"Error generating response: {str(e)}"
            )
    
    async def _generate_ollama(self, prompt, model, config):
        """Generate response using Ollama"""
        try:
            response = await asyncio.to_thread(
                ollama.generate,
                model=model,
                prompt=prompt,
                options={
                    'temperature': float(config.get('temperature', 0.7)),
                    'top_p': float(config.get('top_p', 0.9)),
                    'max_tokens': int(config.get('max_tokens', 1000))
                }
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def _generate_openai(self, prompt, model, config):
        """Generate response using OpenAI"""
        try:
            client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = await client.chat.completions.create(
                model=model or 'gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=float(config.get('temperature', 0.7)),
                max_tokens=int(config.get('max_tokens', 1000))
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def _generate_langchain(self, prompt, model, config):
        """Generate response using LangChain"""
        try:
            provider_type = config.get('type', 'ollama')
            if provider_type in self.langchain_models:
                llm = self.langchain_models[provider_type]
                response = await asyncio.to_thread(llm.invoke, prompt)
                return response.content if hasattr(response, 'content') else str(response)
            else:
                raise ValueError(f"LangChain model type {provider_type} not available")
        except Exception as e:
            logger.error(f"LangChain generation error: {e}")
            raise
    
    async def _generate_llama_index(self, prompt, model, config):
        """Generate response using LlamaIndex"""
        try:
            provider_type = config.get('type', 'ollama')
            if provider_type in self.llama_models:
                llm = self.llama_models[provider_type]
                response = await asyncio.to_thread(llm.complete, prompt)
                return response.text
            else:
                raise ValueError(f"LlamaIndex model type {provider_type} not available")
        except Exception as e:
            logger.error(f"LlamaIndex generation error: {e}")
            raise
    
    async def _generate_local(self, prompt, model, config):
        """Generate response using local transformers"""
        try:
            if model in self.local_models:
                generator = self.local_models[model]
                max_length = int(config.get('max_tokens', 100)) + len(prompt.split())
                
                response = await asyncio.to_thread(
                    generator,
                    prompt,
                    max_length=max_length,
                    temperature=float(config.get('temperature', 0.7)),
                    do_sample=True
                )
                
                generated_text = response[0]['generated_text']
                # Remove the original prompt from the response
                return generated_text[len(prompt):].strip()
            else:
                raise ValueError(f"Local model {model} not available")
        except Exception as e:
            logger.error(f"Local generation error: {e}")
            raise

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceServiceImpl(), server
    )
    
    listen_addr = '[::]:50057'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Inference Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
