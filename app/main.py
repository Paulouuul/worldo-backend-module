# app/main.py
import logging
from contextlib import asynccontextmanager
from app.core.database import db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI"""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Inicializando Banco de DADIS
        logger.info("=" * 80)
        logger.info("INICIALIZANDO BANCO DE DADOS...")
        await db.initialize()
        logger.info("Banco de dados inicializado com sucesso!")
        logger.info("=" * 80)
        # Startup Rotas
        logger.info("SERVER STARTED - Available Routes:")
        logger.info("=" * 80)
        
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                methods = ", ".join(sorted(route.methods)) if route.methods else "N/A"
                logger.info(f"  {methods:20} {route.path}")
            elif hasattr(route, "path") and hasattr(route, "name"):
                logger.info(f"  {'WS':20} {route.path}")
        
        logger.info("=" * 80)
        yield  # Aqui a aplicação roda
        
        # Shutdown
        logger.info("SERVER SHUTDOWN")

    # Criar a aplicação
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em desenvolvimento, permite todos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registrar os routers
    app.include_router(api_router)

    # Health check 
    @app.get("/health", tags=["System"])
    async def health_check():
        """Verifica se a API está funcionando"""
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": "1.0.0"
        }
    

    return app


# Criar a instância da app
app = create_app()

# Para executar: uvicorn app.main:app --reload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )