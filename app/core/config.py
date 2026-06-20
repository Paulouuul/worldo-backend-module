# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # App Settings
    app_name: str = "Worldo Backend"
    api_prefix: str = ""
    debug: bool = False
    environment: str = ""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database Settings:
    database_url: str = ""
    database_host: str = ""
    database_port: int = 5432
    database_name: str = ""
    database_user: str = ""
    database_password: str = ""
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10
    db_pool_max_queries: int = 50000
    db_pool_timeout: int = 60

    
    # Redis Settings
    redis_host: str = ""
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # R2 (Cloudflare) Settings
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_public_bucket: str = ""
    r2_private_bucket: str = ""
    r2_public_url: str = ""
    
    # JWT Settings
    jwt_secret: str = ""
    jwt_algorithm: str = ""
    
    # Next.js API URL
    nextjs_url: str = ""
    
    # CORS
    frontend_url: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WORLDO_",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()