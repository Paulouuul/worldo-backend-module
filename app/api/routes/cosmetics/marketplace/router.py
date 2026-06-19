from fastapi import APIRouter
from .cart.router import router as cart_router

router = APIRouter()
router.include_router(cart_router, prefix="/cart")