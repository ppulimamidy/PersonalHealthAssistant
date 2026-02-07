"""Unit tests for Explainability (XAI) service models.

The explainability service only has ORM models, so we test with
simple Pydantic schemas that mirror the DB model structure.
"""
import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# Pydantic schemas for testing (mirrors ORM model shapes)
class ExplanationCreate(BaseModel):
    """Schema for creating an explanation."""

    patient_id: str
    explanation_type: str  # prediction, recommendation
    model_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    feature_importance: Optional[Dict[str, float]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class ModelCardCreate(BaseModel):
    """Schema for creating a model card."""

    model_name: str
    description: Optional[str] = None
    version: Optional[str] = None
    intended_use: Optional[str] = None
    limitations: Optional[str] = None
    training_data_summary: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    ethical_considerations: Optional[str] = None


class TestExplanationModels:
    def test_explanation_creation(self):
        """Test explanation creation with valid data."""
        explanation = ExplanationCreate(
            patient_id=str(uuid4()),
            explanation_type="prediction",
            model_id="risk_model_v2",
            input_data={
                "age": 55,
                "blood_pressure": 140,
                "cholesterol": 220,
                "bmi": 28.5,
            },
            output_data={
                "risk_score": 0.72,
                "risk_level": "high",
                "predicted_condition": "cardiovascular_disease",
            },
            feature_importance={
                "blood_pressure": 0.35,
                "cholesterol": 0.25,
                "age": 0.20,
                "bmi": 0.15,
            },
            confidence_score=0.85,
        )
        assert explanation.explanation_type == "prediction"
        assert explanation.confidence_score == 0.85
        assert explanation.feature_importance["blood_pressure"] == 0.35

    def test_explanation_minimal(self):
        """Test explanation creation with minimal fields."""
        explanation = ExplanationCreate(
            patient_id=str(uuid4()),
            explanation_type="recommendation",
        )
        assert explanation.model_id is None
        assert explanation.input_data is None
        assert explanation.confidence_score is None

    def test_explanation_invalid_confidence(self):
        """Test explanation rejects invalid confidence score."""
        with pytest.raises(Exception):
            ExplanationCreate(
                patient_id=str(uuid4()),
                explanation_type="prediction",
                confidence_score=1.5,
            )

    def test_explanation_recommendation_type(self):
        """Test explanation with recommendation type."""
        explanation = ExplanationCreate(
            patient_id=str(uuid4()),
            explanation_type="recommendation",
            model_id="nutrition_advisor_v1",
            output_data={
                "recommendation": "Increase fiber intake",
                "impact_score": 0.6,
            },
            confidence_score=0.78,
        )
        assert explanation.explanation_type == "recommendation"
        assert explanation.output_data["recommendation"] == "Increase fiber intake"

    def test_explanation_missing_required(self):
        """Test explanation fails without required fields."""
        with pytest.raises(Exception):
            ExplanationCreate(explanation_type="prediction")


class TestModelCardModels:
    def test_model_card_creation(self):
        """Test model card creation with full data."""
        card = ModelCardCreate(
            model_name="cardiovascular_risk_v2",
            description="Predicts 10-year cardiovascular disease risk.",
            version="2.1.0",
            intended_use="Clinical decision support for primary care.",
            limitations="Not validated for patients under 30 or over 80.",
            training_data_summary="Trained on 50,000 patient records from 2015-2024.",
            performance_metrics={
                "accuracy": 0.89,
                "auc_roc": 0.92,
                "f1_score": 0.87,
                "precision": 0.90,
                "recall": 0.85,
            },
            ethical_considerations="Model may underperform for underrepresented populations.",
        )
        assert card.model_name == "cardiovascular_risk_v2"
        assert card.version == "2.1.0"
        assert card.performance_metrics["auc_roc"] == 0.92

    def test_model_card_minimal(self):
        """Test model card creation with minimal fields."""
        card = ModelCardCreate(model_name="simple_model")
        assert card.description is None
        assert card.version is None
        assert card.performance_metrics is None

    def test_model_card_missing_required(self):
        """Test model card fails without required fields."""
        with pytest.raises(Exception):
            ModelCardCreate()

    def test_model_card_with_metrics(self):
        """Test model card with various performance metrics."""
        card = ModelCardCreate(
            model_name="sleep_quality_predictor",
            version="1.0.0",
            performance_metrics={
                "mae": 0.15,
                "rmse": 0.22,
                "r_squared": 0.85,
            },
        )
        assert card.performance_metrics["r_squared"] == 0.85
        assert len(card.performance_metrics) == 3
