# app/api/routes/cosmetics/creation/create_use_case/use_case.py
# Caso de uso de POST /cosmetics/creation/create: valida a moldura, cobra o pacote de criação em
# moedas, converte as imagens para WebP, envia ao R2 e grava moldura, itens de inventário e
# transação em uma única transação do PostgreSQL.

import logging
import time
import cuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import db
from app.core.r2 import r2_client
from app.core.constants import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_IMAGE_MIME_TYPES, MB, WEBP_MIME_TYPE
from app.utils.image_utils import convert_to_webp, add_animated_suffix, ConvertOptions

logger = logging.getLogger(__name__)

class CreateCosmeticFrameRequest(BaseModel):
    """Dados validados da criação: usuário, nome, descrição, pacote e imagens (bytes + metadados)."""
    user_id: str
    name: str
    description: Optional[str] = None
    package_id: str
    image: Dict[str, Any]
    thumbnail: Optional[Dict[str, Any]] = None

class CreateCosmeticFrameUseCase:
    """Cria uma moldura cosmética paga com moedas.

    Limites: moldura até 5MB (GIF 3MB), miniatura até 2MB (GIF 1MB), nome de 3 a 50 caracteres,
    descrição até 500. Formatos aceitos: JPG, PNG, GIF e JFIF.
    """
    MAX_FRAME_SIZE = 5 * MB
    MAX_FRAME_GIF = 3 * MB
    MAX_THUMB_SIZE = 2 * MB
    MAX_THUMB_GIF = 1 * MB
    MAX_NAME_SIZE = 50
    MAX_DESCRIPTION_SIZE = 500
    
    # Conversão para WebP: lado máximo (px) e qualidade para GIF animado / imagem estática
    IMAGE_SIZE = 512
    WEBP_QUALITY_GIF = 70
    WEBP_QUALITY = 75
    
    def __init__(self):
        """Inicializa os caminhos enviados ao R2 (usados no rollback)."""
        self._uploaded_image_path = None
        self._uploaded_thumbnail_path = None

    async def execute(self, payload: dict) -> tuple[Dict[str, Any], int]:
        """Executa a criação completa da moldura.

        Valida campos e arquivos, confere pacote e saldo, envia as imagens ao R2 e, em
        transação, debita as moedas, cria a moldura, adiciona ao inventário a quantidade do
        pacote e registra a coin_transaction. Em qualquer falha, remove do R2 os arquivos já
        enviados. Retorna (resposta, status HTTP).
        """
        try:
            logger.info(f"Iniciando criação de cosmético para o usuário: {payload.get('user_id')}")
            
            # Campos obrigatórios
            if not payload.get('name') or not payload.get('package_id'):
                raise ValueError("Campos obrigatórios inválidos ou faltando (name, package_id)")
            
            # Nome normalizado (espaços colapsados) entre 3 e 50 caracteres
            name = " ".join(payload.get('name', '').strip().split())
            if len(name) > self.MAX_NAME_SIZE:
                raise ValueError(f"Nome deve ter no máximo {self.MAX_NAME_SIZE} caracteres")
            if len(name) < 3:
                raise ValueError("Nome deve ter pelo menos 3 caracteres")
                
            # Descrição opcional de até 500 caracteres
            description = payload.get('description')
            if description is not None:
                description = str(description).strip()
                if len(description) > self.MAX_DESCRIPTION_SIZE:
                    raise ValueError(f"Descrição deve ter no máximo {self.MAX_DESCRIPTION_SIZE} caracteres")
            else:
                description = None
                
                    
            if not payload.get('image'):
                raise ValueError("Imagem principal é obrigatória")

            request = CreateCosmeticFrameRequest(**payload)
            
            # Formato e tamanho das imagens
            self._validate_file(request.image, "moldura", self.MAX_FRAME_SIZE, self.MAX_FRAME_GIF)
            if request.thumbnail:
                self._validate_file(request.thumbnail, "miniatura", self.MAX_THUMB_SIZE, self.MAX_THUMB_GIF)
                
            # Pacote existente e saldo suficiente
            package = await self._get_package(request.package_id)
            if not package:
                return {"error": "Pacote inválido"}, 400
                
            user_coins = await self._get_user_coins(request.user_id)
            total_cost = int(package['totalCost']) 
            if user_coins < total_cost:
                return {
                    "error": f"Moedas insuficientes. Você precisa de {total_cost} moedas."
                }, 400

            # Converte para WebP e envia ao R2; sem miniatura, usa a imagem principal
            timestamp = int(time.time() * 1000)  # Milissegundos compõem o caminho único no bucket
            new_image_url, self._uploaded_image_path = await self._process_frame(request, timestamp)
            
            if request.thumbnail:
                new_thumb_url, self._uploaded_thumbnail_path = await self._process_thumbnail(request, timestamp)
            else:
                new_thumb_url = new_image_url

            # Débito, moldura, inventário e histórico na mesma transação (rollback total em erro)
            try:
                async with db.transaction():
                    # Debita as moedas; saldo negativo aborta a transação
                    updated_user = await db.fetch_one(
                        """UPDATE users SET coins = coins - $1 WHERE id = $2 RETURNING coins""",
                        total_cost, request.user_id
                    )
                    
                    if updated_user['coins'] < 0:
                        raise RuntimeError("INSUFFICIENT_FUNDS")
                    frame_id = cuid.cuid()
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    # Moldura com estoque igual à quantidade do pacote
                    frame = await db.fetch_one(
                        """
                        INSERT INTO cosmetic_frame (id, name, description, "imageUrl", "thumbnailUrl", rarity, stock, "createdBy", "createdAt", "updatedAt")
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        RETURNING *
                        """,
                        frame_id, name, description, new_image_url, new_thumb_url,
                        package['rarity'], int(package['quantity']), request.user_id, now, now
                    )
                    
                    # Uma unidade no inventário do criador para cada item do pacote
                    for _ in range(int(package['quantity'])):
                        item_id = cuid.cuid()
                        await db.execute(
                            """INSERT INTO user_frame_item ("id","frameId", "ownerId", "createdAt", "updatedAt") VALUES ($1, $2, $3, $4, $5)""",
                            item_id, frame['id'], request.user_id, now, now
                        )
                        
                    # Histórico do gasto de moedas
                    transaction_id = cuid.cuid() 
                    await db.execute(
                        """
                        INSERT INTO coin_transaction ("id", "userId", amount, balance, type, description, "createdAt")
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        transaction_id, request.user_id, -total_cost, updated_user['coins'], 'spend',
                        f"Criação de moldura: {name} ({package['rarity']}) - Pacote {package['name']}", now
                    )
                    
            except Exception as db_err:
                logger.error(f"Falha na transação do BD: {db_err}")
                raise db_err  # Tratado abaixo, que também remove os arquivos do R2

            return {
                "success": True,
                "frame": dict(frame),
                "message": f"Moldura criada! {int(package['quantity'])} unidade(s) do pacote {package['name']} adicionadas ao seu inventário."
            }, 201

        except ValueError as e:
            await self._rollback()
            return {"error": str(e)}, 400
        except RuntimeError as e:
            await self._rollback()
            if str(e) == "INSUFFICIENT_FUNDS":
                return {"error": "Moedas insuficientes"}, 400
            return {"error": "Erro interno de processamento"}, 500
        except Exception as e:
            logger.error(f"Erro crítico ao criar moldura: {e}")
            await self._rollback()
            return {"error": "Erro interno ao criar moldura", "details": str(e)}, 500

    # Validação e consultas

    def _validate_file(self, file_data: Dict, file_type: str, max_size: int, max_gif_size: int):
        """Valida formato (MIME e extensão) e tamanho do arquivo, com limite menor para GIF."""
        filename = file_data.get('filename', '')
        content_type = file_data.get('content_type', '')
        size = file_data.get('size', 0)
        extension = filename.split('.')[-1].lower() if filename else ''
        
        if content_type not in ALLOWED_IMAGE_MIME_TYPES or extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(f"Formato da {file_type} não suportado. Use JPG, PNG, GIF ou JFIF.")
        
        if content_type == 'image/gif' and size > max_gif_size:
            raise ValueError(f"GIF para {file_type} deve ter no máximo {max_gif_size // 1024 // 1024}MB.")
            
        if size > max_size:
            raise ValueError(f"{file_type.capitalize()} deve ter no máximo {max_size // 1024 // 1024}MB.")

    async def _get_package(self, package_id: str):
        """Busca o pacote de criação (cosmetic_creation_package) pelo id."""
        return await db.fetch_one('SELECT * FROM cosmetic_creation_package WHERE id = $1', package_id)

    async def _get_user_coins(self, user_id: str) -> int:
        """Saldo de moedas do usuário (0 se não encontrado)."""
        user = await db.fetch_one('SELECT coins FROM users WHERE id = $1', user_id)
        return int(user['coins']) if user else 0

    # Processamento e upload de imagens

    async def _process_frame(self, request: CreateCosmeticFrameRequest, timestamp: int):
        """Converte a imagem principal para WebP (até 512x512, animado se GIF), envia ao R2 e
        retorna (url, caminho).
        """
        is_gif = request.image['content_type'] == 'image/gif'
        image_bytes = request.image['data']
        
        converted = convert_to_webp(
            image_bytes,
            request.image['content_type'],
            ConvertOptions(
                format='webp-animated' if is_gif else 'webp', 
                quality=self.WEBP_QUALITY_GIF if is_gif else self.WEBP_QUALITY, 
                width=self.IMAGE_SIZE, 
                height=self.IMAGE_SIZE, 
                fit='inside'
            )
        )
        
        filename = f"image-{timestamp}.webp"
        final_filename = add_animated_suffix(filename, is_gif)
        path = f"frames/{timestamp}-{request.user_id}/{final_filename}"
        
        url = await r2_client.upload_public(converted.buffer, path, WEBP_MIME_TYPE)
        return url, path

    async def _process_thumbnail(self, request: CreateCosmeticFrameRequest, timestamp: int):
        """Converte a miniatura para WebP 512x512 recortada (cover), envia ao R2 e retorna (url,
        caminho).
        """
        is_gif = request.thumbnail['content_type'] == 'image/gif'
        thumb_bytes = request.thumbnail['data']
        
        converted = convert_to_webp(
            thumb_bytes,
            request.thumbnail['content_type'],
            ConvertOptions(
                format='webp-animated' if is_gif else 'webp', 
                quality=self.WEBP_QUALITY_GIF if is_gif else self.WEBP_QUALITY, 
                width=self.IMAGE_SIZE, 
                height=self.IMAGE_SIZE, 
                fit='cover'
            )
        )
        
        filename = f"thumbnail-{timestamp}.webp"
        final_filename = add_animated_suffix(filename, is_gif)
        path = f"frames/{timestamp}-{request.user_id}/{final_filename}"
        
        url = await r2_client.upload_public(converted.buffer, path, WEBP_MIME_TYPE)
        return url, path

    # Limpeza do R2 em caso de falha

    async def _rollback(self):
        """Remove do R2 a imagem e a miniatura já enviadas quando a criação falha."""
        if self._uploaded_image_path:
            await r2_client.delete_file(self._uploaded_image_path, is_public=True)
            logger.info(f"Rollback executado: moldura deletada -> {self._uploaded_image_path}")
            
        if self._uploaded_thumbnail_path and self._uploaded_thumbnail_path != self._uploaded_image_path:
            await r2_client.delete_file(self._uploaded_thumbnail_path, is_public=True)
            logger.info(f"Rollback executado: thumbnail deletada -> {self._uploaded_thumbnail_path}")
