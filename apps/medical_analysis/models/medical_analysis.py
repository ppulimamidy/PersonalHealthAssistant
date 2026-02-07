"""
Medical Analysis Models
Data models for comprehensive medical analysis.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """Types of medical analysis"""
    DIAGNOSIS = "diagnosis"
    PROGNOSIS = "prognosis"
    LITERATURE = "literature"
    TREATMENT = "treatment"
    COMPREHENSIVE = "comprehensive"


class ConfidenceLevel(str, Enum):
    """Confidence levels for medical analysis"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SeverityLevel(str, Enum):
    """Severity levels for medical conditions"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class MedicalDomain(str, Enum):
    """Medical domains for specialized analysis"""
    DERMATOLOGY = "dermatology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"
    RESPIRATORY = "respiratory"
    GENERAL = "general"


class Diagnosis(BaseModel):
    """Medical diagnosis model"""
    condition_name: str = Field(..., description="Name of the diagnosed condition")
    icd_code: Optional[str] = Field(None, description="ICD-10/11 code for the condition")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0-1)")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level category")
    differential_diagnoses: List[str] = Field(default_factory=list, description="List of differential diagnoses")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting evidence for diagnosis")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications or exclusions")
    severity: SeverityLevel = Field(..., description="Severity of the condition")
    urgency_level: int = Field(..., ge=1, le=5, description="Urgency level (1-5)")
    domain: MedicalDomain = Field(..., description="Medical domain")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Prognosis(BaseModel):
    """Medical prognosis model"""
    condition_name: str = Field(..., description="Name of the condition")
    prognosis_type: str = Field(..., description="Type of prognosis (short-term, long-term, etc.)")
    predicted_outcome: str = Field(..., description="Predicted outcome")
    time_frame: str = Field(..., description="Expected time frame")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0-1)")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level category")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors affecting prognosis")
    protective_factors: List[str] = Field(default_factory=list, description="Protective factors")
    progression_stages: List[str] = Field(default_factory=list, description="Expected progression stages")
    survival_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Survival rate if applicable")
    quality_of_life_impact: str = Field(..., description="Expected impact on quality of life")
    domain: MedicalDomain = Field(..., description="Medical domain")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LiteratureInsight(BaseModel):
    """Medical literature insight model"""
    topic: str = Field(..., description="Medical topic or condition")
    research_findings: List[str] = Field(default_factory=list, description="Key research findings")
    clinical_guidelines: List[str] = Field(default_factory=list, description="Relevant clinical guidelines")
    treatment_evidence: List[str] = Field(default_factory=list, description="Evidence-based treatment options")
    recent_studies: List[Dict[str, Any]] = Field(default_factory=list, description="Recent relevant studies")
    meta_analyses: List[Dict[str, Any]] = Field(default_factory=list, description="Meta-analysis results")
    expert_opinions: List[str] = Field(default_factory=list, description="Expert opinions and consensus")
    emerging_treatments: List[str] = Field(default_factory=list, description="Emerging treatment options")
    clinical_trials: List[Dict[str, Any]] = Field(default_factory=list, description="Ongoing clinical trials")
    domain: MedicalDomain = Field(..., description="Medical domain")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    evidence_level: str = Field(..., description="Level of evidence (A, B, C, etc.)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TreatmentRecommendation(BaseModel):
    """Treatment recommendation model"""
    condition_name: str = Field(..., description="Name of the condition")
    treatment_type: str = Field(..., description="Type of treatment (medication, surgery, lifestyle, etc.)")
    treatment_name: str = Field(..., description="Name of the treatment")
    description: str = Field(..., description="Description of the treatment")
    effectiveness: float = Field(..., ge=0.0, le=1.0, description="Effectiveness rating (0-1)")
    evidence_level: str = Field(..., description="Level of evidence")
    side_effects: List[str] = Field(default_factory=list, description="Potential side effects")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications")
    dosage_info: Optional[str] = Field(None, description="Dosage information if applicable")
    duration: Optional[str] = Field(None, description="Treatment duration")
    cost_estimate: Optional[str] = Field(None, description="Estimated cost")
    insurance_coverage: Optional[str] = Field(None, description="Insurance coverage information")
    alternative_treatments: List[str] = Field(default_factory=list, description="Alternative treatment options")
    domain: MedicalDomain = Field(..., description="Medical domain")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MedicalAnalysisRequest(BaseModel):
    """Request model for medical analysis"""
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    analysis_type: AnalysisType = Field(..., description="Type of analysis requested")
    symptoms: List[str] = Field(default_factory=list, description="Patient symptoms")
    medical_history: Dict[str, Any] = Field(default_factory=dict, description="Medical history")
    current_medications: List[str] = Field(default_factory=list, description="Current medications")
    vital_signs: Dict[str, Any] = Field(default_factory=dict, description="Vital signs")
    lab_results: Dict[str, Any] = Field(default_factory=dict, description="Laboratory results")
    imaging_results: Dict[str, Any] = Field(default_factory=dict, description="Imaging results")
    age: Optional[int] = Field(None, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")
    family_history: List[str] = Field(default_factory=list, description="Family medical history")
    lifestyle_factors: Dict[str, Any] = Field(default_factory=dict, description="Lifestyle factors")
    domain: Optional[MedicalDomain] = Field(None, description="Preferred medical domain")
    urgency_level: int = Field(default=1, ge=1, le=5, description="Urgency level (1-5)")


class MedicalAnalysisResult(BaseModel):
    """Result model for medical analysis"""
    analysis_id: UUID = Field(..., description="Analysis identifier")
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    domain: MedicalDomain = Field(..., description="Medical domain")
    
    # Analysis results
    diagnosis: Optional[Diagnosis] = Field(None, description="Diagnosis if applicable")
    prognosis: Optional[Prognosis] = Field(None, description="Prognosis if applicable")
    literature_insights: Optional[LiteratureInsight] = Field(None, description="Literature insights if applicable")
    treatment_recommendations: List[TreatmentRecommendation] = Field(default_factory=list, description="Treatment recommendations")
    
    # Metadata
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_used: str = Field(..., description="AI model used for analysis")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")
    disclaimers: List[str] = Field(default_factory=list, description="Medical disclaimers")
    recommendations: List[str] = Field(default_factory=list, description="General recommendations")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ComprehensiveMedicalReport(BaseModel):
    """Comprehensive medical report combining all analyses"""
    report_id: UUID = Field(..., description="Report identifier")
    patient_id: UUID = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Executive summary
    executive_summary: str = Field(..., description="Executive summary of findings")
    key_findings: List[str] = Field(default_factory=list, description="Key findings")
    critical_alerts: List[str] = Field(default_factory=list, description="Critical alerts")
    
    # Detailed analyses
    diagnosis_summary: Optional[Diagnosis] = Field(None, description="Primary diagnosis")
    prognosis_summary: Optional[Prognosis] = Field(None, description="Prognosis summary")
    literature_summary: Optional[LiteratureInsight] = Field(None, description="Literature summary")
    treatment_plan: List[TreatmentRecommendation] = Field(default_factory=list, description="Treatment plan")
    
    # Risk assessment
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    protective_factors: List[str] = Field(default_factory=list, description="Protective factors")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall risk score")
    
    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions required")
    short_term_goals: List[str] = Field(default_factory=list, description="Short-term goals")
    long_term_goals: List[str] = Field(default_factory=list, description="Long-term goals")
    monitoring_plan: List[str] = Field(default_factory=list, description="Monitoring plan")
    
    # Metadata
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Data quality score")
    model_versions: Dict[str, str] = Field(default_factory=dict, description="AI model versions used")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 