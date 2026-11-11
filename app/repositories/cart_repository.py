# app/repositories/cart_repository.py
# Repositório do carrinho no Redis: salva, busca, remove e consulta o TTL do carrinho de cada
# usuário (chave cart:<user_id>, expira em 7 dias).

from app.core.redis_client import redis_client
from app.entities.cart_entity import CartEntity
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CartRepository:
    """Persistência do carrinho no Redis como JSON, com TTL de 7 dias renovado a cada gravação."""
    
    PREFIX = "cart:"
    
    # Tempo de vida em segundos (7 dias)
    TTL = 604800
    
    def _get_key(self, user_id: str) -> str:
        """Monta a chave Redis do carrinho do usuário (cart:<user_id>)."""
        return f"{self.PREFIX}{user_id}"
    
    def save(self, cart: CartEntity) -> bool:
        """Grava o carrinho no Redis renovando o TTL. Retorna False em caso de falha."""
        try:
            key = self._get_key(cart.user_id)
            data = cart.to_dict()
            
            success = redis_client.set_json(key, data, self.TTL)
            
            if success:
                logger.info(f"Carrinho salvo para usuário: {cart.user_id}")
            else:
                logger.error(f"Falha ao salvar carrinho: {cart.user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao salvar carrinho: {e}")
            return False
    
    def find_by_user_id(self, user_id: str) -> Optional[CartEntity]:
        """Carrega o carrinho do usuário. Retorna None se não existir ou em caso de erro."""
        try:
            key = self._get_key(user_id)
            data = redis_client.get_json(key)
            
            if not data:
                logger.info(f"Carrinho não encontrado para usuário: {user_id}")
                return None
            
            cart = CartEntity.from_dict(data)
            logger.info(f"Carrinho carregado para usuário: {user_id}")
            
            return cart
            
        except Exception as e:
            logger.error(f"Erro ao buscar carrinho: {e}")
            return None
    
    def delete(self, user_id: str) -> bool:
        """Remove o carrinho do usuário. Retorna True se havia carrinho para remover."""
        try:
            key = self._get_key(user_id)
            result = redis_client.delete(key)
            
            if result:
                logger.info(f"Carrinho deletado para usuário: {user_id}")
            else:
                logger.info(f"Carrinho não existia para deletar: {user_id}")
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Erro ao deletar carrinho: {e}")
            return False
    
    def exists(self, user_id: str) -> bool:
        """Retorna True se o usuário tem carrinho salvo."""
        try:
            key = self._get_key(user_id)
            return redis_client.exists(key)
            
        except Exception as e:
            logger.error(f"Erro ao verificar carrinho: {e}")
            return False
    
    def get_ttl(self, user_id: str) -> int:
        """Segundos restantes até o carrinho expirar (-1 sem expiração, -2 inexistente ou erro)."""
        try:
            key = self._get_key(user_id)
            return redis_client.client.ttl(key)
        except Exception as e:
            logger.error(f"Erro ao obter TTL: {e}")
            return -2
