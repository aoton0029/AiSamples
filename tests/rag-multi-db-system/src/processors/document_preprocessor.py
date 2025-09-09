from typing import List, Dict, Any
import re

class DocumentPreprocessor:
    """Class for preprocessing documents before embedding generation and storage."""
    
    def normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace and converting to lowercase."""
        return ' '.join(text.split()).lower()
    
    def segment_language(self, text: str) -> List[str]:
        """Segment text into sentences or paragraphs."""
        # Simple segmentation based on periods, can be improved with NLP libraries
        return re.split(r'(?<=[.!?]) +', text)
    
    def chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """Chunk text into smaller pieces for embedding."""
        words = text.split()
        return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    def preprocess_document(self, document: str) -> Dict[str, Any]:
        """Preprocess the document and return structured data."""
        normalized_text = self.normalize_text(document)
        segments = self.segment_language(normalized_text)
        chunks = self.chunk_text(normalized_text)
        
        return {
            "normalized_text": normalized_text,
            "segments": segments,
            "chunks": chunks
        }