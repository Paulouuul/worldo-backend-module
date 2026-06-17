# app/api/routes/cosmetic/marketplace/cart/add_item/use_case.py
from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class AddItemRequest:
    def __init__(self, user_id: str, item_data: Dict[str, Any]):
        self.user_id = user_id
        self.item_data = item_data

class AddItemUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    def execute(self, request: AddItemRequest) -> Dict[str, Any]:
        """
        Adiciona item ao carrinho
        
        Returns:
            Dict: Resumo do carrinho atualizado
        """
        try:
            cart = self.cart_service.add_item(request.user_id, request.item_data)
            
            if not cart:
                return {
                    "success": False,
                    "error": "Erro ao adicionar item ao carrinho",
                    "status_code": 400
                }
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
                "status_code": 200
            }
            
        except Exception as e:
            logger.error(f"Erro no AddItemUseCase: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }