"""
MVP Nutrition API

Thin proxy endpoints to the Nutrition service for the MVP frontend.
"""

# pylint: disable=broad-except,line-too-long

import os
import asyncio
from typing import Any, Dict, Optional

import aiohttp
from urllib.parse import urlencode
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    UploadFile,
    File,
    Form,
    status,
)
from datetime import date, timedelta

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import UsageGate

logger = get_logger(__name__)
router = APIRouter()

NUTRITION_SERVICE_URL = os.environ.get(
    "NUTRITION_SERVICE_URL", "http://localhost:8007"
).rstrip("/")
TIMEOUT_S = float(os.environ.get("NUTRITION_SERVICE_TIMEOUT_S", "8.0"))
RECOGNIZE_TIMEOUT_S = float(
    os.environ.get("NUTRITION_SERVICE_RECOGNIZE_TIMEOUT_S", "30.0")
)


def _bearer_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        return auth_header
    return None


async def _request_json(
    method: str,
    url: str,
    headers: Dict[str, str],
    json_body: Optional[Dict[str, Any]] = None,
) -> Any:
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_S)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            method_upper = method.upper()
            if method_upper == "GET":
                req = session.get(url, headers=headers)
            elif method_upper == "POST":
                req = session.post(url, headers=headers, json=json_body or {})
            elif method_upper == "PUT":
                req = session.put(url, headers=headers, json=json_body or {})
            elif method_upper == "DELETE":
                req = session.delete(url, headers=headers)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unsupported nutrition proxy method",
                )

            async with req as resp:
                text = await resp.text()
                if resp.status >= 400:
                    logger.warning(
                        "Nutrition upstream error %s: %s", resp.status, text[:500]
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Nutrition service error",
                    )
                try:
                    return await resp.json()
                except Exception:
                    logger.warning(
                        "Nutrition upstream returned non-JSON: %s", text[:500]
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Nutrition service returned invalid response",
                    )
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        logger.warning("Nutrition upstream request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Nutrition service unreachable",
        ) from exc


async def _request_multipart(
    url: str,
    headers: Dict[str, str],
    form: aiohttp.FormData,
    timeout_s: float,
) -> Any:
    timeout = aiohttp.ClientTimeout(total=timeout_s)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, data=form) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    logger.warning(
                        "Nutrition upstream error %s: %s", resp.status, text[:500]
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Nutrition service error",
                    )
                try:
                    return await resp.json()
                except Exception:
                    logger.warning(
                        "Nutrition upstream returned non-JSON: %s", text[:500]
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Nutrition service returned invalid response",
                    )
    except asyncio.TimeoutError as exc:
        logger.warning("Nutrition upstream request timed out: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Nutrition service timed out processing the image",
        ) from exc
    except aiohttp.ClientError as exc:
        logger.warning("Nutrition upstream request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Nutrition service unreachable",
        ) from exc


@router.get("/summary")
async def get_nutrition_summary(
    request: Request,
    days: int = Query(default=14, ge=1, le=90),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a nutrition summary for the authenticated user.

    Proxies to Nutrition Service:
    - GET /api/v1/nutrition/nutrition-summary?days={days}
    """
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    url = f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/nutrition-summary?days={days}"
    payload = await _request_json("GET", url, headers={"Authorization": bearer})

    # Nutrition service uses { success: bool, data: {...} }
    if (
        isinstance(payload, dict)
        and payload.get("success") is True
        and "data" in payload
    ):
        return payload["data"]
    return payload


@router.get("/meals")
async def list_meals(
    request: Request,
    days: int = Query(default=14, ge=1, le=90),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List meal logs for the authenticated user.

    Proxies to Nutrition Service:
    - GET /api/v1/nutrition/nutrition-history?start_date=...&end_date=...
    """
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    end_d = date.today()
    start_d = end_d - timedelta(days=days)
    url = (
        f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/nutrition-history"
        f"?start_date={start_d.isoformat()}&end_date={end_d.isoformat()}"
    )
    payload = await _request_json("GET", url, headers={"Authorization": bearer})
    if (
        isinstance(payload, dict)
        and payload.get("success") is True
        and "data" in payload
    ):
        return {"items": payload["data"]}
    # best-effort fallback
    return {"items": payload if isinstance(payload, list) else []}


@router.post("/recognize-meal-image")
async def recognize_meal_image(
    request: Request,
    image: UploadFile = File(...),
    meal_type: Optional[str] = Form(default=None),
    cuisine_hint: Optional[str] = Form(default=None),
    region_hint: Optional[str] = Form(default=None),
    dietary_restrictions: Optional[str] = Form(default=None),
    preferred_units: Optional[str] = Form(default=None),
    enable_portion_estimation: bool = Form(default=True),
    enable_nutrition_lookup: bool = Form(default=True),
    enable_cultural_recognition: bool = Form(default=True),
    models_to_use: str = Form(default="openai_vision,google_vision,azure_vision"),
    current_user: Dict[str, Any] = Depends(UsageGate("nutrition_scans")),
) -> Dict[str, Any]:
    """
    Recognize foods from an uploaded meal image.

    Proxies to Nutrition Service:
    - POST /api/v1/food-recognition/recognize (multipart/form-data)
    """
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    img_bytes = await image.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="Image is required")

    url = f"{NUTRITION_SERVICE_URL}/api/v1/food-recognition/recognize"
    form = aiohttp.FormData()
    form.add_field(
        "image",
        img_bytes,
        filename=image.filename or "meal.jpg",
        content_type=image.content_type or "application/octet-stream",
    )
    # Nutrition service requires user_id + verifies it matches current_user.id
    form.add_field("user_id", str(current_user.get("id")))
    if meal_type is not None:
        form.add_field("meal_type", meal_type)
    if cuisine_hint is not None:
        form.add_field("cuisine_hint", cuisine_hint)
    if region_hint is not None:
        form.add_field("region_hint", region_hint)
    if dietary_restrictions is not None:
        form.add_field("dietary_restrictions", dietary_restrictions)
    if preferred_units is not None:
        form.add_field("preferred_units", preferred_units)
    form.add_field(
        "enable_portion_estimation", "true" if enable_portion_estimation else "false"
    )
    form.add_field(
        "enable_nutrition_lookup", "true" if enable_nutrition_lookup else "false"
    )
    form.add_field(
        "enable_cultural_recognition",
        "true" if enable_cultural_recognition else "false",
    )
    form.add_field("models_to_use", models_to_use)

    payload = await _request_multipart(
        url,
        headers={"Authorization": bearer},
        form=form,
        timeout_s=RECOGNIZE_TIMEOUT_S,
    )
    return payload


@router.post("/log-meal")
async def log_meal(
    request: Request,
    meal_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Log a meal for the authenticated user.

    Proxies to Nutrition Service:
    - POST /api/v1/nutrition/log-meal
    """
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    url = f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/log-meal"
    payload = await _request_json(
        "POST", url, headers={"Authorization": bearer}, json_body=meal_data
    )

    if (
        isinstance(payload, dict)
        and payload.get("success") is True
        and "data" in payload
    ):
        return payload["data"]
    return payload


@router.put("/meals/{meal_id}")
async def update_meal(
    request: Request,
    meal_id: str,
    meal_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update an existing meal log for the authenticated user."""
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    url = f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/meals/{meal_id}"
    payload = await _request_json(
        "PUT", url, headers={"Authorization": bearer}, json_body=meal_data
    )
    if (
        isinstance(payload, dict)
        and payload.get("success") is True
        and "data" in payload
    ):
        return payload["data"]
    return payload


@router.delete("/meals/{meal_id}")
async def delete_meal(
    request: Request,
    meal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete an existing meal log for the authenticated user."""
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    url = f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/meals/{meal_id}"
    payload = await _request_json("DELETE", url, headers={"Authorization": bearer})
    if isinstance(payload, dict) and payload.get("success") is True:
        return {"success": True}
    return payload


@router.post("/analyze-meal")
async def analyze_meal(
    request: Request,
    meal_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Analyze a meal without persisting it.

    Proxies to Nutrition Service:
    - POST /api/v1/nutrition/analyze-meal
    """
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    url = f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/analyze-meal"
    payload = await _request_json(
        "POST", url, headers={"Authorization": bearer}, json_body=meal_data
    )

    if (
        isinstance(payload, dict)
        and payload.get("success") is True
        and "data" in payload
    ):
        return payload["data"]
    return payload


@router.get("/food-cache")
async def get_food_cache(
    request: Request,
    q: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List cached foods stored in Nutrition service.

    Proxies to Nutrition Service:
    - GET /api/v1/nutrition/food-cache?q=...&source=...&limit=...
    """
    bearer = _bearer_from_request(request)
    if not bearer:
        raise HTTPException(status_code=401, detail="Authentication required")

    params = {
        k: v
        for k, v in {"q": q, "source": source, "limit": limit}.items()
        if v is not None
    }
    qs = urlencode(params)
    url = f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/food-cache"
    if qs:
        url = f"{url}?{qs}"

    payload = await _request_json("GET", url, headers={"Authorization": bearer})
    if (
        isinstance(payload, dict)
        and payload.get("success") is True
        and "data" in payload
    ):
        return payload["data"]
    return payload
