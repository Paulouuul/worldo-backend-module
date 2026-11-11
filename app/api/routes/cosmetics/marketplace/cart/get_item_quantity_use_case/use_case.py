# app/api/routes/cosmetics/marketplace/cart/get_item_quantity_use_case/use_case.py
# Caso de uso de GET /cosmetics/marketplace/cart/item/{listing_id}/quantity: quantidade do
# anúncio no carrinho.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GetItemQuantityRequest:
    """Parâmetros: id do usuário e id do anúncio."""
    def __init__(self, user_id: str, listing_id: str):
        """Guarda os parâmetros da requisição."""
        self.user_id = user_id
        self.listing_id = listing_id

class GetItemQuantityUseCase:
    """Consulta quantas unidades de um anúncio estão no carrinho."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, request: GetItemQuantityRequest) -> tuple[Dict[str, Any], int]:
        """Retorna {listing_id, quantity} (0 se o anúncio não estiver no carrinho) e o status HTTP."""
        try:
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
