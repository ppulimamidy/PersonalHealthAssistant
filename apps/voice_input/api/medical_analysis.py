"""
Medical Analysis API
API endpoints for medical analysis integration with voice input.
"""

import asyncio
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel

from ..models.multi_modal import MultiModalInput, MultiModalResult
from ..services.medical_integration_service import MedicalIntegrationService
from common.utils.logging import get_logger

logger = get_logger(__name__)

medical_analysis_router = APIRouter(prefix="/medical-analysis", tags=["Medical Analysis"])

# Initialize service
medical_integration_service = MedicalIntegrationService()


class MedicalQueryRequest(BaseModel):
    """Request model for medical query analysis"""
    patient_id: UUID
    session_id: Optional[str] = None
    query_text: str
    symptoms: List[str] = []
    medical_history: Dict[str, Any] = {}
    analysis_type: str = "comprehensive"


class MedicalVisionRequest(BaseModel):
    """Request model for medical vision analysis"""
    patient_id: UUID
    session_id: Optional[str] = None
    vision_response: Dict[str, Any]
    query_text: str


@medical_analysis_router.post("/analyze-query")
async def analyze_medical_query(request: MedicalQueryRequest):
    """
    Analyze medical query from voice input
    
    - **request**: Medical query analysis request
    """
    try:
        logger.info(f"Analyzing medical query for patient {request.patient_id}")
        
        result = await medical_integration_service.analyze_medical_query(
            patient_id=request.patient_id,
            query_text=request.query_text,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            session_id=request.session_id,
            analysis_type=request.analysis_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in medical query analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in medical query analysis: {str(e)}")


@medical_analysis_router.post("/analyze-vision")
async def analyze_medical_vision(request: MedicalVisionRequest):
    """
    Analyze medical query with vision data
    
    - **request**: Medical vision analysis request
    """
    try:
        logger.info(f"Analyzing medical vision for patient {request.patient_id}")
        
        # Convert vision response to proper format
        from ..models.vision_analysis import VisionAnalysisResponse
        vision_response = VisionAnalysisResponse(**request.vision_response)
        
        result = await medical_integration_service.analyze_vision_medical_query(
            patient_id=request.patient_id,
            vision_response=vision_response,
            query_text=request.query_text,
            session_id=request.session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in medical vision analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in medical vision analysis: {str(e)}")


@medical_analysis_router.post("/generate-report")
async def generate_medical_report(multi_modal_result: MultiModalResult):
    """
    Generate comprehensive medical report from multi-modal input
    
    - **multi_modal_result**: Multi-modal processing result
    """
    try:
        logger.info(f"Generating medical report for patient {multi_modal_result.patient_id}")
        
        result = await medical_integration_service.generate_comprehensive_medical_report(
            patient_id=multi_modal_result.patient_id,
            multi_modal_result=multi_modal_result,
            session_id=multi_modal_result.session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating medical report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating medical report: {str(e)}")


@medical_analysis_router.get("/capabilities")
async def get_medical_capabilities():
    """Get medical analysis capabilities"""
    return {
        "service": "voice_input_medical_integration",
        "capabilities": {
            "medical_analysis": {
                "diagnosis": "Medical diagnosis based on voice input",
                "prognosis": "Disease prognosis and outcome prediction",
                "literature": "Medical literature and research insights",
                "comprehensive": "Complete medical analysis"
            },
            "integration": {
                "voice_input": "Process voice queries for medical analysis",
                "vision_input": "Process vision data for medical analysis",
                "multi_modal": "Combine multiple inputs for comprehensive analysis"
            },
            "outputs": {
                "analysis_result": "Structured medical analysis",
                "comprehensive_report": "Complete medical report",
                "recommendations": "Evidence-based recommendations"
            }
        }
    }


@medical_analysis_router.get("/health")
async def health_check():
    """Health check for medical analysis integration"""
    return {
        "service": "voice_input_medical_integration",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "analyze_query": "/api/v1/voice-input/medical-analysis/analyze-query",
            "analyze_vision": "/api/v1/voice-input/medical-analysis/analyze-vision",
            "generate_report": "/api/v1/voice-input/medical-analysis/generate-report"
        }
    } 