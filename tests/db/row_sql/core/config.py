import os
from typing import Dict, Any
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class ServerType(Enum):
    """データベース接続先を定義するEnum"""
    SQL001 = "SQL001"
    SRVDB02 = "SRVDB02"
    VRVSQL2022 = "VRVSQL2022"


class DatabaseConfig:
    """データベース接続設定を管理するクラス"""
    
    @staticmethod
    def get_connection_config() -> Dict[ServerType, Dict[str, Any]]:
        """各データベースの接続設定を取得"""
        return {
            ServerType.SQL001: {
                "server": os.getenv("SQL001_SERVER", "prod-server.example.com"),
                "username": os.getenv("SQL001_USER", "prod_user"),
                "password": os.getenv("SQL001_PASSWORD", "prod_password"),
                "port": int(os.getenv("SQL001_PORT", "1433")),
                "driver": "ODBC Driver 17 for SQL Server"
            },
            ServerType.SRVDB02: {
                "server": os.getenv("SRVDB02_SERVER", "staging-server.example.com"),
                "username": os.getenv("SRVDB02_USER", "staging_user"),
                "password": os.getenv("SRVDB02_PASSWORD", "staging_password"),
                "port": int(os.getenv("SRVDB02_PORT", "1433")),
                "driver": "ODBC Driver 17 for SQL Server"
            },
            ServerType.VRVSQL2022: {
                "server": os.getenv("VRVSQL2022_SERVER", "dev-server.example.com"),
                "username": os.getenv("VRVSQL2022_USER", "dev_user"),
                "password": os.getenv("VRVSQL2022_PASSWORD", "dev_password"),
                "port": int(os.getenv("VRVSQL2022_PORT", "1433")),
                "driver": "ODBC Driver 17 for SQL Server"
            }
        }
