# app/api/routes/cosmetics/marketplace/cart/add_item_use_case/use_case.py
# Caso de uso de POST /cosmetics/marketplace/cart/add/: valida e adiciona um anúncio ao
# carrinho.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AddItemRequest:
    """Parâmetros: id e publicId do usuário e dados do anúncio (item_data)."""
    def __init__(self, user_id: str, public_id: str, item_data: Dict[str, Any]):
        """Guarda os parâmetros da requisição."""
        self.user_id = user_id
        self.public_id = public_id
        self.item_data = item_data

class AddItemUseCase:
    """Adiciona um anúncio ao carrinho do usuário."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, request: AddItemRequest) -> tuple[Dict[str, Any], int]:
        """Valida campos obrigatórios, quantidade positiva e se o anúncio não é do próprio usuário,
        e adiciona ao carrinho.

        Quando o serviço recusa, identifica o motivo (estoque, limite de anúncios ou de
        unidades) para a mensagem de erro. Retorna (resposta, status HTTP).
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
            
            # O serviço aplica limites de carrinho, quantidade e estoque
            cart = self.cart_service.add_item(request.user_id, request.item_data)
            
            # None indica recusa: descobre o motivo para a mensagem de erro
            if cart is None:
                
                current_cart = self.cart_service.get_cart(request.user_id)
                
                # Estoque insuficiente
                listing_id = request.item_data["listing_id"]
                current_quantity = self.cart_service.get_item_quantity(request.user_id, listing_id)
                requested_quantity = request.item_data.get("quantity", 1)
                max_quantity = request.item_data.get("max_quantity", 0)
                
                if max_quantity > 0 and (current_quantity + requested_quantity) > max_quantity:
                    available = max_quantity - current_quantity
                    return {
                        "error": f"Você já tem {current_quantity} no carrinho. Disponível para adicionar: {available} unidades"
                    }, 400
                
                # Limite de anúncios distintos
                if current_cart and current_cart.unique_items_count >= RedisCartService.MAX_ITEMS_PER_CART:
                    return {
                        "error": f"Limite de {RedisCartService.MAX_ITEMS_PER_CART} itens diferentes no carrinho excedido"
                    }, 400
                
                # Limite de unidades por item
                if requested_quantity > RedisCartService.MAX_QUANTITY_PER_ITEM:
                    return {
                        "error": f"Quantidade máxima por item é {RedisCartService.MAX_QUANTITY_PER_ITEM}"
                    }, 400
                
                # Erro genérico
                return {
                    "error": "Erro ao adicionar item ao carrinho"
                }, 400
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no AddItemUseCase: {e}", exc_info=True)
            return {
                "error": "Erro interno ao processar solicitação",
            }, 500
