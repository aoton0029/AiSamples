"""
SQLServer通信用汎用ライブラリ

生SQL用: SQLServerごとにセッション作成（データベースアーキテクチャ）
ドメインクラス用: データベースごとにセッション作成（ドメインアーキテクチャ）
"""

from .config.database_config import DatabaseConfig, DatabaseConfigManager
from .raw_sql.sql_server_manager import SQLServerManager, SQLServerManagerFactory
from .domain.database_manager import DatabaseManager
from .domain.database_session import DatabaseSession, Repository
from .domain.base_entity import BaseEntity, Base
from .core.exceptions import (
    DatabaseError,
    ConnectionError,
    QueryError,
    TransactionError,
    ConfigurationError
)

__all__ = [
    # Config
    'DatabaseConfig',
    'DatabaseConfigManager',
    # Raw SQL
    'SQLServerManager',
    'SQLServerManagerFactory',
    # Domain
    'DatabaseManager',
    'DatabaseSession',
    'Repository',
    'BaseEntity',
    'Base',
    # Exceptions
    'DatabaseError',
    'ConnectionError',
    'QueryError',
    'TransactionError',
    'ConfigurationError',
]

__version__ = '1.0.0'
