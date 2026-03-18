"""Tests for common.metrics.persistence and the health_data.py wiring helpers."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from common.metrics.adapters.base import NormalizedMetric
from common.metrics.registry import SourceType
from common.metrics.persistence import _to_row, persist_normalized_metrics


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

USER_ID = "00000000-0000-0000-0000-000000000001"
DATE = "2026-03-18"
NOW = "2026-03-18T10:00:00+00:00"


def _make_metric(
    canonical: str = "steps",
    value: float = 8000.0,
    source: str = "healthkit",
    source_type: SourceType = SourceType.DIRECT,
    raw_metric: str = "steps",
    confidence: float = 1.0,
) -> NormalizedMetric:
    return NormalizedMetric(
        canonical_metric=canonical,
        value=value,
        source=source,
        source_type=source_type,
        raw_metric=raw_metric,
        confidence=confidence,
        baseline_used=None,
    )


# ---------------------------------------------------------------------------
# _to_row helper
# ---------------------------------------------------------------------------


class TestToRow:
    def test_direct_metric_row(self):
        m = _make_metric("steps", 8000.0, "healthkit", SourceType.DIRECT, "steps", 1.0)
        row = _to_row(USER_ID, DATE, m, NOW)

        assert row["user_id"] == USER_ID
        assert row["date"] == DATE
        assert row["canonical_metric"] == "steps"
        assert row["value"] == 8000.0
        assert row["source"] == "healthkit"
        assert row["source_type"] == "direct"
        assert row["raw_metric"] == "steps"
        assert row["confidence"] == 1.0
        assert row["computed_at"] == NOW

    def test_derived_metric_row(self):
        m = _make_metric(
            "body_temp_deviation_c",
            0.3,
            "healthkit",
            SourceType.DERIVED,
            "body_temperature",
            0.70,
        )
        row = _to_row(USER_ID, DATE, m, NOW)
        assert row["source_type"] == "derived"
        assert row["confidence"] == 0.70
        assert row["raw_metric"] == "body_temperature"

    def test_composite_metric_row(self):
        m = _make_metric(
            "sleep_score",
            82.0,
            "healthkit",
            SourceType.COMPUTED_COMPOSITE,
            None,
            0.55,
        )
        row = _to_row(USER_ID, DATE, m, NOW)
        assert row["source_type"] == "computed_composite"
        assert row["raw_metric"] is None


# ---------------------------------------------------------------------------
# persist_normalized_metrics — credentials missing
# ---------------------------------------------------------------------------


class TestPersistNormalizedMetricsMissingCreds:
    @pytest.mark.asyncio
    async def test_returns_zero_when_no_url(self):
        metrics = [_make_metric()]
        result = await persist_normalized_metrics(
            USER_ID, DATE, metrics, supabase_url="", supabase_service_key="key"
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_key(self):
        metrics = [_make_metric()]
        result = await persist_normalized_metrics(
            USER_ID,
            DATE,
            metrics,
            supabase_url="https://example.supabase.co",
            supabase_service_key="",
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_zero_when_empty_metrics(self):
        result = await persist_normalized_metrics(
            USER_ID,
            DATE,
            [],
            supabase_url="https://example.supabase.co",
            supabase_service_key="key",
        )
        assert result == 0


# ---------------------------------------------------------------------------
# persist_normalized_metrics — HTTP success
# ---------------------------------------------------------------------------


def _mock_session(status: int, response_body):
    """Build a mock aiohttp.ClientSession that returns a fake response."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=response_body)
    mock_resp.text = AsyncMock(return_value=str(response_body))
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    return mock_session


class TestPersistNormalizedMetricsHTTP:
    @pytest.mark.asyncio
    async def test_success_returns_row_count(self):
        metrics = [
            _make_metric("steps", 8000.0),
            _make_metric("sleep_duration_min", 450.0),
        ]
        fake_rows = [{"id": "1"}, {"id": "2"}]

        with patch("aiohttp.ClientSession", return_value=_mock_session(201, fake_rows)):
            result = await persist_normalized_metrics(
                USER_ID,
                DATE,
                metrics,
                supabase_url="https://example.supabase.co",
                supabase_service_key="test-key",
            )
        assert result == 2

    @pytest.mark.asyncio
    async def test_http_200_also_accepted(self):
        metrics = [_make_metric()]
        fake_rows = [{"id": "1"}]

        with patch("aiohttp.ClientSession", return_value=_mock_session(200, fake_rows)):
            result = await persist_normalized_metrics(
                USER_ID,
                DATE,
                metrics,
                supabase_url="https://example.supabase.co",
                supabase_service_key="test-key",
            )
        assert result == 1

    @pytest.mark.asyncio
    async def test_http_error_returns_zero(self):
        metrics = [_make_metric()]

        with patch("aiohttp.ClientSession", return_value=_mock_session(500, "error")):
            result = await persist_normalized_metrics(
                USER_ID,
                DATE,
                metrics,
                supabase_url="https://example.supabase.co",
                supabase_service_key="test-key",
            )
        assert result == 0

    @pytest.mark.asyncio
    async def test_non_list_response_falls_back_to_metric_count(self):
        """When Supabase returns a dict (not list), use len(rows) as accepted count."""
        metrics = [_make_metric("steps"), _make_metric("resting_hr_bpm")]
        # Non-list response
        with patch(
            "aiohttp.ClientSession", return_value=_mock_session(201, {"count": 2})
        ):
            result = await persist_normalized_metrics(
                USER_ID,
                DATE,
                metrics,
                supabase_url="https://example.supabase.co",
                supabase_service_key="test-key",
            )
        assert result == 2  # falls back to len(rows)

    @pytest.mark.asyncio
    async def test_exception_returns_zero(self):
        metrics = [_make_metric()]

        with patch("aiohttp.ClientSession", side_effect=Exception("network down")):
            result = await persist_normalized_metrics(
                USER_ID,
                DATE,
                metrics,
                supabase_url="https://example.supabase.co",
                supabase_service_key="test-key",
            )
        assert result == 0


# ---------------------------------------------------------------------------
# _build_raw_day (imported from health_data ingest module)
# ---------------------------------------------------------------------------

# We test _build_raw_day separately because it has no I/O — pure dict logic.


class TestBuildRawDay:
    def _dp(self, metric_type, date, value_json):
        """Minimal HealthDataPoint-like object."""
        obj = MagicMock()
        obj.metric_type = metric_type
        obj.date = date
        obj.value_json = value_json
        return obj

    def setup_method(self):
        # Import here to avoid pulling in FastAPI at module level in tests
        from apps.mvp_api.api.health_data import _build_raw_day  # noqa: PLC0415

        self._build_raw_day = _build_raw_day

    def test_healthkit_steps_remapped(self):
        dps = [self._dp("steps", "2026-03-18", {"steps": 8000})]
        result = self._build_raw_day("healthkit", dps)
        assert result["2026-03-18"]["steps"] == 8000.0

    def test_healthkit_sleep_hours_remapped(self):
        dps = [self._dp("sleep", "2026-03-18", {"hours": 7.5})]
        result = self._build_raw_day("healthkit", dps)
        assert result["2026-03-18"]["sleep_hours"] == 7.5

    def test_healthkit_hrv_sdnn_remapped(self):
        dps = [self._dp("hrv_sdnn", "2026-03-18", {"ms": 44.0})]
        result = self._build_raw_day("healthkit", dps)
        assert result["2026-03-18"]["hrv_sdnn_ms"] == 44.0

    def test_health_connect_hrv_rmssd_remapped(self):
        dps = [self._dp("hrv_rmssd", "2026-03-18", {"ms": 38.0})]
        result = self._build_raw_day("health_connect", dps)
        assert result["2026-03-18"]["hrv_rmssd_ms"] == 38.0

    def test_health_connect_stress_score(self):
        dps = [self._dp("stress_score", "2026-03-18", {"score": 34.0})]
        result = self._build_raw_day("health_connect", dps)
        assert result["2026-03-18"]["stress_score"] == 34.0

    def test_dexcom_time_in_range(self):
        dps = [self._dp("time_in_range", "2026-03-18", {"pct": 89.0})]
        result = self._build_raw_day("dexcom", dps)
        assert result["2026-03-18"]["time_in_range_pct"] == 89.0

    def test_multiple_metrics_same_date(self):
        dps = [
            self._dp("steps", "2026-03-18", {"steps": 9000}),
            self._dp("sleep", "2026-03-18", {"hours": 6.5}),
            self._dp("resting_heart_rate", "2026-03-18", {"bpm": 58}),
        ]
        result = self._build_raw_day("healthkit", dps)
        day = result["2026-03-18"]
        assert day["steps"] == 9000.0
        assert day["sleep_hours"] == 6.5
        assert day["resting_heart_rate"] == 58.0

    def test_multiple_dates(self):
        dps = [
            self._dp("steps", "2026-03-17", {"steps": 7000}),
            self._dp("steps", "2026-03-18", {"steps": 9000}),
        ]
        result = self._build_raw_day("healthkit", dps)
        assert len(result) == 2
        assert result["2026-03-17"]["steps"] == 7000.0
        assert result["2026-03-18"]["steps"] == 9000.0

    def test_unknown_source_uses_fallback(self):
        """Unregistered source falls back to extracting first numeric from value_json."""
        dps = [self._dp("custom_metric", "2026-03-18", {"value": 42.5})]
        result = self._build_raw_day("unknown_device", dps)
        assert result["2026-03-18"]["custom_metric"] == 42.5

    def test_non_numeric_value_json_skipped(self):
        dps = [self._dp("steps", "2026-03-18", {"steps": "not_a_number"})]
        result = self._build_raw_day("healthkit", dps)
        # "not_a_number" can't be float → key absent
        assert "steps" not in result.get("2026-03-18", {})

    def test_empty_data_points_returns_empty(self):
        result = self._build_raw_day("healthkit", [])
        assert result == {}
