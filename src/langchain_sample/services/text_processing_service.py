import tiktoken
import logging
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter
from llama_index.core.schema import TextNode, Document

logger = logging.getLogger(__name__)

class TextProcessingService:
    def __init__(self, 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 tokenizer_model: str = "gpt-3.5-turbo",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        self.embedding_model_name = embedding_model
        self.tokenizer_model = tokenizer_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.embedding_model = None
        self.tokenizer = None
        self.tiktoken_encoder = None
        self.sentence_splitter = None
        self.token_splitter = None
        
    async def initialize(self):
        """Initialize all text processing components"""
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            
            # Initialize tokenizers
            self.tiktoken_encoder = tiktoken.encoding_for_model(self.tokenizer_model)
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            logger.info(f"Loaded tokenizers")
            
            # Initialize text splitters
            self.sentence_splitter = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            
            self.token_splitter = TokenTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                tokenizer=self._tiktoken_tokenizer
            )
            
            logger.info("Text processing service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize text processing service: {e}")
            raise
    
    def _tiktoken_tokenizer(self, text: str) -> List[str]:
        """Tokenizer function for TokenTextSplitter"""
        tokens = self.tiktoken_encoder.encode(text)
        return [self.tiktoken_encoder.decode([token]) for token in tokens]
    
    async def tokenize(self, text: str, method: str = "tiktoken") -> Dict[str, Any]:
        """Tokenize text using specified method"""
        try:
            if method == "tiktoken":
                tokens = self.tiktoken_encoder.encode(text)
                decoded_tokens = [self.tiktoken_encoder.decode([token]) for token in tokens]
                return {
                    "tokens": tokens,
                    "decoded_tokens": decoded_tokens,
                    "token_count": len(tokens),
                    "method": "tiktoken"
                }
            
            elif method == "transformers":
                tokenized = self.tokenizer(text, return_tensors="pt", add_special_tokens=True)
                tokens = tokenized["input_ids"][0].tolist()
                decoded_tokens = self.tokenizer.convert_ids_to_tokens(tokens)
                return {
                    "tokens": tokens,
                    "decoded_tokens": decoded_tokens,
                    "token_count": len(tokens),
                    "method": "transformers"
                }
            
            else:
                raise ValueError(f"Unknown tokenization method: {method}")
                
        except Exception as e:
            logger.error(f"Tokenization error: {e}")
            raise
    
    async def chunk_text(self, text: str, method: str = "sentence") -> List[Dict[str, Any]]:
        """Chunk text using specified method"""
        try:
            if method == "sentence":
                nodes = self.sentence_splitter.get_nodes_from_documents([Document(text=text)])
            elif method == "token":
                nodes = self.token_splitter.get_nodes_from_documents([Document(text=text)])
            else:
                raise ValueError(f"Unknown chunking method: {method}")
            
            chunks = []
            for i, node in enumerate(nodes):
                chunk_info = {
                    "chunk_id": i,
                    "text": node.text,
                    "char_count": len(node.text),
                    "token_count": len(self.tiktoken_encoder.encode(node.text)),
                    "method": method,
                    "metadata": node.metadata
                }
                chunks.append(chunk_info)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Chunking error: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """Generate embeddings for a list of texts"""
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=True)
            
            # Convert to numpy for serialization
            embeddings_np = embeddings.cpu().numpy() if torch.is_tensor(embeddings) else embeddings
            
            return {
                "embeddings": embeddings_np.tolist(),
                "dimensions": embeddings_np.shape[1],
                "count": len(texts),
                "model": self.embedding_model_name
            }
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise
    
    async def process_document(self, text: str, doc_id: str) -> Dict[str, Any]:
        """Complete document processing pipeline"""
        try:
            # Tokenize
            tokenization_result = await self.tokenize(text)
            
            # Chunk
            chunks = await self.chunk_text(text, method="sentence")
            
            # Generate embeddings for chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings_result = await self.generate_embeddings(chunk_texts)
            
            # Combine chunk data with embeddings
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings_result["embeddings"][i]
                chunk["doc_id"] = doc_id
                processed_chunks.append(chunk)
            
            return {
                "doc_id": doc_id,
                "tokenization": tokenization_result,
                "chunks": processed_chunks,
                "total_chunks": len(processed_chunks),
                "embedding_dimensions": embeddings_result["dimensions"],
                "processing_summary": {
                    "original_length": len(text),
                    "total_tokens": tokenization_result["token_count"],
                    "chunks_created": len(processed_chunks),
                    "embedding_model": self.embedding_model_name
                }
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise
    
    async def similarity_search(self, query: str, embeddings_db: List[Dict], top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search using cosine similarity"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=True)
            query_embedding_np = query_embedding.cpu().numpy()[0]
            
            # Calculate similarities
            similarities = []
            for item in embeddings_db:
                item_embedding = np.array(item["embedding"])
                similarity = np.dot(query_embedding_np, item_embedding) / (
                    np.linalg.norm(query_embedding_np) * np.linalg.norm(item_embedding)
                )
                similarities.append({
                    "similarity": float(similarity),
                    "chunk": item
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            raise
