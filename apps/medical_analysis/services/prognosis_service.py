"""
Prognosis Service
Service for providing medical prognosis based on diagnosis and patient data.
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
    Prognosis,
    MedicalAnalysisRequest,
    MedicalAnalysisResult,
    AnalysisType,
    ConfidenceLevel,
    MedicalDomain
)

logger = get_logger(__name__)


class PrognosisService:
    """Service for medical prognosis analysis"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.openai_api_key = None
        self.groq_api_key = None
        self._load_api_keys()
        
        # Prognosis knowledge base
        self.prognosis_patterns = {
            MedicalDomain.CARDIOLOGY: {
                "angina": {
                    "short_term": "Stable with medication management",
                    "long_term": "Good with lifestyle modifications",
                    "risk_factors": ["smoking", "diabetes", "hypertension"],
                    "protective_factors": ["exercise", "healthy_diet", "medication_compliance"]
                },
                "myocardial_infarction": {
                    "short_term": "Critical period requiring intensive care",
                    "long_term": "Variable based on extent of damage",
                    "risk_factors": ["age", "diabetes", "previous_heart_attack"],
                    "protective_factors": ["early_intervention", "cardiac_rehabilitation"]
                }
            },
            MedicalDomain.DERMATOLOGY: {
                "eczema": {
                    "short_term": "Manageable with topical treatments",
                    "long_term": "Chronic condition with flare-ups",
                    "risk_factors": ["allergies", "stress", "dry_skin"],
                    "protective_factors": ["moisturizing", "avoiding_triggers"]
                },
                "melanoma": {
                    "short_term": "Depends on stage at diagnosis",
                    "long_term": "Good prognosis if caught early",
                    "risk_factors": ["sun_exposure", "family_history", "fair_skin"],
                    "protective_factors": ["early_detection", "sun_protection"]
                }
            },
            MedicalDomain.NEUROLOGY: {
                "migraine": {
                    "short_term": "Episodic with acute treatment",
                    "long_term": "Chronic condition with preventive strategies",
                    "risk_factors": ["stress", "hormonal_changes", "certain_foods"],
                    "protective_factors": ["trigger_avoidance", "preventive_medication"]
                },
                "epilepsy": {
                    "short_term": "Controlled with medication in most cases",
                    "long_term": "Variable - many achieve remission",
                    "risk_factors": ["brain_injury", "family_history", "sleep_deprivation"],
                    "protective_factors": ["medication_compliance", "lifestyle_modifications"]
                }
            }
        }
    
    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
    
    async def analyze_prognosis(
        self, 
        request: MedicalAnalysisRequest,
        diagnosis: Optional[str] = None
    ) -> MedicalAnalysisResult:
        """
        Perform comprehensive prognosis analysis
        
        Args:
            request: Medical analysis request with patient data
            diagnosis: Optional diagnosis to base prognosis on
            
        Returns:
            MedicalAnalysisResult with prognosis
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting prognosis analysis for patient {request.patient_id}")
            
            # Determine medical domain
            domain = request.domain or self._detect_domain(request.symptoms)
            
            # Perform AI-powered prognosis
            prognosis = await self._perform_ai_prognosis(request, domain, diagnosis)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(prognosis, request)
            
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.PROGNOSIS,
                domain=domain,
                prognosis=prognosis,
                confidence_score=confidence_score,
                processing_time=processing_time,
                model_used="gpt-4 + prognosis_knowledge_base",
                data_sources=["patient_symptoms", "medical_history", "diagnosis", "risk_factors"],
                disclaimers=[
                    "This prognosis is AI-assisted and should be discussed with healthcare professionals",
                    "Individual outcomes may vary significantly",
                    "Prognosis is based on general patterns and may not apply to specific cases"
                ],
                recommendations=[
                    "Discuss prognosis with your healthcare provider",
                    "Follow recommended treatment and monitoring plans",
                    "Address modifiable risk factors"
                ],
                next_steps=[
                    "Schedule follow-up appointments",
                    "Implement recommended lifestyle changes",
                    "Monitor for changes in condition"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Error in prognosis analysis: {str(e)}")
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.PROGNOSIS,
                domain=MedicalDomain.GENERAL,
                confidence_score=0.0,
                processing_time=processing_time,
                model_used="error",
                data_sources=[],
                disclaimers=["Prognosis analysis failed - consult healthcare professional"],
                recommendations=["Seek professional medical advice"],
                next_steps=["Contact healthcare provider"]
            )
    
    async def _perform_ai_prognosis(
        self, 
        request: MedicalAnalysisRequest, 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> Prognosis:
        """Perform AI-powered prognosis"""
        try:
            # Create prognosis prompt
            prompt = self._create_prognosis_prompt(request, domain, diagnosis)
            
            # Use OpenAI for prognosis
            if self.openai_api_key:
                prognosis_text = await self._call_openai_prognosis(prompt)
            elif self.groq_api_key:
                prognosis_text = await self._call_groq_prognosis(prompt)
            else:
                # Fallback to pattern-based prognosis
                prognosis_text = self._pattern_based_prognosis(request, domain, diagnosis)
            
            # Parse prognosis from AI response
            prognosis = self._parse_prognosis_response(prognosis_text, domain)
            
            return prognosis
            
        except Exception as e:
            self.logger.error(f"Error in AI prognosis: {str(e)}")
            # Fallback to basic prognosis
            return self._create_basic_prognosis(request, domain, diagnosis)
    
    def _create_prognosis_prompt(
        self, 
        request: MedicalAnalysisRequest, 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> str:
        """Create prognosis prompt for AI"""
        prompt = f"""
You are a medical AI assistant specializing in {domain.value} prognosis. Analyze the following patient information and provide a comprehensive prognosis.

PATIENT INFORMATION:
- Age: {request.age or 'Unknown'}
- Gender: {request.gender or 'Unknown'}
- Diagnosis: {diagnosis or 'Not specified'}
- Symptoms: {', '.join(request.symptoms)}
- Medical History: {json.dumps(request.medical_history, indent=2)}
- Current Medications: {', '.join(request.current_medications)}
- Vital Signs: {json.dumps(request.vital_signs, indent=2)}
- Lab Results: {json.dumps(request.lab_results, indent=2)}
- Family History: {', '.join(request.family_history)}
- Lifestyle Factors: {json.dumps(request.lifestyle_factors, indent=2)}

INSTRUCTIONS:
1. Analyze the diagnosis and patient factors
2. Provide short-term and long-term prognosis
3. Identify risk factors affecting prognosis
4. Identify protective factors
5. Assess expected progression stages
6. Estimate survival rate if applicable
7. Evaluate quality of life impact

RESPONSE FORMAT (JSON):
{{
    "condition_name": "Diagnosed condition",
    "prognosis_type": "short-term",
    "predicted_outcome": "Expected outcome description",
    "time_frame": "Expected time frame",
    "confidence": 0.8,
    "confidence_level": "high",
    "risk_factors": ["risk1", "risk2"],
    "protective_factors": ["protective1", "protective2"],
    "progression_stages": ["stage1", "stage2"],
    "survival_rate": 0.95,
    "quality_of_life_impact": "Expected impact on quality of life"
}}

Please provide a comprehensive prognosis analysis.
"""
        return prompt
    
    async def _call_openai_prognosis(self, prompt: str) -> str:
        """Call OpenAI API for prognosis"""
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
                            {"role": "system", "content": "You are a medical AI assistant providing prognosis analysis."},
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
    
    async def _call_groq_prognosis(self, prompt: str) -> str:
        """Call GROQ API for prognosis"""
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
                            {"role": "system", "content": "You are a medical AI assistant providing prognosis analysis."},
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
    
    def _pattern_based_prognosis(
        self, 
        request: MedicalAnalysisRequest, 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> str:
        """Fallback pattern-based prognosis"""
        condition = diagnosis or "general_symptoms"
        
        # Get prognosis pattern for domain and condition
        domain_patterns = self.prognosis_patterns.get(domain, {})
        condition_pattern = domain_patterns.get(condition.lower(), domain_patterns.get("general", {}))
        
        if condition_pattern:
            return json.dumps({
                "condition_name": condition,
                "prognosis_type": "short-term",
                "predicted_outcome": condition_pattern.get("short_term", "Variable outcome"),
                "time_frame": "3-6 months",
                "confidence": 0.6,
                "confidence_level": "medium",
                "risk_factors": condition_pattern.get("risk_factors", []),
                "protective_factors": condition_pattern.get("protective_factors", []),
                "progression_stages": ["Initial", "Progressive", "Stable"],
                "survival_rate": 0.9,
                "quality_of_life_impact": "Moderate impact expected"
            })
        else:
            return json.dumps({
                "condition_name": condition,
                "prognosis_type": "general",
                "predicted_outcome": "Variable outcome based on individual factors",
                "time_frame": "Variable",
                "confidence": 0.4,
                "confidence_level": "low",
                "risk_factors": ["age", "comorbidities"],
                "protective_factors": ["healthy_lifestyle", "medical_compliance"],
                "progression_stages": ["Initial", "Follow-up"],
                "survival_rate": None,
                "quality_of_life_impact": "Variable impact"
            })
    
    def _parse_prognosis_response(self, response_text: str, domain: MedicalDomain) -> Prognosis:
        """Parse prognosis from AI response"""
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
            
            return Prognosis(
                condition_name=data.get("condition_name", "Unknown condition"),
                prognosis_type=data.get("prognosis_type", "general"),
                predicted_outcome=data.get("predicted_outcome", "Variable outcome"),
                time_frame=data.get("time_frame", "Variable"),
                confidence=data.get("confidence", 0.5),
                confidence_level=ConfidenceLevel(data.get("confidence_level", "medium")),
                risk_factors=data.get("risk_factors", []),
                protective_factors=data.get("protective_factors", []),
                progression_stages=data.get("progression_stages", []),
                survival_rate=data.get("survival_rate"),
                quality_of_life_impact=data.get("quality_of_life_impact", "Variable impact"),
                domain=domain
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing prognosis response: {str(e)}")
            return self._create_basic_prognosis(None, domain, None)
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """Parse text response into structured data"""
        # Simple text parsing as fallback
        return {
            "condition_name": "General condition",
            "prognosis_type": "general",
            "predicted_outcome": "Variable outcome",
            "time_frame": "Variable",
            "confidence": 0.3,
            "confidence_level": "low",
            "risk_factors": [],
            "protective_factors": [],
            "progression_stages": [],
            "survival_rate": None,
            "quality_of_life_impact": "Variable impact"
        }
    
    def _create_basic_prognosis(
        self, 
        request: Optional[MedicalAnalysisRequest], 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> Prognosis:
        """Create basic prognosis when AI fails"""
        return Prognosis(
            condition_name=diagnosis or "General condition",
            prognosis_type="general",
            predicted_outcome="Variable outcome based on individual factors",
            time_frame="Variable",
            confidence=0.3,
            confidence_level=ConfidenceLevel.LOW,
            risk_factors=["age", "comorbidities"],
            protective_factors=["healthy_lifestyle", "medical_compliance"],
            progression_stages=["Initial", "Follow-up"],
            survival_rate=None,
            quality_of_life_impact="Variable impact",
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
    
    def _calculate_confidence_score(self, prognosis: Prognosis, request: MedicalAnalysisRequest) -> float:
        """Calculate overall confidence score"""
        base_confidence = prognosis.confidence
        
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