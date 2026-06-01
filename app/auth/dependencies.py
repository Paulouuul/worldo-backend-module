# app/auth/dependencies.py
import logging
from typing import Annotated, Optional

from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.auth.schemas import UserInfo
from app.core.config import settings
from jose.exceptions import JWTError, ExpiredSignatureError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_current_user(
    token: Annotated[Optional[str], Depends(security)] = None,
) -> UserInfo:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário não autenticado. Por favor, faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        logger.warning("Tentativa de acesso sem token")
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Por favor, faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning(f"Token inválido: {e}")
        raise credentials_exception

    if not payload:
        raise credentials_exception

    user_id = payload.get("sub") or payload.get("id")
    email = payload.get("email")
    
    if not user_id or not email:
        logger.warning(f"Token com dados insuficientes: {payload}")
        raise credentials_exception

    logger.info(f"Usuário autenticado: {user_id} - {payload.get('username') or email}")

    return UserInfo(
        id=user_id,
        public_id=payload.get("publicId") or payload.get("public_id") or user_id,
        email=email,
        name=payload.get("name") or email.split('@')[0],
        username=payload.get("username") or email.split('@')[0],
        avatar=payload.get("avatar"),
        cover_image=payload.get("coverImage"),
        bio=payload.get("bio", ""),
        location=payload.get("location", ""),
        website=payload.get("website", ""),
        provider=payload.get("provider", "credentials"),
        is_oauth=payload.get("isOAuth", False),
        has_password=payload.get("hasPassword", True),
        equipped_frame=payload.get("equippedFrame"),
    )


def get_current_user_optional(
    token: Annotated[Optional[str], Depends(security)] = None,
) -> Optional[UserInfo]:
    if not token:
        return None
    try:
        return get_current_user(token)
    except HTTPException:
        return None


require_auth = Depends(get_current_user)
require_optional_auth = Depends(get_current_user_optional)