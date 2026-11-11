# app/api/routes/cosmetics/marketplace/cart/sync_cart_use_case/use_case.py
# Caso de uso de POST /cosmetics/marketplace/cart/sync: sincroniza o carrinho com o PostgreSQL.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SyncCartRequest:
    """Parâmetros: id do usuário."""
    def __init__(self, user_id: str):
        """Guarda os parâmetros da requisição."""
        self.user_id = user_id

class SyncCartUseCase:
    """Sincroniza preço e estoque dos itens do carrinho."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, request: SyncCartRequest) -> tuple[Dict[str, Any], int]:
        """Sincroniza o carrinho com o PostgreSQL e retorna o resumo. Retorna (resposta, status
        HTTP).
        """
        try:
            cart = await self.cart_service.sync_with_postgres(request.user_id)
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
                "message": "Carrinho sincronizado com sucesso"
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no SyncCartUseCase: {e}")
            return {"error": str(e)}, 500
