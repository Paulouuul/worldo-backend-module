from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RemoveItemRequest:
    def __init__(self, user_id: str, item_id: str):
        self.user_id = user_id
        self.item_id = item_id

class RemoveItemUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    async def execute(self, request: RemoveItemRequest) ->tuple[Dict[str, Any], int]:
        """Remove item do carrinho"""
        try:
            cart = self.cart_service.remove_item(request.user_id, request.item_id)
            
            if not cart:
                return {
                    "error": "Item não encontrado no carrinho",
                }, 404
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no RemoveItemUseCase: {e}")
            return {
                "error": str(e),
            }, 500