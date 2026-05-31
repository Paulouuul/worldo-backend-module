# app/entities/cart_item.py
from app.interfaces.entity_interface import EntityInterface
from typing import Optional

class CartItemEntity(EntityInterface):
    listing_id: str
    frame_id: str
    name: str
    price: int
    quantity: int
    seller_id: str
    seller_name: str
    image_url: Optional[str] = ""
    
    def total(self) -> int:
        return self.price * self.quantity
    
    def to_dict(self) -> dict:
        """Converte para dicionário (serializável para JSON)"""
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "total": self.total()
        }
    
    @classmethod
    def list_fields_to_not_update(cls):
        """Sobrescreve se necessário"""
        return ['id', 'created_at', 'listing_id']