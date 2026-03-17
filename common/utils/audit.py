"""
HIPAA-compliant audit logging for PHI access events.

Logs WHO accessed WHAT data, WHEN, and from WHERE.
All PHI access must be logged per HIPAA §164.312(b).

Usage:
    from common.utils.audit import log_phi_access, log_phi_modification

    # Log a read event
    await log_phi_access(
        user_id="abc-123",
        action="read",
        resource="lab_results",
        detail="Viewed 3 lab results",
        ip_address=request.client.host,
    )

    # Log a modification
    await log_phi_modification(
        user_id="abc-123",
        action="delete",
        resource="account",
        detail="Full account deletion (GDPR)",
        ip_address=request.client.host,
    )
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("audit.phi")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def log_phi_access(
    user_id: str,
    action: str,
    resource: str,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
    agent_type: Optional[str] = None,
) -> None:
    """
    Log a PHI access event. Actions: read, search, export, share, ai_query.
    """
    event = {
        "event_type": "phi_access",
        "timestamp": _now_iso(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "detail": detail,
        "ip_address": ip_address,
        "agent_type": agent_type,
        "compliance": ["HIPAA_164.312(b)", "GDPR_Art30"],
    }
    logger.info(json.dumps(event))


async def log_phi_modification(
    user_id: str,
    action: str,
    resource: str,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Log a PHI modification event. Actions: create, update, delete, account_delete.
    """
    event = {
        "event_type": "phi_modification",
        "timestamp": _now_iso(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "detail": detail,
        "ip_address": ip_address,
        "compliance": ["HIPAA_164.312(b)", "HIPAA_164.312(c)", "GDPR_Art30"],
    }
    logger.info(json.dumps(event))


async def log_auth_event(
    user_id: Optional[str],
    action: str,
    success: bool,
    ip_address: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    """
    Log authentication events. Actions: login, logout, mfa_setup, mfa_verify, token_refresh.
    """
    event = {
        "event_type": "auth",
        "timestamp": _now_iso(),
        "user_id": user_id,
        "action": action,
        "success": success,
        "ip_address": ip_address,
        "detail": detail,
        "compliance": ["HIPAA_164.312(d)"],
    }
    level = logging.INFO if success else logging.WARNING
    logger.log(level, json.dumps(event))


async def log_consent_event(
    user_id: str,
    action: str,
    consent_type: str,
    granted: bool,
    detail: Optional[str] = None,
) -> None:
    """
    Log consent changes. Actions: grant, revoke, update.
    """
    event = {
        "event_type": "consent",
        "timestamp": _now_iso(),
        "user_id": user_id,
        "action": action,
        "consent_type": consent_type,
        "granted": granted,
        "detail": detail,
        "compliance": ["GDPR_Art7", "HIPAA_164.508"],
    }
    logger.info(json.dumps(event))
