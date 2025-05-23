"""
Tệp cấu hình tập trung cho backend
"""
import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env nếu có
load_dotenv()

class Config:
    # Database configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3300))
    DB_USER = os.getenv("DB_USER", "chatbot")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "chatbot")
    DB_NAME = os.getenv("DB_NAME", "chatbot")

    # Tạo một dictionary DB_CONFIG để dễ dàng truyền cho các thư viện DB nếu cần
    DB_CONFIG = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME
    }

    # JWT Configuration
    JWT_SECRET = os.getenv("JWT_SECRET", "SECRET_KEY")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

    # File Upload Configuration
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10MB

    # Ollama Configuration
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 120))  # Thời gian chờ đợi tối đa 120 giây

    # CORS Configuration
    CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    CORS_ORIGINS = CORS_ORIGINS_STR.split(",") if CORS_ORIGINS_STR else []


    # Embedding Model Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
