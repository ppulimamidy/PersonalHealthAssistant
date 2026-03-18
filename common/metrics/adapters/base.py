"""
Base classes for device adapters.

All device adapters inherit from ``DeviceAdapter`` and register themselves
with ``AdapterRegistry``.  The correlation engine calls
``AdapterRegistry.get(source)`` to retrieve the right adapter for any
connected device.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional, Type

from common.metrics.registry import SourceType


# ---------------------------------------------------------------------------
# Data transfer object
# ---------------------------------------------------------------------------


@dataclass
class NormalizedMetric:
    """
    One canonical metric value for one day from one source.

    Attributes:
        canonical_metric:  Key from ``CANONICAL_METRICS`` (e.g. ``"hrv_ms"``).
        value:             Numeric value in the canonical unit.
        source:            Data source name matching ``native_health_data.source``
                           (e.g. ``"oura"``, ``"healthkit"``).
        source_type:       How the value was obtained (direct / derived /
                           computed_composite).
        raw_metric:        Original field name on the device before mapping.
                           Preserved for debugging and auditability.
        confidence:        0–1 float; 1.0 = directly measured, 0.7 = derived,
                           0.5–0.6 = computed composite.
        baseline_used:     Snapshot of the baseline parameters used when
                           computing a derived or composite metric.  None for
                           direct measurements.
    """

    canonical_metric: str
    value: float
    source: str
    source_type: SourceType
    raw_metric: Optional[str] = None
    confidence: float = 1.0
    baseline_used: Optional[dict] = field(default=None)


# ---------------------------------------------------------------------------
# Abstract adapter
# ---------------------------------------------------------------------------


class DeviceAdapter(ABC):
    """
    Abstract base class for all device adapters.

    Subclasses map one day of raw, device-specific data to a list of
    ``NormalizedMetric`` objects using the canonical metric names defined in
    ``common.metrics.registry``.

    Contract
    --------
    * ``source_name`` must match the ``source`` column value in
      ``native_health_data`` (e.g. ``"oura"``, ``"healthkit"``).
    * ``to_canonical`` must be pure / side-effect-free.
    * Missing or zero values should be omitted from the output list rather
      than returned as 0.0, so the engine can distinguish "not measured"
      from "measured as zero".
    * The adapter must not perform I/O or database access.
    """

    source_name: ClassVar[str]

    @abstractmethod
    def to_canonical(
        self,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        """
        Map one day of raw device data to canonical metrics.

        Parameters
        ----------
        raw_day:
            Flat ``{field_name: scalar_value}`` dict.  Keys are
            device-specific; values are already extracted scalars
            (not nested JSON).

            Examples by source:
              oura:
                {"sleep_score": 82, "total_sleep_hours": 7.1,
                 "hrv_balance": 1.2, "resting_heart_rate": 56, ...}
              healthkit / health_connect:
                {"steps": 8430, "sleep_hours": 6.9,
                 "resting_heart_rate": 58, "hrv_sdnn_ms": 44, ...}
              dexcom:
                {"avg_glucose_mgdl": 105.3, "peak_glucose_mgdl": 178,
                 "time_in_range_pct": 89.0, "glucose_variability_cv": 18.2,
                 "glucose_spikes_count": 0}

        date:
            ISO date string, e.g. ``"2026-03-18"``.

        user_baseline:
            Per-user rolling statistics keyed by canonical metric name::

                {
                  "hrv_ms":            {"mean_30d": 42.1, "std_30d": 8.3, "n": 28},
                  "body_temperature_c": {"mean_30d": 36.61, "std_30d": 0.19, "n": 30},
                }

            Used by adapters / composite_scores to compute derived metrics
            (e.g. hrv_balance, body_temp_deviation_c).  May be empty if no
            baseline is available yet.

        Returns
        -------
        list[NormalizedMetric]
            One entry per canonical metric found in *raw_day*.
            Metrics absent from *raw_day* are omitted entirely.
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @classmethod
    def _f(cls, raw_day: dict, key: str) -> Optional[float]:
        """
        Extract a non-zero float from *raw_day[key]*.
        Returns None if the key is missing, None, or converts to 0.0.
        (Zero usually means "not measured" in health device data.)
        """
        val = raw_day.get(key)
        if val is None:
            return None
        try:
            f = float(val)
        except (TypeError, ValueError):
            return None
        return f if f != 0.0 else None

    @classmethod
    def _f_allow_zero(cls, raw_day: dict, key: str) -> Optional[float]:
        """
        Like ``_f`` but allows 0.0 as a valid value.
        Use for metrics where zero is meaningful (e.g. sleep disturbances,
        glucose_spikes_count, body_temp_deviation_c).
        """
        val = raw_day.get(key)
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _direct(
        cls,
        canonical: str,
        value: float,
        source: str,
        raw_metric: Optional[str] = None,
    ) -> NormalizedMetric:
        """Convenience constructor for a directly-measured metric."""
        return NormalizedMetric(
            canonical_metric=canonical,
            value=value,
            source=source,
            source_type=SourceType.DIRECT,
            raw_metric=raw_metric or canonical,
            confidence=1.0,
        )

    @classmethod
    def _derived(
        cls,
        canonical: str,
        value: float,
        source: str,
        raw_metric: str,
        confidence: float,
        baseline_used: Optional[dict] = None,
    ) -> NormalizedMetric:
        """Convenience constructor for a derived metric."""
        return NormalizedMetric(
            canonical_metric=canonical,
            value=value,
            source=source,
            source_type=SourceType.DERIVED,
            raw_metric=raw_metric,
            confidence=confidence,
            baseline_used=baseline_used,
        )

    @classmethod
    def _composite(
        cls,
        canonical: str,
        value: float,
        source: str,
        confidence: float,
        baseline_used: Optional[dict] = None,
    ) -> NormalizedMetric:
        """Convenience constructor for a computed-composite metric."""
        return NormalizedMetric(
            canonical_metric=canonical,
            value=value,
            source=source,
            source_type=SourceType.COMPUTED_COMPOSITE,
            raw_metric=None,
            confidence=confidence,
            baseline_used=baseline_used,
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class AdapterRegistry:
    """
    Maps source names to registered adapter instances.

    Usage::

        @AdapterRegistry.register
        class OuraAdapter(DeviceAdapter):
            source_name = "oura"
            ...

        adapter = AdapterRegistry.get("oura")
        metrics = adapter.to_canonical(raw, date, baseline)
    """

    _registry: Dict[str, DeviceAdapter] = {}

    @classmethod
    def register(cls, adapter_cls: Type[DeviceAdapter]) -> Type[DeviceAdapter]:
        """
        Class decorator / explicit call that instantiates and registers an adapter.

        Can be used as a decorator::

            @AdapterRegistry.register
            class MyAdapter(DeviceAdapter): ...

        Or called explicitly::

            AdapterRegistry.register(MyAdapter)
        """
        instance = adapter_cls()
        cls._registry[instance.source_name] = instance
        return adapter_cls

    @classmethod
    def get(cls, source: str) -> Optional[DeviceAdapter]:
        """Return the adapter for *source*, or None if not registered."""
        return cls._registry.get(source)

    @classmethod
    def all_sources(cls) -> List[str]:
        """Return all registered source names."""
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, source: str) -> bool:
        return source in cls._registry
