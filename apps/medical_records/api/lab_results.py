"""
Lab Results API Endpoints
Provides CRUD and file upload endpoints for lab results.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy import func
from ..models.lab_results import LabResultCreate, LabResultUpdate, LabResultResponse, LabResultListResponse
from ..models.lab_results_db import LabResultDB
from ..models.base import MedicalRecordsModel
from common.database.connection import get_async_db
from ..services import service_integration
import logging

router = APIRouter(prefix="/lab-results", tags=["Lab Results"])
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

# Create Lab Result
@router.post("/", response_model=LabResultResponse)
async def create_lab_result(
    lab_result: LabResultCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Check if user has write permissions
        if not await service_integration.auth_client.check_permissions(
            current_user["user_id"], 
            ["medical_records:write"], 
            request.headers.get("authorization", "").replace("Bearer ", "")
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Set patient_id to current user if not provided
        if not lab_result.patient_id:
            lab_result.patient_id = UUID(current_user["user_id"])
        
        db_lab = LabResultDB(**lab_result.dict())
        db.add(db_lab)
        await db.commit()
        await db.refresh(db_lab)
        
        logger.info(f"Lab result created for user {current_user['user_id']}: {db_lab.id}")
        return LabResultResponse.from_orm(db_lab)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create lab result: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lab result")

# List Lab Results
@router.get("/", response_model=LabResultListResponse)
async def list_lab_results(
    patient_id: Optional[UUID] = Query(None),
    skip: int = 0,
    limit: int = 20,
    request: Request = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
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
        
        query = select(LabResultDB).where(LabResultDB.patient_id == patient_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()
        
        # Get paginated results
        results = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
        items = [LabResultResponse.from_orm(r) for r in results]
        
        logger.info(f"Retrieved {len(items)} lab results for user {current_user['user_id']}")
        return LabResultListResponse(items=items, total=total, page=skip//limit+1, size=limit, pages=(total+limit-1)//limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list lab results: {e}")
        raise HTTPException(status_code=500, detail="Failed to list lab results")

# Get Single Lab Result
@router.get("/{lab_result_id}", response_model=LabResultResponse)
async def get_lab_result(
    lab_result_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = await db.get(LabResultDB, lab_result_id)
        if not result:
            raise HTTPException(status_code=404, detail="Lab result not found")
        
        # Check if user has permission to access this lab result
        if str(result.patient_id) != current_user["user_id"]:
            # Check if user has admin permissions
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions to access this lab result")
        
        logger.info(f"Retrieved lab result {lab_result_id} for user {current_user['user_id']}")
        return LabResultResponse.from_orm(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lab result: {e}")
        raise HTTPException(status_code=500, detail="Failed to get lab result")

# Update Lab Result
@router.put("/{lab_result_id}", response_model=LabResultResponse)
async def update_lab_result(
    lab_result_id: UUID,
    update: LabResultUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        db_lab = await db.get(LabResultDB, lab_result_id)
        if not db_lab:
            raise HTTPException(status_code=404, detail="Lab result not found")
        
        # Check if user has permission to update this lab result
        if str(db_lab.patient_id) != current_user["user_id"]:
            # Check if user has admin permissions
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions to update this lab result")
        
        for key, value in update.dict(exclude_unset=True).items():
            setattr(db_lab, key, value)
        
        await db.commit()
        await db.refresh(db_lab)
        
        logger.info(f"Updated lab result {lab_result_id} for user {current_user['user_id']}")
        return LabResultResponse.from_orm(db_lab)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update lab result: {e}")
        raise HTTPException(status_code=500, detail="Failed to update lab result")

# Delete Lab Result
@router.delete("/{lab_result_id}", response_model=dict)
async def delete_lab_result(
    lab_result_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        db_lab = await db.get(LabResultDB, lab_result_id)
        if not db_lab:
            raise HTTPException(status_code=404, detail="Lab result not found")
        
        # Check if user has permission to delete this lab result
        if str(db_lab.patient_id) != current_user["user_id"]:
            # Check if user has admin permissions
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions to delete this lab result")
        
        await db.delete(db_lab)
        await db.commit()
        
        logger.info(f"Deleted lab result {lab_result_id} for user {current_user['user_id']}")
        return {"detail": "Lab result deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete lab result: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete lab result")

# File Upload (Direct or URL)
@router.post("/upload", response_model=dict)
async def upload_lab_result_file(
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        if not file and not file_url:
            raise HTTPException(status_code=400, detail="Either file or file_url must be provided")
        
        # Check if user has upload permissions
        if not await service_integration.auth_client.check_permissions(
            current_user["user_id"], 
            ["medical_records:upload"], 
            request.headers.get("authorization", "").replace("Bearer ", "")
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to upload files")
        
        # TODO: Integrate Supabase Storage and OCR pipeline here
        # For now, just return a mock response
        logger.info(f"File upload received for user {current_user['user_id']}: {file.filename if file else file_url}")
        return {
            "detail": "File upload received (mock)", 
            "file_url": file_url, 
            "filename": file.filename if file else None,
            "user_id": current_user["user_id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

# Get lab results with health context
@router.get("/{lab_result_id}/context", response_model=dict)
async def get_lab_result_with_context(
    lab_result_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Get lab result with health context and correlations"""
    try:
        # Get the lab result
        result = await db.get(LabResultDB, lab_result_id)
        if not result:
            raise HTTPException(status_code=404, detail="Lab result not found")
        
        # Check permissions
        if str(result.patient_id) != current_user["user_id"]:
            if not await service_integration.auth_client.check_permissions(
                current_user["user_id"], 
                ["medical_records:admin"], 
                request.headers.get("authorization", "").replace("Bearer ", "")
            ):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get health context
        health_context = await service_integration.get_health_context(
            current_user["user_id"],
            request.headers.get("authorization", "").replace("Bearer ", "")
        )
        
        # Correlate with health data
        correlations = await service_integration.correlate_lab_results_with_health_data(
            current_user["user_id"],
            [result.__dict__],
            request.headers.get("authorization", "").replace("Bearer ", "")
        )
        
        return {
            "lab_result": LabResultResponse.from_orm(result),
            "health_context": health_context,
            "correlations": correlations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lab result context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get lab result context")

# Test endpoint without auth service integration
@router.get("/test/no-auth")
async def test_no_auth():
    """Test endpoint that doesn't require authentication"""
    return {"message": "No auth test endpoint working"}


@router.post("/{lab_result_id}/enrich-with-knowledge-graph", response_model=dict)
async def enrich_lab_result_with_knowledge_graph(
    lab_result_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Enrich lab result with knowledge graph entities and medical recommendations"""
    try:
        # Get the lab result
        result = await db.execute(
            select(LabResultDB).where(LabResultDB.id == lab_result_id)
        )
        lab_result = result.scalar_one_or_none()
        
        if not lab_result:
            raise HTTPException(status_code=404, detail="Lab result not found")
        
        # Check if user has access to this lab result
        if str(lab_result.patient_id) != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this lab result")
        
        # Extract medical text from lab result
        medical_text = f"{lab_result.test_name} {lab_result.result_value} {lab_result.unit} {lab_result.reference_range or ''} {lab_result.interpretation or ''}"
        
        # Enrich with knowledge graph entities
        enrichment_result = await service_integration.enrich_medical_record_with_knowledge_graph(medical_text)
        
        # Extract conditions and medications for recommendations
        conditions = []
        medications = []
        
        for entity in enrichment_result.get("enriched_entities", []):
            entity_type = entity.get("type", "").lower()
            if entity_type == "condition":
                conditions.append(entity.get("name", ""))
            elif entity_type == "medication":
                medications.append(entity.get("name", ""))
        
        # Get medical recommendations
        recommendations = await service_integration.get_medical_recommendations(conditions, medications)
        
        # Combine results
        enriched_result = {
            "lab_result_id": str(lab_result_id),
            "enrichment": enrichment_result,
            "recommendations": recommendations,
            "summary": {
                "entities_found": enrichment_result.get("entity_count", 0),
                "conditions_identified": len(conditions),
                "medications_identified": len(medications),
                "treatments_suggested": len(recommendations.get("treatments", [])),
                "interactions_found": len(recommendations.get("interactions", []))
            },
            "timestamp": enrichment_result.get("enrichment_timestamp")
        }
        
        logger.info(f"Lab result {lab_result_id} enriched with knowledge graph for user {current_user['user_id']}")
        return enriched_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enrich lab result with knowledge graph: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to enrich lab result with knowledge graph"
        )


@router.post("/validate-medical-codes", response_model=dict)
async def validate_medical_codes(
    codes: List[dict],
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Validate medical codes against the knowledge graph"""
    try:
        # Validate medical codes
        validation_result = await service_integration.validate_medical_codes(codes)
        
        logger.info(f"Medical codes validated for user {current_user['user_id']}: {validation_result['valid_count']} valid, {validation_result['invalid_count']} invalid")
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate medical codes: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to validate medical codes"
        ) 