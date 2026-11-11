# app/core/r2.py
# Cliente do Cloudflare R2 (API compatível com S3) para upload, remoção, verificação e URLs
# assinadas nos buckets público e privado.

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class R2Client:
    """Cliente boto3 configurado para os buckets público e privado do Cloudflare R2."""
    
    def __init__(self):
        """Valida as variáveis WORLDO_R2_* e cria o cliente S3 apontando para o endpoint do R2."""
        if not all([settings.r2_account_id, settings.r2_access_key_id, 
                   settings.r2_secret_access_key, settings.r2_public_bucket,
                   settings.r2_public_url]):
            raise ValueError("Missing R2 environment variables")
        
        # Configuração do cliente S3 compatível com R2
        endpoint = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
        
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name='auto',
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3}
            )
        )
        
        self.public_bucket = settings.r2_public_bucket
        self.private_bucket = settings.r2_private_bucket
        self.public_url = settings.r2_public_url
    
    async def upload_public(self, file_data: bytes, path: str, content_type: str) -> str:
        """Envia o arquivo ao bucket público com cache de 1 ano e retorna a URL pública.

        `path` é a chave no bucket (ex.: avatars/<userId>/current.jpg).
        """
        try:
            self.client.put_object(
                Bucket=self.public_bucket,
                Key=path,
                Body=file_data,
                ContentType=content_type,
                CacheControl='public, max-age=31536000'  # 1 ano
            )
            
            return f"{self.public_url}/{path}"
        except ClientError as e:
            logger.error(f"Erro ao fazer upload público: {e}")
            raise
    
    async def upload_private(self, file_data: bytes, path: str, content_type: str) -> str:
        """Envia o arquivo ao bucket privado e retorna a chave (`path`) do objeto."""
        try:
            self.client.put_object(
                Bucket=self.private_bucket,
                Key=path,
                Body=file_data,
                ContentType=content_type
            )
            
            return path
        except ClientError as e:
            logger.error(f"Erro ao fazer upload privado: {e}")
            raise
    
    async def delete_file(self, path: str, is_public: bool = True) -> bool:
        """Remove o arquivo do bucket público ou privado. Aceita chave ou URL pública.

        Retorna False (sem lançar) se o R2 recusar a remoção.
        """
        try:
            # Converte URL pública em chave do bucket
            if path.startswith(self.public_url):
                path = path.replace(f"{self.public_url}/", "")
            
            bucket = self.public_bucket if is_public else self.private_bucket
            
            self.client.delete_object(
                Bucket=bucket,
                Key=path
            )
            logger.info(f"Arquivo deletado: {path} (bucket: {bucket})")
            return True
        except ClientError as e:
            logger.error(f"Erro ao deletar arquivo: {e}")
            return False
    
    async def file_exists(self, path: str, is_public: bool = True) -> bool:
        """Retorna True se a chave existe no bucket público ou privado."""
        try:
            bucket = self.public_bucket if is_public else self.private_bucket
            self.client.head_object(Bucket=bucket, Key=path)
            return True
        except ClientError:
            return False
    
    async def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Gera uma URL temporária de leitura para um arquivo do bucket privado (padrão: 1 hora)."""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.private_bucket,
                    'Key': path
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Erro ao gerar URL assinada: {e}")
            raise

# Instância compartilhada pela aplicação
r2_client = R2Client()
