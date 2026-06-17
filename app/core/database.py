# app/core/database.py
import asyncpg
from asyncpg import Pool, Connection
from typing import Optional, AsyncGenerator, Dict, Any, List, Union
import logging
from contextlib import asynccontextmanager
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gerenciador singleton do pool de conexões PostgreSQL
    """
    
    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[Pool] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> None:
        """
        Inicializa o pool de conexões.
        Deve ser chamado durante o startup da aplicação.
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
                # Configurações adicionais para produção
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
        """
        Fecha o pool de conexões.
        Deve ser chamado durante o shutdown da aplicação.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("Pool de conexões fechado")
    
    @property
    def pool(self) -> Pool:
        """Retorna o pool de conexões (lança erro se não inicializado)"""
        if not self._pool or not self._initialized:
            raise RuntimeError("DatabaseManager não foi inicializado. Chame await db.initialize() primeiro.")
        return self._pool
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Connection, None]:
        """
        Adquire uma conexão do pool.
        
        Exemplo:
            async with db.acquire() as conn:
                result = await conn.fetch("SELECT * FROM users")
        """
        async with self.pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        """
        Executa operações dentro de uma transação.
        Commit automático se não houver erro, rollback em caso de exceção.
        
        Exemplo:
            async with db.transaction() as conn:
                await conn.execute("INSERT INTO users ...")
                await conn.execute("UPDATE accounts ...")
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    # ============ MÉTODOS AUXILIARES ============
    
    async def fetch_one(
        self, 
        query: str, 
        *args, 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Executa uma query e retorna a primeira linha como dicionário.
        
        Exemplo:
            user = await db.fetch_one(
                "SELECT * FROM users WHERE id = $1", 
                user_id
            )
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
        """
        Executa uma query e retorna todas as linhas como lista de dicionários.
        
        Exemplo:
            users = await db.fetch_all(
                "SELECT * FROM users WHERE active = $1", 
                True
            )
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
        """
        Executa uma query e retorna um único valor (primeira coluna da primeira linha).
        
        Exemplo:
            count = await db.fetch_value(
                "SELECT COUNT(*) FROM users WHERE active = $1", 
                True
            )
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, **kwargs)
    
    async def execute(
        self, 
        query: str, 
        *args, 
        **kwargs
    ) -> str:
        """
        Executa uma query que não retorna dados (INSERT, UPDATE, DELETE).
        Retorna o status da execução.
        
        Exemplo:
            status = await db.execute(
                "INSERT INTO users (id, name) VALUES ($1, $2)", 
                user_id, 
                name
            )
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    async def execute_many(
        self, 
        query: str, 
        params_list: List[tuple]
    ) -> None:
        """
        Executa a mesma query com múltiplos parâmetros (batch insert/update).
        
        Exemplo:
            users = [(1, "João"), (2, "Maria")]
            await db.execute_many(
                "INSERT INTO users (id, name) VALUES ($1, $2)",
                users
            )
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
        """
        Executa uma query preparada (melhor performance para queries repetidas).
        
        Exemplo:
            # Preparar (uma vez)
            await db.prepare_statement("get_user", "SELECT * FROM users WHERE id = $1")
            
            # Executar (múltiplas vezes)
            user = await db.fetch_one_prepared("get_user", user_id)
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
        """
        Executa uma query preparada que não retorna dados.
        
        Exemplo:
            # Preparar (uma vez)
            await db.prepare_statement("update_user", "UPDATE users SET name = $2 WHERE id = $1")
            
            # Executar (múltiplas vezes)
            status = await db.execute_prepared("update_user", user_id, new_name)
        """
        async with self.acquire() as conn:
            stmt = await conn.prepare(query, name=name)
            return await stmt.execute(*args, **kwargs)
    
    async def prepare_statement(self, name: str, query: str) -> None:
        """
        Pré-prepara uma statement para uso futuro.
        Útil para otimizar queries executadas frequentemente.
        """
        async with self.acquire() as conn:
            await conn.prepare(query, name=name)
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o pool de conexões"""
        if not self._pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "connected",
            "pool_size": self._pool.get_size(),
            "max_size": settings.db_pool_max_size,
            "min_size": settings.db_pool_min_size,
            "is_closed": self._pool.is_closed(),
        }
    
    # ============ MÉTODOS DE TESTE ============
    
    async def health_check(self) -> bool:
        """
        Verifica se o banco de dados está respondendo.
        Útil para health checks da aplicação.
        """
        try:
            result = await self.fetch_value("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False


# Instância global para uso em toda a aplicação
db = DatabaseManager()


# ============ FUNÇÕES DE LIFECYCLE ============

async def init_db():
    """Inicializa o banco de dados (chamar no startup)"""
    await db.initialize()


async def close_db():
    """Fecha o banco de dados (chamar no shutdown)"""
    await db.close()