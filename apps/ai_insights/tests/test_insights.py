"""Unit tests for AI Insights service models."""
import pytest
from datetime import datetime
from uuid import uuid4


class TestInsightModels:
    def test_insight_create(self):
        """Test InsightCreate model with valid data."""
        from apps.ai_insights.models.insight_models import InsightCreate

        insight = InsightCreate(
            patient_id=uuid4(),
            insight_type="trend_analysis",
            category="health_metrics",
            title="Heart Rate Trend Detected",
            description="Your resting heart rate has decreased by 5 bpm over 30 days.",
            severity="low",
            confidence_score=0.85,
            relevance_score=0.9,
            data_sources=["device_data", "health_tracking"],
        )
        assert insight.title == "Heart Rate Trend Detected"
        assert insight.confidence_score == 0.85
        assert insight.insight_type == "trend_analysis"

    def test_insight_create_minimal(self):
        """Test InsightCreate with minimal required fields."""
        from apps.ai_insights.models.insight_models import InsightCreate

        insight = InsightCreate(
            patient_id=uuid4(),
            insight_type="anomaly_detection",
            category="clinical",
            title="Anomaly Detected",
            description="Unusual pattern found.",
            confidence_score=0.7,
            relevance_score=0.6,
        )
        assert insight.data_sources is None
        assert insight.severity == "medium"

    def test_insight_invalid_confidence_score(self):
        """Test InsightCreate rejects invalid confidence score."""
        from apps.ai_insights.models.insight_models import InsightCreate

        with pytest.raises(Exception):
            InsightCreate(
                patient_id=uuid4(),
                insight_type="trend_analysis",
                category="health_metrics",
                title="Bad Score",
                description="Test",
                confidence_score=1.5,  # Over max
                relevance_score=0.5,
            )

    def test_insight_update_partial(self):
        """Test InsightUpdate allows partial updates."""
        from apps.ai_insights.models.insight_models import InsightUpdate

        update = InsightUpdate(title="Updated Title", severity="high")
        assert update.title == "Updated Title"
        assert update.description is None

    def test_insight_missing_required(self):
        """Test InsightCreate fails without required fields."""
        from apps.ai_insights.models.insight_models import InsightCreate

        with pytest.raises(Exception):
            InsightCreate(title="Incomplete")


class TestHealthPatternModels:
    def test_health_pattern_create(self):
        """Test HealthPatternCreate model."""
        from apps.ai_insights.models.insight_models import HealthPatternCreate

        pattern = HealthPatternCreate(
            patient_id=uuid4(),
            pattern_type="sleep_pattern",
            pattern_name="Late Sleep Onset",
            description="Consistently falling asleep after midnight on weekdays.",
            confidence_score=0.88,
            data_points=[
                {"date": "2026-01-01", "sleep_onset": "00:45"},
                {"date": "2026-01-02", "sleep_onset": "01:15"},
            ],
        )
        assert pattern.pattern_name == "Late Sleep Onset"
        assert pattern.confidence_score == 0.88
        assert len(pattern.data_points) == 2

    def test_health_pattern_missing_required(self):
        """Test HealthPatternCreate fails without required fields."""
        from apps.ai_insights.models.insight_models import HealthPatternCreate

        with pytest.raises(Exception):
            HealthPatternCreate(pattern_name="Incomplete")


class TestHealthScoreModels:
    def test_health_score_create(self):
        """Test HealthScoreCreate model."""
        from apps.ai_insights.models.health_score_models import HealthScoreCreate

        score = HealthScoreCreate(
            patient_id=uuid4(),
            score_type="overall_health",
            score_name="Overall Health Score",
            score_value=82.5,
            max_score=100.0,
            components={"cardiovascular": 85.0, "metabolic": 78.0, "mental": 84.0},
            risk_level="low",
            trend_direction="improving",
        )
        assert score.score_value == 82.5
        assert score.score_name == "Overall Health Score"
        assert score.components["cardiovascular"] == 85.0

    def test_health_score_missing_required(self):
        """Test HealthScoreCreate fails without required fields."""
        from apps.ai_insights.models.health_score_models import HealthScoreCreate

        with pytest.raises(Exception):
            HealthScoreCreate(score_name="Incomplete")


class TestInsightEnums:
    def test_insight_type_enum(self):
        """Test InsightType enum values."""
        from apps.ai_insights.models.insight_models import InsightType

        assert InsightType.TREND_ANALYSIS == "trend_analysis"
        assert InsightType.ANOMALY_DETECTION == "anomaly_detection"
        assert InsightType.RISK_ASSESSMENT == "risk_assessment"

    def test_insight_severity_enum(self):
        """Test InsightSeverity enum values."""
        from apps.ai_insights.models.insight_models import InsightSeverity

        assert InsightSeverity.LOW == "low"
        assert InsightSeverity.CRITICAL == "critical"

    def test_score_type_enum(self):
        """Test ScoreType enum values."""
        from apps.ai_insights.models.health_score_models import ScoreType

        assert ScoreType.OVERALL_HEALTH == "overall_health"
        assert ScoreType.CARDIOVASCULAR_HEALTH == "cardiovascular_health"

    def test_risk_level_enum(self):
        """Test RiskLevel enum values."""
        from apps.ai_insights.models.health_score_models import RiskLevel

        assert RiskLevel.LOW == "low"
        assert RiskLevel.CRITICAL == "critical"
