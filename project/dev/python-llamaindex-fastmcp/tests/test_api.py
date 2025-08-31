import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_query_endpoint():
    query = {"input": "test query"}
    response = client.post("/query", json=query)
    assert response.status_code == 200
    assert "result" in response.json()  # Adjust based on actual response structure

def test_invalid_query():
    query = {"input": ""}
    response = client.post("/query", json=query)
    assert response.status_code == 400  # Assuming 400 for bad request
    assert "detail" in response.json()  # Adjust based on actual response structure