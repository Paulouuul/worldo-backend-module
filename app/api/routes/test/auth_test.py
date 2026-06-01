from typing import Annotated
from fastapi import APIRouter, Depends, Request
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.auth.schemas import UserInfo

router = APIRouter(prefix="/test/auth", tags=["test"])


@router.get("/debug-token")
async def debug_token(request: Request):
    """Retorna o header Authorization para debug"""
    auth_header = request.headers.get("Authorization")
    
    return {
        "has_auth_header": bool(auth_header),
        "auth_header": auth_header,
        "all_headers": dict(request.headers)
    }


@router.get("/debug-jwt")
async def debug_jwt(request: Request):
    """Tenta decodificar o JWT e retorna o resultado"""
    from jose import jwt
    from app.core.config import settings
    
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        return {"error": "No Authorization header"}
    
    if not auth_header.startswith("Bearer "):
        return {"error": "Invalid Authorization format"}
    
    token = auth_header.replace("Bearer ", "")
    
    result = {
        "token_received": True,
        "token_length": len(token),
        "token_preview": token[:50] + "...",
    }
    
    # 🔥 CORRIGIDO: Alterado para get_unverified_claims para evitar o erro de falta de chave
    try:
        payload = jwt.get_unverified_claims(token)
        result["decoded_without_verify"] = {
            "success": True,
            "payload": payload
        }
    except Exception as e:
        result["decoded_without_verify"] = {
            "success": False,
            "error": str(e)
        }
    
    # Tentar decodificar com verificação de assinatura (Continua igual, funcionando perfeitamente)
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        result["decoded_with_verify"] = {
            "success": True,
            "payload": payload
        }
    except Exception as e:
        result["decoded_with_verify"] = {
            "success": False,
            "error": str(e)
        }
    
    return result


@router.get("/me")
async def test_get_current_user(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """Testa autenticação obrigatória"""
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "public_id": user.public_id,
            "email": user.email,
            "name": user.name,
            "username": user.username
        }
    }