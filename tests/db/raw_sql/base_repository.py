from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

class BaseRepository(ABC):
    """Base repository class for SQL management"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def execute_query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dictionaries"""
        try:
            result = self.session.execute(text(sql), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            self.session.rollback()
            raise e
    
    def execute_scalar(self, sql: str, params: Dict[str, Any] = None) -> Any:
        """Execute query and return single scalar value"""
        try:
            result = self.session.execute(text(sql), params or {})
            return result.scalar()
        except Exception as e:
            self.session.rollback()
            raise e
    
    def execute_non_query(self, sql: str, params: Dict[str, Any] = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        try:
            result = self.session.execute(text(sql), params or {})
            self.session.commit()
            return result.rowcount
        except Exception as e:
            self.session.rollback()
            raise e
    
    def execute_batch(self, sql: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute batch operation"""
        try:
            total_affected = 0
            for params in params_list:
                result = self.session.execute(text(sql), params)
                total_affected += result.rowcount
            self.session.commit()
            return total_affected
        except Exception as e:
            self.session.rollback()
            raise e
