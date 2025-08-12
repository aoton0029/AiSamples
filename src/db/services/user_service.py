from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from repositories.user_repository import UserRepository
from models.user import User
from database import DBType

class UserService:
    def __init__(self, db_session: Session, db_type: Optional[str] = None):
        self.db_type = db_type
        self.repository = UserRepository(db_session, db_type)
    
    # ORM使用メソッド
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.repository.get_by_id(user_id)
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        # DBタイプに応じた前処理の例
        if self.db_type == DBType.SQLSERVER:
            # SQL Serverでは文字列長制限に注意が必要な場合など
            if 'username' in user_data and len(user_data['username']) > 50:
                user_data['username'] = user_data['username'][:50]
                
        return self.repository.create(user_data)
    
    # Raw SQL使用メソッド
    def get_users_custom(self) -> List[Dict]:
        # 異なるDBタイプに対応したリポジトリメソッドを呼び出す
        return self.repository.get_users_with_custom_query()