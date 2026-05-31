# test_repository.py
import sys
sys.path.insert(0, ".")

from app.repositories.cart_repository import CartRepository
from app.entities.cart_entity import CartEntity
from app.entities.cart_item_entity import CartItemEntity

def test_repository():
    print("=== Testando CartRepository ===\n")
    
    repo = CartRepository()
    user_id = "test_user_123"
    
    # 1. Criar carrinho
    print("1. Criando carrinho...")
    cart = CartEntity(user_id=user_id)
    
    # 2. Adicionar item
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
    
    # 3. Salvar
    print("3. Salvando no Redis...")
    result = repo.save(cart)
    print(f"   Salvo: {result}")
    
    if result:
        # 4. Buscar
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
        
        # 5. Verificar existência
        print("\n5. Verificando existência...")
        exists = repo.exists(user_id)
        print(f"   Existe: {exists}")
        
        # 6. Deletar
        print("\n6. Deletando carrinho...")
        deleted = repo.delete(user_id)
        print(f"   Deletado: {deleted}")
    else:
        print("   ❌ Falha ao salvar!")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    test_repository()