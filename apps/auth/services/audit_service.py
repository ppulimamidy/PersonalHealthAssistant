"""
Audit logging service for comprehensive security and compliance tracking.

This service handles:
- Authentication event logging
- Security event tracking
- HIPAA compliance logging
- Data access logging
- Threat detection and alerting
- Audit trail management
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_, desc
from common.utils.logging import get_logger
from common.config.settings import get_settings
from ..models.audit import AuthAuditLog, AuditEventType, AuditSeverity, AuditStatus
from ..models.user import User

logger = get_logger(__name__)


class AuditService:
    """Service for audit logging and security monitoring."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = get_settings()
    
    async def log_event(self, user_id: Optional[str] = None, event_type: AuditEventType = None,
                       description: str = "", details: Dict[str, Any] = None, severity: AuditSeverity = AuditSeverity.LOW,
                       status: AuditStatus = AuditStatus.PROCESSED, ip_address: str = None, user_agent: str = None,
                       session_id: str = None, device_id: str = None, location: str = None, timezone: str = None,
                       isp: str = None, risk_score: float = 0.0, is_suspicious: bool = False,
                       threat_indicators: List[str] = None, hipaa_relevant: bool = False, phi_accessed: bool = False,
                       data_subject_id: str = None, related_user_id: str = None, related_session_id: str = None,
                       related_device_id: str = None) -> AuthAuditLog:
        """Log an audit event."""
        try:
            audit_log = AuthAuditLog(
                id=uuid.uuid4(),
                user_id=user_id,
                event_type=event_type,
                event_timestamp=datetime.utcnow(),
                severity=severity,
                status=status,
                description=description,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                device_id=device_id,
                location=location,
                timezone=timezone,
                isp=isp,
                risk_score=risk_score,
                is_suspicious=is_suspicious,
                threat_indicators=threat_indicators or [],
                hipaa_relevant=hipaa_relevant,
                phi_accessed=phi_accessed,
                data_subject_id=data_subject_id,
                related_user_id=related_user_id,
                related_session_id=related_session_id,
                related_device_id=related_device_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(audit_log)
            await self.db.commit()
            await self.db.refresh(audit_log)
            
            logger.info(f"Audit event logged: {event_type} - {description}")
            return audit_log
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to log audit event: {e}")
            raise
    
    async def log_login_success(self, user_id: str, ip_address: str = None, user_agent: str = None,
                              session_id: str = None, device_id: str = None, location: str = None,
                              timezone: str = None, isp: str = None) -> AuthAuditLog:
        """Log successful login event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.LOGIN_SUCCESS,
            description=f"Successful login for user {user_id}",
            severity=AuditSeverity.LOW,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id,
            location=location,
            timezone=timezone,
            isp=isp
        )
    
    async def log_login_failure(self, email: str, reason: str, ip_address: str = None, user_agent: str = None,
                              device_id: str = None, location: str = None, timezone: str = None,
                              isp: str = None, risk_score: float = 0.0) -> AuthAuditLog:
        """Log failed login event."""
        return await self.log_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            description=f"Failed login attempt for {email}: {reason}",
            severity=AuditSeverity.MEDIUM,
            status=AuditStatus.PENDING,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location=location,
            timezone=timezone,
            isp=isp,
            risk_score=risk_score,
            is_suspicious=risk_score > 0.7
        )
    
    async def log_logout(self, user_id: str, session_id: str, ip_address: str = None, user_agent: str = None,
                        device_id: str = None, reason: str = "manual_logout") -> AuthAuditLog:
        """Log logout event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.LOGOUT,
            description=f"User logout: {reason}",
            severity=AuditSeverity.LOW,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id
        )
    
    async def log_password_change(self, user_id: str, ip_address: str = None, user_agent: str = None,
                                session_id: str = None, device_id: str = None) -> AuthAuditLog:
        """Log password change event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.PASSWORD_CHANGE,
            description="Password changed successfully",
            severity=AuditSeverity.LOW,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id
        )
    
    async def log_password_reset(self, user_id: str, ip_address: str = None, user_agent: str = None,
                               device_id: str = None) -> AuthAuditLog:
        """Log password reset event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.PASSWORD_RESET,
            description="Password reset requested",
            severity=AuditSeverity.MEDIUM,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id
        )
    
    async def log_mfa_setup(self, user_id: str, device_name: str, ip_address: str = None, user_agent: str = None,
                          session_id: str = None, device_id: str = None) -> AuthAuditLog:
        """Log MFA device setup event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.MFA_DEVICE_ADDED,
            description=f"MFA device setup: {device_name}",
            severity=AuditSeverity.LOW,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id
        )
    
    async def log_mfa_verification(self, user_id: str, device_name: str, success: bool, ip_address: str = None,
                                 user_agent: str = None, session_id: str = None, device_id: str = None,
                                 risk_score: float = 0.0) -> AuthAuditLog:
        """Log MFA verification event."""
        event_type = AuditEventType.MFA_VERIFICATION_SUCCESS if success else AuditEventType.MFA_VERIFICATION_FAILURE
        status = AuditStatus.PROCESSED if success else AuditStatus.PENDING
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM
        
        return await self.log_event(
            user_id=user_id,
            event_type=event_type,
            description=f"MFA verification {'successful' if success else 'failed'} for {device_name}",
            severity=severity,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id,
            risk_score=risk_score,
            is_suspicious=risk_score > 0.7
        )
    
    async def log_session_creation(self, user_id: str, session_id: str, ip_address: str = None, user_agent: str = None,
                                 device_id: str = None, location: str = None, timezone: str = None,
                                 isp: str = None) -> AuthAuditLog:
        """Log session creation event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.SESSION_CREATED,
            description="New session created",
            severity=AuditSeverity.LOW,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id,
            location=location,
            timezone=timezone,
            isp=isp
        )
    
    async def log_session_revocation(self, user_id: str, session_id: str, reason: str, ip_address: str = None,
                                   user_agent: str = None, device_id: str = None) -> AuthAuditLog:
        """Log session revocation event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.SESSION_REVOKED,
            description=f"Session revoked: {reason}",
            severity=AuditSeverity.MEDIUM,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id
        )
    
    async def log_data_access(self, user_id: str, resource_type: str, resource_id: str, action: str,
                            data_subject_id: str = None, purpose: str = None, justification: str = None,
                            ip_address: str = None, user_agent: str = None, session_id: str = None,
                            phi_involved: bool = False, hipaa_relevant: bool = False) -> AuthAuditLog:
        """Log data access event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.DATA_ACCESSED,
            description=f"Data access: {action} on {resource_type} {resource_id}",
            severity=AuditSeverity.LOW,
            status=AuditStatus.PROCESSED,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            data_subject_id=data_subject_id,
            hipaa_relevant=hipaa_relevant,
            phi_accessed=phi_involved,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "purpose": purpose,
                "justification": justification
            }
        )
    
    async def log_security_alert(self, user_id: str, alert_type: str, title: str, description: str,
                               severity: AuditSeverity = AuditSeverity.MEDIUM, threat_level: str = "medium",
                               threat_indicators: List[str] = None, ip_address: str = None, user_agent: str = None,
                               session_id: str = None, device_id: str = None) -> AuthAuditLog:
        """Log security alert event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.SECURITY_ALERT,
            description=f"Security alert: {title}",
            severity=severity,
            status=AuditStatus.PENDING,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id,
            threat_indicators=threat_indicators or [],
            details={
                "alert_type": alert_type,
                "title": title,
                "description": description,
                "threat_level": threat_level
            }
        )
    
    async def log_suspicious_activity(self, user_id: str, activity_type: str, description: str,
                                    risk_score: float, threat_indicators: List[str] = None,
                                    ip_address: str = None, user_agent: str = None, session_id: str = None,
                                    device_id: str = None) -> AuthAuditLog:
        """Log suspicious activity event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            description=f"Suspicious activity detected: {activity_type}",
            severity=AuditSeverity.MEDIUM,
            status=AuditStatus.PENDING,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id,
            risk_score=risk_score,
            is_suspicious=True,
            threat_indicators=threat_indicators or []
        )
    
    async def log_hipaa_violation(self, user_id: str, violation_type: str, description: str,
                                data_subject_id: str = None, ip_address: str = None, user_agent: str = None,
                                session_id: str = None, device_id: str = None) -> AuthAuditLog:
        """Log HIPAA violation event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.COMPLIANCE_VIOLATION,
            description=f"HIPAA violation: {violation_type}",
            severity=AuditSeverity.CRITICAL,
            status=AuditStatus.PENDING,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_id=device_id,
            data_subject_id=data_subject_id,
            hipaa_relevant=True,
            phi_accessed=True,
            details={
                "violation_type": violation_type,
                "description": description
            }
        )
    
    async def get_user_audit_logs(self, user_id: str, limit: int = 100, offset: int = 0,
                                event_types: List[AuditEventType] = None, severity_levels: List[AuditSeverity] = None,
                                start_date: datetime = None, end_date: datetime = None) -> List[AuthAuditLog]:
        """Get audit logs for a specific user."""
        try:
            query = self.db.query(AuthAuditLog).filter(AuthAuditLog.user_id == user_id)
            
            if event_types:
                query = query.filter(AuthAuditLog.event_type.in_(event_types))
            
            if severity_levels:
                query = query.filter(AuthAuditLog.severity.in_(severity_levels))
            
            if start_date:
                query = query.filter(AuthAuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuthAuditLog.event_timestamp <= end_date)
            
            return query.order_by(desc(AuthAuditLog.event_timestamp)).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get user audit logs: {e}")
            return []
    
    async def get_suspicious_activities(self, risk_threshold: float = 0.7, limit: int = 100,
                                      start_date: datetime = None, end_date: datetime = None) -> List[AuthAuditLog]:
        """Get suspicious activities above a risk threshold."""
        try:
            query = self.db.query(AuthAuditLog).filter(
                and_(
                    AuthAuditLog.is_suspicious == True,
                    AuthAuditLog.risk_score >= risk_threshold
                )
            )
            
            if start_date:
                query = query.filter(AuthAuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuthAuditLog.event_timestamp <= end_date)
            
            return query.order_by(desc(AuthAuditLog.event_timestamp)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get suspicious activities: {e}")
            return []
    
    async def get_hipaa_events(self, limit: int = 100, start_date: datetime = None,
                             end_date: datetime = None) -> List[AuthAuditLog]:
        """Get HIPAA-relevant audit events."""
        try:
            query = self.db.query(AuthAuditLog).filter(AuthAuditLog.hipaa_relevant == True)
            
            if start_date:
                query = query.filter(AuthAuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuthAuditLog.event_timestamp <= end_date)
            
            return query.order_by(desc(AuthAuditLog.event_timestamp)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get HIPAA events: {e}")
            return []
    
    async def get_failed_login_attempts(self, user_id: str = None, limit: int = 100,
                                      start_date: datetime = None, end_date: datetime = None) -> List[AuthAuditLog]:
        """Get failed login attempts."""
        try:
            query = self.db.query(AuthAuditLog).filter(AuthAuditLog.event_type == AuditEventType.LOGIN_FAILURE)
            
            if user_id:
                query = query.filter(AuthAuditLog.user_id == user_id)
            
            if start_date:
                query = query.filter(AuthAuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuthAuditLog.event_timestamp <= end_date)
            
            return query.order_by(desc(AuthAuditLog.event_timestamp)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get failed login attempts: {e}")
            return []
    
    async def get_audit_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get audit statistics for reporting."""
        try:
            query = self.db.query(AuthAuditLog)
            
            if start_date:
                query = query.filter(AuthAuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuthAuditLog.event_timestamp <= end_date)
            
            total_events = query.count()
            
            # Count by event type
            event_type_counts = {}
            for event_type in AuditEventType:
                count = query.filter(AuthAuditLog.event_type == event_type).count()
                if count > 0:
                    event_type_counts[event_type.value] = count
            
            # Count by severity
            severity_counts = {}
            for severity in AuditSeverity:
                count = query.filter(AuthAuditLog.severity == severity).count()
                if count > 0:
                    severity_counts[severity.value] = count
            
            # Count suspicious activities
            suspicious_count = query.filter(AuthAuditLog.is_suspicious == True).count()
            
            # Count HIPAA events
            hipaa_count = query.filter(AuthAuditLog.hipaa_relevant == True).count()
            
            # Count PHI access
            phi_count = query.filter(AuthAuditLog.phi_accessed == True).count()
            
            return {
                "total_events": total_events,
                "event_type_counts": event_type_counts,
                "severity_counts": severity_counts,
                "suspicious_activities": suspicious_count,
                "hipaa_events": hipaa_count,
                "phi_access_events": phi_count,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            return {}
    
    async def cleanup_old_audit_logs(self, retention_days: int = 365) -> int:
        """Clean up old audit logs based on retention policy."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count logs to be deleted
            count = self.db.query(AuthAuditLog).filter(
                AuthAuditLog.event_timestamp < cutoff_date
            ).count()
            
            # Delete old logs
            self.db.query(AuthAuditLog).filter(
                AuthAuditLog.event_timestamp < cutoff_date
            ).delete()
            
            await self.db.commit()
            
            logger.info(f"Cleaned up {count} old audit logs (older than {retention_days} days)")
            return count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cleanup old audit logs: {e}")
            return 0
    
    async def export_audit_logs(self, start_date: datetime = None, end_date: datetime = None,
                              event_types: List[AuditEventType] = None, format: str = "json") -> str:
        """Export audit logs in specified format."""
        try:
            query = self.db.query(AuthAuditLog)
            
            if start_date:
                query = query.filter(AuthAuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuthAuditLog.event_timestamp <= end_date)
            
            if event_types:
                query = query.filter(AuthAuditLog.event_type.in_(event_types))
            
            logs = query.order_by(AuthAuditLog.event_timestamp).all()
            
            if format.lower() == "json":
                import json
                return json.dumps([log.to_dict() for log in logs], default=str, indent=2)
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    "id", "user_id", "event_type", "event_timestamp", "severity", "status",
                    "description", "ip_address", "user_agent", "session_id", "device_id",
                    "risk_score", "is_suspicious", "hipaa_relevant", "phi_accessed"
                ])
                
                # Write data
                for log in logs:
                    writer.writerow([
                        log.id, log.user_id, log.event_type.value, log.event_timestamp,
                        log.severity.value, log.status.value, log.description, log.ip_address,
                        log.user_agent, log.session_id, log.device_id, log.risk_score,
                        log.is_suspicious, log.hipaa_relevant, log.phi_accessed
                    ])
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            return ""
    
    async def analyze_user_behavior(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze user behavior patterns for security assessment."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user's audit logs
            logs = await self.get_user_audit_logs(
                user_id=user_id,
                start_date=start_date,
                limit=1000
            )
            
            if not logs:
                return {"user_id": user_id, "analysis_period_days": days, "no_activity": True}
            
            # Analyze patterns
            login_count = len([log for log in logs if log.event_type == AuditEventType.LOGIN_SUCCESS])
            failed_login_count = len([log for log in logs if log.event_type == AuditEventType.LOGIN_FAILURE])
            logout_count = len([log for log in logs if log.event_type == AuditEventType.LOGOUT])
            suspicious_count = len([log for log in logs if log.is_suspicious])
            hipaa_count = len([log for log in logs if log.hipaa_relevant])
            phi_count = len([log for log in logs if log.phi_accessed])
            
            # Calculate risk score
            risk_factors = []
            if failed_login_count > 5:
                risk_factors.append("high_failed_logins")
            if suspicious_count > 3:
                risk_factors.append("suspicious_activities")
            if hipaa_count > 10:
                risk_factors.append("frequent_hipaa_access")
            
            risk_score = len(risk_factors) * 0.3
            
            # Get unique IP addresses and devices
            unique_ips = set(log.ip_address for log in logs if log.ip_address)
            unique_devices = set(log.device_id for log in logs if log.device_id)
            
            return {
                "user_id": user_id,
                "analysis_period_days": days,
                "total_events": len(logs),
                "login_count": login_count,
                "failed_login_count": failed_login_count,
                "logout_count": logout_count,
                "suspicious_activities": suspicious_count,
                "hipaa_events": hipaa_count,
                "phi_access_events": phi_count,
                "unique_ip_addresses": len(unique_ips),
                "unique_devices": len(unique_devices),
                "risk_factors": risk_factors,
                "calculated_risk_score": min(risk_score, 1.0),
                "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.3 else "low"
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user behavior: {e}")
            return {"user_id": user_id, "error": str(e)} 