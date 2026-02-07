"""
Risk Assessment Agent
Advanced AI agent for assessing health risks and providing risk stratification.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import json
import numpy as np
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base_insight_agent import BaseInsightAgent, AgentResult, AgentStatus, AgentPriority
from ..models import (
    InsightDB, InsightType, InsightSeverity, InsightStatus, InsightCategory,
    InsightCreate, InsightResponse
)
from common.utils.logging import get_logger


class RiskAssessmentAgent(BaseInsightAgent):
    """Advanced AI agent for health risk assessment."""
    
    def __init__(self):
        super().__init__(
            agent_name="risk_assessment",
            priority=AgentPriority.HIGH
        )
        
        # Risk assessment models and algorithms
        self.risk_models = self._initialize_risk_models()
        self.risk_factors = self._load_risk_factors()
        self.risk_scores = self._load_risk_scores()
        self.intervention_rules = self._load_intervention_rules()
    
    def _get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return [
            "health_risk_assessment",
            "risk_stratification",
            "risk_factor_analysis",
            "predictive_risk_modeling",
            "intervention_recommendations",
            "risk_monitoring",
            "multi_risk_integration",
            "risk_trend_analysis"
        ]
    
    def _get_data_requirements(self) -> List[str]:
        """Get list of required data sources."""
        return [
            "patient_id",
            "demographics",
            "medical_history",
            "vital_signs",
            "lab_results",
            "medication_data",
            "lifestyle_data",
            "family_history"
        ]
    
    def _get_output_schema(self) -> Dict[str, Any]:
        """Get output schema for the agent."""
        return {
            "risks": [
                {
                    "risk_type": "string",
                    "risk_level": "string",
                    "risk_score": "float",
                    "probability": "float",
                    "severity": "string",
                    "timeframe": "string",
                    "risk_factors": "array",
                    "protective_factors": "array",
                    "interventions": "array"
                }
            ],
            "metadata": {
                "total_risks": "integer",
                "risks_by_level": "object",
                "overall_risk_score": "float",
                "assessment_timestamp": "string"
            }
        }
    
    async def execute(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """Execute risk assessment analysis."""
        self.start_time = datetime.utcnow()
        self.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"🚀 Starting risk assessment for patient {data.get('patient_id')}")
            
            # Preprocess data
            processed_data = await self.preprocess_data(data)
            
            # Assess various health risks
            risks = await self._assess_health_risks(processed_data)
            
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(risks)
            
            # Generate risk insights
            insights = await self._generate_risk_insights(risks, overall_risk, processed_data)
            
            # Save risks to database
            saved_risks = await self._save_risks(risks, data['patient_id'], db)
            
            # Update status
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            # Create result
            result = AgentResult(
                success=True,
                agent_name=self.agent_name,
                status=AgentStatus.COMPLETED,
                risks=risks,
                insights=insights,
                data={
                    'total_risks': len(risks),
                    'risks_by_level': self._count_by_level(risks),
                    'overall_risk_score': overall_risk,
                    'assessment_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Postprocess results
            result = await self.postprocess_results(result)
            
            self.logger.info(f"✅ Risk assessment completed: {len(risks)} risks assessed")
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.end_time = datetime.utcnow()
            
            self.logger.error(f"❌ Risk assessment failed: {str(e)}")
            
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
    
    def _initialize_risk_models(self) -> Dict[str, Any]:
        """Initialize risk assessment models."""
        return {
            "cardiovascular_risk": self._create_cardiovascular_risk_model(),
            "diabetes_risk": self._create_diabetes_risk_model(),
            "cancer_risk": self._create_cancer_risk_model(),
            "respiratory_risk": self._create_respiratory_risk_model(),
            "mental_health_risk": self._create_mental_health_risk_model()
        }
    
    def _create_cardiovascular_risk_model(self) -> Dict[str, Any]:
        """Create cardiovascular risk assessment model."""
        return {
            "type": "cardiovascular_risk",
            "algorithm": "framingham_risk_score",
            "parameters": {
                "age_weight": 0.3,
                "gender_weight": 0.2,
                "bp_weight": 0.25,
                "cholesterol_weight": 0.15,
                "smoking_weight": 0.1
            }
        }
    
    def _create_diabetes_risk_model(self) -> Dict[str, Any]:
        """Create diabetes risk assessment model."""
        return {
            "type": "diabetes_risk",
            "algorithm": "finrisk_score",
            "parameters": {
                "age_weight": 0.25,
                "bmi_weight": 0.3,
                "waist_circumference_weight": 0.2,
                "family_history_weight": 0.15,
                "physical_activity_weight": 0.1
            }
        }
    
    def _create_cancer_risk_model(self) -> Dict[str, Any]:
        """Create cancer risk assessment model."""
        return {
            "type": "cancer_risk",
            "algorithm": "gail_model",
            "parameters": {
                "age_weight": 0.3,
                "family_history_weight": 0.4,
                "lifestyle_weight": 0.2,
                "environmental_weight": 0.1
            }
        }
    
    def _create_respiratory_risk_model(self) -> Dict[str, Any]:
        """Create respiratory risk assessment model."""
        return {
            "type": "respiratory_risk",
            "algorithm": "copd_risk_score",
            "parameters": {
                "smoking_weight": 0.4,
                "age_weight": 0.2,
                "occupation_weight": 0.2,
                "symptoms_weight": 0.2
            }
        }
    
    def _create_mental_health_risk_model(self) -> Dict[str, Any]:
        """Create mental health risk assessment model."""
        return {
            "type": "mental_health_risk",
            "algorithm": "phq9_gad7",
            "parameters": {
                "symptoms_weight": 0.4,
                "stress_weight": 0.3,
                "social_support_weight": 0.2,
                "history_weight": 0.1
            }
        }
    
    def _load_risk_factors(self) -> Dict[str, Any]:
        """Load risk factors and their weights."""
        return {
            "demographic": {
                "age": {"weight": 0.3, "high_risk_threshold": 65},
                "gender": {"weight": 0.2, "high_risk_values": ["male"]},
                "ethnicity": {"weight": 0.1, "high_risk_values": ["african_american", "hispanic"]}
            },
            "medical": {
                "hypertension": {"weight": 0.4, "high_risk": True},
                "diabetes": {"weight": 0.4, "high_risk": True},
                "obesity": {"weight": 0.3, "high_risk_threshold": 30},
                "high_cholesterol": {"weight": 0.3, "high_risk": True}
            },
            "lifestyle": {
                "smoking": {"weight": 0.5, "high_risk": True},
                "alcohol": {"weight": 0.3, "high_risk_threshold": 14},
                "physical_inactivity": {"weight": 0.3, "high_risk": True},
                "poor_diet": {"weight": 0.2, "high_risk": True}
            },
            "family_history": {
                "cardiovascular_disease": {"weight": 0.4, "high_risk": True},
                "diabetes": {"weight": 0.3, "high_risk": True},
                "cancer": {"weight": 0.3, "high_risk": True}
            }
        }
    
    def _load_risk_scores(self) -> Dict[str, Any]:
        """Load risk scoring algorithms."""
        return {
            "low_risk": {"score_range": [0, 0.3], "color": "green"},
            "moderate_risk": {"score_range": [0.3, 0.6], "color": "yellow"},
            "high_risk": {"score_range": [0.6, 0.8], "color": "orange"},
            "very_high_risk": {"score_range": [0.8, 1.0], "color": "red"}
        }
    
    def _load_intervention_rules(self) -> Dict[str, Any]:
        """Load intervention rules based on risk levels."""
        return {
            "low_risk": {
                "monitoring_frequency": "annual",
                "interventions": ["preventive_care", "lifestyle_education"],
                "urgency": "low"
            },
            "moderate_risk": {
                "monitoring_frequency": "semi_annual",
                "interventions": ["lifestyle_modification", "medication_review"],
                "urgency": "medium"
            },
            "high_risk": {
                "monitoring_frequency": "quarterly",
                "interventions": ["medication_management", "specialist_referral"],
                "urgency": "high"
            },
            "very_high_risk": {
                "monitoring_frequency": "monthly",
                "interventions": ["immediate_intervention", "emergency_plan"],
                "urgency": "critical"
            }
        }
    
    async def _assess_health_risks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess various health risks."""
        risks = []
        
        # Assess cardiovascular risk
        cv_risk = await self._assess_cardiovascular_risk(data)
        if cv_risk:
            risks.append(cv_risk)
        
        # Assess diabetes risk
        diabetes_risk = await self._assess_diabetes_risk(data)
        if diabetes_risk:
            risks.append(diabetes_risk)
        
        # Assess cancer risk
        cancer_risk = await self._assess_cancer_risk(data)
        if cancer_risk:
            risks.append(cancer_risk)
        
        # Assess respiratory risk
        respiratory_risk = await self._assess_respiratory_risk(data)
        if respiratory_risk:
            risks.append(respiratory_risk)
        
        # Assess mental health risk
        mental_risk = await self._assess_mental_health_risk(data)
        if mental_risk:
            risks.append(mental_risk)
        
        return risks
    
    async def _assess_cardiovascular_risk(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess cardiovascular risk."""
        try:
            # Extract relevant data
            age = data.get('demographics', {}).get('age', 50)
            gender = data.get('demographics', {}).get('gender', 'unknown')
            bp_systolic = data.get('vital_signs', {}).get('blood_pressure_systolic', 120)
            bp_diastolic = data.get('vital_signs', {}).get('blood_pressure_diastolic', 80)
            cholesterol_total = data.get('lab_results', {}).get('total_cholesterol', 200)
            hdl = data.get('lab_results', {}).get('hdl_cholesterol', 50)
            smoking = data.get('lifestyle_data', {}).get('smoking_status', False)
            
            # Calculate risk score (simplified Framingham-like score)
            risk_score = 0.0
            
            # Age factor
            if age >= 65:
                risk_score += 0.3
            elif age >= 55:
                risk_score += 0.2
            elif age >= 45:
                risk_score += 0.1
            
            # Gender factor
            if gender == 'male':
                risk_score += 0.2
            
            # Blood pressure factor
            if bp_systolic >= 140 or bp_diastolic >= 90:
                risk_score += 0.25
            elif bp_systolic >= 130 or bp_diastolic >= 80:
                risk_score += 0.15
            
            # Cholesterol factor
            if cholesterol_total >= 240:
                risk_score += 0.15
            if hdl < 40:
                risk_score += 0.1
            
            # Smoking factor
            if smoking:
                risk_score += 0.1
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            risk_factors = []
            if age >= 65:
                risk_factors.append("advanced_age")
            if gender == 'male':
                risk_factors.append("male_gender")
            if bp_systolic >= 140 or bp_diastolic >= 90:
                risk_factors.append("hypertension")
            if cholesterol_total >= 240:
                risk_factors.append("high_cholesterol")
            if smoking:
                risk_factors.append("smoking")
            
            return {
                "risk_type": "cardiovascular_disease",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "probability": min(risk_score * 2, 0.95),
                "severity": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
                "timeframe": "10_years",
                "risk_factors": risk_factors,
                "protective_factors": [],
                "interventions": self._get_interventions(risk_level, "cardiovascular"),
                "confidence": 0.8
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing cardiovascular risk: {e}")
            return None
    
    async def _assess_diabetes_risk(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess diabetes risk."""
        try:
            # Extract relevant data
            age = data.get('demographics', {}).get('age', 50)
            bmi = data.get('vital_signs', {}).get('bmi', 25)
            waist_circumference = data.get('vital_signs', {}).get('waist_circumference', 90)
            family_history = data.get('family_history', {}).get('diabetes', False)
            physical_activity = data.get('lifestyle_data', {}).get('physical_activity_level', 'moderate')
            
            # Calculate risk score
            risk_score = 0.0
            
            # Age factor
            if age >= 65:
                risk_score += 0.25
            elif age >= 55:
                risk_score += 0.2
            elif age >= 45:
                risk_score += 0.15
            
            # BMI factor
            if bmi >= 30:
                risk_score += 0.3
            elif bmi >= 25:
                risk_score += 0.2
            
            # Waist circumference factor
            if waist_circumference >= 102:  # cm for men
                risk_score += 0.2
            
            # Family history factor
            if family_history:
                risk_score += 0.15
            
            # Physical activity factor
            if physical_activity == 'low':
                risk_score += 0.1
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            risk_factors = []
            if age >= 65:
                risk_factors.append("advanced_age")
            if bmi >= 30:
                risk_factors.append("obesity")
            if waist_circumference >= 102:
                risk_factors.append("central_obesity")
            if family_history:
                risk_factors.append("family_history")
            if physical_activity == 'low':
                risk_factors.append("physical_inactivity")
            
            return {
                "risk_type": "diabetes",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "probability": min(risk_score * 1.5, 0.9),
                "severity": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
                "timeframe": "5_years",
                "risk_factors": risk_factors,
                "protective_factors": [],
                "interventions": self._get_interventions(risk_level, "diabetes"),
                "confidence": 0.75
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing diabetes risk: {e}")
            return None
    
    async def _assess_cancer_risk(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess cancer risk."""
        try:
            # Extract relevant data
            age = data.get('demographics', {}).get('age', 50)
            gender = data.get('demographics', {}).get('gender', 'unknown')
            family_history = data.get('family_history', {}).get('cancer', False)
            smoking = data.get('lifestyle_data', {}).get('smoking_status', False)
            alcohol = data.get('lifestyle_data', {}).get('alcohol_consumption', 0)
            
            # Calculate risk score
            risk_score = 0.0
            
            # Age factor
            if age >= 65:
                risk_score += 0.3
            elif age >= 55:
                risk_score += 0.2
            elif age >= 45:
                risk_score += 0.1
            
            # Family history factor
            if family_history:
                risk_score += 0.4
            
            # Lifestyle factors
            if smoking:
                risk_score += 0.2
            if alcohol > 14:  # units per week
                risk_score += 0.1
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            risk_factors = []
            if age >= 65:
                risk_factors.append("advanced_age")
            if family_history:
                risk_factors.append("family_history")
            if smoking:
                risk_factors.append("smoking")
            if alcohol > 14:
                risk_factors.append("excessive_alcohol")
            
            return {
                "risk_type": "cancer",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "probability": min(risk_score * 1.2, 0.85),
                "severity": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
                "timeframe": "lifetime",
                "risk_factors": risk_factors,
                "protective_factors": [],
                "interventions": self._get_interventions(risk_level, "cancer"),
                "confidence": 0.7
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing cancer risk: {e}")
            return None
    
    async def _assess_respiratory_risk(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess respiratory risk."""
        try:
            # Extract relevant data
            age = data.get('demographics', {}).get('age', 50)
            smoking = data.get('lifestyle_data', {}).get('smoking_status', False)
            occupation = data.get('demographics', {}).get('occupation', 'unknown')
            symptoms = data.get('medical_history', {}).get('respiratory_symptoms', [])
            
            # Calculate risk score
            risk_score = 0.0
            
            # Age factor
            if age >= 65:
                risk_score += 0.2
            elif age >= 55:
                risk_score += 0.15
            
            # Smoking factor
            if smoking:
                risk_score += 0.4
            
            # Occupational factor
            if occupation in ['mining', 'construction', 'manufacturing']:
                risk_score += 0.2
            
            # Symptoms factor
            if symptoms:
                risk_score += 0.2
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            risk_factors = []
            if age >= 65:
                risk_factors.append("advanced_age")
            if smoking:
                risk_factors.append("smoking")
            if occupation in ['mining', 'construction', 'manufacturing']:
                risk_factors.append("occupational_exposure")
            if symptoms:
                risk_factors.append("respiratory_symptoms")
            
            return {
                "risk_type": "respiratory_disease",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "probability": min(risk_score * 1.8, 0.9),
                "severity": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
                "timeframe": "10_years",
                "risk_factors": risk_factors,
                "protective_factors": [],
                "interventions": self._get_interventions(risk_level, "respiratory"),
                "confidence": 0.75
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing respiratory risk: {e}")
            return None
    
    async def _assess_mental_health_risk(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess mental health risk."""
        try:
            # Extract relevant data
            symptoms = data.get('medical_history', {}).get('mental_health_symptoms', [])
            stress_level = data.get('lifestyle_data', {}).get('stress_level', 'moderate')
            social_support = data.get('lifestyle_data', {}).get('social_support', 'moderate')
            history = data.get('medical_history', {}).get('mental_health_history', False)
            
            # Calculate risk score
            risk_score = 0.0
            
            # Symptoms factor
            if symptoms:
                risk_score += 0.4
            
            # Stress factor
            if stress_level == 'high':
                risk_score += 0.3
            elif stress_level == 'moderate':
                risk_score += 0.15
            
            # Social support factor
            if social_support == 'low':
                risk_score += 0.2
            
            # History factor
            if history:
                risk_score += 0.1
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            risk_factors = []
            if symptoms:
                risk_factors.append("mental_health_symptoms")
            if stress_level == 'high':
                risk_factors.append("high_stress")
            if social_support == 'low':
                risk_factors.append("low_social_support")
            if history:
                risk_factors.append("mental_health_history")
            
            return {
                "risk_type": "mental_health",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "probability": min(risk_score * 2.0, 0.95),
                "severity": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
                "timeframe": "1_year",
                "risk_factors": risk_factors,
                "protective_factors": [],
                "interventions": self._get_interventions(risk_level, "mental_health"),
                "confidence": 0.7
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing mental health risk: {e}")
            return None
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score."""
        if risk_score >= 0.8:
            return "very_high_risk"
        elif risk_score >= 0.6:
            return "high_risk"
        elif risk_score >= 0.3:
            return "moderate_risk"
        else:
            return "low_risk"
    
    def _get_interventions(self, risk_level: str, risk_type: str) -> List[Dict[str, Any]]:
        """Get interventions based on risk level and type."""
        base_interventions = self.intervention_rules.get(risk_level, {})
        interventions = []
        
        # Add base interventions
        for intervention in base_interventions.get('interventions', []):
            interventions.append({
                "type": intervention,
                "priority": base_interventions.get('urgency', 'medium'),
                "timeframe": "immediate" if risk_level in ['high_risk', 'very_high_risk'] else "within_3_months"
            })
        
        # Add type-specific interventions
        type_interventions = {
            "cardiovascular": ["blood_pressure_monitoring", "cholesterol_management"],
            "diabetes": ["glucose_monitoring", "diet_management"],
            "cancer": ["screening_recommendations", "lifestyle_modification"],
            "respiratory": ["smoking_cessation", "pulmonary_function_testing"],
            "mental_health": ["counseling_referral", "stress_management"]
        }
        
        if risk_type in type_interventions:
            for intervention in type_interventions[risk_type]:
                interventions.append({
                    "type": intervention,
                    "priority": "medium",
                    "timeframe": "within_1_month"
                })
        
        return interventions
    
    def _calculate_overall_risk(self, risks: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score."""
        if not risks:
            return 0.0
        
        # Weight risks by severity and type
        weighted_scores = []
        for risk in risks:
            weight = 1.0
            if risk.get('severity') == 'high':
                weight = 1.5
            elif risk.get('severity') == 'medium':
                weight = 1.0
            else:
                weight = 0.5
            
            weighted_scores.append(risk.get('risk_score', 0.0) * weight)
        
        # Calculate average weighted score
        return sum(weighted_scores) / len(weighted_scores)
    
    async def _generate_risk_insights(self, risks: List[Dict[str, Any]], overall_risk: float, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from risk assessment."""
        insights = []
        
        # Generate overall risk insight
        overall_insight = await self._create_overall_risk_insight(risks, overall_risk, data)
        if overall_insight:
            insights.append(overall_insight)
        
        # Generate insights for high-risk conditions
        for risk in risks:
            if risk.get('risk_level') in ['high_risk', 'very_high_risk']:
                insight = await self._create_risk_insight(risk, data)
                if insight:
                    insights.append(insight)
        
        return insights
    
    async def _create_overall_risk_insight(self, risks: List[Dict[str, Any]], overall_risk: float, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create overall risk insight."""
        risk_level = self._determine_risk_level(overall_risk)
        
        # Count risks by level
        high_risks = len([r for r in risks if r.get('risk_level') in ['high_risk', 'very_high_risk']])
        moderate_risks = len([r for r in risks if r.get('risk_level') == 'moderate_risk'])
        
        title = f"Overall Health Risk Assessment"
        description = f"Patient has {len(risks)} identified health risks with an overall risk level of {risk_level.replace('_', ' ')}. "
        
        if high_risks > 0:
            description += f"There are {high_risks} high-risk conditions requiring immediate attention. "
        if moderate_risks > 0:
            description += f"There are {moderate_risks} moderate-risk conditions requiring monitoring. "
        
        description += "Regular health monitoring and preventive interventions are recommended."
        
        # Determine severity
        severity = InsightSeverity.HIGH if overall_risk > 0.6 else InsightSeverity.MEDIUM if overall_risk > 0.3 else InsightSeverity.LOW
        
        return {
            "insight_type": InsightType.RISK_ASSESSMENT,
            "category": InsightCategory.PREVENTIVE,
            "title": title,
            "description": description,
            "severity": severity,
            "confidence_score": 0.8,
            "relevance_score": min(overall_risk + 0.2, 1.0),
            "supporting_evidence": {
                "total_risks": len(risks),
                "overall_risk_score": overall_risk,
                "risk_breakdown": self._count_by_level(risks),
                "analysis_method": "comprehensive_risk_assessment"
            },
            "recommendations": self._get_overall_recommendations(risks, overall_risk)
        }
    
    async def _create_risk_insight(self, risk: Dict[str, Any], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create insight for a specific risk."""
        risk_type = risk.get('risk_type', '')
        risk_level = risk.get('risk_level', '')
        risk_score = risk.get('risk_score', 0.0)
        risk_factors = risk.get('risk_factors', [])
        
        title = f"{risk_type.replace('_', ' ').title()} Risk Assessment"
        description = f"Patient has a {risk_level.replace('_', ' ')} risk of {risk_type.replace('_', ' ')} "
        description += f"with a risk score of {risk_score:.2f}. "
        
        if risk_factors:
            description += f"Key risk factors include: {', '.join(risk_factors)}. "
        
        description += "Intervention and monitoring strategies should be implemented."
        
        # Determine severity
        severity = InsightSeverity.HIGH if risk_level in ['high_risk', 'very_high_risk'] else InsightSeverity.MEDIUM
        
        return {
            "insight_type": InsightType.RISK_ASSESSMENT,
            "category": InsightCategory.PREVENTIVE,
            "title": title,
            "description": description,
            "severity": severity,
            "confidence_score": risk.get('confidence', 0.7),
            "relevance_score": min(risk_score + 0.1, 1.0),
            "supporting_evidence": {
                "risk_data": risk,
                "analysis_method": "specialized_risk_assessment"
            },
            "recommendations": risk.get('interventions', [])
        }
    
    def _get_overall_recommendations(self, risks: List[Dict[str, Any]], overall_risk: float) -> List[Dict[str, Any]]:
        """Get overall recommendations based on all risks."""
        recommendations = []
        
        # Add general recommendations
        if overall_risk > 0.6:
            recommendations.append({
                "type": "urgent_intervention",
                "description": "Schedule immediate consultation with healthcare provider",
                "priority": "critical"
            })
        elif overall_risk > 0.3:
            recommendations.append({
                "type": "preventive_care",
                "description": "Schedule preventive health screening",
                "priority": "high"
            })
        
        # Add lifestyle recommendations
        recommendations.append({
            "type": "lifestyle_modification",
            "description": "Implement healthy lifestyle changes",
            "priority": "medium"
        })
        
        # Add monitoring recommendations
        recommendations.append({
            "type": "regular_monitoring",
            "description": "Establish regular health monitoring schedule",
            "priority": "medium"
        })
        
        return recommendations
    
    async def _save_risks(self, risks: List[Dict[str, Any]], patient_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """Save risks to database."""
        saved_risks = []
        
        for risk in risks:
            try:
                # Create insight record for significant risks
                if risk.get('risk_level') in ['high_risk', 'very_high_risk']:
                    insight_data = InsightCreate(
                        patient_id=patient_id,
                        insight_type=InsightType.RISK_ASSESSMENT,
                        category=InsightCategory.PREVENTIVE,
                        title=f"{risk.get('risk_type', '').replace('_', ' ').title()} Risk Assessment",
                        description=f"Risk assessment for {risk.get('risk_type', '')}: {risk.get('risk_level', '')} risk level",
                        severity=InsightSeverity.HIGH if risk.get('risk_level') == 'very_high_risk' else InsightSeverity.MEDIUM,
                        confidence_score=risk.get('confidence', 0.7),
                        relevance_score=min(risk.get('risk_score', 0.0) + 0.1, 1.0),
                        supporting_evidence=risk,
                        data_sources=["risk_assessment"]
                    )
                    
                    insight_db = InsightDB(**insight_data.dict())
                    db.add(insight_db)
                    await db.flush()
                    await db.refresh(insight_db)
                    
                    saved_risks.append(InsightResponse.from_orm(insight_db))
                
            except Exception as e:
                self.logger.error(f"❌ Error saving risk {risk.get('risk_type', '')}: {e}")
                continue
        
        await db.commit()
        return saved_risks
    
    def _count_by_level(self, risks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count risks by level."""
        counts = {}
        for risk in risks:
            level = risk.get('risk_level', 'unknown')
            counts[level] = counts.get(level, 0) + 1
        return counts 