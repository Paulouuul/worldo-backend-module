from fastapi import APIRouter
from .marketplace.router import router as marketplace_router
from .creation.router import router as creation_router

router = APIRouter()
router.include_router(marketplace_router, prefix="/marketplace")
router.include_router(creation_router, prefix="/creation")