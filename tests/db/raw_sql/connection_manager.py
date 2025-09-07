from typing import Dict
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from .config import Config
from .sql_server_type import SqlServerType

class ConnectionManager:
    """Manages database connections for multiple SQL Servers"""
    
    def __init__(self, config: Config):
        self.config = config
        self._engines: Dict[SqlServerType, Engine] = {}
        self._session_makers: Dict[SqlServerType, sessionmaker] = {}
        self._init_engines()
    
    def _init_engines(self):
        """Initialize engines for all configured SQL Servers"""
        for server_type, db_config in self.config.databases.items():
            if db_config.server:  # Only create engine if server is configured
                engine = create_engine(
                    db_config.get_connection_string(),
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                self._engines[server_type] = engine
                self._session_makers[server_type] = sessionmaker(bind=engine)
    
    def get_engine(self, server_type: SqlServerType) -> Engine:
        """Get engine for specific SQL Server"""
        return self._engines.get(server_type)
    
    def get_session(self, server_type: SqlServerType) -> Session:
        """Get new session for specific SQL Server"""
        session_maker = self._session_makers.get(server_type)
        if session_maker:
            return session_maker()
        raise ValueError(f"No session maker found for {server_type}")
