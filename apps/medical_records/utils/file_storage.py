"""
File Storage Utilities for Medical Documents
Handles file upload, storage, and management for medical documents.
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import uuid

from fastapi import UploadFile
from common.utils.logging import get_logger

logger = get_logger(__name__)


class FileStorageManager:
    """Manages file storage for medical documents."""
    
    def __init__(self, base_path: str = None):
        """
        Initialize file storage manager.
        
        Args:
            base_path: Base directory for file storage
        """
        if base_path is None:
            # Use absolute path from project root
            import os
            project_root = Path(__file__).parent.parent.parent.parent
            self.base_path = project_root / "uploads" / "medical_documents"
        else:
            self.base_path = Path(base_path)
        
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "temp").mkdir(exist_ok=True)
        (self.base_path / "processed").mkdir(exist_ok=True)
        (self.base_path / "archived").mkdir(exist_ok=True)
    
    def save_uploaded_file(self, file: UploadFile, patient_id: str) -> Dict[str, Any]:
        """
        Save an uploaded file to storage.
        
        Args:
            file: Uploaded file
            patient_id: Patient ID for organization
            
        Returns:
            Dictionary containing file information
        """
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create patient directory
            patient_dir = self.base_path / "processed" / patient_id
            patient_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            original_extension = Path(file.filename).suffix if file.filename else ""
            filename = f"{file_id}_{timestamp}{original_extension}"
            file_path = patient_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file info
            file_size = file_path.stat().st_size
            mime_type = file.content_type or "application/octet-stream"
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            logger.info(f"File saved: {file_path} (size: {file_size} bytes)")
            
            return {
                'file_path': str(file_path),
                'file_url': f"/uploads/medical_documents/processed/{patient_id}/{filename}",
                'file_size': file_size,
                'mime_type': mime_type,
                'filename': filename,
                'file_hash': file_hash,
                'original_filename': file.filename
            }
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise
    
    def save_file_from_path(self, source_path: str, patient_id: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Save a file from a source path to storage.
        
        Args:
            source_path: Source file path
            patient_id: Patient ID for organization
            filename: Optional custom filename
            
        Returns:
            Dictionary containing file information
        """
        try:
            source_path = Path(source_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            # Generate filename if not provided
            if not filename:
                file_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = source_path.suffix
                filename = f"{file_id}_{timestamp}{extension}"
            
            # Create patient directory
            patient_dir = self.base_path / "processed" / patient_id
            patient_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            dest_path = patient_dir / filename
            shutil.copy2(source_path, dest_path)
            
            # Get file info
            file_size = dest_path.stat().st_size
            mime_type = self._get_mime_type(dest_path)
            file_hash = self._calculate_file_hash(dest_path)
            
            logger.info(f"File copied: {dest_path} (size: {file_size} bytes)")
            
            return {
                'file_path': str(dest_path),
                'file_url': f"/uploads/medical_documents/processed/{patient_id}/{filename}",
                'file_size': file_size,
                'mime_type': mime_type,
                'filename': filename,
                'file_hash': file_hash,
                'original_filename': source_path.name
            }
            
        except Exception as e:
            logger.error(f"Failed to save file from path: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary containing file information or None if not found
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            return {
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'mime_type': self._get_mime_type(file_path),
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'file_hash': self._calculate_file_hash(file_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of a file based on extension."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for temp files
            
        Returns:
            Number of files cleaned up
        """
        try:
            temp_dir = self.base_path / "temp"
            if not temp_dir.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            cleaned_count = 0
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0


# Global file storage manager instance
file_storage = FileStorageManager()
