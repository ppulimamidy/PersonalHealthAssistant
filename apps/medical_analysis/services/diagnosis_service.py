"""
Diagnosis Service
Service for providing medical diagnosis based on symptoms, history, and data.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import httpx
import json

from common.utils.logging import get_logger
from ..models.medical_analysis import (
    Diagnosis,
    MedicalAnalysisRequest,
    MedicalAnalysisResult,
    AnalysisType,
    ConfidenceLevel,
    SeverityLevel,
    MedicalDomain
)

logger = get_logger(__name__)


class DiagnosisService:
    """Service for medical diagnosis analysis"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.openai_api_key = None
        self.groq_api_key = None
        self._load_api_keys()
        
        # Medical knowledge base for diagnosis
        self.diagnosis_patterns = {
            MedicalDomain.CARDIOLOGY: {
                "chest_pain": {
                    "conditions": ["angina", "myocardial_infarction", "pericarditis", "aortic_dissection"],
                    "symptoms": ["chest pain", "shortness of breath", "sweating", "nausea"],
                    "severity": SeverityLevel.SEVERE
                },
                "arrhythmia": {
                    "conditions": ["atrial_fibrillation", "ventricular_tachycardia", "bradycardia"],
                    "symptoms": ["palpitations", "dizziness", "fainting", "fatigue"],
                    "severity": SeverityLevel.MODERATE
                }
            },
            MedicalDomain.DERMATOLOGY: {
                "rash": {
                    "conditions": ["eczema", "psoriasis", "contact_dermatitis", "urticaria"],
                    "symptoms": ["itchy skin", "redness", "swelling", "blisters"],
                    "severity": SeverityLevel.MILD
                },
                "mole": {
                    "conditions": ["benign_nevus", "melanoma", "dysplastic_nevus"],
                    "symptoms": ["asymmetric", "irregular_borders", "color_changes"],
                    "severity": SeverityLevel.MODERATE
                }
            },
            MedicalDomain.NEUROLOGY: {
                "headache": {
                    "conditions": ["migraine", "tension_headache", "cluster_headache", "meningitis"],
                    "symptoms": ["throbbing pain", "nausea", "light_sensitivity", "aura"],
                    "severity": SeverityLevel.MODERATE
                },
                "seizure": {
                    "conditions": ["epilepsy", "febrile_seizure", "metabolic_disorder"],
                    "symptoms": ["unconsciousness", "convulsions", "confusion"],
                    "severity": SeverityLevel.SEVERE
                }
            }
        }
    
    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
    
    async def analyze_diagnosis(
        self, 
        request: MedicalAnalysisRequest
    ) -> MedicalAnalysisResult:
        """
        Perform comprehensive diagnosis analysis
        
        Args:
            request: Medical analysis request with patient data
            
        Returns:
            MedicalAnalysisResult with diagnosis
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting diagnosis analysis for patient {request.patient_id}")
            
            # Determine medical domain
            domain = request.domain or self._detect_domain(request.symptoms)
            
            # Perform AI-powered diagnosis
            diagnosis = await self._perform_ai_diagnosis(request, domain)
            
            # Generate treatment recommendations
            treatment_recommendations = await self._generate_treatment_recommendations(diagnosis)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(diagnosis, request)
            
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.DIAGNOSIS,
                domain=domain,
                diagnosis=diagnosis,
                treatment_recommendations=treatment_recommendations,
                confidence_score=confidence_score,
                processing_time=processing_time,
                model_used="gpt-4 + medical_knowledge_base",
                data_sources=["patient_symptoms", "medical_history", "vital_signs", "lab_results"],
                disclaimers=[
                    "This diagnosis is AI-assisted and should be verified by a healthcare professional",
                    "The analysis is based on provided information and may not be complete",
                    "Always consult with a qualified medical professional for definitive diagnosis"
                ],
                recommendations=[
                    "Schedule an appointment with your healthcare provider",
                    "Bring this analysis to your medical consultation",
                    "Monitor your symptoms and report any changes"
                ],
                next_steps=[
                    "Consult with a healthcare professional",
                    "Follow up on recommended tests",
                    "Monitor symptoms and report changes"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Error in diagnosis analysis: {str(e)}")
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.DIAGNOSIS,
                domain=MedicalDomain.GENERAL,
                confidence_score=0.0,
                processing_time=processing_time,
                model_used="error",
                data_sources=[],
                disclaimers=["Analysis failed - please consult healthcare professional"],
                recommendations=["Seek immediate medical attention if symptoms are severe"],
                next_steps=["Contact healthcare provider"]
            )
    
    async def _perform_ai_diagnosis(
        self, 
        request: MedicalAnalysisRequest, 
        domain: MedicalDomain
    ) -> Diagnosis:
        """Perform AI-powered diagnosis"""
        try:
            # Create diagnosis prompt
            prompt = self._create_diagnosis_prompt(request, domain)
            
            # Use OpenAI for diagnosis
            if self.openai_api_key:
                diagnosis_text = await self._call_openai_diagnosis(prompt)
            elif self.groq_api_key:
                diagnosis_text = await self._call_groq_diagnosis(prompt)
            else:
                # Fallback to pattern-based diagnosis
                diagnosis_text = self._pattern_based_diagnosis(request, domain)
            
            # Parse diagnosis from AI response
            diagnosis = self._parse_diagnosis_response(diagnosis_text, domain)
            
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"Error in AI diagnosis: {str(e)}")
            # Fallback to basic diagnosis
            return self._create_basic_diagnosis(request, domain)
    
    def _create_diagnosis_prompt(self, request: MedicalAnalysisRequest, domain: MedicalDomain) -> str:
        """Create diagnosis prompt for AI"""
        prompt = f"""
You are a medical AI assistant specializing in {domain.value} diagnosis. Analyze the following patient information and provide a comprehensive diagnosis.

PATIENT INFORMATION:
- Age: {request.age or 'Unknown'}
- Gender: {request.gender or 'Unknown'}
- Symptoms: {', '.join(request.symptoms)}
- Medical History: {json.dumps(request.medical_history, indent=2)}
- Current Medications: {', '.join(request.current_medications)}
- Vital Signs: {json.dumps(request.vital_signs, indent=2)}
- Lab Results: {json.dumps(request.lab_results, indent=2)}
- Family History: {', '.join(request.family_history)}

INSTRUCTIONS:
1. Analyze the symptoms and medical data
2. Provide a primary diagnosis with confidence level
3. List differential diagnoses
4. Identify supporting evidence
5. Assess severity and urgency
6. Provide ICD-10 codes if possible

RESPONSE FORMAT (JSON):
{{
    "condition_name": "Primary diagnosis",
    "icd_code": "ICD-10 code if available",
    "confidence": 0.85,
    "confidence_level": "high",
    "differential_diagnoses": ["condition1", "condition2"],
    "supporting_evidence": ["evidence1", "evidence2"],
    "contraindications": ["contraindication1"],
    "severity": "moderate",
    "urgency_level": 3
}}

Please provide a comprehensive diagnosis analysis.
"""
        return prompt
    
    async def _call_openai_diagnosis(self, prompt: str) -> str:
        """Call OpenAI API for diagnosis"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "system", "content": "You are a medical AI assistant providing diagnosis analysis."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.3
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"OpenAI API error: {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def _call_groq_diagnosis(self, prompt: str) -> str:
        """Call GROQ API for diagnosis"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": "You are a medical AI assistant providing diagnosis analysis."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.3
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"GROQ API error: {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"GROQ API error: {str(e)}")
            raise
    
    def _pattern_based_diagnosis(self, request: MedicalAnalysisRequest, domain: MedicalDomain) -> str:
        """Fallback pattern-based diagnosis"""
        symptoms_text = " ".join(request.symptoms).lower()
        
        # Simple pattern matching
        if "chest pain" in symptoms_text:
            return json.dumps({
                "condition_name": "Angina",
                "icd_code": "I20.9",
                "confidence": 0.7,
                "confidence_level": "medium",
                "differential_diagnoses": ["Myocardial infarction", "Pericarditis"],
                "supporting_evidence": ["Chest pain reported"],
                "contraindications": [],
                "severity": "moderate",
                "urgency_level": 3
            })
        elif "headache" in symptoms_text:
            return json.dumps({
                "condition_name": "Tension headache",
                "icd_code": "G44.2",
                "confidence": 0.6,
                "confidence_level": "medium",
                "differential_diagnoses": ["Migraine", "Cluster headache"],
                "supporting_evidence": ["Headache reported"],
                "contraindications": [],
                "severity": "mild",
                "urgency_level": 2
            })
        else:
            return json.dumps({
                "condition_name": "General symptoms",
                "icd_code": None,
                "confidence": 0.3,
                "confidence_level": "low",
                "differential_diagnoses": ["Multiple possible conditions"],
                "supporting_evidence": ["Symptoms reported"],
                "contraindications": [],
                "severity": "mild",
                "urgency_level": 1
            })
    
    def _parse_diagnosis_response(self, response_text: str, domain: MedicalDomain) -> Diagnosis:
        """Parse diagnosis from AI response"""
        try:
            # Try to extract JSON from response
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)
            else:
                # Fallback to basic parsing
                data = self._parse_text_response(response_text)
            
            return Diagnosis(
                condition_name=data.get("condition_name", "Unknown condition"),
                icd_code=data.get("icd_code"),
                confidence=data.get("confidence", 0.5),
                confidence_level=ConfidenceLevel(data.get("confidence_level", "medium")),
                differential_diagnoses=data.get("differential_diagnoses", []),
                supporting_evidence=data.get("supporting_evidence", []),
                contraindications=data.get("contraindications", []),
                severity=SeverityLevel(data.get("severity", "mild")),
                urgency_level=data.get("urgency_level", 1),
                domain=domain
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing diagnosis response: {str(e)}")
            return self._create_basic_diagnosis(None, domain)
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """Parse text response into structured data"""
        # Simple text parsing as fallback
        return {
            "condition_name": "General symptoms",
            "confidence": 0.3,
            "confidence_level": "low",
            "differential_diagnoses": [],
            "supporting_evidence": [],
            "contraindications": [],
            "severity": "mild",
            "urgency_level": 1
        }
    
    def _create_basic_diagnosis(self, request: Optional[MedicalAnalysisRequest], domain: MedicalDomain) -> Diagnosis:
        """Create basic diagnosis when AI fails"""
        return Diagnosis(
            condition_name="General symptoms",
            icd_code=None,
            confidence=0.3,
            confidence_level=ConfidenceLevel.LOW,
            differential_diagnoses=["Multiple possible conditions"],
            supporting_evidence=["Symptoms reported"],
            contraindications=[],
            severity=SeverityLevel.MILD,
            urgency_level=1,
            domain=domain
        )
    
    def _detect_domain(self, symptoms: List[str]) -> MedicalDomain:
        """Detect medical domain from symptoms"""
        symptoms_text = " ".join(symptoms).lower()
        
        if any(word in symptoms_text for word in ["chest", "heart", "cardiac", "ecg", "ekg"]):
            return MedicalDomain.CARDIOLOGY
        elif any(word in symptoms_text for word in ["skin", "rash", "mole", "lesion"]):
            return MedicalDomain.DERMATOLOGY
        elif any(word in symptoms_text for word in ["brain", "headache", "seizure", "stroke"]):
            return MedicalDomain.NEUROLOGY
        else:
            return MedicalDomain.GENERAL
    
    async def _generate_treatment_recommendations(self, diagnosis: Diagnosis) -> List[Any]:
        """Generate treatment recommendations based on diagnosis"""
        # This would be implemented with a treatment service
        # For now, return empty list
        return []
    
    def _calculate_confidence_score(self, diagnosis: Diagnosis, request: MedicalAnalysisRequest) -> float:
        """Calculate overall confidence score"""
        base_confidence = diagnosis.confidence
        
        # Adjust based on data quality
        data_quality = 0.5
        if request.symptoms:
            data_quality += 0.2
        if request.medical_history:
            data_quality += 0.1
        if request.vital_signs:
            data_quality += 0.1
        if request.lab_results:
            data_quality += 0.1
        
        # Combine base confidence with data quality
        return min(base_confidence * data_quality, 1.0) 