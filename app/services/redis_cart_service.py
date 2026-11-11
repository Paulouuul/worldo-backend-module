# app/services/redis_cart_service.py
# Regras de negócio do carrinho de compras (armazenado no Redis): adicionar, remover, alterar
# quantidade, limpar, resumir e sincronizar preço/estoque com o PostgreSQL antes do checkout.

from app.repositories.cart_repository import CartRepository
from app.entities.cart_entity import CartEntity
from app.entities.cart_item_entity import CartItemEntity
from app.services.listing_service import ListingService
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RedisCartService:
    """Serviço do carrinho: aplica limites de negócio (50 anúncios, 99 unidades por item) e usa o
    CartRepository (Redis) e o ListingService (PostgreSQL).
    """
    
    # Limites de negócio
    MAX_ITEMS_PER_CART = 50
    MAX_QUANTITY_PER_ITEM = 99
    
    def __init__(self):
        """Cria o repositório do carrinho e o serviço de anúncios."""
        self.repository = CartRepository()
        self.listing_service = ListingService() 
    
    def get_cart(self, user_id: str) -> CartEntity:
        """Retorna o carrinho salvo do usuário ou um carrinho vazio novo (não persistido)."""
        cart = self.repository.find_by_user_id(user_id)
        
        if not cart:
            logger.info(f"Criando novo carrinho para usuário: {user_id}")
            cart = CartEntity(user_id=user_id)
        
        return cart
    

    
    def get_item_quantity(self, user_id: str, listing_id: str) -> int:
        """Quantidade do anúncio no carrinho do usuário (0 se não estiver nele)."""
        cart = self.get_cart(user_id)
        
        for item in cart.items:
            if item.listing_id == listing_id:
                return item.quantity
        
        return 0

    def get_cart_item(self, user_id: str, listing_id: str) -> Optional[CartItemEntity]:
        """Item do carrinho referente ao anúncio, ou None."""
        cart = self.get_cart(user_id)
        
        for item in cart.items:
            if item.listing_id == listing_id:
                return item
        
        return None
    
    def add_item(self, user_id: str, item_data: Dict[str, Any]) -> Optional[CartEntity]:
        """Adiciona o anúncio ao carrinho (somando à quantidade existente) e salva no Redis.

        Retorna None se o carrinho já tem 50 anúncios, se a quantidade passa de 99, se o total
        ultrapassa `max_quantity` (estoque informado) ou se a gravação falhar.
        """
        
        cart = self.get_cart(user_id)
            
        # Validação: limite de itens diferentes
        if cart.unique_items_count >= self.MAX_ITEMS_PER_CART:
            logger.warning(f"Carrinho do usuário {user_id} atingiu limite de {self.MAX_ITEMS_PER_CART} itens")
            return None
        
        # Validação: quantidade máxima por item
        quantity = item_data.get("quantity", 1)
        if quantity > self.MAX_QUANTITY_PER_ITEM:
            logger.warning(f"Quantidade {quantity} excede o limite de {self.MAX_QUANTITY_PER_ITEM}")
            return None
        
        # Item já existente para o mesmo anúncio
        existing_item = None
        for item in cart.items:
            if item.listing_id == item_data["listing_id"]:
                existing_item = item
                break
        
        # Quantidade final após a adição
        max_quantity = item_data.get("max_quantity", 0)
        if existing_item:
            new_quantity = existing_item.quantity + quantity
        else:
            new_quantity = quantity
        
        # Não pode exceder o estoque informado
        if max_quantity > 0 and new_quantity > max_quantity:
            logger.warning(
                f"Quantidade {new_quantity} excede o estoque disponível {max_quantity} "
                f"para o item '{item_data['name']}'"
            )
            return None
        
        # Criar item
        new_item = CartItemEntity(
            listing_id=item_data["listing_id"],
            frame_id=item_data["frame_id"],
            name=item_data["name"],
            price=item_data["price"],
            quantity=quantity,
            seller_id=item_data["seller_id"],
            seller_name=item_data["seller_name"],
            image_url=item_data.get("image_url", ""),
            thumbnail_url=item_data.get("thumbnail_url", ""),
            max_quantity=item_data.get("max_quantity", 0)
        )
        
        cart.add_item(new_item)
        if not self.repository.save(cart):
            logger.error(f"Falha ao salvar carrinho no Redis: {user_id}")
            return None
        
        logger.info(f"Item adicionado ao carrinho do usuário {user_id}: {new_item.name}")
        return cart
    
    def remove_item(self, user_id: str, item_id: str) -> Optional[CartEntity]:
        """Remove o item do carrinho; se o carrinho ficar vazio, apaga a chave no Redis.

        Retorna None se o item não existir ou se a gravação falhar.
        """
        cart = self.get_cart(user_id)
        
        if cart.remove_item(item_id):
            if not cart.items:
                if not self.repository.delete(user_id):
                    logger.error(f"Falha ao deletar carrinho vazio: {user_id}")
                    return None
            else:
                if not self.repository.save(cart):
                    logger.error(f"Falha ao salvar carrinho após remoção: {user_id}")
                    return None
            logger.info(f"Item {item_id} removido do carrinho do usuário {user_id}")
            return cart
        
        logger.warning(f"Item {item_id} não encontrado no carrinho do usuário {user_id}")
        return None
    
    def update_quantity(self, user_id: str, item_id: str, quantity: int) -> Optional[CartEntity]:
        """Define a quantidade do item (limitada a 0–99; zero remove o item) e salva.

        Retorna None se o item não existir ou se a gravação falhar.
        """
        if quantity < 0:
            quantity = 0
        
        if quantity > self.MAX_QUANTITY_PER_ITEM:
            logger.warning(f"Quantidade {quantity} excede o limite de {self.MAX_QUANTITY_PER_ITEM}")
            quantity = self.MAX_QUANTITY_PER_ITEM
        
        cart = self.get_cart(user_id)
        
        if cart.update_quantity(item_id, quantity):
            if not self.repository.save(cart):
                logger.error(f"Falha ao salvar carrinho após atualização: {user_id}")
                return None
            
            logger.info(f"Quantidade do item {item_id} atualizada para {quantity}")
            return cart
        
        logger.warning(f"Item {item_id} não encontrado no carrinho do usuário {user_id}")
        return None
    
    def clear_cart(self, user_id: str) -> CartEntity:
        """Esvazia o carrinho apagando a chave no Redis. Retorna None se a remoção falhar."""
        cart = self.get_cart(user_id)
        cart.clear()
        if not self.repository.delete(user_id):
            logger.error(f"Falha ao esvaziar carrinho: {user_id}")
            return None
        
        logger.info(f"Carrinho do usuário {user_id} foi esvaziado")
        return cart
    
    def delete_cart(self, user_id: str) -> bool:
        """Apaga o carrinho do Redis. Retorna True se havia carrinho."""
        result = self.repository.delete(user_id)
        
        if result:
            logger.info(f"Carrinho do usuário {user_id} foi removido do Redis")
        else:
            logger.warning(f"Carrinho do usuário {user_id} não existia para remover")
        
        return result
    
    def get_cart_summary(self, user_id: str) -> Dict[str, Any]:
        """Resumo do carrinho: totais e lista simplificada dos itens."""
        cart = self.get_cart(user_id)
        
        return {
            "user_id": cart.user_id,
            "total_items": cart.total_items,
            "total_price": cart.total_price,
            "unique_items_count": cart.unique_items_count,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "total": item.total(),
                    "seller_name": item.seller_name,
                    "image_url": item.image_url
                }
                for item in cart.items
            ]
        }
    

    async def sync_with_postgres(self, user_id: str) -> CartEntity:
        """Atualiza os itens do carrinho com preço, estoque e nome atuais do PostgreSQL.

        Remove itens cujo anúncio não existe mais ou está sem estoque e reduz quantidades acima
        do estoque. O carrinho é regravado no Redis apenas quando algum item é removido.
        """
        cart = self.get_cart(user_id)
        
        if not cart.items:
            return cart
        
        # Busca todos os anúncios do carrinho em uma única consulta
        listing_ids = [item.listing_id for item in cart.items]
        listings = await self.listing_service.get_listings_batch(listing_ids)
        
        items_to_remove = []
        
        for item in cart.items:
            listing = listings.get(item.listing_id)
            
            if not listing or listing['quantity'] <= 0:
                items_to_remove.append(item.id)
                logger.info(f"Item {item.name} sem estoque, será removido")
                continue
            
            # Preço, estoque e nome atuais do anúncio
            old_price = item.price
            item.price = listing['priceCoins']
            item.max_quantity = listing['quantity']
            item.name = listing['frame_name']
            
            if old_price != item.price:
                logger.info(f"Preço de {item.name} alterado: {old_price} → {item.price}")
            
            # Reduz a quantidade ao estoque disponível
            if item.quantity > item.max_quantity:
                logger.info(f"Ajustando quantidade de {item.name} de {item.quantity} para {item.max_quantity}")
                item.quantity = item.max_quantity
        
        # Remove itens sem estoque ou com anúncio inativo
        for item_id in items_to_remove:
            cart.remove_item(item_id)
        
        if items_to_remove:
            if not self.repository.save(cart):
                logger.error(f"Falha ao sincronizar carrinho: {user_id}")
        
        return cart
    
    async def validate_for_checkout(self, user_id: str) -> Dict[str, Any]:
        """Sincroniza o carrinho e verifica se pode ir para o checkout.

        Retorna {valid, error, cart}; `error` é uma mensagem única para carrinho vazio ou itens
        indisponíveis.
        """
        cart = await self.sync_with_postgres(user_id)
        
        if not cart.items:
            return {
                "valid": False,
                "error": "Seu carrinho está vazio",
                "cart": cart
            }
        
        # Algum item sem estoque ou acima do estoque
        has_errors = False
        for item in cart.items:
            if item.max_quantity == 0 or item.quantity > item.max_quantity:
                has_errors = True
                break
        
        if not has_errors:
            return {
                "valid": True,
                "error": None,
                "cart": cart
            }
        
        return {
            "valid": False,
            "error": "Alguns itens do seu carrinho estão indisponíveis ou com quantidade excedida. Não foi possível completar a compra.",
            "cart": cart
        }
    
    async def get_cart_with_details(self, user_id: str) -> Dict[str, Any]:
        """Sincroniza o carrinho e retorna os itens com imagem, raridade e disponibilidade do
        anúncio.
        """
        cart = await self.sync_with_postgres(user_id)
        
        if not cart.items:
            return {
                "user_id": cart.user_id,
                "total_items": 0,
                "total_price": 0,
                "unique_items_count": 0,
                "items": [],
                "updated_at": cart.updated_at
            }
        
        # Busca todos os anúncios do carrinho em uma única consulta
        listing_ids = [item.listing_id for item in cart.items]
        listings = await self.listing_service.get_listings_batch(listing_ids)
        
        items_with_details = []
        for item in cart.items:
            listing = listings.get(item.listing_id)
            
            items_with_details.append({
                "id": item.id,
                "listing_id": item.listing_id,
                "frame_id": item.frame_id,
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity,
                "seller_id": item.seller_id,
                "seller_name": item.seller_name,
                "image_url": item.image_url,
                "max_quantity": item.max_quantity,
                "total": item.total(),
                "frame": {
                    "imageUrl": listing['imageUrl'] if listing else None,
                    "thumbnailUrl": listing['thumbnailUrl'] if listing else None,
                    "rarity": listing['rarity'] if listing else None
                } if listing else None,
                "in_stock": listing is not None and listing['quantity'] > 0
            })
        
        return {
            "user_id": cart.user_id,
            "total_items": cart.total_items,
            "total_price": cart.total_price,
            "unique_items_count": cart.unique_items_count,
            "items": items_with_details,
            "updated_at": cart.updated_at
        }
    
    def get_cart_ttl(self, user_id: str) -> int:
        """Segundos restantes até o carrinho expirar no Redis."""
        return self.repository.get_ttl(user_id)
