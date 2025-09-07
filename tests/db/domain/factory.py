from .config import ConfigManager
from .connection import DatabaseManager
from .unit_of_work import UnitOfWorkFactory
from .service import UserService, ProductService


class DomainFactory:
    """ドメインオブジェクトファクトリ"""
    
    def __init__(self):
        self._config_manager = ConfigManager()
        self._db_manager = DatabaseManager(self._config_manager)
        self._uow_factory = UnitOfWorkFactory(self._db_manager)
    
    @property
    def config_manager(self) -> ConfigManager:
        return self._config_manager
    
    @property
    def db_manager(self) -> DatabaseManager:
        return self._db_manager
    
    @property
    def uow_factory(self) -> UnitOfWorkFactory:
        return self._uow_factory
    
    def create_user_service(self) -> UserService:
        return UserService(self._uow_factory)
    
    def create_product_service(self) -> ProductService:
        return ProductService(self._uow_factory)
    
    def cleanup(self) -> None:
        """リソースをクリーンアップ"""
        self._db_manager.close_all()
