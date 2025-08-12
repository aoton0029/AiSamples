from typing import Optional, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user import User
from repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db_session: Session, db_type: Optional[str] = None):
        super().__init__(User, db_session, db_type)
    
    # ORM方式のメソッド
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db_session.query(User).filter(User.email == email).first()
    
    # 直接SQL方式のメソッド - DBタイプに依存する例
    def get_users_with_custom_query(self) -> List[Dict]:
        # DBタイプに応じて異なるクエリを実行する例
        query_name = "users.get_users_with_filter"
        
        # SQLiteでは特定の関数が使えないなどの理由で異なるクエリを使う例
        from database import DBType
        if self.db_type == DBType.SQLITE:
            # SQLite固有の日付フォーマット例
            params = {"date_format": "%Y-%m-%d"}
        elif self.db_type == DBType.SQLSERVER:
            # SQL Server固有のパラメータ例
            params = {"use_offset_fetch": True}
        else:
            # MariaDB/MySQLのパラメータ例
            params = {"use_limit": True}
        
        return self.execute_named_query(query_name, params)