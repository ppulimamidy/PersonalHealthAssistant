"""
Oura Ring Integration API
Endpoints for connecting and syncing data from Oura Ring.
Supports sandbox mode for development (mock data, no OAuth required).

Supabase table required (run once in SQL editor):
    CREATE TABLE public.oura_connections (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        token_type TEXT DEFAULT 'Bearer',
        scope TEXT,
        expires_at TIMESTAMPTZ,
        connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    ALTER TABLE public.oura_connections ENABLE ROW LEVEL SECURITY;
    CREATE POLICY "own oura connection" ON public.oura_connections
        FOR ALL USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_upsert,
    _supabase_delete,
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    _supabase_headers,
    _ssl_context,
)

logger = get_logger(__name__)

router = APIRouter()

# Sandbox mode - uses mock data, no real API calls
USE_SANDBOX = os.getenv("USE_SANDBOX", "true").lower() in ("true", "1", "yes")

# In-memory store for sandbox disconnect state (per user_id)
_sandbox_disconnected: set[str] = set()


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
                "user_type": "sandbox",
            }
    else:
        # In production, require authentication
        return await get_current_user(request)


# Oura OAuth Configuration (only needed in production mode)
OURA_CLIENT_ID = os.getenv("OURA_CLIENT_ID", "")
OURA_CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET", "")
OURA_REDIRECT_URI = os.getenv(
    "OURA_REDIRECT_URI", "http://localhost:3000/oura/callback"
)
OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/oauth/token"


async def _load_oura_token(user_id: str) -> Optional[dict]:
    """Load the stored Oura OAuth token for a user from Supabase."""
    rows = await _supabase_get("oura_connections", f"user_id=eq.{user_id}&limit=1")
    return rows[0] if rows else None


async def _save_oura_token(user_id: str, token_data: dict) -> None:
    """Upsert the Oura OAuth token for a user into Supabase."""
    from datetime import timezone

    expires_in = token_data.get("expires_in", 86400)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()
    row = {
        "user_id": user_id,
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type", "Bearer"),
        "scope": token_data.get("scope"),
        "expires_at": expires_at,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await _supabase_upsert("oura_connections", row, "user_id")


async def _delete_oura_token(user_id: str) -> None:
    """Remove the Oura OAuth token for a user from Supabase."""
    await _supabase_delete("oura_connections", f"user_id=eq.{user_id}")


async def _get_valid_access_token(user_id: str) -> Optional[str]:
    """
    Return a valid Oura access token for the user.
    Auto-refreshes if the token is expired (or within 5 min of expiry).
    Returns None if no token is stored.
    """
    from datetime import timezone

    row = await _load_oura_token(user_id)
    if not row:
        return None

    access_token = row.get("access_token")
    refresh_token = row.get("refresh_token")
    expires_at_str = row.get("expires_at")

    # Check if token is about to expire
    if expires_at_str and refresh_token:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if expires_at - now < timedelta(minutes=5):
                # Refresh the token
                access_token = await _refresh_oura_token(user_id, refresh_token)
        except (ValueError, TypeError):
            pass  # Use existing token if parsing fails

    return access_token


async def _refresh_oura_token(user_id: str, refresh_token: str) -> Optional[str]:
    """
    Exchange a refresh token for a new access token.
    Saves the new token to DB. Returns the new access_token or None on failure.
    """
    import aiohttp

    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=_ssl_context())
        ) as session:
            async with session.post(
                OURA_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": OURA_CLIENT_ID,
                    "client_secret": OURA_CLIENT_SECRET,
                },
            ) as resp:
                if resp.status != 200:
                    logger.error("Oura token refresh failed: %s", await resp.text())
                    return None
                token_data = await resp.json()
                await _save_oura_token(user_id, token_data)
                return token_data.get("access_token")
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Oura token refresh exception: %s", exc)
        return None


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
        "message": "Using mock data (sandbox mode)"
        if USE_SANDBOX
        else "Production mode",
    }


@router.get("/auth-url")
async def get_auth_url(current_user: dict = Depends(get_user_optional)):
    """
    Get Oura OAuth authorization URL.
    In sandbox mode, returns a mock URL that auto-connects.
    """
    if USE_SANDBOX:
        # Reconnecting — clear any prior disconnect
        _sandbox_disconnected.discard(current_user["id"])
        return {
            "auth_url": None,
            "sandbox_mode": True,
            "message": "Sandbox mode - device is automatically connected with mock data",
        }

    if not OURA_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Oura OAuth not configured. Set OURA_CLIENT_ID or enable sandbox mode.",
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
    request: OuraCallbackRequest, current_user: dict = Depends(get_user_optional)
):
    """
    Handle OAuth callback from Oura.
    In sandbox mode, this immediately returns a connected status.
    """
    if USE_SANDBOX:
        _sandbox_disconnected.discard(current_user["id"])
        return OuraConnectionResponse(
            id=f"oura_sandbox_{current_user['id']}",
            user_id=current_user["id"],
            is_active=True,
            is_sandbox=True,
            connected_at=datetime.utcnow(),
        )

    import aiohttp

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=_ssl_context())
    ) as session:
        async with session.post(
            OURA_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": request.code,
                "client_id": OURA_CLIENT_ID,
                "client_secret": OURA_CLIENT_SECRET,
                "redirect_uri": OURA_REDIRECT_URI,
            },
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Oura token exchange failed: {error_text}")
                raise HTTPException(status_code=400, detail="Failed to connect Oura")

            token_data = await response.json()

    await _save_oura_token(current_user["id"], token_data)

    connection = OuraConnectionResponse(
        id=f"oura_{current_user['id']}",
        user_id=current_user["id"],
        is_active=True,
        is_sandbox=False,
        connected_at=datetime.utcnow(),
        expires_at=datetime.utcnow()
        + timedelta(seconds=token_data.get("expires_in", 86400)),
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
        user_id = current_user["id"]
        is_active = user_id not in _sandbox_disconnected
        return OuraConnectionResponse(
            id=f"oura_sandbox_{user_id}",
            user_id=user_id,
            is_active=is_active,
            is_sandbox=True,
            connected_at=datetime.utcnow() - timedelta(days=7) if is_active else None,
        )

    # In production, query database for connection status
    row = await _load_oura_token(current_user["id"])
    if row:
        connected_at = row.get("connected_at")
        expires_at = row.get("expires_at")
        return OuraConnectionResponse(
            id=f"oura_{current_user['id']}",
            user_id=current_user["id"],
            is_active=True,
            is_sandbox=False,
            connected_at=datetime.fromisoformat(connected_at.replace("Z", "+00:00"))
            if connected_at
            else None,
            expires_at=datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_at
            else None,
        )

    return OuraConnectionResponse(
        id="",
        user_id=current_user["id"],
        is_active=False,
        is_sandbox=False,
    )


@router.delete("/connection")
async def disconnect(current_user: dict = Depends(get_user_optional)):
    """
    Disconnect Oura Ring.
    In sandbox mode, marks as disconnected in-memory.
    """
    if USE_SANDBOX:
        _sandbox_disconnected.add(current_user["id"])
        return {"status": "disconnected", "message": "Sandbox mode - reconnect anytime"}

    await _delete_oura_token(current_user["id"])
    logger.info(f"Oura disconnected for user {current_user['id']}")
    return {"status": "disconnected"}


@router.post("/sync", response_model=SyncResponse)
async def sync_data(current_user: dict = Depends(get_user_optional)):
    """
    Sync latest data from Oura Ring.
    In sandbox mode, generates fresh mock data.
    """
    from apps.device_data.services.oura_client import OuraAPIClient

    if USE_SANDBOX:
        access_token = None
        use_sandbox = True
    else:
        access_token = await _get_valid_access_token(current_user["id"])
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Please connect your Oura Ring first",
            )
        use_sandbox = False

    try:
        async with OuraAPIClient(
            access_token=access_token,
            use_sandbox=use_sandbox,
            user_id=current_user["id"],
        ) as client:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            data = await client.get_all_data(start_date, end_date)

            synced = sum(
                [
                    len(data.get("daily_sleep", {}).get("data", [])),
                    len(data.get("daily_activity", {}).get("data", [])),
                    len(data.get("daily_readiness", {}).get("data", [])),
                ]
            )

            return SyncResponse(
                synced_records=synced,
                last_sync=datetime.utcnow(),
                is_sandbox=USE_SANDBOX,
            )
    except Exception as e:
        logger.error(f"Oura sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sleep")
async def get_sleep_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_user_optional),
):
    """Get sleep data for date range."""
    from apps.device_data.services.oura_client import OuraAPIClient

    if USE_SANDBOX:
        access_token = None
        use_sandbox = True
    else:
        access_token = await _get_valid_access_token(current_user["id"])
        use_sandbox = not access_token

    async with OuraAPIClient(
        access_token=access_token,
        use_sandbox=use_sandbox,
        user_id=current_user["id"],
    ) as client:
        data = await client.get_daily_sleep(start_date, end_date)
        return data.get("data", [])


@router.get("/activity")
async def get_activity_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_user_optional),
):
    """Get activity data for date range."""
    from apps.device_data.services.oura_client import OuraAPIClient

    if USE_SANDBOX:
        access_token = None
        use_sandbox = True
    else:
        access_token = await _get_valid_access_token(current_user["id"])
        use_sandbox = not access_token

    async with OuraAPIClient(
        access_token=access_token,
        use_sandbox=use_sandbox,
        user_id=current_user["id"],
    ) as client:
        data = await client.get_daily_activity(start_date, end_date)
        return data.get("data", [])


@router.get("/readiness")
async def get_readiness_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_user_optional),
):
    """Get readiness data for date range."""
    from apps.device_data.services.oura_client import OuraAPIClient

    if USE_SANDBOX:
        access_token = None
        use_sandbox = True
    else:
        access_token = await _get_valid_access_token(current_user["id"])
        use_sandbox = not access_token

    async with OuraAPIClient(
        access_token=access_token,
        use_sandbox=use_sandbox,
        user_id=current_user["id"],
    ) as client:
        data = await client.get_daily_readiness(start_date, end_date)
        return data.get("data", [])
