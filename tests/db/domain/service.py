from typing import List, Optional
from .unit_of_work import UnitOfWorkFactory
from .models import User, Product
from .enums import DatabaseServer


class DomainService:
    """ドメインサービス基底クラス"""
    
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory


class UserService(DomainService):
    """ユーザーサービス"""
    
    def get_user_by_id(self, user_id: int, server: DatabaseServer = DatabaseServer.PRIMARY) -> Optional[User]:
        """ユーザーをIDで取得"""
        with self._uow_factory.create(server) as uow:
            return uow.users.get_by_id(user_id)
    
    def get_all_users(self, server: DatabaseServer = DatabaseServer.PRIMARY) -> List[User]:
        """全ユーザーを取得"""
        with self._uow_factory.create(server) as uow:
            return uow.users.get_all()
    
    def create_user(self, user: User, server: DatabaseServer = DatabaseServer.PRIMARY) -> User:
        """ユーザーを作成"""
        with self._uow_factory.create(server) as uow:
            created_user = uow.users.add(user)
            uow.commit()
            return created_user


class ProductService(DomainService):
    """商品サービス"""
    
    def get_product_by_id(self, product_id: int, server: DatabaseServer = DatabaseServer.PRIMARY) -> Optional[Product]:
        """商品をIDで取得"""
        with self._uow_factory.create(server) as uow:
            return uow.products.get_by_id(product_id)
    
    def get_all_products(self, server: DatabaseServer = DatabaseServer.PRIMARY) -> List[Product]:
        """全商品を取得"""
        with self._uow_factory.create(server) as uow:
            return uow.products.get_all()
