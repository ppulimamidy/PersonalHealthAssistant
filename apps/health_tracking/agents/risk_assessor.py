"""
Risk Assessor Agent
Autonomous agent for assessing health risks and providing risk mitigation strategies.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
from dataclasses import dataclass

from .base_agent import BaseHealthAgent, AgentResult
from ..models.health_metrics import HealthMetric, MetricType
from ..models.vital_signs import VitalSigns, VitalSignType
from ..models.symptoms import Symptoms, SymptomSeverity
from common.utils.logging import get_logger

logger = get_logger(__name__)

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class RiskCategory(Enum):
    """Risk category enumeration"""
    CARDIOVASCULAR = "cardiovascular"
    METABOLIC = "metabolic"
    RESPIRATORY = "respiratory"
    LIFESTYLE = "lifestyle"
    MENTAL_HEALTH = "mental_health"
    INFECTIOUS = "infectious"
    CHRONIC_DISEASE = "chronic_disease"

@dataclass
class HealthRisk:
    """Health risk assessment result"""
    category: RiskCategory
    level: RiskLevel
    description: str
    factors: List[str]
    probability: float
    impact: str
    mitigation_strategies: List[str]
    urgency: str
    monitoring_frequency: str

class RiskAssessorAgent(BaseHealthAgent):
    """
    Autonomous agent for assessing health risks and providing mitigation strategies.
    Uses comprehensive health data to identify potential risks and recommend interventions.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="risk_assessor",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Risk assessment thresholds and criteria
        self.risk_thresholds = {
            RiskCategory.CARDIOVASCULAR: {
                "blood_pressure_systolic": {"high": 140, "very_high": 160, "critical": 180},
                "blood_pressure_diastolic": {"high": 90, "very_high": 100, "critical": 110},
                "heart_rate": {"high": 100, "very_high": 120, "critical": 140},
                "cholesterol": {"high": 200, "very_high": 240, "critical": 300}
            },
            RiskCategory.METABOLIC: {
                "blood_glucose": {"high": 140, "very_high": 200, "critical": 300},
                "bmi": {"high": 30, "very_high": 35, "critical": 40},
                "waist_circumference": {"high": 102, "very_high": 110, "critical": 120}
            },
            RiskCategory.RESPIRATORY: {
                "oxygen_saturation": {"low": 95, "very_low": 90, "critical": 85},
                "respiratory_rate": {"high": 20, "very_high": 25, "critical": 30}
            },
            RiskCategory.LIFESTYLE: {
                "steps": {"low": 5000, "very_low": 3000, "critical": 1000},
                "sleep_duration": {"low": 6, "very_low": 5, "critical": 4}
            }
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Assess health risks based on user data.
        
        Args:
            data: Dictionary containing user_id and optional parameters
            db: Database session
            
        Returns:
            AgentResult with risk assessment
        """
        user_id = data.get("user_id")
        assessment_period = data.get("assessment_period", 30)  # days
        include_symptoms = data.get("include_symptoms", True)
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Collect comprehensive health data
            health_data = await self._collect_health_data(user_id, assessment_period, include_symptoms, db)
            
            # Assess risks across different categories
            risk_assessment = await self._assess_health_risks(health_data)
            
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(risk_assessment)
            
            # Generate mitigation strategies
            mitigation_plan = self._generate_mitigation_plan(risk_assessment)
            
            # Generate insights and alerts
            insights = self._generate_risk_insights(risk_assessment, overall_risk)
            alerts = self._generate_risk_alerts(risk_assessment)
            recommendations = self._generate_risk_recommendations(risk_assessment, overall_risk)
            
            return AgentResult(
                success=True,
                data={
                    "risk_assessment": [risk.__dict__ for risk in risk_assessment],
                    "overall_risk": overall_risk,
                    "mitigation_plan": mitigation_plan,
                    "assessment_period_days": assessment_period,
                    "total_risks_identified": len(risk_assessment)
                },
                insights=insights,
                alerts=alerts,
                recommendations=recommendations,
                confidence=0.88
            )
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Risk assessment failed: {str(e)}"
            )
    
    async def _collect_health_data(
        self, 
        user_id: str, 
        assessment_period: int, 
        include_symptoms: bool, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Collect comprehensive health data for risk assessment"""
        start_date = datetime.utcnow() - timedelta(days=assessment_period)
        
        health_data = {
            "metrics": {},
            "vital_signs": {},
            "symptoms": [],
            "demographics": {},
            "lifestyle": {}
        }
        
        # Collect health metrics
        for metric_type in MetricType:
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.created_at >= start_date
                )
            ).order_by(desc(HealthMetric.created_at))
            
            result = await db.execute(query)
            metrics = result.scalars().all()
            
            if metrics:
                values = [m.value for m in metrics]
                health_data["metrics"][metric_type.value] = {
                    "latest": values[0] if values else None,
                    "average": sum(values) / len(values) if values else None,
                    "min": min(values) if values else None,
                    "max": max(values) if values else None,
                    "count": len(values),
                    "trend": self._calculate_trend(values)
                }
        
        # Collect vital signs
        for vital_type in VitalSignType:
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.user_id == user_id,
                    VitalSigns.vital_sign_type == vital_type.value,
                    VitalSigns.created_at >= start_date
                )
            ).order_by(desc(VitalSigns.created_at))
            
            result = await db.execute(query)
            vital_signs = result.scalars().all()
            
            if vital_signs:
                values = [self._get_vital_sign_value(vs, vital_type.value) for vs in vital_signs]
                values = [v for v in values if v is not None]
                
                if values:
                    health_data["vital_signs"][vital_type.value] = {
                        "latest": values[0] if values else None,
                        "average": sum(values) / len(values) if values else None,
                        "min": min(values) if values else None,
                        "max": max(values) if values else None,
                        "count": len(values),
                        "trend": self._calculate_trend(values)
                    }
        
        # Collect symptoms if requested
        if include_symptoms:
            query = select(Symptoms).where(
                and_(
                    Symptoms.user_id == user_id,
                    Symptoms.created_at >= start_date
                )
            ).order_by(desc(Symptoms.created_at))
            
            result = await db.execute(query)
            symptoms = result.scalars().all()
            
            health_data["symptoms"] = [
                {
                    "name": symptom.symptom_name,
                    "severity": symptom.severity,
                    "frequency": symptom.frequency,
                    "duration": symptom.duration,
                    "category": symptom.symptom_category,
                    "requires_medical_attention": symptom.requires_medical_attention
                }
                for symptom in symptoms
            ]
        
        return health_data
    
    async def _assess_health_risks(self, health_data: Dict[str, Any]) -> List[HealthRisk]:
        """Assess health risks across different categories"""
        risks = []
        
        # Assess cardiovascular risks
        cardiovascular_risks = self._assess_cardiovascular_risks(health_data)
        risks.extend(cardiovascular_risks)
        
        # Assess metabolic risks
        metabolic_risks = self._assess_metabolic_risks(health_data)
        risks.extend(metabolic_risks)
        
        # Assess respiratory risks
        respiratory_risks = self._assess_respiratory_risks(health_data)
        risks.extend(respiratory_risks)
        
        # Assess lifestyle risks
        lifestyle_risks = self._assess_lifestyle_risks(health_data)
        risks.extend(lifestyle_risks)
        
        # Assess symptom-based risks
        symptom_risks = self._assess_symptom_risks(health_data.get("symptoms", []))
        risks.extend(symptom_risks)
        
        return risks
    
    def _assess_cardiovascular_risks(self, health_data: Dict[str, Any]) -> List[HealthRisk]:
        """Assess cardiovascular health risks"""
        risks = []
        factors = []
        risk_level = RiskLevel.LOW
        probability = 0.1
        
        # Check blood pressure
        bp_systolic = health_data.get("vital_signs", {}).get("blood_pressure_systolic", {})
        bp_diastolic = health_data.get("vital_signs", {}).get("blood_pressure_diastolic", {})
        
        if bp_systolic.get("latest"):
            systolic = bp_systolic["latest"]
            if systolic >= 180:
                factors.append(f"Very high systolic blood pressure ({systolic} mmHg)")
                risk_level = RiskLevel.CRITICAL
                probability = 0.9
            elif systolic >= 160:
                factors.append(f"High systolic blood pressure ({systolic} mmHg)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.7)
            elif systolic >= 140:
                factors.append(f"Elevated systolic blood pressure ({systolic} mmHg)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.5)
        
        if bp_diastolic.get("latest"):
            diastolic = bp_diastolic["latest"]
            if diastolic >= 110:
                factors.append(f"Very high diastolic blood pressure ({diastolic} mmHg)")
                risk_level = RiskLevel.CRITICAL
                probability = 0.9
            elif diastolic >= 100:
                factors.append(f"High diastolic blood pressure ({diastolic} mmHg)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.7)
            elif diastolic >= 90:
                factors.append(f"Elevated diastolic blood pressure ({diastolic} mmHg)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.5)
        
        # Check heart rate
        heart_rate = health_data.get("vital_signs", {}).get("heart_rate", {})
        if heart_rate.get("latest"):
            hr = heart_rate["latest"]
            if hr >= 140:
                factors.append(f"Very high heart rate ({hr} bpm)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.6)
            elif hr >= 120:
                factors.append(f"Elevated heart rate ({hr} bpm)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.4)
        
        if factors:
            risks.append(HealthRisk(
                category=RiskCategory.CARDIOVASCULAR,
                level=risk_level,
                description="Cardiovascular health risks identified",
                factors=factors,
                probability=probability,
                impact="High - affects heart and blood vessel health",
                mitigation_strategies=self._get_cardiovascular_mitigation(factors),
                urgency="High" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Medium",
                monitoring_frequency="Daily" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Weekly"
            ))
        
        return risks
    
    def _assess_metabolic_risks(self, health_data: Dict[str, Any]) -> List[HealthRisk]:
        """Assess metabolic health risks"""
        risks = []
        factors = []
        risk_level = RiskLevel.LOW
        probability = 0.1
        
        # Check blood glucose
        blood_glucose = health_data.get("vital_signs", {}).get("blood_glucose", {})
        if blood_glucose.get("latest"):
            bg = blood_glucose["latest"]
            if bg >= 300:
                factors.append(f"Very high blood glucose ({bg} mg/dL)")
                risk_level = RiskLevel.CRITICAL
                probability = 0.9
            elif bg >= 200:
                factors.append(f"High blood glucose ({bg} mg/dL)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.7)
            elif bg >= 140:
                factors.append(f"Elevated blood glucose ({bg} mg/dL)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.5)
        
        # Check BMI
        weight = health_data.get("metrics", {}).get("weight", {})
        if weight.get("latest"):
            # Simplified BMI calculation (assuming average height)
            weight_kg = weight["latest"]
            bmi = weight_kg / (1.7 ** 2)  # Assuming 1.7m height
            
            if bmi >= 40:
                factors.append(f"Severe obesity (BMI: {bmi:.1f})")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.8)
            elif bmi >= 35:
                factors.append(f"Moderate obesity (BMI: {bmi:.1f})")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.6)
            elif bmi >= 30:
                factors.append(f"Obesity (BMI: {bmi:.1f})")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.4)
        
        if factors:
            risks.append(HealthRisk(
                category=RiskCategory.METABOLIC,
                level=risk_level,
                description="Metabolic health risks identified",
                factors=factors,
                probability=probability,
                impact="High - affects energy metabolism and organ function",
                mitigation_strategies=self._get_metabolic_mitigation(factors),
                urgency="High" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Medium",
                monitoring_frequency="Daily" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Weekly"
            ))
        
        return risks
    
    def _assess_respiratory_risks(self, health_data: Dict[str, Any]) -> List[HealthRisk]:
        """Assess respiratory health risks"""
        risks = []
        factors = []
        risk_level = RiskLevel.LOW
        probability = 0.1
        
        # Check oxygen saturation
        oxygen_sat = health_data.get("vital_signs", {}).get("oxygen_saturation", {})
        if oxygen_sat.get("latest"):
            o2 = oxygen_sat["latest"]
            if o2 <= 85:
                factors.append(f"Critical oxygen saturation ({o2}%)")
                risk_level = RiskLevel.CRITICAL
                probability = 0.9
            elif o2 <= 90:
                factors.append(f"Low oxygen saturation ({o2}%)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.7)
            elif o2 <= 95:
                factors.append(f"Below normal oxygen saturation ({o2}%)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.4)
        
        # Check respiratory rate
        resp_rate = health_data.get("vital_signs", {}).get("respiratory_rate", {})
        if resp_rate.get("latest"):
            rr = resp_rate["latest"]
            if rr >= 30:
                factors.append(f"Very high respiratory rate ({rr} breaths/min)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.6)
            elif rr >= 25:
                factors.append(f"Elevated respiratory rate ({rr} breaths/min)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.4)
        
        if factors:
            risks.append(HealthRisk(
                category=RiskCategory.RESPIRATORY,
                level=risk_level,
                description="Respiratory health risks identified",
                factors=factors,
                probability=probability,
                impact="High - affects oxygen delivery and breathing function",
                mitigation_strategies=self._get_respiratory_mitigation(factors),
                urgency="High" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Medium",
                monitoring_frequency="Daily" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Weekly"
            ))
        
        return risks
    
    def _assess_lifestyle_risks(self, health_data: Dict[str, Any]) -> List[HealthRisk]:
        """Assess lifestyle-related health risks"""
        risks = []
        factors = []
        risk_level = RiskLevel.LOW
        probability = 0.1
        
        # Check physical activity
        steps = health_data.get("metrics", {}).get("steps", {})
        if steps.get("latest"):
            step_count = steps["latest"]
            if step_count <= 1000:
                factors.append(f"Very low physical activity ({step_count} steps/day)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.6)
            elif step_count <= 3000:
                factors.append(f"Low physical activity ({step_count} steps/day)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.4)
        
        # Check sleep
        sleep = health_data.get("metrics", {}).get("sleep_duration", {})
        if sleep.get("latest"):
            sleep_hours = sleep["latest"]
            if sleep_hours <= 4:
                factors.append(f"Severe sleep deprivation ({sleep_hours} hours)")
                risk_level = max(risk_level, RiskLevel.HIGH)
                probability = max(probability, 0.7)
            elif sleep_hours <= 5:
                factors.append(f"Sleep deprivation ({sleep_hours} hours)")
                risk_level = max(risk_level, RiskLevel.MODERATE)
                probability = max(probability, 0.5)
        
        if factors:
            risks.append(HealthRisk(
                category=RiskCategory.LIFESTYLE,
                level=risk_level,
                description="Lifestyle health risks identified",
                factors=factors,
                probability=probability,
                impact="Medium - affects overall health and well-being",
                mitigation_strategies=self._get_lifestyle_mitigation(factors),
                urgency="Medium" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Low",
                monitoring_frequency="Weekly" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "Monthly"
            ))
        
        return risks
    
    def _assess_symptom_risks(self, symptoms: List[Dict[str, Any]]) -> List[HealthRisk]:
        """Assess risks based on reported symptoms"""
        risks = []
        
        if not symptoms:
            return risks
        
        # Group symptoms by severity
        severe_symptoms = [s for s in symptoms if s.get("severity") == SymptomSeverity.SEVERE.value]
        moderate_symptoms = [s for s in symptoms if s.get("severity") == SymptomSeverity.MODERATE.value]
        
        if severe_symptoms:
            factors = [f"Severe {s['name']}" for s in severe_symptoms[:3]]
            risks.append(HealthRisk(
                category=RiskCategory.CHRONIC_DISEASE,
                level=RiskLevel.HIGH,
                description="Severe symptoms requiring medical attention",
                factors=factors,
                probability=0.8,
                impact="High - requires immediate medical evaluation",
                mitigation_strategies=["Seek immediate medical attention", "Follow up with healthcare provider"],
                urgency="High",
                monitoring_frequency="Daily"
            ))
        
        if moderate_symptoms:
            factors = [f"Moderate {s['name']}" for s in moderate_symptoms[:3]]
            risks.append(HealthRisk(
                category=RiskCategory.CHRONIC_DISEASE,
                level=RiskLevel.MODERATE,
                description="Moderate symptoms requiring monitoring",
                factors=factors,
                probability=0.5,
                impact="Medium - requires monitoring and potential intervention",
                mitigation_strategies=["Monitor symptoms", "Consider lifestyle changes", "Consult healthcare provider if persistent"],
                urgency="Medium",
                monitoring_frequency="Weekly"
            ))
        
        return risks
    
    def _calculate_overall_risk(self, risk_assessment: List[HealthRisk]) -> Dict[str, Any]:
        """Calculate overall risk score and level"""
        if not risk_assessment:
            return {
                "level": RiskLevel.LOW.value,
                "score": 0,
                "description": "No significant health risks identified"
            }
        
        # Calculate weighted risk score
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        total_score = sum(risk_scores[risk.level] * risk.probability for risk in risk_assessment)
        average_score = total_score / len(risk_assessment)
        
        # Determine overall risk level
        if average_score >= 3.5:
            overall_level = RiskLevel.CRITICAL
        elif average_score >= 2.5:
            overall_level = RiskLevel.HIGH
        elif average_score >= 1.5:
            overall_level = RiskLevel.MODERATE
        else:
            overall_level = RiskLevel.LOW
        
        return {
            "level": overall_level.value,
            "score": round(average_score, 2),
            "description": f"Overall health risk level: {overall_level.value}",
            "risk_count": len(risk_assessment),
            "critical_risks": len([r for r in risk_assessment if r.level == RiskLevel.CRITICAL]),
            "high_risks": len([r for r in risk_assessment if r.level == RiskLevel.HIGH])
        }
    
    def _generate_mitigation_plan(self, risk_assessment: List[HealthRisk]) -> Dict[str, Any]:
        """Generate comprehensive risk mitigation plan"""
        mitigation_plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_strategies": [],
            "monitoring_plan": {},
            "healthcare_recommendations": []
        }
        
        # Prioritize risks by level
        critical_risks = [r for r in risk_assessment if r.level == RiskLevel.CRITICAL]
        high_risks = [r for r in risk_assessment if r.level == RiskLevel.HIGH]
        moderate_risks = [r for r in risk_assessment if r.level == RiskLevel.MODERATE]
        
        # Immediate actions for critical risks
        for risk in critical_risks:
            mitigation_plan["immediate_actions"].extend(risk.mitigation_strategies[:2])
            mitigation_plan["healthcare_recommendations"].append(f"Consult healthcare provider for {risk.category.value}")
        
        # Short-term goals for high risks
        for risk in high_risks:
            mitigation_plan["short_term_goals"].extend(risk.mitigation_strategies[:3])
        
        # Long-term strategies for all risks
        for risk in risk_assessment:
            mitigation_plan["long_term_strategies"].extend(risk.mitigation_strategies[3:])
        
        # Create monitoring plan
        for risk in risk_assessment:
            category = risk.category.value
            if category not in mitigation_plan["monitoring_plan"]:
                mitigation_plan["monitoring_plan"][category] = []
            mitigation_plan["monitoring_plan"][category].append({
                "frequency": risk.monitoring_frequency,
                "focus": ", ".join(risk.factors[:2])
            })
        
        # Remove duplicates
        mitigation_plan["immediate_actions"] = list(set(mitigation_plan["immediate_actions"]))
        mitigation_plan["short_term_goals"] = list(set(mitigation_plan["short_term_goals"]))
        mitigation_plan["long_term_strategies"] = list(set(mitigation_plan["long_term_strategies"]))
        mitigation_plan["healthcare_recommendations"] = list(set(mitigation_plan["healthcare_recommendations"]))
        
        return mitigation_plan
    
    def _get_cardiovascular_mitigation(self, factors: List[str]) -> List[str]:
        """Get cardiovascular risk mitigation strategies"""
        strategies = [
            "Monitor blood pressure regularly",
            "Reduce sodium intake",
            "Increase physical activity",
            "Manage stress through relaxation techniques",
            "Maintain healthy weight",
            "Limit alcohol consumption",
            "Quit smoking if applicable",
            "Follow DASH diet principles"
        ]
        
        if any("systolic" in factor for factor in factors):
            strategies.extend([
                "Consider blood pressure medication if prescribed",
                "Practice deep breathing exercises"
            ])
        
        if any("heart rate" in factor for factor in factors):
            strategies.extend([
                "Practice cardiovascular exercise",
                "Monitor heart rate during activities"
            ])
        
        return strategies
    
    def _get_metabolic_mitigation(self, factors: List[str]) -> List[str]:
        """Get metabolic risk mitigation strategies"""
        strategies = [
            "Follow a balanced diet",
            "Monitor blood glucose regularly",
            "Increase physical activity",
            "Maintain healthy weight",
            "Limit refined carbohydrates",
            "Include fiber-rich foods",
            "Stay hydrated"
        ]
        
        if any("glucose" in factor for factor in factors):
            strategies.extend([
                "Consider diabetes management plan",
                "Monitor carbohydrate intake",
                "Exercise regularly to improve insulin sensitivity"
            ])
        
        if any("obesity" in factor or "BMI" in factor for factor in factors):
            strategies.extend([
                "Create calorie deficit through diet and exercise",
                "Set realistic weight loss goals",
                "Consider working with a nutritionist"
            ])
        
        return strategies
    
    def _get_respiratory_mitigation(self, factors: List[str]) -> List[str]:
        """Get respiratory risk mitigation strategies"""
        strategies = [
            "Practice deep breathing exercises",
            "Avoid smoking and secondhand smoke",
            "Maintain good posture",
            "Exercise regularly to improve lung capacity",
            "Monitor respiratory symptoms"
        ]
        
        if any("oxygen" in factor for factor in factors):
            strategies.extend([
                "Consider oxygen therapy if prescribed",
                "Avoid high altitudes",
                "Monitor oxygen levels during activities"
            ])
        
        return strategies
    
    def _get_lifestyle_mitigation(self, factors: List[str]) -> List[str]:
        """Get lifestyle risk mitigation strategies"""
        strategies = [
            "Set realistic health goals",
            "Create daily routines",
            "Track progress regularly",
            "Find enjoyable physical activities",
            "Establish healthy sleep habits"
        ]
        
        if any("activity" in factor or "steps" in factor for factor in factors):
            strategies.extend([
                "Start with 10-minute walks",
                "Use a pedometer or fitness tracker",
                "Find activities you enjoy",
                "Gradually increase activity level"
            ])
        
        if any("sleep" in factor for factor in factors):
            strategies.extend([
                "Establish consistent bedtime routine",
                "Create a sleep-friendly environment",
                "Limit screen time before bed",
                "Avoid caffeine in the evening"
            ])
        
        return strategies
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if change_percent > 5:
            return "worsening"
        elif change_percent < -5:
            return "improving"
        else:
            return "stable"
    
    def _get_vital_sign_value(self, vital_sign: VitalSigns, vital_type: str) -> Optional[float]:
        """Get the relevant value for a vital sign type"""
        value_mapping = {
            VitalSignType.BLOOD_PRESSURE_SYSTOLIC.value: vital_sign.systolic,
            VitalSignType.BLOOD_PRESSURE_DIASTOLIC.value: vital_sign.diastolic,
            VitalSignType.HEART_RATE.value: vital_sign.heart_rate,
            VitalSignType.BODY_TEMPERATURE.value: vital_sign.temperature,
            VitalSignType.OXYGEN_SATURATION.value: vital_sign.oxygen_saturation,
            VitalSignType.RESPIRATORY_RATE.value: vital_sign.respiratory_rate,
            VitalSignType.BLOOD_GLUCOSE.value: vital_sign.blood_glucose,
        }
        
        return value_mapping.get(vital_type)
    
    def _generate_risk_insights(self, risk_assessment: List[HealthRisk], overall_risk: Dict[str, Any]) -> List[str]:
        """Generate insights from risk assessment"""
        insights = []
        
        overall_level = overall_risk.get("level", "low")
        risk_count = overall_risk.get("risk_count", 0)
        
        if risk_count == 0:
            insights.append("No significant health risks identified in your current data.")
            return insights
        
        insights.append(f"Identified {risk_count} health risk areas requiring attention.")
        
        if overall_level == "critical":
            insights.append("Critical health risks detected - immediate action required.")
        elif overall_level == "high":
            insights.append("High health risks identified - prompt intervention recommended.")
        elif overall_level == "moderate":
            insights.append("Moderate health risks found - proactive management advised.")
        
        # Category-specific insights
        categories = [risk.category.value for risk in risk_assessment]
        if RiskCategory.CARDIOVASCULAR.value in categories:
            insights.append("Cardiovascular health requires attention.")
        if RiskCategory.METABOLIC.value in categories:
            insights.append("Metabolic health needs monitoring and management.")
        
        return insights
    
    def _generate_risk_alerts(self, risk_assessment: List[HealthRisk]) -> List[str]:
        """Generate alerts for concerning risks"""
        alerts = []
        
        for risk in risk_assessment:
            if risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                if risk.urgency == "High":
                    alerts.append(f"🚨 {risk.description} - {', '.join(risk.factors[:2])}")
                else:
                    alerts.append(f"⚠️ {risk.description} - {', '.join(risk.factors[:2])}")
        
        return alerts
    
    def _generate_risk_recommendations(self, risk_assessment: List[HealthRisk], overall_risk: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on risk assessment"""
        recommendations = []
        
        overall_level = overall_risk.get("level", "low")
        
        if overall_level == "critical":
            recommendations.append("Seek immediate medical attention for critical health risks.")
            recommendations.append("Follow up with healthcare provider within 24-48 hours.")
        elif overall_level == "high":
            recommendations.append("Schedule appointment with healthcare provider within 1 week.")
            recommendations.append("Implement immediate lifestyle changes to reduce risks.")
        elif overall_level == "moderate":
            recommendations.append("Consider consulting healthcare provider for guidance.")
            recommendations.append("Focus on preventive measures and lifestyle improvements.")
        
        # General recommendations
        if risk_assessment:
            recommendations.append("Monitor your health metrics regularly to track improvements.")
            recommendations.append("Set specific, achievable goals for risk reduction.")
        
        return recommendations 