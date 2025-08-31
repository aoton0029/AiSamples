import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.settings import DATABASE_URL
from src.database.connections import get_db
from src.services.llama_service import LlamaService
from src.services.mcp_service import McpService

@pytest.fixture(scope='module')
def db_session():
    """Create a new database session for a test."""
    engine = create_engine(DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope='module')
def llama_service(db_session):
    """Fixture for LlamaService."""
    return LlamaService(db_session)

@pytest.fixture(scope='module')
def mcp_service(db_session):
    """Fixture for McpService."""
    return McpService(db_session)

def test_llama_service_functionality(llama_service):
    """Test LlamaService functionality."""
    # Add your test logic here
    assert llama_service is not None

def test_mcp_service_functionality(mcp_service):
    """Test McpService functionality."""
    # Add your test logic here
    assert mcp_service is not None

def test_database_connection(db_session):
    """Test database connection."""
    assert db_session is not None
    result = db_session.execute("SELECT 1")
    assert result.scalar() == 1