# app/main.py
# Ponto de entrada da API FastAPI: cria a aplicação, inicializa o pool do PostgreSQL no startup,
# configura CORS, registra os routers e expõe o health check.

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
    """Cria e configura a aplicação FastAPI (lifespan, CORS, routers e /health)."""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Ciclo de vida da aplicação: inicializa o banco e lista as rotas no startup; registra o
        shutdown.
        """
        # Inicializa o pool de conexões do PostgreSQL
        logger.info("=" * 80)
        logger.info("INICIALIZANDO BANCO DE DADOS...")
        await db.initialize()
        logger.info("Banco de dados inicializado com sucesso!")
        logger.info("=" * 80)
        # Lista no log todas as rotas registradas (HTTP e WebSocket)
        logger.info("SERVER STARTED - Available Routes:")
        logger.info("=" * 80)
        
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                methods = ", ".join(sorted(route.methods)) if route.methods else "N/A"
                logger.info(f"  {methods:20} {route.path}")
            elif hasattr(route, "path") and hasattr(route, "name"):
                logger.info(f"  {'WS':20} {route.path}")
        
        logger.info("=" * 80)
        yield  # A aplicação atende requisições enquanto o contexto está aberto
        
        # Shutdown
        logger.info("SERVER SHUTDOWN")

    # Documentação (/docs, /redoc) só fica disponível em modo debug
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
        allow_origins=["*"],  # Aceita qualquer origem
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registrar os routers
    app.include_router(api_router)

    # Health check 
    @app.get("/health", tags=["System"])
    async def health_check():
        """GET /health — informa que a API está no ar, com nome do serviço e versão."""
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": "1.0.0"
        }
    

    return app


# Instância usada pelo uvicorn (uvicorn app.main:app --reload)
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
