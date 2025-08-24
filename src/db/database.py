import os
from typing import Dict, Optional, Any, List, Union
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# データベース種類の定義
class DBType:
    SQLITE = "sqlite"
    MARIADB = "mariadb"
    SQLSERVER = "sqlserver"

# データベース接続URL生成
def get_connection_url(db_type: str) -> str:
    """指定されたデータベースタイプに基づいて接続URLを生成"""
    if db_type == DBType.SQLITE:
        return os.getenv("SQLITE_DATABASE_URL", "sqlite:///./app.db")
    
    elif db_type == DBType.SQLSERVER:
        host = os.getenv("SQLSERVER_HOST", "localhost")
        port = os.getenv("SQLSERVER_PORT", "1433")
        database = os.getenv("SQLSERVER_DATABASE", "dev")
        driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")
        user = os.getenv("SQLSERVER_USER", "ka")
        password = os.getenv("SQLSERVER_PASSWORD", "0418")
        extra_params = {
            "driver": driver.replace(" ", "+"),
            "timeout": "30",  # Increase connection timeout
            "encrypt": "no",  # Try disabling encryption
        }
        if user and password:
            # SQL Server認証
            auth_part = f"{user}:{password}@{host}:{port}"
        else:
            # Windows認証
            auth_part = f"@{host}:{port}"
            extra_params["trusted_connection"] = "yes"
        
        # Build connection URL with all parameters
        params_str = "&".join(f"{k}={v}" for k, v in extra_params.items())
        return f"mssql+pyodbc://{auth_part}/{database}?{params_str}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

# エンジンとセッションファクトリの保持
class DatabaseManager:
    def __init__(self):
        self.engines: Dict[str, Engine] = {}
        self.session_factories: Dict[str, scoped_session] = {}
        self.default_db = os.getenv("DEFAULT_DB", DBType.SQLITE)
        
        # Base classは全DBで共有
        self.Base = declarative_base()

    def init_db(self, db_type: Optional[str] = None) -> None:
        """指定されたデータベース向けにエンジンとセッションファクトリを初期化"""
        db_type = db_type or self.default_db
        
        if db_type not in self.engines:
            connection_url = get_connection_url(db_type)
            
            # DB固有のエンジン設定
            kwargs = {"pool_pre_ping": True}
            if db_type == DBType.SQLITE:
                kwargs["connect_args"] = {"check_same_thread": False}
            
            engine = create_engine(connection_url, **kwargs)
            self.engines[db_type] = engine
            
            session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.session_factories[db_type] = scoped_session(session_factory)

    def get_engine(self, db_type: Optional[str] = None) -> Engine:
        """指定されたデータベース向けのエンジンを取得"""
        db_type = db_type or self.default_db
        
        if db_type not in self.engines:
            self.init_db(db_type)
        
        return self.engines[db_type]

    def get_session(self, db_type: Optional[str] = None) -> scoped_session:
        """指定されたデータベース向けのセッションを取得"""
        db_type = db_type or self.default_db
        
        if db_type not in self.session_factories:
            self.init_db(db_type)
        
        return self.session_factories[db_type]

    def create_tables(self, db_type: Optional[str] = None) -> None:
        """指定されたデータベースにテーブルを作成"""
        db_type = db_type or self.default_db
        engine = self.get_engine(db_type)
        self.Base.metadata.create_all(bind=engine)

    def execute_raw_sql(self, sql: str, params: Dict = None, is_select: bool = True,
                        db_type: Optional[str] = None) -> Union[List[Dict], int]:
        """生のSQLクエリを実行するヘルパー関数"""
        db_type = db_type or self.default_db
        engine = self.get_engine(db_type)
        
        with engine.connect() as conn:
            if isinstance(sql, str):
                sql = text(sql)
                
            result = conn.execute(sql, params or {})
            
            if is_select:
                return [dict(row) for row in result]
            else:
                conn.commit()
                return result.rowcount

# シングルトンインスタンス
db_manager = DatabaseManager()

# DBセッション取得用コンテキストマネージャー
@contextmanager
def get_db(db_type: Optional[str] = None) -> Session:
    """指定されたデータベースのセッションを取得するコンテキストマネージャー"""
    db_type = db_type or db_manager.default_db
    session = db_manager.get_session(db_type)
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.remove()