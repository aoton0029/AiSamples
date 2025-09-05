from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Dict, Any, List, Optional, Union
import logging
from contextlib import contextmanager

from ..config.database_config import DatabaseConfig, DatabaseConfigManager
from ..core.exceptions import ConnectionError, QueryError, TransactionError


class SQLServerManager:
    """SQLServerごとのセッション管理クラス（生SQL用）"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> None:
        """データベースに接続"""
        try:
            self._engine = create_engine(
                self.config.get_connection_string(),
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self._session_factory = sessionmaker(bind=self._engine)
            # 接続テスト
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info(f"Connected to {self.config.server}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.config.server}: {str(e)}")
    
    def disconnect(self) -> None:
        """データベースから切断"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self.logger.info(f"Disconnected from {self.config.server}")
    
    @contextmanager
    def get_session(self):
        """セッションのコンテキストマネージャ"""
        if not self._session_factory:
            raise ConnectionError("Not connected to database")
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise QueryError(f"Query execution failed: {str(e)}")
        finally:
            session.close()
    
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """SELECT文を実行"""
        with self.get_session() as session:
            try:
                result = session.execute(text(sql), params or {})
                return [dict(row._mapping) for row in result]
            except Exception as e:
                raise QueryError(f"Query execution failed: {str(e)}")
    
    def execute_non_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        """INSERT/UPDATE/DELETE文を実行"""
        with self.get_session() as session:
            try:
                result = session.execute(text(sql), params or {})
                return result.rowcount
            except Exception as e:
                raise QueryError(f"Non-query execution failed: {str(e)}")
    
    def execute_scalar(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """スカラー値を取得"""
        with self.get_session() as session:
            try:
                result = session.execute(text(sql), params or {})
                return result.scalar()
            except Exception as e:
                raise QueryError(f"Scalar query execution failed: {str(e)}")


class SQLServerManagerFactory:
    """SQLServerManagerのファクトリクラス"""
    
    def __init__(self, config_manager: DatabaseConfigManager):
        self.config_manager = config_manager
        self._managers: Dict[str, SQLServerManager] = {}
    
    def get_manager(self, server_name: str) -> SQLServerManager:
        """SQLServerManagerを取得"""
        if server_name not in self._managers:
            config = self.config_manager.get_config(server_name)
            manager = SQLServerManager(config)
            manager.connect()
            self._managers[server_name] = manager
        return self._managers[server_name]
    
    def close_all(self) -> None:
        """全ての接続を閉じる"""
        for manager in self._managers.values():
            manager.disconnect()
        self._managers.clear()
