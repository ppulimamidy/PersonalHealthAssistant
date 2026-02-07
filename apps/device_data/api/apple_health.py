"""Apple Health API endpoints for importing HealthKit data."""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/apple-health", tags=["Apple Health"])


# --------------- Pydantic models ---------------


class AppleHealthRecord(BaseModel):
    type: str
    value: float
    unit: str
    start_date: str
    end_date: str
    source_name: Optional[str] = "Apple Health"
    device: Optional[str] = None


class AppleHealthDataImport(BaseModel):
    data_type: str  # steps, heart_rate, sleep, workouts, etc.
    records: List[AppleHealthRecord]
    start_date: Optional[str] = None
    end_date: Optional[str] = None


SUPPORTED_TYPES = [
    "steps",
    "heart_rate",
    "sleep_analysis",
    "workouts",
    "active_energy",
    "resting_heart_rate",
    "blood_oxygen",
    "respiratory_rate",
    "body_temperature",
    "blood_pressure",
    "weight",
    "height",
    "body_fat_percentage",
]

# In-memory sync status per user (would be Redis/DB-backed in production)
_sync_status: Dict[str, Dict[str, Any]] = {}


# --------------- Endpoints ---------------


@router.post("/import")
async def import_apple_health_data(
    data: AppleHealthDataImport,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Import Apple Health data from HealthKit export."""
    if data.data_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported data type: {data.data_type}. Supported types: {SUPPORTED_TYPES}",
        )

    user_id = current_user["id"]
    inserted = 0

    for record in data.records:
        try:
            point_id = str(uuid.uuid4())
            await db.execute(
                text(
                    """
                    INSERT INTO device_data_points
                        (id, user_id, device_type, data_type, value, unit,
                         recorded_at, source, metadata, created_at)
                    VALUES
                        (:id, :user_id, :device_type, :data_type, :value, :unit,
                         :recorded_at, :source, :metadata, NOW())
                    """
                ),
                {
                    "id": point_id,
                    "user_id": user_id,
                    "device_type": "apple_health",
                    "data_type": data.data_type,
                    "value": record.value,
                    "unit": record.unit,
                    "recorded_at": record.start_date,
                    "source": record.source_name or "Apple Health",
                    "metadata": f'{{"end_date": "{record.end_date}", "device": "{record.device or ""}"}}',
                },
            )
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert Apple Health record: {e}")

    await db.commit()

    logger.info(
        f"Imported {inserted}/{len(data.records)} Apple Health {data.data_type} records for user {user_id}"
    )

    return {
        "status": "success",
        "imported": inserted,
        "total_records": len(data.records),
        "data_type": data.data_type,
        "user_id": user_id,
    }


@router.get("/supported-types")
async def get_supported_types():
    """List supported Apple Health data types."""
    return {"types": SUPPORTED_TYPES}


@router.post("/sync")
async def sync_apple_health(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Initiate Apple Health sync."""
    user_id = current_user["id"]
    now = datetime.utcnow().isoformat()

    _sync_status[user_id] = {
        "status": "syncing",
        "started_at": now,
        "completed_at": None,
        "last_error": None,
        "records_synced": 0,
    }

    # In a real implementation this would trigger an async background job.
    # For now we mark it as completed immediately.
    _sync_status[user_id].update(
        {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
        }
    )

    logger.info(f"Apple Health sync initiated for user {user_id}")

    return {
        "status": "sync_initiated",
        "user_id": user_id,
        "message": "Apple Health sync has been initiated. Check /status for progress.",
        "started_at": now,
    }


@router.get("/status")
async def get_sync_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get Apple Health sync status."""
    user_id = current_user["id"]
    sync_info = _sync_status.get(user_id)

    if not sync_info:
        return {
            "status": "never_synced",
            "user_id": user_id,
            "message": "No Apple Health sync has been performed yet.",
        }

    return {
        "user_id": user_id,
        **sync_info,
    }


@router.get("/data/{data_type}")
async def get_apple_health_data(
    data_type: str,
    days: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get imported Apple Health data by type."""
    if data_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported data type: {data_type}. Supported types: {SUPPORTED_TYPES}",
        )

    user_id = current_user["id"]
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    try:
        result = await db.execute(
            text(
                """
                SELECT id, data_type, value, unit, recorded_at, source, metadata, created_at
                FROM device_data_points
                WHERE user_id = :user_id
                  AND device_type = 'apple_health'
                  AND data_type = :data_type
                  AND recorded_at >= :since
                ORDER BY recorded_at DESC
                """
            ),
            {"user_id": user_id, "data_type": data_type, "since": since},
        )
        rows = result.fetchall()
    except Exception as e:
        logger.error(f"Failed to query Apple Health data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Apple Health data",
        )

    records = [
        {
            "id": str(row[0]),
            "data_type": row[1],
            "value": float(row[2]) if row[2] is not None else None,
            "unit": row[3],
            "recorded_at": str(row[4]),
            "source": row[5],
            "metadata": row[6],
            "created_at": str(row[7]),
        }
        for row in rows
    ]

    return {
        "data_type": data_type,
        "days": days,
        "total_records": len(records),
        "records": records,
    }
