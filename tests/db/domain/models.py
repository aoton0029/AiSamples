from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func


class BaseModel:
    """ベースモデルクラス"""
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


Base = declarative_base(cls=BaseModel)


# サンプルモデル
class User(Base):
    """ユーザーモデル例"""
    __tablename__ = 'users'
    
    # 追加フィールドをここに定義
    pass


class Product(Base):
    """商品モデル例"""
    __tablename__ = 'products'
    
    # 追加フィールドをここに定義
    pass
