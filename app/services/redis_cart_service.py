# app/services/cart_service.py
from app.repositories.cart_repository import CartRepository
from app.entities.cart_entity import CartEntity
from app.entities.cart_item_entity import CartItemEntity
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RedisCartService:
    """Serviço para gerenciar carrinho de compras"""
    
    # Limites de negócio
    MAX_ITEMS_PER_CART = 50  # Máximo de itens diferentes no carrinho
    MAX_QUANTITY_PER_ITEM = 99  # Máximo de unidades por item
    
    def __init__(self):
        self.repository = CartRepository()
    
    def get_cart(self, user_id: str) -> CartEntity:
        """
        Obtém o carrinho do usuário.
        Se não existir, cria um novo carrinho vazio.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            CartEntity: Carrinho do usuário
        """
        cart = self.repository.find_by_user_id(user_id)
        
        if not cart:
            logger.info(f"Criando novo carrinho para usuário: {user_id}")
            cart = CartEntity(user_id=user_id)
            self.repository.save(cart)
        
        return cart
    
    def add_item(self, user_id: str, item_data: Dict[str, Any]) -> Optional[CartEntity]:
        """
        Adiciona item ao carrinho.
        
        Args:
            user_id: ID do usuário
            item_data: Dados do item (listing_id, frame_id, name, price, seller_id, etc.)
            
        Returns:
            CartEntity: Carrinho atualizado ou None se erro
        """
        cart = self.get_cart(user_id)
        
        # Validação: limite de itens diferentes
        if cart.unique_items_count >= self.MAX_ITEMS_PER_CART:
            logger.warning(f"Carrinho do usuário {user_id} atingiu limite de {self.MAX_ITEMS_PER_CART} itens")
            return None
        
        # Validação: quantidade máxima por item
        quantity = item_data.get("quantity", 1)
        if quantity > self.MAX_QUANTITY_PER_ITEM:
            logger.warning(f"Quantidade {quantity} excede o limite de {self.MAX_QUANTITY_PER_ITEM}")
            return None
        
        # Criar item
        new_item = CartItemEntity(
            listing_id=item_data["listing_id"],
            frame_id=item_data["frame_id"],
            name=item_data["name"],
            price=item_data["price"],
            quantity=quantity,
            seller_id=item_data["seller_id"],
            seller_name=item_data["seller_name"],
            image_url=item_data.get("image_url", "")
        )
        
        cart.add_item(new_item)
        self.repository.save(cart)
        
        logger.info(f"Item adicionado ao carrinho do usuário {user_id}: {new_item.name}")
        return cart
    
    def remove_item(self, user_id: str, item_id: str) -> Optional[CartEntity]:
        """
        Remove item do carrinho.
        
        Args:
            user_id: ID do usuário
            item_id: ID do item a ser removido
            
        Returns:
            CartEntity: Carrinho atualizado ou None se item não encontrado
        """
        cart = self.get_cart(user_id)
        
        if cart.remove_item(item_id):
            self.repository.save(cart)
            logger.info(f"Item {item_id} removido do carrinho do usuário {user_id}")
            return cart
        
        logger.warning(f"Item {item_id} não encontrado no carrinho do usuário {user_id}")
        return None
    
    def update_quantity(self, user_id: str, item_id: str, quantity: int) -> Optional[CartEntity]:
        """
        Atualiza quantidade de um item no carrinho.
        
        Args:
            user_id: ID do usuário
            item_id: ID do item
            quantity: Nova quantidade (se <= 0, remove o item)
            
        Returns:
            CartEntity: Carrinho atualizado ou None se item não encontrado
        """
        if quantity < 0:
            quantity = 0
        
        if quantity > self.MAX_QUANTITY_PER_ITEM:
            logger.warning(f"Quantidade {quantity} excede o limite de {self.MAX_QUANTITY_PER_ITEM}")
            quantity = self.MAX_QUANTITY_PER_ITEM
        
        cart = self.get_cart(user_id)
        
        if cart.update_quantity(item_id, quantity):
            self.repository.save(cart)
            logger.info(f"Quantidade do item {item_id} atualizada para {quantity} no carrinho do usuário {user_id}")
            return cart
        
        logger.warning(f"Item {item_id} não encontrado no carrinho do usuário {user_id}")
        return None
    
    def clear_cart(self, user_id: str) -> CartEntity:
        """
        Esvazia completamente o carrinho.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            CartEntity: Carrinho vazio
        """
        cart = self.get_cart(user_id)
        cart.clear()
        self.repository.save(cart)
        
        logger.info(f"Carrinho do usuário {user_id} foi esvaziado")
        return cart
    
    def delete_cart(self, user_id: str) -> bool:
        """
        Remove completamente o carrinho do Redis.
        Usado após finalização de compra.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            bool: True se removido com sucesso
        """
        result = self.repository.delete(user_id)
        
        if result:
            logger.info(f"Carrinho do usuário {user_id} foi removido do Redis")
        else:
            logger.warning(f"Carrinho do usuário {user_id} não existia para remover")
        
        return result
    
    def get_cart_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna um resumo do carrinho (útil para o frontend).
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict: Resumo do carrinho
        """
        cart = self.get_cart(user_id)
        
        return {
            "user_id": cart.user_id,
            "total_items": cart.total_items,
            "total_price": cart.total_price,
            "unique_items_count": cart.unique_items_count,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "total": item.total(),
                    "seller_name": item.seller_name,
                    "image_url": item.image_url
                }
                for item in cart.items
            ]
        }