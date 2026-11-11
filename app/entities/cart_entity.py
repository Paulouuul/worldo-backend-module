# app/entities/cart_entity.py
# Entidade de carrinho de compras do usuário, com itens, totais e operações de adicionar,
# remover, alterar quantidade e limpar.

from app.interfaces.entity_interface import EntityInterface
from typing import List
from app.entities.cart_item_entity import CartItemEntity
from datetime import datetime, timezone

class CartEntity(EntityInterface):
    
    """Carrinho de compras de um usuário."""
    user_id: str
    items: List[CartItemEntity] = []
    
    @property
    def total_items(self) -> int:
        """Total de unidades no carrinho (soma das quantidades)."""
        return sum(item.quantity for item in self.items)
    
    @property
    def total_price(self) -> int:
        """Preço total do carrinho em moedas."""
        return sum(item.total() for item in self.items)
    
    @property
    def unique_items_count(self) -> int:
        """Quantidade de anúncios distintos no carrinho."""
        return len(self.items)
    
    def add_item(self, new_item: CartItemEntity) -> bool:
        """Adiciona o item ao carrinho; se o anúncio já estiver nele, soma a quantidade. Retorna
        True.
        """
        for item in self.items:
            if item.listing_id == new_item.listing_id:
                item.quantity += new_item.quantity
                self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                return True
        
        self.items.append(new_item)
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return True
    
    def remove_item(self, item_id: str) -> bool:
        """Remove o item pelo id. Retorna False se o item não existir."""
        original_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        
        if len(self.items) != original_count:
            self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            return True
        return False
    
    def update_quantity(self, item_id: str, quantity: int) -> bool:
        """Define a quantidade do item (zero ou menos remove o item). Retorna False se o item não
        existir.
        """
        for item in self.items:
            if item.id == item_id:
                if quantity <= 0:
                    self.remove_item(item_id)
                else:
                    item.quantity = quantity
                self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                return True
        return False
    
    def clear(self) -> None:
        """Remove todos os itens do carrinho."""
        self.items = []
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def to_dict(self) -> dict:

        """Converte o carrinho em dict serializável, com itens e totais."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items],
            "total_items": self.total_items,
            "total_price": self.total_price,
            "unique_items_count": self.unique_items_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CartEntity":
        """Reconstrói o carrinho (e seus itens) a partir do dict salvo no Redis."""
        from app.entities.cart_item_entity import CartItemEntity
        
        # Converte strings ISO para datetime
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        # Reconstrói os itens
        items = []
        for item_data in data.get('items', []):
            items.append(CartItemEntity.from_dict(item_data))
        
        return cls(
            id=data.get('id'),
            user_id=data['user_id'],
            items=items,
            created_at=created_at,
            updated_at=updated_at
        )
    
    @classmethod
    def list_fields_to_not_update(cls):
        """Campos que `update()` nunca altera (inclui o user_id)."""
        return ['id', 'created_at', 'user_id']
