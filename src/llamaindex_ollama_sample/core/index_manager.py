from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class IndexManager:
    def __init__(self, llm, embed_model, storage_context, chunk_size: int = 512, chunk_overlap: int = 50):
        Settings.llm = llm
        Settings.embed_model = embed_model
        
        self.storage_context = storage_context
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self._index = None
    
    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        try:
            nodes = self.node_parser.get_nodes_from_documents(documents)
            logger.info(f"Created {len(nodes)} nodes from {len(documents)} documents")
            
            self._index = VectorStoreIndex(
                nodes,
                storage_context=self.storage_context
            )
            logger.info("Index created successfully")
            return self._index
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise
    
    def load_index(self) -> Optional[VectorStoreIndex]:
        try:
            self._index = VectorStoreIndex.from_vector_store(
                self.storage_context.vector_store
            )
            logger.info("Index loaded successfully")
            return self._index
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return None
    
    def get_index(self) -> Optional[VectorStoreIndex]:
        return self._index
    
    def persist_index(self):
        if self._index:
            self._index.storage_context.persist()
            logger.info("Index persisted successfully")
