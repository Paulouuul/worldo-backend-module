# app/core/database.py
# Gerenciador do pool de conexões asyncpg com o PostgreSQL (singleton `db`) e helpers de
# consulta, transação e statements preparados.

import asyncpg
from asyncpg import Pool, Connection
from typing import Optional, AsyncGenerator, Dict, Any, List, Union
import logging
from contextlib import asynccontextmanager
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Singleton que mantém o pool de conexões asyncpg com o PostgreSQL."""
    
    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[Pool] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Retorna sempre a mesma instância (singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> None:
        """Cria o pool de conexões e testa a conexão com `SELECT version()`.

        Chamado no startup da aplicação; chamadas repetidas são ignoradas.
        """
        if self._initialized:
            logger.warning("DatabaseManager já foi inicializado")
            return
            
        try:
            logger.info(f"Conectando ao PostgreSQL: {settings.database_host}:{settings.database_port}/{settings.database_name}")
            
            self._pool = await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=settings.db_pool_min_size,
                max_size=settings.db_pool_max_size,
                max_queries=settings.db_pool_max_queries,
                timeout=settings.db_pool_timeout,
                command_timeout=60.0,
                # Identifica a aplicação no PostgreSQL e limita cada statement a 30s
                server_settings={
                    'application_name': settings.app_name,
                    'statement_timeout': '30000',  # 30 segundos
                }
            )
            
            # Testa a conexão
            async with self._pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Conectado ao PostgreSQL: {version[:50]}...")
            
            self._initialized = True
            logger.info(f"Pool de conexões inicializado (min={settings.db_pool_min_size}, max={settings.db_pool_max_size})")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
            raise
    
    async def close(self) -> None:
        """Fecha o pool de conexões. Chamado no shutdown da aplicação."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("Pool de conexões fechado")
    
    @property
    def pool(self) -> Pool:
        """Pool de conexões ativo. Lança RuntimeError se `initialize()` ainda não rodou."""
        if not self._pool or not self._initialized:
            raise RuntimeError("DatabaseManager não foi inicializado. Chame await db.initialize() primeiro.")
        return self._pool
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Connection, None]:
        """Empresta uma conexão do pool durante o bloco `async with`.

        Exemplo:
            async with db.acquire() as conn:
                result = await conn.fetch("SELECT * FROM users")
        """
        async with self.pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        """Abre uma conexão com transação: commit ao final do bloco, rollback em caso de exceção.

        Exemplo:
            async with db.transaction() as conn:
                await conn.execute("INSERT INTO users ...")
                await conn.execute("UPDATE accounts ...")
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    # Helpers de consulta
    
    async def fetch_one(
        self, 
        query: str, 
        *args, 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Executa a query e retorna a primeira linha como dicionário (ou None).

        Exemplo:
            user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args, **kwargs)
            return dict(row) if row else None
    
    async def fetch_all(
        self, 
        query: str, 
        *args, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Executa a query e retorna todas as linhas como lista de dicionários.

        Exemplo:
            users = await db.fetch_all("SELECT * FROM users WHERE active = $1", True)
        """
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args, **kwargs)
            return [dict(row) for row in rows]
    
    async def fetch_value(
        self, 
        query: str, 
        *args, 
        **kwargs
    ) -> Any:
        """Executa a query e retorna a primeira coluna da primeira linha.

        Exemplo:
            count = await db.fetch_value("SELECT COUNT(*) FROM users WHERE active = $1", True)
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, **kwargs)
    
    async def execute(
        self, 
        query: str, 
        *args, 
        **kwargs
    ) -> str:
        """Executa um comando sem retorno de linhas (INSERT, UPDATE, DELETE) e retorna o status do
        PostgreSQL.

        Exemplo:
            status = await db.execute("INSERT INTO users (id, name) VALUES ($1, $2)", user_id,
            name)
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    async def execute_many(
        self, 
        query: str, 
        params_list: List[tuple]
    ) -> None:
        """Executa o mesmo comando para cada tupla de parâmetros (insert/update em lote).

        Exemplo:
            await db.execute_many("INSERT INTO users (id, name) VALUES ($1, $2)", [(1, "João"),
            (2, "Maria")])
        """
        async with self.acquire() as conn:
            await conn.executemany(query, params_list)
    
    async def fetch_one_prepared(
        self,
        name: str,
        query: str,
        *args,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Prepara a query com o nome informado e retorna a primeira linha como dicionário (ou
        None).
        """
        async with self.acquire() as conn:
            stmt = await conn.prepare(query, name=name)
            row = await stmt.fetchrow(*args, **kwargs)
            return dict(row) if row else None
    
    async def execute_prepared(
        self,
        name: str,
        query: str,
        *args,
        **kwargs
    ) -> str:
        """Prepara o comando com o nome informado e o executa, retornando o status do PostgreSQL."""
        async with self.acquire() as conn:
            stmt = await conn.prepare(query, name=name)
            return await stmt.execute(*args, **kwargs)
    
    async def prepare_statement(self, name: str, query: str) -> None:
        """Prepara uma statement nomeada em uma conexão do pool."""
        async with self.acquire() as conn:
            await conn.prepare(query, name=name)
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Retorna o estado do pool: tamanho atual, limites e se está fechado."""
        if not self._pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "connected",
            "pool_size": self._pool.get_size(),
            "max_size": settings.db_pool_max_size,
            "min_size": settings.db_pool_min_size,
            "is_closed": self._pool.is_closed(),
        }
    
    # Verificação de saúde
    
    async def health_check(self) -> bool:
        """Retorna True se o banco responde a `SELECT 1`."""
        try:
            result = await self.fetch_value("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False


# Instância global para uso em toda a aplicação
db = DatabaseManager()


# Funções de ciclo de vida do pool global

async def init_db():
    """Inicializa o pool global `db`."""
    await db.initialize()


async def close_db():
    """Fecha o pool global `db`."""
    await db.close()
