# app/core/r2.py
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class R2Client:
    """Cliente para Cloudflare R2"""
    
    def __init__(self):
        # Validação das variáveis
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
        """
        Upload de arquivo para bucket público
        
        Args:
            file_data: Dados do arquivo em bytes
            path: Caminho no bucket (ex: avatars/userId/current.jpg)
            content_type: Tipo MIME do arquivo
        
        Returns:
            URL pública do arquivo
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
        """
        Upload de arquivo para bucket privado
        
        Args:
            file_data: Dados do arquivo em bytes
            path: Caminho no bucket
            content_type: Tipo MIME do arquivo
        
        Returns:
            Path do arquivo
        """
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
        """
        Deletar arquivo de qualquer bucket
        
        Args:
            path: Caminho do arquivo (pode ser URL ou path)
            is_public: Se é público (True) ou privado (False)
        
        Returns:
            True se deletado com sucesso
        """
        try:
            # Remove a URL pública se fornecida
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
        """
        Verifica se arquivo existe
        
        Args:
            path: Caminho do arquivo
            is_public: Se é público (True) ou privado (False)
        
        Returns:
            True se existe
        """
        try:
            bucket = self.public_bucket if is_public else self.private_bucket
            self.client.head_object(Bucket=bucket, Key=path)
            return True
        except ClientError:
            return False
    
    async def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """
        Gera URL assinada para arquivo privado
        
        Args:
            path: Caminho do arquivo no bucket privado
            expires_in: Tempo de expiração em segundos (padrão: 1 hora)
        
        Returns:
            URL assinada temporária
        """
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

# Instância global
r2_client = R2Client()