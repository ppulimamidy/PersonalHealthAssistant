"""
DICOM Processing Utilities for Medical Imaging
Handles DICOM file processing, metadata extraction, and image conversion.
"""

import os
import tempfile
import time
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import logging
import shutil
import hashlib
from datetime import datetime
import uuid

try:
    import pydicom
    from pydicom.dataset import Dataset
    from pydicom.uid import generate_uid
    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False
    pydicom = None

from PIL import Image
import numpy as np

from common.utils.logging import get_logger

logger = get_logger(__name__)


class DICOMProcessor:
    """DICOM file processor for medical imaging."""
    
    def __init__(self):
        """Initialize DICOM processor."""
        if not DICOM_AVAILABLE:
            logger.warning("pydicom not available. DICOM processing will be limited.")
        
        self.supported_formats = ['.dcm', '.dicom']
        self.image_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    
    def process_dicom_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a DICOM file and extract metadata.
        
        Args:
            file_path: Path to the DICOM file
            
        Returns:
            Dictionary containing DICOM metadata and processing results
        """
        start_time = time.time()
        
        try:
            if not DICOM_AVAILABLE:
                return {
                    'success': False,
                    'error': 'pydicom not available',
                    'processing_time_ms': int((time.time() - start_time) * 1000)
                }
            
            logger.info(f"Processing DICOM file: {file_path}")
            
            # Read DICOM file
            ds = pydicom.dcmread(file_path)
            
            # Extract metadata
            metadata = self._extract_dicom_metadata(ds)
            
            # Extract image data if available
            image_data = self._extract_image_data(ds)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                'success': True,
                'metadata': metadata,
                'image_data': image_data,
                'processing_time_ms': int(processing_time),
                'file_path': file_path
            }
            
            logger.info(f"DICOM processing completed in {processing_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"DICOM processing failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    def _extract_dicom_metadata(self, ds: "Dataset") -> Dict[str, Any]:
        """Extract metadata from DICOM dataset."""
        metadata = {
            'patient_info': {},
            'study_info': {},
            'series_info': {},
            'instance_info': {},
            'technical_info': {},
            'image_info': {}
        }
        
        try:
            # Patient Information
            if hasattr(ds, 'PatientName'):
                metadata['patient_info']['name'] = str(ds.PatientName)
            if hasattr(ds, 'PatientID'):
                metadata['patient_info']['id'] = str(ds.PatientID)
            if hasattr(ds, 'PatientBirthDate'):
                metadata['patient_info']['birth_date'] = str(ds.PatientBirthDate)
            if hasattr(ds, 'PatientSex'):
                metadata['patient_info']['sex'] = str(ds.PatientSex)
            
            # Study Information
            if hasattr(ds, 'StudyInstanceUID'):
                metadata['study_info']['study_instance_uid'] = str(ds.StudyInstanceUID)
            if hasattr(ds, 'StudyDate'):
                metadata['study_info']['study_date'] = str(ds.StudyDate)
            if hasattr(ds, 'StudyTime'):
                metadata['study_info']['study_time'] = str(ds.StudyTime)
            if hasattr(ds, 'StudyDescription'):
                metadata['study_info']['study_description'] = str(ds.StudyDescription)
            if hasattr(ds, 'ReferringPhysicianName'):
                metadata['study_info']['referring_physician'] = str(ds.ReferringPhysicianName)
            if hasattr(ds, 'PerformingPhysicianName'):
                metadata['study_info']['performing_physician'] = str(ds.PerformingPhysicianName)
            
            # Series Information
            if hasattr(ds, 'SeriesInstanceUID'):
                metadata['series_info']['series_instance_uid'] = str(ds.SeriesInstanceUID)
            if hasattr(ds, 'SeriesNumber'):
                metadata['series_info']['series_number'] = int(ds.SeriesNumber)
            if hasattr(ds, 'SeriesDate'):
                metadata['series_info']['series_date'] = str(ds.SeriesDate)
            if hasattr(ds, 'SeriesTime'):
                metadata['series_info']['series_time'] = str(ds.SeriesTime)
            if hasattr(ds, 'SeriesDescription'):
                metadata['series_info']['series_description'] = str(ds.SeriesDescription)
            if hasattr(ds, 'BodyPartExamined'):
                metadata['series_info']['body_part_examined'] = str(ds.BodyPartExamined)
            if hasattr(ds, 'Modality'):
                metadata['series_info']['modality'] = str(ds.Modality)
            
            # Instance Information
            if hasattr(ds, 'SOPInstanceUID'):
                metadata['instance_info']['sop_instance_uid'] = str(ds.SOPInstanceUID)
            if hasattr(ds, 'InstanceNumber'):
                metadata['instance_info']['instance_number'] = int(ds.InstanceNumber)
            if hasattr(ds, 'AcquisitionDate'):
                metadata['instance_info']['acquisition_date'] = str(ds.AcquisitionDate)
            if hasattr(ds, 'AcquisitionTime'):
                metadata['instance_info']['acquisition_time'] = str(ds.AcquisitionTime)
            
            # Technical Information
            if hasattr(ds, 'Manufacturer'):
                metadata['technical_info']['manufacturer'] = str(ds.Manufacturer)
            if hasattr(ds, 'ManufacturerModelName'):
                metadata['technical_info']['model_name'] = str(ds.ManufacturerModelName)
            if hasattr(ds, 'StationName'):
                metadata['technical_info']['station_name'] = str(ds.StationName)
            if hasattr(ds, 'InstitutionName'):
                metadata['technical_info']['institution_name'] = str(ds.InstitutionName)
            
            # Image Information
            if hasattr(ds, 'Rows'):
                metadata['image_info']['rows'] = int(ds.Rows)
            if hasattr(ds, 'Columns'):
                metadata['image_info']['columns'] = int(ds.Columns)
            if hasattr(ds, 'BitsAllocated'):
                metadata['image_info']['bits_allocated'] = int(ds.BitsAllocated)
            if hasattr(ds, 'BitsStored'):
                metadata['image_info']['bits_stored'] = int(ds.BitsStored)
            if hasattr(ds, 'HighBit'):
                metadata['image_info']['high_bit'] = int(ds.HighBit)
            if hasattr(ds, 'PixelRepresentation'):
                metadata['image_info']['pixel_representation'] = int(ds.PixelRepresentation)
            if hasattr(ds, 'SamplesPerPixel'):
                metadata['image_info']['samples_per_pixel'] = int(ds.SamplesPerPixel)
            if hasattr(ds, 'PhotometricInterpretation'):
                metadata['image_info']['photometric_interpretation'] = str(ds.PhotometricInterpretation)
            
        except Exception as e:
            logger.error(f"Error extracting DICOM metadata: {e}")
        
        return metadata
    
    def _extract_image_data(self, ds: "Dataset") -> Optional[Dict[str, Any]]:
        """Extract image data from DICOM dataset."""
        try:
            if not hasattr(ds, 'pixel_array'):
                return None
            
            # Get pixel data
            pixel_array = ds.pixel_array
            
            # Normalize pixel values
            if pixel_array.dtype != np.uint8:
                # Normalize to 0-255 range
                pixel_min = pixel_array.min()
                pixel_max = pixel_array.max()
                if pixel_max > pixel_min:
                    pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
                else:
                    pixel_array = pixel_array.astype(np.uint8)
            
            # Convert to PIL Image
            image = Image.fromarray(pixel_array)
            
            return {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'size_bytes': len(pixel_array.tobytes()),
                'pixel_array_shape': pixel_array.shape,
                'pixel_array_dtype': str(pixel_array.dtype)
            }
            
        except Exception as e:
            logger.error(f"Error extracting image data: {e}")
            return None
    
    def convert_dicom_to_image(self, dicom_path: str, output_path: str, format: str = 'PNG') -> bool:
        """
        Convert DICOM file to standard image format.
        
        Args:
            dicom_path: Path to DICOM file
            output_path: Path for output image
            format: Output format (PNG, JPEG, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not DICOM_AVAILABLE:
                return False
            
            # Read DICOM file
            ds = pydicom.dcmread(dicom_path)
            
            # Extract pixel data
            pixel_array = ds.pixel_array
            
            # Normalize pixel values
            if pixel_array.dtype != np.uint8:
                pixel_min = pixel_array.min()
                pixel_max = pixel_array.max()
                if pixel_max > pixel_min:
                    pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
                else:
                    pixel_array = pixel_array.astype(np.uint8)
            
            # Convert to PIL Image
            image = Image.fromarray(pixel_array)
            
            # Save image
            image.save(output_path, format=format)
            
            logger.info(f"Converted DICOM to {format}: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert DICOM to image: {e}")
            return False
    
    def validate_dicom_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate DICOM file and check for required fields.
        
        Args:
            file_path: Path to DICOM file
            
        Returns:
            Validation result dictionary
        """
        try:
            if not DICOM_AVAILABLE:
                return {
                    'valid': False,
                    'error': 'pydicom not available'
                }
            
            # Read DICOM file
            ds = pydicom.dcmread(file_path)
            
            # Check required fields
            required_fields = ['PatientID', 'StudyInstanceUID', 'SeriesInstanceUID', 'SOPInstanceUID']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(ds, field):
                    missing_fields.append(field)
            
            # Check if it's a valid DICOM file
            is_valid = len(missing_fields) == 0
            
            return {
                'valid': is_valid,
                'missing_fields': missing_fields,
                'file_size': os.path.getsize(file_path),
                'modality': getattr(ds, 'Modality', 'Unknown'),
                'study_date': getattr(ds, 'StudyDate', 'Unknown'),
                'series_number': getattr(ds, 'SeriesNumber', 'Unknown')
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def extract_series_info(self, dicom_files: List[str]) -> Dict[str, Any]:
        """
        Extract series information from multiple DICOM files.
        
        Args:
            dicom_files: List of DICOM file paths
            
        Returns:
            Series information dictionary
        """
        if not DICOM_AVAILABLE:
            return {'error': 'pydicom not available'}
        
        series_info = {
            'total_files': len(dicom_files),
            'series_uid': None,
            'study_uid': None,
            'modality': None,
            'body_part': None,
            'instance_count': 0,
            'total_size_bytes': 0
        }
        
        try:
            for file_path in dicom_files:
                ds = pydicom.dcmread(file_path)
                
                # Get series UID
                if hasattr(ds, 'SeriesInstanceUID'):
                    if series_info['series_uid'] is None:
                        series_info['series_uid'] = str(ds.SeriesInstanceUID)
                    elif series_info['series_uid'] != str(ds.SeriesInstanceUID):
                        logger.warning(f"Multiple series UIDs found in files")
                
                # Get study UID
                if hasattr(ds, 'StudyInstanceUID'):
                    if series_info['study_uid'] is None:
                        series_info['study_uid'] = str(ds.StudyInstanceUID)
                
                # Get modality
                if hasattr(ds, 'Modality'):
                    if series_info['modality'] is None:
                        series_info['modality'] = str(ds.Modality)
                
                # Get body part
                if hasattr(ds, 'BodyPartExamined'):
                    if series_info['body_part'] is None:
                        series_info['body_part'] = str(ds.BodyPartExamined)
                
                # Count instances
                series_info['instance_count'] += 1
                series_info['total_size_bytes'] += os.path.getsize(file_path)
            
        except Exception as e:
            logger.error(f"Error extracting series info: {e}")
            series_info['error'] = str(e)
        
        return series_info


# Global DICOM processor instance
dicom_processor = DICOMProcessor()
