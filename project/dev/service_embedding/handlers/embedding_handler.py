from typing import List, Dict, Any, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
from transformers import AutoTokenizer, AutoModel
import torch
from loguru import logger
from langchain.embeddings import OpenAIEmbeddings
from llama_index.embeddings import OpenAIEmbedding

from ..models import EmbeddingRequest, EmbeddingResponse, EmbeddingMethod
from ..config import settings


class EmbeddingHandler:
    def __init__(self):
        self._models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize commonly used embedding models"""
        try:
            # Initialize Sentence Transformers
            if settings.default_embedding_model:
                self._models[EmbeddingMethod.SENTENCE_TRANSFORMERS] = {
                    settings.default_embedding_model: SentenceTransformer(settings.default_embedding_model)
                }
            
            # Initialize OpenAI
            if settings.openai_api_key:
                openai.api_key = settings.openai_api_key
            
            logger.info("Embedding models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing embedding models: {e}")
    
    async def create_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings based on the specified method"""
        try:
            # Ensure text is a list
            texts = request.text if isinstance(request.text, list) else [request.text]
            
            if request.method == EmbeddingMethod.SENTENCE_TRANSFORMERS:
                return await self._embed_sentence_transformers(texts, request)
            elif request.method == EmbeddingMethod.OPENAI:
                return await self._embed_openai(texts, request)
            elif request.method == EmbeddingMethod.HUGGINGFACE:
                return await self._embed_huggingface(texts, request)
            elif request.method == EmbeddingMethod.LANGCHAIN:
                return await self._embed_langchain(texts, request)
            elif request.method == EmbeddingMethod.LLAMAINDEX:
                return await self._embed_llamaindex(texts, request)
            else:
                raise ValueError(f"Unsupported embedding method: {request.method}")
                
        except Exception as e:
            logger.error(f"Error in create_embeddings: {e}")
            raise
    
    async def _embed_sentence_transformers(self, texts: List[str], request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings using Sentence Transformers"""
        model_name = request.model_name or settings.default_embedding_model
        
        # Load model if not cached
        if (EmbeddingMethod.SENTENCE_TRANSFORMERS not in self._models or 
            model_name not in self._models[EmbeddingMethod.SENTENCE_TRANSFORMERS]):
            
            if EmbeddingMethod.SENTENCE_TRANSFORMERS not in self._models:
                self._models[EmbeddingMethod.SENTENCE_TRANSFORMERS] = {}
            
            self._models[EmbeddingMethod.SENTENCE_TRANSFORMERS][model_name] = SentenceTransformer(model_name)
        
        model = self._models[EmbeddingMethod.SENTENCE_TRANSFORMERS][model_name]
        
        # Create embeddings
        embeddings = model.encode(
            texts,
            batch_size=request.batch_size,
            normalize_embeddings=request.normalize,
            convert_to_numpy=True
        )
        
        # Convert to list of lists
        embeddings_list = embeddings.tolist()
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            dimensions=len(embeddings_list[0]) if embeddings_list else 0,
            model_name=model_name,
            metadata={
                "method": request.method,
                "text_count": len(texts),
                "normalized": request.normalize
            }
        )
    
    async def _embed_openai(self, texts: List[str], request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings using OpenAI API"""
        model_name = request.model_name or settings.openai_embedding_model
        
        embeddings_list = []
        
        # Process in batches
        for i in range(0, len(texts), request.batch_size):
            batch_texts = texts[i:i + request.batch_size]
            
            response = await openai.Embedding.acreate(
                input=batch_texts,
                model=model_name
            )
            
            batch_embeddings = [data.embedding for data in response.data]
            embeddings_list.extend(batch_embeddings)
        
        # Normalize if requested
        if request.normalize:
            embeddings_list = [self._normalize_vector(emb) for emb in embeddings_list]
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            dimensions=len(embeddings_list[0]) if embeddings_list else 0,
            model_name=model_name,
            metadata={
                "method": request.method,
                "text_count": len(texts),
                "normalized": request.normalize,
                "usage": response.usage.dict() if hasattr(response, 'usage') else None
            }
        )
    
    async def _embed_huggingface(self, texts: List[str], request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings using HuggingFace transformers"""
        model_name = request.model_name or "sentence-transformers/all-MiniLM-L6-v2"
        
        # Load model if not cached
        if (EmbeddingMethod.HUGGINGFACE not in self._models or 
            model_name not in self._models[EmbeddingMethod.HUGGINGFACE]):
            
            if EmbeddingMethod.HUGGINGFACE not in self._models:
                self._models[EmbeddingMethod.HUGGINGFACE] = {}
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            self._models[EmbeddingMethod.HUGGINGFACE][model_name] = {
                "tokenizer": tokenizer,
                "model": model
            }
        
        tokenizer = self._models[EmbeddingMethod.HUGGINGFACE][model_name]["tokenizer"]
        model = self._models[EmbeddingMethod.HUGGINGFACE][model_name]["model"]
        
        embeddings_list = []
        
        # Process texts
        for text in texts:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Use mean pooling
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                
                if request.normalize:
                    embeddings = self._normalize_vector(embeddings.tolist())
                else:
                    embeddings = embeddings.tolist()
                
                embeddings_list.append(embeddings)
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            dimensions=len(embeddings_list[0]) if embeddings_list else 0,
            model_name=model_name,
            metadata={
                "method": request.method,
                "text_count": len(texts),
                "normalized": request.normalize
            }
        )
    
    async def _embed_langchain(self, texts: List[str], request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings using LangChain"""
        model_name = request.model_name or settings.openai_embedding_model
        
        embeddings_model = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=settings.openai_api_key
        )
        
        embeddings_list = await embeddings_model.aembed_documents(texts)
        
        # Normalize if requested
        if request.normalize:
            embeddings_list = [self._normalize_vector(emb) for emb in embeddings_list]
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            dimensions=len(embeddings_list[0]) if embeddings_list else 0,
            model_name=model_name,
            metadata={
                "method": request.method,
                "text_count": len(texts),
                "normalized": request.normalize,
                "framework": "langchain"
            }
        )
    
    async def _embed_llamaindex(self, texts: List[str], request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings using LlamaIndex"""
        model_name = request.model_name or settings.openai_embedding_model
        
        embed_model = OpenAIEmbedding(
            model=model_name,
            api_key=settings.openai_api_key
        )
        
        embeddings_list = []
        for text in texts:
            embedding = await embed_model.aget_text_embedding(text)
            embeddings_list.append(embedding)
        
        # Normalize if requested
        if request.normalize:
            embeddings_list = [self._normalize_vector(emb) for emb in embeddings_list]
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            dimensions=len(embeddings_list[0]) if embeddings_list else 0,
            model_name=model_name,
            metadata={
                "method": request.method,
                "text_count": len(texts),
                "normalized": request.normalize,
                "framework": "llamaindex"
            }
        )
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize a vector to unit length"""
        np_vector = np.array(vector)
        norm = np.linalg.norm(np_vector)
        if norm == 0:
            return vector
        return (np_vector / norm).tolist()
    
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    async def find_most_similar(self, query_embedding: List[float], 
                               candidate_embeddings: List[List[float]], 
                               top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar embeddings to query"""
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = await self.compute_similarity(query_embedding, candidate)
            similarities.append({
                "index": i,
                "similarity": similarity
            })
        
        # Sort by similarity in descending order
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities[:top_k]
