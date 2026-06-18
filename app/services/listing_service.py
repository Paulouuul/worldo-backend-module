# app/services/listing_service.py
from app.core.database import db  # ← Instância global
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ListingService:
    """Serviço para buscar dados do PostgreSQL usando DatabaseManager"""
    
    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca um listing no PostgreSQL pelo ID.
        
        Returns:
            Dict com: id, quantity, priceCoins, frame_name, imageUrl, thumbnailUrl, rarity, seller_name
        """
        try:
            query = """
                SELECT 
                    cl.id,
                    cl.quantity,
                    cl.priceCoins,
                    cf.name as frame_name,
                    cf.imageUrl,
                    cf.thumbnailUrl,
                    cf.rarity,
                    u.name as seller_name
                FROM cosmetic_listing cl
                JOIN cosmetic_frame cf ON cf.id = cl.frame_id
                JOIN users u ON u.id = cl.seller_id
                WHERE cl.id = $1 
                  AND cl.is_active = true
            """
            
            # Usa o DatabaseManager
            result = await db.fetch_one(query, listing_id)
            
            if result:
                logger.info(f"Listing {listing_id} encontrado no PostgreSQL")
                return result
            
            logger.warning(f"Listing {listing_id} não encontrado no PostgreSQL")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar listing {listing_id}: {e}")
            return None
    
    async def get_listings_batch(self, listing_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Busca múltiplos listings de uma vez (mais eficiente).
        
        Returns:
            Dict com listing_id como chave e dados como valor
        """
        if not listing_ids:
            return {}
        
        try:
            # Cria placeholders para o IN clause
            placeholders = ','.join([f'${i+1}' for i in range(len(listing_ids))])
            
            query = f"""
                SELECT 
                    cl.id,
                    cl.quantity,
                    cl.priceCoins,
                    cf.name as frame_name,
                    cf.imageUrl,
                    cf.thumbnailUrl,
                    cf.rarity,
                    u.name as seller_name
                FROM cosmetic_listing cl
                JOIN cosmetic_frame cf ON cf.id = cl.frame_id
                JOIN users u ON u.id = cl.seller_id
                WHERE cl.id IN ({placeholders})
                  AND cl.is_active = true
            """
            
            # Usa o DatabaseManager
            results = await db.fetch_all(query, *listing_ids)
            
            # Converte para dicionário
            listings_dict = {}
            for row in results:
                listings_dict[row['id']] = row
            
            logger.info(f"{len(listings_dict)} listings encontrados no PostgreSQL")
            return listings_dict
            
        except Exception as e:
            logger.error(f"Erro ao buscar listings em batch: {e}")
            return {}
    
    async def get_listing_with_lock(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca listing com LOCK (FOR UPDATE) para operações críticas.
        Usado durante o checkout para evitar race conditions.
        """
        try:
            query = """
                SELECT 
                    cl.id,
                    cl.quantity,
                    cl.priceCoins,
                    cf.name as frame_name,
                    cf.imageUrl,
                    cf.thumbnailUrl,
                    cf.rarity,
                    u.name as seller_name
                FROM cosmetic_listing cl
                JOIN cosmetic_frame cf ON cf.id = cl.frame_id
                JOIN users u ON u.id = cl.seller_id
                WHERE cl.id = $1 
                  AND cl.is_active = true
                FOR UPDATE
            """
            
            # Usa transação para o LOCK
            async with db.transaction() as conn:
                # Usa a conexão da transação diretamente
                row = await conn.fetchrow(query, listing_id)
                return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar listing com lock {listing_id}: {e}")
            return None
    
    async def update_listing_quantity(self, listing_id: str, new_quantity: int) -> bool:
        """
        Atualiza a quantidade de um listing no PostgreSQL.
        Usado durante o checkout.
        """
        try:
            query = """
                UPDATE cosmetic_listing 
                SET quantity = $1, updatedAt = NOW()
                WHERE id = $2
            """
            
            # Usa o DatabaseManager
            result = await db.execute(query, new_quantity, listing_id)
            
            # asyncpg retorna "UPDATE <count>" ou "UPDATE 0"
            if result and result.startswith("UPDATE"):
                count = int(result.split()[1]) if len(result.split()) > 1 else 0
                if count > 0:
                    logger.info(f"Listing {listing_id} atualizado: quantity = {new_quantity}")
                    return True
            
            logger.warning(f"Listing {listing_id} não encontrado para atualizar")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar listing {listing_id}: {e}")
            return False