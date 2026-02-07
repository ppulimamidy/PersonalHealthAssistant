"""
Lab Result Analyzer Agent
Analyzes laboratory test results for trends, anomalies, and clinical significance.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import joinedload

from .base_agent import BaseMedicalAgent, AgentResult
# from ..models.lab_results_db import LabResultDB  # Commented out for testing
from ..utils.event_streaming import MedicalRecordsEventProducer


class LabTestCategory(str, Enum):
    """Categories of laboratory tests."""
    HEMATOLOGY = "hematology"
    CHEMISTRY = "chemistry"
    LIPID = "lipid"
    THYROID = "thyroid"
    DIABETES = "diabetes"
    CARDIAC = "cardiac"
    LIVER = "liver"
    KIDNEY = "kidney"
    INFECTIOUS_DISEASE = "infectious_disease"
    IMMUNOLOGY = "immunology"
    OTHER = "other"


class TrendDirection(str, Enum):
    """Trend direction for lab values."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"


class AnomalySeverity(str, Enum):
    """Severity levels for lab anomalies."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class LabTrend:
    """Lab result trend analysis."""
    test_name: str
    test_code: str
    direction: TrendDirection
    change_percentage: float
    time_period_days: int
    data_points: int
    confidence: float
    clinical_significance: str


@dataclass
class LabAnomaly:
    """Lab result anomaly detection."""
    test_name: str
    test_code: str
    current_value: float
    unit: str
    reference_range: str
    deviation_percentage: float
    severity: AnomalySeverity
    clinical_implication: str
    recommended_action: str


@dataclass
class LabAnalysis:
    """Complete lab result analysis."""
    patient_id: UUID
    analysis_date: datetime
    trends: List[LabTrend]
    anomalies: List[LabAnomaly]
    critical_values: List[LabAnomaly]
    recommendations: List[str]
    risk_factors: List[str]
    follow_up_tests: List[str]
    overall_health_score: float


class LabResultAnalyzerAgent(BaseMedicalAgent):
    """Agent for analyzing laboratory test results."""
    
    def __init__(self):
        super().__init__("LabResultAnalyzerAgent")
        self.event_producer = MedicalRecordsEventProducer()
        
        # Lab test categorization patterns
        self.test_patterns = {
            LabTestCategory.HEMATOLOGY: [
                r'\b(cbc|complete blood count|hemoglobin|hgb|hct|hematocrit|wbc|white blood cell|rbc|red blood cell|platelet|pt|inr|aptt|ptt)\b',
                r'\b(hemoglobin|hematocrit|mcv|mch|mchc|rdw|mpv|pct|pdw)\b'
            ],
            LabTestCategory.CHEMISTRY: [
                r'\b(chemistry|cmp|bmp|glucose|creatinine|bun|sodium|potassium|chloride|co2|bicarbonate|calcium|magnesium|phosphorus)\b',
                r'\b(glucose|creatinine|bun|sodium|potassium|chloride|co2|calcium|magnesium|phosphorus)\b'
            ],
            LabTestCategory.LIPID: [
                r'\b(lipid|cholesterol|triglyceride|hdl|ldl|vldl|apolipoprotein|lipoprotein)\b',
                r'\b(total cholesterol|hdl cholesterol|ldl cholesterol|triglycerides|apoa|apob)\b'
            ],
            LabTestCategory.THYROID: [
                r'\b(thyroid|tsh|t3|t4|free t4|free t3|thyroxine|triiodothyronine|thyroglobulin|thyroid antibodies)\b',
                r'\b(tsh|t3|t4|free t4|free t3|thyroglobulin|tpo|trab)\b'
            ],
            LabTestCategory.DIABETES: [
                r'\b(diabetes|a1c|hba1c|glucose|insulin|c peptide|ketone|microalbumin)\b',
                r'\b(a1c|hba1c|glucose|insulin|c peptide|ketone|microalbumin|urine glucose)\b'
            ],
            LabTestCategory.CARDIAC: [
                r'\b(cardiac|troponin|ck|cpk|ckmb|bnp|nt pro bnp|creatine kinase|myoglobin)\b',
                r'\b(troponin|ck|cpk|ckmb|bnp|nt pro bnp|myoglobin|ldh|ast|alt)\b'
            ],
            LabTestCategory.LIVER: [
                r'\b(liver|alt|ast|alp|ggt|bilirubin|albumin|protein|pt|inr|ammonia)\b',
                r'\b(alt|ast|alp|ggt|bilirubin|albumin|protein|pt|inr|ammonia)\b'
            ],
            LabTestCategory.KIDNEY: [
                r'\b(kidney|creatinine|bun|egfr|cystatin c|urinalysis|protein|albumin|creatinine clearance)\b',
                r'\b(creatinine|bun|egfr|cystatin c|urinalysis|protein|albumin|creatinine clearance)\b'
            ]
        }
        
        # Critical value thresholds
        self.critical_thresholds = {
            "glucose": {"low": 40, "high": 600},
            "sodium": {"low": 120, "high": 160},
            "potassium": {"low": 2.5, "high": 6.5},
            "calcium": {"low": 6.0, "high": 13.0},
            "hemoglobin": {"low": 6.0, "high": 22.0},
            "platelet": {"low": 20000, "high": 1000000},
            "troponin": {"low": 0, "high": 50},
            "creatinine": {"low": 0.1, "high": 10.0}
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Analyze laboratory test results for trends and anomalies.
        
        Args:
            data: Dictionary containing lab result information
            db: Database session
            
        Returns:
            AgentResult: Analysis result with trends, anomalies, and recommendations
        """
        patient_id = data.get("patient_id")
        lab_result_id = data.get("lab_result_id")
        analysis_period_days = data.get("analysis_period_days", 90)
        
        if not patient_id:
            return AgentResult(
                success=False,
                error="patient_id is required"
            )
        
        try:
            # Get recent lab results for the patient
            lab_results = await self._get_patient_lab_results(db, patient_id, analysis_period_days)
            
            if not lab_results:
                return AgentResult(
                    success=False,
                    error=f"No lab results found for patient {patient_id} in the last {analysis_period_days} days"
                )
            
            # Analyze trends
            trends = await self._analyze_trends(lab_results)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(lab_results)
            
            # Identify critical values
            critical_values = await self._identify_critical_values(lab_results)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(trends, anomalies, critical_values)
            
            # Identify risk factors
            risk_factors = await self._identify_risk_factors(trends, anomalies)
            
            # Suggest follow-up tests
            follow_up_tests = await self._suggest_follow_up_tests(trends, anomalies)
            
            # Calculate overall health score
            health_score = await self._calculate_health_score(trends, anomalies, critical_values)
            
            # Create analysis summary
            analysis = LabAnalysis(
                patient_id=UUID(patient_id),
                analysis_date=datetime.utcnow(),
                trends=trends,
                anomalies=anomalies,
                critical_values=critical_values,
                recommendations=recommendations,
                risk_factors=risk_factors,
                follow_up_tests=follow_up_tests,
                overall_health_score=health_score
            )
            
            # Update lab result with analysis
            if lab_result_id:
                await self._update_lab_result_analysis(db, lab_result_id, analysis)
            
            # Publish analysis event to Kafka
            await self._publish_lab_analysis_event(analysis)
            
            # Generate insights
            insights = self._generate_insights(analysis)
            
            return AgentResult(
                success=True,
                data={
                    "patient_id": str(patient_id),
                    "analysis_date": analysis.analysis_date.isoformat(),
                    "trends": [self._trend_to_dict(trend) for trend in trends],
                    "anomalies": [self._anomaly_to_dict(anomaly) for anomaly in anomalies],
                    "critical_values": [self._anomaly_to_dict(cv) for cv in critical_values],
                    "recommendations": recommendations,
                    "risk_factors": risk_factors,
                    "follow_up_tests": follow_up_tests,
                    "overall_health_score": health_score,
                    "analysis_period_days": analysis_period_days
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.85
            )
            
        except Exception as e:
            self.logger.error(f"Lab result analysis failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Lab result analysis failed: {str(e)}"
            )
    
    async def _get_patient_lab_results(self, db: AsyncSession, patient_id: str, days: int) -> List["LabResultDB"]:
        """Get recent lab results for a patient."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await db.execute(
                select(LabResultDB)
                .where(
                    and_(
                        LabResultDB.patient_id == UUID(patient_id),
                        LabResultDB.test_date >= cutoff_date
                    )
                )
                .order_by(desc(LabResultDB.test_date))
            )
            
            return result.scalars().all()
            
        except Exception as e:
            self.logger.error(f"Error fetching lab results: {e}")
            return []
    
    async def _analyze_trends(self, lab_results: List["LabResultDB"]) -> List["LabTrend"]:
        """Analyze trends in lab results."""
        trends = []
        
        # Group results by test name
        test_groups = {}
        for result in lab_results:
            if result.test_name not in test_groups:
                test_groups[result.test_name] = []
            test_groups[result.test_name].append(result)
        
        # Analyze trends for each test
        for test_name, results in test_groups.items():
            if len(results) < 2:
                continue  # Need at least 2 data points for trend analysis
            
            # Sort by date
            results.sort(key=lambda x: x.test_date)
            
            # Calculate trend
            trend = self._calculate_trend(test_name, results)
            if trend:
                trends.append(trend)
        
        return trends
    
    def _calculate_trend(self, test_name: str, results: List["LabResultDB"]) -> Optional["LabTrend"]:
        """Calculate trend for a specific test."""
        if len(results) < 2:
            return None
        
        try:
            # Extract numeric values
            values = []
            dates = []
            for result in results:
                if result.value is not None:
                    values.append(float(result.value))
                    dates.append(result.test_date)
            
            if len(values) < 2:
                return None
            
            # Calculate trend direction and percentage change
            first_value = values[0]
            last_value = values[-1]
            time_period = (dates[-1] - dates[0]).days
            
            if time_period == 0:
                return None
            
            # Calculate percentage change
            if first_value != 0:
                change_percentage = ((last_value - first_value) / first_value) * 100
            else:
                change_percentage = 0
            
            # Determine trend direction
            if change_percentage > 10:
                direction = TrendDirection.INCREASING
            elif change_percentage < -10:
                direction = TrendDirection.DECREASING
            elif abs(change_percentage) <= 5:
                direction = TrendDirection.STABLE
            else:
                direction = TrendDirection.FLUCTUATING
            
            # Calculate confidence based on data points and consistency
            confidence = min(0.95, 0.5 + (len(values) * 0.1))
            
            # Determine clinical significance
            clinical_significance = self._assess_trend_significance(test_name, direction, change_percentage)
            
            return LabTrend(
                test_name=test_name,
                test_code=results[0].test_code or "",
                direction=direction,
                change_percentage=round(change_percentage, 2),
                time_period_days=time_period,
                data_points=len(values),
                confidence=round(confidence, 2),
                clinical_significance=clinical_significance
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating trend for {test_name}: {e}")
            return None
    
    def _assess_trend_significance(self, test_name: str, direction: TrendDirection, change_percentage: float) -> str:
        """Assess clinical significance of a trend."""
        test_lower = test_name.lower()
        
        # Define significant changes for different tests
        significant_changes = {
            "glucose": 20,
            "creatinine": 25,
            "hemoglobin": 15,
            "platelet": 30,
            "sodium": 10,
            "potassium": 15,
            "calcium": 10
        }
        
        threshold = significant_changes.get(test_lower, 20)
        
        if abs(change_percentage) >= threshold:
            if direction == TrendDirection.INCREASING:
                return f"Significant increase in {test_name} - requires attention"
            elif direction == TrendDirection.DECREASING:
                return f"Significant decrease in {test_name} - requires attention"
            else:
                return f"Significant fluctuation in {test_name} - monitor closely"
        else:
            return f"Stable trend in {test_name} - continue monitoring"
    
    async def _detect_anomalies(self, lab_results: List["LabResultDB"]) -> List["LabAnomaly"]:
        """Detect anomalies in lab results."""
        anomalies = []
        
        for result in lab_results:
            if result.value is None or not result.abnormal:
                continue
            
            try:
                value = float(result.value)
                
                # Calculate deviation from reference range
                deviation = self._calculate_deviation(result)
                
                # Determine severity
                severity = self._determine_anomaly_severity(result, deviation)
                
                # Get clinical implications
                clinical_implication = self._get_clinical_implication(result, severity)
                
                # Generate recommended action
                recommended_action = self._get_recommended_action(result, severity)
                
                anomaly = LabAnomaly(
                    test_name=result.test_name,
                    test_code=result.test_code or "",
                    current_value=value,
                    unit=result.unit or "",
                    reference_range=result.reference_range_text or "",
                    deviation_percentage=deviation,
                    severity=severity,
                    clinical_implication=clinical_implication,
                    recommended_action=recommended_action
                )
                
                anomalies.append(anomaly)
                
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Error processing anomaly for {result.test_name}: {e}")
                continue
        
        return anomalies
    
    def _calculate_deviation(self, result: "LabResultDB") -> float:
        """Calculate deviation percentage from reference range."""
        try:
            value = float(result.value)
            
            # Parse reference range
            if result.reference_range_low is not None and result.reference_range_high is not None:
                low = float(result.reference_range_low)
                high = float(result.reference_range_high)
                mid = (low + high) / 2
                
                if value > high:
                    return ((value - high) / high) * 100
                elif value < low:
                    return ((low - value) / low) * 100
                else:
                    return 0
            else:
                # Use text reference range if available
                ref_text = result.reference_range_text or ""
                if "high" in ref_text.lower() and value > 0:
                    return 50  # Estimate 50% high
                elif "low" in ref_text.lower() and value > 0:
                    return 50  # Estimate 50% low
                else:
                    return 0
                    
        except (ValueError, TypeError):
            return 0
    
    def _determine_anomaly_severity(self, result: "LabResultDB", deviation: float) -> AnomalySeverity:
        """Determine severity of an anomaly."""
        if result.critical:
            return AnomalySeverity.CRITICAL
        
        if deviation >= 100:
            return AnomalySeverity.SEVERE
        elif deviation >= 50:
            return AnomalySeverity.MODERATE
        else:
            return AnomalySeverity.MILD
    
    def _get_clinical_implication(self, result: "LabResultDB", severity: AnomalySeverity) -> str:
        """Get clinical implications of an anomaly."""
        test_lower = result.test_name.lower()
        
        implications = {
            "glucose": {
                AnomalySeverity.MILD: "Slightly elevated glucose - monitor diet and exercise",
                AnomalySeverity.MODERATE: "Moderately elevated glucose - consider diabetes evaluation",
                AnomalySeverity.SEVERE: "Severely elevated glucose - immediate medical attention required",
                AnomalySeverity.CRITICAL: "Critical glucose level - emergency intervention needed"
            },
            "creatinine": {
                AnomalySeverity.MILD: "Slightly elevated creatinine - monitor kidney function",
                AnomalySeverity.MODERATE: "Moderately elevated creatinine - kidney function impairment",
                AnomalySeverity.SEVERE: "Severely elevated creatinine - significant kidney dysfunction",
                AnomalySeverity.CRITICAL: "Critical creatinine level - renal failure possible"
            },
            "hemoglobin": {
                AnomalySeverity.MILD: "Slightly low hemoglobin - monitor for anemia",
                AnomalySeverity.MODERATE: "Moderately low hemoglobin - anemia likely",
                AnomalySeverity.SEVERE: "Severely low hemoglobin - significant anemia",
                AnomalySeverity.CRITICAL: "Critical hemoglobin level - transfusion may be needed"
            }
        }
        
        # Find matching test pattern
        for test_pattern, test_implications in implications.items():
            if test_pattern in test_lower:
                return test_implications.get(severity, f"{severity.value} abnormality in {result.test_name}")
        
        return f"{severity.value} abnormality in {result.test_name} - clinical correlation recommended"
    
    def _get_recommended_action(self, result: "LabResultDB", severity: AnomalySeverity) -> str:
        """Get recommended action for an anomaly."""
        if severity == AnomalySeverity.CRITICAL:
            return "Immediate medical attention required - contact healthcare provider"
        elif severity == AnomalySeverity.SEVERE:
            return "Urgent follow-up with healthcare provider within 24-48 hours"
        elif severity == AnomalySeverity.MODERATE:
            return "Schedule follow-up with healthcare provider within 1 week"
        else:
            return "Monitor and repeat test as recommended by healthcare provider"
    
    async def _identify_critical_values(self, lab_results: List["LabResultDB"]) -> List["LabAnomaly"]:
        """Identify critical lab values."""
        critical_values = []
        
        for result in lab_results:
            if result.value is None:
                continue
            
            try:
                value = float(result.value)
                test_lower = result.test_name.lower()
                
                # Check against critical thresholds
                for test_pattern, thresholds in self.critical_thresholds.items():
                    if test_pattern in test_lower:
                        if value <= thresholds["low"] or value >= thresholds["high"]:
                            critical_values.append(LabAnomaly(
                                test_name=result.test_name,
                                test_code=result.test_code or "",
                                current_value=value,
                                unit=result.unit or "",
                                reference_range=result.reference_range_text or "",
                                deviation_percentage=100,
                                severity=AnomalySeverity.CRITICAL,
                                clinical_implication=f"Critical {result.test_name} value - immediate attention required",
                                recommended_action="EMERGENCY - Contact healthcare provider immediately"
                            ))
                        break
                
            except (ValueError, TypeError):
                continue
        
        return critical_values
    
    async def _generate_recommendations(self, trends: List["LabTrend"], anomalies: List["LabAnomaly"], critical_values: List["LabAnomaly"]) -> List[str]:
        """Generate clinical recommendations based on analysis."""
        recommendations = []
        
        # Critical value recommendations
        if critical_values:
            recommendations.append("Critical lab values detected - immediate medical attention required")
        
        # Severe anomaly recommendations
        severe_anomalies = [a for a in anomalies if a.severity in [AnomalySeverity.SEVERE, AnomalySeverity.CRITICAL]]
        if severe_anomalies:
            recommendations.append(f"Multiple severe abnormalities detected - urgent follow-up recommended")
        
        # Trend-based recommendations
        for trend in trends:
            if trend.direction == TrendDirection.INCREASING and trend.change_percentage > 20:
                recommendations.append(f"Significant increase in {trend.test_name} - consider intervention")
            elif trend.direction == TrendDirection.DECREASING and trend.change_percentage < -20:
                recommendations.append(f"Significant decrease in {trend.test_name} - investigate cause")
        
        # General recommendations
        if len(anomalies) > 5:
            recommendations.append("Multiple lab abnormalities - comprehensive evaluation recommended")
        
        if not recommendations:
            recommendations.append("Lab results within normal limits - continue routine monitoring")
        
        return recommendations
    
    async def _identify_risk_factors(self, trends: List["LabTrend"], anomalies: List["LabAnomaly"]) -> List[str]:
        """Identify risk factors based on lab analysis."""
        risk_factors = []
        
        # Check for diabetes risk
        glucose_anomalies = [a for a in anomalies if "glucose" in a.test_name.lower()]
        if glucose_anomalies:
            risk_factors.append("Elevated glucose levels - diabetes risk")
        
        # Check for kidney disease risk
        creatinine_anomalies = [a for a in anomalies if "creatinine" in a.test_name.lower()]
        if creatinine_anomalies:
            risk_factors.append("Elevated creatinine - kidney disease risk")
        
        # Check for anemia risk
        hemoglobin_anomalies = [a for a in anomalies if "hemoglobin" in a.test_name.lower()]
        if hemoglobin_anomalies:
            risk_factors.append("Low hemoglobin - anemia risk")
        
        # Check for cardiovascular risk
        lipid_anomalies = [a for a in anomalies if any(lipid in a.test_name.lower() for lipid in ["cholesterol", "triglyceride", "hdl", "ldl"])]
        if lipid_anomalies:
            risk_factors.append("Abnormal lipid profile - cardiovascular risk")
        
        return risk_factors
    
    async def _suggest_follow_up_tests(self, trends: List["LabTrend"], anomalies: List["LabAnomaly"]) -> List[str]:
        """Suggest follow-up tests based on analysis."""
        follow_up_tests = []
        
        # Diabetes-related follow-ups
        glucose_anomalies = [a for a in anomalies if "glucose" in a.test_name.lower()]
        if glucose_anomalies:
            follow_up_tests.extend(["HbA1c", "Fasting glucose", "Oral glucose tolerance test"])
        
        # Kidney-related follow-ups
        creatinine_anomalies = [a for a in anomalies if "creatinine" in a.test_name.lower()]
        if creatinine_anomalies:
            follow_up_tests.extend(["eGFR", "Urinalysis", "24-hour urine collection"])
        
        # Anemia-related follow-ups
        hemoglobin_anomalies = [a for a in anomalies if "hemoglobin" in a.test_name.lower()]
        if hemoglobin_anomalies:
            follow_up_tests.extend(["Iron studies", "B12", "Folate", "Reticulocyte count"])
        
        # Cardiovascular follow-ups
        lipid_anomalies = [a for a in anomalies if any(lipid in a.test_name.lower() for lipid in ["cholesterol", "triglyceride"])]
        if lipid_anomalies:
            follow_up_tests.extend(["Lipid panel", "Cardiac markers", "EKG"])
        
        return list(set(follow_up_tests))  # Remove duplicates
    
    async def _calculate_health_score(self, trends: List["LabTrend"], anomalies: List["LabAnomaly"], critical_values: List["LabAnomaly"]) -> float:
        """Calculate overall health score based on lab analysis."""
        base_score = 100.0
        
        # Deduct points for critical values
        base_score -= len(critical_values) * 20
        
        # Deduct points for severe anomalies
        severe_anomalies = [a for a in anomalies if a.severity in [AnomalySeverity.SEVERE, AnomalySeverity.CRITICAL]]
        base_score -= len(severe_anomalies) * 10
        
        # Deduct points for moderate anomalies
        moderate_anomalies = [a for a in anomalies if a.severity == AnomalySeverity.MODERATE]
        base_score -= len(moderate_anomalies) * 5
        
        # Deduct points for mild anomalies
        mild_anomalies = [a for a in anomalies if a.severity == AnomalySeverity.MILD]
        base_score -= len(mild_anomalies) * 2
        
        # Deduct points for concerning trends
        concerning_trends = [t for t in trends if t.direction in [TrendDirection.INCREASING, TrendDirection.DECREASING] and abs(t.change_percentage) > 20]
        base_score -= len(concerning_trends) * 3
        
        return max(0.0, min(100.0, base_score))
    
    async def _update_lab_result_analysis(self, db: AsyncSession, lab_result_id: str, analysis: LabAnalysis):
        """Update lab result with analysis metadata."""
        try:
            # This would update the lab result with analysis metadata
            # Implementation depends on your database schema
            pass
        except Exception as e:
            self.logger.error(f"Error updating lab result analysis: {e}")
    
    async def _publish_lab_analysis_event(self, analysis: LabAnalysis):
        """Publish lab analysis event to Kafka."""
        try:
            event = {
                "event_type": "lab_analysis_completed",
                "timestamp": datetime.utcnow().isoformat(),
                "patient_id": str(analysis.patient_id),
                "analysis_date": analysis.analysis_date.isoformat(),
                "trends_count": len(analysis.trends),
                "anomalies_count": len(analysis.anomalies),
                "critical_values_count": len(analysis.critical_values),
                "health_score": analysis.overall_health_score,
                "risk_factors": analysis.risk_factors,
                "recommendations": analysis.recommendations,
                "source": "LabResultAnalyzerAgent"
            }
            
            await self.event_producer.publish_lab_result_event(event)
            self.logger.info(f"📤 Published lab analysis event for patient {analysis.patient_id}")
            
        except Exception as e:
            self.logger.error(f"Error publishing lab analysis event: {e}")
    
    def _trend_to_dict(self, trend: "LabTrend") -> Dict[str, Any]:
        """Convert LabTrend to dictionary."""
        return {
            "test_name": trend.test_name,
            "test_code": trend.test_code,
            "direction": trend.direction.value,
            "change_percentage": trend.change_percentage,
            "time_period_days": trend.time_period_days,
            "data_points": trend.data_points,
            "confidence": trend.confidence,
            "clinical_significance": trend.clinical_significance
        }
    
    def _anomaly_to_dict(self, anomaly: "LabAnomaly") -> Dict[str, Any]:
        """Convert LabAnomaly to dictionary."""
        return {
            "test_name": anomaly.test_name,
            "test_code": anomaly.test_code,
            "current_value": anomaly.current_value,
            "unit": anomaly.unit,
            "reference_range": anomaly.reference_range,
            "deviation_percentage": anomaly.deviation_percentage,
            "severity": anomaly.severity.value,
            "clinical_implication": anomaly.clinical_implication,
            "recommended_action": anomaly.recommended_action
        }
    
    def _generate_insights(self, analysis: LabAnalysis) -> List[str]:
        """Generate insights from lab analysis."""
        insights = []
        
        if analysis.trends:
            insights.append(f"Analyzed {len(analysis.trends)} lab trends over time")
        
        if analysis.anomalies:
            insights.append(f"Detected {len(analysis.anomalies)} lab abnormalities")
        
        if analysis.critical_values:
            insights.append(f"Identified {len(analysis.critical_values)} critical lab values requiring immediate attention")
        
        if analysis.risk_factors:
            insights.append(f"Identified {len(analysis.risk_factors)} health risk factors")
        
        insights.append(f"Overall health score: {analysis.overall_health_score:.1f}/100")
        
        return insights 