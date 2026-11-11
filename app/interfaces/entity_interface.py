# app/interfaces/entity_interface.py
# Classe base das entidades: gera id/created_at/updated_at e oferece conversão para dict,
# atualização protegida e criação a partir de dict.

from pydantic import BaseModel
from typing import List, Any, Dict
from datetime import datetime, timezone
import uuid

class EntityInterface(BaseModel):
    """Base das entidades com id (UUID) e datas de criação/atualização em UTC sem fuso."""
    
    id: str = None
    created_at: datetime = None
    updated_at: datetime = None
    
    class Config:
        """Configuração do Pydantic: aceita tipos arbitrários e serializa datetime em ISO 8601."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __init__(self, **data):
        """Preenche id, created_at e updated_at quando não informados."""
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
        """Campos que `update()` nunca altera."""
        return ['id', 'created_at']
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade em dict serializável (datetimes em ISO, listas de entidades
        convertidas).
        """
        data = self.model_dump()
        
        # Converte datetimes e listas de entidades para tipos serializáveis
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
        """Aplica os campos de `data` (exceto os protegidos) e atualiza updated_at."""
        protected = self.list_fields_to_not_update()
        
        for key, value in data.items():
            if key not in protected and hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return self
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityInterface":
        """Cria a entidade a partir de um dicionário."""
        return cls(**data)
