"""
Medical Analysis API
API endpoints for comprehensive medical analysis.
"""

import asyncio
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel

from ..models.medical_analysis import (
    MedicalAnalysisRequest,
    MedicalAnalysisResult,
    ComprehensiveMedicalReport,
    AnalysisType,
    MedicalDomain
)
from ..services.medical_analysis_service import MedicalAnalysisService
from common.utils.logging import get_logger

logger = get_logger(__name__)

medical_analysis_router = APIRouter(prefix="/medical-analysis", tags=["Medical Analysis"])

# Initialize service
medical_analysis_service = MedicalAnalysisService()


class AnalysisRequest(BaseModel):
    """Request model for medical analysis"""
    patient_id: UUID
    session_id: Optional[str] = None
    analysis_type: AnalysisType
    symptoms: List[str] = []
    medical_history: Dict[str, Any] = {}
    current_medications: List[str] = []
    vital_signs: Dict[str, Any] = {}
    lab_results: Dict[str, Any] = {}
    imaging_results: Dict[str, Any] = {}
    age: Optional[int] = None
    gender: Optional[str] = None
    family_history: List[str] = []
    lifestyle_factors: Dict[str, Any] = {}
    domain: Optional[MedicalDomain] = None
    urgency_level: int = 1


@medical_analysis_router.post("/analyze", response_model=MedicalAnalysisResult)
async def analyze_medical_condition(request: AnalysisRequest):
    """
    Perform medical analysis based on request type
    
    - **request**: Medical analysis request with patient data and analysis type
    """
    try:
        logger.info(f"Processing medical analysis request for patient {request.patient_id}")
        
        # Convert to internal request model
        medical_request = MedicalAnalysisRequest(
            patient_id=request.patient_id,
            session_id=request.session_id,
            analysis_type=request.analysis_type,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
            vital_signs=request.vital_signs,
            lab_results=request.lab_results,
            imaging_results=request.imaging_results,
            age=request.age,
            gender=request.gender,
            family_history=request.family_history,
            lifestyle_factors=request.lifestyle_factors,
            domain=request.domain,
            urgency_level=request.urgency_level
        )
        
        # Perform analysis
        result = await medical_analysis_service.analyze_medical_condition(medical_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in medical analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in medical analysis: {str(e)}")


@medical_analysis_router.post("/diagnosis", response_model=MedicalAnalysisResult)
async def analyze_diagnosis(request: AnalysisRequest):
    """
    Perform medical diagnosis analysis
    
    - **request**: Medical analysis request with patient data
    """
    try:
        logger.info(f"Processing diagnosis analysis for patient {request.patient_id}")
        
        # Set analysis type to diagnosis
        request.analysis_type = AnalysisType.DIAGNOSIS
        
        # Convert to internal request model
        medical_request = MedicalAnalysisRequest(
            patient_id=request.patient_id,
            session_id=request.session_id,
            analysis_type=request.analysis_type,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
            vital_signs=request.vital_signs,
            lab_results=request.lab_results,
            imaging_results=request.imaging_results,
            age=request.age,
            gender=request.gender,
            family_history=request.family_history,
            lifestyle_factors=request.lifestyle_factors,
            domain=request.domain,
            urgency_level=request.urgency_level
        )
        
        # Perform diagnosis analysis
        result = await medical_analysis_service.analyze_medical_condition(medical_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in diagnosis analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in diagnosis analysis: {str(e)}")


@medical_analysis_router.post("/prognosis", response_model=MedicalAnalysisResult)
async def analyze_prognosis(request: AnalysisRequest):
    """
    Perform medical prognosis analysis
    
    - **request**: Medical analysis request with patient data
    """
    try:
        logger.info(f"Processing prognosis analysis for patient {request.patient_id}")
        
        # Set analysis type to prognosis
        request.analysis_type = AnalysisType.PROGNOSIS
        
        # Convert to internal request model
        medical_request = MedicalAnalysisRequest(
            patient_id=request.patient_id,
            session_id=request.session_id,
            analysis_type=request.analysis_type,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
            vital_signs=request.vital_signs,
            lab_results=request.lab_results,
            imaging_results=request.imaging_results,
            age=request.age,
            gender=request.gender,
            family_history=request.family_history,
            lifestyle_factors=request.lifestyle_factors,
            domain=request.domain,
            urgency_level=request.urgency_level
        )
        
        # Perform prognosis analysis
        result = await medical_analysis_service.analyze_medical_condition(medical_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in prognosis analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in prognosis analysis: {str(e)}")


@medical_analysis_router.post("/literature", response_model=MedicalAnalysisResult)
async def analyze_literature(request: AnalysisRequest):
    """
    Perform medical literature analysis
    
    - **request**: Medical analysis request with patient data
    """
    try:
        logger.info(f"Processing literature analysis for patient {request.patient_id}")
        
        # Set analysis type to literature
        request.analysis_type = AnalysisType.LITERATURE
        
        # Convert to internal request model
        medical_request = MedicalAnalysisRequest(
            patient_id=request.patient_id,
            session_id=request.session_id,
            analysis_type=request.analysis_type,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
            vital_signs=request.vital_signs,
            lab_results=request.lab_results,
            imaging_results=request.imaging_results,
            age=request.age,
            gender=request.gender,
            family_history=request.family_history,
            lifestyle_factors=request.lifestyle_factors,
            domain=request.domain,
            urgency_level=request.urgency_level
        )
        
        # Perform literature analysis
        result = await medical_analysis_service.analyze_medical_condition(medical_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in literature analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in literature analysis: {str(e)}")


@medical_analysis_router.post("/comprehensive", response_model=MedicalAnalysisResult)
async def analyze_comprehensive(request: AnalysisRequest):
    """
    Perform comprehensive medical analysis (diagnosis + prognosis + literature)
    
    - **request**: Medical analysis request with patient data
    """
    try:
        logger.info(f"Processing comprehensive analysis for patient {request.patient_id}")
        
        # Set analysis type to comprehensive
        request.analysis_type = AnalysisType.COMPREHENSIVE
        
        # Convert to internal request model
        medical_request = MedicalAnalysisRequest(
            patient_id=request.patient_id,
            session_id=request.session_id,
            analysis_type=request.analysis_type,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
            vital_signs=request.vital_signs,
            lab_results=request.lab_results,
            imaging_results=request.imaging_results,
            age=request.age,
            gender=request.gender,
            family_history=request.family_history,
            lifestyle_factors=request.lifestyle_factors,
            domain=request.domain,
            urgency_level=request.urgency_level
        )
        
        # Perform comprehensive analysis
        result = await medical_analysis_service.analyze_medical_condition(medical_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in comprehensive analysis: {str(e)}")


@medical_analysis_router.post("/report", response_model=ComprehensiveMedicalReport)
async def generate_comprehensive_report(request: AnalysisRequest):
    """
    Generate comprehensive medical report
    
    - **request**: Medical analysis request with patient data
    """
    try:
        logger.info(f"Generating comprehensive report for patient {request.patient_id}")
        
        # Convert to internal request model
        medical_request = MedicalAnalysisRequest(
            patient_id=request.patient_id,
            session_id=request.session_id,
            analysis_type=AnalysisType.COMPREHENSIVE,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
            vital_signs=request.vital_signs,
            lab_results=request.lab_results,
            imaging_results=request.imaging_results,
            age=request.age,
            gender=request.gender,
            family_history=request.family_history,
            lifestyle_factors=request.lifestyle_factors,
            domain=request.domain,
            urgency_level=request.urgency_level
        )
        
        # Generate comprehensive report
        report = await medical_analysis_service.generate_comprehensive_report(medical_request)
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating comprehensive report: {str(e)}")


@medical_analysis_router.get("/capabilities")
async def get_capabilities():
    """Get medical analysis service capabilities"""
    return {
        "service": "medical_analysis",
        "capabilities": {
            "analysis_types": [
                {
                    "type": "diagnosis",
                    "description": "Medical diagnosis based on symptoms and data",
                    "features": ["condition_identification", "differential_diagnoses", "confidence_scoring"]
                },
                {
                    "type": "prognosis",
                    "description": "Disease progression and outcome prediction",
                    "features": ["outcome_prediction", "risk_assessment", "progression_staging"]
                },
                {
                    "type": "literature",
                    "description": "Medical literature and research insights",
                    "features": ["research_findings", "clinical_guidelines", "treatment_evidence"]
                },
                {
                    "type": "comprehensive",
                    "description": "Complete analysis combining all types",
                    "features": ["diagnosis", "prognosis", "literature", "treatment_recommendations"]
                }
            ],
            "medical_domains": [
                "cardiology", "dermatology", "neurology", "oncology", 
                "endocrinology", "gastroenterology", "respiratory", "general"
            ],
            "data_sources": [
                "patient_symptoms", "medical_history", "vital_signs", 
                "lab_results", "imaging_results", "family_history"
            ],
            "ai_models": [
                "gpt-4", "llama-3.1-8b-instant", "medical_knowledge_base"
            ],
            "output_formats": [
                "analysis_result", "comprehensive_report", "structured_data"
            ]
        }
    }


@medical_analysis_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "medical_analysis",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/medical-analysis/analyze",
            "diagnosis": "/medical-analysis/diagnosis",
            "prognosis": "/medical-analysis/prognosis",
            "literature": "/medical-analysis/literature",
            "comprehensive": "/medical-analysis/comprehensive",
            "report": "/medical-analysis/report"
        }
    } 