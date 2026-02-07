"""
Image Storage Utilities for Medical Imaging
Handles medical image storage, compression, and format conversion.
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import uuid

from PIL import Image, ImageOps
import numpy as np

from common.utils.logging import get_logger

logger = get_logger(__name__)


class MedicalImageStorage:
    """Manages storage for medical images."""
    
    def __init__(self, base_path: str = None):
        """
        Initialize medical image storage.
        
        Args:
            base_path: Base directory for image storage
        """
        if base_path is None:
            # Use absolute path from project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.base_path = project_root / "uploads" / "medical_images"
        else:
            self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "dicom").mkdir(exist_ok=True)
        (self.base_path / "converted").mkdir(exist_ok=True)
        (self.base_path / "thumbnails").mkdir(exist_ok=True)
        (self.base_path / "temp").mkdir(exist_ok=True)
        
        # Supported formats
        self.supported_formats = ['.dcm', '.dicom', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        self.output_formats = ['.jpg', '.jpeg', '.png', '.tiff']
    
    def save_medical_image(
        self, 
        file_path: str, 
        patient_id: str, 
        study_id: str,
        image_format: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Save a medical image to storage.
        
        Args:
            file_path: Path to the image file
            patient_id: Patient ID for organization
            study_id: Study ID for organization
            image_format: Target format (auto, jpg, png, etc.)
            
        Returns:
            Dictionary containing file information
        """
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create directory structure
            patient_dir = self.base_path / "converted" / patient_id / study_id
            patient_dir.mkdir(parents=True, exist_ok=True)
            
            # Get original file info
            original_path = Path(file_path)
            original_extension = original_path.suffix.lower()
            
            # Determine output format
            if image_format == 'auto':
                if original_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                    output_format = original_extension
                else:
                    output_format = '.png'  # Default for DICOM conversion
            else:
                output_format = f'.{image_format.lower()}'
            
            # Generate filename
            filename = f"{file_id}_{timestamp}{output_format}"
            dest_path = patient_dir / filename
            
            # Copy/convert file
            if original_extension in ['.dcm', '.dicom']:
                # Convert DICOM to standard image format
                success = self._convert_dicom_to_image(file_path, str(dest_path), output_format)
                if not success:
                    raise Exception("Failed to convert DICOM file")
            else:
                # Copy standard image file
                shutil.copy2(file_path, dest_path)
            
            # Get file info
            file_size = dest_path.stat().st_size
            file_hash = self._calculate_file_hash(dest_path)
            
            # Generate thumbnail
            thumbnail_path = self._generate_thumbnail(dest_path, patient_id, study_id, file_id)
            
            # Get image properties
            image_props = self._get_image_properties(dest_path)
            
            logger.info(f"Medical image saved: {dest_path} (size: {file_size} bytes)")
            
            return {
                'file_path': str(dest_path),
                'file_url': f"/uploads/medical_images/converted/{patient_id}/{study_id}/{filename}",
                'thumbnail_path': thumbnail_path,
                'thumbnail_url': f"/uploads/medical_images/thumbnails/{patient_id}/{study_id}/{file_id}_thumb.jpg",
                'file_size_bytes': file_size,
                'file_hash': file_hash,
                'filename': filename,
                'image_properties': image_props,
                'original_filename': original_path.name
            }
            
        except Exception as e:
            logger.error(f"Failed to save medical image: {e}")
            raise
    
    def save_dicom_file(
        self, 
        file_path: str, 
        patient_id: str, 
        study_id: str,
        series_id: str
    ) -> Dict[str, Any]:
        """
        Save a DICOM file to storage.
        
        Args:
            file_path: Path to the DICOM file
            patient_id: Patient ID for organization
            study_id: Study ID for organization
            series_id: Series ID for organization
            
        Returns:
            Dictionary containing file information
        """
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create directory structure
            patient_dir = self.base_path / "dicom" / patient_id / study_id / series_id
            patient_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{file_id}_{timestamp}.dcm"
            dest_path = patient_dir / filename
            
            # Copy DICOM file
            shutil.copy2(file_path, dest_path)
            
            # Get file info
            file_size = dest_path.stat().st_size
            file_hash = self._calculate_file_hash(dest_path)
            
            logger.info(f"DICOM file saved: {dest_path} (size: {file_size} bytes)")
            
            return {
                'file_path': str(dest_path),
                'file_url': f"/uploads/medical_images/dicom/{patient_id}/{study_id}/{series_id}/{filename}",
                'file_size_bytes': file_size,
                'file_hash': file_hash,
                'filename': filename,
                'original_filename': Path(file_path).name
            }
            
        except Exception as e:
            logger.error(f"Failed to save DICOM file: {e}")
            raise
    
    def _convert_dicom_to_image(self, dicom_path: str, output_path: str, format: str) -> bool:
        """Convert DICOM file to standard image format."""
        try:
            # Import here to avoid circular imports
            from apps.medical_records.utils.dicom_processor import dicom_processor
            
            return dicom_processor.convert_dicom_to_image(dicom_path, output_path, format.lstrip('.').upper())
            
        except Exception as e:
            logger.error(f"Failed to convert DICOM to image: {e}")
            return False
    
    def _generate_thumbnail(
        self, 
        image_path: Path, 
        patient_id: str, 
        study_id: str, 
        file_id: str,
        size: Tuple[int, int] = (200, 200)
    ) -> Optional[str]:
        """Generate thumbnail for medical image."""
        try:
            # Create thumbnail directory
            thumb_dir = self.base_path / "thumbnails" / patient_id / study_id
            thumb_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate thumbnail path
            thumb_filename = f"{file_id}_thumb.jpg"
            thumb_path = thumb_dir / thumb_filename
            
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumb_path, 'JPEG', quality=85)
            
            logger.info(f"Thumbnail generated: {thumb_path}")
            return str(thumb_path)
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None
    
    def _get_image_properties(self, image_path: Path) -> Dict[str, Any]:
        """Get image properties."""
        try:
            with Image.open(image_path) as img:
                return {
                    'width_pixels': img.width,
                    'height_pixels': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'color_space': self._get_color_space(img.mode),
                    'bit_depth': self._get_bit_depth(img)
                }
        except Exception as e:
            logger.error(f"Failed to get image properties: {e}")
            return {}
    
    def _get_color_space(self, mode: str) -> str:
        """Get color space from PIL mode."""
        color_spaces = {
            'L': 'Grayscale',
            'RGB': 'RGB',
            'RGBA': 'RGBA',
            'CMYK': 'CMYK',
            'YCbCr': 'YCbCr',
            'LAB': 'LAB',
            'HSV': 'HSV',
            'I': 'Grayscale',
            'F': 'Grayscale'
        }
        return color_spaces.get(mode, 'Unknown')
    
    def _get_bit_depth(self, img: Image.Image) -> int:
        """Get bit depth of image."""
        try:
            if img.mode == 'L':
                return 8
            elif img.mode == 'I':
                return 32
            elif img.mode == 'F':
                return 32
            elif img.mode in ('RGB', 'RGBA', 'CMYK'):
                return 24
            else:
                return 8
        except:
            return 8
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def delete_image(self, file_path: str) -> bool:
        """
        Delete an image file and its thumbnail.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            # Delete main file
            file_path.unlink()
            
            # Try to delete thumbnail
            try:
                # Extract file ID from filename
                filename = file_path.stem
                if '_' in filename:
                    file_id = filename.split('_')[0]
                    
                    # Find and delete thumbnail
                    thumb_pattern = f"{file_id}_thumb.jpg"
                    for thumb_file in file_path.parent.glob(thumb_pattern):
                        thumb_file.unlink()
                        logger.info(f"Deleted thumbnail: {thumb_file}")
            except Exception as e:
                logger.warning(f"Failed to delete thumbnail: {e}")
            
            logger.info(f"Deleted image: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete image {file_path}: {e}")
            return False
    
    def get_image_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary containing image information or None if not found
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            # Get image properties
            image_props = self._get_image_properties(file_path)
            
            return {
                'file_path': str(file_path),
                'file_size_bytes': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'file_hash': self._calculate_file_hash(file_path),
                'image_properties': image_props
            }
            
        except Exception as e:
            logger.error(f"Failed to get image info for {file_path}: {e}")
            return None
    
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
            
            logger.info(f"Cleaned up {cleaned_count} temporary image files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp image files: {e}")
            return 0


# Global medical image storage instance
medical_image_storage = MedicalImageStorage()
