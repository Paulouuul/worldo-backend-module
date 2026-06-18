
from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ClearCartUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    def execute(self, user_id: str) -> tuple[Dict[str, Any], int]:
        """Esvazia o carrinho"""
        try:
            self.cart_service.clear_cart(user_id)
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(user_id),
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no ClearCartUseCase: {e}")
            return {
                "error": str(e)
            }, 500