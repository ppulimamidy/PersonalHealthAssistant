"""Tests for device adapters."""

import pytest
from common.metrics.adapters.base import AdapterRegistry, NormalizedMetric
from common.metrics.registry import SourceType, CANONICAL_METRICS

# Import adapters package to trigger registration
import common.metrics.adapters  # noqa: F401

DATE = "2026-03-18"
EMPTY_BASELINE: dict = {}


# ---------------------------------------------------------------------------
# AdapterRegistry
# ---------------------------------------------------------------------------


class TestAdapterRegistry:
    def test_all_expected_sources_registered(self):
        for source in (
            "oura",
            "healthkit",
            "health_connect",
            "dexcom",
            "whoop",
            "garmin",
            "fitbit",
        ):
            assert AdapterRegistry.is_registered(source), f"Not registered: {source}"

    def test_get_unknown_returns_none(self):
        assert AdapterRegistry.get("unknown_device_xyz") is None

    def test_all_sources_returns_list(self):
        sources = AdapterRegistry.all_sources()
        assert isinstance(sources, list)
        assert len(sources) >= 4


# ---------------------------------------------------------------------------
# NormalizedMetric shape helpers
# ---------------------------------------------------------------------------


def _names(metrics: list[NormalizedMetric]) -> set[str]:
    return {m.canonical_metric for m in metrics}


def _val(metrics: list[NormalizedMetric], name: str) -> float:
    for m in metrics:
        if m.canonical_metric == name:
            return m.value
    raise KeyError(name)


def _metric(metrics: list[NormalizedMetric], name: str) -> NormalizedMetric:
    for m in metrics:
        if m.canonical_metric == name:
            return m
    raise KeyError(name)


def _all_canonical_names_valid(metrics: list[NormalizedMetric]):
    for m in metrics:
        assert (
            m.canonical_metric in CANONICAL_METRICS
        ), f"Adapter produced unknown canonical metric: {m.canonical_metric}"


# ---------------------------------------------------------------------------
# Oura adapter
# ---------------------------------------------------------------------------


class TestOuraAdapter:
    @pytest.fixture
    def adapter(self):
        return AdapterRegistry.get("oura")

    @pytest.fixture
    def full_raw(self):
        return {
            "sleep_score": 82,
            "sleep_efficiency": 87,
            "total_sleep_hours": 7.5,
            "deep_sleep_hours": 1.4,
            "steps": 9_200,
            "active_calories": 450,
            "activity_score": 74,
            "workout_minutes": 40,
            "readiness_score": 79,
            "hrv_balance": 1.2,
            "recovery_index": 68,
            "resting_heart_rate": 56,
            "temperature_deviation": -0.1,
            "respiratory_rate": 14.8,
            "spo2": 97.5,
        }

    def test_full_raw_produces_expected_metrics(self, adapter, full_raw):
        metrics = adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE)
        names = _names(metrics)

        assert "sleep_score" in names
        assert "sleep_efficiency_pct" in names
        assert "sleep_duration_min" in names
        assert "deep_sleep_min" in names
        assert "steps" in names
        assert "active_calories_kcal" in names
        assert "activity_score" in names
        assert "active_min" in names
        assert "readiness_score" in names
        assert "hrv_balance" in names
        assert "recovery_index" in names
        assert "resting_hr_bpm" in names
        assert "body_temp_deviation_c" in names
        assert "respiratory_rate_bpm" in names
        assert "spo2_pct" in names

    def test_hours_converted_to_minutes(self, adapter, full_raw):
        metrics = adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE)
        assert _val(metrics, "sleep_duration_min") == pytest.approx(7.5 * 60, abs=0.1)
        assert _val(metrics, "deep_sleep_min") == pytest.approx(1.4 * 60, abs=0.1)

    def test_all_canonical_names_valid(self, adapter, full_raw):
        _all_canonical_names_valid(adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE))

    def test_direct_source_type(self, adapter, full_raw):
        for m in adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE):
            assert m.source_type == SourceType.DIRECT
            assert m.confidence == 1.0
            assert m.source == "oura"

    def test_zero_sleep_score_omitted(self, adapter):
        raw = {"sleep_score": 0, "steps": 5000}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "sleep_score" not in names
        assert "steps" in names

    def test_hrv_balance_zero_included(self, adapter):
        """hrv_balance = 0.0 is a valid value (exactly at baseline)."""
        raw = {"hrv_balance": 0.0, "sleep_score": 75}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "hrv_balance" in names

    def test_temperature_deviation_zero_included(self, adapter):
        """temperature_deviation = 0.0 means exactly at baseline — valid."""
        raw = {"temperature_deviation": 0.0, "sleep_score": 75}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "body_temp_deviation_c" in names

    def test_empty_raw_returns_empty(self, adapter):
        assert adapter.to_canonical({}, DATE, EMPTY_BASELINE) == []

    def test_partial_raw(self, adapter):
        raw = {"readiness_score": 71, "resting_heart_rate": 58}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "readiness_score" in names
        assert "resting_hr_bpm" in names
        assert "sleep_score" not in names


# ---------------------------------------------------------------------------
# Apple Health adapter
# ---------------------------------------------------------------------------


class TestAppleHealthAdapter:
    @pytest.fixture
    def adapter(self):
        return AdapterRegistry.get("healthkit")

    @pytest.fixture
    def full_raw(self):
        return {
            "steps": 8_430,
            "active_calories_kcal": 480,
            "workout_minutes": 35,
            "vo2_max": 42.5,
            "sleep_hours": 6.9,
            "resting_heart_rate": 58,
            "hrv_sdnn_ms": 44,
            "spo2_pct": 97,
            "respiratory_rate": 14.5,
            "weight_kg": 72.4,
            "body_fat_pct": 22.1,
            "blood_pressure_systolic_mmhg": 118,
            "blood_pressure_diastolic_mmhg": 76,
            "blood_glucose_mgdl": 105,
        }

    def test_full_raw_produces_expected_metrics(self, adapter, full_raw):
        names = _names(adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE))
        assert "steps" in names
        assert "active_calories_kcal" in names
        assert "active_min" in names
        assert "vo2_max" in names
        assert "sleep_duration_min" in names
        assert "resting_hr_bpm" in names
        assert "hrv_ms" in names
        assert "spo2_pct" in names
        assert "respiratory_rate_bpm" in names
        assert "weight_kg" in names
        assert "body_fat_pct" in names
        assert "blood_pressure_systolic_mmhg" in names
        assert "blood_pressure_diastolic_mmhg" in names
        assert "avg_glucose_mgdl" in names

    def test_hrv_raw_metric_is_sdnn(self, adapter, full_raw):
        m = _metric(adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE), "hrv_ms")
        assert m.raw_metric == "hrv_sdnn"
        assert m.source_type == SourceType.DIRECT

    def test_sleep_hours_to_minutes(self, adapter, full_raw):
        metrics = adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE)
        assert _val(metrics, "sleep_duration_min") == pytest.approx(6.9 * 60, abs=0.1)

    def test_all_canonical_names_valid(self, adapter, full_raw):
        _all_canonical_names_valid(adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE))

    def test_temp_deviation_not_computed_without_baseline(self, adapter):
        """No baseline → body_temp_deviation_c should be absent."""
        raw = {"body_temperature_c": 36.7, "steps": 5000}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "body_temperature_c" in names  # absolute temp stored
        assert "body_temp_deviation_c" not in names  # deviation needs baseline

    def test_temp_deviation_computed_with_adequate_baseline(self, adapter):
        """With ≥7 days baseline, body_temp_deviation_c should be derived."""
        raw = {"body_temperature_c": 36.9}
        baseline = {"body_temperature_c": {"mean_30d": 36.6, "std_30d": 0.18, "n": 20}}
        metrics = adapter.to_canonical(raw, DATE, baseline)
        names = _names(metrics)
        assert "body_temp_deviation_c" in names
        dev = _metric(metrics, "body_temp_deviation_c")
        assert dev.source_type == SourceType.DERIVED
        assert dev.confidence == pytest.approx(0.70)
        assert dev.value == pytest.approx(0.3, abs=0.01)

    def test_temp_deviation_not_computed_insufficient_baseline(self, adapter):
        """Fewer than 7 baseline days → no deviation."""
        raw = {"body_temperature_c": 36.9}
        baseline = {"body_temperature_c": {"mean_30d": 36.6, "n": 5}}
        names = _names(adapter.to_canonical(raw, DATE, baseline))
        assert "body_temp_deviation_c" not in names

    def test_source_is_healthkit(self, adapter, full_raw):
        for m in adapter.to_canonical(full_raw, DATE, EMPTY_BASELINE):
            assert m.source == "healthkit"


# ---------------------------------------------------------------------------
# Health Connect adapter
# ---------------------------------------------------------------------------


class TestHealthConnectAdapter:
    @pytest.fixture
    def adapter(self):
        return AdapterRegistry.get("health_connect")

    def test_hrv_raw_metric_is_rmssd(self, adapter):
        """Health Connect reports RMSSD, not SDNN."""
        raw = {"hrv_rmssd_ms": 38.0, "steps": 7000}
        m = _metric(adapter.to_canonical(raw, DATE, EMPTY_BASELINE), "hrv_ms")
        assert m.raw_metric == "hrv_rmssd"

    def test_native_stress_score(self, adapter):
        """Health Connect has a native stress metric."""
        raw = {"stress_score": 34.0}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "stress_score" in names
        m = _metric(adapter.to_canonical(raw, DATE, EMPTY_BASELINE), "stress_score")
        assert m.source_type == SourceType.DIRECT

    def test_source_is_health_connect(self, adapter):
        raw = {"steps": 6000, "resting_heart_rate": 60}
        for m in adapter.to_canonical(raw, DATE, EMPTY_BASELINE):
            assert m.source == "health_connect"

    def test_all_canonical_names_valid(self, adapter):
        raw = {
            "steps": 7000,
            "sleep_hours": 7.0,
            "resting_heart_rate": 62,
            "hrv_rmssd_ms": 38,
            "spo2_pct": 97,
            "respiratory_rate": 15,
            "active_calories_kcal": 400,
            "workout_minutes": 30,
        }
        _all_canonical_names_valid(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))


# ---------------------------------------------------------------------------
# Dexcom adapter
# ---------------------------------------------------------------------------


class TestDexcomAdapter:
    @pytest.fixture
    def adapter(self):
        return AdapterRegistry.get("dexcom")

    def test_full_daily_aggregates(self, adapter):
        raw = {
            "avg_glucose_mgdl": 105.3,
            "peak_glucose_mgdl": 178.0,
            "time_in_range_pct": 89.0,
            "glucose_variability_cv": 18.2,
            "glucose_spikes_count": 0.0,
        }
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "avg_glucose_mgdl" in names
        assert "peak_glucose_mgdl" in names
        assert "time_in_range_pct" in names
        assert "glucose_variability_cv" in names
        assert "glucose_spikes_count" in names

    def test_zero_spikes_count_included(self, adapter):
        """glucose_spikes_count = 0 is a valid and meaningful value."""
        raw = {"avg_glucose_mgdl": 100.0, "glucose_spikes_count": 0.0}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "glucose_spikes_count" in names

    def test_zero_tir_included(self, adapter):
        """time_in_range_pct = 0 is valid (100% out of range)."""
        raw = {"avg_glucose_mgdl": 250.0, "time_in_range_pct": 0.0}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "time_in_range_pct" in names

    def test_fallback_blood_glucose(self, adapter):
        """Single blood_glucose reading maps to avg_glucose_mgdl."""
        raw = {"blood_glucose_mgdl": 112.0}
        names = _names(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))
        assert "avg_glucose_mgdl" in names

    def test_all_canonical_names_valid(self, adapter):
        raw = {
            "avg_glucose_mgdl": 105.0,
            "peak_glucose_mgdl": 170.0,
            "time_in_range_pct": 85.0,
            "glucose_variability_cv": 22.0,
            "glucose_spikes_count": 1.0,
        }
        _all_canonical_names_valid(adapter.to_canonical(raw, DATE, EMPTY_BASELINE))

    def test_source_is_dexcom(self, adapter):
        raw = {"avg_glucose_mgdl": 108.0}
        for m in adapter.to_canonical(raw, DATE, EMPTY_BASELINE):
            assert m.source == "dexcom"


# ---------------------------------------------------------------------------
# Stub adapters raise NotImplementedError
# ---------------------------------------------------------------------------


class TestStubAdapters:
    @pytest.mark.parametrize("source", ["whoop", "garmin", "fitbit"])
    def test_stub_raises_not_implemented(self, source):
        adapter = AdapterRegistry.get(source)
        assert adapter is not None, f"Stub adapter {source} not registered"
        with pytest.raises(NotImplementedError):
            adapter.to_canonical({"steps": 1000}, DATE, EMPTY_BASELINE)
