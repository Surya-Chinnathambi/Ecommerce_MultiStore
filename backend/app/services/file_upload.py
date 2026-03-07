"""
Secure File Upload Service
Handles validation, sanitization, and storage of uploaded files.
"""
import io
import secrets
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from fastapi import UploadFile, HTTPException
from PIL import Image
from app.services.storage_service import storage, BaseStorage
import logging

logger = logging.getLogger(__name__)


class SecureFileUpload:
    """
    Enterprise-grade file upload handler with security validations.
    
    Features:
    - MIME type validation using magic bytes
    - File size limits
    - Image dimension limits
    - Metadata stripping
    - Secure filename generation
    - Content re-encoding
    """
    
    # Allowed file types
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.csv', '.xlsx'}
    
    ALLOWED_IMAGE_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    }
    
    # Magic bytes for file type detection
    MAGIC_BYTES = {
        b'\xff\xd8\xff': 'image/jpeg',
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'RIFF': 'image/webp',  # WebP starts with RIFF
        b'%PDF': 'application/pdf',
    }
    
    # Size limits
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_DIMENSIONS = (4096, 4096)
    
    def __init__(self, storage: BaseStorage = storage):
        self.storage = storage
    
    def _detect_mime_type(self, content: bytes) -> Optional[str]:
        """Detect MIME type from file magic bytes."""
        for magic, mime in self.MAGIC_BYTES.items():
            if content.startswith(magic):
                return mime
        
        # Check for WebP (RIFF....WEBP)
        if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
            return 'image/webp'
        
        return None
    
    def _generate_secure_filename(self, extension: str) -> str:
        """Generate a secure, unique filename."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        random_suffix = secrets.token_hex(8)
        return f"{timestamp}_{random_suffix}{extension}"
    
    def _calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    async def validate_image(
        self, 
        file: UploadFile
    ) -> Tuple[bytes, str, dict]:
        """
        Validate and process an uploaded image.
        
        Returns:
            Tuple of (processed_content, secure_filename, metadata)
        
        Raises:
            HTTPException: If validation fails
        """
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > self.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum size is {self.MAX_IMAGE_SIZE // (1024*1024)}MB"
            )
        
        # Check extension
        original_filename = file.filename or "unknown"
        ext = Path(original_filename).suffix.lower()
        if ext not in self.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension. Allowed: {', '.join(self.ALLOWED_IMAGE_EXTENSIONS)}"
            )
        
        # Detect and validate MIME type using magic bytes
        detected_mime = self._detect_mime_type(content)
        if detected_mime not in self.ALLOWED_IMAGE_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type detected"
            )
        
        # Validate image content
        try:
            # First verify it's a valid image
            img = Image.open(io.BytesIO(content))
            img.verify()
            
            # Re-open for processing (verify() closes the file)
            img = Image.open(io.BytesIO(content))
            
            # Check dimensions
            width, height = img.size
            if width > self.MAX_IMAGE_DIMENSIONS[0] or height > self.MAX_IMAGE_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image dimensions too large. Maximum: {self.MAX_IMAGE_DIMENSIONS[0]}x{self.MAX_IMAGE_DIMENSIONS[1]}"
                )
            
            # Get original format
            original_format = img.format
            
            # Re-encode image to strip EXIF metadata and potential malicious content
            output = io.BytesIO()
            
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'P') and original_format == 'JPEG':
                img = img.convert('RGB')
            
            # Save with appropriate settings
            save_kwargs = {'quality': 85, 'optimize': True}
            if original_format == 'PNG':
                save_kwargs = {'optimize': True}
            elif original_format == 'GIF':
                save_kwargs = {}
            
            img.save(output, format=original_format, **save_kwargs)
            processed_content = output.getvalue()
            
            # Generate secure filename
            secure_filename = self._generate_secure_filename(ext)
            
            # Build metadata
            metadata = {
                'original_filename': original_filename,
                'secure_filename': secure_filename,
                'mime_type': detected_mime,
                'file_size': len(processed_content),
                'dimensions': {'width': width, 'height': height},
                'hash': self._calculate_hash(processed_content),
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Image validated: {metadata['secure_filename']}, "
                f"size={metadata['file_size']}, "
                f"dimensions={width}x{height}"
            )
            
            return processed_content, secure_filename, metadata
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid or corrupted image file"
            )
    
    async def save_file(
        self, 
        content: bytes, 
        filename: str,
        subfolder: str = ""
    ) -> str:
        """
        Save file content to disk.
        
        Args:
            content: File content bytes
            filename: Secure filename
            subfolder: Optional subfolder (e.g., store_id)
        
        Returns:
            Relative path to saved file
        """
        return await self.storage.save_file(content, filename, subfolder)
    
    async def process_and_save_image(
        self,
        file: UploadFile,
        store_id: str,
        generate_thumbnails: bool = True
    ) -> dict:
        """
        Complete image upload workflow.
        
        Args:
            file: Uploaded file
            store_id: Store ID for folder organization
            generate_thumbnails: Whether to create thumbnail versions
        
        Returns:
            Dict with file URLs and metadata
        """
        # Validate and process
        content, filename, metadata = await self.validate_image(file)
        
        # Save original
        file_path = await self.save_file(content, filename, store_id)
        
        result = {
            'url': await self.storage.get_url(file_path),
            'filename': filename,
            'metadata': metadata,
            'thumbnails': {}
        }
        
        # Generate thumbnails if requested
        if generate_thumbnails:
            img = Image.open(io.BytesIO(content))
            
            thumbnail_sizes = {
                'small': (150, 150),
                'medium': (300, 300),
                'large': (600, 600)
            }
            
            for size_name, dimensions in thumbnail_sizes.items():
                thumb_img = img.copy()
                thumb_img.thumbnail(dimensions, Image.Resampling.LANCZOS)
                
                thumb_output = io.BytesIO()
                thumb_img.save(thumb_output, format=img.format, quality=80)
                thumb_content = thumb_output.getvalue()
                
                thumb_filename = f"{Path(filename).stem}_{size_name}{Path(filename).suffix}"
                thumb_path = await self.save_file(
                    thumb_content, 
                    thumb_filename, 
                    f"{store_id}/thumbnails"
                )
                
                result['thumbnails'][size_name] = {
                    'url': await self.storage.get_url(thumb_path),
                    'dimensions': thumb_img.size
                }
        
        return result


# Singleton instance
secure_upload = SecureFileUpload()
