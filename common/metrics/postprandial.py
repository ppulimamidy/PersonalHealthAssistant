"""
Track B: Postprandial Glucose Analysis.

Pure computation module — no I/O.

Activates when: raw CGM readings are present AND meal logs have timestamps.
Falls back gracefully to daily-aggregate correlations when only daily glucose
data is available (e.g. fingerstick readings rather than a CGM).

Typical usage
-------------
    from common.metrics.postprandial import PostprandialAnalyzer, MealEntry, GlucoseReading
    from datetime import datetime

    analyzer = PostprandialAnalyzer()
    metrics = analyzer.analyze(glucose_readings, meal_entries)
    series  = analyzer.to_meal_series(metrics)  # {metric: [values, ...], ...}

Per-meal algorithm
------------------
For each meal entry with a valid timestamp:

    pre_window  = readings in [meal_time - 30 min, meal_time]
    post_window = readings in [meal_time, meal_time + 120 min]

    if len(post_window) < MIN_READINGS:
        skip meal (insufficient CGM coverage)

    baseline  = mean(pre_window) if pre_window else first post_window reading
    peak      = max(post_window)
    excursion = peak - baseline
    auc       = trapezoid_integrate(post_window)
    t_to_peak = time(argmax) - meal_time  (minutes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GlucoseReading:
    """A single CGM or fingerstick glucose reading."""

    timestamp: datetime  # tz-aware preferred; naive treated as UTC
    mg_dl: float


@dataclass(frozen=True)
class MealEntry:
    """One logged meal with nutrient data and an exact timestamp."""

    meal_id: str
    timestamp: datetime  # tz-aware preferred
    total_carbs_g: float = 0.0
    total_fiber_g: float = 0.0
    total_fat_g: float = 0.0
    total_protein_g: float = 0.0
    total_calories: float = 0.0
    glycemic_load_est: float = 0.0  # carbs - fiber (rough proxy)


@dataclass
class PostprandialMetrics:
    """Computed postprandial response for one meal."""

    meal_id: str
    meal_date: str  # YYYY-MM-DD
    meal_time_of_day: str  # 'morning' | 'afternoon' | 'evening' | 'late_night'

    # Glucose metrics (mg/dL)
    baseline_glucose: float
    postprandial_peak_mgdl: float
    postprandial_excursion_mgdl: float  # peak - baseline
    postprandial_auc: float  # mg·min/dL (trapezoidal)
    time_to_peak_min: float  # minutes from meal_time to peak

    # Meal macros (for correlation pairing)
    total_carbs_g: float
    total_fiber_g: float
    total_fat_g: float
    total_protein_g: float
    total_calories: float
    glycemic_load_est: float

    # Quality
    readings_used: int  # number of CGM readings in post-meal window


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _minutes_between(a: datetime, b: datetime) -> float:
    """Signed (b - a) in minutes."""
    return (b - a).total_seconds() / 60.0


def _trapezoid_auc(readings: List[Tuple[float, float]]) -> float:
    """
    Compute area under the curve via the trapezoidal rule.
    readings: [(time_min_offset, mg_dl), ...]  sorted by time offset.
    Returns mg·min/dL.
    """
    if len(readings) < 2:
        return 0.0
    auc = 0.0
    for i in range(len(readings) - 1):
        t0, g0 = readings[i]
        t1, g1 = readings[i + 1]
        dt = t1 - t0
        auc += 0.5 * (g0 + g1) * dt
    return round(auc, 2)


def _time_of_day_bucket(dt: datetime) -> str:
    hour = dt.hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "late_night"


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


class PostprandialAnalyzer:
    """
    Compute postprandial glucose metrics for each meal.

    Parameters
    ----------
    pre_window_min:
        Minutes before meal time to define the baseline glucose window.
    post_window_min:
        Minutes after meal time to track the glucose response.
    min_readings:
        Minimum CGM readings required in the post-meal window to produce
        a valid result for that meal.
    """

    def __init__(
        self,
        pre_window_min: int = 30,
        post_window_min: int = 120,
        min_readings: int = 3,
    ) -> None:
        self.pre_window_min = pre_window_min
        self.post_window_min = post_window_min
        self.min_readings = min_readings

    def analyze(
        self,
        glucose_readings: List[GlucoseReading],
        meal_entries: List[MealEntry],
    ) -> List[PostprandialMetrics]:
        """
        Compute postprandial metrics for each meal with sufficient CGM coverage.

        Meals with fewer than ``min_readings`` post-meal readings are silently
        skipped. The caller should check that the returned list is non-empty
        before using it — an empty list means Track B data is unavailable.
        """
        if not glucose_readings or not meal_entries:
            return []

        # Normalise timestamps to UTC, sort readings once
        readings_utc = sorted(
            [
                GlucoseReading(_ensure_utc(r.timestamp), r.mg_dl)
                for r in glucose_readings
            ],
            key=lambda r: r.timestamp,
        )

        results: List[PostprandialMetrics] = []

        for meal in meal_entries:
            meal_ts = _ensure_utc(meal.timestamp)

            pre_cutoff = meal_ts.timestamp() - self.pre_window_min * 60
            post_cutoff = meal_ts.timestamp() + self.post_window_min * 60

            pre_vals = [
                r.mg_dl
                for r in readings_utc
                if pre_cutoff <= r.timestamp.timestamp() <= meal_ts.timestamp()
            ]
            post_timed = [
                (
                    _minutes_between(meal_ts, r.timestamp),
                    r.mg_dl,
                )
                for r in readings_utc
                if meal_ts.timestamp() <= r.timestamp.timestamp() <= post_cutoff
            ]

            if len(post_timed) < self.min_readings:
                continue

            baseline = sum(pre_vals) / len(pre_vals) if pre_vals else post_timed[0][1]

            peak_mg_dl = max(g for _, g in post_timed)
            peak_idx = max(range(len(post_timed)), key=lambda i: post_timed[i][1])
            time_to_peak = post_timed[peak_idx][0]

            auc = _trapezoid_auc(post_timed)
            excursion = peak_mg_dl - baseline

            results.append(
                PostprandialMetrics(
                    meal_id=meal.meal_id,
                    meal_date=meal_ts.strftime("%Y-%m-%d"),
                    meal_time_of_day=_time_of_day_bucket(meal_ts),
                    baseline_glucose=round(baseline, 1),
                    postprandial_peak_mgdl=round(peak_mg_dl, 1),
                    postprandial_excursion_mgdl=round(excursion, 1),
                    postprandial_auc=auc,
                    time_to_peak_min=round(time_to_peak, 1),
                    total_carbs_g=meal.total_carbs_g,
                    total_fiber_g=meal.total_fiber_g,
                    total_fat_g=meal.total_fat_g,
                    total_protein_g=meal.total_protein_g,
                    total_calories=meal.total_calories,
                    glycemic_load_est=meal.glycemic_load_est,
                    readings_used=len(post_timed),
                )
            )

        return results

    def to_meal_series(
        self,
        metrics: List[PostprandialMetrics],
    ) -> Dict[str, List[Any]]:
        """
        Convert per-meal postprandial metrics into paired lists for correlation.

        Returns a dict of ``{field_name: [value, ...]}``.  Every list has the
        same length — one entry per meal in the same order as ``metrics``.

        Typical use: correlate ``excursion`` against ``total_carbs_g`` etc.
        by passing the two lists to ``_pearson_r`` or ``_spearman_r``.
        """
        if not metrics:
            return {}

        keys = [
            "postprandial_excursion_mgdl",
            "postprandial_peak_mgdl",
            "postprandial_auc",
            "time_to_peak_min",
            "baseline_glucose",
            "total_carbs_g",
            "total_fiber_g",
            "total_fat_g",
            "total_protein_g",
            "total_calories",
            "glycemic_load_est",
            "meal_date",
            "meal_time_of_day",
        ]
        series: Dict[str, List[Any]] = {k: [] for k in keys}
        for m in metrics:
            for k in keys:
                series[k].append(getattr(m, k))
        return series

    def meal_correlations(
        self,
        metrics: List[PostprandialMetrics],
    ) -> List[Dict[str, Any]]:
        """
        Convenience method: compute all nutrition→glucose correlation pairs
        from postprandial metrics and return them as raw correlation dicts
        (same shape as ``_one_correlation`` output in the correlation engine).

        Uses Pearson r. The caller is responsible for filtering by min_r / max_p.
        """
        from math import sqrt

        if len(metrics) < 3:
            return []

        series = self.to_meal_series(metrics)

        # nutrition inputs (x) → glucose outcomes (y)
        PAIRS: List[Tuple[str, str]] = [
            ("total_carbs_g", "postprandial_excursion_mgdl"),
            ("glycemic_load_est", "postprandial_excursion_mgdl"),
            ("total_fiber_g", "postprandial_excursion_mgdl"),
            ("total_fat_g", "postprandial_excursion_mgdl"),
            ("total_protein_g", "postprandial_excursion_mgdl"),
            ("total_carbs_g", "postprandial_peak_mgdl"),
            ("glycemic_load_est", "postprandial_peak_mgdl"),
            ("total_carbs_g", "time_to_peak_min"),
        ]

        LABELS: Dict[str, str] = {
            "total_carbs_g": "Carbs (g)",
            "glycemic_load_est": "Glycemic Load",
            "total_fiber_g": "Fiber (g)",
            "total_fat_g": "Fat (g)",
            "total_protein_g": "Protein (g)",
            "postprandial_excursion_mgdl": "Glucose Spike (mg/dL)",
            "postprandial_peak_mgdl": "Peak Glucose (mg/dL)",
            "time_to_peak_min": "Time to Peak (min)",
        }

        import uuid as _uuid

        results = []
        dates = series["meal_date"]

        for x_key, y_key in PAIRS:
            x_vals = series[x_key]
            y_vals = series[y_key]

            # Align (skip zeros in x unless it's fiber)
            pairs_xy = [
                (x, y, d)
                for x, y, d in zip(x_vals, y_vals, dates)
                if (x != 0 or x_key == "total_fiber_g") and y != 0
            ]
            if len(pairs_xy) < 3:
                continue

            xs = [p[0] for p in pairs_xy]
            ys = [p[1] for p in pairs_xy]
            ds = [p[2] for p in pairs_xy]

            n = len(xs)
            mx = sum(xs) / n
            my = sum(ys) / n
            cov = sum((xi - mx) * (yi - my) for xi, yi in zip(xs, ys))
            sx = sqrt(sum((xi - mx) ** 2 for xi in xs))
            sy = sqrt(sum((yi - my) ** 2 for yi in ys))
            if sx == 0 or sy == 0:
                continue
            r = max(-1.0, min(1.0, cov / (sx * sy)))

            # Approximate p-value
            if abs(r) >= 1.0:
                p = 0.0
            elif n <= 2:
                p = 1.0
            else:
                t_stat = r * sqrt((n - 2) / (1 - r * r))
                # Simple approximation via beta function identity
                x_beta = (n - 2) / ((n - 2) + t_stat * t_stat)
                try:
                    from math import lgamma, exp, log

                    a, b = (n - 2) / 2.0, 0.5
                    if 0 < x_beta < 1:
                        lbeta = lgamma(a) + lgamma(b) - lgamma(a + b)
                        front = exp(a * log(x_beta) + b * log(1 - x_beta) - lbeta) / a
                        p = max(0.0, min(1.0, front))
                    else:
                        p = 0.0 if x_beta <= 0 else 1.0
                except Exception:
                    p = 1.0

            abs_r = abs(r)
            strength = (
                "strong" if abs_r >= 0.7 else "moderate" if abs_r >= 0.5 else "weak"
            )
            direction = "positive" if r > 0 else "negative"

            results.append(
                {
                    "id": str(_uuid.uuid4()),
                    "metric_a": x_key,
                    "metric_a_label": LABELS.get(x_key, x_key),
                    "metric_b": y_key,
                    "metric_b_label": LABELS.get(y_key, y_key),
                    "correlation_coefficient": round(r, 4),
                    "p_value": round(p, 6),
                    "sample_size": n,
                    "lag_days": 0,
                    "effect_description": "",
                    "category": "nutrition_glucose",
                    "strength": strength,
                    "direction": direction,
                    "data_points": [
                        {"date": d, "a_value": round(x, 2), "b_value": round(y, 2)}
                        for x, y, d in pairs_xy
                    ],
                    "correlation_type": "pearson",
                }
            )

        results.sort(key=lambda c: abs(c["correlation_coefficient"]), reverse=True)
        return results
