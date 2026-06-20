from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SyncCartRequest:
    def __init__(self, user_id: str):
        self.user_id = user_id

class SyncCartUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    async def execute(self, request: SyncCartRequest) -> tuple[Dict[str, Any], int]:
        try:
            cart = await self.cart_service.sync_with_postgres(request.user_id)
            
            return {
                "success": True,
                "data": self.cart_service.get_cart_summary(request.user_id),
                "message": "Carrinho sincronizado com sucesso"
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no SyncCartUseCase: {e}")
            return {"error": str(e)}, 500