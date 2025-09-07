from abc import ABC, abstractmethod
from typing import Dict, Type
from sqlalchemy.orm import Session
from .repository import BaseRepository, IRepository
from .models import Base, User, Product
from .enums import DatabaseServer
from .connection import DatabaseManager


class IUnitOfWork(ABC):
    """ユニットオブワークインターフェース"""
    
    @abstractmethod
    def commit(self) -> None:
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        pass
    
    @abstractmethod
    def __enter__(self):
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class UnitOfWork(IUnitOfWork):
    """ユニットオブワーク実装"""
    
    def __init__(self, session: Session):
        self._session = session
        self._repositories: Dict[Type, IRepository] = {}
        
        # リポジトリの初期化
        self.users = self._get_repository(User)
        self.products = self._get_repository(Product)
    
    def _get_repository(self, model_class: Type[Base]) -> BaseRepository:
        """リポジトリを取得または作成"""
        if model_class not in self._repositories:
            self._repositories[model_class] = BaseRepository(self._session, model_class)
        return self._repositories[model_class]
    
    def commit(self) -> None:
        """変更をコミット"""
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
    
    def rollback(self) -> None:
        """変更をロールバック"""
        self._session.rollback()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self._session.close()


class UnitOfWorkFactory:
    """ユニットオブワークファクトリ"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
    
    def create(self, server: DatabaseServer) -> UnitOfWork:
        """指定されたサーバーのユニットオブワークを作成"""
        session = self._db_manager.get_session(server)
        return UnitOfWork(session)
