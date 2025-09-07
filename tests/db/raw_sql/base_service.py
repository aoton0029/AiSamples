from contextlib import contextmanager
from typing import TypeVar, Type
from sqlalchemy.orm import Session
from .connection_manager import ConnectionManager
from .sql_server_type import SqlServerType
from .base_repository import BaseRepository

T = TypeVar('T', bound=BaseRepository)

class BaseService:
    """Base service class for session management"""
    
    def __init__(self, connection_manager: ConnectionManager, server_type: SqlServerType):
        self.connection_manager = connection_manager
        self.server_type = server_type
    
    @contextmanager
    def get_repository(self, repository_class: Type[T]) -> T:
        """Context manager to get repository with session management"""
        session = self.connection_manager.get_session(self.server_type)
        try:
            repository = repository_class(session)
            yield repository
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for direct session access"""
        session = self.connection_manager.get_session(self.server_type)
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
