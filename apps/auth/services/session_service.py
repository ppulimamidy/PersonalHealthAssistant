"""
Session management service for authentication and security.

This service handles:
- Session creation and management
- Session validation and verification
- Session revocation and cleanup
- Refresh token management
- Session security monitoring
- Device tracking and management
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_, desc
from common.utils.logging import get_logger
from common.config.settings import get_settings
from ..models.session import Session as SessionModel, SessionStatus, RefreshToken, TokenBlacklist
from ..models.user import User

logger = get_logger(__name__)


class SessionService:
    """Service for session management operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = get_settings()
    
    async def create_session(self, user_id: str, ip_address: str = None, user_agent: str = None,
                           device_id: str = None, device_type: str = None, location: str = None,
                           timezone: str = None, isp: str = None) -> SessionModel:
        """Create a new session for a user."""
        try:
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=user_id,
                session_token=self._generate_session_token(),
                refresh_token=self._generate_refresh_token(),
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id,
                device_type=device_type,
                location=location,
                timezone=timezone,
                isp=isp,
                status=SessionStatus.ACTIVE,
                is_mfa_verified=False,
                access_token_expires_at=datetime.utcnow() + timedelta(minutes=15),
                refresh_token_expires_at=datetime.utcnow() + timedelta(days=7),
                last_activity_at=datetime.utcnow(),
                login_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Session created: {session.id} for user {user_id}")
            return session
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[SessionModel]:
        """Get a session by ID."""
        try:
            session = await self.db.get(SessionModel, session_id)
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            raise
    
    async def get_session_by_token(self, session_token: str) -> Optional[SessionModel]:
        """Get a session by session token."""
        try:
            query = self.db.query(SessionModel).filter(
                and_(
                    SessionModel.session_token == session_token,
                    SessionModel.status == SessionStatus.ACTIVE,
                    SessionModel.access_token_expires_at > datetime.utcnow()
                )
            )
            session = await query.first()
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session by token: {e}")
            raise
    
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[SessionModel]:
        """Get all sessions for a user."""
        try:
            query = self.db.query(SessionModel).filter(SessionModel.user_id == user_id)
            
            if active_only:
                query = query.filter(
                    and_(
                        SessionModel.status == SessionStatus.ACTIVE,
                        SessionModel.access_token_expires_at > datetime.utcnow()
                    )
                )
            
            sessions = await query.order_by(desc(SessionModel.created_at)).all()
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            raise
    
    async def refresh_session(self, refresh_token: str, ip_address: str = None, user_agent: str = None) -> Optional[SessionModel]:
        """Refresh a session using a refresh token."""
        try:
            # Find session with the refresh token
            query = self.db.query(SessionModel).filter(
                and_(
                    SessionModel.refresh_token == refresh_token,
                    SessionModel.status == SessionStatus.ACTIVE,
                    SessionModel.refresh_token_expires_at > datetime.utcnow()
                )
            )
            session = await query.first()
            
            if not session:
                return None
            
            # Update session with new tokens and timestamps
            session.session_token = self._generate_session_token()
            session.refresh_token = self._generate_refresh_token()
            session.access_token_expires_at = datetime.utcnow() + timedelta(minutes=15)
            session.refresh_token_expires_at = datetime.utcnow() + timedelta(days=7)
            session.last_activity_at = datetime.utcnow()
            session.ip_address = ip_address or session.ip_address
            session.user_agent = user_agent or session.user_agent
            session.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Session refreshed: {session.id}")
            return session
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to refresh session: {e}")
            raise
    
    async def revoke_session(self, session_id: str, reason: str = "manual_logout") -> bool:
        """Revoke a session."""
        try:
            session = await self.db.get(SessionModel, session_id)
            if not session:
                return False
            
            session.status = SessionStatus.REVOKED
            session.logout_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
            
            # Add to token blacklist
            await self._blacklist_tokens(session)
            
            await self.db.commit()
            
            logger.info(f"Session revoked: {session_id} - {reason}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to revoke session: {e}")
            raise
    
    async def revoke_all_user_sessions(self, user_id: str, reason: str = "security_measure") -> int:
        """Revoke all sessions for a user."""
        try:
            query = self.db.query(SessionModel).filter(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.status == SessionStatus.ACTIVE
                )
            )
            sessions = await query.all()
            
            count = 0
            for session in sessions:
                session.status = SessionStatus.REVOKED
                session.logout_at = datetime.utcnow()
                session.updated_at = datetime.utcnow()
                await self._blacklist_tokens(session)
                count += 1
            
            await self.db.commit()
            
            logger.info(f"Revoked {count} sessions for user {user_id} - {reason}")
            return count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to revoke user sessions: {e}")
            raise
    
    async def update_session_activity(self, session_id: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Update session activity timestamp."""
        try:
            session = await self.db.get(SessionModel, session_id)
            if not session:
                return False
            
            session.last_activity_at = datetime.utcnow()
            if ip_address:
                session.ip_address = ip_address
            if user_agent:
                session.user_agent = user_agent
            session.updated_at = datetime.utcnow()
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update session activity: {e}")
            raise
    
    async def verify_session(self, session_token: str, require_mfa: bool = False) -> Optional[SessionModel]:
        """Verify if a session is valid."""
        try:
            session = await self.get_session_by_token(session_token)
            if not session:
                return None
            
            # Check if session is expired
            if session.access_token_expires_at <= datetime.utcnow():
                await self.revoke_session(str(session.id), "token_expired")
                return None
            
            # Check if MFA is required and verified
            if require_mfa and not session.is_mfa_verified:
                return None
            
            # Update activity
            await self.update_session_activity(str(session.id))
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to verify session: {e}")
            raise
    
    async def mark_mfa_verified(self, session_id: str) -> bool:
        """Mark session as MFA verified."""
        try:
            session = await self.db.get(SessionModel, session_id)
            if not session:
                return False
            
            session.is_mfa_verified = True
            session.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Session MFA verified: {session_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to mark MFA verified: {e}")
            raise
    
    async def get_session_statistics(self, user_id: str = None, 
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """Get session statistics."""
        try:
            query = self.db.query(SessionModel)
            
            if user_id:
                query = query.filter(SessionModel.user_id == user_id)
            
            if start_date:
                query = query.filter(SessionModel.created_at >= start_date)
            
            if end_date:
                query = query.filter(SessionModel.created_at <= end_date)
            
            total_sessions = await query.count()
            
            # Get counts by status
            active_sessions = await query.filter(SessionModel.status == SessionStatus.ACTIVE).count()
            revoked_sessions = await query.filter(SessionModel.status == SessionStatus.REVOKED).count()
            expired_sessions = await query.filter(SessionModel.status == SessionStatus.EXPIRED).count()
            
            # Get average session duration
            completed_sessions = await query.filter(
                and_(
                    SessionModel.status.in_([SessionStatus.REVOKED, SessionStatus.EXPIRED]),
                    SessionModel.login_at.isnot(None),
                    SessionModel.logout_at.isnot(None)
                )
            ).all()
            
            total_duration = timedelta()
            for session in completed_sessions:
                if session.login_at and session.logout_at:
                    total_duration += session.logout_at - session.login_at
            
            avg_duration = total_duration / len(completed_sessions) if completed_sessions else timedelta()
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "revoked_sessions": revoked_sessions,
                "expired_sessions": expired_sessions,
                "average_duration_minutes": avg_duration.total_seconds() / 60
            }
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            raise
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            expired_sessions = await self.db.query(SessionModel).filter(
                and_(
                    SessionModel.status == SessionStatus.ACTIVE,
                    SessionModel.refresh_token_expires_at < datetime.utcnow()
                )
            ).all()
            
            count = len(expired_sessions)
            for session in expired_sessions:
                session.status = SessionStatus.EXPIRED
                session.updated_at = datetime.utcnow()
                await self._blacklist_tokens(session)
            
            await self.db.commit()
            
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cleanup expired sessions: {e}")
            raise
    
    async def _blacklist_tokens(self, session: SessionModel):
        """Add session tokens to blacklist."""
        try:
            # Blacklist session token
            session_blacklist = TokenBlacklist(
                id=uuid.uuid4(),
                token_hash=self._hash_token(session.session_token),
                token_type="session",
                blacklisted_at=datetime.utcnow(),
                expires_at=session.access_token_expires_at,
                reason="session_revoked",
                user_id=session.user_id,
                session_id=session.id,
                created_at=datetime.utcnow()
            )
            self.db.add(session_blacklist)
            
            # Blacklist refresh token
            refresh_blacklist = TokenBlacklist(
                id=uuid.uuid4(),
                token_hash=self._hash_token(session.refresh_token),
                token_type="refresh",
                blacklisted_at=datetime.utcnow(),
                expires_at=session.refresh_token_expires_at,
                reason="session_revoked",
                user_id=session.user_id,
                session_id=session.id,
                created_at=datetime.utcnow()
            )
            self.db.add(refresh_blacklist)
            
        except Exception as e:
            logger.error(f"Failed to blacklist tokens: {e}")
            raise
    
    def _generate_session_token(self) -> str:
        """Generate a secure session token."""
        return str(uuid.uuid4())
    
    def _generate_refresh_token(self) -> str:
        """Generate a secure refresh token."""
        return str(uuid.uuid4())
    
    def _hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest() 