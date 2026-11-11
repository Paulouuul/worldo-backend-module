# app/api/routes/cosmetics/marketplace/router.py
# Router do marketplace de cosméticos: agrupa /cosmetics/marketplace/cart.

from fastapi import APIRouter
from .cart.router import router as cart_router

router = APIRouter()
router.include_router(cart_router, prefix="/cart")
