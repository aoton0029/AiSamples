from llama_index.core import Document
from llama_index.readers.file import PDFReader, DocxReader
from typing import List, Union
import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class MultiFormatLoader:
    def __init__(self):
        self.pdf_reader = PDFReader()
        self.docx_reader = DocxReader()
    
    def load_documents(self, file_paths: Union[str, List[str]]) -> List[Document]:
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        documents = []
        for file_path in file_paths:
            try:
                docs = self._load_single_file(file_path)
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} documents from {file_path}")
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        
        return documents
    
    def _load_single_file(self, file_path: str) -> List[Document]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.pdf_reader.load_data(file_path)
        elif file_ext == '.docx':
            return self.docx_reader.load_data(file_path)
        elif file_ext == '.txt':
            return self._load_text_file(file_path)
        elif file_ext == '.csv':
            return self._load_csv_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _load_text_file(self, file_path: str) -> List[Document]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [Document(text=content, metadata={"source": file_path})]
    
    def _load_csv_file(self, file_path: str) -> List[Document]:
        df = pd.read_csv(file_path)
        content = df.to_string(index=False)
        return [Document(text=content, metadata={"source": file_path, "type": "csv"})]
