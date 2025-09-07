import os
from dataclasses import dataclass
from typing import Dict
from dotenv import load_dotenv
from .sql_server_type import SqlServerType

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    server: str
    user: str
    password: str
    port: int
    
    def get_connection_string(self) -> str:
        """Generate SQLAlchemy connection string for pymssql"""
        return f"mssql+pymssql://{self.user}:{self.password}@{self.server}:{self.port}"

class Config:
    """Application configuration class"""
    
    def __init__(self, env_file_path: str = None):
        if env_file_path:
            load_dotenv(env_file_path)
        else:
            load_dotenv()
        
        self.databases: Dict[SqlServerType, DatabaseConfig] = {}
        self._load_database_configs()
    
    def _load_database_configs(self):
        """Load database configurations from environment variables"""
        for server_type in SqlServerType:
            prefix = server_type.value
            self.databases[server_type] = DatabaseConfig(
                server=os.getenv(f"{prefix}_SERVER"),
                user=os.getenv(f"{prefix}_USER"),
                password=os.getenv(f"{prefix}_PASSWORD"),
                port=int(os.getenv(f"{prefix}_PORT", 1433))
            )
    
    def get_database_config(self, server_type: SqlServerType) -> DatabaseConfig:
        """Get database configuration for specific server type"""
        return self.databases.get(server_type)
