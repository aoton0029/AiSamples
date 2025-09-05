# LlamaIndex + Ollama Sample

A complete sample implementation showcasing LlamaIndex integration with Ollama for local LLM-powered document querying.

## Features

### Core Components
- **Index Management**: Document indexing with configurable chunking
- **Query Engine**: Advanced query processing with retrieval and synthesis
- **Retrieval**: Semantic search using vector embeddings
- **Synthesis**: Context-aware response generation

### Infrastructure Components
- **LLM Connectors**: Ollama integration for local LLM inference
- **Vector Stores**: ChromaDB for persistent vector storage
- **Document Loaders**: Support for PDF, DOCX, TXT, and CSV files

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install and run Ollama:
```bash
# Install Ollama from https://ollama.ai/
ollama pull llama2
```

3. Run the demo:
```bash
python main.py
```

## Usage

```python
from main import LlamaIndexOllamaSample

app = LlamaIndexOllamaSample()
app.setup()

# Load documents
app.load_documents(["path/to/document.pdf"])

# Query
response = app.query("What is this document about?")
print(response)
```

## Configuration

Modify `config.py` to adjust:
- Ollama model and endpoint
- Chunk size and overlap
- Vector store settings
- Query parameters

## Project Structure

```
├── config.py                 # Configuration settings
├── main.py                   # Main demo application
├── llm_connectors/           # LLM integration
├── vector_stores/            # Vector database abstraction
├── document_loaders/         # Document loading utilities
└── core/                     # Core RAG components
```
