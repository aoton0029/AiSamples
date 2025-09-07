from enum import Enum


class DatabaseServer(Enum):
    """データベースサーバー接続先定義"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ANALYTICS = "analytics"
    REPORTING = "reporting"
