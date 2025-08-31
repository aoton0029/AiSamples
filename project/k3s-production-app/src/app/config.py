import os

class Config:
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://user:password@postgres:5432/mydatabase')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
    PORT = int(os.getenv('PORT', 5000))