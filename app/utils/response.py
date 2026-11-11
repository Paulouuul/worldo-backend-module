# app/utils/response.py
# Helpers de resposta HTTP padronizada para as rotas.

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Any
from fastapi import HTTPException
import logging
logger = logging.getLogger(__name__)

def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Retorna um JSONResponse com o dado serializado via jsonable_encoder."""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(data)
    )

def error_response(message: str, status_code: int = 400) -> None:
    """Registra o erro no log e lança HTTPException com a mensagem e o status informados."""
    logger.warning(f"Erro {status_code}: {message}")
    raise HTTPException(
        status_code=status_code,
        detail=message
    )
