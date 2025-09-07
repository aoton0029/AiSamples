from typing import List, Dict, Any, Optional
from .base_service import BaseService
from .user_repository import UserRepository

class UserService(BaseService):
    """Service for user-related business logic"""
    
    def get_user_by_id(self, database_name: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID with business logic"""
        with self.get_repository(UserRepository) as repo:
            return repo.get_user_by_id(database_name, user_id)
    
    def get_all_users(self, database_name: str) -> List[Dict[str, Any]]:
        """Get all users"""
        with self.get_repository(UserRepository) as repo:
            return repo.get_all_users(database_name)
    
    def create_user(self, database_name: str, username: str, email: str) -> bool:
        """Create user with validation"""
        if not username or not email:
            raise ValueError("Username and email are required")
        
        with self.get_repository(UserRepository) as repo:
            affected_rows = repo.create_user(database_name, username, email)
            return affected_rows > 0
    
    def update_user_email(self, database_name: str, user_id: int, email: str) -> bool:
        """Update user email with validation"""
        if not email or "@" not in email:
            raise ValueError("Valid email is required")
        
        with self.get_repository(UserRepository) as repo:
            affected_rows = repo.update_user_email(database_name, user_id, email)
            return affected_rows > 0
    
    def delete_user(self, database_name: str, user_id: int) -> bool:
        """Delete user"""
        with self.get_repository(UserRepository) as repo:
            affected_rows = repo.delete_user(database_name, user_id)
            return affected_rows > 0
