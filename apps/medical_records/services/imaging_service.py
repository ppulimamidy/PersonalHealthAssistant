"""
Imaging Service for Medical Records
Handles imaging studies, medical images, and DICOM management.
"""

import os
import tempfile
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, UploadFile

from apps.medical_records.models.imaging import (
    ImagingStudyDB, MedicalImageDB, DICOMSeriesDB, DICOMInstanceDB
)
from apps.medical_records.schemas.imaging import (
    ImagingStudyCreate, ImagingStudyUpdate, ImagingStudyResponse,
    MedicalImageCreate, MedicalImageUpdate, MedicalImageResponse,
    ImagingStudyListResponse, MedicalImageListResponse,
    ModalityType, BodyPartType, StudyStatus, ImageFormat, ImageQuality
)
from apps.medical_records.utils.dicom_processor import dicom_processor
from apps.medical_records.utils.image_storage import medical_image_storage
from common.database.connection import get_session
from common.utils.logging import get_logger

logger = get_logger(__name__)


class ImagingService:
    """Service for managing medical imaging studies and images."""
    
    def __init__(self):
        """Initialize imaging service."""
        pass
    
    async def create_imaging_study(
        self, 
        study_data: ImagingStudyCreate,
        db: Session
    ) -> ImagingStudyResponse:
        """
        Create a new imaging study.
        
        Args:
            study_data: Study creation data
            db: Database session
            
        Returns:
            Created imaging study
        """
        try:
            # Create study record
            study = ImagingStudyDB(
                id=uuid4(),
                patient_id=study_data.patient_id,
                study_name=study_data.study_name,
                modality=study_data.modality,
                body_part=study_data.body_part,
                study_date=study_data.study_date or datetime.utcnow(),
                study_description=study_data.study_description,
                referring_physician=study_data.referring_physician,
                performing_physician=study_data.performing_physician,
                study_status=study_data.study_status,
                study_notes=study_data.study_notes,
                external_id=study_data.external_id,
                fhir_resource_id=study_data.fhir_resource_id,
                study_metadata=study_data.study_metadata
            )
            
            db.add(study)
            db.commit()
            db.refresh(study)
            
            logger.info(f"Created imaging study: {study.id} for patient {study_data.patient_id}")
            
            return ImagingStudyResponse.from_orm(study)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create imaging study: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create imaging study: {str(e)}")
    
    async def get_imaging_study(
        self, 
        study_id: UUID,
        db: Session
    ) -> ImagingStudyResponse:
        """
        Get an imaging study by ID.
        
        Args:
            study_id: Study ID
            db: Database session
            
        Returns:
            Imaging study
        """
        try:
            study = db.query(ImagingStudyDB).filter(ImagingStudyDB.id == study_id).first()
            
            if not study:
                raise HTTPException(status_code=404, detail="Imaging study not found")
            
            # Get image count and total size
            image_stats = db.query(
                func.count(MedicalImageDB.id).label('image_count'),
                func.coalesce(func.sum(MedicalImageDB.file_size_bytes), 0).label('total_size')
            ).filter(MedicalImageDB.study_id == study_id).first()
            
            study_dict = ImagingStudyResponse.from_orm(study).dict()
            study_dict['image_count'] = image_stats.image_count
            study_dict['total_size_bytes'] = image_stats.total_size
            
            return ImagingStudyResponse(**study_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get imaging study {study_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get imaging study: {str(e)}")
    
    async def update_imaging_study(
        self, 
        study_id: UUID,
        study_data: ImagingStudyUpdate,
        db: Session
    ) -> ImagingStudyResponse:
        """
        Update an imaging study.
        
        Args:
            study_id: Study ID
            study_data: Study update data
            db: Database session
            
        Returns:
            Updated imaging study
        """
        try:
            study = db.query(ImagingStudyDB).filter(ImagingStudyDB.id == study_id).first()
            
            if not study:
                raise HTTPException(status_code=404, detail="Imaging study not found")
            
            # Update fields
            update_data = study_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(study, field, value)
            
            study.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(study)
            
            logger.info(f"Updated imaging study: {study_id}")
            
            return ImagingStudyResponse.from_orm(study)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update imaging study {study_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update imaging study: {str(e)}")
    
    async def delete_imaging_study(
        self, 
        study_id: UUID,
        db: Session
    ) -> bool:
        """
        Delete an imaging study and all associated images.
        
        Args:
            study_id: Study ID
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            study = db.query(ImagingStudyDB).filter(ImagingStudyDB.id == study_id).first()
            
            if not study:
                raise HTTPException(status_code=404, detail="Imaging study not found")
            
            # Get all images in the study
            images = db.query(MedicalImageDB).filter(MedicalImageDB.study_id == study_id).all()
            
            # Delete image files
            for image in images:
                if image.file_path:
                    medical_image_storage.delete_image(image.file_path)
            
            # Delete database records
            db.query(MedicalImageDB).filter(MedicalImageDB.study_id == study_id).delete()
            db.query(DICOMInstanceDB).join(DICOMSeriesDB).filter(DICOMSeriesDB.study_id == study_id).delete()
            db.query(DICOMSeriesDB).filter(DICOMSeriesDB.study_id == study_id).delete()
            db.delete(study)
            
            db.commit()
            
            logger.info(f"Deleted imaging study: {study_id}")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete imaging study {study_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete imaging study: {str(e)}")
    
    async def list_imaging_studies(
        self,
        patient_id: Optional[UUID] = None,
        modality: Optional[ModalityType] = None,
        status: Optional[StudyStatus] = None,
        page: int = 1,
        size: int = 20,
        db: Session = None
    ) -> ImagingStudyListResponse:
        """
        List imaging studies with filtering and pagination.
        
        Args:
            patient_id: Filter by patient ID
            modality: Filter by modality
            status: Filter by study status
            page: Page number
            size: Page size
            db: Database session
            
        Returns:
            Paginated list of imaging studies
        """
        try:
            query = db.query(ImagingStudyDB)
            
            # Apply filters
            if patient_id:
                query = query.filter(ImagingStudyDB.patient_id == patient_id)
            if modality:
                query = query.filter(ImagingStudyDB.modality == modality)
            if status:
                query = query.filter(ImagingStudyDB.study_status == status)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            studies = query.order_by(desc(ImagingStudyDB.created_at)).offset((page - 1) * size).limit(size).all()
            
            # Convert to response models
            study_responses = []
            for study in studies:
                # Get image count and total size
                image_stats = db.query(
                    func.count(MedicalImageDB.id).label('image_count'),
                    func.coalesce(func.sum(MedicalImageDB.file_size_bytes), 0).label('total_size')
                ).filter(MedicalImageDB.study_id == study.id).first()
                
                study_dict = ImagingStudyResponse.from_orm(study).dict()
                study_dict['image_count'] = image_stats.image_count
                study_dict['total_size_bytes'] = image_stats.total_size
                
                study_responses.append(ImagingStudyResponse(**study_dict))
            
            pages = (total + size - 1) // size
            
            return ImagingStudyListResponse(
                items=study_responses,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list imaging studies: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list imaging studies: {str(e)}")
    
    async def upload_medical_image(
        self,
        study_id: UUID,
        image_file: UploadFile,
        image_data: MedicalImageCreate,
        db: Session
    ) -> MedicalImageResponse:
        """
        Upload a medical image to a study.
        
        Args:
            study_id: Study ID
            image_file: Uploaded image file
            image_data: Image metadata
            db: Database session
            
        Returns:
            Created medical image
        """
        try:
            # Verify study exists
            study = db.query(ImagingStudyDB).filter(ImagingStudyDB.id == study_id).first()
            if not study:
                raise HTTPException(status_code=404, detail="Imaging study not found")
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(image_file.filename).suffix) as temp_file:
                content = await image_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Save image to storage
                storage_info = medical_image_storage.save_medical_image(
                    temp_file_path,
                    str(study.patient_id),
                    str(study_id),
                    image_data.image_format.value if image_data.image_format else 'auto'
                )
                
                # Create image record
                image = MedicalImageDB(
                    id=uuid4(),
                    study_id=study_id,
                    image_name=image_data.image_name,
                    image_format=image_data.image_format,
                    image_quality=image_data.image_quality,
                    image_description=image_data.image_description,
                    file_path=storage_info['file_path'],
                    file_url=storage_info['file_url'],
                    file_size_bytes=storage_info['file_size_bytes'],
                    width_pixels=storage_info['image_properties'].get('width_pixels'),
                    height_pixels=storage_info['image_properties'].get('height_pixels'),
                    bit_depth=storage_info['image_properties'].get('bit_depth'),
                    color_space=storage_info['image_properties'].get('color_space'),
                    image_metadata=image_data.image_metadata,
                    dicom_metadata=image_data.dicom_metadata
                )
                
                db.add(image)
                db.commit()
                db.refresh(image)
                
                logger.info(f"Uploaded medical image: {image.id} to study {study_id}")
                
                return MedicalImageResponse.from_orm(image)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to upload medical image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload medical image: {str(e)}")
    
    async def upload_dicom_file(
        self,
        study_id: UUID,
        dicom_file: UploadFile,
        db: Session
    ) -> Dict[str, Any]:
        """
        Upload a DICOM file to a study.
        
        Args:
            study_id: Study ID
            dicom_file: Uploaded DICOM file
            db: Database session
            
        Returns:
            Processing result
        """
        try:
            # Verify study exists
            study = db.query(ImagingStudyDB).filter(ImagingStudyDB.id == study_id).first()
            if not study:
                raise HTTPException(status_code=404, detail="Imaging study not found")
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as temp_file:
                content = await dicom_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Process DICOM file
                dicom_result = dicom_processor.process_dicom_file(temp_file_path)
                
                if not dicom_result['success']:
                    raise HTTPException(status_code=400, detail=f"DICOM processing failed: {dicom_result['error']}")
                
                # Validate DICOM file
                validation = dicom_processor.validate_dicom_file(temp_file_path)
                if not validation['valid']:
                    raise HTTPException(status_code=400, detail=f"Invalid DICOM file: {validation.get('error', 'Unknown error')}")
                
                # Extract metadata
                metadata = dicom_result['metadata']
                series_info = metadata.get('series_info', {})
                instance_info = metadata.get('instance_info', {})
                
                # Get or create series
                series_instance_uid = series_info.get('series_instance_uid')
                if not series_instance_uid:
                    raise HTTPException(status_code=400, detail="Missing Series Instance UID")
                
                series = db.query(DICOMSeriesDB).filter(
                    DICOMSeriesDB.series_instance_uid == series_instance_uid
                ).first()
                
                if not series:
                    # Create new series
                    series = DICOMSeriesDB(
                        id=uuid4(),
                        study_id=study_id,
                        series_instance_uid=series_instance_uid,
                        series_number=series_info.get('series_number'),
                        series_description=series_info.get('series_description'),
                        modality=ModalityType(series_info.get('modality', 'OT')),
                        body_part_examined=series_info.get('body_part_examined'),
                        series_date=datetime.strptime(series_info.get('series_date', ''), '%Y%m%d') if series_info.get('series_date') else None,
                        series_time=series_info.get('series_time'),
                        manufacturer=metadata.get('technical_info', {}).get('manufacturer'),
                        model_name=metadata.get('technical_info', {}).get('model_name'),
                        station_name=metadata.get('technical_info', {}).get('station_name'),
                        series_metadata=series_info
                    )
                    db.add(series)
                    db.flush()
                
                # Save DICOM file
                storage_info = medical_image_storage.save_dicom_file(
                    temp_file_path,
                    str(study.patient_id),
                    str(study_id),
                    str(series.id)
                )
                
                # Create DICOM instance record
                sop_instance_uid = instance_info.get('sop_instance_uid')
                if not sop_instance_uid:
                    raise HTTPException(status_code=400, detail="Missing SOP Instance UID")
                
                instance = DICOMInstanceDB(
                    id=uuid4(),
                    series_id=series.id,
                    sop_instance_uid=sop_instance_uid,
                    instance_number=instance_info.get('instance_number'),
                    acquisition_date=datetime.strptime(instance_info.get('acquisition_date', ''), '%Y%m%d') if instance_info.get('acquisition_date') else None,
                    acquisition_time=instance_info.get('acquisition_time'),
                    rows=metadata.get('image_info', {}).get('rows'),
                    columns=metadata.get('image_info', {}).get('columns'),
                    bits_allocated=metadata.get('image_info', {}).get('bits_allocated'),
                    bits_stored=metadata.get('image_info', {}).get('bits_stored'),
                    high_bit=metadata.get('image_info', {}).get('high_bit'),
                    pixel_representation=metadata.get('image_info', {}).get('pixel_representation'),
                    samples_per_pixel=metadata.get('image_info', {}).get('samples_per_pixel'),
                    photometric_interpretation=metadata.get('image_info', {}).get('photometric_interpretation'),
                    file_path=storage_info['file_path'],
                    file_size_bytes=storage_info['file_size_bytes'],
                    instance_metadata=instance_info
                )
                
                db.add(instance)
                db.commit()
                
                logger.info(f"Uploaded DICOM file: {instance.id} to series {series.id}")
                
                return {
                    'success': True,
                    'instance_id': str(instance.id),
                    'series_id': str(series.id),
                    'sop_instance_uid': sop_instance_uid,
                    'file_path': storage_info['file_path'],
                    'file_size_bytes': storage_info['file_size_bytes'],
                    'metadata': metadata
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to upload DICOM file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload DICOM file: {str(e)}")
    
    async def get_medical_image(
        self,
        image_id: UUID,
        db: Session
    ) -> MedicalImageResponse:
        """
        Get a medical image by ID.
        
        Args:
            image_id: Image ID
            db: Database session
            
        Returns:
            Medical image
        """
        try:
            image = db.query(MedicalImageDB).filter(MedicalImageDB.id == image_id).first()
            
            if not image:
                raise HTTPException(status_code=404, detail="Medical image not found")
            
            return MedicalImageResponse.from_orm(image)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get medical image {image_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get medical image: {str(e)}")
    
    async def list_medical_images(
        self,
        study_id: UUID,
        page: int = 1,
        size: int = 20,
        db: Session = None
    ) -> MedicalImageListResponse:
        """
        List medical images in a study.
        
        Args:
            study_id: Study ID
            page: Page number
            size: Page size
            db: Database session
            
        Returns:
            Paginated list of medical images
        """
        try:
            query = db.query(MedicalImageDB).filter(MedicalImageDB.study_id == study_id)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            images = query.order_by(desc(MedicalImageDB.created_at)).offset((page - 1) * size).limit(size).all()
            
            # Convert to response models
            image_responses = [MedicalImageResponse.from_orm(image) for image in images]
            
            pages = (total + size - 1) // size
            
            return MedicalImageListResponse(
                items=image_responses,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list medical images: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list medical images: {str(e)}")
    
    async def delete_medical_image(
        self,
        image_id: UUID,
        db: Session
    ) -> bool:
        """
        Delete a medical image.
        
        Args:
            image_id: Image ID
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            image = db.query(MedicalImageDB).filter(MedicalImageDB.id == image_id).first()
            
            if not image:
                raise HTTPException(status_code=404, detail="Medical image not found")
            
            # Delete file
            if image.file_path:
                medical_image_storage.delete_image(image.file_path)
            
            # Delete database record
            db.delete(image)
            db.commit()
            
            logger.info(f"Deleted medical image: {image_id}")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete medical image {image_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete medical image: {str(e)}")


# Global imaging service instance
imaging_service = ImagingService()
