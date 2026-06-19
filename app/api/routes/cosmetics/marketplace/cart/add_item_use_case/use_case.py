# app/api/routes/cosmetic/marketplace/cart/add_item/use_case.py
from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AddItemRequest:
    def __init__(self, user_id: str, item_data: Dict[str, Any]):
        self.user_id = user_id
        self.item_data = item_data

class AddItemUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    async def execute(self, request: AddItemRequest) -> tuple[Dict[str, Any], int]:
        """
        Adiciona item ao carrinho
        """
        try:
            cart = self.cart_service.add_item(request.user_id, request.item_data)
            
            # Erro
            if isinstance(cart, dict) and cart.get("error"):
                return {
                    "error": cart["error"],
                },cart.get("status_code", 400)
            
            if not cart:
                return {
                    "error": "Erro ao adicionar item ao carrinho",
                }, 400
            
            # Sucesso
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no AddItemUseCase: {e}")
            return {
                "error": str(e),
            }, 500