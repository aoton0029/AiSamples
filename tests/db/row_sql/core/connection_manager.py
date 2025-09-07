from typing import Dict, Optional
from urllib.parse import quote_plus
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool
import logging

from .config import DatabaseConfig, ServerType

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """データベース接続を管理するクラス"""
    
    def __init__(self):
        self._engines: Dict[ServerType, Engine] = {}
        self._config = DatabaseConfig.get_connection_config()
    
    def get_engine(self, db_connection: ServerType) -> Engine:
        """指定されたデータベース接続のEngineを取得"""
        if db_connection not in self._engines:
            self._engines[db_connection] = self._create_engine(db_connection)
        return self._engines[db_connection]
    
    def _create_engine(self, db_connection: ServerType) -> Engine:
        """SQLAlchemy Engineを作成"""
        config = self._config[db_connection]
        
        # pymssql用の接続文字列を構築
        connection_string = (
            f"mssql+pymssql://{config['username']}:{quote_plus(config['password'])}"
            f"@{config['server']}:{config['port']}/{config['database']}"
        )
        
        # Engineを作成（接続プール設定も含む）
        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False  # 本番環境ではFalseに設定
        )
        
        logger.info(f"Created engine for {db_connection.value}")
        return engine
    
    def close_all_connections(self):
        """全ての接続を閉じる"""
        for db_connection, engine in self._engines.items():
            engine.dispose()
            logger.info(f"Closed connection for {db_connection.value}")
        self._engines.clear()
