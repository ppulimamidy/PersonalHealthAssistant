"""
Genomic data service for Personal Health Assistant.

This service handles genomic data management including:
- File upload and storage
- Quality assessment
- Data processing
- File validation
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import aiofiles

from ..models.genomic_data import (
    GenomicData, GenomicDataCreate, GenomicDataUpdate, GenomicDataResponse,
    DataSource, DataFormat, QualityStatus
)
from common.exceptions import NotFoundError, ValidationError


class GenomicDataService:
    """Service for managing genomic data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = "/app/genomic_data"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def create_genomic_data(
        self, 
        data: GenomicDataCreate, 
        user_id: uuid.UUID
    ) -> GenomicDataResponse:
        """Create new genomic data record."""
        try:
            # Create genomic data record
            genomic_data = GenomicData(
                user_id=user_id,
                data_source=data.data_source,
                data_format=data.data_format,
                file_path=data.file_path,
                file_size=data.file_size,
                checksum=data.checksum,
                sample_id=data.sample_id,
                collection_date=data.collection_date,
                lab_name=data.lab_name,
                test_name=data.test_name,
                metadata=data.metadata
            )
            
            self.db.add(genomic_data)
            self.db.commit()
            self.db.refresh(genomic_data)
            
            return GenomicDataResponse.from_orm(genomic_data)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create genomic data: {str(e)}")
    
    async def list_genomic_data(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        data_source: Optional[DataSource] = None,
        data_format: Optional[DataFormat] = None,
        quality_status: Optional[QualityStatus] = None
    ) -> List[GenomicDataResponse]:
        """List genomic data for user."""
        try:
            query = self.db.query(GenomicData).filter(GenomicData.user_id == user_id)
            
            if data_source:
                query = query.filter(GenomicData.data_source == data_source)
            if data_format:
                query = query.filter(GenomicData.data_format == data_format)
            if quality_status:
                query = query.filter(GenomicData.quality_status == quality_status)
            
            genomic_data_list = query.offset(skip).limit(limit).all()
            return [GenomicDataResponse.from_orm(data) for data in genomic_data_list]
        except Exception as e:
            raise ValidationError(f"Failed to list genomic data: {str(e)}")
    
    async def get_genomic_data(
        self, 
        data_id: str, 
        user_id: uuid.UUID
    ) -> GenomicDataResponse:
        """Get specific genomic data by ID."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            return GenomicDataResponse.from_orm(genomic_data)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get genomic data: {str(e)}")
    
    async def update_genomic_data(
        self,
        data_id: str,
        data: GenomicDataUpdate,
        user_id: uuid.UUID
    ) -> GenomicDataResponse:
        """Update genomic data."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            # Update fields
            update_data = data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(genomic_data, field, value)
            
            genomic_data.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(genomic_data)
            
            return GenomicDataResponse.from_orm(genomic_data)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update genomic data: {str(e)}")
    
    async def delete_genomic_data(
        self, 
        data_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete genomic data."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            # Delete file if exists
            if os.path.exists(genomic_data.file_path):
                os.remove(genomic_data.file_path)
            
            self.db.delete(genomic_data)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete genomic data: {str(e)}")
    
    async def upload_genomic_file(
        self,
        file: UploadFile,
        user_id: uuid.UUID,
        data_source: DataSource,
        sample_id: Optional[str] = None,
        collection_date: Optional[str] = None,
        lab_name: Optional[str] = None,
        test_name: Optional[str] = None
    ) -> GenomicDataResponse:
        """Upload genomic data file."""
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ".txt"
            filename = f"{file_id}{file_extension}"
            file_path = os.path.join(self.upload_dir, filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Calculate file size and checksum
            file_size = len(content)
            checksum = hashlib.md5(content).hexdigest()
            
            # Determine data format
            data_format = self._determine_data_format(file.filename, content)
            
            # Create genomic data record
            genomic_data = GenomicData(
                user_id=user_id,
                data_source=data_source,
                data_format=data_format,
                file_path=file_path,
                file_size=file_size,
                checksum=checksum,
                sample_id=sample_id,
                collection_date=datetime.fromisoformat(collection_date) if collection_date else None,
                lab_name=lab_name,
                test_name=test_name,
                metadata={
                    "original_filename": file.filename,
                    "content_type": file.content_type
                }
            )
            
            self.db.add(genomic_data)
            self.db.commit()
            self.db.refresh(genomic_data)
            
            return GenomicDataResponse.from_orm(genomic_data)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to upload genomic file: {str(e)}")
    
    async def get_file_path(
        self, 
        data_id: str, 
        user_id: uuid.UUID
    ) -> str:
        """Get file path for genomic data."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            if not os.path.exists(genomic_data.file_path):
                raise NotFoundError("File not found")
            
            return genomic_data.file_path
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get file path: {str(e)}")
    
    async def process_genomic_data(
        self, 
        data_id: str, 
        user_id: uuid.UUID
    ) -> GenomicDataResponse:
        """Process genomic data for analysis."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            # Update processing status
            genomic_data.is_processed = True
            genomic_data.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(genomic_data)
            
            return GenomicDataResponse.from_orm(genomic_data)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to process genomic data: {str(e)}")
    
    async def get_quality_metrics(
        self, 
        data_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get quality metrics for genomic data."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            return {
                "quality_score": genomic_data.quality_score,
                "quality_status": genomic_data.quality_status,
                "coverage_depth": genomic_data.coverage_depth,
                "coverage_breadth": genomic_data.coverage_breadth,
                "file_size": genomic_data.file_size,
                "checksum": genomic_data.checksum
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get quality metrics: {str(e)}")
    
    async def validate_genomic_data(
        self, 
        data_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Validate genomic data format and quality."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            # Perform validation based on data format
            validation_result = await self._validate_data_format(genomic_data)
            
            # Update quality metrics
            genomic_data.quality_score = validation_result.get("quality_score")
            genomic_data.quality_status = validation_result.get("quality_status")
            genomic_data.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return validation_result
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to validate genomic data: {str(e)}")
    
    async def get_processing_status(
        self, 
        data_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get processing status of genomic data."""
        try:
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise NotFoundError("Genomic data not found")
            
            return {
                "is_processed": genomic_data.is_processed,
                "is_analyzed": genomic_data.is_analyzed,
                "is_archived": genomic_data.is_archived,
                "quality_status": genomic_data.quality_status,
                "created_at": genomic_data.created_at,
                "updated_at": genomic_data.updated_at
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get processing status: {str(e)}")
    
    def _determine_data_format(self, filename: str, content: bytes) -> DataFormat:
        """Determine data format from filename and content."""
        if filename:
            filename_lower = filename.lower()
            if filename_lower.endswith('.fastq') or filename_lower.endswith('.fq'):
                return DataFormat.FASTQ
            elif filename_lower.endswith('.bam'):
                return DataFormat.BAM
            elif filename_lower.endswith('.vcf'):
                return DataFormat.VCF
            elif filename_lower.endswith('.gff'):
                return DataFormat.GFF
            elif filename_lower.endswith('.bed'):
                return DataFormat.BED
            elif filename_lower.endswith('.json'):
                return DataFormat.JSON
            elif filename_lower.endswith('.csv'):
                return DataFormat.CSV
            elif filename_lower.endswith('.txt'):
                return DataFormat.TXT
        
        # Try to determine from content
        content_str = content.decode('utf-8', errors='ignore')[:1000]
        
        if content_str.startswith('@') or '\t' in content_str:
            return DataFormat.FASTQ
        elif '##fileformat=VCF' in content_str:
            return DataFormat.VCF
        elif content_str.startswith('{') or content_str.startswith('['):
            return DataFormat.JSON
        elif ',' in content_str:
            return DataFormat.CSV
        
        return DataFormat.TXT
    
    async def _validate_data_format(self, genomic_data: GenomicData) -> Dict[str, Any]:
        """Validate data format and calculate quality metrics."""
        try:
            if not os.path.exists(genomic_data.file_path):
                return {
                    "valid": False,
                    "quality_score": 0.0,
                    "quality_status": QualityStatus.POOR,
                    "error": "File not found"
                }
            
            # Read file content
            async with aiofiles.open(genomic_data.file_path, 'r') as f:
                content = await f.read(10000)  # Read first 10KB
            
            validation_result = {
                "valid": True,
                "quality_score": 0.8,  # Default score
                "quality_status": QualityStatus.GOOD,
                "format": genomic_data.data_format,
                "file_size": genomic_data.file_size
            }
            
            # Format-specific validation
            if genomic_data.data_format == DataFormat.FASTQ:
                validation_result.update(self._validate_fastq(content))
            elif genomic_data.data_format == DataFormat.VCF:
                validation_result.update(self._validate_vcf(content))
            elif genomic_data.data_format == DataFormat.JSON:
                validation_result.update(self._validate_json(content))
            
            return validation_result
        except Exception as e:
            return {
                "valid": False,
                "quality_score": 0.0,
                "quality_status": QualityStatus.POOR,
                "error": str(e)
            }
    
    def _validate_fastq(self, content: str) -> Dict[str, Any]:
        """Validate FASTQ format."""
        lines = content.split('\n')
        if len(lines) < 4:
            return {"valid": False, "quality_score": 0.0, "quality_status": QualityStatus.POOR}
        
        # Check if first line starts with @
        if not lines[0].startswith('@'):
            return {"valid": False, "quality_score": 0.0, "quality_status": QualityStatus.POOR}
        
        return {"valid": True, "quality_score": 0.9, "quality_status": QualityStatus.EXCELLENT}
    
    def _validate_vcf(self, content: str) -> Dict[str, Any]:
        """Validate VCF format."""
        lines = content.split('\n')
        
        # Check for VCF header
        header_found = False
        for line in lines:
            if line.startswith('##fileformat=VCF'):
                header_found = True
                break
        
        if not header_found:
            return {"valid": False, "quality_score": 0.0, "quality_status": QualityStatus.POOR}
        
        return {"valid": True, "quality_score": 0.9, "quality_status": QualityStatus.EXCELLENT}
    
    def _validate_json(self, content: str) -> Dict[str, Any]:
        """Validate JSON format."""
        try:
            import json
            json.loads(content)
            return {"valid": True, "quality_score": 0.9, "quality_status": QualityStatus.EXCELLENT}
        except json.JSONDecodeError:
            return {"valid": False, "quality_score": 0.0, "quality_status": QualityStatus.POOR} 