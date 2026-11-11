# app/api/routes/cosmetics/marketplace/cart/get_cart_use_case/use_case.py
# Caso de uso de GET /cosmetics/marketplace/cart/get e /cosmetics/marketplace/cart/get/summary:
# carrinho com detalhes atualizados.

from app.services.redis_cart_service import RedisCartService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GetCartRequest:
    """Parâmetros: id do usuário."""
    def __init__(self, user_id: str):
        """Guarda os parâmetros da requisição."""
        self.user_id = user_id

class GetCartUseCase:
    """Obtém o carrinho do usuário com dados atualizados dos anúncios."""
    def __init__(self):
        """Cria o serviço de carrinho usado pelo caso de uso."""
        self.cart_service = RedisCartService()
    
    async def execute(self, request: GetCartRequest) -> tuple[Dict[str, Any], int]:
        """Sincroniza o carrinho com o PostgreSQL e retorna os itens detalhados e os totais.
        Retorna (resposta, status HTTP).
        """
        try:
            cart_details = await self.cart_service.get_cart_with_details(request.user_id)
            return {
                "success": True,
                "data": cart_details
            }, 200
            
        except Exception as e:
            logger.error(f"Erro no GetCartUseCase: {e}")
            return {
                "error": str(e),
            }, 500
