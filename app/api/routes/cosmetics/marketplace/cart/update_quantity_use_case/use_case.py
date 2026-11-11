# app/api/routes/cosmetics/marketplace/cart/update_quantity_use_case/use_case.py
# Caso de uso de PATCH /cosmetics/marketplace/cart/update/{item_id}: altera a quantidade de um
# item.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class UpdateQuantityRequest:
    """Parâmetros: id do usuário, id do item e nova quantidade."""
    def __init__(self, user_id: str, item_id: str, quantity: int):
        """Guarda os parâmetros da requisição."""
        self.user_id = user_id
        self.item_id = item_id
        self.quantity = quantity

class UpdateQuantityUseCase:
    """Altera a quantidade de um item do carrinho."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, request: UpdateQuantityRequest) -> tuple[Dict[str, Any], int]:
        """Sincroniza o carrinho, valida a nova quantidade contra o estoque e o limite por item e
        salva.

        Quantidade 0 remove o item. Retorna (resposta, status HTTP); 404 se o item não existir.
        """
        try:
            if request.quantity < 0:
                return {
                    "error": "Quantidade não pode ser negativa"
                }, 400
            
            
            # Garante estoque (max_quantity) atualizado antes de validar
            await self.cart_service.sync_with_postgres(request.user_id)
            
            cart = self.cart_service.get_cart(request.user_id)
            item = None
            for cart_item in cart.items:
                if cart_item.id == request.item_id:
                    item = cart_item
                    break
            
            if not item:
                return {
                    "error": f"Item com ID '{request.item_id}' não encontrado no carrinho"
                }, 404
            
            # Quantidade zero remove o item
            if request.quantity <= 0:
                logger.info(f"Removendo item {request.item_id} (quantity <= 0)")
                updated_cart = self.cart_service.remove_item(
                    request.user_id, 
                    request.item_id
                )
                
                if not updated_cart:
                    return {
                        "error": "Erro ao remover item do carrinho"
                    }, 500
                
                return {
                    "success": True,
                    "message": "Item removido do carrinho",
                    "data": self.cart_service.get_cart_summary(request.user_id),
                }, 200
            
            if request.quantity > item.max_quantity:
                return {
                    "error": f"Quantidade {request.quantity} excede o estoque disponível ({item.max_quantity})",
                    "max_quantity": item.max_quantity,
                    "current_quantity": item.quantity
                }, 400
            
            if request.quantity > RedisCartService.MAX_QUANTITY_PER_ITEM:
                return {
                    "error": f"Quantidade máxima por item é {RedisCartService.MAX_QUANTITY_PER_ITEM}",
                    "max_allowed": RedisCartService.MAX_QUANTITY_PER_ITEM
                }, 400
            
            updated_cart = self.cart_service.update_quantity(
                request.user_id, 
                request.item_id, 
                request.quantity
            )
            
            if not updated_cart:
                return {
                    "error": "Erro ao atualizar quantidade do item"
                }, 500
            
            return {
                "success": True,
                "message": f"Quantidade atualizada para {request.quantity}",
                "data": self.cart_service.get_cart_summary(request.user_id),
            }, 200
            
        except ValueError as e:
            logger.warning(f"Erro de validação no UpdateQuantityUseCase: {e}")
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Erro no UpdateQuantityUseCase: {e}", exc_info=True)
            return {
                "error": "Erro interno ao atualizar quantidade"
            }, 500
