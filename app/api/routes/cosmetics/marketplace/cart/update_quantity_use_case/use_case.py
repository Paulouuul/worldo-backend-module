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
            # VALIDAR QUANTIDADE NEGATIVA
            if request.quantity < 0:
                return {
                    "error": "Quantidade não pode ser negativa"
                }, 400
            
            
            # SINCRONIZAR COM POSTGRES
            await self.cart_service.sync_with_postgres(request.user_id)
            
            # BUSCAR O ITEM ESPECÍFICO
            cart = self.cart_service.get_cart(request.user_id)
            item = None
            for cart_item in cart.items:
                if cart_item.id == request.item_id:
                    item = cart_item
                    break
            
            # VERIFICAR SE ITEM EXISTE
            if not item:
                return {
                    "error": f"Item com ID '{request.item_id}' não encontrado no carrinho"
                }, 404
            
            # SE QUANTITY <= 0, REMOVER ITEM
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
            
            # VALIDAR ESTOQUE
            if request.quantity > item.max_quantity:
                return {
                    "error": f"Quantidade {request.quantity} excede o estoque disponível ({item.max_quantity})",
                    "max_quantity": item.max_quantity,
                    "current_quantity": item.quantity
                }, 400
            
            # VALIDAR LIMITE MÁXIMO POR ITEM
            if request.quantity > RedisCartService.MAX_QUANTITY_PER_ITEM:
                return {
                    "error": f"Quantidade máxima por item é {RedisCartService.MAX_QUANTITY_PER_ITEM}",
                    "max_allowed": RedisCartService.MAX_QUANTITY_PER_ITEM
                }, 400
            
            # ATUALIZAR QUANTIDADE
            updated_cart = self.cart_service.update_quantity(
                request.user_id, 
                request.item_id, 
                request.quantity
            )
            
            if not updated_cart:
                return {
                    "error": "Erro ao atualizar quantidade do item"
                }, 500
            
            # SUCESSO
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