"""
Health Analysis Models

Pydantic models for health analysis requests, responses, and data structures.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class UrgencyLevel(str, Enum):
    """Urgency levels for medical conditions."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EMERGENCY = "emergency"


class TriageLevel(str, Enum):
    """Medical triage levels."""
    IMMEDIATE = "immediate"  # Level 1 - Life-threatening
    EMERGENT = "emergent"    # Level 2 - Urgent care within 1 hour
    URGENT = "urgent"        # Level 3 - Care within 4 hours
    LESS_URGENT = "less_urgent"  # Level 4 - Care within 24 hours
    NON_URGENT = "non_urgent"    # Level 5 - Can wait for appointment


class ConditionType(str, Enum):
    """Types of medical conditions."""
    SKIN = "skin"
    INJURY = "injury"
    EYE = "eye"
    DENTAL = "dental"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    CARDIAC = "cardiac"
    NEUROLOGICAL = "neurological"
    MUSCULOSKELETAL = "musculoskeletal"
    ENDOCRINE = "endocrine"
    HEMATOLOGICAL = "hematological"
    IMMUNOLOGICAL = "immunological"
    INFECTIOUS = "infectious"
    PSYCHIATRIC = "psychiatric"
    REPRODUCTIVE = "reproductive"
    PEDIATRIC = "pediatric"
    GERIATRIC = "geriatric"
    EMERGENCY = "emergency"
    GENERAL = "general"


class AnalysisModel(str, Enum):
    """Available health analysis models."""
    OPENAI_VISION = "openai_vision"
    GOOGLE_VISION = "google_vision"
    AZURE_VISION = "azure_vision"
    BIOGPT = "biogpt"
    PUBMEDGPT = "pubmedgpt"
    CUSTOM_MEDICAL = "custom_medical"
    DERMATOLOGY_AI = "dermatology_ai"
    RADIOLOGY_AI = "radiology_ai"


class ImageFormat(str, Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    HEIC = "heic"


class DetectedCondition(BaseModel):
    """A detected medical condition from image analysis."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    name: str = Field(..., description="Name of the detected condition")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (0-1)")
    
    # Condition details
    category: ConditionType = Field(..., description="Category of the condition")
    severity: str = Field(..., description="Severity level (mild, moderate, severe)")
    urgency: UrgencyLevel = Field(..., description="Urgency level")
    
    # Symptoms
    symptoms: List[str] = Field(default_factory=list, description="Associated symptoms")
    
    # Analysis metadata
    model_used: AnalysisModel = Field(..., description="Model used for detection")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    
    # Additional information
    description: Optional[str] = Field(None, description="Detailed description")
    differential_diagnosis: Optional[List[str]] = Field(None, description="Possible alternative diagnoses")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")

    model_config = {"protected_namespaces": ()}


class MedicalInsight(BaseModel):
    """Medical insight and analysis result."""
    
    condition: DetectedCondition = Field(..., description="Detected condition")
    
    # Analysis results
    prognosis: str = Field(..., description="Medical prognosis")
    diagnosis: str = Field(..., description="Primary diagnosis")
    confidence_level: str = Field(..., description="Confidence level of diagnosis")
    
    # Detailed analysis
    analysis_summary: str = Field(..., description="Summary of the analysis")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from analysis")
    
    # Risk assessment
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    complications: List[str] = Field(default_factory=list, description="Potential complications")
    
    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions to take")
    follow_up_actions: List[str] = Field(default_factory=list, description="Follow-up actions")
    
    # Medical advice
    medical_advice: str = Field(..., description="Medical advice and recommendations")
    when_to_seek_care: str = Field(..., description="When to seek medical care")
    
    # Additional information
    related_conditions: List[str] = Field(default_factory=list, description="Related medical conditions")
    prevention_tips: List[str] = Field(default_factory=list, description="Prevention tips")


class TreatmentRecommendation(BaseModel):
    """Treatment recommendation for a medical condition."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    condition_id: str = Field(..., description="Associated condition ID")
    
    # Treatment details
    treatment_type: str = Field(..., description="Type of treatment (home_care, medication, procedure)")
    name: str = Field(..., description="Treatment name")
    description: str = Field(..., description="Treatment description")
    
    # Instructions
    instructions: List[str] = Field(default_factory=list, description="Step-by-step instructions")
    
    # Medication details
    medications: List[str] = Field(default_factory=list, description="List of medications")
    dosages: List[str] = Field(default_factory=list, description="Medication dosages")
    duration: str = Field(..., description="Treatment duration")
    
    # Safety information
    precautions: List[str] = Field(default_factory=list, description="Precautions to take")
    side_effects: List[str] = Field(default_factory=list, description="Potential side effects")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications")
    warnings: List[str] = Field(default_factory=list, description="Important warnings")
    
    # Effectiveness
    effectiveness: str = Field(..., description="Expected effectiveness")
    time_to_improvement: Optional[str] = Field(None, description="Expected time to improvement")
    
    # Cost and availability
    cost_estimate: Optional[str] = Field(None, description="Estimated cost")
    availability: str = Field(..., description="Availability (otc, prescription, procedure)")
    
    # Evidence
    evidence_level: str = Field(..., description="Level of evidence supporting the treatment")
    source: Optional[str] = Field(None, description="Source of recommendation")
    
    # Follow-up and monitoring
    when_to_stop: str = Field(..., description="When to stop the treatment")
    follow_up: str = Field(..., description="Follow-up instructions")
    
    # Lifestyle and prevention
    lifestyle_modifications: List[str] = Field(default_factory=list, description="Lifestyle modifications")
    diet_modifications: List[str] = Field(default_factory=list, description="Diet modifications")
    prevention_strategies: List[str] = Field(default_factory=list, description="Prevention strategies")
    
    # Research and evidence
    pubmed_research: List[str] = Field(default_factory=list, description="PubMed research abstracts")
    research_summary: Optional[str] = Field(None, description="Research summary")


class SymptomAnalysis(BaseModel):
    """Detailed symptom analysis."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Symptom details
    primary_symptoms: List[str] = Field(default_factory=list, description="Primary symptoms")
    secondary_symptoms: List[str] = Field(default_factory=list, description="Secondary symptoms")
    
    # Analysis results
    symptom_severity: str = Field(..., description="Overall symptom severity")
    symptom_duration: Optional[str] = Field(None, description="How long symptoms have been present")
    
    # Possible causes
    possible_causes: List[str] = Field(default_factory=list, description="Possible causes")
    most_likely_cause: str = Field(..., description="Most likely cause")
    
    # Differential diagnosis
    differential_diagnosis: List[str] = Field(default_factory=list, description="Differential diagnosis")
    
    # Risk assessment
    risk_level: str = Field(..., description="Risk level assessment")
    emergency_indicators: List[str] = Field(default_factory=list, description="Emergency warning signs")
    
    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions")
    monitoring_advice: str = Field(..., description="What to monitor")
    
    # Follow-up
    follow_up_timeline: str = Field(..., description="When to follow up")
    specialist_referral: Optional[str] = Field(None, description="Specialist referral if needed")


class RiskAssessment(BaseModel):
    """Health risk assessment."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Risk levels
    overall_risk: str = Field(..., description="Overall risk level")
    immediate_risk: str = Field(..., description="Immediate risk level")
    long_term_risk: str = Field(..., description="Long-term risk level")
    
    # Risk factors
    identified_risks: List[str] = Field(default_factory=list, description="Identified risk factors")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Risk score (0-10)")
    
    # Complications
    potential_complications: List[str] = Field(default_factory=list, description="Potential complications")
    complication_probability: Dict[str, float] = Field(default_factory=dict, description="Probability of complications")
    
    # Emergency indicators
    emergency_indicators: List[str] = Field(default_factory=list, description="Emergency warning signs")
    emergency_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of emergency")
    
    # Preventive measures
    preventive_measures: List[str] = Field(default_factory=list, description="Preventive measures")
    lifestyle_recommendations: List[str] = Field(default_factory=list, description="Lifestyle recommendations")
    
    # Monitoring
    monitoring_requirements: List[str] = Field(default_factory=list, description="Monitoring requirements")
    follow_up_schedule: str = Field(..., description="Recommended follow-up schedule")


class EmergencyAssessmentResponse(BaseModel):
    """Response from emergency assessment."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Assessment results
    triage_level: TriageLevel = Field(..., description="Triage level")
    urgency_level: UrgencyLevel = Field(..., description="Urgency level")
    severity_score: float = Field(..., ge=0.0, le=10.0, description="Severity score (0-10)")
    
    # Emergency indicators
    is_emergency: bool = Field(..., description="Whether this is an emergency")
    call_911: bool = Field(..., description="Whether to call 911")
    seek_immediate_care: bool = Field(..., description="Whether to seek immediate care")
    
    # Assessment details
    primary_concern: str = Field(..., description="Primary medical concern")
    detected_conditions: List[DetectedCondition] = Field(default_factory=list, description="Detected conditions")
    
    # Immediate actions
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions to take")
    do_not_do: List[str] = Field(default_factory=list, description="Things not to do")
    
    # Care guidance
    care_level: str = Field(..., description="Recommended level of care")
    facility_type: str = Field(..., description="Type of facility to visit")
    time_to_care: str = Field(..., description="How quickly to seek care")
    
    # Monitoring
    signs_to_watch: List[str] = Field(default_factory=list, description="Signs to watch for")
    when_to_escalate: str = Field(..., description="When to escalate care")
    
    # Processing information
    processing_time: float = Field(..., description="Processing time in seconds")
    models_used: List[AnalysisModel] = Field(..., description="Models used for analysis")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Assessment timestamp")


class TriageResult(BaseModel):
    """Medical triage result."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Triage assessment
    triage_level: TriageLevel = Field(..., description="Triage level")
    triage_score: float = Field(..., ge=1.0, le=5.0, description="Triage score (1-5)")
    
    # Urgency assessment
    urgency_level: UrgencyLevel = Field(..., description="Urgency level")
    wait_time: str = Field(..., description="Recommended wait time")
    
    # Care recommendations
    care_recommendation: str = Field(..., description="Care recommendation")
    facility_recommendation: str = Field(..., description="Recommended facility type")
    
    # Clinical indicators
    vital_signs_concern: bool = Field(..., description="Whether vital signs are concerning")
    pain_level: int = Field(..., ge=1, le=10, description="Assessed pain level")
    
    # Risk factors
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    comorbidities: List[str] = Field(default_factory=list, description="Relevant comorbidities")
    
    # Processing information
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Triage confidence")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Triage timestamp")


class EmergencyRecommendation(BaseModel):
    """Emergency recommendation."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Recommendation details
    type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    
    # Actions
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions")
    do_not_actions: List[str] = Field(default_factory=list, description="Actions to avoid")
    
    # Timing
    urgency: str = Field(..., description="How urgent this is")
    time_frame: str = Field(..., description="Time frame for action")
    
    # Resources
    resources_needed: List[str] = Field(default_factory=list, description="Resources needed")
    contact_information: Optional[str] = Field(None, description="Contact information if needed")


class HealthAnalysisRequest(BaseModel):
    """Request for health image analysis."""
    
    user_id: str = Field(..., description="User identifier")
    image_data: bytes = Field(..., description="Image data")
    image_format: str = Field(..., description="Image format")
    
    # Analysis options
    user_query: Optional[str] = Field(None, description="User's specific question")
    body_part: Optional[str] = Field(None, description="Affected body part")
    symptoms: Optional[str] = Field(None, description="Additional symptoms")
    urgency_level: UrgencyLevel = Field(UrgencyLevel.NORMAL, description="Urgency level")
    
    # Processing options
    models_to_use: List[AnalysisModel] = Field(
        default=[AnalysisModel.BIOGPT, AnalysisModel.PUBMEDGPT],
        description="Models to use for analysis"
    )
    enable_detailed_analysis: bool = Field(True, description="Enable detailed analysis")
    enable_treatment_recommendations: bool = Field(True, description="Enable treatment recommendations")
    
    # Context
    medical_history: Optional[List[str]] = Field(None, description="Relevant medical history")
    current_medications: Optional[List[str]] = Field(None, description="Current medications")
    allergies: Optional[List[str]] = Field(None, description="Known allergies")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")


class HealthAnalysisResponse(BaseModel):
    """Response from health image analysis."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Analysis results
    detected_conditions: List[DetectedCondition] = Field(default_factory=list, description="Detected conditions")
    medical_insights: List[MedicalInsight] = Field(default_factory=list, description="Medical insights")
    
    # Overall assessment
    overall_severity: str = Field(..., description="Overall severity assessment")
    urgency_level: UrgencyLevel = Field(..., description="Overall urgency level")
    triage_level: TriageLevel = Field(..., description="Triage level")
    
    # Recommendations
    treatment_recommendations: List[TreatmentRecommendation] = Field(default_factory=list, description="Treatment recommendations")
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions")
    
    # Medical advice
    medical_advice: str = Field(..., description="Medical advice")
    when_to_seek_care: str = Field(..., description="When to seek medical care")
    
    # Risk assessment
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment")
    
    # Processing information
    processing_time: float = Field(..., description="Total processing time")
    models_used: List[AnalysisModel] = Field(..., description="Models used")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    
    # Warnings and disclaimers
    warnings: List[str] = Field(default_factory=list, description="Important warnings")
    disclaimers: List[str] = Field(default_factory=list, description="Medical disclaimers")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ConditionDetectionRequest(BaseModel):
    """Request for specific condition detection."""
    
    user_id: str = Field(..., description="User identifier")
    image_data: bytes = Field(..., description="Image data")
    condition_type: ConditionType = Field(..., description="Type of condition to detect")
    
    # Detection options
    enable_differential_diagnosis: bool = Field(True, description="Enable differential diagnosis")
    enable_severity_assessment: bool = Field(True, description="Enable severity assessment")
    
    # Context
    symptoms: Optional[str] = Field(None, description="Additional symptoms")
    medical_history: Optional[List[str]] = Field(None, description="Relevant medical history")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")


class ConditionDetectionResponse(BaseModel):
    """Response from condition detection."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Detection results
    detected_conditions: List[DetectedCondition] = Field(default_factory=list, description="Detected conditions")
    primary_condition: Optional[DetectedCondition] = Field(None, description="Primary detected condition")
    
    # Analysis
    differential_diagnosis: List[str] = Field(default_factory=list, description="Differential diagnosis")
    confidence_analysis: Dict[str, float] = Field(default_factory=dict, description="Confidence analysis")
    
    # Processing information
    processing_time: float = Field(..., description="Processing time")
    model_used: AnalysisModel = Field(..., description="Model used")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class MedicalQueryRequest(BaseModel):
    """Request for medical query processing."""
    
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="Medical query text")
    
    # Optional image
    image_data: Optional[bytes] = Field(None, description="Optional image data")
    image_format: Optional[str] = Field(None, description="Image format if provided")
    
    # Query context
    query_type: str = Field(..., description="Type of query (symptom, treatment, medication, etc.)")
    urgency_level: UrgencyLevel = Field(UrgencyLevel.NORMAL, description="Urgency level")
    
    # User context
    age: Optional[int] = Field(None, description="User age")
    gender: Optional[str] = Field(None, description="User gender")
    medical_history: Optional[List[str]] = Field(None, description="Medical history")
    current_medications: Optional[List[str]] = Field(None, description="Current medications")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")


class MedicalQueryResponse(BaseModel):
    """Response from medical query processing."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Query analysis
    query_analysis: str = Field(..., description="Analysis of the query")
    key_findings: List[str] = Field(default_factory=list, description="Key findings")
    
    # Medical information
    medical_information: str = Field(..., description="Medical information")
    relevant_conditions: List[str] = Field(default_factory=list, description="Relevant conditions")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    next_steps: List[str] = Field(default_factory=list, description="Next steps")
    
    # Resources
    resources: List[str] = Field(default_factory=list, description="Additional resources")
    references: List[str] = Field(default_factory=list, description="Medical references")
    
    # Processing information
    processing_time: float = Field(..., description="Processing time")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class MedicalInsightRequest(BaseModel):
    """Request for medical insights."""
    
    user_id: str = Field(..., description="User identifier")
    
    # Symptoms and conditions
    symptoms: List[str] = Field(default_factory=list, description="List of symptoms")
    conditions: List[str] = Field(default_factory=list, description="Known conditions")
    
    # Context
    age: Optional[int] = Field(None, description="User age")
    gender: Optional[str] = Field(None, description="User gender")
    medical_history: Optional[List[str]] = Field(None, description="Medical history")
    current_medications: Optional[List[str]] = Field(None, description="Current medications")
    
    # Analysis options
    include_treatment_options: bool = Field(True, description="Include treatment options")
    include_risk_assessment: bool = Field(True, description="Include risk assessment")
    include_literature_search: bool = Field(False, description="Include medical literature search")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")


class MedicalInsightResponse(BaseModel):
    """Response with medical insights."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Analysis results
    symptom_analysis: SymptomAnalysis = Field(..., description="Symptom analysis")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment")
    
    # Treatment information
    treatment_recommendations: List[TreatmentRecommendation] = Field(default_factory=list, description="Treatment recommendations")
    
    # Medical insights
    insights: List[str] = Field(default_factory=list, description="Medical insights")
    recommendations: List[str] = Field(default_factory=list, description="General recommendations")
    
    # Processing information
    processing_time: float = Field(..., description="Processing time")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class EmergencyAssessmentRequest(BaseModel):
    """Request for emergency assessment."""
    
    user_id: str = Field(..., description="User identifier")
    
    # Emergency details
    symptoms: str = Field(..., description="Description of symptoms")
    body_part: Optional[str] = Field(None, description="Affected body part")
    pain_level: int = Field(..., ge=1, le=10, description="Pain level (1-10)")
    duration: Optional[str] = Field(None, description="Duration of symptoms")
    
    # Optional image
    image_data: Optional[bytes] = Field(None, description="Optional image data")
    
    # Context
    age: Optional[int] = Field(None, description="User age")
    medical_history: Optional[List[str]] = Field(None, description="Medical history")
    current_medications: Optional[List[str]] = Field(None, description="Current medications")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")


class AnalysisHistoryResponse(BaseModel):
    """Response for analysis history."""
    
    id: str = Field(..., description="Analysis ID")
    user_id: str = Field(..., description="User identifier")
    
    # Analysis summary
    analysis_type: str = Field(..., description="Type of analysis")
    primary_condition: Optional[str] = Field(None, description="Primary detected condition")
    urgency_level: UrgencyLevel = Field(..., description="Urgency level")
    
    # Results summary
    confidence_score: float = Field(..., description="Confidence score")
    processing_time: float = Field(..., description="Processing time")
    
    # Timestamp
    timestamp: datetime = Field(..., description="Analysis timestamp") 