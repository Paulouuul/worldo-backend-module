# app/entities/cart_item_entity.py
# Entidade de item do carrinho: um anúncio do marketplace com preço, quantidade e vendedor.

from app.interfaces.entity_interface import EntityInterface
from typing import Optional

class CartItemEntity(EntityInterface):
    """Item do carrinho referente a um anúncio (listing) do marketplace.

    `max_quantity` é o estoque disponível do anúncio no momento em que o item foi
    adicionado/sincronizado.
    """
    listing_id: str
    frame_id: str
    name: str
    price: int
    quantity: int
    seller_id: str
    seller_name: str
    image_url: Optional[str] = ""
    thumbnail_url: Optional[str] = ""
    max_quantity: int = 0
    
    def total(self) -> int:
        """Subtotal do item (preço × quantidade)."""
        return self.price * self.quantity
    
    def to_dict(self) -> dict:
        """Converte o item em dict serializável, incluindo o subtotal."""
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "frame_id": self.frame_id,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "seller_id": self.seller_id,
            "seller_name": self.seller_name,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "max_quantity": self.max_quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "total": self.total()
        }
    
    @classmethod
    def list_fields_to_not_update(cls):
        """Campos que `update()` nunca altera (inclui o listing_id)."""
        return ['id', 'created_at', 'listing_id']
