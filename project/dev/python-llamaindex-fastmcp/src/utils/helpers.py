def get_postgres_connection_string():
    import os
    from sqlalchemy.engine import URL

    username = os.getenv("POSTGRES_USERNAME")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DATABASE")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    return str(URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    ))

def get_mongodb_connection_string():
    import os

    username = os.getenv("MONGODB_USERNAME")
    password = os.getenv("MONGODB_PASSWORD")
    host = os.getenv("MONGODB_HOST", "localhost")
    port = os.getenv("MONGODB_PORT", "27017")
    database = os.getenv("MONGODB_DATABASE", "admin")

    return f"mongodb://{username}:{password}@{host}:{port}/{database}"

def validate_environment_variables():
    import os

    required_vars = [
        "POSTGRES_USERNAME",
        "POSTGRES_PASSWORD",
        "POSTGRES_DATABASE",
        "MONGODB_USERNAME",
        "MONGODB_PASSWORD"
    ]

    for var in required_vars:
        if os.getenv(var) is None:
            raise EnvironmentError(f"Missing required environment variable: {var}")