# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    jwt_secret: str = "3e649cf42e8d84a5b824af1fb7033f6a7378a02f040fe5e4caff780e3c44f045"
    jwt_algorithm: str = "HS256"
    
    # Next.js API URL
    nextjs_url: str = "http://localhost:3000"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WORLDO_",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()