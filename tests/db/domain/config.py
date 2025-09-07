import os
from dataclasses import dataclass
from typing import Dict, Optional
from .enums import DatabaseServer


@dataclass
class DatabaseConfig:
    """データベース接続設定"""
    server: str
    database: str
    username: str
    password: str
    port: int = 1433
    driver: str = "ODBC Driver 17 for SQL Server"
    trusted_connection: bool = False


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        self._configs: Dict[DatabaseServer, DatabaseConfig] = {}
        self._load_configs(config_file)
    
    def _load_configs(self, config_file: Optional[str] = None) -> None:
        """設定を読み込み"""
        # 環境変数から設定を読み込み
        for server in DatabaseServer:
            prefix = f"DB_{server.value.upper()}_"
            
            config = DatabaseConfig(
                server=os.getenv(f"{prefix}SERVER", "localhost"),
                database=os.getenv(f"{prefix}DATABASE", ""),
                username=os.getenv(f"{prefix}USERNAME", ""),
                password=os.getenv(f"{prefix}PASSWORD", ""),
                port=int(os.getenv(f"{prefix}PORT", "1433")),
                driver=os.getenv(f"{prefix}DRIVER", "ODBC Driver 17 for SQL Server"),
                trusted_connection=os.getenv(f"{prefix}TRUSTED_CONNECTION", "false").lower() == "true"
            )
            
            self._configs[server] = config
    
    def get_config(self, server: DatabaseServer) -> DatabaseConfig:
        """指定されたサーバーの設定を取得"""
        if server not in self._configs:
            raise ValueError(f"Configuration for {server.value} not found")
        return self._configs[server]
    
    def set_config(self, server: DatabaseServer, config: DatabaseConfig) -> None:
        """設定を手動で設定"""
        self._configs[server] = config
