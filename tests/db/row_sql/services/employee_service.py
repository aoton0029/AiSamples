from typing import List, Dict, Any, Optional
import logging

from ..core.sql_repository import SqlRepository
from ..core.database_enum import DatabaseConnection

logger = logging.getLogger(__name__)

class EmployeeService:
    """Employeeテーブル取得用サービス"""

    def __init__(self, db_connection: DatabaseConnection):
        self.repo = SqlRepository()
        self.db_connection = db_connection

    def get_employee(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """
        指定IDの従業員を取得する。
        戻り値: レコードが存在すればdict、存在しなければNone
        """
        sql = "SELECT * FROM employee WHERE id = :id"
        try:
            rows = self.repo.execute_query(sql, self.db_connection, params={"id": employee_id})
            return rows[0] if rows else None
        except Exception as e:
            logger.exception("Failed to get employee id=%s", employee_id)
            raise

    def list_employees(self) -> List[Dict[str, Any]]:
        """
        Employeeテーブルの一覧を取得する。limit/offsetは任意。
        """
        sql = "SELECT * FROM employee"

        try:
            return self.repo.execute_query(sql, self.db_connection)
        except Exception:
            logger.exception("Failed to list employees")
            raise
    
    def list_employees_dataframe(self):
        """
        pandas.DataFrameで一覧を取得したい場合に使用するメソッド
        """
        sql = "SELECT * FROM employee"

        try:
            return self.repo.execute_query_to_dataframe(sql, self.db_connection)
        except Exception:
            logger.exception("Failed to get employees DataFrame")
            raise