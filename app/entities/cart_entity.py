from app.interfaces.entity_interface import EntityInterface
from typing import List
from app.entities.cart_item_entity import CartItemEntity
from datetime import datetime

class CartEntity(EntityInterface):
    
    user_id: str
    items: List[CartItemEntity] = []
    
    @property
    def total_items(self) -> int:
        """Número total de unidades (soma das quantidades)"""
        return sum(item.quantity for item in self.items)
    
    @property
    def total_price(self) -> int:
        """Preço total do carrinho"""
        return sum(item.total() for item in self.items)
    
    @property
    def unique_items_count(self) -> int:
        """Número de produtos no carrinho"""
        return len(self.items)
    
    def add_item(self, new_item: CartItemEntity) -> bool:
        """Adiciona item ao carrinho (se já existir, aumenta quantidade)
        
        Returns:
            bool: True se adicionado com sucesso
        """
        for item in self.items:
            if item.listing_id == new_item.listing_id:
                item.quantity += new_item.quantity
                self.updated_at = datetime.now()
                return True
        
        self.items.append(new_item)
        self.updated_at = datetime.now()
        return True
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item do carrinho pelo ID
        
        Returns:
            bool: True se encontrado e removido, False se não encontrado
        """
        original_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        
        if len(self.items) != original_count:
            self.updated_at = datetime.now()
            return True
        return False
    
    def update_quantity(self, item_id: str, quantity: int) -> bool:
        """Atualiza quantidade de um item específico
        
        Returns:
            bool: True se encontrado e atualizado, False se não encontrado
        """
        for item in self.items:
            if item.id == item_id:
                if quantity <= 0:
                    self.remove_item(item_id)
                else:
                    item.quantity = quantity
                self.updated_at = datetime.now()
                return True
        return False
    
    def clear(self) -> None:
        """Esvazia o carrinho completamente"""
        self.items = []
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Converte para dicionário (serializável para JSON)"""
        # Converte datetime para string
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items],  # ← CHAMA to_dict do item!
            "total_items": self.total_items,
            "total_price": self.total_price,
            "unique_items_count": self.unique_items_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CartEntity":
        """Cria entidade a partir de dicionário"""
        from app.entities.cart_item_entity import CartItemEntity
        from datetime import datetime
        
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
        """Campos que não podem ser atualizados diretamente"""
        return ['id', 'created_at', 'user_id']