"""Tests for common.metrics.composite_scores."""

import pytest
from common.metrics.composite_scores import (
    compute_hrv_balance,
    compute_readiness_score,
    compute_activity_score,
    compute_sleep_score,
    compute_all_composites,
)
from common.metrics.registry import SourceType

SOURCE = "healthkit"
DATE = "2026-03-18"


# ---------------------------------------------------------------------------
# HRV balance
# ---------------------------------------------------------------------------


class TestComputeHrvBalance:
    def test_computes_z_score_correctly(self):
        canonical_day = {"hrv_ms": 50.0}
        baseline = {"hrv_ms": {"mean_30d": 42.0, "std_30d": 8.0, "n": 25}}
        result = compute_hrv_balance(canonical_day, baseline, SOURCE)
        assert len(result) == 1
        m = result[0]
        assert m.canonical_metric == "hrv_balance"
        assert m.value == pytest.approx(1.0, abs=0.01)  # (50-42)/8 = 1.0
        assert m.source_type == SourceType.DERIVED
        assert m.confidence == pytest.approx(25 / 30, abs=0.01)

    def test_negative_z_score(self):
        canonical_day = {"hrv_ms": 30.0}
        baseline = {"hrv_ms": {"mean_30d": 42.0, "std_30d": 8.0, "n": 30}}
        result = compute_hrv_balance(canonical_day, baseline, SOURCE)
        assert result[0].value == pytest.approx(-1.5, abs=0.01)

    def test_clamped_to_minus_3_plus_3(self):
        canonical_day = {"hrv_ms": 1.0}  # extreme outlier
        baseline = {"hrv_ms": {"mean_30d": 42.0, "std_30d": 4.0, "n": 30}}
        result = compute_hrv_balance(canonical_day, baseline, SOURCE)
        assert result[0].value == -3.0

    def test_returns_empty_without_hrv_ms(self):
        result = compute_hrv_balance({"steps": 8000}, {}, SOURCE)
        assert result == []

    def test_returns_empty_insufficient_baseline_days(self):
        canonical_day = {"hrv_ms": 45.0}
        baseline = {"hrv_ms": {"mean_30d": 42.0, "std_30d": 6.0, "n": 10}}  # < 14
        assert compute_hrv_balance(canonical_day, baseline, SOURCE) == []

    def test_returns_empty_no_baseline(self):
        canonical_day = {"hrv_ms": 45.0}
        assert compute_hrv_balance(canonical_day, {}, SOURCE) == []

    def test_confidence_scales_with_n(self):
        canonical_day = {"hrv_ms": 44.0}
        baseline = {"hrv_ms": {"mean_30d": 42.0, "std_30d": 6.0, "n": 15}}
        result = compute_hrv_balance(canonical_day, baseline, SOURCE)
        assert result[0].confidence == pytest.approx(15 / 30, abs=0.01)


# ---------------------------------------------------------------------------
# Readiness score
# ---------------------------------------------------------------------------


class TestComputeReadinessScore:
    def test_full_inputs_produce_score(self):
        canonical_day = {
            "hrv_balance": 1.0,
            "resting_hr_bpm": 54.0,
            "sleep_score": 85.0,
            "body_temp_deviation_c": 0.0,
        }
        baseline = {"resting_hr_bpm": {"mean_30d": 58.0, "std_30d": 4.0}}
        result = compute_readiness_score(canonical_day, baseline, SOURCE)
        assert len(result) == 1
        m = result[0]
        assert m.canonical_metric == "readiness_score"
        assert 60 <= m.value <= 100  # good HRV + good sleep + low HR
        assert m.source_type == SourceType.COMPUTED_COMPOSITE
        assert m.confidence >= 0.50

    def test_poor_inputs_give_low_score(self):
        canonical_day = {
            "hrv_balance": -2.0,
            "resting_hr_bpm": 75.0,
            "sleep_score": 30.0,
        }
        baseline = {"resting_hr_bpm": {"mean_30d": 58.0, "std_30d": 4.0}}
        result = compute_readiness_score(canonical_day, baseline, SOURCE)
        assert len(result) == 1
        assert result[0].value < 50

    def test_returns_empty_with_single_input(self):
        """Only one metric available — not enough for composite."""
        canonical_day = {"hrv_balance": 0.5}
        result = compute_readiness_score(canonical_day, {}, SOURCE)
        # With only hrv_balance and no resting_hr (rhr_trend=None),
        # no path produces a score — expect empty
        assert result == []

    def test_score_is_0_to_100(self):
        for hrv in [-3.0, 0.0, 3.0]:
            for sleep in [10.0, 50.0, 95.0]:
                canonical_day = {
                    "hrv_balance": hrv,
                    "sleep_score": sleep,
                    "resting_hr_bpm": 60.0,
                }
                baseline = {"resting_hr_bpm": {"mean_30d": 58.0, "std_30d": 4.0}}
                result = compute_readiness_score(canonical_day, baseline, SOURCE)
                if result:
                    assert 0.0 <= result[0].value <= 100.0


# ---------------------------------------------------------------------------
# Activity score
# ---------------------------------------------------------------------------


class TestComputeActivityScore:
    def test_full_inputs(self):
        canonical_day = {
            "steps": 9_000,
            "active_min": 45,
            "active_calories_kcal": 500,
            "vo2_max": 44,
        }
        result = compute_activity_score(canonical_day, {}, SOURCE)
        assert len(result) == 1
        m = result[0]
        assert 60 <= m.value <= 100
        assert m.source_type == SourceType.COMPUTED_COMPOSITE
        assert m.confidence == 0.60

    def test_steps_only(self):
        result = compute_activity_score({"steps": 8_000}, {}, SOURCE)
        assert len(result) == 1
        assert result[0].value == pytest.approx(100.0, abs=1.0)
        assert result[0].confidence == 0.50

    def test_returns_empty_no_activity_data(self):
        result = compute_activity_score({"sleep_score": 80}, {}, SOURCE)
        assert result == []

    def test_score_bounded_0_100(self):
        # Extreme step count should not exceed 100
        result = compute_activity_score({"steps": 100_000}, {}, SOURCE)
        assert result[0].value == pytest.approx(100.0, abs=0.1)

    def test_sedentary_day(self):
        result = compute_activity_score({"steps": 500, "active_min": 0}, {}, SOURCE)
        assert result[0].value < 30

    def test_uses_personal_step_target(self):
        """When a user's 30d mean steps is 12000, 12000 steps = ~100 score."""
        baseline = {"steps": {"mean_30d": 12_000}}
        result = compute_activity_score({"steps": 12_000}, baseline, SOURCE)
        assert result[0].value == pytest.approx(100.0, abs=1.0)


# ---------------------------------------------------------------------------
# Sleep score
# ---------------------------------------------------------------------------


class TestComputeSleepScore:
    def test_optimal_sleep_scores_high(self):
        canonical_day = {
            "sleep_duration_min": 450,  # 7.5 h
            "sleep_efficiency_pct": 92,
            "deep_sleep_min": 90,  # 20% of 450
            "rem_sleep_min": 100,  # 22% of 450
        }
        result = compute_sleep_score(canonical_day, {}, SOURCE)
        assert len(result) == 1
        assert result[0].value >= 80

    def test_poor_sleep_scores_low(self):
        canonical_day = {
            "sleep_duration_min": 240,  # 4 h
            "sleep_efficiency_pct": 55,
        }
        result = compute_sleep_score(canonical_day, {}, SOURCE)
        assert result[0].value < 60

    def test_duration_only(self):
        result = compute_sleep_score({"sleep_duration_min": 450}, {}, SOURCE)
        assert len(result) == 1
        assert result[0].confidence == 0.45

    def test_duration_and_efficiency(self):
        result = compute_sleep_score(
            {"sleep_duration_min": 450, "sleep_efficiency_pct": 90}, {}, SOURCE
        )
        assert result[0].confidence == 0.55

    def test_returns_empty_no_sleep_data(self):
        result = compute_sleep_score({"steps": 8000}, {}, SOURCE)
        assert result == []

    def test_score_bounded_0_100(self):
        for dur in [120, 480, 600]:
            result = compute_sleep_score({"sleep_duration_min": dur}, {}, SOURCE)
            assert 0.0 <= result[0].value <= 100.0


# ---------------------------------------------------------------------------
# compute_all_composites
# ---------------------------------------------------------------------------


class TestComputeAllComposites:
    def test_skips_metrics_already_present(self):
        """If sleep_score is already in already_have, don't recompute it."""
        canonical_day = {
            "sleep_duration_min": 450,
            "sleep_efficiency_pct": 90,
        }
        # sleep_score already populated by device natively
        result = compute_all_composites(
            canonical_day, {}, SOURCE, already_have={"sleep_score"}
        )
        names = {m.canonical_metric for m in result}
        assert "sleep_score" not in names

    def test_computes_multiple_composites(self):
        canonical_day = {
            "steps": 8_000,
            "active_min": 35,
            "active_calories_kcal": 420,
            "sleep_duration_min": 450,
            "sleep_efficiency_pct": 88,
        }
        result = compute_all_composites(canonical_day, {}, SOURCE, already_have=set())
        names = {m.canonical_metric for m in result}
        assert "activity_score" in names
        assert "sleep_score" in names

    def test_all_results_have_computed_composite_type(self):
        canonical_day = {
            "steps": 7_000,
            "sleep_duration_min": 420,
            "sleep_efficiency_pct": 85,
        }
        result = compute_all_composites(canonical_day, {}, SOURCE, already_have=set())
        for m in result:
            assert m.source_type == SourceType.COMPUTED_COMPOSITE

    def test_returns_empty_no_usable_data(self):
        result = compute_all_composites(
            {"avg_glucose_mgdl": 105}, {}, SOURCE, already_have=set()
        )
        # Glucose alone can't produce activity/sleep/readiness composites
        assert result == []
