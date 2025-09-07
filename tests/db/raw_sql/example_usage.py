from .config import Config
from .connection_manager import ConnectionManager
from .sql_server_type import SqlServerType
from .user_service import UserService

def main():
    """Example usage of the DAO architecture"""
    
    # Initialize configuration and connection manager
    config = Config()
    connection_manager = ConnectionManager(config)
    
    # Create user service for production server
    user_service = UserService(connection_manager, SqlServerType.SQL001)
    
    try:
        # Example operations
        database_name = "MyProductionDB"
        
        # Get all users
        users = user_service.get_all_users(database_name)
        print(f"Found {len(users)} users")
        
        # Create new user
        success = user_service.create_user(database_name, "john_doe", "john@example.com")
        if success:
            print("User created successfully")
        
        # Get specific user
        user = user_service.get_user_by_id(database_name, 1)
        if user:
            print(f"User found: {user['username']}")
        
        # Update user email
        success = user_service.update_user_email(database_name, 1, "newemail@example.com")
        if success:
            print("Email updated successfully")
            
    except Exception as e:
        print(f"Error: {e}")

def example_with_different_servers():
    """Example using different SQL Servers"""
    config = Config()
    connection_manager = ConnectionManager(config)
    
    # Use different servers for different environments
    prod_service = UserService(connection_manager, SqlServerType.SQL001)
    staging_service = UserService(connection_manager, SqlServerType.SRVDB02)
    dev_service = UserService(connection_manager, SqlServerType.VRVSQL2022)
    
    # Each service connects to different SQL Server but uses same business logic
    prod_users = prod_service.get_all_users("ProductionDB")
    staging_users = staging_service.get_all_users("StagingDB")
    dev_users = dev_service.get_all_users("DevelopmentDB")

if __name__ == "__main__":
    main()
