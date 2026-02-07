"""
OCR Processing Utilities for Medical Documents
Handles OCR processing using Tesseract and LayoutLM for medical document analysis.
"""

import os
import tempfile
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

from common.utils.logging import get_logger

logger = get_logger(__name__)


class OCRProcessor:
    """OCR processor for medical documents."""
    
    def __init__(self):
        """Initialize OCR processor."""
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        self.tesseract_config = '--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
        
    def process_document(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Process a document for OCR text extraction.
        
        Args:
            file_path: Path to the document file
            file_type: Type of document (pdf, image, etc.)
            
        Returns:
            Dictionary containing OCR results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting OCR processing for {file_path}")
            
            if file_type.lower() == 'pdf':
                result = self._process_pdf(file_path)
            elif file_type.lower() in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
                result = self._process_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            result.update({
                'processing_time_ms': int(processing_time),
                'file_path': file_path,
                'file_type': file_type
            })
            
            logger.info(f"OCR processing completed in {processing_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"OCR processing failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0.0,
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    def _process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF document for OCR."""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            full_text = ""
            total_confidence = 0.0
            page_count = len(images)
            
            for i, image in enumerate(images):
                logger.info(f"Processing PDF page {i+1}/{page_count}")
                
                # Convert PIL image to format suitable for OCR
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    image.save(temp_file.name, 'PNG')
                    temp_path = temp_file.name
                
                try:
                    # Perform OCR on the page
                    page_result = self._perform_ocr(temp_path)
                    full_text += f"\n--- Page {i+1} ---\n{page_result['text']}\n"
                    total_confidence += page_result['confidence']
                    
                finally:
                    # Clean up temporary file
                    os.unlink(temp_path)
            
            avg_confidence = total_confidence / page_count if page_count > 0 else 0.0
            
            return {
                'success': True,
                'text': full_text.strip(),
                'confidence': avg_confidence,
                'page_count': page_count,
                'method': 'tesseract_pdf'
            }
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise
    
    def _process_image(self, image_path: str) -> Dict[str, Any]:
        """Process image document for OCR."""
        try:
            result = self._perform_ocr(image_path)
            result['method'] = 'tesseract_image'
            return result
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise
    
    def _perform_ocr(self, image_path: str) -> Dict[str, Any]:
        """Perform OCR on an image using Tesseract."""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            # Get confidence data
            data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'success': True,
                'text': text.strip(),
                'confidence': avg_confidence / 100.0  # Normalize to 0-1 range
            }
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise
    
    def extract_medical_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract medical-specific metadata from OCR text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            'lab_values': [],
            'dates': [],
            'measurements': [],
            'medical_terms': [],
            'patient_info': {}
        }
        
        try:
            # Extract dates (various formats)
            import re
            date_patterns = [
                r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
                r'\d{4}-\d{2}-\d{2}',        # YYYY-MM-DD
                r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
            ]
            
            for pattern in date_patterns:
                dates = re.findall(pattern, text)
                metadata['dates'].extend(dates)
            
            # Extract lab values (number + unit patterns)
            lab_patterns = [
                r'(\d+\.?\d*)\s*(mg/dL|g/dL|mmol/L|mEq/L|ng/mL|pg/mL|U/L|IU/L|%|cells/μL)',
                r'(\d+\.?\d*)\s*(mg|g|mmol|mEq|ng|pg|U|IU)',
            ]
            
            for pattern in lab_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                metadata['lab_values'].extend([f"{value} {unit}" for value, unit in matches])
            
            # Extract measurements
            measurement_patterns = [
                r'(\d+\.?\d*)\s*(cm|mm|in|ft|kg|lb|°F|°C)',
            ]
            
            for pattern in measurement_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                metadata['measurements'].extend([f"{value} {unit}" for value, unit in matches])
            
            # Extract common medical terms
            medical_terms = [
                'normal', 'abnormal', 'elevated', 'decreased', 'high', 'low',
                'positive', 'negative', 'critical', 'urgent', 'routine',
                'fasting', 'random', 'postprandial', 'baseline'
            ]
            
            for term in medical_terms:
                if term.lower() in text.lower():
                    metadata['medical_terms'].append(term)
            
            # Remove duplicates
            metadata['dates'] = list(set(metadata['dates']))
            metadata['lab_values'] = list(set(metadata['lab_values']))
            metadata['measurements'] = list(set(metadata['measurements']))
            metadata['medical_terms'] = list(set(metadata['medical_terms']))
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
        
        return metadata


# Global OCR processor instance
ocr_processor = OCRProcessor()
