from typing import Generic, TypeVar, Type, List, Optional, Any, Dict, Union
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import db_manager
from sql_loader import sql_loader

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db_session: Session, db_type: Optional[str] = None):
        self.model = model
        self.db_session = db_session
        self.db_type = db_type or db_manager.default_db
    
    # 標準のORMメソッド
    def get_by_id(self, id: Any) -> Optional[T]:
        return self.db_session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self) -> List[T]:
        return self.db_session.query(self.model).all()
    
    def create(self, obj_in: Dict[str, Any]) -> T:
        try:
            obj = self.model(**obj_in)
            self.db_session.add(obj)
            self.db_session.commit()
            self.db_session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
    
    def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[T]:
        obj = self.get_by_id(id)
        if obj:
            for key, value in obj_in.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.db_session.commit()
            self.db_session.refresh(obj)
        return obj
    
    def delete(self, id: Any) -> bool:
        obj = self.get_by_id(id)
        if obj:
            self.db_session.delete(obj)
            self.db_session.commit()
            return True
        return False
    
    # 直接SQLを実行するメソッド
    def execute_sql(self, sql: str, params: Dict = None, is_select: bool = True) -> Union[List[Dict], int]:
        """セッション内で直接SQLを実行"""
        if isinstance(sql, str):
            sql = text(sql)
        
        if is_select:
            result = self.db_session.execute(sql, params or {})
            return [dict(row) for row in result]
        else:
            result = self.db_session.execute(sql, params or {})
            self.db_session.commit()
            return result.rowcount
    
    def execute_named_query(self, query_name: str, params: Dict = None, is_select: bool = True) -> Union[List[Dict], int]:
        """事前に定義された名前付きクエリを実行"""
        sql = sql_loader.get_query(query_name, self.db_type)
        if not sql:
            raise ValueError(f"Named query '{query_name}' not found for DB type '{self.db_type}'")
        
        return self.execute_sql(sql, params, is_select)