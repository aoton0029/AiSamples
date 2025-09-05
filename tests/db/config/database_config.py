from dataclasses import dataclass
from typing import Dict, Optional
import os


@dataclass
class DatabaseConfig:
    """データベース接続設定"""
    server: str
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    driver: str = "ODBC Driver 17 for SQL Server"
    port: int = 1433
    trusted_connection: bool = False
    
    def get_connection_string(self) -> str:
        """接続文字列を生成"""
        if self.trusted_connection:
            return (f"mssql+pymssql://@{self.server}:{self.port}/{self.database}"
                   f"?trusted_connection=yes")
        else:
            return (f"mssql+pymssql://{self.username}:{self.password}"
                   f"@{self.server}:{self.port}/{self.database}")


class DatabaseConfigManager:
    """データベース設定管理クラス"""
    
    def __init__(self):
        self._configs: Dict[str, DatabaseConfig] = {}
    
    def add_config(self, name: str, config: DatabaseConfig) -> None:
        """設定を追加"""
        self._configs[name] = config
    
    def get_config(self, name: str) -> DatabaseConfig:
        """設定を取得"""
        if name not in self._configs:
            raise ValueError(f"Database config '{name}' not found")
        return self._configs[name]
    
    def remove_config(self, name: str) -> None:
        """設定を削除"""
        if name in self._configs:
            del self._configs[name]
    
    @classmethod
    def from_env(cls, prefix: str = "DB") -> "DatabaseConfigManager":
        """環境変数から設定を読み込み"""
        manager = cls()
        # 環境変数からの読み込み実装
        return manager
