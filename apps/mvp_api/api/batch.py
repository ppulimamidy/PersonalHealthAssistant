"""
Batch API — aggregate multiple data fetches in a single round-trip.

Designed for mobile and web dashboard loads where fetching each resource
individually would waste latency and tokens.

Usage:
    GET /api/v1/batch
    GET /api/v1/batch?resources=health_score,timeline,insights&days=7
    GET /api/v1/batch?resources=timeline&since_timestamp=2026-01-15T00:00:00Z
"""

# pylint: disable=broad-except,import-outside-toplevel

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Resources available in the batch endpoint
ALL_RESOURCES = {
    "health_score",
    "trajectory",
    "timeline",
    "timeline_actions",
    "insights",
    "metric_deltas",
    "correlated_insights",
}

# Default bundle for a home-dashboard load
DEFAULT_RESOURCES = ["health_score", "timeline", "insights", "metric_deltas"]


class BatchResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Batch API response — partial failures are recorded in `errors`, not raised."""

    requested_at: str
    resources: Dict[str, Any]
    errors: Dict[str, str]


def _serialize(result: Any) -> Any:
    """Convert Pydantic models / lists thereof to JSON-compatible types."""
    if isinstance(result, list):
        return [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in result
        ]
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


# ---------------------------------------------------------------------------
# Internal fetch wrappers — call endpoint functions directly (no HTTP hop)
# ---------------------------------------------------------------------------


async def _fetch_health_score(user: dict) -> Any:
    from .health_score import (
        get_health_score,
    )  # pylint: disable=import-outside-toplevel

    return await get_health_score(current_user=user)


async def _fetch_trajectory(user: dict) -> Any:
    from .health_score import get_trajectory  # pylint: disable=import-outside-toplevel

    return await get_trajectory(current_user=user)


async def _fetch_timeline(user: dict, days: int, since_timestamp: Optional[str]) -> Any:
    from .timeline import get_timeline  # pylint: disable=import-outside-toplevel

    return await get_timeline(
        days=days, since_timestamp=since_timestamp, current_user=user
    )


async def _fetch_insights(user: dict) -> Any:
    from .insights import get_insights  # pylint: disable=import-outside-toplevel

    return await get_insights(limit=5, current_user=user)


async def _fetch_metric_deltas(user: dict) -> Any:
    from .insights import get_insight_delta  # pylint: disable=import-outside-toplevel

    return await get_insight_delta(current_user=user)


async def _fetch_correlated_insights(user: dict) -> Any:
    from .insights import (  # pylint: disable=import-outside-toplevel
        get_correlated_insights,
    )

    return await get_correlated_insights(current_user=user)


async def _fetch_timeline_actions(user: dict, days: int) -> Any:
    from .timeline_actions import (  # pylint: disable=import-outside-toplevel
        get_timeline_actions,
    )

    return await get_timeline_actions(days=days, current_user=user)


# ---------------------------------------------------------------------------
# Batch endpoint
# ---------------------------------------------------------------------------

# Maps resource name → fetch wrapper (timeline handled separately due to extra args)
_FETCHERS: Dict[str, Any] = {
    "health_score": _fetch_health_score,
    "trajectory": _fetch_trajectory,
    "insights": _fetch_insights,
    "metric_deltas": _fetch_metric_deltas,
    "correlated_insights": _fetch_correlated_insights,
}


@router.get("", response_model=BatchResponse)
async def batch_fetch(
    resources: str = Query(
        default=",".join(DEFAULT_RESOURCES),
        description="Comma-separated list of resources to fetch. "
        f"Available: {', '.join(sorted(ALL_RESOURCES))}",
    ),
    days: int = Query(
        default=7,
        ge=1,
        le=90,
        description="Days of timeline data to return (used only when 'timeline' is in resources)",
    ),
    since_timestamp: Optional[str] = Query(
        default=None,
        description="ISO 8601 timestamp — narrows timeline fetch to entries on/after "
        "this date (reduces transfer on incremental sync)",
    ),
    current_user: dict = Depends(get_current_user),
) -> BatchResponse:
    """
    Fetch multiple data types in a single authenticated request.

    All requested resources are fetched in **parallel**. If any individual
    fetch fails the result for that resource is `null` and the error is
    recorded in the `errors` map — the rest of the batch still returns
    successfully.

    **Tip for incremental sync:** pass `since_timestamp` to limit timeline
    data to only entries newer than your last successful sync.
    """
    # Build de-duplicated, validated resource list
    requested: List[str] = list(
        dict.fromkeys(  # preserves order, removes duplicates
            r.strip() for r in resources.split(",") if r.strip() in ALL_RESOURCES
        )
    )
    if not requested:
        requested = DEFAULT_RESOURCES[:]

    # Assemble coroutines
    keys: List[str] = []
    coros = []

    for resource in requested:
        keys.append(resource)
        if resource == "timeline":
            coros.append(_fetch_timeline(current_user, days, since_timestamp))
        elif resource == "timeline_actions":
            coros.append(_fetch_timeline_actions(current_user, days))
        elif resource in _FETCHERS:
            coros.append(_FETCHERS[resource](current_user))

    # Run all fetches in parallel; capture exceptions per-resource
    raw_results = await asyncio.gather(*coros, return_exceptions=True)

    result_map: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    for key, raw in zip(keys, raw_results):
        if isinstance(raw, Exception):
            logger.warning("Batch: resource '%s' failed — %s", key, raw)
            errors[key] = type(raw).__name__ + ": " + str(raw)
            result_map[key] = None
        else:
            result_map[key] = _serialize(raw)

    return BatchResponse(
        requested_at=datetime.now(timezone.utc).isoformat(),
        resources=result_map,
        errors=errors,
    )
