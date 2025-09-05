from typing import Dict, Type, TypeVar
from ..config.database_config import DatabaseConfig, DatabaseConfigManager
from .database_session import DatabaseSession, Repository, BaseEntity
from ..core.exceptions import ConfigurationError

T = TypeVar('T', bound=BaseEntity)


class DatabaseManager:
    """データベース管理クラス（ドメインアーキテクチャ用）"""
    
    def __init__(self, config_manager: DatabaseConfigManager):
        self.config_manager = config_manager
        self._sessions: Dict[str, DatabaseSession] = {}
        self._repositories: Dict[str, Repository] = {}
    
    def add_database(self, server_name: str, database_name: str) -> DatabaseSession:
        """データベースセッションを追加"""
        config = self.config_manager.get_config(server_name)
        session_key = f"{server_name}_{database_name}"
        
        if session_key not in self._sessions:
            session = DatabaseSession(config, database_name)
            session.initialize()
            self._sessions[session_key] = session
        
        return self._sessions[session_key]
    
    def get_session(self, server_name: str, database_name: str) -> DatabaseSession:
        """データベースセッションを取得"""
        session_key = f"{server_name}_{database_name}"
        if session_key not in self._sessions:
            return self.add_database(server_name, database_name)
        return self._sessions[session_key]
    
    def get_repository(self, entity_class: Type[T], server_name: str, database_name: str) -> Repository[T]:
        """リポジトリを取得"""
        repo_key = f"{entity_class.__name__}_{server_name}_{database_name}"
        
        if repo_key not in self._repositories:
            session = self.get_session(server_name, database_name)
            repository = Repository(entity_class, session)
            self._repositories[repo_key] = repository
        
        return self._repositories[repo_key]
    
    def create_tables(self, server_name: str, database_name: str) -> None:
        """テーブルを作成"""
        session = self.get_session(server_name, database_name)
        session.create_tables()
    
    def close_all(self) -> None:
        """全てのセッションを閉じる"""
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
        self._repositories.clear()
