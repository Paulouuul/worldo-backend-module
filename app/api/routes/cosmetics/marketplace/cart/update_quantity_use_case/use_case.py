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
    
    async def execute(self, request: UpdateQuantityRequest) -> tuple[Dict[str, Any], int]:
        """Atualiza quantidade de um item no carrinho"""
        try:
            await self.cart_service.sync_with_postgres(request.user_id)
            cart = self.cart_service.get_cart(request.user_id)
            item = None
            for cart_item in cart.items:
                if cart_item.id == request.item_id:
                    item = cart_item
                    break
            
            if item and request.quantity > item.max_quantity:
                return {
                    "error": f"Quantidade {request.quantity} excede o estoque disponível ({item.max_quantity})",
                    "max_quantity": item.max_quantity,
                    "current_quantity": item.quantity
                }, 400
            
            # Atualizar quantidade
            updated_cart = self.cart_service.update_quantity(
                request.user_id, 
                request.item_id, 
                request.quantity
            )
            
            if not updated_cart:
                return {
                    "error": "Item não encontrado no carrinho",
                }, 404
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no UpdateQuantityUseCase: {e}")
            return {
                "error": str(e),
            }, 500