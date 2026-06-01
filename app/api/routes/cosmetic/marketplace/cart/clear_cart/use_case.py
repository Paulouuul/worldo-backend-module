
from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ClearCartUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    def execute(self, user_id: str) -> Dict[str, Any]:
        """Esvazia o carrinho"""
        try:
            cart = self.cart_service.clear_cart(user_id)
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(user_id),
                "status_code": 200
            }
            
        except Exception as e:
            logger.error(f"Erro no ClearCartUseCase: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }