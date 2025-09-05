import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
import os
import logging

logger = logging.getLogger(__name__)

class ChromaStore:
    def __init__(self, persist_dir: str = "./storage"):
        self.persist_dir = persist_dir
        self._client = None
        self._collection = None
        self._vector_store = None
    
    def get_client(self):
        if self._client is None:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client
    
    def get_collection(self, collection_name: str = "default"):
        if self._collection is None:
            client = self.get_client()
            self._collection = client.get_or_create_collection(collection_name)
        return self._collection
    
    def get_vector_store(self, collection_name: str = "default") -> ChromaVectorStore:
        if self._vector_store is None:
            collection = self.get_collection(collection_name)
            self._vector_store = ChromaVectorStore(chroma_collection=collection)
        return self._vector_store
    
    def get_storage_context(self, collection_name: str = "default") -> StorageContext:
        vector_store = self.get_vector_store(collection_name)
        return StorageContext.from_defaults(vector_store=vector_store)
    
    def clear_collection(self, collection_name: str = "default"):
        try:
            client = self.get_client()
            client.delete_collection(collection_name)
            self._collection = None
            self._vector_store = None
            logger.info(f"Cleared collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear collection {collection_name}: {e}")
