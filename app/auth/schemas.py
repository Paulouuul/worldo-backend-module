# app/auth/schemas.py
# Schemas de autenticação: dados do usuário extraídos do JWT emitido pelo Next.js.

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class UserInfo(BaseModel):
    """Usuário autenticado. Aceita os nomes em camelCase do token (publicId, coverImage...) e em
    snake_case.
    """
    id: str
    public_id: str = Field(alias="publicId")
    email: str 
    name: str
    username: str
    avatar: Optional[str] = None
    cover_image: Optional[str] = Field(default=None, alias="coverImage")
    bio: Optional[str] = ""
    location: Optional[str] = ""
    website: Optional[str] = ""
    equipped_frame: Optional[Dict[str, Any]] = Field(default=None, alias="equippedFrame")
    
    # Flags de controle de autenticação
    provider: Optional[str] = "credentials"
    is_oauth: bool = Field(default=False, alias="isOAuth")
    has_password: bool = Field(default=True, alias="hasPassword")
    
    class Config:
        """Permite popular o modelo tanto pelo nome do campo quanto pelo alias."""
        populate_by_name = True
