# app/api/routes/profile/update_use_case/use_case.py
# Caso de uso de PUT /profile/update: valida e normaliza os dados do perfil, converte
# avatar/capa para WebP, envia ao R2, atualiza o usuário no PostgreSQL e remove do R2 as imagens
# substituídas.

import logging
import re
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import db
from app.core.r2 import r2_client
from app.core.constants import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_IMAGE_MIME_TYPES, MB, WEBP_MIME_TYPE
from app.utils.image_utils import convert_to_webp, add_animated_suffix, ConvertOptions

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class UpdateProfileRequest(BaseModel):
    """Dados recebidos para atualizar o perfil (texto, arquivos e flags de remoção)."""
    user_id: str
    name: str
    username: str
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    avatar: Optional[Dict[str, Any]] = None
    cover: Optional[Dict[str, Any]] = None
    remove_avatar: bool = False
    remove_cover: bool = False

class UpdateProfileUseCase:
    """Atualiza o perfil do usuário.

    Limites: avatar até 5MB (GIF 3MB), capa até 8MB (GIF 5MB), nome de 3 a 50 caracteres, bio
    até 500, localização até 30, site até 200. Formatos aceitos: JPG, PNG, GIF e JFIF.
    """
    MAX_AVATAR_SIZE = 5 * MB
    MAX_COVER_SIZE = 8 * MB
    MAX_AVATAR_GIF = 3 * MB
    MAX_COVER_GIF = 5 * MB
    
    MAX_NAME_LENGTH = 50
    MIN_NAME_LENGTH = 3
    MAX_BIO_LENGTH = 500
    MAX_LOCATION_LENGTH = 30
    MAX_WEBSITE_LENGTH = 200
    
    # Conversão para WebP: dimensões do avatar e da capa e qualidade para GIF / imagem estática
    AVATAR_SIZE = (512, 512)
    COVER_SIZE = (1920, 400)
    WEBP_QUALITY_GIF = 75
    WEBP_QUALITY = 80

    async def execute(self, payload: dict) -> tuple[Dict[str, Any], int]:
        """Executa a atualização do perfil.

        Valida os dados, confere se o usuário existe, envia as novas imagens ao R2, atualiza o
        banco e apaga as imagens antigas substituídas ou removidas. Em falha, remove do R2 o que
        foi enviado. Retorna (resposta, status HTTP).
        """
        uploaded_paths = []
        try:
            logger.info("Iniciando execução do UseCase")
            request = UpdateProfileRequest(**payload)
            
            # Valida os dados antes de qualquer upload
            sanitized_data = await self._validate_and_sanitize(request)
            
            # Usuário precisa existir antes de enviar mídia
            current_user = await self._get_current_user(request.user_id)
            if not current_user:
                return {"error": "Usuário não encontrado"}, 404

            # Envia as novas imagens ao R2
            new_avatar_url, uploaded_avatar_path = await self._process_avatar(request)
            if uploaded_avatar_path:
                uploaded_paths.append(uploaded_avatar_path)
                
            new_cover_url, uploaded_cover_path = await self._process_cover(request)
            if uploaded_cover_path:
                uploaded_paths.append(uploaded_cover_path)

            # Atualiza o usuário no banco
            updated_user = await self._update_user(request.user_id, sanitized_data, new_avatar_url, new_cover_url, request.remove_avatar, request.remove_cover)
            if not updated_user:
                await self._rollback(uploaded_paths)
                return {"error": "Erro ao atualizar perfil"}, 500

            # Apaga do R2 as imagens antigas substituídas/removidas
            await self._cleanup_old_files(
                current_user, new_avatar_url, new_cover_url,
                request.remove_avatar, request.remove_cover
            )

            return {
                "success": True,
                "user": {
                    "id": updated_user['id'],
                    "name": updated_user['name'],
                    "username": updated_user['username'],
                    "email": updated_user['email'],
                    "bio": updated_user.get('bio'),
                    "location": updated_user.get('location'),
                    "website": updated_user.get('website'),
                    "avatar": updated_user.get('avatar'),
                    "coverImage": updated_user.get('coverImage'),
                }
            }, 200

        except ValueError as e:
            await self._rollback(uploaded_paths)
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Erro crítico ao atualizar perfil: {e}", exc_info=True)
            await self._rollback(uploaded_paths)
            return {"error": "Erro interno ao atualizar perfil"}, 500

    async def _validate_and_sanitize(self, request: UpdateProfileRequest) -> dict:
        """Normaliza e valida nome, username (único, minúsculo, 3–30 caracteres [a-z0-9_]), bio,
        localização, site (prefixa https:// quando falta) e arquivos. Retorna os campos de
        texto.
        """
        data = {}

        # Nome de exibição
        name = " ".join(request.name.strip().split())
        if not name:
            raise ValueError("Nome de Exibição é obrigatório")
        if len(name) < self.MIN_NAME_LENGTH or len(name) > self.MAX_NAME_LENGTH:
            raise ValueError(f"Nome de Exibição deve ter entre {self.MIN_NAME_LENGTH} e {self.MAX_NAME_LENGTH} caracteres")
        data['name'] = name

        # Nome de usuário
        if not request.username or not request.username.strip():
            raise ValueError("Nome de Usuário é obrigatório")
        
        sanitized_username = request.username.lower().strip()
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', sanitized_username):
            raise ValueError("Nome de Usuário inválido. Use apenas letras, números e underscore (3-30 caracteres)")

        existing_user = await db.fetch_one(
            'SELECT id FROM users WHERE username = $1 AND id != $2 AND "deletedAt" IS NULL',
            sanitized_username, request.user_id
        )
        if existing_user:
            raise ValueError("Nome de Usuário já em uso")
        data['username'] = sanitized_username

        # Bio
        if request.bio is not None:
            bio = request.bio.strip() if request.bio else None
            if bio and len(bio) > self.MAX_BIO_LENGTH:
                raise ValueError(f"Bio deve ter no máximo {self.MAX_BIO_LENGTH} caracteres")
            data['bio'] = bio

        # Localização
        if request.location is not None:
            location = request.location.strip() if request.location else None
            if location and len(location) > self.MAX_LOCATION_LENGTH:
                raise ValueError(f"Localização deve ter no máximo {self.MAX_LOCATION_LENGTH} caracteres")
            data['location'] = location

        # Site (sem espaços, https:// por padrão)
        if request.website is not None:
            website = "".join(request.website.strip().split()) if request.website else None
            if website:
                if not website.startswith(('http://', 'https://')):
                    website = f"https://{website}"
                if len(website) > self.MAX_WEBSITE_LENGTH:
                    raise ValueError(f"Website deve ter no máximo {self.MAX_WEBSITE_LENGTH} caracteres")
                if not URL_REGEX.match(website):
                    raise ValueError("URL inválida.")
            data['website'] = website

        # Arquivos
        if request.avatar:
            self._validate_file(request.avatar, "avatar", self.MAX_AVATAR_SIZE, self.MAX_AVATAR_GIF)
        if request.cover:
            self._validate_file(request.cover, "cover", self.MAX_COVER_SIZE, self.MAX_COVER_GIF)

        return data

    def _validate_file(self, file_data: Dict, file_type: str, max_size: int, max_gif_size: int):
        """Valida formato (MIME e extensão) e tamanho do arquivo, com limite menor para GIF."""
        filename = file_data.get('filename', '')
        content_type = file_data.get('content_type', '')
        size = file_data.get('size', 0)
        extension = filename.split('.')[-1].lower() if filename else ''

        if content_type not in ALLOWED_IMAGE_MIME_TYPES or extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(f"Formato do {file_type} não suportado. Use JPG, PNG, GIF ou JFIF.")

        if content_type == 'image/gif' and size > max_gif_size:
            raise ValueError(f"GIF muito grande para {file_type}. Máximo: {max_gif_size // 1024 // 1024}MB.")

        if size > max_size:
            raise ValueError(f"{file_type.capitalize()} muito grande. Máximo: {max_size // 1024 // 1024}MB.")

    async def _process_avatar(self, request: UpdateProfileRequest):
        """Converte o avatar para WebP 512x512 (animado se GIF), envia ao R2 e retorna (url,
        caminho) ou (None, None) sem avatar.
        """
        if request.avatar and request.avatar.get('data'):
            avatar_data = request.avatar
            is_gif = avatar_data['content_type'] == 'image/gif'
            
            converted = convert_to_webp(
                avatar_data['data'],
                avatar_data['content_type'],
                ConvertOptions(
                    format='webp-animated' if is_gif else 'webp',
                    quality=self.WEBP_QUALITY_GIF if is_gif else self.WEBP_QUALITY,
                    width=self.AVATAR_SIZE[0],
                    height=self.AVATAR_SIZE[1],
                    fit='cover'
                )
            )
            filename = add_animated_suffix(f"avatar-{int(time.time())}.webp", is_gif)
            path = f"avatars/{request.user_id}/{filename}"
            url = await r2_client.upload_public(converted.buffer, path, WEBP_MIME_TYPE)
            return url, path
        return None, None

    async def _process_cover(self, request: UpdateProfileRequest):
        """Converte a capa para WebP 1920x400 (animada se GIF), envia ao R2 e retorna (url,
        caminho) ou (None, None) sem capa.
        """
        if request.cover and request.cover.get('data'):
            cover_data = request.cover
            is_gif = cover_data['content_type'] == 'image/gif'
            
            converted = convert_to_webp(
                cover_data['data'],
                cover_data['content_type'],
                ConvertOptions(
                    format='webp-animated' if is_gif else 'webp',
                    quality=self.WEBP_QUALITY_GIF if is_gif else self.WEBP_QUALITY,
                    width=self.COVER_SIZE[0],
                    height=self.COVER_SIZE[1],
                    fit='cover'
                )
            )
            filename = add_animated_suffix(f"cover-{int(time.time())}.webp", is_gif)
            path = f"cover_image/{request.user_id}/{filename}"
            url = await r2_client.upload_public(converted.buffer, path, WEBP_MIME_TYPE)
            return url, path
        return None, None

    async def _get_current_user(self, user_id: str):
        """Busca id, avatar e capa atuais do usuário ativo."""
        return await db.fetch_one(
            'SELECT id, avatar, "coverImage" FROM users WHERE id = $1 AND "deletedAt" IS NULL',
            user_id
        )

    async def _update_user(self, user_id: str, sanitized_data: dict, new_avatar: str, new_cover: str, rm_avatar: bool, rm_cover: bool):
        """Atualiza os campos do usuário (incluindo nova imagem ou remoção) e retorna o registro
        atualizado.
        """
        update_data = dict(sanitized_data)

        if new_avatar:
            update_data['avatar'] = new_avatar
        elif rm_avatar:
            update_data['avatar'] = None

        if new_cover:
            update_data['coverImage'] = new_cover
        elif rm_cover:
            update_data['coverImage'] = None

        set_clause = ', '.join([f'"{k}" = ${i+1}' for i, k in enumerate(update_data.keys())])
        values = list(update_data.values()) + [user_id]

        return await db.fetch_one(
            f'UPDATE users SET {set_clause}, "updatedAt" = CURRENT_TIMESTAMP WHERE id = ${len(values)} AND "deletedAt" IS NULL RETURNING *',
            *values
        )

    async def _cleanup_old_files(self, user: Dict, new_avatar: str, new_cover: str, rm_avatar: bool, rm_cover: bool):
        """Apaga do R2 o avatar e a capa anteriores quando foram substituídos ou removidos."""
        if user.get('avatar') and (new_avatar or rm_avatar):
            path = user['avatar'].split('.com/')[-1] if '.com/' in user['avatar'] else user['avatar']
            await r2_client.delete_file(path, is_public=True)

        if user.get('coverImage') and (new_cover or rm_cover):
            path = user['coverImage'].split('.com/')[-1] if '.com/' in user['coverImage'] else user['coverImage']
            await r2_client.delete_file(path, is_public=True)

    async def _rollback(self, paths: list):
        """Remove do R2 os arquivos enviados nesta requisição, registrando falhas sem interromper."""
        for path in paths:
            try:
                await r2_client.delete_file(path, is_public=True)
            except Exception as e:
                logger.error(f"Erro ao deletar arquivo no rollback ({path}): {e}")
