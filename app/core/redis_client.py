# app/core/redis_client.py
# Cliente Redis compartilhado (redis_simplify), configurado a partir das settings.

from redis_simplify import RedisClient
from app.core.config import settings

redis_client = RedisClient(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password or None,
    db=settings.redis_db,
    log_level="INFO"
)
