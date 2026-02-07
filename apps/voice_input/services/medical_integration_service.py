"""
Medical Integration Service
Service for integrating voice input with medical analysis capabilities.
"""

import asyncio
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from common.utils.logging import get_logger
from ..models.multi_modal import MultiModalInput, MultiModalResult
from ..models.vision_analysis import VisionAnalysisResponse

logger = get_logger(__name__)


class MedicalIntegrationService:
    """Service for integrating voice input with medical analysis"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.medical_analysis_url = "http://medical-analysis:8000/api/v1/medical-analysis"
        self.timeout = 30.0
    
    async def analyze_medical_query(
        self,
        patient_id: UUID,
        query_text: str,
        symptoms: List[str] = None,
        medical_history: Dict[str, Any] = None,
        session_id: Optional[str] = None,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze medical query using the medical analysis service
        
        Args:
            patient_id: Patient identifier
            query_text: Text query from voice input
            symptoms: Extracted symptoms
            medical_history: Patient medical history
            session_id: Session identifier
            analysis_type: Type of analysis (diagnosis, prognosis, literature, comprehensive)
            
        Returns:
            Medical analysis result
        """
        try:
            self.logger.info(f"Analyzing medical query for patient {patient_id}")
            
            # Prepare request payload
            payload = {
                "patient_id": str(patient_id),
                "session_id": session_id,
                "analysis_type": analysis_type,
                "symptoms": symptoms or [],
                "medical_history": medical_history or {},
                "current_medications": [],
                "vital_signs": {},
                "lab_results": {},
                "imaging_results": {},
                "age": None,
                "gender": None,
                "family_history": [],
                "lifestyle_factors": {},
                "domain": None,
                "urgency_level": 1
            }
            
            # Call medical analysis service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.medical_analysis_url}/{analysis_type}",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"Medical analysis completed for patient {patient_id}")
                    return result
                else:
                    self.logger.error(f"Medical analysis failed: {response.status_code}")
                    return self._create_fallback_response(patient_id, query_text)
                    
        except Exception as e:
            self.logger.error(f"Error in medical analysis integration: {str(e)}")
            return self._create_fallback_response(patient_id, query_text)
    
    async def analyze_vision_medical_query(
        self,
        patient_id: UUID,
        vision_response: VisionAnalysisResponse,
        query_text: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze medical query with vision data
        
        Args:
            patient_id: Patient identifier
            vision_response: Vision analysis response
            query_text: Text query
            session_id: Session identifier
            
        Returns:
            Medical analysis result with vision context
        """
        try:
            self.logger.info(f"Analyzing vision medical query for patient {patient_id}")
            
            # Extract symptoms from vision analysis
            symptoms = self._extract_symptoms_from_vision(vision_response, query_text)
            
            # Prepare request payload
            payload = {
                "patient_id": str(patient_id),
                "session_id": session_id,
                "analysis_type": "comprehensive",
                "symptoms": symptoms,
                "medical_history": {
                    "vision_analysis": vision_response.response,
                    "medical_domain": vision_response.medical_domain,
                    "confidence": vision_response.medical_confidence
                },
                "current_medications": [],
                "vital_signs": {},
                "lab_results": {},
                "imaging_results": {
                    "vision_analysis": {
                        "response": vision_response.response,
                        "domain": vision_response.medical_domain,
                        "confidence": vision_response.medical_confidence
                    }
                },
                "age": None,
                "gender": None,
                "family_history": [],
                "lifestyle_factors": {},
                "domain": vision_response.medical_domain,
                "urgency_level": 1
            }
            
            # Call medical analysis service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.medical_analysis_url}/comprehensive",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"Vision medical analysis completed for patient {patient_id}")
                    return result
                else:
                    self.logger.error(f"Vision medical analysis failed: {response.status_code}")
                    return self._create_fallback_response(patient_id, query_text)
                    
        except Exception as e:
            self.logger.error(f"Error in vision medical analysis integration: {str(e)}")
            return self._create_fallback_response(patient_id, query_text)
    
    async def generate_comprehensive_medical_report(
        self,
        patient_id: UUID,
        multi_modal_result: MultiModalResult,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive medical report from multi-modal input
        
        Args:
            patient_id: Patient identifier
            multi_modal_result: Multi-modal processing result
            session_id: Session identifier
            
        Returns:
            Comprehensive medical report
        """
        try:
            self.logger.info(f"Generating comprehensive medical report for patient {patient_id}")
            
            # Extract information from multi-modal result
            symptoms = self._extract_symptoms_from_multi_modal(multi_modal_result)
            medical_context = self._extract_medical_context(multi_modal_result)
            
            # Prepare request payload
            payload = {
                "patient_id": str(patient_id),
                "session_id": session_id,
                "analysis_type": "comprehensive",
                "symptoms": symptoms,
                "medical_history": medical_context,
                "current_medications": [],
                "vital_signs": {},
                "lab_results": {},
                "imaging_results": {},
                "age": None,
                "gender": None,
                "family_history": [],
                "lifestyle_factors": {},
                "domain": None,
                "urgency_level": 1
            }
            
            # Call medical analysis service for comprehensive report
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.medical_analysis_url}/report",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"Comprehensive medical report generated for patient {patient_id}")
                    return result
                else:
                    self.logger.error(f"Comprehensive medical report generation failed: {response.status_code}")
                    return self._create_fallback_report(patient_id, multi_modal_result)
                    
        except Exception as e:
            self.logger.error(f"Error in comprehensive medical report generation: {str(e)}")
            return self._create_fallback_report(patient_id, multi_modal_result)
    
    def _extract_symptoms_from_vision(
        self, 
        vision_response: VisionAnalysisResponse, 
        query_text: str
    ) -> List[str]:
        """Extract symptoms from vision analysis response"""
        symptoms = []
        
        # Extract symptoms from query text
        query_lower = query_text.lower()
        symptom_keywords = [
            "pain", "ache", "hurt", "sore", "uncomfortable", "discomfort",
            "headache", "stomachache", "backache", "toothache",
            "fever", "temperature", "hot", "cold", "chills",
            "nausea", "vomit", "sick", "dizzy", "lightheaded",
            "fatigue", "tired", "exhausted", "weak",
            "cough", "sneeze", "runny nose", "congestion"
        ]
        
        for keyword in symptom_keywords:
            if keyword in query_lower:
                symptoms.append(keyword)
        
        # Extract symptoms from vision response
        if vision_response.response:
            response_lower = vision_response.response.lower()
            for keyword in symptom_keywords:
                if keyword in response_lower and keyword not in symptoms:
                    symptoms.append(keyword)
        
        return symptoms
    
    def _extract_symptoms_from_multi_modal(self, multi_modal_result: MultiModalResult) -> List[str]:
        """Extract symptoms from multi-modal result"""
        symptoms = []
        
        # Extract from combined text
        if multi_modal_result.combined_text:
            text_lower = multi_modal_result.combined_text.lower()
            symptom_keywords = [
                "pain", "ache", "hurt", "sore", "uncomfortable", "discomfort",
                "headache", "stomachache", "backache", "toothache",
                "fever", "temperature", "hot", "cold", "chills",
                "nausea", "vomit", "sick", "dizzy", "lightheaded",
                "fatigue", "tired", "exhausted", "weak",
                "cough", "sneeze", "runny nose", "congestion"
            ]
            
            for keyword in symptom_keywords:
                if keyword in text_lower:
                    symptoms.append(keyword)
        
        # Extract from entities
        if multi_modal_result.entities:
            for entity in multi_modal_result.entities:
                if hasattr(entity, 'entity_type') and entity.entity_type == 'symptom':
                    symptoms.append(entity.entity_value)
        
        return list(set(symptoms))  # Remove duplicates
    
    def _extract_medical_context(self, multi_modal_result: MultiModalResult) -> Dict[str, Any]:
        """Extract medical context from multi-modal result"""
        context = {
            "primary_intent": multi_modal_result.primary_intent,
            "confidence_score": multi_modal_result.confidence_score,
            "entities": [entity.dict() if hasattr(entity, 'dict') else str(entity) 
                        for entity in multi_modal_result.entities] if multi_modal_result.entities else [],
            "health_indicators": multi_modal_result.health_indicators or {},
            "recommendations": multi_modal_result.recommendations or []
        }
        
        return context
    
    def _create_fallback_response(self, patient_id: UUID, query_text: str) -> Dict[str, Any]:
        """Create fallback response when medical analysis fails"""
        return {
            "analysis_id": str(uuid4()),
            "patient_id": str(patient_id),
            "analysis_type": "comprehensive",
            "domain": "general",
            "confidence_score": 0.3,
            "processing_time": 0.0,
            "model_used": "fallback",
            "data_sources": ["voice_input"],
            "disclaimers": [
                "Medical analysis service unavailable",
                "Please consult healthcare professional for medical advice"
            ],
            "recommendations": [
                "Contact healthcare provider",
                "Seek professional medical evaluation"
            ],
            "next_steps": [
                "Schedule appointment with healthcare provider",
                "Bring voice query to medical consultation"
            ],
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _create_fallback_report(self, patient_id: UUID, multi_modal_result: MultiModalResult) -> Dict[str, Any]:
        """Create fallback report when comprehensive report generation fails"""
        return {
            "report_id": str(uuid4()),
            "patient_id": str(patient_id),
            "executive_summary": "Medical analysis service unavailable. Please consult healthcare professional.",
            "key_findings": ["Voice input processed", "Medical analysis pending"],
            "critical_alerts": [],
            "overall_confidence": 0.3,
            "data_quality_score": 0.5,
            "model_versions": {"fallback": "1.0.0"},
            "data_sources": ["voice_input"],
            "created_at": datetime.utcnow().isoformat()
        } 