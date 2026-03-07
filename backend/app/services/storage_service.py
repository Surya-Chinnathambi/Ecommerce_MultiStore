import abc
import io
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

import aiofiles
from app.core.config import settings

logger = logging.getLogger(__name__)

class BaseStorage(abc.ABC):
    """Abstract base class for storage providers."""
    
    @abc.abstractmethod
    async def save_file(self, content: bytes, filename: str, subfolder: str = "") -> str:
        """Save file and return the access URL or relative path."""
        pass

    @abc.abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Delete a file from storage."""
        pass

    @abc.abstractmethod
    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a signed or public URL for the file."""
        pass

    @abc.abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in a directory/prefix."""
        pass


class LocalStorage(BaseStorage):
    """Local disk storage implementation."""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # In a real app, this base URL would be the server's public URL
        self.base_url = "/uploads"

    async def save_file(self, content: bytes, filename: str, subfolder: str = "") -> str:
        save_dir = self.upload_dir / subfolder if subfolder else self.upload_dir
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = save_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        rel_path = file_path.relative_to(self.upload_dir)
        return str(rel_path).replace("\\", "/")

    async def delete_file(self, path: str) -> bool:
        file_path = self.upload_dir / path
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False

    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        # Local storage doesn't really have signed URLs in this simple impl
        return f"{self.base_url}/{path.replace('\\', '/')}"

    async def list_files(self, prefix: str = "") -> List[str]:
        search_dir = self.upload_dir / prefix
        if not search_dir.exists():
            return []
        return [str(p.relative_to(self.upload_dir)).replace("\\", "/") for p in search_dir.glob("**/*") if p.is_file()]


class S3Storage(BaseStorage):
    """S3-compatible cloud storage implementation using aiobotocore."""
    
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.S3_REGION
        self.endpoint = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        
    def _get_session(self):
        from aiobotocore.session import get_session
        return get_session()

    async def save_file(self, content: bytes, filename: str, subfolder: str = "") -> str:
        path = f"{subfolder}/{filename}" if subfolder else filename
        session = self._get_session()
        async with session.create_client(
            's3', 
            region_name=self.region,
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        ) as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=path,
                Body=content,
                # ACL='public-read' # Often better to keep private and use signed URLs
            )
        return path

    async def delete_file(self, path: str) -> bool:
        session = self._get_session()
        async with session.create_client(
            's3',
            region_name=self.region,
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        ) as client:
            try:
                await client.delete_object(Bucket=self.bucket_name, Key=path)
                return True
            except Exception as e:
                logger.error(f"Error deleting S3 object {path}: {e}")
                return False

    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        session = self._get_session()
        async with session.create_client(
            's3',
            region_name=self.region,
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        ) as client:
            url = await client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': path},
                ExpiresIn=expires_in
            )
            return url

    async def list_files(self, prefix: str = "") -> List[str]:
        session = self._get_session()
        async with session.create_client(
            's3',
            region_name=self.region,
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        ) as client:
            paginator = client.get_paginator('list_objects_v2')
            files = []
            async for result in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for content in result.get('Contents', []):
                    files.append(content['Key'])
            return files


def get_storage() -> BaseStorage:
    """Factory function to get the configured storage provider."""
    if settings.ENVIRONMENT == "production" and settings.S3_ACCESS_KEY:
        return S3Storage()
    return LocalStorage()

# Singleton instance for general use
storage = get_storage()
