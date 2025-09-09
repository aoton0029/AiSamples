from typing import Any, Dict

class Document:
    """Document model representing the structure of documents in the document database."""
    
    def __init__(self, document_id: str, content: str, metadata: Dict[str, Any] = None):
        self.document_id = document_id
        self.content = content
        self.metadata = metadata if metadata is not None else {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Document instance to a dictionary."""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata
        }