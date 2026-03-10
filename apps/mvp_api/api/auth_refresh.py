"""
Auth Token Refresh API

Proxies Supabase refresh-token exchange for native clients that cannot use
the Supabase JS/Python SDK directly (e.g., Swift / Kotlin mobile apps).

Web clients should call supabase.auth.refreshSession() instead — the SDK
handles token refresh transparently and more efficiently.
"""

import os
import ssl

import aiohttp
import certifi
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
# Supabase requires the project's anon/publishable key in the apikey header
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


class RefreshTokenRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Payload for the refresh-token exchange request."""

    refresh_token: str


class TokenResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Access + refresh token pair returned after a successful refresh."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest) -> TokenResponse:
    """
    Exchange a Supabase refresh token for a new access + refresh token pair.

    The new `access_token` expires in `expires_in` seconds (typically 3600).
    Store the returned `refresh_token` — it replaces the old one (rotation).
    """
    if not SUPABASE_URL:
        raise HTTPException(status_code=503, detail="Auth service not configured")

    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(
            url,
            json={"refresh_token": body.refresh_token},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.warning("Token refresh failed (%s): %s", resp.status, text)
                raise HTTPException(
                    status_code=401,
                    detail="Token refresh failed — token may be expired or revoked",
                )

            data = await resp.json()

    return TokenResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_in=data.get("expires_in", 3600),
        token_type=data.get("token_type", "bearer"),
    )
