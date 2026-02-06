"""
Role-based access control models for the Personal Health Assistant.

This module defines comprehensive RBAC models with fine-grained permissions
for different user types and data access patterns.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
import uuid
from ..models import Base


class PermissionScope(str, Enum):
    """Permission scope enumeration."""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    USER = "user"
    DATA = "data"
    SYSTEM = "system"


class PermissionAction(str, Enum):
    """Permission action enumeration."""
    # CRUD operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Special operations
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    GRANT = "grant"
    REVOKE = "revoke"
    
    # Health-specific operations
    PRESCRIBE = "prescribe"
    DIAGNOSE = "diagnose"
    TREAT = "treat"
    MONITOR = "monitor"
    ANALYZE = "analyze"
    REPORT = "report"
    
    # Administrative operations
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SYSTEM = "manage_system"
    AUDIT = "audit"


class ResourceType(str, Enum):
    """Resource type enumeration for fine-grained permissions."""
    # User resources
    USER_PROFILE = "user_profile"
    USER_PREFERENCES = "user_preferences"
    USER_SESSIONS = "user_sessions"
    
    # Health data resources
    VITAL_SIGNS = "vital_signs"
    SYMPTOMS = "symptoms"
    MEDICATIONS = "medications"
    LAB_RESULTS = "lab_results"
    MEDICAL_IMAGES = "medical_images"
    MEDICAL_REPORTS = "medical_reports"
    HEALTH_GOALS = "health_goals"
    ACTIVITY_DATA = "activity_data"
    SLEEP_DATA = "sleep_data"
    NUTRITION_DATA = "nutrition_data"
    
    # Device resources
    DEVICES = "devices"
    DEVICE_DATA = "device_data"
    
    # Medical resources
    MEDICAL_CONDITIONS = "medical_conditions"
    TREATMENT_PLANS = "treatment_plans"
    APPOINTMENTS = "appointments"
    PRESCRIPTIONS = "prescriptions"
    
    # Consent and privacy
    CONSENT_RECORDS = "consent_records"
    DATA_ACCESS_LOGS = "data_access_logs"
    PRIVACY_SETTINGS = "privacy_settings"
    
    # Administrative resources
    USERS = "users"
    ROLES = "roles"
    PERMISSIONS = "permissions"
    AUDIT_LOGS = "audit_logs"
    SYSTEM_CONFIG = "system_config"
    
    # AI and analytics
    AI_INSIGHTS = "ai_insights"
    ANALYTICS_REPORTS = "analytics_reports"
    PREDICTIONS = "predictions"
    
    # E-commerce
    PRODUCTS = "products"
    ORDERS = "orders"
    PAYMENTS = "payments"
    
    # Insurance
    INSURANCE_POLICIES = "insurance_policies"
    CLAIMS = "claims"
    COVERAGE = "coverage"


class Role(Base):
    """Role model for role-based access control."""
    
    __tablename__ = "roles"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)  # System-defined roles cannot be deleted
    is_active = Column(Boolean, default=True)
    
    # HIPAA compliance
    hipaa_compliant = Column(Boolean, default=False)
    data_access_level = Column(String, default="none")  # none, limited, full
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    """Permission model for fine-grained access control."""
    
    __tablename__ = "permissions"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    resource_type = Column(SQLEnum(ResourceType), nullable=False)
    action = Column(SQLEnum(PermissionAction), nullable=False)
    scope = Column(SQLEnum(PermissionScope), default=PermissionScope.USER)
    
    # Conditions for permission evaluation
    conditions = Column(Text, nullable=True)  # JSON string for complex conditions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name}, resource={self.resource_type}, action={self.action})>"
    
    @property
    def full_name(self) -> str:
        """Get full permission name."""
        return f"{self.resource_type}:{self.action}"


class UserRole(Base):
    """Many-to-many relationship between users and roles."""
    
    __tablename__ = "user_roles"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("auth.roles.id"), nullable=False)
    
    # Role assignment details
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Context for role assignment
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    context = Column(Text, nullable=True)  # JSON string for additional context
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(Base):
    """Many-to-many relationship between roles and permissions."""
    
    __tablename__ = "role_permissions"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("auth.roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("auth.permissions.id"), nullable=False)
    
    # Permission grant details
    granted_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Conditions for this specific role-permission combination
    conditions = Column(Text, nullable=True)  # JSON string for conditions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


# Pydantic models for API
class RoleBase(BaseModel):
    """Base role model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    hipaa_compliant: bool = False
    data_access_level: str = "none"


class RoleCreate(RoleBase):
    """Model for role creation."""
    pass


class RoleUpdate(BaseModel):
    """Model for role updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    hipaa_compliant: Optional[bool] = None
    data_access_level: Optional[str] = None


class RoleResponse(RoleBase):
    """Model for role API responses."""
    id: uuid.UUID
    is_system_role: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """Base permission model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    resource_type: ResourceType
    action: PermissionAction
    scope: PermissionScope = PermissionScope.USER
    conditions: Optional[str] = None


class PermissionCreate(PermissionBase):
    """Model for permission creation."""
    pass


class PermissionUpdate(BaseModel):
    """Model for permission updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    action: Optional[PermissionAction] = None
    scope: Optional[PermissionScope] = None
    conditions: Optional[str] = None


class PermissionResponse(PermissionBase):
    """Model for permission API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserRoleBase(BaseModel):
    """Base user role model."""
    role_id: uuid.UUID
    expires_at: Optional[datetime] = None
    organization_id: Optional[uuid.UUID] = None
    context: Optional[str] = None


class UserRoleCreate(UserRoleBase):
    """Model for user role assignment."""
    pass


class UserRoleUpdate(BaseModel):
    """Model for user role updates."""
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    context: Optional[str] = None


class UserRoleResponse(UserRoleBase):
    """Model for user role API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    assigned_by: Optional[uuid.UUID] = None
    assigned_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RolePermissionBase(BaseModel):
    """Base role permission model."""
    permission_id: uuid.UUID
    expires_at: Optional[datetime] = None
    conditions: Optional[str] = None


class RolePermissionCreate(RolePermissionBase):
    """Model for role permission assignment."""
    pass


class RolePermissionUpdate(BaseModel):
    """Model for role permission updates."""
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    conditions: Optional[str] = None


class RolePermissionResponse(RolePermissionBase):
    """Model for role permission API responses."""
    id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None
    granted_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Predefined roles and permissions
DEFAULT_ROLES = {
    "patient": {
        "description": "Patient user with access to own health data",
        "hipaa_compliant": True,
        "data_access_level": "limited",
        "permissions": [
            (ResourceType.USER_PROFILE, PermissionAction.READ),
            (ResourceType.USER_PROFILE, PermissionAction.UPDATE),
            (ResourceType.VITAL_SIGNS, PermissionAction.READ),
            (ResourceType.VITAL_SIGNS, PermissionAction.CREATE),
            (ResourceType.SYMPTOMS, PermissionAction.READ),
            (ResourceType.SYMPTOMS, PermissionAction.CREATE),
            (ResourceType.MEDICATIONS, PermissionAction.READ),
            (ResourceType.HEALTH_GOALS, PermissionAction.READ),
            (ResourceType.HEALTH_GOALS, PermissionAction.CREATE),
            (ResourceType.HEALTH_GOALS, PermissionAction.UPDATE),
            (ResourceType.CONSENT_RECORDS, PermissionAction.READ),
            (ResourceType.CONSENT_RECORDS, PermissionAction.CREATE),
        ]
    },
    "doctor": {
        "description": "Healthcare provider with access to patient data",
        "hipaa_compliant": True,
        "data_access_level": "full",
        "permissions": [
            (ResourceType.USER_PROFILE, PermissionAction.READ),
            (ResourceType.USER_PROFILE, PermissionAction.UPDATE),
            (ResourceType.VITAL_SIGNS, PermissionAction.READ),
            (ResourceType.SYMPTOMS, PermissionAction.READ),
            (ResourceType.MEDICATIONS, PermissionAction.READ),
            (ResourceType.MEDICATIONS, PermissionAction.CREATE),
            (ResourceType.MEDICATIONS, PermissionAction.UPDATE),
            (ResourceType.LAB_RESULTS, PermissionAction.READ),
            (ResourceType.MEDICAL_IMAGES, PermissionAction.READ),
            (ResourceType.MEDICAL_REPORTS, PermissionAction.READ),
            (ResourceType.MEDICAL_REPORTS, PermissionAction.CREATE),
            (ResourceType.TREATMENT_PLANS, PermissionAction.READ),
            (ResourceType.TREATMENT_PLANS, PermissionAction.CREATE),
            (ResourceType.TREATMENT_PLANS, PermissionAction.UPDATE),
            (ResourceType.PRESCRIPTIONS, PermissionAction.CREATE),
            (ResourceType.PRESCRIPTIONS, PermissionAction.READ),
            (ResourceType.MEDICAL_CONDITIONS, PermissionAction.CREATE),
            (ResourceType.TREATMENT_PLANS, PermissionAction.CREATE),
        ]
    },
    "admin": {
        "description": "System administrator with full access",
        "hipaa_compliant": True,
        "data_access_level": "full",
        "permissions": [
            (ResourceType.SYSTEM_CONFIG, PermissionAction.MANAGE_SYSTEM),
            (ResourceType.USERS, PermissionAction.MANAGE_USERS),
            (ResourceType.ROLES, PermissionAction.MANAGE_ROLES),
            (ResourceType.AUDIT_LOGS, PermissionAction.READ),
            (ResourceType.SYSTEM_CONFIG, PermissionAction.READ),
            (ResourceType.SYSTEM_CONFIG, PermissionAction.UPDATE),
        ]
    },
    "pharma": {
        "description": "Pharmaceutical representative with limited access",
        "hipaa_compliant": True,
        "data_access_level": "limited",
        "permissions": [
            (ResourceType.MEDICATIONS, PermissionAction.READ),
            (ResourceType.PRODUCTS, PermissionAction.READ),
            (ResourceType.ANALYTICS_REPORTS, PermissionAction.READ),
        ]
    },
    "insurance": {
        "description": "Insurance provider with claims access",
        "hipaa_compliant": True,
        "data_access_level": "limited",
        "permissions": [
            (ResourceType.INSURANCE_POLICIES, PermissionAction.READ),
            (ResourceType.CLAIMS, PermissionAction.READ),
            (ResourceType.CLAIMS, PermissionAction.CREATE),
            (ResourceType.CLAIMS, PermissionAction.UPDATE),
            (ResourceType.MEDICAL_REPORTS, PermissionAction.READ),
        ]
    },
    "researcher": {
        "description": "Research personnel with anonymized data access",
        "hipaa_compliant": True,
        "data_access_level": "limited",
        "permissions": [
            (ResourceType.ANALYTICS_REPORTS, PermissionAction.READ),
            (ResourceType.AI_INSIGHTS, PermissionAction.READ),
            (ResourceType.PREDICTIONS, PermissionAction.READ),
        ]
    }
} 