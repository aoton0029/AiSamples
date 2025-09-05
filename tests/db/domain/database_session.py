from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Optional, TypeVar, Generic, List, Type
from contextlib import contextmanager
import logging

from ..config.database_config import DatabaseConfig
from ..core.exceptions import ConnectionError, TransactionError
from .base_entity import Base, BaseEntity

T = TypeVar('T', bound=BaseEntity)


class DatabaseSession:
    """データベースごとのセッション管理クラス（ドメインクラス用）"""
    
    def __init__(self, config: DatabaseConfig, database_name: str):
        self.config = config
        self.database_name = database_name
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> None:
        """データベースセッションを初期化"""
        try:
            # データベース固有の接続文字列を作成
            connection_string = self.config.get_connection_string()
            if self.database_name != self.config.database:
                connection_string = connection_string.replace(
                    f"/{self.config.database}",
                    f"/{self.database_name}"
                )
            
            self._engine = create_engine(
                connection_string,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self._session_factory = sessionmaker(bind=self._engine)
            
            self.logger.info(f"Initialized session for database: {self.database_name}")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize session for {self.database_name}: {str(e)}")
    
    def create_tables(self) -> None:
        """テーブルを作成"""
        if not self._engine:
            raise ConnectionError("Session not initialized")
        Base.metadata.create_all(self._engine)
    
    def drop_tables(self) -> None:
        """テーブルを削除"""
        if not self._engine:
            raise ConnectionError("Session not initialized")
        Base.metadata.drop_all(self._engine)
    
    @contextmanager
    def get_session(self):
        """セッションのコンテキストマネージャ"""
        if not self._session_factory:
            raise ConnectionError("Session not initialized")
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise TransactionError(f"Transaction failed: {str(e)}")
        finally:
            session.close()
    
    def close(self) -> None:
        """セッションを閉じる"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self.logger.info(f"Closed session for database: {self.database_name}")


class Repository(Generic[T]):
    """汎用リポジトリクラス"""
    
    def __init__(self, entity_class: Type[T], db_session: DatabaseSession):
        self.entity_class = entity_class
        self.db_session = db_session
    
    def create(self, entity: T) -> T:
        """エンティティを作成"""
        with self.db_session.get_session() as session:
            session.add(entity)
            session.flush()
            session.refresh(entity)
            return entity
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """IDでエンティティを取得"""
        with self.db_session.get_session() as session:
            return session.query(self.entity_class).filter(
                self.entity_class.id == entity_id
            ).first()
    
    def get_all(self) -> List[T]:
        """全てのエンティティを取得"""
        with self.db_session.get_session() as session:
            return session.query(self.entity_class).all()
    
    def update(self, entity: T) -> T:
        """エンティティを更新"""
        with self.db_session.get_session() as session:
            session.merge(entity)
            return entity
    
    def delete(self, entity_id: int) -> bool:
        """エンティティを削除"""
        with self.db_session.get_session() as session:
            entity = session.query(self.entity_class).filter(
                self.entity_class.id == entity_id
            ).first()
            if entity:
                session.delete(entity)
                return True
            return False
    
    def delete_entity(self, entity: T) -> None:
        """エンティティオブジェクトを削除"""
        with self.db_session.get_session() as session:
            session.delete(entity)
