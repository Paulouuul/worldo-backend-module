from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ValidateCartRequest:
    def __init__(self, user_id: str):
        self.user_id = user_id

class ValidateCartUseCase:
    def __init__(self):
        self.cart_service = RedisCartService()
    
    async def execute(self, request: ValidateCartRequest) -> tuple[Dict[str, Any], int]:
        try:
            validation = await self.cart_service.validate_for_checkout(request.user_id)
            
            if validation["valid"]:
                return {
                    "success": True,
                    "valid": True,
                    "cart": validation["cart"].to_dict(),
                    "message": "Carrinho validado com sucesso"
                }, 200
            else:
                return {
                    "valid": False,
                    "errors": validation["errors"],
                    "cart": validation["cart"].to_dict(),
                    "message": "Carrinho possui itens com problema"
                }, 400
                
        except Exception as e:
            logger.error(f"Erro no ValidateCartUseCase: {e}")
            return {"error": str(e)}, 500