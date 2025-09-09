class SearchResult:
    """SearchResult model representing the structure of search results returned by the API."""
    
    def __init__(self, document_id: str, chunk_id: str, text: str, score: float):
        self.document_id = document_id
        self.chunk_id = chunk_id
        self.text = text
        self.score = score

    def to_dict(self) -> dict:
        """Convert the SearchResult instance to a dictionary."""
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": self.score
        }