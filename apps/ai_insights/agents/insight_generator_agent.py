"""
Insight Generator Agent
Advanced AI agent for generating health insights from various data sources.
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
from ..models.insight_models import (
    InsightDB, InsightType, InsightSeverity, InsightStatus, InsightCategory,
    InsightCreate, InsightResponse
)
from common.utils.logging import get_logger


class InsightGeneratorAgent(BaseInsightAgent):
    """Advanced AI agent for generating health insights."""
    
    def __init__(self):
        super().__init__(
            agent_name="insight_generator",
            priority=AgentPriority.HIGH
        )
        
        # AI models and algorithms
        self.insight_models = self._initialize_models()
        self.pattern_detectors = self._initialize_pattern_detectors()
        self.correlation_analyzers = self._initialize_correlation_analyzers()
        
        # Insight templates and rules
        self.insight_templates = self._load_insight_templates()
        self.severity_rules = self._load_severity_rules()
        self.category_mappings = self._load_category_mappings()
    
    def _get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return [
            "health_data_analysis",
            "pattern_recognition",
            "trend_identification",
            "anomaly_detection",
            "correlation_analysis",
            "insight_generation",
            "severity_assessment",
            "category_classification",
            "confidence_scoring",
            "multi_source_integration"
        ]
    
    def _get_data_requirements(self) -> List[str]:
        """Get list of required data sources."""
        return [
            "patient_id",
            "health_metrics",
            "vital_signs",
            "lab_results",
            "medication_data",
            "lifestyle_data",
            "medical_history"
        ]
    
    def _get_output_schema(self) -> Dict[str, Any]:
        """Get output schema for the agent."""
        return {
            "insights": [
                {
                    "insight_type": "string",
                    "category": "string",
                    "title": "string",
                    "description": "string",
                    "severity": "string",
                    "confidence_score": "float",
                    "relevance_score": "float",
                    "supporting_evidence": "object",
                    "recommendations": "array"
                }
            ],
            "metadata": {
                "total_insights": "integer",
                "insights_by_category": "object",
                "insights_by_severity": "object",
                "average_confidence": "float",
                "generation_timestamp": "string"
            }
        }
    
    async def execute(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Execute insight generation analysis.
        
        Args:
            data: Input health data
            db: Database session
            
        Returns:
            AgentResult: Generated insights
        """
        self.start_time = datetime.utcnow()
        self.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"🚀 Starting insight generation for patient {data.get('patient_id')}")
            
            # Preprocess data
            processed_data = await self.preprocess_data(data)
            
            # Generate insights using multiple approaches
            insights = await self._generate_insights(processed_data, db)
            
            # Analyze and categorize insights
            categorized_insights = self._categorize_insights(insights)
            
            # Calculate severity and confidence scores
            scored_insights = await self._score_insights(categorized_insights, processed_data)
            
            # Filter and rank insights
            ranked_insights = self._rank_insights(scored_insights)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(ranked_insights, processed_data)
            
            # Save insights to database
            saved_insights = await self._save_insights(ranked_insights, data['patient_id'], db)
            
            # Update status
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            # Create result
            result = AgentResult(
                success=True,
                agent_name=self.agent_name,
                status=AgentStatus.COMPLETED,
                insights=ranked_insights,
                recommendations=recommendations,
                data={
                    'total_insights': len(ranked_insights),
                    'insights_by_category': self._count_by_category(ranked_insights),
                    'insights_by_severity': self._count_by_severity(ranked_insights),
                    'average_confidence': self._calculate_average_confidence(ranked_insights),
                    'generation_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Postprocess results
            result = await self.postprocess_results(result)
            
            self.logger.info(f"✅ Insight generation completed: {len(ranked_insights)} insights generated")
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.end_time = datetime.utcnow()
            
            self.logger.error(f"❌ Insight generation failed: {str(e)}")
            
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
    
    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize AI models for insight generation."""
        return {
            "trend_analyzer": self._create_trend_analyzer(),
            "pattern_detector": self._create_pattern_detector(),
            "anomaly_detector": self._create_anomaly_detector(),
            "correlation_analyzer": self._create_correlation_analyzer(),
            "risk_assessor": self._create_risk_assessor()
        }
    
    def _create_trend_analyzer(self) -> Dict[str, Any]:
        """Create trend analysis model."""
        return {
            "type": "statistical_trend",
            "algorithms": ["linear_regression", "moving_average", "seasonal_decomposition"],
            "parameters": {
                "window_size": 7,
                "confidence_level": 0.95,
                "min_data_points": 5
            }
        }
    
    def _create_pattern_detector(self) -> Dict[str, Any]:
        """Create pattern detection model."""
        return {
            "type": "pattern_recognition",
            "algorithms": ["fourier_analysis", "wavelet_analysis", "clustering"],
            "parameters": {
                "pattern_types": ["cyclic", "seasonal", "trending", "irregular"],
                "min_pattern_length": 3,
                "similarity_threshold": 0.8
            }
        }
    
    def _create_anomaly_detector(self) -> Dict[str, Any]:
        """Create anomaly detection model."""
        return {
            "type": "anomaly_detection",
            "algorithms": ["isolation_forest", "one_class_svm", "statistical_outlier"],
            "parameters": {
                "contamination": 0.1,
                "threshold": 2.0,
                "window_size": 10
            }
        }
    
    def _create_correlation_analyzer(self) -> Dict[str, Any]:
        """Create correlation analysis model."""
        return {
            "type": "correlation_analysis",
            "algorithms": ["pearson", "spearman", "kendall"],
            "parameters": {
                "min_correlation": 0.3,
                "significance_level": 0.05,
                "lag_analysis": True
            }
        }
    
    def _create_risk_assessor(self) -> Dict[str, Any]:
        """Create risk assessment model."""
        return {
            "type": "risk_assessment",
            "algorithms": ["logistic_regression", "random_forest", "gradient_boosting"],
            "parameters": {
                "risk_thresholds": {
                    "low": 0.3,
                    "medium": 0.6,
                    "high": 0.8
                },
                "prediction_horizon": 30  # days
            }
        }
    
    def _initialize_pattern_detectors(self) -> Dict[str, Any]:
        """Initialize pattern detection algorithms."""
        return {
            "vital_signs": self._create_vital_signs_detector(),
            "lab_results": self._create_lab_results_detector(),
            "medication": self._create_medication_detector(),
            "lifestyle": self._create_lifestyle_detector()
        }
    
    def _create_vital_signs_detector(self) -> Dict[str, Any]:
        """Create vital signs pattern detector."""
        return {
            "metrics": ["heart_rate", "blood_pressure", "temperature", "respiratory_rate", "oxygen_saturation"],
            "patterns": ["trending_up", "trending_down", "volatile", "stable", "abnormal_range"],
            "thresholds": {
                "heart_rate": {"low": 60, "high": 100},
                "systolic_bp": {"low": 90, "high": 140},
                "diastolic_bp": {"low": 60, "high": 90},
                "temperature": {"low": 97.0, "high": 99.5},
                "respiratory_rate": {"low": 12, "high": 20},
                "oxygen_saturation": {"low": 95, "high": 100}
            }
        }
    
    def _create_lab_results_detector(self) -> Dict[str, Any]:
        """Create lab results pattern detector."""
        return {
            "categories": ["metabolic", "cardiac", "renal", "liver", "hematology", "inflammation"],
            "patterns": ["elevated", "decreased", "trending", "stable", "critical"],
            "critical_values": {
                "glucose": {"low": 70, "high": 200},
                "creatinine": {"high": 1.2},
                "troponin": {"high": 0.04},
                "hemoglobin": {"low": 12, "high": 16}
            }
        }
    
    def _create_medication_detector(self) -> Dict[str, Any]:
        """Create medication pattern detector."""
        return {
            "patterns": ["adherence", "interactions", "side_effects", "effectiveness", "dosage_changes"],
            "adherence_threshold": 0.8,
            "interaction_severity": ["mild", "moderate", "severe", "contraindicated"]
        }
    
    def _create_lifestyle_detector(self) -> Dict[str, Any]:
        """Create lifestyle pattern detector."""
        return {
            "categories": ["exercise", "nutrition", "sleep", "stress", "social"],
            "patterns": ["improving", "declining", "stable", "irregular", "optimal"],
            "optimal_ranges": {
                "exercise_minutes": {"min": 150, "max": 300},
                "sleep_hours": {"min": 7, "max": 9},
                "stress_level": {"min": 1, "max": 5}
            }
        }
    
    def _initialize_correlation_analyzers(self) -> Dict[str, Any]:
        """Initialize correlation analysis algorithms."""
        return {
            "vital_signs_correlations": self._create_vital_signs_correlations(),
            "lifestyle_health_correlations": self._create_lifestyle_health_correlations(),
            "medication_effectiveness": self._create_medication_effectiveness_correlations()
        }
    
    def _create_vital_signs_correlations(self) -> Dict[str, Any]:
        """Create vital signs correlation analyzer."""
        return {
            "pairs": [
                ("heart_rate", "blood_pressure"),
                ("respiratory_rate", "oxygen_saturation"),
                ("temperature", "heart_rate"),
                ("blood_pressure", "stress_level")
            ],
            "threshold": 0.5,
            "lag_analysis": True
        }
    
    def _create_lifestyle_health_correlations(self) -> Dict[str, Any]:
        """Create lifestyle-health correlation analyzer."""
        return {
            "pairs": [
                ("exercise", "heart_rate"),
                ("sleep", "stress_level"),
                ("nutrition", "energy_level"),
                ("stress", "blood_pressure")
            ],
            "threshold": 0.3,
            "lag_days": 7
        }
    
    def _create_medication_effectiveness_correlations(self) -> Dict[str, Any]:
        """Create medication effectiveness correlation analyzer."""
        return {
            "metrics": ["symptom_improvement", "side_effects", "adherence"],
            "threshold": 0.4,
            "time_window": 30  # days
        }
    
    def _load_insight_templates(self) -> Dict[str, Any]:
        """Load insight generation templates."""
        return {
            "trend_analysis": {
                "improving": "Your {metric} has been {trend} over the past {period}, indicating {interpretation}.",
                "declining": "Your {metric} has been {trend} over the past {period}, which may indicate {interpretation}.",
                "stable": "Your {metric} has remained {trend} over the past {period}, which is {interpretation}."
            },
            "pattern_detection": {
                "cyclic": "We've detected a {pattern_type} pattern in your {metric} with a {frequency} cycle.",
                "seasonal": "Your {metric} shows {pattern_type} variations that follow {seasonal_pattern}.",
                "irregular": "Your {metric} shows {pattern_type} patterns that may require attention."
            },
            "anomaly_detection": {
                "high": "Your {metric} is currently {anomaly_type} compared to your usual range.",
                "low": "Your {metric} is currently {anomaly_type} compared to your usual range.",
                "critical": "Your {metric} has reached a {anomaly_type} level that requires immediate attention."
            },
            "correlation": {
                "positive": "We've found a {strength} positive correlation between {metric1} and {metric2}.",
                "negative": "We've found a {strength} negative correlation between {metric1} and {metric2}.",
                "causal": "Changes in {metric1} appear to {relationship} {metric2}."
            }
        }
    
    def _load_severity_rules(self) -> Dict[str, Any]:
        """Load severity assessment rules."""
        return {
            "critical": {
                "conditions": ["life_threatening", "immediate_attention", "severe_anomaly"],
                "thresholds": {"confidence": 0.9, "magnitude": 3.0}
            },
            "high": {
                "conditions": ["significant_change", "moderate_anomaly", "trending_negative"],
                "thresholds": {"confidence": 0.7, "magnitude": 2.0}
            },
            "medium": {
                "conditions": ["moderate_change", "minor_anomaly", "attention_needed"],
                "thresholds": {"confidence": 0.5, "magnitude": 1.0}
            },
            "low": {
                "conditions": ["minor_change", "normal_variation", "informational"],
                "thresholds": {"confidence": 0.3, "magnitude": 0.5}
            }
        }
    
    def _load_category_mappings(self) -> Dict[str, str]:
        """Load category mappings for insights."""
        return {
            "vital_signs": InsightCategory.HEALTH_METRICS,
            "lab_results": InsightCategory.CLINICAL,
            "medication": InsightCategory.CLINICAL,
            "lifestyle": InsightCategory.LIFESTYLE,
            "exercise": InsightCategory.LIFESTYLE,
            "nutrition": InsightCategory.LIFESTYLE,
            "sleep": InsightCategory.LIFESTYLE,
            "stress": InsightCategory.LIFESTYLE,
            "behavior": InsightCategory.BEHAVIOR,
            "risk": InsightCategory.PREVENTIVE,
            "trend": InsightCategory.HEALTH_METRICS,
            "pattern": InsightCategory.HEALTH_METRICS,
            "anomaly": InsightCategory.CLINICAL
        }
    
    async def _generate_insights(self, data: Dict[str, Any], db: AsyncSession) -> List[Dict[str, Any]]:
        """Generate insights using multiple analysis approaches."""
        insights = []
        
        # Generate trend-based insights
        trend_insights = await self._generate_trend_insights(data)
        insights.extend(trend_insights)
        
        # Generate pattern-based insights
        pattern_insights = await self._generate_pattern_insights(data)
        insights.extend(pattern_insights)
        
        # Generate anomaly-based insights
        anomaly_insights = await self._generate_anomaly_insights(data)
        insights.extend(anomaly_insights)
        
        # Generate correlation-based insights
        correlation_insights = await self._generate_correlation_insights(data)
        insights.extend(correlation_insights)
        
        # Generate risk-based insights
        risk_insights = await self._generate_risk_insights(data)
        insights.extend(risk_insights)
        
        return insights
    
    async def _generate_trend_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights based on trend analysis."""
        insights = []
        
        # Analyze vital signs trends
        if 'vital_signs' in data:
            vital_trends = self._analyze_vital_signs_trends(data['vital_signs'])
            for trend in vital_trends:
                insight = self._create_trend_insight(trend)
                insights.append(insight)
        
        # Analyze lab results trends
        if 'lab_results' in data:
            lab_trends = self._analyze_lab_results_trends(data['lab_results'])
            for trend in lab_trends:
                insight = self._create_trend_insight(trend)
                insights.append(insight)
        
        return insights
    
    def _analyze_vital_signs_trends(self, vital_signs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze trends in vital signs data."""
        trends = []
        
        # Group by metric
        metrics = {}
        for record in vital_signs:
            metric = record.get('metric')
            if metric not in metrics:
                metrics[metric] = []
            metrics[metric].append(record)
        
        # Analyze each metric
        for metric, records in metrics.items():
            if len(records) < 3:
                continue
            
            # Sort by timestamp
            sorted_records = sorted(records, key=lambda x: x.get('timestamp', ''))
            
            # Calculate trend
            values = [r.get('value', 0) for r in sorted_records]
            timestamps = [r.get('timestamp', '') for r in sorted_records]
            
            trend = self._calculate_trend(values, timestamps)
            if trend:
                trends.append({
                    'type': 'trend_analysis',
                    'metric': metric,
                    'trend': trend,
                    'values': values,
                    'timestamps': timestamps,
                    'confidence': self._calculate_trend_confidence(values, trend)
                })
        
        return trends
    
    def _calculate_trend(self, values: List[float], timestamps: List[str]) -> Optional[Dict[str, Any]]:
        """Calculate trend from time series data."""
        if len(values) < 3:
            return None
        
        # Simple linear trend calculation
        x = list(range(len(values)))
        y = values
        
        # Calculate slope
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        # Determine trend direction
        if abs(slope) < 0.1:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        return {
            'direction': direction,
            'slope': slope,
            'magnitude': abs(slope),
            'period_days': len(values)
        }
    
    def _calculate_trend_confidence(self, values: List[float], trend: Dict[str, Any]) -> float:
        """Calculate confidence in trend analysis."""
        if len(values) < 3:
            return 0.0
        
        # Calculate R-squared (coefficient of determination)
        mean_y = sum(values) / len(values)
        ss_tot = sum((y - mean_y) ** 2 for y in values)
        
        # Simple linear regression residuals
        x = list(range(len(values)))
        slope = trend['slope']
        intercept = mean_y - slope * (len(values) - 1) / 2
        ss_res = sum((y - (slope * i + intercept)) ** 2 for i, y in enumerate(values))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Adjust confidence based on data quality
        confidence = r_squared * 0.8 + 0.2  # Base confidence of 0.2
        
        return min(confidence, 1.0)
    
    def _create_trend_insight(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """Create insight from trend analysis."""
        metric = trend['metric']
        direction = trend['direction']
        confidence = trend['confidence']
        
        # Get template
        template = self.insight_templates['trend_analysis'].get(direction, 
            "Your {metric} shows a {trend} trend over the past {period}.")
        
        # Generate description
        description = template.format(
            metric=metric.replace('_', ' ').title(),
            trend=direction,
            period=f"{trend['period_days']} days",
            interpretation=self._get_trend_interpretation(metric, direction)
        )
        
        return {
            'insight_type': InsightType.TREND_ANALYSIS,
            'category': self.category_mappings.get('trend', InsightCategory.HEALTH_METRICS),
            'title': f"{metric.replace('_', ' ').title()} Trend Analysis",
            'description': description,
            'severity': self._assess_severity(confidence, trend['magnitude']),
            'confidence_score': confidence,
            'relevance_score': self._calculate_relevance_score(metric, direction),
            'supporting_evidence': {
                'trend_data': trend,
                'data_points': len(trend['values']),
                'analysis_method': 'linear_regression'
            },
            'metadata': {
                'metric': metric,
                'trend_direction': direction,
                'trend_magnitude': trend['magnitude'],
                'period_days': trend['period_days']
            }
        }
    
    def _get_trend_interpretation(self, metric: str, direction: str) -> str:
        """Get interpretation for trend direction."""
        interpretations = {
            'heart_rate': {
                'increasing': 'potential stress or cardiovascular concerns',
                'decreasing': 'improved cardiovascular fitness',
                'stable': 'good cardiovascular stability'
            },
            'blood_pressure': {
                'increasing': 'potential hypertension development',
                'decreasing': 'improved blood pressure control',
                'stable': 'good blood pressure management'
            },
            'temperature': {
                'increasing': 'potential infection or inflammation',
                'decreasing': 'normal body temperature regulation',
                'stable': 'stable body temperature'
            }
        }
        
        return interpretations.get(metric, {}).get(direction, 'normal variation')
    
    def _assess_severity(self, confidence: float, magnitude: float) -> InsightSeverity:
        """Assess severity based on confidence and magnitude."""
        for severity, rules in self.severity_rules.items():
            if (confidence >= rules['thresholds']['confidence'] and 
                magnitude >= rules['thresholds']['magnitude']):
                return InsightSeverity(severity.upper())
        
        return InsightSeverity.LOW
    
    def _calculate_relevance_score(self, metric: str, direction: str) -> float:
        """Calculate relevance score for insight."""
        # Base relevance
        relevance = 0.5
        
        # Adjust based on metric importance
        important_metrics = ['heart_rate', 'blood_pressure', 'temperature', 'glucose']
        if metric in important_metrics:
            relevance += 0.2
        
        # Adjust based on trend direction
        if direction in ['increasing', 'decreasing']:
            relevance += 0.1
        
        return min(relevance, 1.0)
    
    async def _generate_pattern_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights based on pattern detection."""
        # Implementation for pattern-based insights
        return []
    
    async def _generate_anomaly_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights based on anomaly detection."""
        # Implementation for anomaly-based insights
        return []
    
    async def _generate_correlation_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights based on correlation analysis."""
        # Implementation for correlation-based insights
        return []
    
    async def _generate_risk_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights based on risk assessment."""
        # Implementation for risk-based insights
        return []
    
    def _categorize_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize insights by type and category."""
        for insight in insights:
            # Ensure category is set
            if 'category' not in insight:
                insight['category'] = InsightCategory.HEALTH_METRICS
            
            # Ensure insight type is set
            if 'insight_type' not in insight:
                insight['insight_type'] = InsightType.TREND_ANALYSIS
        
        return insights
    
    async def _score_insights(self, insights: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate confidence and relevance scores for insights."""
        for insight in insights:
            # Ensure confidence score is set
            if 'confidence_score' not in insight:
                insight['confidence_score'] = 0.7
            
            # Ensure relevance score is set
            if 'relevance_score' not in insight:
                insight['relevance_score'] = 0.5
        
        return insights
    
    def _rank_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank insights by importance and relevance."""
        # Sort by combined score (confidence * relevance * severity_weight)
        def get_combined_score(insight):
            confidence = insight.get('confidence_score', 0.5)
            relevance = insight.get('relevance_score', 0.5)
            severity_weight = {
                InsightSeverity.CRITICAL: 1.0,
                InsightSeverity.HIGH: 0.8,
                InsightSeverity.MEDIUM: 0.6,
                InsightSeverity.LOW: 0.4
            }.get(insight.get('severity', InsightSeverity.LOW), 0.5)
            
            return confidence * relevance * severity_weight
        
        return sorted(insights, key=get_combined_score, reverse=True)
    
    async def _generate_recommendations(self, insights: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on insights."""
        recommendations = []
        
        for insight in insights[:5]:  # Top 5 insights
            recommendation = self._create_recommendation_from_insight(insight)
            if recommendation:
                recommendations.append(recommendation)
        
        return recommendations
    
    def _create_recommendation_from_insight(self, insight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create recommendation from insight."""
        insight_type = insight.get('insight_type')
        severity = insight.get('severity')
        
        if severity == InsightSeverity.CRITICAL:
            return {
                'type': 'immediate_action',
                'title': f"Immediate attention required for {insight.get('title', 'health concern')}",
                'description': f"Based on {insight.get('title')}, immediate action is recommended.",
                'priority': 'critical',
                'actions': ['contact_healthcare_provider', 'monitor_closely']
            }
        elif severity == InsightSeverity.HIGH:
            return {
                'type': 'lifestyle_change',
                'title': f"Consider lifestyle changes for {insight.get('title', 'health improvement')}",
                'description': f"Based on {insight.get('title')}, consider making lifestyle adjustments.",
                'priority': 'high',
                'actions': ['schedule_appointment', 'lifestyle_modification']
            }
        
        return None
    
    async def _save_insights(self, insights: List[Dict[str, Any]], patient_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """Save insights to database."""
        saved_insights = []
        
        for insight_data in insights:
            try:
                # Create insight record
                insight_create = InsightCreate(
                    patient_id=patient_id,
                    insight_type=insight_data['insight_type'],
                    category=insight_data['category'],
                    title=insight_data['title'],
                    description=insight_data['description'],
                    severity=insight_data['severity'],
                    confidence_score=insight_data['confidence_score'],
                    relevance_score=insight_data['relevance_score'],
                    supporting_evidence=insight_data.get('supporting_evidence'),
                    data_sources=insight_data.get('metadata', {}).get('data_sources', [])
                )
                
                # Convert to database model
                insight_db = InsightDB(**insight_create.dict())
                db.add(insight_db)
                await db.flush()
                
                saved_insights.append(insight_data)
                
            except Exception as e:
                self.logger.error(f"Failed to save insight: {e}")
                continue
        
        await db.commit()
        return saved_insights
    
    def _count_by_category(self, insights: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count insights by category."""
        counts = {}
        for insight in insights:
            category = insight.get('category', 'unknown')
            counts[category] = counts.get(category, 0) + 1
        return counts
    
    def _count_by_severity(self, insights: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count insights by severity."""
        counts = {}
        for insight in insights:
            severity = insight.get('severity', 'unknown')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _calculate_average_confidence(self, insights: List[Dict[str, Any]]) -> float:
        """Calculate average confidence score."""
        if not insights:
            return 0.0
        
        total_confidence = sum(insight.get('confidence_score', 0.0) for insight in insights)
        return total_confidence / len(insights) 