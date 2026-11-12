# app/core/constants.py
# Constantes compartilhadas pelos casos de uso de upload de imagens (perfil e criação de
# cosméticos). Os limites equivalentes do frontend ficam em constants/uploads.ts do Next.js.

# Bytes em um megabyte
MB = 1024 * 1024

# Formatos de imagem aceitos nos uploads
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'jfif'}
ALLOWED_IMAGE_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/jfif'}

# Tipo de conteúdo das imagens salvas no R2 (todas convertidas para WebP)
WEBP_MIME_TYPE = 'image/webp'
