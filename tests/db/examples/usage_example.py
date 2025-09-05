"""
使用例
"""
from sqlalchemy import Column, String, Integer
from ..config.database_config import DatabaseConfig, DatabaseConfigManager
from ..raw_sql.sql_server_manager import SQLServerManagerFactory
from ..domain.database_manager import DatabaseManager
from ..domain.base_entity import BaseEntity


# サンプルエンティティ
class User(BaseEntity):
    __tablename__ = 'users'
    
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)


def raw_sql_example():
    """生SQL使用例"""
    # 設定管理
    config_manager = DatabaseConfigManager()
    config_manager.add_config('server1', DatabaseConfig(
        server='localhost',
        database='testdb',
        username='user',
        password='password'
    ))
    
    # SQLServerManagerFactory使用
    factory = SQLServerManagerFactory(config_manager)
    
    try:
        # SQLServer単位でのセッション管理
        manager = factory.get_manager('server1')
        
        # 生SQLの実行
        results = manager.execute_query(
            "SELECT * FROM users WHERE username = :username",
            {'username': 'john'}
        )
        
        # データの挿入
        affected_rows = manager.execute_non_query(
            "INSERT INTO users (username, email) VALUES (:username, :email)",
            {'username': 'jane', 'email': 'jane@example.com'}
        )
        
        print(f"Query results: {results}")
        print(f"Affected rows: {affected_rows}")
        
    finally:
        factory.close_all()


def domain_example():
    """ドメインクラス使用例"""
    # 設定管理
    config_manager = DatabaseConfigManager()
    config_manager.add_config('server1', DatabaseConfig(
        server='localhost',
        database='master',  # 接続用
        username='user',
        password='password'
    ))
    
    # DatabaseManager使用
    db_manager = DatabaseManager(config_manager)
    
    try:
        # データベース単位でのセッション管理
        db_manager.create_tables('server1', 'userdb')
        
        # リポジトリの取得
        user_repo = db_manager.get_repository(User, 'server1', 'userdb')
        
        # エンティティの作成
        user = User(username='john', email='john@example.com')
        created_user = user_repo.create(user)
        
        # エンティティの取得
        found_user = user_repo.get_by_id(created_user.id)
        all_users = user_repo.get_all()
        
        print(f"Created user: {created_user}")
        print(f"Found user: {found_user}")
        print(f"All users: {len(all_users)}")
        
    finally:
        db_manager.close_all()


if __name__ == "__main__":
    print("=== Raw SQL Example ===")
    raw_sql_example()
    
    print("\n=== Domain Example ===")
    domain_example()
