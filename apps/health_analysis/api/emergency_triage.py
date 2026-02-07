"""
Emergency Triage API Router

Endpoints for emergency medical assessment and urgent care triage.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from apps.health_analysis.models.health_analysis_models import (
    EmergencyAssessmentRequest,
    EmergencyAssessmentResponse,
    TriageResult,
    EmergencyRecommendation
)
from apps.health_analysis.services.health_analysis_service import HealthAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global service instance (will be set in main.py)
health_analysis_service: HealthAnalysisService = None


def get_health_analysis_service() -> HealthAnalysisService:
    """Get health analysis service instance."""
    if not health_analysis_service:
        raise HTTPException(status_code=503, detail="Service not available")
    return health_analysis_service


@router.post("/assess-emergency", response_model=EmergencyAssessmentResponse)
async def assess_emergency_situation(
    image: Optional[UploadFile] = File(None, description="Image of the emergency situation"),
    symptoms: str = Form(..., description="Description of symptoms and situation"),
    body_part: Optional[str] = Form(None, description="Affected body part"),
    pain_level: int = Form(..., ge=1, le=10, description="Pain level (1-10)"),
    duration: Optional[str] = Form(None, description="How long the condition has been present"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Assess emergency medical situations and provide immediate guidance.
    
    This endpoint provides:
    - Emergency severity assessment
    - Immediate action recommendations
    - Whether to call 911
    - Urgent care vs emergency room guidance
    """
    try:
        # Read image data if provided
        image_data = None
        if image:
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            image_data = await image.read()
        
        # Create emergency assessment request
        request_data = {
            "user_id": current_user["id"],
            "image_data": image_data,
            "symptoms": symptoms,
            "body_part": body_part,
            "pain_level": pain_level,
            "duration": duration,
            "timestamp": datetime.utcnow()
        }
        
        # Perform emergency assessment
        assessment = await service.assess_emergency_situation(request_data)
        
        logger.info(f"Emergency assessment completed for user {current_user['id']}")
        
        return assessment
        
    except Exception as e:
        logger.error(f"Emergency assessment failed: {e}")
        raise HTTPException(status_code=500, detail="Emergency assessment failed")


@router.post("/triage", response_model=TriageResult)
async def perform_triage(
    request: EmergencyAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Perform medical triage to determine urgency and care level needed.
    
    Triage levels:
    - Level 1 (Immediate): Life-threatening, call 911 immediately
    - Level 2 (Emergent): Urgent care needed within 1 hour
    - Level 3 (Urgent): Care needed within 4 hours
    - Level 4 (Less Urgent): Care needed within 24 hours
    - Level 5 (Non-Urgent): Can wait for regular appointment
    """
    try:
        # Add user context
        request.user_id = current_user["id"]
        request.timestamp = datetime.utcnow()
        
        # Perform triage
        triage_result = await service.perform_triage(request)
        
        logger.info(f"Triage completed for user {current_user['id']}")
        
        return triage_result
        
    except Exception as e:
        logger.error(f"Triage failed: {e}")
        raise HTTPException(status_code=500, detail="Triage failed")


@router.post("/emergency-recommendations", response_model=List[EmergencyRecommendation])
async def get_emergency_recommendations(
    request: EmergencyAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Get immediate emergency recommendations and actions.
    
    Provides:
    - Immediate first aid steps
    - What to do while waiting for help
    - Signs to watch for
    - When to escalate care
    """
    try:
        # Add user context
        request.user_id = current_user["id"]
        request.timestamp = datetime.utcnow()
        
        # Get recommendations
        recommendations = await service.get_emergency_recommendations(request)
        
        logger.info(f"Emergency recommendations generated for user {current_user['id']}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Emergency recommendations failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/emergency-symptoms")
async def get_emergency_symptoms(
    category: Optional[str] = Query(None, description="Symptom category (cardiac, respiratory, neurological, etc.)"),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Get list of emergency symptoms and warning signs.
    
    Categories:
    - cardiac: heart attack, chest pain
    - respiratory: breathing difficulties
    - neurological: stroke, seizures
    - trauma: injuries, bleeding
    - pediatric: child-specific emergencies
    """
    try:
        symptoms = await service.get_emergency_symptoms(category)
        
        return symptoms
        
    except Exception as e:
        logger.error(f"Failed to get emergency symptoms: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emergency symptoms")


@router.get("/nearest-emergency-facilities")
async def find_nearest_emergency_facilities(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: float = Query(10.0, description="Search radius in miles"),
    facility_type: Optional[str] = Query("all", description="Type of facility (emergency_room, urgent_care, hospital)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Find nearest emergency medical facilities.
    
    Returns:
    - Emergency rooms
    - Urgent care centers
    - Hospitals
    - Contact information
    - Distance and travel time
    """
    try:
        facilities = await service.find_nearest_emergency_facilities(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            facility_type=facility_type
        )
        
        return facilities
        
    except Exception as e:
        logger.error(f"Failed to find emergency facilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to find emergency facilities")


@router.post("/emergency-contact")
async def create_emergency_contact(
    name: str = Form(..., description="Contact name"),
    relationship: str = Form(..., description="Relationship to user"),
    phone: str = Form(..., description="Phone number"),
    email: Optional[str] = Form(None, description="Email address"),
    is_primary: bool = Form(False, description="Is this the primary emergency contact"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Create or update emergency contact information.
    
    This information can be used in emergency situations
    to notify family members or caregivers.
    """
    try:
        contact_data = {
            "user_id": current_user["id"],
            "name": name,
            "relationship": relationship,
            "phone": phone,
            "email": email,
            "is_primary": is_primary,
            "timestamp": datetime.utcnow()
        }
        
        contact = await service.create_emergency_contact(contact_data)
        
        logger.info(f"Emergency contact created for user {current_user['id']}")
        
        return contact
        
    except Exception as e:
        logger.error(f"Failed to create emergency contact: {e}")
        raise HTTPException(status_code=500, detail="Failed to create emergency contact")


@router.get("/emergency-contacts")
async def get_emergency_contacts(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """Get user's emergency contacts."""
    try:
        contacts = await service.get_emergency_contacts(current_user["id"])
        
        return contacts
        
    except Exception as e:
        logger.error(f"Failed to get emergency contacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emergency contacts")


@router.post("/emergency-alert")
async def send_emergency_alert(
    alert_type: str = Form(..., description="Type of emergency alert"),
    message: str = Form(..., description="Emergency message"),
    location: Optional[str] = Form(None, description="Current location"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Send emergency alert to contacts and emergency services if needed.
    
    Alert types:
    - medical_emergency: Serious medical situation
    - fall_alert: Fall detection
    - cardiac_alert: Heart-related emergency
    - stroke_alert: Stroke symptoms
    """
    try:
        alert_data = {
            "user_id": current_user["id"],
            "alert_type": alert_type,
            "message": message,
            "location": location,
            "timestamp": datetime.utcnow()
        }
        
        alert_result = await service.send_emergency_alert(alert_data)
        
        logger.info(f"Emergency alert sent for user {current_user['id']}")
        
        return alert_result
        
    except Exception as e:
        logger.error(f"Failed to send emergency alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to send emergency alert") 