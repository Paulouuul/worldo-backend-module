# app/api/routes/cosmetics/marketplace/cart/clear_cart_use_case/use_case.py
# Caso de uso de DELETE /cosmetics/marketplace/cart/clear: esvazia o carrinho do usuário.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ClearCartUseCase:
    """Esvazia o carrinho do usuário."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, user_id: str) -> tuple[Dict[str, Any], int]:
        """Apaga o carrinho do Redis e retorna o resumo (vazio). Retorna (resposta, status HTTP)."""
        try:

            cart = self.cart_service.clear_cart(user_id)
        
            if cart is None:
                logger.error(f"Falha ao esvaziar carrinho: {user_id}")
                return {
                    "error": "Erro ao esvaziar carrinho. Tente novamente."
                }, 500
            return {
                "success": True,
                "message": "Carrinho esvaziado com sucesso",
                "data": self.cart_service.get_cart_summary(user_id),
            }, 200
        except Exception as e:
            logger.error(f"Erro no ClearCartUseCase para usuário {user_id}: {e}", exc_info=True)
            return {
                "error": "Erro interno ao esvaziar carrinho"
            }, 500
