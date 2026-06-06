# app/core/redis_client.py
from redis_simplify import RedisClient
from app.core.config import settings

# Cria o cliente usando as configurações do seu settings
redis_client = RedisClient(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password or None,
    db=settings.redis_db,
    log_level="INFO"
)