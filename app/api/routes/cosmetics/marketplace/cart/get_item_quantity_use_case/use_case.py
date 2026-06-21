# app/api/routes/cosmetic/marketplace/cart/get_item_quantity_use_case/use_case.py
from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GetItemQuantityRequest:
    def __init__(self, user_id: str, listing_id: str):
        self.user_id = user_id
        self.listing_id = listing_id

class GetItemQuantityUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    async def execute(self, request: GetItemQuantityRequest) -> tuple[Dict[str, Any], int]:
        try:
            # Buscar quantidade do item no carrinho
            quantity = self.cart_service.get_item_quantity(
                request.user_id, 
                request.listing_id
            )
            
            return {
                "success": True,
                "data": {
                    "listing_id": request.listing_id,
                    "quantity": quantity
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Erro ao buscar quantidade do item: {e}")
            return {"error": str(e)}, 500