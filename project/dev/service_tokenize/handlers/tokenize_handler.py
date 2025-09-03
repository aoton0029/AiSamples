from typing import List, Dict, Any, Optional
import tiktoken
from transformers import AutoTokenizer
from loguru import logger

from ..models import TokenizeRequest, TokenizeResponse, TokenizeMethod
from ..config import settings


class TokenizeHandler:
    def __init__(self):
        self._tokenizers = {}
        self._initialize_tokenizers()
    
    def _initialize_tokenizers(self):
        """Initialize commonly used tokenizers"""
        try:
            # Initialize tiktoken for OpenAI models
            self._tokenizers[TokenizeMethod.TIKTOKEN] = {
                "gpt-3.5-turbo": tiktoken.encoding_for_model("gpt-3.5-turbo"),
                "gpt-4": tiktoken.encoding_for_model("gpt-4"),
                "text-davinci-003": tiktoken.encoding_for_model("text-davinci-003")
            }
            
            # Initialize HuggingFace tokenizers
            self._tokenizers[TokenizeMethod.HUGGINGFACE] = {}
            
            logger.info("Tokenizers initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing tokenizers: {e}")
    
    async def tokenize_text(self, request: TokenizeRequest) -> TokenizeResponse:
        """Tokenize text based on the specified method"""
        try:
            if request.method == TokenizeMethod.TIKTOKEN:
                return await self._tokenize_tiktoken(request)
            elif request.method == TokenizeMethod.HUGGINGFACE:
                return await self._tokenize_huggingface(request)
            else:
                raise ValueError(f"Unsupported tokenization method: {request.method}")
                
        except Exception as e:
            logger.error(f"Error in tokenize_text: {e}")
            raise
    
    async def _tokenize_tiktoken(self, request: TokenizeRequest) -> TokenizeResponse:
        """Tokenize using tiktoken"""
        model_name = request.model_name or settings.openai_model
        
        if model_name not in self._tokenizers[TokenizeMethod.TIKTOKEN]:
            self._tokenizers[TokenizeMethod.TIKTOKEN][model_name] = tiktoken.encoding_for_model(model_name)
        
        encoder = self._tokenizers[TokenizeMethod.TIKTOKEN][model_name]
        tokens = encoder.encode(request.text)
        token_strings = [encoder.decode([token]) for token in tokens]
        
        # Apply max_tokens limit if specified
        if request.max_tokens and len(tokens) > request.max_tokens:
            tokens = tokens[:request.max_tokens]
            token_strings = token_strings[:request.max_tokens]
        
        # Create chunks if needed
        chunks = None
        if request.max_tokens:
            chunks = self._create_chunks(request.text, encoder, request.max_tokens, request.chunk_overlap)
        
        return TokenizeResponse(
            tokens=token_strings,
            token_count=len(token_strings),
            chunks=chunks,
            metadata={
                "method": request.method,
                "model": model_name,
                "original_length": len(request.text)
            }
        )
    
    async def _tokenize_huggingface(self, request: TokenizeRequest) -> TokenizeResponse:
        """Tokenize using HuggingFace tokenizers"""
        model_name = request.model_name or settings.huggingface_model
        
        if model_name not in self._tokenizers[TokenizeMethod.HUGGINGFACE]:
            self._tokenizers[TokenizeMethod.HUGGINGFACE][model_name] = AutoTokenizer.from_pretrained(model_name)
        
        tokenizer = self._tokenizers[TokenizeMethod.HUGGINGFACE][model_name]
        encoded = tokenizer.encode(request.text, add_special_tokens=False)
        tokens = tokenizer.convert_ids_to_tokens(encoded)
        
        # Apply max_tokens limit if specified
        if request.max_tokens and len(tokens) > request.max_tokens:
            tokens = tokens[:request.max_tokens]
            encoded = encoded[:request.max_tokens]
        
        # Create chunks if needed
        chunks = None
        if request.max_tokens:
            chunks = self._create_chunks_hf(request.text, tokenizer, request.max_tokens, request.chunk_overlap)
        
        return TokenizeResponse(
            tokens=tokens,
            token_count=len(tokens),
            chunks=chunks,
            metadata={
                "method": request.method,
                "model": model_name,
                "original_length": len(request.text)
            }
        )
    
    def _create_chunks(self, text: str, encoder, max_tokens: int, overlap: int = 0) -> List[str]:
        """Create text chunks using tiktoken encoder"""
        tokens = encoder.encode(text)
        chunks = []
        
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            if end >= len(tokens):
                break
                
            start = end - overlap
        
        return chunks
    
    def _create_chunks_hf(self, text: str, tokenizer, max_tokens: int, overlap: int = 0) -> List[str]:
        """Create text chunks using HuggingFace tokenizer"""
        tokens = tokenizer.encode(text, add_special_tokens=False)
        chunks = []
        
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append(chunk_text)
            
            if end >= len(tokens):
                break
                
            start = end - overlap
        
        return chunks
