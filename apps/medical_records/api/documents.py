"""
Document API Endpoints
Provides CRUD and file upload endpoints for medical documents.
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.documents import (
    DocumentUploadRequest, DocumentCreate, DocumentUpdate, DocumentResponse, 
    DocumentListResponse, DocumentType, ProcessingStatus, DocumentStatus
)
from ..services.document_service import document_service
from ..services import service_integration
from ..utils.file_storage import file_storage
from common.database.connection import get_async_db
import logging

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Get current user from auth service
async def get_current_user(request: Request, credentials: HTTPBearer = Depends(security)):
    """Get current user from auth service"""
    try:
        # Validate user access with required permissions
        user_info = await service_integration.validate_user_access(
            credentials.credentials,
            required_permissions=["medical_records:read"]
        )
        
        # Add user info to request state for logging
        request.state.user_id = user_info["user_id"]
        request.state.user_profile = user_info["user_profile"]
        
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

# Create Document
@router.post("/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new document."""
    try:
        # Check if user has write permissions
        if not await service_integration.auth_client.check_permissions(
            current_user["user_id"], 
            ["medical_records:write"], 
            request.headers.get("authorization", "").replace("Bearer ", "")
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Set patient_id to current user if not provided
        if not document.patient_id:
            document.patient_id = UUID(current_user["user_id"])
        
        result = await document_service.create_document(db, document)
        
        logger.info(f"Document created for user {current_user['user_id']}: {result.id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document")

# Upload Document File
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload a document file with OCR processing."""
    try:
        # Check if user has write permissions
        if not await service_integration.auth_client.check_permissions(
            current_user["user_id"], 
            ["medical_records:write"], 
            request.headers.get("authorization", "").replace("Bearer ", "")
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Validate file type
        allowed_types = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg', 'image/tiff']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not supported. Allowed: {allowed_types}"
            )
        
        # Save file
        file_info = file_storage.save_uploaded_file(file, str(current_user["user_id"]))
        
        # Parse tags
        tag_list = []
        if tags:
            import json
            try:
                tag_list = json.loads(tags)
            except json.JSONDecodeError:
                tag_list = [tags]
        
        # Create document record
        document_data = DocumentCreate(
            patient_id=UUID(current_user["user_id"]),
            document_type=document_type,
            title=title or file.filename or f"Uploaded {document_type.value}",
            file_path=file_info['file_path'],
            file_url=file_info['file_url'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            tags=tag_list,
            source="upload",
            processing_status=ProcessingStatus.PENDING,
            document_status=DocumentStatus.UPLOADED
        )
        
        document = await document_service.create_document(db, document_data)
        
        # Start OCR processing in background
        if background_tasks:
            background_tasks.add_task(
                document_service.process_document_ocr,
                db, document.id, file_info['file_path']
            )
        
        logger.info(f"Document uploaded for user {current_user['user_id']}: {document.id}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

# List Documents
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    patient_id: Optional[UUID] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    status: Optional[DocumentStatus] = Query(None),
    skip: int = 0,
    limit: int = 20,
    request: Request = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """List documents for a patient."""
    try:
        # If patient_id not provided, use current user's ID
        if not patient_id:
            patient_id = UUID(current_user["user_id"])
        
        # Check if user has permission to access this patient's data
        if str(patient_id) != current_user["user_id"]:
            # Check if user has admin permissions
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions to access other patient data")
        
        result = await document_service.list_documents(
            db, patient_id, skip, limit, 
            document_type.value if document_type else None,
            status.value if status else None
        )
        
        logger.info(f"Retrieved {len(result.items)} documents for user {current_user['user_id']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

# Get Single Document
@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a document by ID."""
    try:
        document = await document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user has permission to access this document
        if str(document.patient_id) != current_user["user_id"]:
            # Check if user has admin permissions
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions to access this document")
        
        logger.info(f"Retrieved document {document_id} for user {current_user['user_id']}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")

# Update Document
@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    update: DocumentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a document."""
    try:
        # Check if user has write permissions
        if not await service_integration.auth_client.check_permissions(
            current_user["user_id"], 
            ["medical_records:write"], 
            request.headers.get("authorization", "").replace("Bearer ", "")
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        document = await document_service.update_document(db, document_id, update)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user has permission to update this document
        if str(document.patient_id) != current_user["user_id"]:
            # Check if user has admin permissions
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions to update this document")
        
        logger.info(f"Updated document {document_id} for user {current_user['user_id']}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document")

# Delete Document
@router.delete("/{document_id}", response_model=dict)
async def delete_document(
    document_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a document."""
    try:
        # Check if user has write permissions
        if not await service_integration.auth_client.check_permissions(
            current_user["user_id"], 
            ["medical_records:write"], 
            request.headers.get("authorization", "").replace("Bearer ", "")
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        success = await document_service.delete_document(db, document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Deleted document {document_id} for user {current_user['user_id']}")
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

# Get Document Processing Status
@router.get("/{document_id}/status", response_model=dict)
async def get_document_status(
    document_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Get document processing status."""
    try:
        document = await document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user has permission to access this document
        if str(document.patient_id) != current_user["user_id"]:
            # Check if user has admin permissions
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions to access this document")
        
        return {
            "document_id": str(document_id),
            "processing_status": document.processing_status,
            "document_status": document.document_status,
            "ocr_confidence": document.ocr_confidence,
            "has_ocr_text": bool(document.ocr_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document status")

# Test endpoint (no auth required)
@router.get("/test/no-auth")
async def test_no_auth():
    """Test endpoint without authentication."""
    return {
        "message": "Document API is working",
        "status": "healthy",
        "auth_service_integration": "bypassed"
    }
