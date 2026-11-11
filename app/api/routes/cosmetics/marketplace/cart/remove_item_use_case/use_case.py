# app/api/routes/cosmetics/marketplace/cart/remove_item_use_case/use_case.py
# Caso de uso de DELETE /cosmetics/marketplace/cart/remove/{item_id}: remove um item do
# carrinho.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RemoveItemRequest:
    """Parâmetros: id do usuário e id do item no carrinho."""
    def __init__(self, user_id: str, item_id: str):
        """Guarda os parâmetros da requisição."""
        self.user_id = user_id
        self.item_id = item_id

class RemoveItemUseCase:
    """Remove um item do carrinho do usuário."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, request: RemoveItemRequest) ->tuple[Dict[str, Any], int]:
        """Remove o item e retorna o resumo atualizado; 404 se o item não existir. Retorna
        (resposta, status HTTP).
        """
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
