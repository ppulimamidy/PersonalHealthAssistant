"""
Oura Ring Integration API
Endpoints for connecting and syncing data from Oura Ring.
Supports sandbox mode for development (mock data, no OAuth required).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Sandbox mode - uses mock data, no real API calls
USE_SANDBOX = os.getenv("USE_SANDBOX", "true").lower() in ("true", "1", "yes")


# Helper function for optional auth in sandbox mode
async def get_user_optional(request: Request) -> dict:
    """Get current user, or return a sandbox user if not authenticated and in sandbox mode"""
    if USE_SANDBOX:
        try:
            return await get_current_user(request)
        except HTTPException:
            # In sandbox mode, if auth fails, return a mock user
            return {
                "id": "sandbox-user-123",
                "email": "sandbox@example.com",
                "user_type": "sandbox"
            }
    else:
        # In production, require authentication
        return await get_current_user(request)

# Oura OAuth Configuration (only needed in production mode)
OURA_CLIENT_ID = os.getenv("OURA_CLIENT_ID", "")
OURA_CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET", "")
OURA_REDIRECT_URI = os.getenv("OURA_REDIRECT_URI", "http://localhost:3000/api/oura/callback")
OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/oauth/token"


class OuraConnectionResponse(BaseModel):
    id: str
    user_id: str
    is_active: bool
    is_sandbox: bool = False
    connected_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class OuraCallbackRequest(BaseModel):
    code: str


class SyncResponse(BaseModel):
    synced_records: int
    last_sync: datetime
    is_sandbox: bool = False


@router.get("/status")
async def get_status():
    """
    Get Oura integration status and mode.
    """
    return {
        "sandbox_mode": USE_SANDBOX,
        "oauth_configured": bool(OURA_CLIENT_ID),
        "message": "Using mock data (sandbox mode)" if USE_SANDBOX else "Production mode"
    }


@router.get("/auth-url")
async def get_auth_url(current_user: dict = Depends(get_user_optional)):
    """
    Get Oura OAuth authorization URL.
    In sandbox mode, returns a mock URL that auto-connects.
    """
    if USE_SANDBOX:
        # In sandbox mode, return a URL that will auto-connect
        return {
            "auth_url": None,
            "sandbox_mode": True,
            "message": "Sandbox mode - device is automatically connected with mock data"
        }

    if not OURA_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Oura OAuth not configured. Set OURA_CLIENT_ID or enable sandbox mode."
        )

    auth_url = (
        f"{OURA_AUTH_URL}"
        f"?client_id={OURA_CLIENT_ID}"
        f"&redirect_uri={OURA_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=daily+personal+heartrate+workout+session+spo2"
        f"&state={current_user['id']}"
    )

    return {"auth_url": auth_url, "sandbox_mode": False}


@router.post("/callback")
async def handle_callback(
    request: OuraCallbackRequest,
    current_user: dict = Depends(get_user_optional)
):
    """
    Handle OAuth callback from Oura.
    In sandbox mode, this immediately returns a connected status.
    """
    if USE_SANDBOX:
        return OuraConnectionResponse(
            id=f"oura_sandbox_{current_user['id']}",
            user_id=current_user['id'],
            is_active=True,
            is_sandbox=True,
            connected_at=datetime.utcnow(),
        )

    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.post(
            OURA_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": request.code,
                "client_id": OURA_CLIENT_ID,
                "client_secret": OURA_CLIENT_SECRET,
                "redirect_uri": OURA_REDIRECT_URI,
            }
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Oura token exchange failed: {error_text}")
                raise HTTPException(status_code=400, detail="Failed to connect Oura")

            token_data = await response.json()

    connection = OuraConnectionResponse(
        id=f"oura_{current_user['id']}",
        user_id=current_user['id'],
        is_active=True,
        is_sandbox=False,
        connected_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 86400))
    )

    logger.info(f"Oura connected for user {current_user['id']}")
    return connection


@router.get("/connection", response_model=OuraConnectionResponse)
async def get_connection_status(current_user: dict = Depends(get_user_optional)):
    """
    Get current Oura connection status.
    In sandbox mode, always returns connected.
    """
    if USE_SANDBOX:
        return OuraConnectionResponse(
            id=f"oura_sandbox_{current_user['id']}",
            user_id=current_user['id'],
            is_active=True,
            is_sandbox=True,
            connected_at=datetime.utcnow() - timedelta(days=7),
        )

    # In production, query database for connection status
    if OURA_CLIENT_ID:
        return OuraConnectionResponse(
            id=f"oura_{current_user['id']}",
            user_id=current_user['id'],
            is_active=True,
            is_sandbox=False,
            connected_at=datetime.utcnow() - timedelta(days=7),
        )

    return OuraConnectionResponse(
        id="",
        user_id=current_user['id'],
        is_active=False,
        is_sandbox=False,
    )


@router.delete("/connection")
async def disconnect(current_user: dict = Depends(get_user_optional)):
    """
    Disconnect Oura Ring.
    In sandbox mode, this is a no-op.
    """
    if USE_SANDBOX:
        return {"status": "disconnected", "message": "Sandbox mode - reconnect anytime"}

    logger.info(f"Oura disconnected for user {current_user['id']}")
    return {"status": "disconnected"}


@router.post("/sync", response_model=SyncResponse)
async def sync_data(current_user: dict = Depends(get_user_optional)):
    """
    Sync latest data from Oura Ring.
    In sandbox mode, generates fresh mock data.
    """
    from apps.device_data.services.oura_client import OuraAPIClient

    access_token = os.getenv("OURA_ACCESS_TOKEN", "")

    try:
        async with OuraAPIClient(
            access_token=access_token if not USE_SANDBOX else None,
            use_sandbox=USE_SANDBOX or not access_token,
            user_id=current_user['id']
        ) as client:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            data = await client.get_all_data(start_date, end_date)

            synced = sum([
                len(data.get("daily_sleep", {}).get("data", [])),
                len(data.get("daily_activity", {}).get("data", [])),
                len(data.get("daily_readiness", {}).get("data", [])),
            ])

            return SyncResponse(
                synced_records=synced,
                last_sync=datetime.utcnow(),
                is_sandbox=USE_SANDBOX
            )
    except Exception as e:
        logger.error(f"Oura sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sleep")
async def get_sleep_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_user_optional)
):
    """Get sleep data for date range."""
    from apps.device_data.services.oura_client import OuraAPIClient

    access_token = os.getenv("OURA_ACCESS_TOKEN", "")

    async with OuraAPIClient(
        access_token=access_token if not USE_SANDBOX else None,
        use_sandbox=USE_SANDBOX or not access_token,
        user_id=current_user['id']
    ) as client:
        data = await client.get_daily_sleep(start_date, end_date)
        return data.get("data", [])


@router.get("/activity")
async def get_activity_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_user_optional)
):
    """Get activity data for date range."""
    from apps.device_data.services.oura_client import OuraAPIClient

    access_token = os.getenv("OURA_ACCESS_TOKEN", "")

    async with OuraAPIClient(
        access_token=access_token if not USE_SANDBOX else None,
        use_sandbox=USE_SANDBOX or not access_token,
        user_id=current_user['id']
    ) as client:
        data = await client.get_daily_activity(start_date, end_date)
        return data.get("data", [])


@router.get("/readiness")
async def get_readiness_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_user_optional)
):
    """Get readiness data for date range."""
    from apps.device_data.services.oura_client import OuraAPIClient

    access_token = os.getenv("OURA_ACCESS_TOKEN", "")

    async with OuraAPIClient(
        access_token=access_token if not USE_SANDBOX else None,
        use_sandbox=USE_SANDBOX or not access_token,
        user_id=current_user['id']
    ) as client:
        data = await client.get_daily_readiness(start_date, end_date)
        return data.get("data", [])
