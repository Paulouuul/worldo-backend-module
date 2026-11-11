# app/api/routes/cosmetics/marketplace/cart/router.py
# Rotas do carrinho de compras do marketplace (/cosmetics/marketplace/cart/*, sob
# WORLDO_API_PREFIX). Todas exigem JWT e operam sobre o carrinho do usuário autenticado,
# armazenado no Redis.

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from .add_item_use_case.use_case import AddItemUseCase, AddItemRequest
from .get_cart_use_case.use_case import GetCartUseCase, GetCartRequest
from .remove_item_use_case.use_case import RemoveItemUseCase, RemoveItemRequest
from .update_quantity_use_case.use_case import UpdateQuantityUseCase, UpdateQuantityRequest
from .clear_cart_use_case.use_case import ClearCartUseCase
from .validate_cart_use_case.use_case import ValidateCartUseCase, ValidateCartRequest
from .sync_cart_use_case.use_case import SyncCartUseCase, SyncCartRequest
from .get_item_quantity_use_case.use_case import GetItemQuantityUseCase, GetItemQuantityRequest
from app.utils.response import success_response, error_response

router = APIRouter()

class ItemCartSchema(BaseModel):
    """Dados de um anúncio enviados pelo frontend ao adicionar ao carrinho."""
    listing_id: str
    frame_id: str
    name: str
    price: float
    seller_id: str
    seller_name: str
    quantity: int = 1
    max_quantity: int = 0
    image_url: Optional[str] = ""
    thumbnail_url: Optional[str] = ""

class AddToCartPayload(BaseModel):
    """Corpo do POST /add: { "item_data": { ... } }."""
    item_data: ItemCartSchema


@router.get("/get", summary="Obter meu próprio carrinho")
async def get_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """GET /cosmetics/marketplace/cart/get — carrinho completo, sincronizado com preço/estoque do
    PostgreSQL.
    """
    
    request = GetCartRequest(user_id=user.id)
    response_data, status_code = await GetCartUseCase().execute(request)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    
    return success_response(response_data)


@router.get("/get/summary", summary="Obter resumo do meu carrinho")
async def get_my_cart_summary(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """GET /cosmetics/marketplace/cart/get/summary — apenas os totais do carrinho (unidades, preço
    e anúncios distintos).
    """
    
    request = GetCartRequest(user_id=user.id)
    response_data, status_code = await GetCartUseCase().execute(request)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    data = response_data.get("data", {})
    return success_response({
        "total_items": data.get("total_items", 0),
        "total_price": data.get("total_price", 0),
        "unique_items_count": data.get("unique_items_count", 0)
        }
    )

@router.get("/item/{listing_id}/quantity", summary="Obter quantidade de um item no carrinho")
async def get_item_quantity(
    listing_id: str,
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """GET /cosmetics/marketplace/cart/item/{listing_id}/quantity — quantas unidades do anúncio já
    estão no carrinho.
    """
    request = GetItemQuantityRequest(user_id=user.id, listing_id=listing_id)
    response_data, status_code = await GetItemQuantityUseCase().execute(request)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    
    return success_response(response_data)



@router.post("/add/", summary="Adicionar item ao meu carrinho")
async def add_item_to_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)],
    payload: AddToCartPayload = Body(..., description="Dados do item envelopados em item_data")
):
    """POST /cosmetics/marketplace/cart/add/ — adiciona o anúncio ao carrinho (não permite comprar
    os próprios itens).
    """
    
    request = AddItemRequest(
        user_id=user.id,
        public_id=user.public_id,
        item_data=payload.item_data.model_dump()
    )
    response_data, status_code = await AddItemUseCase().execute(request)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    
    return success_response(response_data)



@router.delete("/remove/{item_id}", summary="Remover item do meu carrinho")
async def remove_item_from_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)],
    item_id: str
):
    """DELETE /cosmetics/marketplace/cart/remove/{item_id} — remove o item do carrinho."""
    
    request = RemoveItemRequest(user_id=user.id, item_id=item_id)
    response_data, status_code = await RemoveItemUseCase().execute(request)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    
    return success_response(response_data)


@router.patch("/update/{item_id}", summary="Atualizar quantidade de item")
async def update_quantity_in_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)],
    item_id: str,
    quantity: int = Query(..., ge=0, description="Nova quantidade (0 remove o item)")
):
    """PATCH /cosmetics/marketplace/cart/update/{item_id}?quantity=N — altera a quantidade (0
    remove o item).
    """
    
    request = UpdateQuantityRequest(
        user_id=user.id,
        item_id=item_id,
        quantity=quantity
    )
    response_data, status_code = await UpdateQuantityUseCase().execute(request)
    
    if "error" in response_data:
       error_response(response_data["error"], status_code)
    
    return success_response(response_data)


@router.delete("/clear", summary="Esvaziar meu carrinho")
async def clear_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """DELETE /cosmetics/marketplace/cart/clear — esvazia o carrinho."""
    
    response_data, status_code = await ClearCartUseCase().execute(user.id)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    
    return success_response(response_data)


@router.post("/validate", summary="Validar carrinho para checkout")
async def validate_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """POST /cosmetics/marketplace/cart/validate — sincroniza e valida o carrinho antes do checkout
    (400 se houver itens indisponíveis).
    """
    request = ValidateCartRequest(user_id=user.id)
    response_data, status_code = await ValidateCartUseCase().execute(request)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    
    return success_response(response_data)

@router.post("/sync", summary="Sincronizar carrinho com PostgreSQL")
async def sync_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """POST /cosmetics/marketplace/cart/sync — sincroniza o carrinho com preço e estoque atuais do
    PostgreSQL.
    """
    request = SyncCartRequest(user_id=user.id)
    response_data, status_code = await SyncCartUseCase().execute(request)
    
    if "error" in response_data:
        error_response(response_data["error"], status_code)
    
    return success_response(response_data)
