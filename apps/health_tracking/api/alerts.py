"""
Alerts API Router
Handles endpoints for health alerts management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from ..models.alerts import AlertCreate, AlertUpdate, AlertResponse
from ..services.health_analytics import HealthAnalyticsService

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.create_alert(
            user_id=current_user["id"],
            alert_data=alert.dict()
        )
        return AlertResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        alerts = await analytics_service.list_alerts(
            user_id=current_user["id"]
        )
        return [AlertResponse(**alert) for alert in alerts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        alert = await analytics_service.get_alert(
            user_id=current_user["id"],
            alert_id=alert_id
        )
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return AlertResponse(**alert)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_update: AlertUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.update_alert(
            user_id=current_user["id"],
            alert_id=alert_id,
            update_data=alert_update.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Alert not found")
        return AlertResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        success = await analytics_service.delete_alert(
            user_id=current_user["id"],
            alert_id=alert_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 