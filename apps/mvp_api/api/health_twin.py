"""
Health Twin API — Phase 5: Digital Health Twin

Digital twin modeling for personalized health trajectories, what-if simulations,
and goal tracking using machine learning and health data.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,line-too-long

import json
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_insert,
    _supabase_upsert,
    _supabase_patch,
)

logger = get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class HealthTwinProfile(BaseModel):
    """Digital health twin profile."""

    id: str
    user_id: str
    model_version: str
    last_calibrated_at: str
    baseline_metrics: Dict[str, float]
    health_age: float
    chronological_age: int = 35  # Frontend compat — hardcoded until user DOB
    health_age_trend: str = "stable"  # Frontend compat — mapped from health_trajectory
    resilience_score: float
    adaptability_score: float
    recovery_capacity: float = 70.0  # Frontend compat — proxy for resilience_score
    metabolic_age: float = 35.0  # Frontend compat — computed from health_age
    biological_age_factors: Dict[
        str, float
    ] = {}  # Frontend compat — from baseline_metrics
    recent_changes: List[
        Dict[str, Any]
    ] = []  # Frontend compat — future: from snapshots
    risk_factors: List[Dict[str, Any]]
    protective_factors: List[Dict[str, Any]]
    health_trajectory: str  # improving, stable, declining
    projected_health_age_1y: float
    projected_health_age_5y: float
    data_completeness_score: float
    model_accuracy_score: float
    created_at: str
    updated_at: str


class SimulationChange(BaseModel):
    """A proposed change for simulation."""

    metric: str
    current_value: float
    target_value: float
    change_type: str  # percentage, absolute


class CreateSimulationRequest(BaseModel):
    """Request to create a health twin simulation."""

    simulation_name: str
    simulation_type: str  # lifestyle_change, goal_achievement, risk_mitigation
    scenario_description: str
    changes: List[SimulationChange]
    duration_days: int


class HealthTwinSimulation(BaseModel):
    """Health twin simulation with predicted outcomes."""

    id: str
    user_id: str
    simulation_name: str
    simulation_type: str
    scenario_description: str
    changes: List[SimulationChange]
    duration_days: int
    predicted_outcomes: Dict[str, Any]  # flat {metric: target_value} for frontend
    timeline_predictions: List[
        Dict[str, Any]
    ] = []  # Frontend compat — derived from metrics
    confidence_score: float = 0.7  # Frontend compat — mapped from success_probability
    recommendations: List[str] = []  # Frontend compat — from implementation_plan
    warnings: List[str] = []  # Frontend compat — from success_probability/effort
    parameters: Dict[str, Any] = {}  # Frontend compat — from changes
    health_age_impact: float
    risk_reduction: Dict[str, float]
    implementation_plan: List[Dict[str, str]]
    success_probability: float
    estimated_effort: str
    is_active: bool
    status: str
    actual_progress: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class HealthTwinSnapshot(BaseModel):
    """Daily snapshot of health twin state."""

    id: str
    snapshot_date: str
    health_age: float
    resilience_score: float
    overall_health_score: float
    cardiovascular_score: float
    metabolic_score: float
    recovery_score: float
    mental_wellbeing_score: float
    metrics_snapshot: Dict[str, float]
    deviations: Dict[str, float]
    created_at: str


class HealthTwinGoal(BaseModel):
    """Health goal tracked by digital twin."""

    id: str
    goal_type: str
    goal_name: str
    goal_description: str = ""  # Frontend compat — same as goal_name
    target_metric: str
    current_value: float
    target_value: float
    target_date: Optional[str] = None
    predicted_success_probability: float
    success_probability: float = (
        0.7  # Frontend compat — same as predicted_success_probability
    )
    predicted_completion_date: Optional[str] = None
    required_changes: List[Dict[str, Any]]
    strategies: List[str] = []  # Frontend compat — extracted from required_changes
    progress_percentage: float
    estimated_timeline_days: Optional[int] = None  # Frontend compat — from target_date
    milestones: List[Dict[str, Any]]
    status: str
    is_active: bool
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Health Age Calculation
# ---------------------------------------------------------------------------


def _calculate_health_age(
    chronological_age: int,
    sleep_score: float,
    readiness_score: float,
    hrv_balance: float,
    activity_score: float,
    bmi: Optional[float] = None,
) -> float:
    """
    Calculate biological/health age based on health metrics.
    Uses a simplified algorithm. In production, this would use ML models.
    """
    # Baseline is chronological age
    health_age = float(chronological_age)

    # Sleep impact (-5 to +5 years)
    if sleep_score >= 85:
        health_age -= 3.0
    elif sleep_score >= 75:
        health_age -= 1.0
    elif sleep_score < 60:
        health_age += 3.0
    elif sleep_score < 70:
        health_age += 1.0

    # Readiness/recovery impact (-4 to +4 years)
    if readiness_score >= 85:
        health_age -= 2.5
    elif readiness_score >= 75:
        health_age -= 1.0
    elif readiness_score < 60:
        health_age += 2.5
    elif readiness_score < 70:
        health_age += 1.0

    # HRV impact (-3 to +3 years)
    if hrv_balance >= 80:
        health_age -= 2.0
    elif hrv_balance < 60:
        health_age += 2.0

    # Activity impact (-2 to +2 years)
    if activity_score >= 85:
        health_age -= 1.5
    elif activity_score < 60:
        health_age += 1.5

    # BMI impact if provided
    if bmi:
        if 18.5 <= bmi <= 24.9:
            health_age -= 1.0
        elif bmi > 30:
            health_age += 2.0
        elif bmi > 25:
            health_age += 1.0

    return round(max(health_age, chronological_age - 10), 1)


def _calculate_resilience_score(
    hrv_balance: float,
    recovery_index: float,
    sleep_variability: float,
) -> float:
    """Calculate resilience/recovery capacity score (0-100)."""
    score = hrv_balance * 0.4
    score += recovery_index * 0.4
    variability_penalty = min(sleep_variability, 20) / 20 * 20
    score += 20 - variability_penalty
    return round(min(max(score, 0), 100), 1)


def _calculate_adaptability_score(
    readiness_variability: float,
    activity_consistency: float,
) -> float:
    """Calculate stress adaptability score (0-100)."""
    variability_score = max(0, 100 - (readiness_variability * 5))
    consistency_score = activity_consistency
    score = variability_score * 0.5 + consistency_score * 0.5
    return round(min(max(score, 0), 100), 1)


# ---------------------------------------------------------------------------
# Simulation Functions
# ---------------------------------------------------------------------------


def _simulate_lifestyle_change(
    baseline_metrics: Dict[str, float],
    changes: List[Dict[str, Any]],
    duration_days: int,
) -> Dict[str, Any]:
    """
    Simulate impact of lifestyle changes on health metrics.
    Simple linear projection for demo. Production would use ML models.
    """
    predicted_outcomes = {}

    for change in changes:
        metric = change["metric"]
        current = change["current_value"]
        target = change["target_value"]
        change_type = change["change_type"]

        if change_type == "percentage":
            delta = current * (target / 100)
            final_value = current + delta
        else:
            final_value = target

        timeline = []
        steps = min(duration_days // 7, 12)
        for i in range(steps + 1):
            progress = i / steps
            interpolated = current + (final_value - current) * progress
            timeline.append(
                {
                    "day": int(i * duration_days / steps),
                    "value": round(interpolated, 2),
                    "confidence": 0.9 - (progress * 0.2),
                }
            )

        predicted_outcomes[metric] = {
            "current": current,
            "target": final_value,
            "timeline": timeline,
            "confidence": 0.75,
        }

    # Calculate secondary impacts
    if "sleep_score" in predicted_outcomes:
        sleep_improvement = (
            predicted_outcomes["sleep_score"]["target"]
            - predicted_outcomes["sleep_score"]["current"]
        )
        if "readiness_score" not in predicted_outcomes:
            current_readiness = baseline_metrics.get("readiness_score", 75)
            predicted_readiness = current_readiness + (sleep_improvement * 0.75)

            predicted_outcomes["readiness_score"] = {
                "current": current_readiness,
                "target": round(predicted_readiness, 1),
                "timeline": [],
                "confidence": 0.65,
                "note": "Secondary effect from sleep improvement",
            }

    return predicted_outcomes


def _calculate_health_age_impact(
    current_health_age: float,
    predicted_outcomes: Dict[str, Any],
) -> float:
    """Calculate predicted change in health age from simulation."""
    impact = 0.0
    for metric, outcome in predicted_outcomes.items():
        if metric in ("sleep_score", "readiness_score", "activity_score"):
            improvement = outcome["target"] - outcome["current"]
            impact -= (improvement / 10) * 0.5
    return round(impact, 1)


# ---------------------------------------------------------------------------
# Frontend Compatibility Helpers
# ---------------------------------------------------------------------------


def _build_timeline_predictions(
    nested_outcomes: Dict[str, Any],
    base_health_age: float,
    health_age_impact: float,
    duration_days: int,
) -> List[Dict[str, Any]]:
    """Build frontend-compatible timeline_predictions from per-metric timelines."""
    all_days: set = set()
    for _metric, outcome in nested_outcomes.items():
        if isinstance(outcome, dict):
            for step in outcome.get("timeline", []):
                all_days.add(step.get("day", 0))

    if not all_days:
        all_days = {0, max(1, duration_days // 2), max(2, duration_days)}

    result = []
    for day in sorted(all_days):
        predicted_scores: Dict[str, float] = {}
        for metric, outcome in nested_outcomes.items():
            if isinstance(outcome, dict):
                for step in outcome.get("timeline", []):
                    if step.get("day") == day:
                        predicted_scores[metric] = round(step.get("value", 0.0), 1)
                        break

        progress = day / max(duration_days, 1)
        predicted_health_age = base_health_age + health_age_impact * progress

        result.append(
            {
                "days_from_now": day,
                "predicted_health_age": round(predicted_health_age, 1),
                "predicted_scores": predicted_scores,
            }
        )

    return result


def _enrich_profile(profile: dict) -> HealthTwinProfile:
    """Enrich DB profile dict with frontend-compatible computed fields."""
    if isinstance(profile.get("baseline_metrics"), str):
        profile["baseline_metrics"] = json.loads(profile["baseline_metrics"])
    if isinstance(profile.get("risk_factors"), str):
        profile["risk_factors"] = json.loads(profile["risk_factors"])
    if isinstance(profile.get("protective_factors"), str):
        profile["protective_factors"] = json.loads(profile["protective_factors"])

    health_age = profile.get("health_age", 35.0)
    trajectory = profile.get("health_trajectory", "stable")
    resilience = profile.get("resilience_score", 70.0)
    baseline = profile.get("baseline_metrics", {})

    profile["chronological_age"] = 35
    profile["health_age_trend"] = trajectory
    profile["recovery_capacity"] = resilience
    profile["metabolic_age"] = round(health_age * 0.97, 1)
    profile["biological_age_factors"] = baseline
    profile["recent_changes"] = []

    return HealthTwinProfile(**profile)


def _enrich_simulation(
    sim: dict, base_health_age: float = 35.0
) -> HealthTwinSimulation:
    """Enrich DB simulation dict with frontend-compatible computed fields."""
    if isinstance(sim.get("changes"), str):
        changes_data = json.loads(sim["changes"])
        sim["changes"] = [SimulationChange(**c) for c in changes_data]
    if isinstance(sim.get("risk_reduction"), str):
        sim["risk_reduction"] = json.loads(sim["risk_reduction"])
    if isinstance(sim.get("implementation_plan"), str):
        sim["implementation_plan"] = json.loads(sim["implementation_plan"])
    if isinstance(sim.get("actual_progress"), str) and sim["actual_progress"]:
        sim["actual_progress"] = json.loads(sim["actual_progress"])

    # Parse predicted_outcomes and split into nested (for timeline) and flat (for display)
    raw_outcomes = sim.get("predicted_outcomes", {})
    nested_outcomes: Dict[str, Any] = {}

    if isinstance(raw_outcomes, str):
        parsed = json.loads(raw_outcomes)
    else:
        parsed = raw_outcomes

    first_val = next(iter(parsed.values()), None) if parsed else None
    if isinstance(first_val, dict):
        nested_outcomes = parsed
    # else already flat

    # Build flat predicted_outcomes for frontend
    flat_outcomes: Dict[str, Any] = {}
    for metric, outcome in nested_outcomes.items():
        if isinstance(outcome, dict) and "target" in outcome:
            flat_outcomes[metric] = round(float(outcome["target"]), 1)
    if not flat_outcomes and isinstance(parsed, dict):
        flat_outcomes = {k: v for k, v in parsed.items() if isinstance(v, (int, float))}

    # Build timeline_predictions
    timeline = _build_timeline_predictions(
        nested_outcomes,
        base_health_age,
        sim.get("health_age_impact", 0.0),
        sim.get("duration_days", 90),
    )

    # Build recommendations from implementation_plan
    impl_plan = sim.get("implementation_plan", [])
    recommendations = [
        step.get("action", "") for step in impl_plan if step.get("action")
    ]

    # Build warnings from success_probability and effort
    success_prob = float(sim.get("success_probability", 0.7))
    effort = sim.get("estimated_effort", "medium")
    warnings: List[str] = []
    if success_prob < 0.5:
        warnings.append(
            "Low success probability — consider smaller, more gradual changes."
        )
    if effort == "high":
        warnings.append(
            "High effort required — ensure you have adequate support and resources."
        )

    # Build parameters from changes
    changes = sim.get("changes", [])
    parameters: Dict[str, Any] = {}
    for c in changes:
        if hasattr(c, "metric"):
            parameters[c.metric] = {
                "current": c.current_value,
                "target": c.target_value,
            }
        elif isinstance(c, dict) and c.get("metric"):
            parameters[c["metric"]] = {
                "current": c.get("current_value", 0),
                "target": c.get("target_value", 0),
            }

    sim["predicted_outcomes"] = flat_outcomes
    sim["timeline_predictions"] = timeline
    sim["confidence_score"] = success_prob
    sim["recommendations"] = recommendations
    sim["warnings"] = warnings
    sim["parameters"] = parameters

    return HealthTwinSimulation(**sim)


def _enrich_goal(goal: dict) -> HealthTwinGoal:
    """Enrich DB goal dict with frontend-compatible computed fields."""
    if isinstance(goal.get("required_changes"), str):
        goal["required_changes"] = json.loads(goal["required_changes"])
    if isinstance(goal.get("milestones"), str):
        goal["milestones"] = json.loads(goal["milestones"])

    goal["goal_description"] = goal.get("goal_name", "")
    goal["success_probability"] = float(goal.get("predicted_success_probability", 0.7))

    required_changes = goal.get("required_changes", [])
    strategies: List[str] = []
    for change in required_changes:
        if isinstance(change, dict):
            metric = change.get("metric", "")
            target = change.get("target_value", "")
            if metric:
                strategies.append(f"Improve {metric.replace('_', ' ')} to {target}")
    goal["strategies"] = strategies

    target_date_str = goal.get("target_date")
    if target_date_str:
        try:
            target_dt = date.fromisoformat(str(target_date_str)[:10])
            today = date.today()
            goal["estimated_timeline_days"] = max(0, (target_dt - today).days)
        except Exception:
            goal["estimated_timeline_days"] = None
    else:
        goal["estimated_timeline_days"] = None

    return HealthTwinGoal(**goal)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/profile", response_model=HealthTwinProfile)
async def get_health_twin_profile(
    current_user: dict = Depends(UsageGate("health_twin")),
):
    """
    Get or create user's health twin profile.
    Requires Pro+ subscription.
    """
    user_id = current_user["id"]

    profiles = await _supabase_get("health_twin_profile", f"user_id=eq.{user_id}")

    if profiles:
        return _enrich_profile(profiles[0])

    # Create new profile — fetch recent health data to initialize
    from .timeline import get_timeline

    try:
        timeline = await get_timeline(days=30, current_user=current_user)
    except Exception:
        timeline = []

    baseline_metrics = {
        "sleep_score": 75.0,
        "readiness_score": 75.0,
        "activity_score": 75.0,
        "hrv_balance": 70.0,
    }

    if timeline:
        sleep_scores = [
            e.sleep.sleep_score
            for e in timeline
            if hasattr(e, "sleep") and e.sleep and e.sleep.sleep_score
        ]
        if sleep_scores:
            baseline_metrics["sleep_score"] = sum(sleep_scores) / len(sleep_scores)

        readiness_scores = [
            e.readiness.readiness_score
            for e in timeline
            if hasattr(e, "readiness") and e.readiness and e.readiness.readiness_score
        ]
        if readiness_scores:
            baseline_metrics["readiness_score"] = sum(readiness_scores) / len(
                readiness_scores
            )

    chronological_age = 35
    health_age = _calculate_health_age(
        chronological_age,
        baseline_metrics["sleep_score"],
        baseline_metrics["readiness_score"],
        baseline_metrics["hrv_balance"],
        baseline_metrics["activity_score"],
    )

    resilience = _calculate_resilience_score(baseline_metrics["hrv_balance"], 75, 10)
    adaptability = _calculate_adaptability_score(8, 75)

    profile_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "model_version": "v1",
        "last_calibrated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_metrics": json.dumps(baseline_metrics),
        "health_age": health_age,
        "resilience_score": resilience,
        "adaptability_score": adaptability,
        "risk_factors": json.dumps([]),
        "protective_factors": json.dumps([]),
        "health_trajectory": "stable",
        "projected_health_age_1y": health_age,
        "projected_health_age_5y": health_age,
        "data_completeness_score": 0.7,
        "model_accuracy_score": 0.75,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_insert("health_twin_profile", profile_data)

    if not result:
        raise HTTPException(
            status_code=500, detail="Failed to create health twin profile"
        )

    result["baseline_metrics"] = baseline_metrics
    result["risk_factors"] = []
    result["protective_factors"] = []

    return _enrich_profile(result)


@router.post("/simulations", response_model=HealthTwinSimulation)
async def create_simulation(
    request: CreateSimulationRequest,
    current_user: dict = Depends(UsageGate("health_twin")),
):
    """
    Create a new health twin simulation (what-if scenario).
    Requires Pro+ subscription.
    """
    user_id = current_user["id"]

    profiles = await _supabase_get("health_twin_profile", f"user_id=eq.{user_id}")

    if not profiles:
        raise HTTPException(
            status_code=400,
            detail="Health twin profile not found. Please visit the Health Twin page first.",
        )

    profile = profiles[0]
    baseline_metrics = (
        json.loads(profile["baseline_metrics"])
        if isinstance(profile["baseline_metrics"], str)
        else profile["baseline_metrics"]
    )
    current_health_age = profile["health_age"]

    changes_data = [c.model_dump() for c in request.changes]

    predicted_outcomes = _simulate_lifestyle_change(
        baseline_metrics,
        changes_data,
        request.duration_days,
    )

    health_age_impact = _calculate_health_age_impact(
        current_health_age, predicted_outcomes
    )

    risk_reduction = {}
    for metric, outcome in predicted_outcomes.items():
        if metric in ("sleep_score", "readiness_score"):
            improvement = outcome["target"] - outcome["current"]
            if improvement > 5:
                risk_reduction["sleep_decline"] = min(improvement / 20 * 100, 50)
                risk_reduction["burnout"] = min(improvement / 30 * 100, 40)

    implementation_plan = [
        {
            "step": "1",
            "action": f"Establish baseline measurement for {request.changes[0].metric}",
            "timeframe": "Week 1",
        },
        {
            "step": "2",
            "action": "Begin gradual lifestyle changes",
            "timeframe": "Week 2-4",
        },
        {
            "step": "3",
            "action": "Monitor metrics and adjust approach",
            "timeframe": "Ongoing",
        },
    ]

    avg_change = sum(
        abs(c.target_value - c.current_value) for c in request.changes
    ) / len(request.changes)
    success_probability = max(0.5, 1.0 - (avg_change / 100))
    estimated_effort = (
        "high" if avg_change > 20 else "medium" if avg_change > 10 else "low"
    )

    simulation = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "simulation_name": request.simulation_name,
        "simulation_type": request.simulation_type,
        "scenario_description": request.scenario_description,
        "changes": json.dumps(changes_data),
        "duration_days": request.duration_days,
        "predicted_outcomes": json.dumps(predicted_outcomes),
        "health_age_impact": health_age_impact,
        "risk_reduction": json.dumps(risk_reduction),
        "implementation_plan": json.dumps(implementation_plan),
        "success_probability": success_probability,
        "estimated_effort": estimated_effort,
        "is_active": True,
        "status": "active",
        "actual_progress": None,
        "started_at": None,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_insert("health_twin_simulations", simulation)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create simulation")

    result["changes"] = [SimulationChange(**c) for c in changes_data]
    result["predicted_outcomes"] = predicted_outcomes
    result["risk_reduction"] = risk_reduction
    result["implementation_plan"] = implementation_plan

    return _enrich_simulation(result, base_health_age=current_health_age)


@router.get("/simulations", response_model=List[HealthTwinSimulation])
async def get_simulations(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get user's health twin simulations."""
    user_id = current_user["id"]

    profiles = await _supabase_get("health_twin_profile", f"user_id=eq.{user_id}")
    base_health_age = float(profiles[0]["health_age"]) if profiles else 35.0

    query = f"user_id=eq.{user_id}"
    if status:
        query += f"&status=eq.{status}"
    query += "&order=created_at.desc&limit=20"

    simulations = await _supabase_get("health_twin_simulations", query)

    if not simulations:
        return []

    return [_enrich_simulation(s, base_health_age) for s in simulations]


@router.get("/goals", response_model=List[HealthTwinGoal])
async def get_health_twin_goals(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get user's health twin goals."""
    user_id = current_user["id"]

    query = f"user_id=eq.{user_id}"
    if status:
        query += f"&status=eq.{status}"
    else:
        query += "&is_active=eq.true"

    query += "&order=created_at.desc&limit=20"

    goals = await _supabase_get("health_twin_goals", query)

    if not goals:
        return []

    return [_enrich_goal(g) for g in goals]
