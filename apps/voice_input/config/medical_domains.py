"""
Medical Domain Configuration
Configuration settings for different medical domains and their analysis parameters.
"""

from typing import Dict, List, Any
from enum import Enum


class MedicalDomain(str, Enum):
    """Medical domains for specialized analysis"""
    DERMATOLOGY = "dermatology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    GENERAL = "general"


# Medical domain configurations
MEDICAL_DOMAIN_CONFIG = {
    MedicalDomain.DERMATOLOGY: {
        "keywords": [
            "rash", "skin", "lesion", "mole", "acne", "eczema", "psoriasis", 
            "dermatitis", "infection", "allergy", "hives", "blister", "wart",
            "melanoma", "basal cell", "squamous cell", "dermatological"
        ],
        "analysis_focus": "skin conditions, lesions, rashes, moles, infections, inflammatory conditions",
        "disclaimer": "This analysis is for educational purposes only and should not replace professional medical evaluation.",
        "recommended_models": ["gpt-4-vision-preview", "meta-llama/llama-4-scout-17b-16e-instruct"],
        "temperature": 0.3,  # Lower temperature for more focused responses
        "max_tokens": 800,
        "safety_checks": ["skin_cancer", "infection", "allergic_reaction"]
    },
    
    MedicalDomain.RADIOLOGY: {
        "keywords": [
            "x-ray", "ct", "mri", "scan", "imaging", "fracture", "tumor", 
            "mass", "lesion", "pneumonia", "cancer", "bone", "joint", "spine",
            "chest", "abdomen", "brain", "radiological", "diagnostic"
        ],
        "analysis_focus": "anatomical structures, abnormalities, fractures, masses, lesions, positioning",
        "disclaimer": "This analysis is for educational purposes only and should not replace professional radiological interpretation.",
        "recommended_models": ["gpt-4-vision-preview"],
        "temperature": 0.2,  # Very low temperature for precise analysis
        "max_tokens": 1000,
        "safety_checks": ["fracture", "tumor", "pneumonia", "cancer"]
    },
    
    MedicalDomain.PATHOLOGY: {
        "keywords": [
            "biopsy", "tissue", "cells", "microscopic", "histology", "cancer", 
            "tumor", "malignant", "benign", "metastasis", "pathological",
            "cellular", "molecular", "diagnostic"
        ],
        "analysis_focus": "cellular patterns, tissue architecture, pathological changes, diagnostic features",
        "disclaimer": "This analysis is for educational purposes only and should not replace professional pathological evaluation.",
        "recommended_models": ["gpt-4-vision-preview"],
        "temperature": 0.1,  # Very low temperature for precise cellular analysis
        "max_tokens": 1200,
        "safety_checks": ["cancer", "malignant", "metastasis", "pathological"]
    },
    
    MedicalDomain.CARDIOLOGY: {
        "keywords": [
            "heart", "ecg", "ekg", "cardiac", "arrhythmia", "infarction", 
            "cardiovascular", "coronary", "angina", "heart attack", "stroke",
            "blood pressure", "cardiovascular"
        ],
        "analysis_focus": "cardiac rhythms, structural abnormalities, vascular changes, diagnostic patterns",
        "disclaimer": "This analysis is for educational purposes only and should not replace professional cardiac evaluation.",
        "recommended_models": ["gpt-4-vision-preview", "meta-llama/llama-4-scout-17b-16e-instruct"],
        "temperature": 0.2,
        "max_tokens": 900,
        "safety_checks": ["heart_attack", "arrhythmia", "infarction", "emergency"]
    },
    
    MedicalDomain.NEUROLOGY: {
        "keywords": [
            "brain", "neurological", "stroke", "seizure", "nervous", "cognitive", 
            "motor", "sensory", "memory", "speech", "coordination", "neurological",
            "cerebral", "spinal", "nerve"
        ],
        "analysis_focus": "neurological patterns, brain structures, cognitive changes, motor function",
        "disclaimer": "This analysis is for educational purposes only and should not replace professional neurological evaluation.",
        "recommended_models": ["gpt-4-vision-preview"],
        "temperature": 0.2,
        "max_tokens": 1000,
        "safety_checks": ["stroke", "seizure", "emergency", "neurological"]
    },
    
    MedicalDomain.GENERAL: {
        "keywords": [
            "medical", "health", "symptom", "condition", "diagnosis", "treatment",
            "doctor", "patient", "clinical", "healthcare", "wellness"
        ],
        "analysis_focus": "general health assessment, symptom analysis, condition identification",
        "disclaimer": "This analysis is for educational purposes only and should not replace professional medical evaluation.",
        "recommended_models": ["gpt-4-vision-preview", "meta-llama/llama-4-scout-17b-16e-instruct"],
        "temperature": 0.5,
        "max_tokens": 800,
        "safety_checks": ["emergency", "urgent", "serious"]
    }
}

# Medical safety guidelines
MEDICAL_SAFETY_GUIDELINES = {
    "emergency_keywords": [
        "emergency", "urgent", "immediate", "critical", "severe", "acute",
        "chest pain", "shortness of breath", "unconscious", "bleeding",
        "trauma", "overdose", "poisoning"
    ],
    "disclaimer_required": True,
    "professional_consultation_required": True,
    "no_diagnosis_policy": True,
    "educational_purpose_only": True
}

# Medical response templates
MEDICAL_RESPONSE_TEMPLATES = {
    "educational_prefix": "Based on the image analysis, here are some educational insights:",
    "disclaimer_suffix": "Please note: This analysis is for educational purposes only and should not replace professional medical evaluation. Always consult with a healthcare professional for proper diagnosis and treatment.",
    "consultation_recommendation": "I recommend consulting with a healthcare professional for a proper evaluation and diagnosis.",
    "emergency_warning": "If you are experiencing severe symptoms or this is an emergency, please seek immediate medical attention or call emergency services."
}


def get_medical_domain_config(domain: MedicalDomain) -> Dict[str, Any]:
    """Get configuration for a specific medical domain"""
    return MEDICAL_DOMAIN_CONFIG.get(domain, MEDICAL_DOMAIN_CONFIG[MedicalDomain.GENERAL])


def get_medical_keywords(domain: MedicalDomain) -> List[str]:
    """Get keywords for a specific medical domain"""
    config = get_medical_domain_config(domain)
    return config.get("keywords", [])


def get_medical_disclaimer(domain: MedicalDomain) -> str:
    """Get disclaimer for a specific medical domain"""
    config = get_medical_domain_config(domain)
    return config.get("disclaimer", MEDICAL_DOMAIN_CONFIG[MedicalDomain.GENERAL]["disclaimer"])


def get_recommended_models(domain: MedicalDomain) -> List[str]:
    """Get recommended models for a specific medical domain"""
    config = get_medical_domain_config(domain)
    return config.get("recommended_models", ["gpt-4-vision-preview"])


def get_optimal_parameters(domain: MedicalDomain) -> Dict[str, Any]:
    """Get optimal parameters for a specific medical domain"""
    config = get_medical_domain_config(domain)
    return {
        "temperature": config.get("temperature", 0.5),
        "max_tokens": config.get("max_tokens", 800),
        "model": config.get("recommended_models", ["gpt-4-vision-preview"])[0]
    } 