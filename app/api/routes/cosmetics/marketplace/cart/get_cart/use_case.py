from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GetCartRequest:
    def __init__(self, user_id: str):
        self.user_id = user_id

class GetCartUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    def execute(self, request: GetCartRequest) -> tuple[Dict[str, Any], int]:
        """Retorna o carrinho do usuário"""
        try:
            cart_summary = self.cart_service.get_cart_summary(request.user_id)
            
            return {
                "success": True,
                "data": cart_summary
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no GetCartUseCase: {e}")
            return {
                "error": str(e),
            }, 500