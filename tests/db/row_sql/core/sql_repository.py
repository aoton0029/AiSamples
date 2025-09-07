from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Result, Engine
import logging

from .database_enum import DatabaseConnection
from .connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)

class SqlRepository:
    """生SQL実行用のリポジトリクラス"""
    
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
    
    def _get_engine(self, db_connection: DatabaseConnection) -> Engine:
        """エンジンを取得する内部メソッド"""
        return self.connection_manager.get_engine(db_connection)
    
    def _execute_with_connection(
        self, 
        sql: str, 
        db_connection: DatabaseConnection,
        params: Optional[Dict[str, Any]] = None,
        with_transaction: bool = False
    ) -> Result:
        """接続を使用してSQLを実行する共通メソッド"""
        engine = self._get_engine(db_connection)
        
        with engine.connect() as connection:
            if with_transaction:
                with connection.begin():
                    return connection.execute(text(sql), params or {})
            else:
                return connection.execute(text(sql), params or {})
    
    def _log_error(self, operation: str, db_connection: DatabaseConnection, error: Exception):
        """エラーログを出力する共通メソッド"""
        logger.error(f"{operation} failed for {db_connection.value}: {error}")
    
    def execute_query(
        self, 
        sql: str, 
        db_connection: DatabaseConnection,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """SELECT文を実行してdict形式のリストで結果を返す"""
        try:
            result: Result = self._execute_with_connection(sql, db_connection, params)
            # 結果をdict形式で取得
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self._log_error("Query execution", db_connection, e)
            raise
    
    def execute_query_to_dataframe(
        self, 
        sql: str, 
        db_connection: DatabaseConnection,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """SELECT文を実行してDataFrameで結果を返す"""
        engine = self._get_engine(db_connection)
        
        try:
            return pd.read_sql(text(sql), engine, params=params or {})
        except Exception as e:
            self._log_error("Query execution to DataFrame", db_connection, e)
            raise
    
    def execute_non_query(
        self, 
        sql: str, 
        db_connection: DatabaseConnection,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """INSERT/UPDATE/DELETE文を実行して影響行数を返す"""
        try:
            result: Result = self._execute_with_connection(sql, db_connection, params, with_transaction=True)
            return result.rowcount
                    
        except Exception as e:
            self._log_error("Non-query execution", db_connection, e)
            raise
    
    def execute_batch(
        self, 
        sql_statements: List[str], 
        db_connection: DatabaseConnection
    ) -> None:
        """複数のSQL文をバッチで実行"""
        engine = self._get_engine(db_connection)
        
        try:
            with engine.connect() as connection:
                with connection.begin():  # トランザクション管理
                    for sql in sql_statements:
                        connection.execute(text(sql))
                        
        except Exception as e:
            self._log_error("Batch execution", db_connection, e)
            raise
    
    def close_connections(self):
        """全ての接続を閉じる"""
        self.connection_manager.close_all_connections()
