"""
AI Insights Models
Data models for AI insights and recommendations.
"""

# Import specific models to avoid conflicts
from .insight_models import (
    InsightDB, HealthPatternDB,
    InsightType, InsightSeverity, InsightStatus, InsightCategory,
    InsightBase, InsightCreate, InsightUpdate, InsightResponse,
    HealthPatternBase, HealthPatternCreate, HealthPatternUpdate, HealthPatternResponse
)

from .recommendation_models import (
    RecommendationDB, RecommendationActionDB, HealthGoalDB,
    RecommendationType, RecommendationPriority, RecommendationStatus, ActionType,
    RecommendationBase, RecommendationCreate, RecommendationUpdate, RecommendationResponse,
    RecommendationActionBase, RecommendationActionCreate, RecommendationActionUpdate, RecommendationActionResponse,
    HealthGoalBase, HealthGoalCreate, HealthGoalUpdate, HealthGoalResponse
)

from .health_score_models import (
    HealthScoreDB, HealthScoreTrendDB, RiskAssessmentDB, WellnessIndexDB,
    ScoreType, ScoreCategory, RiskLevel, TrendDirection,
    HealthScoreBase, HealthScoreCreate, HealthScoreUpdate, HealthScoreResponse,
    HealthScoreTrendBase, HealthScoreTrendCreate, HealthScoreTrendResponse,
    RiskAssessmentBase, RiskAssessmentCreate, RiskAssessmentUpdate, RiskAssessmentResponse,
    WellnessIndexBase, WellnessIndexCreate, WellnessIndexUpdate, WellnessIndexResponse
) 