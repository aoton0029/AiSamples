import pytest
from src.api.routes.documents import upload_document, get_document
from src.models.document import Document
from unittest.mock import patch, MagicMock

@pytest.fixture
def sample_document():
    return {
        "document_id": "doc1",
        "content": "This is a sample document.",
        "metadata": {"author": "John Doe", "type": "text"}
    }

def test_upload_document(sample_document):
    with patch('src.services.document_service.DocumentService') as mock_service:
        mock_service.return_value.upload_document.return_value = sample_document
        response = upload_document(sample_document)
        
        assert response.status_code == 201
        assert response.json() == sample_document

def test_get_document(sample_document):
    with patch('src.services.document_service.DocumentService') as mock_service:
        mock_service.return_value.get_document.return_value = sample_document
        response = get_document("doc1")
        
        assert response.status_code == 200
        assert response.json() == sample_document

def test_upload_document_invalid_data():
    invalid_document = {
        "content": "This is a sample document without an ID."
    }
    
    with pytest.raises(ValueError):
        upload_document(invalid_document)

def test_get_nonexistent_document():
    with patch('src.services.document_service.DocumentService') as mock_service:
        mock_service.return_value.get_document.return_value = None
        response = get_document("nonexistent_doc")
        
        assert response.status_code == 404
        assert response.json() == {"error": "Document not found"}