# app/api/router.py
from fastapi import APIRouter, Depends

from app.api.routes.test.auth_test import router as auth_test
from app.api.routes.profile import router as profile_router
from app.auth.dependencies import get_current_user

# Router principal
api_router = APIRouter()

# ============================================
# Rotas Protegidas (Precisa de Autenticação)
# ============================================
protected_router = APIRouter(
    prefix="/api/py",
    dependencies=[Depends(get_current_user)],
)

protected_router.include_router(
    auth_test, 
    prefix="/auth_test", 
    tags=["AuthTest"]
)
protected_router.include_router(
    profile_router, 
    prefix="/profile", 
    tags=["Profile"]
)

# Rotas Públicas (Não Precisa de Autenticação)
auth_router_public = APIRouter(
    prefix="/api/py/auth",
    tags=["Authentication"]
)

api_router.include_router(protected_router)
api_router.include_router(auth_router_public)