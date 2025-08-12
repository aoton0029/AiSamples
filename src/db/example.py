from sqlalchemy import text
from database import get_db, db_manager, DBType

# テーブル作成
db_manager.create_tables(DBType.SQLITE)
db_manager.create_tables(DBType.MARIADB)
db_manager.create_tables(DBType.SQLSERVER)

# SQLiteを使用する例
from services.user_service import UserService

print("--- Using SQLite ---")
with get_db(DBType.SQLITE) as db:
    user_service = UserService(db, DBType.SQLITE)
    user = user_service.create_user({
        "username": "sqlite_user",
        "email": "sqlite@example.com",
        "hashed_password": "hash123"
    })
    print(f"Created user in SQLite: {user.username}")
    
    # カスタムクエリ実行
    users = user_service.get_users_custom()
    print(f"Found {len(users)} users in SQLite")

# MariaDBを使用する例
print("\n--- Using MariaDB ---")
with get_db(DBType.MARIADB) as db:
    user_service = UserService(db, DBType.MARIADB)
    user = user_service.create_user({
        "username": "mariadb_user",
        "email": "mariadb@example.com",
        "hashed_password": "hash456"
    })
    print(f"Created user in MariaDB: {user.username}")
    
    # カスタムクエリ実行
    users = user_service.get_users_custom()
    print(f"Found {len(users)} users in MariaDB")

# SQL Serverを使用する例
print("\n--- Using SQL Server ---")
with get_db(DBType.SQLSERVER) as db:
    user_service = UserService(db, DBType.SQLSERVER)
    user = user_service.create_user({
        "username": "sqlserver_user",
        "email": "sqlserver@example.com",
        "hashed_password": "hash789"
    })
    print(f"Created user in SQL Server: {user.username}")
    
    # カスタムクエリ実行
    users = user_service.get_users_custom()
    print(f"Found {len(users)} users in SQL Server")

# デフォルトデータベースを使用する例
print("\n--- Using Default Database ---")
with get_db() as db:
    user_service = UserService(db)
    users = user_service.get_users_custom()
    print(f"Found {len(users)} users in default database")

# 直接SQLを実行する例
print("\n--- Direct SQL Execution ---")
from database import db_manager

sqlite_users = db_manager.execute_raw_sql(
    "SELECT * FROM users", 
    db_type=DBType.SQLITE
)
print(f"Direct SQLite query found {len(sqlite_users)} users")

# トランザクション内で複数のSQLを実行する例
with get_db(DBType.MARIADB) as db:
    try:
        # マルチステートメントトランザクション
        db.execute(text("UPDATE users SET status = 'active' WHERE id = :id"), {"id": 1})
        db.execute(text("INSERT INTO logs (message) VALUES (:msg)"), {"msg": "User activated"})
        # with句の終了時に自動コミット
    except Exception as e:
        # エラー時は自動ロールバック
        print(f"Error in transaction: {e}")