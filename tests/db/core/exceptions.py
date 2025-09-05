class DatabaseError(Exception):
    """データベース関連の基底例外"""
    pass


class ConnectionError(DatabaseError):
    """接続エラー"""
    pass


class QueryError(DatabaseError):
    """クエリ実行エラー"""
    pass


class TransactionError(DatabaseError):
    """トランザクションエラー"""
    pass


class ConfigurationError(DatabaseError):
    """設定エラー"""
    pass
