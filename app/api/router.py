# app/api/router.py
# Router raiz da API: agrupa as rotas protegidas (exigem JWT) sob o prefixo configurado —
# /auth_test, /profile e /cosmetics.

from fastapi import APIRouter, Depends
from app.core.config import settings
from app.api.routes.test.auth_test import router as auth_test
from app.api.routes.profile.router import router as profile_router
from app.api.routes.cosmetics.router import router as cosmetic_router
from app.auth.dependencies import get_current_user

# Router exportado para a aplicação
api_router = APIRouter()

# Rotas protegidas: todas passam por get_current_user
protected_router = APIRouter(
    prefix=f"{settings.api_prefix}",
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

protected_router.include_router(
    cosmetic_router, 
    prefix="/cosmetics", 
    tags=["Cosmetics"]
)

api_router.include_router(protected_router)
