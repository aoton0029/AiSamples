import logging
import os
from pathlib import Path

from config import config
from llm_connectors import OllamaConnector
from vector_stores import ChromaStore
from document_loaders import MultiFormatLoader
from core import IndexManager, QueryEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LlamaIndexOllamaSample:
    def __init__(self):
        self.ollama_connector = OllamaConnector(
            base_url=config.ollama_base_url,
            model=config.ollama_model
        )
        self.vector_store = ChromaStore(config.persist_dir)
        self.document_loader = MultiFormatLoader()
        self.index_manager = None
        self.query_engine = None
    
    def setup(self):
        # Check if Ollama model is available
        if not self.ollama_connector.is_model_available():
            logger.warning(f"Model {config.ollama_model} not found. Please ensure Ollama is running and the model is installed.")
            return False
        
        # Initialize LLM and embedding model
        llm = self.ollama_connector.get_llm()
        embed_model = self.ollama_connector.get_embedding()
        storage_context = self.vector_store.get_storage_context()
        
        # Setup index manager
        self.index_manager = IndexManager(
            llm=llm,
            embed_model=embed_model,
            storage_context=storage_context,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        
        logger.info("Setup completed successfully")
        return True
    
    def load_documents(self, file_paths):
        documents = self.document_loader.load_documents(file_paths)
        if not documents:
            logger.error("No documents loaded")
            return False
        
        # Create index
        index = self.index_manager.create_index(documents)
        
        # Setup query engine
        self.query_engine = QueryEngine(
            index=index,
            top_k=config.top_k,
            similarity_threshold=config.similarity_threshold
        )
        
        return True
    
    def query(self, question: str) -> str:
        if not self.query_engine:
            return "No documents loaded. Please load documents first."
        
        return self.query_engine.query(question)
    
    def run_demo(self):
        print("🦙 LlamaIndex + Ollama Sample")
        print("=" * 40)
        
        if not self.setup():
            print("❌ Setup failed. Please check Ollama installation and model availability.")
            return
        
        # Demo with sample text
        sample_text = """
        LlamaIndex is a data framework for your LLM application.
        It helps you index and query your data using large language models.
        The framework provides tools for data ingestion, indexing, and querying.
        """
        
        from llama_index.core import Document
        documents = [Document(text=sample_text)]
        
        # Create index and setup query engine
        index = self.index_manager.create_index(documents)
        self.query_engine = QueryEngine(index)
        
        # Interactive query loop
        print("\n✅ System ready! Ask questions about your documents.")
        print("Type 'quit' to exit.\n")
        
        while True:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            print("\n🤔 Thinking...")
            response = self.query(question)
            print(f"📝 Answer: {response}\n")
            print("-" * 40)

if __name__ == "__main__":
    app = LlamaIndexOllamaSample()
    app.run_demo()
        logger.info("Knowledge graph index created with Neo4j")
        return kg_index
    
    def perform_search_and_query(self, vector_index, kg_index):
        """Perform various search and query operations"""
        
        # Vector similarity search
        logger.info("=== Vector Similarity Search ===")
        vector_query_engine = vector_index.as_query_engine(
            similarity_top_k=3,
            response_mode="compact"
        )
        
        query = "What is artificial intelligence?"
        response = vector_query_engine.query(query)
        logger.info(f"Query: {query}")
        logger.info(f"Response: {response}")
        
        # Knowledge graph query
        logger.info("\n=== Knowledge Graph Query ===")
        kg_query_engine = kg_index.as_query_engine(
            include_text=True,
            response_mode="tree_summarize"
        )
        
        kg_query = "Explain the relationship between AI and machine learning"
        kg_response = kg_query_engine.query(kg_query)
        logger.info(f"KG Query: {kg_query}")
        logger.info(f"KG Response: {kg_response}")
        
        # Retrieval with metadata filtering
        logger.info("\n=== Metadata Filtered Search ===")
        retriever = vector_index.as_retriever(
            similarity_top_k=2,
            filters={"language": "japanese"}
        )
        
        nodes = retriever.retrieve("ベクトルデータベースについて教えて")
        for i, node in enumerate(nodes):
            logger.info(f"Retrieved Node {i+1}: {node.text[:100]}...")
    
    def demonstrate_embeddings(self):
        """Demonstrate embedding generation"""
        logger.info("=== Embedding Generation ===")
        
        texts = [
            "人工知能は未来の技術です",
            "Machine learning is a subset of AI",
            "ベクトル検索は効率的です"
        ]
        
        for text in texts:
            embedding = self.embedding_model.get_text_embedding(text)
            logger.info(f"Text: {text}")
            logger.info(f"Embedding dimension: {len(embedding)}")
            logger.info(f"First 5 values: {embedding[:5]}")
    
    def store_metadata_in_redis(self):
        """Store metadata in Redis key-value store"""
        if self.stores["kv_store"] is None:
            logger.error("Redis KV store not available")
            return
        
        logger.info("=== Redis Key-Value Operations ===")
        
        # Store some metadata
        metadata = {
            "last_indexed": "2024-01-15",
            "total_documents": "4",
            "index_version": "1.0"
        }
        
        for key, value in metadata.items():
            self.stores["kv_store"].put(key, value)
            logger.info(f"Stored: {key} = {value}")
        
        # Retrieve metadata
        for key in metadata.keys():
            retrieved_value = self.stores["kv_store"].get(key)
            logger.info(f"Retrieved: {key} = {retrieved_value}")
    
    def run_complete_demo(self):
        """Run complete demonstration of all features"""
        logger.info("Starting LlamaIndex Ollama Sample Demo")
        
        # Create and process documents
        documents = self.create_sample_documents()
        nodes = self.tokenize_and_split_documents(documents)
        
        # Create indexes
        vector_index = self.create_vector_index(documents)
        kg_index = self.create_knowledge_graph_index(documents)
        
        # Perform searches and queries
        self.perform_search_and_query(vector_index, kg_index)
        
        # Demonstrate embeddings
        self.demonstrate_embeddings()
        
        # Store metadata in Redis
        self.store_metadata_in_redis()
        
        logger.info("Demo completed successfully!")

def main():
    try:
        sample = LlamaIndexOllamaSample()
        sample.run_complete_demo()
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        raise

if __name__ == "__main__":
    main()
