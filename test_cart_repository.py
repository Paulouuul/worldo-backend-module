# test_cart_repository.py
# Script manual de teste do CartRepository contra o Redis local: cria, salva, lê, verifica e
# remove um carrinho de exemplo. Executar com: python test_cart_repository.py

import sys
sys.path.insert(0, ".")

from app.repositories.cart_repository import CartRepository
from app.entities.cart_entity import CartEntity
from app.entities.cart_item_entity import CartItemEntity

def test_repository():
    """Executa o fluxo completo do CartRepository e imprime o resultado de cada etapa."""
    print("=== Testando CartRepository ===\n")
    
    repo = CartRepository()
    user_id = "test_user_123"
    
    # Cria o carrinho
    print("1. Criando carrinho...")
    cart = CartEntity(user_id=user_id)
    
    # Adiciona um item
    print("2. Adicionando item...")
    item = CartItemEntity(
        listing_id="listing_456",
        frame_id="frame_789",
        name="Moldura Aurora",
        price=100,
        quantity=2,
        seller_id="seller_999",
        seller_name="João Vendedor"
    )
    cart.add_item(item)
    
    # Salva no Redis
    print("3. Salvando no Redis...")
    result = repo.save(cart)
    print(f"   Salvo: {result}")
    
    if result:
        # Lê do Redis
        print("4. Buscando do Redis...")
        found = repo.find_by_user_id(user_id)
        if found:
            print(f"   ✅ Carrinho encontrado!")
            print(f"   ID: {found.id}")
            print(f"   Usuário: {found.user_id}")
            print(f"   Total de itens: {found.total_items}")
            print(f"   Preço total: {found.total_price}")
            print(f"   Produtos diferentes: {found.unique_items_count}")
            
            if found.items:
                print(f"\n   Itens no carrinho:")
                for i, item in enumerate(found.items, 1):
                    print(f"     {i}. {item.name} - {item.quantity}x - {item.total()} moedas")
        else:
            print("   ❌ Carrinho não encontrado!")
        
        # Verifica existência
        print("\n5. Verificando existência...")
        exists = repo.exists(user_id)
        print(f"   Existe: {exists}")
        
        # Remove
        print("\n6. Deletando carrinho...")
        deleted = repo.delete(user_id)
        print(f"   Deletado: {deleted}")
    else:
        print("   ❌ Falha ao salvar!")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    test_repository()
