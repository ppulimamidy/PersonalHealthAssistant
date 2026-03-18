"""Tests for common.metrics.registry."""

import pytest
from common.metrics.registry import (
    CANONICAL_METRICS,
    MetricCategory,
    SourceType,
    get_metric,
    is_known,
    metrics_by_category,
)


class TestCanonicalMetrics:
    def test_all_entries_have_required_fields(self):
        for name, metric in CANONICAL_METRICS.items():
            assert metric.name == name, f"{name}: name mismatch"
            assert isinstance(metric.category, MetricCategory)
            assert metric.unit
            assert metric.description

    def test_known_metrics_exist(self):
        expected = [
            "sleep_score",
            "sleep_duration_min",
            "deep_sleep_min",
            "rem_sleep_min",
            "sleep_efficiency_pct",
            "readiness_score",
            "hrv_ms",
            "hrv_balance",
            "resting_hr_bpm",
            "body_temp_deviation_c",
            "activity_score",
            "steps",
            "active_calories_kcal",
            "active_min",
            "vo2_max",
            "avg_glucose_mgdl",
            "time_in_range_pct",
            "glucose_variability_cv",
            "postprandial_peak_mgdl",
            "postprandial_auc",
            "postprandial_excursion_mgdl",
            "weight_kg",
            "body_fat_pct",
            "blood_pressure_systolic_mmhg",
            "symptom_severity_avg",
            "symptom_count",
        ]
        for name in expected:
            assert name in CANONICAL_METRICS, f"Missing canonical metric: {name}"

    def test_get_metric_returns_correct(self):
        m = get_metric("hrv_ms")
        assert m is not None
        assert m.category == MetricCategory.RECOVERY
        assert m.unit == "ms"

    def test_get_metric_unknown_returns_none(self):
        assert get_metric("not_a_metric") is None

    def test_is_known(self):
        assert is_known("steps")
        assert not is_known("whoop_proprietary_field")

    def test_metrics_by_category(self):
        sleep = metrics_by_category(MetricCategory.SLEEP)
        assert "sleep_score" in sleep
        assert "sleep_duration_min" in sleep
        assert "hrv_ms" not in sleep

        glucose = metrics_by_category(MetricCategory.GLUCOSE)
        assert "avg_glucose_mgdl" in glucose
        assert "postprandial_auc" in glucose

    def test_value_ranges_are_valid_when_present(self):
        for name, metric in CANONICAL_METRICS.items():
            if metric.value_range is not None:
                lo, hi = metric.value_range
                assert lo < hi, f"{name}: invalid range {metric.value_range}"

    def test_source_type_enum_values(self):
        assert SourceType.DIRECT == "direct"
        assert SourceType.DERIVED == "derived"
        assert SourceType.COMPUTED_COMPOSITE == "computed_composite"
