"""
common.metrics — canonical health metric layer.

All health data flowing into the correlation engine is normalised to
canonical metric names defined here.  Device-specific raw field names
are mapped to canonical names by the adapters in common.metrics.adapters.

Quick-start::

    from common.metrics.normalizer import HealthNormalizer

    normalizer = HealthNormalizer()
    metrics = normalizer.normalize("oura", raw_day_dict, date="2026-03-18",
                                   user_baseline={})
"""
