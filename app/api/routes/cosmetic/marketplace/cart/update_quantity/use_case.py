from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class UpdateQuantityRequest:
    def __init__(self, user_id: str, item_id: str, quantity: int):
        self.user_id = user_id
        self.item_id = item_id
        self.quantity = quantity

class UpdateQuantityUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    def execute(self, request: UpdateQuantityRequest) -> Dict[str, Any]:
        """Atualiza quantidade de um item no carrinho"""
        try:
            cart = self.cart_service.update_quantity(
                request.user_id, 
                request.item_id, 
                request.quantity
            )
            
            if not cart:
                return {
                    "success": False,
                    "error": "Item não encontrado no carrinho",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
                "status_code": 200
            }
            
        except Exception as e:
            logger.error(f"Erro no UpdateQuantityUseCase: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }