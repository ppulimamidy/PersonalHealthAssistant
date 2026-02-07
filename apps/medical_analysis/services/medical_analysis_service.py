"""
Medical Analysis Service
Main service for orchestrating comprehensive medical analysis.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from common.utils.logging import get_logger
from ..models.medical_analysis import (
    MedicalAnalysisRequest,
    MedicalAnalysisResult,
    ComprehensiveMedicalReport,
    AnalysisType,
    MedicalDomain
)
from .diagnosis_service import DiagnosisService
from .prognosis_service import PrognosisService
from .literature_service import LiteratureService

logger = get_logger(__name__)


class MedicalAnalysisService:
    """Main service for comprehensive medical analysis"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.diagnosis_service = DiagnosisService()
        self.prognosis_service = PrognosisService()
        self.literature_service = LiteratureService()
    
    async def analyze_medical_condition(
        self, 
        request: MedicalAnalysisRequest
    ) -> MedicalAnalysisResult:
        """
        Perform comprehensive medical analysis based on request type
        
        Args:
            request: Medical analysis request
            
        Returns:
            MedicalAnalysisResult with analysis
        """
        try:
            self.logger.info(f"Starting medical analysis for patient {request.patient_id}")
            
            if request.analysis_type == AnalysisType.DIAGNOSIS:
                return await self.diagnosis_service.analyze_diagnosis(request)
            elif request.analysis_type == AnalysisType.PROGNOSIS:
                return await self.prognosis_service.analyze_prognosis(request)
            elif request.analysis_type == AnalysisType.LITERATURE:
                return await self.literature_service.analyze_literature(request)
            elif request.analysis_type == AnalysisType.COMPREHENSIVE:
                return await self._perform_comprehensive_analysis(request)
            else:
                raise ValueError(f"Unsupported analysis type: {request.analysis_type}")
                
        except Exception as e:
            self.logger.error(f"Error in medical analysis: {str(e)}")
            raise
    
    async def _perform_comprehensive_analysis(
        self, 
        request: MedicalAnalysisRequest
    ) -> MedicalAnalysisResult:
        """Perform comprehensive analysis including diagnosis, prognosis, and literature"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting comprehensive analysis for patient {request.patient_id}")
            
            # Perform all analyses in parallel
            tasks = [
                self.diagnosis_service.analyze_diagnosis(request),
                self.prognosis_service.analyze_prognosis(request),
                self.literature_service.analyze_literature(request)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract results
            diagnosis_result = results[0] if not isinstance(results[0], Exception) else None
            prognosis_result = results[1] if not isinstance(results[1], Exception) else None
            literature_result = results[2] if not isinstance(results[2], Exception) else None
            
            # Determine domain
            domain = request.domain or self._detect_domain(request.symptoms)
            
            # Calculate overall confidence
            confidence_scores = []
            if diagnosis_result:
                confidence_scores.append(diagnosis_result.confidence_score)
            if prognosis_result:
                confidence_scores.append(prognosis_result.confidence_score)
            if literature_result:
                confidence_scores.append(literature_result.confidence_score)
            
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.COMPREHENSIVE,
                domain=domain,
                diagnosis=diagnosis_result.diagnosis if diagnosis_result else None,
                prognosis=prognosis_result.prognosis if prognosis_result else None,
                literature_insights=literature_result.literature_insights if literature_result else None,
                treatment_recommendations=[],
                confidence_score=overall_confidence,
                processing_time=processing_time,
                model_used="comprehensive_analysis",
                data_sources=["diagnosis", "prognosis", "literature"],
                disclaimers=[
                    "This comprehensive analysis combines multiple AI-powered assessments",
                    "All findings should be verified by healthcare professionals",
                    "Individual responses may vary significantly"
                ],
                recommendations=[
                    "Schedule comprehensive consultation with healthcare team",
                    "Review all analysis components with medical professionals",
                    "Consider second opinion for complex cases"
                ],
                next_steps=[
                    "Consult with primary care physician",
                    "Schedule specialist consultation if needed",
                    "Implement recommended monitoring and follow-up"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {str(e)}")
            processing_time = time.time() - start_time
            
            return MedicalAnalysisResult(
                analysis_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                analysis_type=AnalysisType.COMPREHENSIVE,
                domain=MedicalDomain.GENERAL,
                confidence_score=0.0,
                processing_time=processing_time,
                model_used="error",
                data_sources=[],
                disclaimers=["Comprehensive analysis failed - seek professional medical advice"],
                recommendations=["Contact healthcare provider immediately"],
                next_steps=["Seek immediate medical attention"]
            )
    
    async def generate_comprehensive_report(
        self, 
        request: MedicalAnalysisRequest
    ) -> ComprehensiveMedicalReport:
        """
        Generate comprehensive medical report
        
        Args:
            request: Medical analysis request
            
        Returns:
            ComprehensiveMedicalReport
        """
        try:
            self.logger.info(f"Generating comprehensive report for patient {request.patient_id}")
            
            # Perform comprehensive analysis
            analysis_result = await self._perform_comprehensive_analysis(request)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(analysis_result)
            
            # Extract key findings
            key_findings = self._extract_key_findings(analysis_result)
            
            # Identify critical alerts
            critical_alerts = self._identify_critical_alerts(analysis_result)
            
            # Generate risk assessment
            risk_factors, protective_factors, risk_score = self._assess_risks(analysis_result)
            
            # Generate recommendations
            immediate_actions, short_term_goals, long_term_goals, monitoring_plan = self._generate_recommendations(analysis_result)
            
            # Calculate data quality score
            data_quality_score = self._calculate_data_quality_score(request)
            
            return ComprehensiveMedicalReport(
                report_id=uuid4(),
                patient_id=request.patient_id,
                session_id=request.session_id,
                executive_summary=executive_summary,
                key_findings=key_findings,
                critical_alerts=critical_alerts,
                diagnosis_summary=analysis_result.diagnosis,
                prognosis_summary=analysis_result.prognosis,
                literature_summary=analysis_result.literature_insights,
                treatment_plan=analysis_result.treatment_recommendations,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                risk_score=risk_score,
                immediate_actions=immediate_actions,
                short_term_goals=short_term_goals,
                long_term_goals=long_term_goals,
                monitoring_plan=monitoring_plan,
                overall_confidence=analysis_result.confidence_score,
                data_quality_score=data_quality_score,
                model_versions={"comprehensive": "1.0.0"},
                data_sources=analysis_result.data_sources
            )
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {str(e)}")
            raise
    
    def _generate_executive_summary(self, analysis_result: MedicalAnalysisResult) -> str:
        """Generate executive summary from analysis results"""
        summary_parts = []
        
        if analysis_result.diagnosis:
            summary_parts.append(f"Primary diagnosis: {analysis_result.diagnosis.condition_name} (confidence: {analysis_result.diagnosis.confidence:.1%})")
        
        if analysis_result.prognosis:
            summary_parts.append(f"Prognosis: {analysis_result.prognosis.predicted_outcome}")
        
        if analysis_result.literature_insights:
            summary_parts.append(f"Literature relevance: {analysis_result.literature_insights.relevance_score:.1%}")
        
        summary_parts.append(f"Overall confidence: {analysis_result.confidence_score:.1%}")
        
        return ". ".join(summary_parts) if summary_parts else "Analysis completed with limited confidence."
    
    def _extract_key_findings(self, analysis_result: MedicalAnalysisResult) -> List[str]:
        """Extract key findings from analysis results"""
        findings = []
        
        if analysis_result.diagnosis:
            findings.append(f"Diagnosis: {analysis_result.diagnosis.condition_name}")
            findings.extend(analysis_result.diagnosis.supporting_evidence[:3])
        
        if analysis_result.prognosis:
            findings.append(f"Prognosis: {analysis_result.prognosis.predicted_outcome}")
            findings.extend(analysis_result.prognosis.risk_factors[:2])
        
        if analysis_result.literature_insights:
            findings.extend(analysis_result.literature_insights.research_findings[:2])
        
        return findings
    
    def _identify_critical_alerts(self, analysis_result: MedicalAnalysisResult) -> List[str]:
        """Identify critical alerts from analysis results"""
        alerts = []
        
        if analysis_result.diagnosis:
            if analysis_result.diagnosis.urgency_level >= 4:
                alerts.append(f"URGENT: {analysis_result.diagnosis.condition_name} requires immediate attention")
            if analysis_result.diagnosis.severity.value in ["severe", "critical"]:
                alerts.append(f"SEVERE: {analysis_result.diagnosis.condition_name} is {analysis_result.diagnosis.severity.value}")
        
        if analysis_result.prognosis:
            if analysis_result.prognosis.survival_rate and analysis_result.prognosis.survival_rate < 0.8:
                alerts.append(f"CONCERNING: Survival rate is {analysis_result.prognosis.survival_rate:.1%}")
        
        return alerts
    
    def _assess_risks(self, analysis_result: MedicalAnalysisResult) -> tuple:
        """Assess risk factors and protective factors"""
        risk_factors = []
        protective_factors = []
        risk_score = 0.5  # Default moderate risk
        
        if analysis_result.prognosis:
            risk_factors.extend(analysis_result.prognosis.risk_factors)
            protective_factors.extend(analysis_result.prognosis.protective_factors)
            
            # Adjust risk score based on prognosis
            if analysis_result.prognosis.survival_rate:
                risk_score = 1.0 - analysis_result.prognosis.survival_rate
        
        if analysis_result.diagnosis:
            if analysis_result.diagnosis.severity.value == "critical":
                risk_score = max(risk_score, 0.9)
            elif analysis_result.diagnosis.severity.value == "severe":
                risk_score = max(risk_score, 0.7)
        
        return risk_factors, protective_factors, risk_score
    
    def _generate_recommendations(self, analysis_result: MedicalAnalysisResult) -> tuple:
        """Generate recommendations from analysis results"""
        immediate_actions = []
        short_term_goals = []
        long_term_goals = []
        monitoring_plan = []
        
        # Immediate actions
        if analysis_result.diagnosis and analysis_result.diagnosis.urgency_level >= 4:
            immediate_actions.append("Seek immediate medical attention")
        immediate_actions.extend(analysis_result.recommendations[:2])
        
        # Short-term goals
        short_term_goals.append("Schedule follow-up with healthcare provider")
        if analysis_result.diagnosis:
            short_term_goals.append(f"Begin treatment for {analysis_result.diagnosis.condition_name}")
        
        # Long-term goals
        long_term_goals.append("Achieve optimal health outcomes")
        if analysis_result.prognosis:
            long_term_goals.append(f"Manage {analysis_result.prognosis.condition_name} progression")
        
        # Monitoring plan
        monitoring_plan.append("Regular follow-up appointments")
        monitoring_plan.append("Monitor symptoms and report changes")
        if analysis_result.diagnosis:
            monitoring_plan.append(f"Track {analysis_result.diagnosis.condition_name} progression")
        
        return immediate_actions, short_term_goals, long_term_goals, monitoring_plan
    
    def _calculate_data_quality_score(self, request: MedicalAnalysisRequest) -> float:
        """Calculate data quality score"""
        score = 0.0
        
        if request.symptoms:
            score += 0.3
        if request.medical_history:
            score += 0.2
        if request.vital_signs:
            score += 0.2
        if request.lab_results:
            score += 0.2
        if request.imaging_results:
            score += 0.1
        
        return min(score, 1.0)
    
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