from db.database import get_db, db_manager, DBType
from db.models.user import User

if __name__ == "__main__":
    db_manager.init_db(DBType.SQLSERVER)
    with get_db(DBType.SQLSERVER) as session:
        # Userテーブル作成
        db_manager.create_tables(DBType.SQLSERVER)
        user = User(username="John Doe", email="john.doe@example.com")
        session.add(user)