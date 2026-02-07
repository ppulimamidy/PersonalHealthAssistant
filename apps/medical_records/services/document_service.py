"""
Document Service for Medical Records
Handles document CRUD operations, OCR processing, and metadata extraction.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.exc import NoResultFound

from apps.medical_records.models.documents import (
    DocumentDB, DocumentProcessingLogDB, DocumentCreate, DocumentUpdate,
    DocumentResponse, DocumentListResponse, ProcessingStatus, DocumentStatus
)
from apps.medical_records.utils.ocr import ocr_processor
from apps.medical_records.utils.file_storage import file_storage
from common.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Service for managing medical documents."""
    
    def __init__(self):
        """Initialize document service."""
        pass
    
    async def create_document(self, db: AsyncSession, document_data: DocumentCreate) -> DocumentResponse:
        """
        Create a new document.
        
        Args:
            db: Database session
            document_data: Document creation data
            
        Returns:
            Created document response
        """
        try:
            # Create document record
            db_document = DocumentDB(**document_data.dict())
            db.add(db_document)
            await db.commit()
            await db.refresh(db_document)
            
            # Log processing step
            await self._log_processing_step(
                db, db_document.id, "document_creation", 
                ProcessingStatus.COMPLETED, "Document created successfully"
            )
            
            logger.info(f"Document created: {db_document.id}")
            return DocumentResponse.from_orm(db_document)
            
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise
    
    async def get_document(self, db: AsyncSession, document_id: UUID) -> Optional[DocumentResponse]:
        """
        Get a document by ID.
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            Document response or None if not found
        """
        try:
            result = await db.get(DocumentDB, document_id)
            if result:
                return DocumentResponse.from_orm(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise
    
    async def list_documents(
        self, 
        db: AsyncSession, 
        patient_id: UUID,
        skip: int = 0, 
        limit: int = 20,
        document_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> DocumentListResponse:
        """
        List documents for a patient.
        
        Args:
            db: Database session
            patient_id: Patient ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            document_type: Filter by document type
            status: Filter by processing status
            
        Returns:
            Document list response
        """
        try:
            # Build query
            query = select(DocumentDB).where(DocumentDB.patient_id == patient_id)
            
            if document_type:
                query = query.where(DocumentDB.document_type == document_type)
            
            if status:
                query = query.where(DocumentDB.document_status == status)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = (await db.execute(count_query)).scalar()
            
            # Get paginated results
            results = (await db.execute(
                query.order_by(desc(DocumentDB.created_at))
                .offset(skip)
                .limit(limit)
            )).scalars().all()
            
            items = [DocumentResponse.from_orm(r) for r in results]
            
            return DocumentListResponse(
                items=items,
                total=total,
                page=skip // limit + 1,
                size=limit,
                pages=(total + limit - 1) // limit
            )
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise
    
    async def update_document(
        self, 
        db: AsyncSession, 
        document_id: UUID, 
        update_data: DocumentUpdate
    ) -> Optional[DocumentResponse]:
        """
        Update a document.
        
        Args:
            db: Database session
            document_id: Document ID
            update_data: Update data
            
        Returns:
            Updated document response or None if not found
        """
        try:
            db_document = await db.get(DocumentDB, document_id)
            if not db_document:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(db_document, key, value)
            
            db_document.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(db_document)
            
            logger.info(f"Document updated: {document_id}")
            return DocumentResponse.from_orm(db_document)
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise
    
    async def delete_document(self, db: AsyncSession, document_id: UUID) -> bool:
        """
        Delete a document.
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            True if successful, False if not found
        """
        try:
            db_document = await db.get(DocumentDB, document_id)
            if not db_document:
                return False
            
            # Delete associated file if exists
            if db_document.file_path:
                file_storage.delete_file(db_document.file_path)
            
            # Delete document record
            await db.delete(db_document)
            await db.commit()
            
            logger.info(f"Document deleted: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
    
    async def process_document_ocr(
        self, 
        db: AsyncSession, 
        document_id: UUID,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process document OCR asynchronously.
        
        Args:
            db: Database session
            document_id: Document ID
            file_path: Path to document file
            
        Returns:
            Processing result
        """
        try:
            # Update status to processing
            await self.update_document(
                db, document_id, 
                DocumentUpdate(processing_status=ProcessingStatus.IN_PROGRESS)
            )
            
            await self._log_processing_step(
                db, document_id, "ocr_processing", 
                ProcessingStatus.IN_PROGRESS, "Starting OCR processing"
            )
            
            # Perform OCR processing
            file_type = self._get_file_type(file_path)
            ocr_result = ocr_processor.process_document(file_path, file_type)
            
            if ocr_result['success']:
                # Extract metadata
                metadata = ocr_processor.extract_medical_metadata(ocr_result['text'])
                
                # Update document with OCR results
                update_data = DocumentUpdate(
                    ocr_text=ocr_result['text'],
                    ocr_confidence=ocr_result['confidence'],
                    processing_status=ProcessingStatus.COMPLETED,
                    document_status=DocumentStatus.OCR_COMPLETED,
                    document_metadata=metadata
                )
                
                await self.update_document(db, document_id, update_data)
                
                await self._log_processing_step(
                    db, document_id, "ocr_processing", 
                    ProcessingStatus.COMPLETED, 
                    f"OCR completed with {ocr_result['confidence']:.2f} confidence"
                )
                
                logger.info(f"OCR processing completed for document {document_id}")
                return {
                    'success': True,
                    'text': ocr_result['text'],
                    'confidence': ocr_result['confidence'],
                    'metadata': metadata
                }
            else:
                # Update status to failed
                await self.update_document(
                    db, document_id, 
                    DocumentUpdate(
                        processing_status=ProcessingStatus.FAILED,
                        document_status=DocumentStatus.ERROR
                    )
                )
                
                await self._log_processing_step(
                    db, document_id, "ocr_processing", 
                    ProcessingStatus.FAILED, 
                    f"OCR failed: {ocr_result.get('error', 'Unknown error')}"
                )
                
                logger.error(f"OCR processing failed for document {document_id}")
                return ocr_result
                
        except Exception as e:
            logger.error(f"OCR processing failed for document {document_id}: {e}")
            
            # Update status to failed
            await self.update_document(
                db, document_id, 
                DocumentUpdate(
                    processing_status=ProcessingStatus.FAILED,
                    document_status=DocumentStatus.ERROR
                )
            )
            
            await self._log_processing_step(
                db, document_id, "ocr_processing", 
                ProcessingStatus.FAILED, 
                f"OCR processing error: {str(e)}"
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _log_processing_step(
        self,
        db: AsyncSession,
        document_id: UUID,
        step: str,
        status: ProcessingStatus,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a processing step."""
        try:
            log_entry = DocumentProcessingLogDB(
                document_id=document_id,
                step=step,
                status=status,
                message=message,
                document_metadata=metadata or {}
            )
            db.add(log_entry)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log processing step: {e}")
    
    def _get_file_type(self, file_path: str) -> str:
        """Get file type from file path."""
        import os
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip('.') if ext else 'unknown'


# Global document service instance
document_service = DocumentService()
