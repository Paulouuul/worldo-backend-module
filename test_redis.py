# test_redis.py
import sys
sys.path.insert(0, ".")

from app.core.redis_client import redis_client

# Teste genérico
print("Ping:", redis_client.ping())

# Teste JSON
redis_client.set_json("test:generic", {"message": "Funciona!"}, 60)
print("JSON:", redis_client.get_json("test:generic"))

# Teste Set
redis_client.sadd("test:set", "valor1", "valor2")
print("Set members:", redis_client.smembers("test:set"))

print("✅ RedisClient genérico funcionando!")