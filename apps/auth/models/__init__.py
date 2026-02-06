"""
Authentication models for the Personal Health Assistant.

This module contains all authentication-related models including:
- User models with comprehensive role-based access control
- Session management models
- MFA and security models
- Audit logging models
"""

# Import the shared Base from common models
from common.models.base import Base

from .user import User, UserProfile, UserPreferences
from .session import Session, RefreshToken
from .roles import Role, Permission, UserRole, RolePermission
from .mfa import MFADevice, MFABackupCode
from .audit import AuthAuditLog
from .consent import ConsentRecord, DataAccessLog

__all__ = [
    "Base",  # Export the shared Base
    "User",
    "UserProfile", 
    "UserPreferences",
    "Session",
    "RefreshToken",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "MFADevice",
    "MFABackupCode",
    "AuthAuditLog",
    "ConsentRecord",
    "DataAccessLog"
] 