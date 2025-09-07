from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    """Repository for user-related SQL operations"""
    
    def get_user_by_id(self, database_name: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        sql = f"""
        SELECT user_id, username, email, created_at
        FROM {database_name}.dbo.users
        WHERE user_id = :user_id
        """
        results = self.execute_query(sql, {"user_id": user_id})
        return results[0] if results else None
    
    def get_all_users(self, database_name: str) -> List[Dict[str, Any]]:
        """Get all users"""
        sql = f"""
        SELECT user_id, username, email, created_at
        FROM {database_name}.dbo.users
        ORDER BY created_at DESC
        """
        return self.execute_query(sql)
    
    def create_user(self, database_name: str, username: str, email: str) -> int:
        """Create new user and return affected rows"""
        sql = f"""
        INSERT INTO {database_name}.dbo.users (username, email, created_at)
        VALUES (:username, :email, GETDATE())
        """
        return self.execute_non_query(sql, {
            "username": username,
            "email": email
        })
    
    def update_user_email(self, database_name: str, user_id: int, email: str) -> int:
        """Update user email"""
        sql = f"""
        UPDATE {database_name}.dbo.users
        SET email = :email, updated_at = GETDATE()
        WHERE user_id = :user_id
        """
        return self.execute_non_query(sql, {
            "user_id": user_id,
            "email": email
        })
    
    def delete_user(self, database_name: str, user_id: int) -> int:
        """Delete user"""
        sql = f"""
        DELETE FROM {database_name}.dbo.users
        WHERE user_id = :user_id
        """
        return self.execute_non_query(sql, {"user_id": user_id})
