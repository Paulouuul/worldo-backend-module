# app/api/routes/test/auth_test.py
# Rotas de diagnóstico de autenticação (/auth_test/test/auth/*, sob WORLDO_API_PREFIX):
# inspecionam o header Authorization e o JWT recebido. Expõem headers e claims; uso restrito a
# desenvolvimento.

from typing import Annotated
from fastapi import APIRouter, Depends, Request
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.auth.schemas import UserInfo

router = APIRouter(prefix="/test/auth", tags=["test"])


@router.get("/debug-token")
async def debug_token(request: Request):
    """GET /auth_test/test/auth/debug-token — retorna o header Authorization e todos os headers
    recebidos.
    """
    auth_header = request.headers.get("Authorization")
    
    return {
        "has_auth_header": bool(auth_header),
        "auth_header": auth_header,
        "all_headers": dict(request.headers)
    }


@router.get("/debug-jwt")
async def debug_jwt(request: Request):
    """GET /auth_test/test/auth/debug-jwt — decodifica o JWT sem e com verificação de assinatura e
    retorna as claims.
    """
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
    
    # Claims sem verificar a assinatura
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
    
    # Claims com verificação de assinatura (WORLDO_JWT_SECRET)
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
    """GET /auth_test/test/auth/me — retorna os dados do usuário autenticado pelo JWT."""
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
