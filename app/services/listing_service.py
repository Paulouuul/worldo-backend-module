# app/services/listing_service.py
from app.core.database import db
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ListingService:
    """Serviço para buscar dados do PostgreSQL usando DatabaseManager"""
    
    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca um listing no PostgreSQL pelo ID.
        """
        try:
            query = """
                SELECT 
                    cl.id,
                    cl.quantity,
                    cl."priceCoins",
                    cf.name as frame_name,
                    cf."imageUrl",
                    cf."thumbnailUrl",
                    cf.rarity,
                    u.name as seller_name
                FROM cosmetic_listing cl
                JOIN cosmetic_frame cf ON cf.id = cl."frameId"
                JOIN users u ON u.id = cl."sellerId"
                WHERE cl.id = $1 
                  AND cl."isActive" = true
            """
            
            result = await db.fetch_one(query, listing_id)
            
            if result:
                logger.info(f"Listing {listing_id} encontrado no PostgreSQL")
                return dict(result)
            
            logger.warning(f"Listing {listing_id} não encontrado no PostgreSQL")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar listing {listing_id}: {e}")
            return None
    
    async def get_listings_batch(self, listing_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Busca múltiplos listings de uma vez (mais eficiente).
        """
        if not listing_ids:
            return {}
        
        try:
            placeholders = ','.join([f'${i+1}' for i in range(len(listing_ids))])
            
            query = f"""
                SELECT 
                    cl.id,
                    cl.quantity,
                    cl."priceCoins",
                    cf.name as frame_name,
                    cf."imageUrl",
                    cf."thumbnailUrl",
                    cf.rarity,
                    u.name as seller_name
                FROM cosmetic_listing cl
                JOIN cosmetic_frame cf ON cf.id = cl."frameId"
                JOIN users u ON u.id = cl."sellerId"
                WHERE cl.id IN ({placeholders})
                  AND cl."isActive" = true
            """
            
            results = await db.fetch_all(query, *listing_ids)
            
            listings_dict = {}
            for row in results:
                listings_dict[row['id']] = dict(row)
            
            logger.info(f"{len(listings_dict)} listings encontrados no PostgreSQL")
            return listings_dict
            
        except Exception as e:
            logger.error(f"Erro ao buscar listings em batch: {e}")
            return {}
    
    async def get_listing_with_lock(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca listing com LOCK (FOR UPDATE) para operações críticas.
        """
        try:
            query = """
                SELECT 
                    cl.id,
                    cl.quantity,
                    cl."priceCoins",
                    cf.name as frame_name,
                    cf."imageUrl",
                    cf."thumbnailUrl",
                    cf.rarity,
                    u.name as seller_name
                FROM cosmetic_listing cl
                JOIN cosmetic_frame cf ON cf.id = cl."frameId"
                JOIN users u ON u.id = cl."sellerId"
                WHERE cl.id = $1 
                  AND cl."isActive" = true
                FOR UPDATE
            """
            
            async with db.transaction() as conn:
                row = await conn.fetchrow(query, listing_id)
                return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar listing com lock {listing_id}: {e}")
            return None
    
    async def update_listing_quantity(self, listing_id: str, new_quantity: int) -> bool:
        """
        Atualiza a quantidade de um listing no PostgreSQL.
        """
        try:
            query = """
                UPDATE cosmetic_listing 
                SET quantity = $1, "updatedAt" = NOW()
                WHERE id = $2
            """
            
            result = await db.execute(query, new_quantity, listing_id)
            
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