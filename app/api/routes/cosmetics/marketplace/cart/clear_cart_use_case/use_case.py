from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ClearCartUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    async def execute(self, user_id: str) -> tuple[Dict[str, Any], int]:
        """
        Remove todos os itens do carrinho do usuário.
        Mantém o carrinho vazio no Redis para futuras adições.
        """
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