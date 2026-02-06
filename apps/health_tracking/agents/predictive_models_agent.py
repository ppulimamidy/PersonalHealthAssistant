"""
Predictive Models Agent
Advanced machine learning models for health prediction and forecasting.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
from dataclasses import dataclass
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

from .base_agent import BaseHealthAgent, AgentResult
from ..models.health_metrics import HealthMetric, MetricType
from common.utils.logging import get_logger

logger = get_logger(__name__)

class PredictionType(Enum):
    """Prediction type enumeration"""
    DISEASE_RISK = "disease_risk"
    READMISSION_RISK = "readmission_risk"
    TREATMENT_OUTCOME = "treatment_outcome"
    HEALTH_DECLINE = "health_decline"
    LIFESPAN_PREDICTION = "lifespan_prediction"

@dataclass
class PredictionResult:
    """Prediction result"""
    prediction_type: PredictionType
    predicted_value: float
    confidence: float
    probability: float
    risk_factors: List[str]
    recommendations: List[str]
    model_accuracy: float
    data_quality_score: float

class PredictiveModelsAgent(BaseHealthAgent):
    """
    Advanced predictive modeling agent using machine learning for health predictions.
    Implements various ML models for disease prediction, risk assessment, and outcomes.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="predictive_models",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Model configurations
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        
        # Feature engineering configurations
        self.feature_configs = {
            PredictionType.DISEASE_RISK: {
                "required_features": ["age", "bmi", "blood_pressure", "cholesterol", "glucose"],
                "target_diseases": ["diabetes", "heart_disease", "hypertension", "obesity"]
            },
            PredictionType.READMISSION_RISK: {
                "required_features": ["length_of_stay", "comorbidities", "age", "discharge_condition"],
                "time_window": 30  # days
            },
            PredictionType.TREATMENT_OUTCOME: {
                "required_features": ["treatment_type", "baseline_metrics", "compliance_score"],
                "outcome_types": ["success", "partial", "failure"]
            }
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Generate predictions using advanced ML models.
        
        Args:
            data: Dictionary containing user_id, prediction_type, and parameters
            db: Database session
            
        Returns:
            AgentResult with predictions
        """
        user_id = data.get("user_id")
        prediction_type = data.get("prediction_type")
        target_disease = data.get("target_disease")
        time_horizon = data.get("time_horizon", 365)  # days
        
        if not user_id or not prediction_type:
            return AgentResult(
                success=False,
                error="user_id and prediction_type are required"
            )
        
        try:
            # Get comprehensive health data
            health_data = await self._get_comprehensive_health_data(user_id, db)
            
            if not health_data:
                return AgentResult(
                    success=False,
                    error="Insufficient health data for prediction"
                )
            
            # Generate predictions based on type
            if prediction_type == PredictionType.DISEASE_RISK.value:
                predictions = await self._predict_disease_risk(health_data, target_disease)
            elif prediction_type == PredictionType.READMISSION_RISK.value:
                predictions = await self._predict_readmission_risk(health_data)
            elif prediction_type == PredictionType.TREATMENT_OUTCOME.value:
                predictions = await self._predict_treatment_outcome(health_data)
            elif prediction_type == PredictionType.HEALTH_DECLINE.value:
                predictions = await self._predict_health_decline(health_data, time_horizon)
            else:
                return AgentResult(
                    success=False,
                    error=f"Unsupported prediction type: {prediction_type}"
                )
            
            # Generate insights and recommendations
            insights = self._generate_prediction_insights(predictions)
            recommendations = self._generate_prediction_recommendations(predictions)
            
            return AgentResult(
                success=True,
                data={
                    "predictions": [self._prediction_to_dict(pred) for pred in predictions],
                    "prediction_type": prediction_type,
                    "time_horizon": time_horizon,
                    "data_quality": self._assess_data_quality(health_data)
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.85  # High confidence for ML models
            )
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Prediction failed: {str(e)}"
            )
    
    async def _get_comprehensive_health_data(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive health data for prediction"""
        # Get recent health metrics
        start_date = datetime.utcnow() - timedelta(days=365)
        
        query = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.created_at >= start_date
            )
        ).order_by(HealthMetric.created_at.desc())
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        # Process metrics into features
        health_data = {
            "metrics": {},
            "demographics": {},
            "lifestyle": {},
            "medical_history": {}
        }
        
        # Group metrics by type
        for metric in metrics:
            metric_type = metric.metric_type.value
            if metric_type not in health_data["metrics"]:
                health_data["metrics"][metric_type] = []
            health_data["metrics"][metric_type].append({
                "value": metric.value,
                "timestamp": metric.created_at,
                "metadata": metric.metric_metadata
            })
        
        # Calculate aggregated features
        health_data["features"] = self._extract_features(health_data["metrics"])
        
        return health_data
    
    def _extract_features(self, metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Extract ML features from health metrics"""
        features = {}
        
        for metric_type, metric_list in metrics.items():
            if not metric_list:
                continue
            
            values = [m["value"] for m in metric_list]
            
            # Basic statistics
            features[f"{metric_type}_mean"] = np.mean(values)
            features[f"{metric_type}_std"] = np.std(values)
            features[f"{metric_type}_min"] = np.min(values)
            features[f"{metric_type}_max"] = np.max(values)
            features[f"{metric_type}_latest"] = values[0]  # Most recent
            
            # Trend features
            if len(values) >= 2:
                features[f"{metric_type}_trend"] = (values[0] - values[-1]) / values[-1] if values[-1] != 0 else 0
            
            # Volatility
            if len(values) >= 3:
                features[f"{metric_type}_volatility"] = np.std(np.diff(values))
        
        return features
    
    async def _predict_disease_risk(self, health_data: Dict[str, Any], target_disease: str) -> List[PredictionResult]:
        """Predict disease risk using ML models"""
        predictions = []
        
        # Feature engineering for disease prediction
        features = self._engineer_disease_features(health_data)
        
        if not features:
            return predictions
        
        # Train or load model for each disease
        diseases = ["diabetes", "heart_disease", "hypertension", "obesity"]
        
        for disease in diseases:
            if target_disease and disease != target_disease:
                continue
            
            try:
                # Train model (in production, this would use pre-trained models)
                model, accuracy = await self._train_disease_model(disease, features)
                
                # Make prediction
                prediction = model.predict_proba([list(features.values())])[0]
                risk_probability = prediction[1] if len(prediction) > 1 else prediction[0]
                
                # Determine risk level
                if risk_probability > 0.7:
                    risk_level = "high"
                elif risk_probability > 0.4:
                    risk_level = "moderate"
                else:
                    risk_level = "low"
                
                # Identify risk factors
                risk_factors = self._identify_disease_risk_factors(disease, features)
                
                predictions.append(PredictionResult(
                    prediction_type=PredictionType.DISEASE_RISK,
                    predicted_value=risk_probability,
                    confidence=accuracy,
                    probability=risk_probability,
                    risk_factors=risk_factors,
                    recommendations=self._generate_disease_recommendations(disease, risk_level),
                    model_accuracy=accuracy,
                    data_quality_score=self._assess_data_quality(health_data)
                ))
                
            except Exception as e:
                logger.error(f"Error predicting {disease} risk: {str(e)}")
                continue
        
        return predictions
    
    def _engineer_disease_features(self, health_data: Dict[str, Any]) -> Dict[str, float]:
        """Engineer features for disease prediction"""
        features = {}
        
        # Extract features from health data
        metrics = health_data.get("features", {})
        
        # BMI calculation (simplified)
        if "weight_mean" in metrics and "height_mean" in metrics:
            height_m = metrics["height_mean"] / 100
            features["bmi"] = metrics["weight_mean"] / (height_m ** 2)
        
        # Blood pressure features
        if "blood_pressure_systolic_mean" in metrics:
            features["systolic_bp"] = metrics["blood_pressure_systolic_mean"]
        if "blood_pressure_diastolic_mean" in metrics:
            features["diastolic_bp"] = metrics["blood_pressure_diastolic_mean"]
        
        # Glucose features
        if "blood_glucose_mean" in metrics:
            features["glucose"] = metrics["blood_glucose_mean"]
        
        # Heart rate features
        if "heart_rate_mean" in metrics:
            features["heart_rate"] = metrics["heart_rate_mean"]
        
        # Activity features
        if "steps_mean" in metrics:
            features["activity_level"] = metrics["steps_mean"]
        
        # Sleep features
        if "sleep_duration_mean" in metrics:
            features["sleep_hours"] = metrics["sleep_duration_mean"]
        
        # Add default values for missing features
        default_features = {
            "age": 45,  # Default age
            "bmi": 25,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "glucose": 100,
            "heart_rate": 70,
            "activity_level": 5000,
            "sleep_hours": 7
        }
        
        for feature, default_value in default_features.items():
            if feature not in features:
                features[feature] = default_value
        
        return features
    
    async def _train_disease_model(self, disease: str, features: Dict[str, float]) -> Tuple[Any, float]:
        """Train or load disease prediction model"""
        # In production, this would load pre-trained models
        # For demo purposes, we'll create a simple model
        
        # Create synthetic training data
        n_samples = 1000
        X = np.random.rand(n_samples, len(features))
        y = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])  # 30% disease prevalence
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Calculate accuracy
        accuracy = np.mean(cross_val_score(model, X, y, cv=5))
        
        return model, accuracy
    
    def _identify_disease_risk_factors(self, disease: str, features: Dict[str, float]) -> List[str]:
        """Identify risk factors for specific disease"""
        risk_factors = []
        
        if disease == "diabetes":
            if features.get("glucose", 0) > 140:
                risk_factors.append("Elevated blood glucose")
            if features.get("bmi", 0) > 30:
                risk_factors.append("High BMI")
            if features.get("activity_level", 0) < 3000:
                risk_factors.append("Low physical activity")
        
        elif disease == "heart_disease":
            if features.get("systolic_bp", 0) > 140:
                risk_factors.append("High blood pressure")
            if features.get("heart_rate", 0) > 100:
                risk_factors.append("Elevated heart rate")
            if features.get("bmi", 0) > 30:
                risk_factors.append("High BMI")
        
        elif disease == "hypertension":
            if features.get("systolic_bp", 0) > 140:
                risk_factors.append("High systolic blood pressure")
            if features.get("diastolic_bp", 0) > 90:
                risk_factors.append("High diastolic blood pressure")
        
        elif disease == "obesity":
            if features.get("bmi", 0) > 30:
                risk_factors.append("High BMI")
            if features.get("activity_level", 0) < 3000:
                risk_factors.append("Low physical activity")
        
        return risk_factors
    
    def _generate_disease_recommendations(self, disease: str, risk_level: str) -> List[str]:
        """Generate recommendations for disease prevention"""
        recommendations = []
        
        if disease == "diabetes":
            if risk_level == "high":
                recommendations.extend([
                    "Monitor blood glucose regularly",
                    "Consult with endocrinologist",
                    "Follow diabetes prevention diet",
                    "Increase physical activity"
                ])
            else:
                recommendations.extend([
                    "Maintain healthy diet",
                    "Exercise regularly",
                    "Monitor weight"
                ])
        
        elif disease == "heart_disease":
            if risk_level == "high":
                recommendations.extend([
                    "Consult cardiologist",
                    "Monitor blood pressure daily",
                    "Follow heart-healthy diet",
                    "Quit smoking if applicable"
                ])
            else:
                recommendations.extend([
                    "Maintain healthy lifestyle",
                    "Regular cardiovascular exercise",
                    "Monitor cholesterol levels"
                ])
        
        return recommendations
    
    async def _predict_readmission_risk(self, health_data: Dict[str, Any]) -> List[PredictionResult]:
        """Predict readmission risk"""
        # Implementation for readmission risk prediction
        # This would use hospital discharge data and patient history
        return []
    
    async def _predict_treatment_outcome(self, health_data: Dict[str, Any]) -> List[PredictionResult]:
        """Predict treatment outcomes"""
        # Implementation for treatment outcome prediction
        # This would use treatment history and patient response data
        return []
    
    async def _predict_health_decline(self, health_data: Dict[str, Any], time_horizon: int) -> List[PredictionResult]:
        """Predict health decline over time"""
        # Implementation for health decline prediction
        # This would use trend analysis and ML models
        return []
    
    def _assess_data_quality(self, health_data: Dict[str, Any]) -> float:
        """Assess quality of health data for prediction"""
        metrics = health_data.get("metrics", {})
        
        if not metrics:
            return 0.0
        
        # Calculate data completeness
        total_metrics = len(metrics)
        complete_metrics = sum(1 for m in metrics.values() if len(m) > 0)
        
        completeness = complete_metrics / total_metrics if total_metrics > 0 else 0
        
        # Calculate data recency
        recent_data = 0
        for metric_list in metrics.values():
            if metric_list:
                latest_date = metric_list[0]["timestamp"]
                if (datetime.utcnow() - latest_date).days <= 30:
                    recent_data += 1
        
        recency = recent_data / total_metrics if total_metrics > 0 else 0
        
        # Overall quality score
        quality_score = (completeness * 0.6) + (recency * 0.4)
        
        return round(quality_score, 2)
    
    def _prediction_to_dict(self, prediction: PredictionResult) -> Dict[str, Any]:
        """Convert prediction result to dictionary"""
        return {
            "prediction_type": prediction.prediction_type.value,
            "predicted_value": prediction.predicted_value,
            "confidence": prediction.confidence,
            "probability": prediction.probability,
            "risk_factors": prediction.risk_factors,
            "recommendations": prediction.recommendations,
            "model_accuracy": prediction.model_accuracy,
            "data_quality_score": prediction.data_quality_score
        }
    
    def _generate_prediction_insights(self, predictions: List[PredictionResult]) -> List[str]:
        """Generate insights from predictions"""
        insights = []
        
        if not predictions:
            return ["No predictions available due to insufficient data"]
        
        # Overall risk assessment
        high_risk_predictions = [p for p in predictions if p.probability > 0.7]
        if high_risk_predictions:
            insights.append(f"High risk detected in {len(high_risk_predictions)} health areas")
        
        # Data quality insights
        avg_quality = np.mean([p.data_quality_score for p in predictions])
        if avg_quality < 0.5:
            insights.append("Data quality is low - consider collecting more health metrics")
        
        # Model confidence insights
        avg_confidence = np.mean([p.confidence for p in predictions])
        if avg_confidence < 0.7:
            insights.append("Model confidence is moderate - predictions should be interpreted with caution")
        
        return insights
    
    def _generate_prediction_recommendations(self, predictions: List[PredictionResult]) -> List[str]:
        """Generate recommendations based on predictions"""
        recommendations = []
        
        if not predictions:
            return ["Collect more health data to enable predictions"]
        
        # Prioritize high-risk predictions
        high_risk = [p for p in predictions if p.probability > 0.7]
        if high_risk:
            recommendations.append("Schedule consultation with healthcare provider for high-risk conditions")
        
        # General recommendations
        recommendations.extend([
            "Continue monitoring health metrics regularly",
            "Follow preventive care recommendations",
            "Maintain healthy lifestyle habits"
        ])
        
        return recommendations 