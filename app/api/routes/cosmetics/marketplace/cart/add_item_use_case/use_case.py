# app/api/routes/cosmetic/marketplace/cart/add_item/use_case.py
from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AddItemRequest:
    def __init__(self, user_id: str, public_id: str, item_data: Dict[str, Any]):
        self.user_id = user_id
        self.public_id = public_id
        self.item_data = item_data

class AddItemUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    async def execute(self, request: AddItemRequest) -> tuple[Dict[str, Any], int]:
        """
        Adiciona item ao carrinho com validações de negócio
        """
        try:

            # Validar campos obrigatórios
            required_fields = ["listing_id", "frame_id", "name", "price", "seller_id", "quantity"]
            for field in required_fields:
                if field not in request.item_data:
                    return {
                        "error": f"Campo '{field}' é obrigatório"
                    }, 400
            
            # Validar quantidade
            quantity = request.item_data.get("quantity", 1)
            if quantity <= 0:
                return {"error": "Quantidade deve ser maior que zero"}, 400
            
            # Validação de não comprar próprios itens
            if request.item_data["seller_id"] == request.public_id:
                return {
                    "error": "Você não pode comprar seus próprios itens"
                }, 400
            
            # DELEGAR PARA O RedisCartService (já tem validações)
            cart = self.cart_service.add_item(request.user_id, request.item_data)
            
            # TRATAR O RETORNO DO RedisCartService
            if cart is None:
                
                # Verificar o carrinho atual
                current_cart = self.cart_service.get_cart(request.user_id)
                
                # Verificar se é erro de estoque
                listing_id = request.item_data["listing_id"]
                current_quantity = self.cart_service.get_item_quantity(request.user_id, listing_id)
                requested_quantity = request.item_data.get("quantity", 1)
                max_quantity = request.item_data.get("max_quantity", 0)
                
                if max_quantity > 0 and (current_quantity + requested_quantity) > max_quantity:
                    available = max_quantity - current_quantity
                    return {
                        "error": f"Você já tem {current_quantity} no carrinho. Disponível para adicionar: {available} unidades"
                    }, 400
                
                # Verificar se é erro de limite de itens
                if current_cart and current_cart.unique_items_count >= RedisCartService.MAX_ITEMS_PER_CART:
                    return {
                        "error": f"Limite de {RedisCartService.MAX_ITEMS_PER_CART} itens diferentes no carrinho excedido"
                    }, 400
                
                # Verificar se é erro de quantidade máxima
                if requested_quantity > RedisCartService.MAX_QUANTITY_PER_ITEM:
                    return {
                        "error": f"Quantidade máxima por item é {RedisCartService.MAX_QUANTITY_PER_ITEM}"
                    }, 400
                
                # Erro genérico
                return {
                    "error": "Erro ao adicionar item ao carrinho"
                }, 400
            
            # SUCESSO
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no AddItemUseCase: {e}", exc_info=True)
            return {
                "error": "Erro interno ao processar solicitação",
            }, 500