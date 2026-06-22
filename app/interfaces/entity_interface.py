# app/interfaces/entity_interface.py
from pydantic import BaseModel
from typing import List, Any, Dict
from datetime import datetime, timezone
import uuid

class EntityInterface(BaseModel):
    """Interface base para todas as entidades"""
    
    id: str = None
    created_at: datetime = None
    updated_at: datetime = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __init__(self, **data):
        # Gera ID automaticamente se não existir
        if 'id' not in data or not data['id']:
            data['id'] = str(uuid.uuid4())
        
        # Gera created_at automaticamente
        if 'created_at' not in data or not data['created_at']:
            data['created_at'] = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Gera updated_at automaticamente
        if 'updated_at' not in data or not data['updated_at']:
            data['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None)
        
        super().__init__(**data)
    
    @classmethod
    def list_fields_to_not_update(cls) -> List[str]:
        """Campos que não devem ser atualizados"""
        return ['id', 'created_at']
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte entidade para dicionário (serializável para JSON)"""
        data = self.model_dump()
        
        # Converte datetime para string manualmente (garantia extra)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, list):
                # Se for lista de objetos com to_dict, converte cada um
                data[key] = [
                    item.to_dict() if hasattr(item, 'to_dict') else item 
                    for item in value
                ]
        
        return data
    
    def update(self, data: Dict[str, Any]) -> "EntityInterface":
        """Atualiza entidade protegendo campos sensíveis"""
        protected = self.list_fields_to_not_update()
        
        for key, value in data.items():
            if key not in protected and hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return self
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityInterface":
        """Cria entidade a partir de dicionário"""
        return cls(**data)