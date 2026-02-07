"""
Main authentication service for the Personal Health Assistant.

This service provides comprehensive authentication functionality including:
- Supabase Auth integration
- Auth0 OAuth provider support
- Multi-factor authentication
- Session management
- Security monitoring
- HIPAA compliance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_

from passlib.context import CryptContext
from jose import JWTError, jwt
import pyotp
import qrcode
from io import BytesIO
import base64

from common.database.connection import get_async_db
from common.utils.logging import get_logger

# from common.middleware.auth import get_current_user
from common.services.base import BaseService

from ..models.user import User, UserStatus, UserType, MFAStatus
from ..models.session import Session, SessionStatus, RefreshToken
from ..models.roles import Role, Permission, UserRole, RolePermission
from ..models.mfa import MFADevice, MFADeviceStatus, MFABackupCode, MFAAttempt
from ..models.audit import AuthAuditLog, AuditEventType, AuditSeverity
from ..models.consent import ConsentRecord, ConsentStatus, ConsentType

from .supabase_service import SupabaseService
from .auth0_service import Auth0Service
from .mfa_service import MFAService
from .role_service import RoleService
from .audit_service import AuditService
from .consent_service import ConsentService

logger = get_logger(__name__)


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send email via SMTP or external provider.

    When SMTP_HOST is configured in settings, emails are sent through the
    SMTP relay.  Otherwise the email content is logged only (development
    fallback).  This function is intentionally a standalone coroutine so
    that it can be easily swapped for a SendGrid / AWS SES adapter later.
    """
    from common.config.settings import get_settings

    settings = get_settings()

    # Attempt real SMTP delivery when configured
    if settings.SMTP_HOST:
        try:
            import aiosmtplib
            from email.mime.text import MIMEText

            message = MIMEText(body, "html")
            message["From"] = settings.SMTP_FROM or "noreply@healthassistant.com"
            message["To"] = to_email
            message["Subject"] = subject

            smtp_kwargs: dict = {
                "hostname": settings.SMTP_HOST,
                "port": settings.SMTP_PORT or 587,
            }
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp_kwargs["username"] = settings.SMTP_USERNAME
                smtp_kwargs["password"] = settings.SMTP_PASSWORD
                smtp_kwargs["start_tls"] = True

            await aiosmtplib.send(message, **smtp_kwargs)
            logger.info(f"Email sent to {to_email} via SMTP")
            return True
        except Exception as e:
            logger.warning(f"SMTP send failed: {e}, falling back to log-only mode")

    # Fallback: log only (development mode)
    logger.info(f"[DEV EMAIL] To: {to_email}, Subject: {subject}")
    logger.info(f"[DEV EMAIL] Body: {body}")
    return True


# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService(BaseService):
    """Main authentication service with comprehensive security features."""

    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
        self.supabase_service = SupabaseService()
        self.auth0_service = Auth0Service()
        self.mfa_service = MFAService()
        self.role_service = RoleService(db)
        self.audit_service = AuditService(db)
        self.consent_service = ConsentService(db)

    @property
    def model_class(self):
        """Return the SQLAlchemy model class"""
        return User

    @property
    def schema_class(self):
        """Return the Pydantic schema class"""
        from ..models.user import UserResponse

        return UserResponse

    @property
    def create_schema_class(self):
        """Return the Pydantic create schema class"""
        from ..models.user import UserCreate

        return UserCreate

    @property
    def update_schema_class(self):
        """Return the Pydantic update schema class"""
        from ..models.user import UserUpdate

        return UserUpdate

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        logger.warning(
            f"[DEBUG] Login: plain_password='{plain_password}' hashed_password='{hashed_password}'"
        )
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        hash = pwd_context.hash(password)
        logger.warning(f"[DEBUG] Registration: password='{password}' hash='{hash}'")
        return hash

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.get_jwt_secret_key(), algorithm=JWT_ALGORITHM
        )
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, self.get_jwt_secret_key(), algorithm=JWT_ALGORITHM
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, self.get_jwt_secret_key(), algorithms=[JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key from environment variable."""
        from common.config.settings import settings

        return settings.JWT_SECRET_KEY

    async def authenticate_user(
        self, email: str, password: str, ip_address: str = None, user_agent: str = None
    ) -> Optional[User]:
        """Authenticate user with email and password."""
        try:
            logger.info(f"Authenticating user: {email}")
            # Get user from database
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            logger.info(f"User lookup result: {user}")

            if not user:
                logger.warning(f"User not found: {email}")
                await self._log_failed_login(
                    email, ip_address, user_agent, "user_not_found"
                )
                return None

            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Password mismatch for user: {email}")
                user.increment_failed_login()
                await self.db.commit()
                await self._log_failed_login(
                    email, ip_address, user_agent, "invalid_password"
                )
                return None

            if not user.is_active:
                logger.warning(f"User inactive: {email}")
                await self._log_failed_login(
                    email, ip_address, user_agent, "account_inactive"
                )
                return None

            if user.is_locked:
                logger.warning(f"User locked: {email}")
                await self._log_failed_login(
                    email, ip_address, user_agent, "account_locked"
                )
                return None

            # Reset failed login attempts on successful login
            user.reset_failed_login_attempts()
            user.last_login_at = datetime.utcnow()
            await self.db.commit()

            # Log successful login
            logger.info(f"Login successful for user: {email}")
            await self._log_successful_login(user, ip_address, user_agent)

            return user

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self._log_failed_login(email, ip_address, user_agent, "system_error")
            return None

    async def authenticate_with_supabase(
        self, supabase_token: str, ip_address: str = None, user_agent: str = None
    ) -> Optional[User]:
        """Authenticate user with Supabase token."""
        try:
            # Verify token with Supabase
            supabase_user = await self.supabase_service.verify_token(supabase_token)
            if not supabase_user:
                await self._log_failed_login(
                    "supabase_user", ip_address, user_agent, "invalid_supabase_token"
                )
                return None

            # Get or create user in our database
            user = await self._get_or_create_supabase_user(supabase_user)
            if not user.is_active:
                await self._log_failed_login(
                    user.email, ip_address, user_agent, "account_inactive"
                )
                return None

            # Log successful login
            await self._log_successful_login(user, ip_address, user_agent)

            return user

        except Exception as e:
            logger.error(f"Supabase authentication error: {e}")
            await self._log_failed_login(
                "supabase_user", ip_address, user_agent, "supabase_error"
            )
            return None

    async def authenticate_with_auth0(
        self, auth0_token: str, ip_address: str = None, user_agent: str = None
    ) -> Optional[User]:
        """Authenticate user with Auth0 token."""
        try:
            # Verify token with Auth0
            auth0_user = await self.auth0_service.verify_token(auth0_token)
            if not auth0_user:
                await self._log_failed_login(
                    "auth0_user", ip_address, user_agent, "invalid_auth0_token"
                )
                return None

            # Get or create user in our database
            user = await self._get_or_create_auth0_user(auth0_user)
            if not user.is_active:
                await self._log_failed_login(
                    user.email, ip_address, user_agent, "account_inactive"
                )
                return None

            # Log successful login
            await self._log_successful_login(user, ip_address, user_agent)

            return user

        except Exception as e:
            logger.error(f"Auth0 authentication error: {e}")
            await self._log_failed_login(
                "auth0_user", ip_address, user_agent, "auth0_error"
            )
            return None

    async def create_session(
        self,
        user: User,
        ip_address: str = None,
        user_agent: str = None,
        device_id: str = None,
    ) -> Session:
        """Create a new user session."""
        try:
            # Create session tokens
            access_token = self.create_access_token(
                {"sub": str(user.id), "email": user.email}
            )
            refresh_token = self.create_refresh_token({"sub": str(user.id)})

            # Create session record
            session = Session(
                user_id=user.id,
                session_token=access_token,
                refresh_token=refresh_token,
                access_token_expires_at=datetime.utcnow()
                + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                refresh_token_expires_at=datetime.utcnow()
                + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id,
                is_mfa_verified=user.mfa_status == MFAStatus.DISABLED,
            )

            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)

            # Log session creation
            await self.audit_service.log_event(
                user_id=user.id,
                event_type=AuditEventType.SESSION_CREATED,
                description=f"Session created for user {user.email}",
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session.id,
            )

            return session

        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise HTTPException(status_code=500, detail="Failed to create session")

    async def refresh_session(
        self, refresh_token: str, ip_address: str = None, user_agent: str = None
    ) -> Optional[Session]:
        """Refresh user session with refresh token."""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            # Get user
            user = await self._get_user_by_id(UUID(user_id))
            if not user or not user.is_active:
                return None

            # Get existing session
            query = select(Session).where(
                and_(
                    Session.refresh_token == refresh_token,
                    Session.status == SessionStatus.ACTIVE,
                )
            )
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()

            if not session or not session.is_refresh_valid:
                return None

            # Create new tokens
            new_access_token = self.create_access_token(
                {"sub": str(user.id), "email": user.email}
            )
            new_refresh_token = self.create_refresh_token({"sub": str(user.id)})

            # Update session
            session.session_token = new_access_token
            session.refresh_token = new_refresh_token
            session.access_token_expires_at = datetime.utcnow() + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
            session.refresh_token_expires_at = datetime.utcnow() + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
            session.last_activity_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(session)

            # Log token refresh
            await self.audit_service.log_event(
                user_id=user.id,
                event_type=AuditEventType.TOKEN_REFRESHED,
                description="Access token refreshed",
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session.id,
            )

            return session

        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            return None

    async def revoke_session(
        self, session_id: UUID, user_id: UUID, reason: str = "manual_logout"
    ) -> bool:
        """Revoke a user session."""
        try:
            query = select(Session).where(
                and_(Session.id == session_id, Session.user_id == user_id)
            )
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()

            if not session:
                return False

            session.revoke(reason)
            await self.db.commit()

            # Log session revocation
            await self.audit_service.log_event(
                user_id=user_id,
                event_type=AuditEventType.SESSION_REVOKED,
                description=f"Session revoked: {reason}",
                session_id=session_id,
            )

            return True

        except Exception as e:
            logger.error(f"Session revocation error: {e}")
            return False

    async def verify_mfa(
        self, user: User, mfa_code: str, session_id: UUID = None
    ) -> bool:
        """Verify MFA code for user."""
        try:
            # Verify MFA code
            is_valid = await self.mfa_service.verify_code(user.id, mfa_code, session_id)

            if is_valid:
                # Update session MFA status if session provided
                if session_id:
                    query = select(Session).where(Session.id == session_id)
                    result = await self.db.execute(query)
                    session = result.scalar_one_or_none()
                    if session:
                        session.is_mfa_verified = True
                        await self.db.commit()

                # Log successful MFA verification
                await self.audit_service.log_event(
                    user_id=user.id,
                    event_type=AuditEventType.MFA_VERIFICATION_SUCCESS,
                    description="MFA verification successful",
                    session_id=session_id,
                )
            else:
                # Log failed MFA verification
                await self.audit_service.log_event(
                    user_id=user.id,
                    event_type=AuditEventType.MFA_VERIFICATION_FAILURE,
                    description="MFA verification failed",
                    session_id=session_id,
                    severity=AuditSeverity.MEDIUM,
                )

            return is_valid

        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return False

    async def setup_mfa(self, user: User, device_name: str) -> Dict[str, Any]:
        """Setup MFA for user."""
        try:
            # Generate MFA secret
            secret = pyotp.random_base32()

            # Create MFA device
            device = await self.mfa_service.create_device(
                user_id=user.id, device_name=device_name, secret_key=secret
            )

            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email, issuer_name="Personal Health Assistant"
            )

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

            # Generate backup codes
            backup_codes = await self.mfa_service.generate_backup_codes(
                user.id, device.id
            )

            # Update user MFA status
            user.mfa_status = MFAStatus.SETUP_REQUIRED
            await self.db.commit()

            # Log MFA setup
            await self.audit_service.log_event(
                user_id=user.id,
                event_type=AuditEventType.MFA_ENABLED,
                description=f"MFA setup initiated for device: {device_name}",
            )

            return {
                "device_id": device.id,
                "secret_key": secret,
                "qr_code_url": f"data:image/png;base64,{qr_code_base64}",
                "backup_codes": backup_codes,
                "verification_required": True,
            }

        except Exception as e:
            logger.error(f"MFA setup error: {e}")
            raise HTTPException(status_code=500, detail="Failed to setup MFA")

    async def _get_or_create_supabase_user(self, supabase_user: Dict[str, Any]) -> User:
        """Get or create user from Supabase user data."""
        # Check if user exists
        query = select(User).where(User.supabase_user_id == supabase_user["id"])
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return user

        # Create new user
        user = User(
            supabase_user_id=supabase_user["id"],
            email=supabase_user["email"],
            first_name=supabase_user.get("user_metadata", {}).get("first_name", ""),
            last_name=supabase_user.get("user_metadata", {}).get("last_name", ""),
            user_type=UserType.PATIENT,  # Default type
            email_verified=supabase_user.get("email_confirmed_at") is not None,
            status=UserStatus.ACTIVE,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Assign default role
        await self.role_service.assign_default_role(user.id, user.user_type)

        return user

    async def _get_or_create_auth0_user(self, auth0_user: Dict[str, Any]) -> User:
        """Get or create user from Auth0 user data."""
        # Check if user exists
        query = select(User).where(User.auth0_user_id == auth0_user["user_id"])
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return user

        # Create new user
        user = User(
            auth0_user_id=auth0_user["user_id"],
            email=auth0_user["email"],
            first_name=auth0_user.get("given_name", ""),
            last_name=auth0_user.get("family_name", ""),
            user_type=UserType.PATIENT,  # Default type
            email_verified=auth0_user.get("email_verified", False),
            status=UserStatus.ACTIVE,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Assign default role
        await self.role_service.assign_default_role(user.id, user.user_type)

        return user

    async def _get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _log_successful_login(
        self, user: User, ip_address: str = None, user_agent: str = None
    ):
        """Log successful login event."""
        await self.audit_service.log_event(
            user_id=user.id,
            event_type=AuditEventType.LOGIN_SUCCESS,
            description=f"Successful login for user {user.email}",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _log_failed_login(
        self,
        email: str,
        ip_address: str = None,
        user_agent: str = None,
        reason: str = "unknown",
    ):
        """Log failed login event."""
        await self.audit_service.log_event(
            user_id=None,
            event_type=AuditEventType.LOGIN_FAILURE,
            description=f"Failed login attempt for {email}: {reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            severity=AuditSeverity.MEDIUM,
        )

    async def request_password_reset(
        self, email: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """Request a password reset for the specified email."""
        try:
            logger.info(f"Requesting password reset for email: {email}")

            # Get user from database
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                # Don't reveal if user exists or not
                logger.info(f"Password reset requested for non-existent email: {email}")
                await self._log_audit_event(
                    "password_reset_requested",
                    None,
                    ip_address,
                    user_agent,
                    {"email": email, "user_found": False},
                )
                return True  # Return success to avoid email enumeration

            # Generate reset token
            reset_token = self._generate_reset_token(user)

            # Store reset token (you might want to use Redis for this)
            # For now, we'll use a simple approach
            user.user_metadata = user.user_metadata or {}
            user.user_metadata["password_reset_token"] = reset_token
            user.user_metadata["password_reset_expires"] = (
                datetime.utcnow() + timedelta(hours=1)
            ).isoformat()

            await self.db.commit()

            # Send reset email (implement your email service here)
            await self._send_password_reset_email(user.email, reset_token)

            # Log the event
            await self._log_audit_event(
                "password_reset_requested",
                user.id,
                ip_address,
                user_agent,
                {"email": email, "user_found": True},
            )

            return True

        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            return False

    async def confirm_password_reset(
        self,
        email: str,
        token: str,
        new_password: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> bool:
        """Confirm password reset with token and set new password."""
        try:
            logger.info(f"Confirming password reset for email: {email}")

            # Get user from database
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(
                    f"Password reset confirmation for non-existent user: {email}"
                )
                return False

            # Check if reset token is valid
            if not self._verify_reset_token(user, token):
                logger.warning(f"Invalid reset token for user: {email}")
                await self._log_audit_event(
                    "password_reset_failed",
                    user.id,
                    ip_address,
                    user_agent,
                    {"email": email, "reason": "invalid_token"},
                )
                return False

            # Update password
            user.password_hash = self.get_password_hash(new_password)
            user.password_changed_at = datetime.utcnow()
            user.user_metadata = user.user_metadata or {}
            user.user_metadata.pop("password_reset_token", None)
            user.user_metadata.pop("password_reset_expires", None)

            await self.db.commit()

            # Log the event
            await self._log_audit_event(
                "password_reset_completed",
                user.id,
                ip_address,
                user_agent,
                {"email": email},
            )

            return True

        except Exception as e:
            logger.error(f"Password reset confirmation error: {e}")
            return False

    async def request_email_verification(
        self, email: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """Request email verification for the specified email."""
        try:
            logger.info(f"Requesting email verification for email: {email}")

            # Get user from database
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                # Don't reveal if user exists or not
                logger.info(
                    f"Email verification requested for non-existent email: {email}"
                )
                await self._log_audit_event(
                    "email_verification_requested",
                    None,
                    ip_address,
                    user_agent,
                    {"email": email, "user_found": False},
                )
                return True  # Return success to avoid email enumeration

            if user.email_verified:
                logger.info(f"Email already verified for user: {email}")
                return True

            # Generate verification token
            verification_token = self._generate_verification_token(user)

            # Store verification token
            user.user_metadata = user.user_metadata or {}
            user.user_metadata["email_verification_token"] = verification_token
            user.user_metadata["email_verification_expires"] = (
                datetime.utcnow() + timedelta(hours=24)
            ).isoformat()

            await self.db.commit()

            # Send verification email
            await self._send_email_verification_email(user.email, verification_token)

            # Log the event
            await self._log_audit_event(
                "email_verification_requested",
                user.id,
                ip_address,
                user_agent,
                {"email": email, "user_found": True},
            )

            return True

        except Exception as e:
            logger.error(f"Email verification request error: {e}")
            return False

    async def confirm_email_verification(
        self, email: str, token: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """Confirm email verification with token."""
        try:
            logger.info(f"Confirming email verification for email: {email}")

            # Get user from database
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(
                    f"Email verification confirmation for non-existent user: {email}"
                )
                return False

            # Check if verification token is valid
            if not self._verify_verification_token(user, token):
                logger.warning(f"Invalid verification token for user: {email}")
                await self._log_audit_event(
                    "email_verification_failed",
                    user.id,
                    ip_address,
                    user_agent,
                    {"email": email, "reason": "invalid_token"},
                )
                return False

            # Mark email as verified
            user.email_verified = True
            user.status = (
                UserStatus.ACTIVE
            )  # Activate account if it was pending verification
            user.user_metadata = user.user_metadata or {}
            user.user_metadata.pop("email_verification_token", None)
            user.user_metadata.pop("email_verification_expires", None)

            await self.db.commit()

            # Log the event
            await self._log_audit_event(
                "email_verification_completed",
                user.id,
                ip_address,
                user_agent,
                {"email": email},
            )

            return True

        except Exception as e:
            logger.error(f"Email verification confirmation error: {e}")
            return False

    def _generate_reset_token(self, user: User) -> str:
        """Generate a secure password reset token."""
        import secrets

        token = secrets.token_urlsafe(32)
        return token

    def _verify_reset_token(self, user: User, token: str) -> bool:
        """Verify password reset token."""
        if not user.user_metadata:
            return False

        stored_token = user.user_metadata.get("password_reset_token")
        expires_str = user.user_metadata.get("password_reset_expires")

        if not stored_token or not expires_str:
            return False

        try:
            expires = datetime.fromisoformat(expires_str)
            if datetime.utcnow() > expires:
                return False

            return stored_token == token
        except Exception:
            return False

    def _generate_verification_token(self, user: User) -> str:
        """Generate a secure email verification token."""
        import secrets

        token = secrets.token_urlsafe(32)
        return token

    def _verify_verification_token(self, user: User, token: str) -> bool:
        """Verify email verification token."""
        if not user.user_metadata:
            return False

        stored_token = user.user_metadata.get("email_verification_token")
        expires_str = user.user_metadata.get("email_verification_expires")

        if not stored_token or not expires_str:
            return False

        try:
            expires = datetime.fromisoformat(expires_str)
            if datetime.utcnow() > expires:
                return False

            return stored_token == token
        except Exception:
            return False

    async def _send_password_reset_email(self, email: str, token: str):
        """Send password reset email with a secure token link."""
        subject = "Password Reset - Personal Health Assistant"
        body = (
            "<h2>Password Reset Request</h2>"
            "<p>You requested a password reset for your Personal Health Assistant account.</p>"
            f"<p>Your password reset token is: <strong>{token}</strong></p>"
            "<p>This token expires in 1 hour.</p>"
            "<p>If you did not request this, please ignore this email.</p>"
        )
        # Always log token for development/debugging
        logger.info(f"Password reset token for {email}: {token}")
        await send_email(email, subject, body)

    async def _send_email_verification_email(self, email: str, token: str):
        """Send email verification email with a secure token link."""
        subject = "Verify Your Email - Personal Health Assistant"
        body = (
            "<h2>Email Verification</h2>"
            "<p>Thank you for registering with Personal Health Assistant.</p>"
            f"<p>Your email verification token is: <strong>{token}</strong></p>"
            "<p>This token expires in 24 hours.</p>"
            "<p>If you did not create an account, please ignore this email.</p>"
        )
        # Always log token for development/debugging
        logger.info(f"Email verification token for {email}: {token}")
        await send_email(email, subject, body)

    async def _log_audit_event(
        self,
        event_type: str,
        user_id: Optional[UUID],
        ip_address: str = None,
        user_agent: str = None,
        metadata: Dict[str, Any] = None,
    ):
        """Log audit event."""
        try:
            await self.audit_service.log_event(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    async def validate_token(self, token: str, db: AsyncSession) -> User:
        """
        Validate JWT token and return user information.
        Used by forward authentication endpoints.
        """
        try:
            # Verify token
            payload = self.verify_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )

            # Get user information
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            # Get user from database
            user = await self._get_user_by_id(UUID(user_id), db)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                )

            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token validation failed",
            )


# Dependency injection
async def get_auth_service(db: AsyncSession = Depends(get_async_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)
