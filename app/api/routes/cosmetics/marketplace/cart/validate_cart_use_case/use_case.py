# app/api/routes/cosmetics/marketplace/cart/validate_cart_use_case/use_case.py
# Caso de uso de POST /cosmetics/marketplace/cart/validate: valida o carrinho antes do checkout.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ValidateCartRequest:
    """Parâmetros: id do usuário."""
    def __init__(self, user_id: str):
        """Guarda os parâmetros da requisição."""
        self.user_id = user_id

class ValidateCartUseCase:
    """Valida o carrinho para o checkout."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, request: ValidateCartRequest) -> tuple[Dict[str, Any], int]:
        """Sincroniza e valida o carrinho: 200 com o carrinho se estiver tudo disponível, 400 com a
        mensagem de erro caso contrário.
        """
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
                    "error": validation["error"],
                    "cart": validation["cart"].to_dict(),
                    "message": "Carrinho possui itens com problema"
                }, 400
                
        except Exception as e:
            logger.error(f"Erro no ValidateCartUseCase: {e}")
            return {"error": str(e)}, 500
