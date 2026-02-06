"""
Consent management service for HIPAA compliance and data governance.

This service handles:
- Consent record creation and management
- Consent template management
- Consent verification and validation
- HIPAA authorization tracking
- GDPR compliance management
- Consent withdrawal and updates
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_, desc
from common.utils.logging import get_logger
from common.config.settings import get_settings
from ..models.consent import ConsentRecord, ConsentTemplate, ConsentStatus, ConsentType
from ..models.user import User

logger = get_logger(__name__)


class ConsentService:
    """Service for consent management operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = get_settings()
    
    async def create_consent_record(self, user_id: str, consent_type: ConsentType, 
                                  consent_scope: str, title: str, description: str,
                                  detailed_terms: str = None, data_categories: List[str] = None,
                                  purpose: str = None, justification: str = None,
                                  hipaa_authorization: bool = False, hipaa_expiration: datetime = None,
                                  hipaa_conditions: Dict[str, Any] = None,
                                  created_by: str = None) -> ConsentRecord:
        """Create a new consent record."""
        try:
            consent_record = ConsentRecord(
                id=uuid.uuid4(),
                user_id=user_id,
                consent_type=consent_type,
                consent_scope=consent_scope,
                status=ConsentStatus.PENDING,
                version="1.0",
                title=title,
                description=description,
                detailed_terms=detailed_terms,
                data_categories=data_categories or [],
                purpose=purpose,
                justification=justification,
                hipaa_authorization=hipaa_authorization,
                hipaa_expiration=hipaa_expiration,
                hipaa_conditions=hipaa_conditions or {},
                created_by=created_by,
                requested_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(consent_record)
            await self.db.commit()
            await self.db.refresh(consent_record)
            
            logger.info(f"Consent record created: {consent_record.id} for user {user_id}")
            return consent_record
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create consent record: {e}")
            raise
    
    async def grant_consent(self, consent_id: str, granted_by: str = None,
                          consent_method: str = "digital", consent_location: str = None,
                          witness_present: bool = False) -> ConsentRecord:
        """Grant consent for a consent record."""
        try:
            consent_record = await self.db.get(ConsentRecord, consent_id)
            if not consent_record:
                raise ValueError(f"Consent record {consent_id} not found")
            
            consent_record.status = ConsentStatus.GRANTED
            consent_record.granted_at = datetime.utcnow()
            consent_record.consent_method = consent_method
            consent_record.consent_location = consent_location
            consent_record.witness_present = witness_present
            consent_record.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(consent_record)
            
            logger.info(f"Consent granted: {consent_id}")
            return consent_record
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to grant consent: {e}")
            raise
    
    async def withdraw_consent(self, consent_id: str, withdrawn_by: str = None,
                             reason: str = None) -> ConsentRecord:
        """Withdraw consent for a consent record."""
        try:
            consent_record = await self.db.get(ConsentRecord, consent_id)
            if not consent_record:
                raise ValueError(f"Consent record {consent_id} not found")
            
            consent_record.status = ConsentStatus.WITHDRAWN
            consent_record.withdrawn_at = datetime.utcnow()
            consent_record.updated_at =datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(consent_record)
            
            logger.info(f"Consent withdrawn: {consent_id}")
            return consent_record
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to withdraw consent: {e}")
            raise
    
    async def update_consent(self, consent_id: str, updates: Dict[str, Any],
                           updated_by: str = None) -> ConsentRecord:
        """Update a consent record."""
        try:
            consent_record = await self.db.get(ConsentRecord, consent_id)
            if not consent_record:
                raise ValueError(f"Consent record {consent_id} not found")
            
            # Update allowed fields
            allowed_fields = ['title', 'description', 'detailed_terms', 'data_categories',
                            'purpose', 'justification', 'hipaa_conditions']
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(consent_record, field):
                    setattr(consent_record, field, value)
            
            consent_record.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(consent_record)
            
            logger.info(f"Consent record updated: {consent_id}")
            return consent_record
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update consent record: {e}")
            raise
    
    async def get_user_consents(self, user_id: str, status: ConsentStatus = None,
                              consent_type: ConsentType = None, active_only: bool = True) -> List[ConsentRecord]:
        """Get consent records for a user."""
        try:
            query = self.db.query(ConsentRecord).filter(ConsentRecord.user_id == user_id)
            
            if status:
                query = query.filter(ConsentRecord.status == status)
            
            if consent_type:
                query = query.filter(ConsentRecord.consent_type == consent_type)
            
            if active_only:
                query = query.filter(
                    and_(
                        ConsentRecord.status == ConsentStatus.GRANTED,
                        or_(
                            ConsentRecord.expires_at.is_(None),
                            ConsentRecord.expires_at > datetime.utcnow()
                        )
                    )
                )
            
            consent_records = await query.order_by(desc(ConsentRecord.created_at)).all()
            return consent_records
            
        except Exception as e:
            logger.error(f"Failed to get user consents: {e}")
            raise
    
    async def get_consent_by_id(self, consent_id: str) -> Optional[ConsentRecord]:
        """Get a consent record by ID."""
        try:
            consent_record = await self.db.get(ConsentRecord, consent_id)
            return consent_record
            
        except Exception as e:
            logger.error(f"Failed to get consent record: {e}")
            raise
    
    async def verify_consent(self, user_id: str, consent_type: ConsentType,
                           data_categories: List[str] = None, purpose: str = None) -> bool:
        """Verify if user has valid consent for the specified type and categories."""
        try:
            query = self.db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.user_id == user_id,
                    ConsentRecord.consent_type == consent_type,
                    ConsentRecord.status == ConsentStatus.GRANTED,
                    or_(
                        ConsentRecord.expires_at.is_(None),
                        ConsentRecord.expires_at > datetime.utcnow()
                    )
                )
            )
            
            consent_records = await query.all()
            
            if not consent_records:
                return False
            
            # Check if any consent record covers the required data categories
            for consent_record in consent_records:
                if data_categories:
                    if not consent_record.data_categories or not all(
                        category in consent_record.data_categories for category in data_categories
                    ):
                        continue
                
                if purpose and consent_record.purpose and purpose not in consent_record.purpose:
                    continue
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify consent: {e}")
            raise
    
    async def create_consent_template(self, name: str, consent_type: ConsentType,
                                    title: str, description: str, detailed_terms: str,
                                    sections: Dict[str, Any] = None,
                                    required_fields: List[str] = None,
                                    optional_fields: List[str] = None,
                                    legal_requirements: List[str] = None,
                                    regulatory_compliance: List[str] = None) -> ConsentTemplate:
        """Create a new consent template."""
        try:
            template = ConsentTemplate(
                id=uuid.uuid4(),
                name=name,
                consent_type=consent_type,
                version="1.0",
                is_active=True,
                title=title,
                description=description,
                detailed_terms=detailed_terms,
                sections=sections or {},
                required_fields=required_fields or [],
                optional_fields=optional_fields or [],
                legal_requirements=legal_requirements or [],
                regulatory_compliance=regulatory_compliance or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)
            
            logger.info(f"Consent template created: {template.id}")
            return template
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create consent template: {e}")
            raise
    
    async def get_consent_templates(self, consent_type: ConsentType = None,
                                  active_only: bool = True) -> List[ConsentTemplate]:
        """Get consent templates."""
        try:
            query = self.db.query(ConsentTemplate)
            
            if consent_type:
                query = query.filter(ConsentTemplate.consent_type == consent_type)
            
            if active_only:
                query = query.filter(ConsentTemplate.is_active == True)
            
            templates = await query.order_by(ConsentTemplate.name).all()
            return templates
            
        except Exception as e:
            logger.error(f"Failed to get consent templates: {e}")
            raise
    
    async def get_hipaa_authorizations(self, user_id: str, active_only: bool = True) -> List[ConsentRecord]:
        """Get HIPAA authorizations for a user."""
        try:
            query = self.db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.user_id == user_id,
                    ConsentRecord.hipaa_authorization == True
                )
            )
            
            if active_only:
                query = query.filter(
                    and_(
                        ConsentRecord.status == ConsentStatus.GRANTED,
                        or_(
                            ConsentRecord.hipaa_expiration.is_(None),
                            ConsentRecord.hipaa_expiration > datetime.utcnow()
                        )
                    )
                )
            
            authorizations = await query.order_by(desc(ConsentRecord.created_at)).all()
            return authorizations
            
        except Exception as e:
            logger.error(f"Failed to get HIPAA authorizations: {e}")
            raise
    
    async def check_hipaa_compliance(self, user_id: str, data_categories: List[str],
                                   purpose: str) -> Dict[str, Any]:
        """Check HIPAA compliance for data access."""
        try:
            # Get active HIPAA authorizations
            authorizations = await self.get_hipaa_authorizations(user_id, active_only=True)
            
            compliance_result = {
                "compliant": False,
                "authorizations": [],
                "missing_authorizations": [],
                "recommendations": []
            }
            
            if not authorizations:
                compliance_result["missing_authorizations"].append("No HIPAA authorizations found")
                compliance_result["recommendations"].append("Obtain HIPAA authorization from patient")
                return compliance_result
            
            # Check if any authorization covers the required data categories and purpose
            for auth in authorizations:
                if data_categories and auth.data_categories:
                    if all(category in auth.data_categories for category in data_categories):
                        if purpose and auth.purpose and purpose in auth.purpose:
                            compliance_result["compliant"] = True
                            compliance_result["authorizations"].append({
                                "id": str(auth.id),
                                "title": auth.title,
                                "expires_at": auth.hipaa_expiration
                            })
            
            if not compliance_result["compliant"]:
                compliance_result["recommendations"].append(
                    "Ensure HIPAA authorization covers required data categories and purpose"
                )
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"Failed to check HIPAA compliance: {e}")
            raise
    
    async def get_consent_statistics(self, user_id: str = None, 
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """Get consent statistics."""
        try:
            query = self.db.query(ConsentRecord)
            
            if user_id:
                query = query.filter(ConsentRecord.user_id == user_id)
            
            if start_date:
                query = query.filter(ConsentRecord.created_at >= start_date)
            
            if end_date:
                query = query.filter(ConsentRecord.created_at <= end_date)
            
            total_consents = await query.count()
            
            # Get counts by status
            granted_consents = await query.filter(ConsentRecord.status == ConsentStatus.GRANTED).count()
            pending_consents = await query.filter(ConsentRecord.status == ConsentStatus.PENDING).count()
            withdrawn_consents = await query.filter(ConsentRecord.status == ConsentStatus.WITHDRAWN).count()
            
            # Get counts by type
            hipaa_consents = await query.filter(ConsentRecord.hipaa_authorization == True).count()
            
            return {
                "total_consents": total_consents,
                "granted_consents": granted_consents,
                "pending_consents": pending_consents,
                "withdrawn_consents": withdrawn_consents,
                "hipaa_consents": hipaa_consents,
                "grant_rate": (granted_consents / total_consents * 100) if total_consents > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get consent statistics: {e}")
            raise
    
    async def cleanup_expired_consents(self) -> int:
        """Clean up expired consent records."""
        try:
            expired_consents = await self.db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.expires_at.isnot(None),
                    ConsentRecord.expires_at < datetime.utcnow(),
                    ConsentRecord.status == ConsentStatus.GRANTED
                )
            ).all()
            
            count = len(expired_consents)
            for consent in expired_consents:
                consent.status = ConsentStatus.EXPIRED
                consent.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Cleaned up {count} expired consent records")
            return count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cleanup expired consents: {e}")
            raise 