# app/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # App Settings
    app_name: str = "Worldo Realtime Api"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Redis Settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # JWT Settings (para autenticação com Next.js)
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    
    # Next.js API URL
    nextjs_url: str = "http://localhost:3000"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        env_prefix = "WORLDO_"
        case_sensitive = False

settings = Settings()