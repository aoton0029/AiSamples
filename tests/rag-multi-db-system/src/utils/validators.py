def is_valid_document_id(document_id: str) -> bool:
    """Validate the document ID format."""
    return isinstance(document_id, str) and len(document_id) > 0

def is_valid_metadata(metadata: dict) -> bool:
    """Validate the metadata structure."""
    return isinstance(metadata, dict)

def is_valid_embedding(embedding: list) -> bool:
    """Validate the embedding vector."""
    return isinstance(embedding, list) and all(isinstance(i, (int, float)) for i in embedding)

def is_valid_query(query: dict) -> bool:
    """Validate the search query structure."""
    return isinstance(query, dict)

def is_valid_entity(entity: dict) -> bool:
    """Validate the entity structure."""
    return isinstance(entity, dict) and 'entity_id' in entity and 'properties' in entity

def is_valid_document_content(content: str) -> bool:
    """Validate the document content."""
    return isinstance(content, str) and len(content) > 0