"""Tests for common.metrics.normalizer.HealthNormalizer."""

import pytest
from common.metrics.normalizer import HealthNormalizer, SOURCE_PRIORITY
from common.metrics.registry import SourceType, CANONICAL_METRICS

DATE = "2026-03-18"
EMPTY_BASELINE: dict = {}

normalizer = HealthNormalizer()


class TestHealthNormalizerBasic:
    def test_oura_returns_metrics(self):
        raw = {
            "sleep_score": 82,
            "readiness_score": 79,
            "hrv_balance": 1.2,
            "resting_heart_rate": 56,
            "steps": 9000,
            "activity_score": 74,
        }
        metrics = normalizer.normalize("oura", raw, DATE, EMPTY_BASELINE)
        assert len(metrics) > 0
        names = {m.canonical_metric for m in metrics}
        assert "sleep_score" in names
        assert "readiness_score" in names
        assert "hrv_balance" in names

    def test_unknown_source_returns_empty(self):
        result = normalizer.normalize("unknown_device_xyz", {"steps": 1000}, DATE, {})
        assert result == []

    def test_stub_adapter_returns_empty_gracefully(self):
        """Whoop/Garmin/Fitbit stubs raise NotImplementedError; normalizer catches it."""
        for source in ("whoop", "garmin", "fitbit"):
            result = normalizer.normalize(source, {"steps": 1000}, DATE, {})
            assert result == [], f"Expected empty for stub {source}"

    def test_all_output_canonical_names_valid(self):
        raw = {
            "sleep_score": 80,
            "steps": 7500,
            "activity_score": 70,
            "readiness_score": 75,
            "hrv_balance": 0.5,
            "resting_heart_rate": 60,
        }
        for m in normalizer.normalize("oura", raw, DATE, EMPTY_BASELINE):
            assert m.canonical_metric in CANONICAL_METRICS

    def test_source_field_matches_input(self):
        raw = {"steps": 8000, "resting_heart_rate": 60}
        for source in ("oura", "healthkit", "health_connect"):
            for m in normalizer.normalize(source, raw, DATE, EMPTY_BASELINE):
                assert m.source == source


class TestHealthNormalizerCompositeIntegration:
    def test_apple_health_activity_score_computed(self):
        """Apple Health has no native activity_score; it should be computed."""
        raw = {"steps": 9_000, "active_min": 40, "active_calories_kcal": 500}
        metrics = normalizer.normalize("healthkit", raw, DATE, EMPTY_BASELINE)
        names = {m.canonical_metric for m in metrics}
        assert "activity_score" in names
        composite = next(m for m in metrics if m.canonical_metric == "activity_score")
        assert composite.source_type == SourceType.COMPUTED_COMPOSITE

    def test_oura_activity_score_not_overridden_by_composite(self):
        """Oura provides activity_score natively; composite should not overwrite."""
        raw = {"activity_score": 74, "steps": 9000}
        metrics = normalizer.normalize("oura", raw, DATE, EMPTY_BASELINE)
        activity_metrics = [
            m for m in metrics if m.canonical_metric == "activity_score"
        ]
        assert len(activity_metrics) == 1
        assert activity_metrics[0].source_type == SourceType.DIRECT
        assert activity_metrics[0].value == 74.0

    def test_sleep_score_computed_for_healthkit(self):
        raw = {"sleep_hours": 7.5, "workout_minutes": 30}
        # sleep_hours → sleep_duration_min; normalizer should then compute sleep_score
        metrics = normalizer.normalize("healthkit", raw, DATE, EMPTY_BASELINE)
        names = {m.canonical_metric for m in metrics}
        assert "sleep_score" in names

    def test_hrv_balance_derived_from_hrv_ms_for_healthkit(self):
        raw = {"hrv_sdnn_ms": 50.0, "steps": 7000}
        baseline = {"hrv_ms": {"mean_30d": 42.0, "std_30d": 8.0, "n": 20}}
        metrics = normalizer.normalize("healthkit", raw, DATE, baseline)
        names = {m.canonical_metric for m in metrics}
        assert "hrv_ms" in names
        assert "hrv_balance" in names
        hrv_bal = next(m for m in metrics if m.canonical_metric == "hrv_balance")
        assert hrv_bal.source_type == SourceType.DERIVED


class TestNormalizeMultiSource:
    def test_source_priority_oura_wins_over_healthkit(self):
        days_data = {
            DATE: {
                "oura": {"sleep_score": 82, "resting_heart_rate": 56},
                "healthkit": {"resting_heart_rate": 62},  # same metric, different value
            }
        }
        result = normalizer.normalize_multi_source(days_data, EMPTY_BASELINE)
        day = result[DATE]
        # Oura has higher priority → should win for resting_hr_bpm
        assert day["resting_hr_bpm"].source == "oura"
        assert day["resting_hr_bpm"].value == 56.0

    def test_healthkit_supplements_oura(self):
        """Metrics oura doesn't have but healthkit does should still appear."""
        days_data = {
            DATE: {
                "oura": {"sleep_score": 82},
                "healthkit": {"steps": 8430, "vo2_max": 42.5},
            }
        }
        result = normalizer.normalize_multi_source(days_data, EMPTY_BASELINE)
        day = result[DATE]
        assert "sleep_score" in day
        assert day["sleep_score"].source == "oura"
        assert "steps" in day
        assert day["steps"].source == "healthkit"

    def test_multi_day_result_has_correct_dates(self):
        days_data = {
            "2026-03-17": {"oura": {"sleep_score": 78, "steps": 7000}},
            "2026-03-18": {"oura": {"sleep_score": 84, "steps": 9000}},
        }
        result = normalizer.normalize_multi_source(days_data, EMPTY_BASELINE)
        assert "2026-03-17" in result
        assert "2026-03-18" in result
        assert result["2026-03-17"]["sleep_score"].value == 78.0
        assert result["2026-03-18"]["sleep_score"].value == 84.0

    def test_empty_days_data_returns_empty(self):
        result = normalizer.normalize_multi_source({}, EMPTY_BASELINE)
        assert result == {}


class TestToFlatDict:
    def test_converts_correctly(self):
        days_data = {DATE: {"oura": {"sleep_score": 80, "steps": 7000}}}
        result = normalizer.normalize_multi_source(days_data, EMPTY_BASELINE)
        flat = HealthNormalizer.to_flat_dict(result[DATE])
        assert flat["sleep_score"] == 80.0
        assert flat["steps"] == 7000.0


class TestSourcePriority:
    def test_oura_highest_priority(self):
        assert SOURCE_PRIORITY["oura"] > SOURCE_PRIORITY["healthkit"]
        assert SOURCE_PRIORITY["oura"] > SOURCE_PRIORITY["health_connect"]

    def test_clinical_high_priority(self):
        assert SOURCE_PRIORITY["clinical"] >= SOURCE_PRIORITY["healthkit"]

    def test_dexcom_high_for_glucose(self):
        assert SOURCE_PRIORITY["dexcom"] > SOURCE_PRIORITY["healthkit"]
