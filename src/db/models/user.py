from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from database import db_manager

Base = db_manager.Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # SQLiteではTextとして保存し、他のDBではJSONタイプを使う例
    @property
    def profile_data_column(self):
        from sqlalchemy import JSON, Text
        from database import DBType
        
        # 現在のエンジンが何かを特定する必要がある場合の例
        # 実際の実装では異なるモデル定義や動的なカラム型定義が必要な場合もある
        if db_manager.default_db == DBType.SQLITE:
            return Column("profile_data", Text)
        else:
            return Column("profile_data", JSON)