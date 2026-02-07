"""
Medical Prompt Engineering Service
Provides medical-specific prompts and context for vision analysis and voice processing.
"""

from typing import Dict, List, Optional
from common.utils.logging import get_logger
from ..config.medical_domains import (
    MedicalDomain, 
    MEDICAL_DOMAIN_CONFIG, 
    MEDICAL_SAFETY_GUIDELINES, 
    MEDICAL_RESPONSE_TEMPLATES,
    get_medical_domain_config,
    get_optimal_parameters
)

logger = get_logger(__name__)


class MedicalPromptEngine:
    """Engine for generating medical-specific prompts and context"""
    
    def __init__(self):
        self.medical_contexts = MEDICAL_DOMAIN_CONFIG
    
    def detect_medical_domain(self, query: str) -> MedicalDomain:
        """Detect the medical domain from the query"""
        query_lower = query.lower()
        
        for domain, context in self.medical_contexts.items():
            for keyword in context["keywords"]:
                if keyword in query_lower:
                    return domain
        
        return MedicalDomain.GENERAL
    
    def create_medical_vision_prompt(self, query: str, domain: Optional[MedicalDomain] = None) -> str:
        """Create a medical-specific vision analysis prompt"""
        if not domain:
            domain = self.detect_medical_domain(query)
        
        context = self.medical_contexts[domain]
        
        medical_prompt = f"""
You are a medical AI assistant specialized in {domain.value} analysis. Your role is to provide educational insights about medical images while maintaining appropriate medical disclaimers.

CONTEXT: {context['analysis_focus']}

USER QUERY: {query}

INSTRUCTIONS:
1. Analyze the image from a {domain.value} perspective
2. Focus on {context['analysis_focus']}
3. Provide educational insights and observations
4. Use medical terminology appropriately
5. Always include appropriate medical disclaimers
6. Do not provide definitive diagnoses
7. Recommend professional medical consultation when appropriate

RESPONSE FORMAT:
- Observations: [Describe what you observe]
- Educational Context: [Provide educational information]
- Recommendations: [Suggest next steps]
- Disclaimer: {context['disclaimer']}

Please provide a comprehensive but educational response focused on {domain.value} analysis.
"""
        return medical_prompt.strip()
    
    def create_medical_voice_prompt(self, query: str, domain: Optional[MedicalDomain] = None) -> str:
        """Create a medical-specific voice analysis prompt"""
        if not domain:
            domain = self.detect_medical_domain(query)
        
        context = self.medical_contexts[domain]
        
        voice_prompt = f"""
You are a medical AI assistant specialized in {domain.value}. A user has provided a voice query about a medical image.

USER QUERY: {query}

INSTRUCTIONS:
1. Focus on {context['analysis_focus']}
2. Provide educational insights about the medical image
3. Use appropriate medical terminology
4. Include relevant medical context
5. Always include appropriate disclaimers
6. Do not provide definitive diagnoses
7. Recommend professional consultation when appropriate

RESPONSE FORMAT:
- Image Analysis: [Educational analysis of the image]
- Medical Context: [Relevant medical information]
- Recommendations: [Suggested next steps]
- Disclaimer: {context['disclaimer']}

Please provide a helpful, educational response focused on {domain.value}.
"""
        return voice_prompt.strip()
    
    def create_medical_system_prompt(self, domain: MedicalDomain = MedicalDomain.GENERAL) -> str:
        """Create a medical system prompt for the AI model"""
        context = self.medical_contexts[domain]
        
        system_prompt = f"""
You are a specialized medical AI assistant focused on {domain.value} analysis. Your primary responsibilities are:

1. EDUCATIONAL ANALYSIS: Provide educational insights about medical images and conditions
2. MEDICAL CONTEXT: Offer relevant medical information and context
3. APPROPRIATE DISCLAIMERS: Always include medical disclaimers
4. PROFESSIONAL GUIDANCE: Recommend professional medical consultation when appropriate
5. SAFETY FIRST: Never provide definitive diagnoses or treatment recommendations

SPECIALIZATION: {context['analysis_focus']}

KEY PRINCIPLES:
- Educational purpose only
- No definitive diagnoses
- Always recommend professional consultation
- Use appropriate medical terminology
- Maintain patient safety and privacy
- Follow medical ethics guidelines

DISCLAIMER: {context['disclaimer']}

You are designed to assist with educational medical analysis while maintaining appropriate medical boundaries and safety protocols.
"""
        return system_prompt.strip()
    
    def get_medical_keywords(self, domain: MedicalDomain) -> List[str]:
        """Get medical keywords for a specific domain"""
        return self.medical_contexts[domain]["keywords"]
    
    def validate_medical_query(self, query: str) -> Dict[str, any]:
        """Validate if a query is medical-related"""
        domain = self.detect_medical_domain(query)
        is_medical = domain != MedicalDomain.GENERAL or any(
            medical_word in query.lower() 
            for medical_word in ["medical", "health", "doctor", "symptom", "condition", "diagnosis"]
        )
        
        return {
            "is_medical": is_medical,
            "domain": domain,
            "confidence": 0.8 if is_medical else 0.3
        } 