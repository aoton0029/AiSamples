from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    # PostgreSQL settings
    POSTGRES_DATABASE: str = os.getenv("POSTGRES_DATABASE")
    POSTGRES_USERNAME: str = os.getenv("POSTGRES_USERNAME")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))

    # MongoDB settings
    MONGODB_USERNAME: str = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD")
    MONGODB_HOST: str = os.getenv("MONGODB_HOST", "mongodb")
    MONGODB_PORT: int = int(os.getenv("MONGODB_PORT", 27017))

    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD")

    # Other settings
    N8N_ENCRYPTION_KEY: str = os.getenv("N8N_ENCRYPTION_KEY")
    N8N_USER_MANAGEMENT_JWT_SECRET: str = os.getenv("N8N_USER_MANAGEMENT_JWT_SECRET")

settings = Settings()