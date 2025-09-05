import asyncio
import logging
from typing import Optional
from langchain_ollama import OllamaLLM
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, ollama_url: str = "http://localhost:11434", model_name: str = "llama2"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.llm = None
        
    async def initialize(self):
        """Initialize the Ollama LLM connection"""
        try:
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            self.llm = OllamaLLM(
                base_url=self.ollama_url,
                model=self.model_name,
                callback_manager=callback_manager,
                temperature=0.7,
            )
            
            # Test connection
            test_response = await self._async_invoke("Hello")
            logger.info(f"LLM service initialized successfully. Test response: {test_response[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def _async_invoke(self, prompt: str) -> str:
        """Async wrapper for LLM invocation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.llm.invoke, prompt)
    
    async def chat(self, message: str, context: Optional[str] = None) -> str:
        """Chat with the LLM"""
        try:
            if context:
                prompt = f"Context: {context}\n\nUser: {message}\n\nAssistant:"
            else:
                prompt = f"User: {message}\n\nAssistant:"
            
            response = await self._async_invoke(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise
    
    async def generate_embeddings(self, text: str) -> list:
        """Generate embeddings for text (placeholder for future implementation)"""
        # This would typically use a separate embedding model
        # For now, return a simple hash-based representation
        return [hash(text) % 1000 / 1000.0] * 384  # Simulated 384-dim embedding
