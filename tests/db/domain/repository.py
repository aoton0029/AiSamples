from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any
from sqlalchemy.orm import Session
from .models import Base

T = TypeVar('T', bound=Base)


class IRepository(ABC, Generic[T]):
    """リポジトリインターフェース"""
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        pass
    
    @abstractmethod
    def add(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class BaseRepository(IRepository[T]):
    """ベースリポジトリクラス"""
    
    def __init__(self, session: Session, model_class: type[T]):
        self._session = session
        self._model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        return self._session.query(self._model_class).filter(
            self._model_class.id == id
        ).first()
    
    def get_all(self) -> List[T]:
        return self._session.query(self._model_class).all()
    
    def add(self, entity: T) -> T:
        self._session.add(entity)
        return entity
    
    def update(self, entity: T) -> T:
        self._session.merge(entity)
        return entity
    
    def delete(self, id: int) -> bool:
        entity = self.get_by_id(id)
        if entity:
            self._session.delete(entity)
            return True
        return False
    
    def find_by(self, **kwargs) -> List[T]:
        """条件検索"""
        query = self._session.query(self._model_class)
        for key, value in kwargs.items():
            if hasattr(self._model_class, key):
                query = query.filter(getattr(self._model_class, key) == value)
        return query.all()
