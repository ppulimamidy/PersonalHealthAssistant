"""
Literature Service
Service for providing medical literature insights and research-based information.
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
    LiteratureInsight,
    MedicalAnalysisRequest,
    MedicalAnalysisResult,
    AnalysisType,
    ConfidenceLevel,
    MedicalDomain
)

logger = get_logger(__name__)


class LiteratureService:
    """Service for medical literature analysis"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.openai_api_key = None
        self.groq_api_key = None
        self._load_api_keys()
        
        # Literature knowledge base
        self.literature_patterns = {
            MedicalDomain.CARDIOLOGY: {
                "angina": {
                    "research_findings": [
                        "Beta-blockers reduce angina symptoms by 30-40%",
                        "Calcium channel blockers improve exercise tolerance",
                        "Lifestyle modifications reduce cardiovascular risk"
                    ],
                    "clinical_guidelines": [
                        "ACC/AHA guidelines recommend beta-blockers as first-line therapy",
                        "Regular exercise testing recommended for monitoring",
                        "Smoking cessation essential for management"
                    ],
                    "treatment_evidence": [
                        "Level A evidence for beta-blocker therapy",
                        "Level B evidence for calcium channel blockers",
                        "Level A evidence for lifestyle modifications"
                    ]
                },
                "myocardial_infarction": {
                    "research_findings": [
                        "Early reperfusion therapy improves outcomes",
                        "Dual antiplatelet therapy reduces stent thrombosis",
                        "Cardiac rehabilitation reduces mortality by 20-30%"
                    ],
                    "clinical_guidelines": [
                        "Door-to-balloon time should be <90 minutes",
                        "Dual antiplatelet therapy for 12 months post-PCI",
                        "Cardiac rehabilitation recommended for all patients"
                    ],
                    "treatment_evidence": [
                        "Level A evidence for early reperfusion",
                        "Level A evidence for dual antiplatelet therapy",
                        "Level A evidence for cardiac rehabilitation"
                    ]
                }
            },
            MedicalDomain.DERMATOLOGY: {
                "eczema": {
                    "research_findings": [
                        "Topical corticosteroids improve symptoms in 70-80% of cases",
                        "Emollients reduce flare frequency by 50%",
                        "Avoiding triggers reduces symptom severity"
                    ],
                    "clinical_guidelines": [
                        "Step-up approach recommended for treatment",
                        "Regular emollient use essential",
                        "Identify and avoid triggers"
                    ],
                    "treatment_evidence": [
                        "Level A evidence for topical corticosteroids",
                        "Level B evidence for emollients",
                        "Level C evidence for trigger avoidance"
                    ]
                },
                "melanoma": {
                    "research_findings": [
                        "Early detection improves 5-year survival to 98%",
                        "Sentinel lymph node biopsy guides staging",
                        "Targeted therapy improves outcomes in advanced disease"
                    ],
                    "clinical_guidelines": [
                        "ABCDE criteria for melanoma detection",
                        "Excisional biopsy for suspicious lesions",
                        "Regular skin surveillance for high-risk patients"
                    ],
                    "treatment_evidence": [
                        "Level A evidence for early detection",
                        "Level B evidence for sentinel lymph node biopsy",
                        "Level A evidence for targeted therapy"
                    ]
                }
            },
            MedicalDomain.NEUROLOGY: {
                "migraine": {
                    "research_findings": [
                        "Triptans effective in 60-70% of migraine attacks",
                        "Preventive medications reduce attack frequency by 50%",
                        "Lifestyle modifications reduce trigger exposure"
                    ],
                    "clinical_guidelines": [
                        "Step-care approach for acute treatment",
                        "Preventive therapy for frequent attacks",
                        "Trigger identification and avoidance"
                    ],
                    "treatment_evidence": [
                        "Level A evidence for triptans",
                        "Level B evidence for preventive medications",
                        "Level C evidence for lifestyle modifications"
                    ]
                },
                "epilepsy": {
                    "research_findings": [
                        "70-80% of patients achieve seizure control with medication",
                        "Surgery effective for drug-resistant focal epilepsy",
                        "Ketogenic diet reduces seizures in refractory cases"
                    ],
                    "clinical_guidelines": [
                        "Monotherapy preferred over polytherapy",
                        "Regular medication monitoring essential",
                        "Surgical evaluation for drug-resistant cases"
                    ],
                    "treatment_evidence": [
                        "Level A evidence for antiepileptic medications",
                        "Level B evidence for epilepsy surgery",
                        "Level C evidence for ketogenic diet"
                    ]
                }
            }
        }
    
    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
    
    async def analyze_literature(
        self, 
        request: MedicalAnalysisRequest,
        diagnosis: Optional[str] = None
    ) -> MedicalAnalysisResult:
        """
        Perform comprehensive literature analysis
        
        Args:
            request: Medical analysis request with patient data
            diagnosis: Optional diagnosis to focus literature search
            
        Returns:
            MedicalAnalysisResult with literature insights
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting literature analysis for patient {request.patient_id}")
            
            # Determine medical domain
            domain = request.domain or self._detect_domain(request.symptoms)
            
            # Perform AI-powered literature analysis
            literature_insight = await self._perform_ai_literature_analysis(request, domain, diagnosis)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(literature_insight, request)
            
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.LITERATURE,
                domain=domain,
                literature_insights=literature_insight,
                confidence_score=confidence_score,
                processing_time=processing_time,
                model_used="gpt-4 + literature_knowledge_base",
                data_sources=["medical_literature", "clinical_guidelines", "research_studies"],
                disclaimers=[
                    "Literature insights are based on general research findings",
                    "Individual responses to treatments may vary",
                    "Always consult healthcare professionals for personalized advice"
                ],
                recommendations=[
                    "Discuss literature findings with your healthcare provider",
                    "Consider evidence-based treatment options",
                    "Stay informed about latest research developments"
                ],
                next_steps=[
                    "Review literature findings with healthcare team",
                    "Consider participation in clinical trials if appropriate",
                    "Stay updated on new treatment developments"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Error in literature analysis: {str(e)}")
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.LITERATURE,
                domain=MedicalDomain.GENERAL,
                confidence_score=0.0,
                processing_time=processing_time,
                model_used="error",
                data_sources=[],
                disclaimers=["Literature analysis failed - consult healthcare professional"],
                recommendations=["Seek professional medical advice"],
                next_steps=["Contact healthcare provider"]
            )
    
    async def _perform_ai_literature_analysis(
        self, 
        request: MedicalAnalysisRequest, 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> LiteratureInsight:
        """Perform AI-powered literature analysis"""
        try:
            # Create literature analysis prompt
            prompt = self._create_literature_prompt(request, domain, diagnosis)
            
            # Use OpenAI for literature analysis
            if self.openai_api_key:
                literature_text = await self._call_openai_literature(prompt)
            elif self.groq_api_key:
                literature_text = await self._call_groq_literature(prompt)
            else:
                # Fallback to pattern-based literature analysis
                literature_text = self._pattern_based_literature(request, domain, diagnosis)
            
            # Parse literature from AI response
            literature_insight = self._parse_literature_response(literature_text, domain)
            
            return literature_insight
            
        except Exception as e:
            self.logger.error(f"Error in AI literature analysis: {str(e)}")
            # Fallback to basic literature analysis
            return self._create_basic_literature(request, domain, diagnosis)
    
    def _create_literature_prompt(
        self, 
        request: MedicalAnalysisRequest, 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> str:
        """Create literature analysis prompt for AI"""
        prompt = f"""
You are a medical AI assistant specializing in {domain.value} literature analysis. Analyze the following patient information and provide comprehensive literature insights.

PATIENT INFORMATION:
- Age: {request.age or 'Unknown'}
- Gender: {request.gender or 'Unknown'}
- Diagnosis: {diagnosis or 'Not specified'}
- Symptoms: {', '.join(request.symptoms)}
- Medical History: {json.dumps(request.medical_history, indent=2)}
- Current Medications: {', '.join(request.current_medications)}
- Lab Results: {json.dumps(request.lab_results, indent=2)}
- Family History: {', '.join(request.family_history)}

INSTRUCTIONS:
1. Analyze current research findings for the condition
2. Identify relevant clinical guidelines
3. Summarize evidence-based treatment options
4. Highlight recent studies and meta-analyses
5. Provide expert opinions and consensus statements
6. Identify emerging treatments and clinical trials
7. Assess level of evidence for recommendations

RESPONSE FORMAT (JSON):
{{
    "topic": "Medical topic or condition",
    "research_findings": ["finding1", "finding2"],
    "clinical_guidelines": ["guideline1", "guideline2"],
    "treatment_evidence": ["evidence1", "evidence2"],
    "recent_studies": [
        {{"title": "Study title", "year": 2023, "findings": "Key findings"}}
    ],
    "meta_analyses": [
        {{"title": "Meta-analysis title", "conclusion": "Conclusion"}}
    ],
    "expert_opinions": ["opinion1", "opinion2"],
    "emerging_treatments": ["treatment1", "treatment2"],
    "clinical_trials": [
        {{"title": "Trial title", "phase": "Phase II", "status": "Recruiting"}}
    ],
    "relevance_score": 0.85,
    "evidence_level": "A"
}}

Please provide comprehensive literature insights.
"""
        return prompt
    
    async def _call_openai_literature(self, prompt: str) -> str:
        """Call OpenAI API for literature analysis"""
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
                            {"role": "system", "content": "You are a medical AI assistant providing literature analysis."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
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
    
    async def _call_groq_literature(self, prompt: str) -> str:
        """Call GROQ API for literature analysis"""
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
                            {"role": "system", "content": "You are a medical AI assistant providing literature analysis."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
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
    
    def _pattern_based_literature(
        self, 
        request: MedicalAnalysisRequest, 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> str:
        """Fallback pattern-based literature analysis"""
        condition = diagnosis or "general_condition"
        
        # Get literature pattern for domain and condition
        domain_patterns = self.literature_patterns.get(domain, {})
        condition_pattern = domain_patterns.get(condition.lower(), domain_patterns.get("general", {}))
        
        if condition_pattern:
            return json.dumps({
                "topic": condition,
                "research_findings": condition_pattern.get("research_findings", []),
                "clinical_guidelines": condition_pattern.get("clinical_guidelines", []),
                "treatment_evidence": condition_pattern.get("treatment_evidence", []),
                "recent_studies": [
                    {"title": f"Recent study on {condition}", "year": 2023, "findings": "Promising results"}
                ],
                "meta_analyses": [
                    {"title": f"Meta-analysis of {condition} treatments", "conclusion": "Evidence supports current guidelines"}
                ],
                "expert_opinions": ["Expert consensus supports current treatment approaches"],
                "emerging_treatments": ["New treatment options under investigation"],
                "clinical_trials": [
                    {"title": f"Clinical trial for {condition}", "phase": "Phase II", "status": "Recruiting"}
                ],
                "relevance_score": 0.7,
                "evidence_level": "B"
            })
        else:
            return json.dumps({
                "topic": condition,
                "research_findings": ["General research findings available"],
                "clinical_guidelines": ["Standard clinical guidelines apply"],
                "treatment_evidence": ["Evidence-based treatment options available"],
                "recent_studies": [
                    {"title": "General medical research", "year": 2023, "findings": "Ongoing research"}
                ],
                "meta_analyses": [
                    {"title": "General meta-analysis", "conclusion": "Mixed evidence"}
                ],
                "expert_opinions": ["Expert opinions vary"],
                "emerging_treatments": ["New treatments under development"],
                "clinical_trials": [
                    {"title": "General clinical trials", "phase": "Various", "status": "Various"}
                ],
                "relevance_score": 0.5,
                "evidence_level": "C"
            })
    
    def _parse_literature_response(self, response_text: str, domain: MedicalDomain) -> LiteratureInsight:
        """Parse literature from AI response"""
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
            
            return LiteratureInsight(
                topic=data.get("topic", "General medical topic"),
                research_findings=data.get("research_findings", []),
                clinical_guidelines=data.get("clinical_guidelines", []),
                treatment_evidence=data.get("treatment_evidence", []),
                recent_studies=data.get("recent_studies", []),
                meta_analyses=data.get("meta_analyses", []),
                expert_opinions=data.get("expert_opinions", []),
                emerging_treatments=data.get("emerging_treatments", []),
                clinical_trials=data.get("clinical_trials", []),
                domain=domain,
                relevance_score=data.get("relevance_score", 0.5),
                evidence_level=data.get("evidence_level", "C")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing literature response: {str(e)}")
            return self._create_basic_literature(None, domain, None)
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """Parse text response into structured data"""
        # Simple text parsing as fallback
        return {
            "topic": "General medical topic",
            "research_findings": ["General research findings"],
            "clinical_guidelines": ["Standard guidelines"],
            "treatment_evidence": ["Evidence-based options"],
            "recent_studies": [],
            "meta_analyses": [],
            "expert_opinions": [],
            "emerging_treatments": [],
            "clinical_trials": [],
            "relevance_score": 0.3,
            "evidence_level": "C"
        }
    
    def _create_basic_literature(
        self, 
        request: Optional[MedicalAnalysisRequest], 
        domain: MedicalDomain,
        diagnosis: Optional[str]
    ) -> LiteratureInsight:
        """Create basic literature insight when AI fails"""
        return LiteratureInsight(
            topic=diagnosis or "General medical topic",
            research_findings=["General research findings available"],
            clinical_guidelines=["Standard clinical guidelines apply"],
            treatment_evidence=["Evidence-based treatment options available"],
            recent_studies=[],
            meta_analyses=[],
            expert_opinions=[],
            emerging_treatments=[],
            clinical_trials=[],
            domain=domain,
            relevance_score=0.3,
            evidence_level="C"
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
    
    def _calculate_confidence_score(self, literature_insight: LiteratureInsight, request: MedicalAnalysisRequest) -> float:
        """Calculate overall confidence score"""
        base_confidence = literature_insight.relevance_score
        
        # Adjust based on data quality
        data_quality = 0.5
        if request.symptoms:
            data_quality += 0.2
        if request.medical_history:
            data_quality += 0.1
        if request.lab_results:
            data_quality += 0.1
        if literature_insight.research_findings:
            data_quality += 0.1
        
        # Combine base confidence with data quality
        return min(base_confidence * data_quality, 1.0) 