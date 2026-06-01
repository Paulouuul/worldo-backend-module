# app/api/routes/cosmetic/marketplace/cart/router.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
import json
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo

from .add_item.use_case import AddItemUseCase
from .get_cart.use_case import GetCartUseCase
from .remove_item.use_case import RemoveItemUseCase
from .update_quantity.use_case import UpdateQuantityUseCase
from .clear_cart.use_case import ClearCartUseCase

router = APIRouter()


@router.get("/me", summary="Obter meu próprio carrinho")
async def get_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """Retorna o carrinho do usuário autenticado"""
    
    payload = {"user_id": user.id}
    
    use_case = GetCartUseCase()
    use_case._request = json.dumps(payload)
    response = use_case.execute()
    
    if not response.get("success"):
        raise HTTPException(status_code=response.get("status_code", 500), detail=response.get("error"))
    
    return response.get("data")


@router.get("/me/summary", summary="Obter resumo do meu carrinho")
async def get_my_cart_summary(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """Retorna apenas o resumo do carrinho (totais)"""
    
    payload = {"user_id": user.id}
    
    use_case = GetCartUseCase()
    use_case._request = json.dumps(payload)
    response = use_case.execute()
    
    if not response.get("success"):
        raise HTTPException(status_code=response.get("status_code", 500), detail=response.get("error"))
    
    data = response.get("data", {})
    return {
        "total_items": data.get("total_items", 0),
        "total_price": data.get("total_price", 0),
        "unique_items_count": data.get("unique_items_count", 0)
    }


@router.post("/me/items", summary="Adicionar item ao meu carrinho")
async def add_item_to_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)],
    item_data: dict
):
    """Adiciona um item ao carrinho do usuário autenticado"""
    
    payload = {
        "user_id": user.id,
        "item_data": item_data
    }
    
    use_case = AddItemUseCase()
    use_case._request = json.dumps(payload)
    response = use_case.execute()
    
    if not response.get("success"):
        raise HTTPException(status_code=response.get("status_code", 500), detail=response.get("error"))
    
    return response.get("data")


@router.delete("/me/items/{item_id}", summary="Remover item do meu carrinho")
async def remove_item_from_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)],
    item_id: str
):
    """Remove um item específico do carrinho do usuário autenticado"""
    
    payload = {
        "user_id": user.id,
        "item_id": item_id
    }
    
    use_case = RemoveItemUseCase()
    use_case._request = json.dumps(payload)
    response = use_case.execute()
    
    if not response.get("success"):
        raise HTTPException(status_code=response.get("status_code", 500), detail=response.get("error"))
    
    return response.get("data")


@router.patch("/me/items/{item_id}", summary="Atualizar quantidade de item")
async def update_quantity_in_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)],
    item_id: str,
    quantity: int = Query(..., ge=0, description="Nova quantidade (0 remove o item)"),
):
    """Atualiza a quantidade de um item no carrinho do usuário autenticado"""
    
    payload = {
        "user_id": user.id,
        "item_id": item_id,
        "quantity": quantity
    }
    
    use_case = UpdateQuantityUseCase()
    use_case._request = json.dumps(payload)
    response = use_case.execute()
    
    if not response.get("success"):
        raise HTTPException(status_code=response.get("status_code", 500), detail=response.get("error"))
    
    return response.get("data")


@router.delete("/me/clear", summary="Esvaziar meu carrinho")
async def clear_my_cart(
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """Remove todos os itens do carrinho do usuário autenticado"""
    
    payload = {"user_id": user.id}
    
    use_case = ClearCartUseCase()
    use_case._request = json.dumps(payload)
    response = use_case.execute()
    
    if not response.get("success"):
        raise HTTPException(status_code=response.get("status_code", 500), detail=response.get("error"))
    
    return response.get("data")