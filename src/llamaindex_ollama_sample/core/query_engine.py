from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import ResponseSynthesizer
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class QueryEngine:
    def __init__(self, index: VectorStoreIndex, top_k: int = 3, similarity_threshold: float = 0.7):
        self.index = index
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self._query_engine = None
        self._setup_query_engine()
    
    def _setup_query_engine(self):
        try:
            # Configure retriever
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=self.top_k
            )
            
            # Configure response synthesizer
            response_synthesizer = ResponseSynthesizer.from_args(
                response_mode="compact"
            )
            
            # Create query engine
            self._query_engine = RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer
            )
            
            logger.info("Query engine setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup query engine: {e}")
            raise
    
    def query(self, question: str) -> str:
        try:
            if not self._query_engine:
                raise ValueError("Query engine not initialized")
            
            response = self._query_engine.query(question)
            logger.info(f"Query processed: {question}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return f"Error processing query: {str(e)}"
    
    def get_retriever(self):
        return VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.top_k
        )
