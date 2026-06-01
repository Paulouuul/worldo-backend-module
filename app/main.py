import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.test.auth_test import router as auth_test_router
from app.api.routes.cosmetic.marketplace.cart.router import router as cart_router

# Configura logging ANTES de usar
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("=" * 80)
        logger.info("🚀 SERVER STARTED - Available Routes:")
        logger.info("=" * 80)
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                methods = ", ".join(sorted(route.methods)) if route.methods else "N/A"
                logger.info(f"  {methods:20} {route.path}")
            elif hasattr(route, "path") and hasattr(route, "name"):
                logger.info(f"  {'WS':20} {route.path}")
        logger.info("=" * 80)
        yield
        logger.info("👋 SERVER SHUTDOWN")

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em desenvolvimento, permite todos
        allow_credentials=True,
        allow_methods=["*"],  # Permite TODOS os métodos (GET, POST, PUT, DELETE, OPTIONS)
        allow_headers=["*"],  # Permite TODOS os headers
    )

    # 🔥 Registra os routers (adicionar conforme criar)
    app.include_router(auth_test_router)
    # app.include_router(cart_router)  # Descomentar quando o cart estiver pronto

    return app


# Criar a instância da app
app = create_app()


# Opcional: endpoint de health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}