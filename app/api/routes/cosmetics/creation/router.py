# app/api/routes/cosmetics/creation/router.py
# Rotas de criação de cosméticos (/cosmetics/creation/*, sob WORLDO_API_PREFIX). Exige JWT.

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import logging
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from .create_use_case.use_case import CreateCosmeticFrameUseCase
from app.utils.response import success_response, error_response
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create", summary="Criar nova moldura cosmética", status_code=201)
async def create_cosmetic_frame(
    user: Annotated[UserInfo, Depends(get_current_user)],
    name: str = Form(..., description="Nome da moldura"),
    packageId: str = Form(..., description="ID do pacote selecionado (cosmetic_creation_package)"),
    description: Optional[str] = Form(None, description="Descrição opcional da moldura"),
    image: UploadFile = File(..., description="Arquivo da imagem principal"),
    thumbnail: Optional[UploadFile] = File(None, description="Arquivo da miniatura opcional"),
):
    """POST /cosmetics/creation/create — cria uma moldura a partir do FormData do Next.js.

    Lê a imagem principal (obrigatória) e a miniatura (opcional) em memória e delega validação,
    cobrança de moedas, upload ao R2 e gravação ao CreateCosmeticFrameUseCase. Retorna 201 com a
    moldura criada.
    """
    logger.info("=" * 50)
    logger.info(f"INICIANDO CRIAÇÃO DE COSMÉTICO | Usuário: {user.id}")
    logger.info(f" Nome: {name}")
    logger.info(f" Pacote ID: {packageId}")
    logger.info(f"Imagem principal recebida: {image.filename} ({image.content_type}) - {image.size} bytes")
    if thumbnail:
        logger.info(f"  Miniatura recebida: {thumbnail.filename} ({thumbnail.content_type}) - {thumbnail.size} bytes")
    logger.info("=" * 50)

    try:
        # Imagem principal em memória (obrigatória)
        image_data = None
        if image and image.size > 0:
            image_data = {
                "filename": image.filename,
                "content_type": image.content_type,
                "size": image.size,
                "data": await image.read()
            }
        else:
            raise ValueError("O arquivo de imagem principal é obrigatório e não pode estar vazio.")

        # Miniatura em memória (opcional)
        thumbnail_data = None
        if thumbnail and thumbnail.size > 0:
            thumbnail_data = {
                "filename": thumbnail.filename,
                "content_type": thumbnail.content_type,
                "size": thumbnail.size,
                "data": await thumbnail.read()
            }

        # Payload do caso de uso (bytes das imagens incluídos)
        payload = {
            "user_id": user.id,
            "name": name,
            "description": description,
            "package_id": packageId,
            "image": image_data,
            "thumbnail": thumbnail_data
        }

        # Executa a criação (validação, cobrança, upload e gravação)
        use_case = CreateCosmeticFrameUseCase()

        response_data, status_code = await use_case.execute(payload)

        # Converte o erro do caso de uso em HTTPException
        if "error" in response_data:
            logger.error(f"Erro no use_case de cosmético: {response_data.get('error')}")
            error_response(response_data["error"], status_code)

        logger.info("Cosmético criado com sucesso!")
        return success_response(response_data)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Erro de validação no router")
        error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Erro inesperado no router de cosmético")
        error_response("Erro interno ao processar requisição", 500)
