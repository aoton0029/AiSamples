from typing import Dict, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from .config import ConfigManager, DatabaseConfig
from .enums import DatabaseServer


class DatabaseManager:
    """データベース接続管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        self._config_manager = config_manager
        self._engines: Dict[DatabaseServer, Engine] = {}
        self._session_makers: Dict[DatabaseServer, sessionmaker] = {}
    
    def _create_connection_string(self, config: DatabaseConfig) -> str:
        """接続文字列を作成"""
        if config.trusted_connection:
            return (
                f"mssql+pymssql://@{config.server}:{config.port}/"
                f"{config.database}?trusted_connection=yes"
            )
        else:
            return (
                f"mssql+pymssql://{config.username}:{config.password}@"
                f"{config.server}:{config.port}/{config.database}"
            )
    
    def get_engine(self, server: DatabaseServer) -> Engine:
        """指定されたサーバーのエンジンを取得"""
        if server not in self._engines:
            config = self._config_manager.get_config(server)
            connection_string = self._create_connection_string(config)
            
            self._engines[server] = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
        
        return self._engines[server]
    
    def get_session_maker(self, server: DatabaseServer) -> sessionmaker:
        """指定されたサーバーのセッションメーカーを取得"""
        if server not in self._session_makers:
            engine = self.get_engine(server)
            self._session_makers[server] = sessionmaker(bind=engine)
        
        return self._session_makers[server]
    
    def get_session(self, server: DatabaseServer) -> Session:
        """指定されたサーバーのセッションを取得"""
        session_maker = self.get_session_maker(server)
        return session_maker()
    
    def close_all(self) -> None:
        """全ての接続を閉じる"""
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear()
        self._session_makers.clear()
