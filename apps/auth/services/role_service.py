"""
Role and Permission management service.

This service handles:
- Role creation, updates, and deletion
- Permission management
- Role assignments to users
- Permission assignments to roles
- Role-based access control (RBAC)
- HIPAA compliance role management
"""

import uuid
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_
from common.utils.logging import get_logger
from common.config.settings import get_settings
from ..models.roles import Role, Permission, UserRole, RolePermission
from ..models.user import User

logger = get_logger(__name__)


class RoleService:
    """Service for role and permission management."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = get_settings()
    
    def create_role(self, role_data: Dict[str, Any], created_by: str) -> Role:
        """Create a new role."""
        try:
            role = Role(
                id=uuid.uuid4(),
                name=role_data['name'],
                description=role_data.get('description', ''),
                is_system_role=role_data.get('is_system_role', False),
                is_active=role_data.get('is_active', True),
                hipaa_compliant=role_data.get('hipaa_compliant', False),
                data_access_level=role_data.get('data_access_level', 'basic'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
            
            logger.info(f"Created role: {role.name} by user: {created_by}")
            return role
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create role: {e}")
            raise
    
    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        try:
            return self.db.query(Role).filter(Role.id == role_id).first()
            
        except Exception as e:
            logger.error(f"Failed to get role by ID: {e}")
            return None
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        try:
            return self.db.query(Role).filter(Role.name == name).first()
            
        except Exception as e:
            logger.error(f"Failed to get role by name: {e}")
            return None
    
    def get_all_roles(self, include_inactive: bool = False) -> List[Role]:
        """Get all roles."""
        try:
            query = self.db.query(Role)
            if not include_inactive:
                query = query.filter(Role.is_active == True)
            return query.all()
            
        except Exception as e:
            logger.error(f"Failed to get all roles: {e}")
            return []
    
    def update_role(self, role_id: str, role_data: Dict[str, Any], updated_by: str) -> Optional[Role]:
        """Update an existing role."""
        try:
            role = self.get_role_by_id(role_id)
            if not role:
                logger.warning(f"Role not found: {role_id}")
                return None
            
            # Update fields
            for field, value in role_data.items():
                if hasattr(role, field) and field not in ['id', 'created_at']:
                    setattr(role, field, value)
            
            role.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(role)
            
            logger.info(f"Updated role: {role.name} by user: {updated_by}")
            return role
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update role: {e}")
            return None
    
    def delete_role(self, role_id: str, deleted_by: str) -> bool:
        """Delete a role (soft delete by setting is_active to False)."""
        try:
            role = self.get_role_by_id(role_id)
            if not role:
                logger.warning(f"Role not found: {role_id}")
                return False
            
            if role.is_system_role:
                logger.warning(f"Cannot delete system role: {role.name}")
                return False
            
            # Check if role is assigned to any users
            user_roles = self.db.query(UserRole).filter(
                and_(UserRole.role_id == role_id, UserRole.is_active == True)
            ).count()
            
            if user_roles > 0:
                logger.warning(f"Cannot delete role with active users: {role.name}")
                return False
            
            # Soft delete
            role.is_active = False
            role.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Deleted role: {role.name} by user: {deleted_by}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete role: {e}")
            return False
    
    def create_permission(self, permission_data: Dict[str, Any], created_by: str) -> Permission:
        """Create a new permission."""
        try:
            permission = Permission(
                id=uuid.uuid4(),
                name=permission_data['name'],
                description=permission_data.get('description', ''),
                resource_type=permission_data['resource_type'],
                action=permission_data['action'],
                scope=permission_data.get('scope', 'global'),
                conditions=permission_data.get('conditions', {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            
            logger.info(f"Created permission: {permission.name} by user: {created_by}")
            return permission
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create permission: {e}")
            raise
    
    def get_permission_by_id(self, permission_id: str) -> Optional[Permission]:
        """Get permission by ID."""
        try:
            return self.db.query(Permission).filter(Permission.id == permission_id).first()
            
        except Exception as e:
            logger.error(f"Failed to get permission by ID: {e}")
            return None
    
    def get_permissions_by_resource(self, resource_type: str) -> List[Permission]:
        """Get permissions by resource type."""
        try:
            return self.db.query(Permission).filter(Permission.resource_type == resource_type).all()
            
        except Exception as e:
            logger.error(f"Failed to get permissions by resource: {e}")
            return []
    
    def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: str, 
                          expires_at: Optional[datetime] = None, context: Dict[str, Any] = None) -> UserRole:
        """Assign a role to a user."""
        try:
            # Check if role is already assigned
            existing_assignment = self.db.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if existing_assignment:
                logger.warning(f"Role already assigned to user: {user_id}, role: {role_id}")
                return existing_assignment
            
            user_role = UserRole(
                id=uuid.uuid4(),
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
                assigned_at=datetime.utcnow(),
                expires_at=expires_at,
                is_active=True,
                context=context or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(user_role)
            self.db.commit()
            self.db.refresh(user_role)
            
            logger.info(f"Assigned role {role_id} to user {user_id} by {assigned_by}")
            return user_role
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to assign role to user: {e}")
            raise
    
    def remove_role_from_user(self, user_id: str, role_id: str, removed_by: str) -> bool:
        """Remove a role from a user."""
        try:
            user_role = self.db.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if not user_role:
                logger.warning(f"Role assignment not found: user {user_id}, role {role_id}")
                return False
            
            user_role.is_active = False
            user_role.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Removed role {role_id} from user {user_id} by {removed_by}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove role from user: {e}")
            return False
    
    def get_user_roles(self, user_id: str, include_inactive: bool = False) -> List[UserRole]:
        """Get all roles assigned to a user."""
        try:
            query = self.db.query(UserRole).filter(UserRole.user_id == user_id)
            if not include_inactive:
                query = query.filter(UserRole.is_active == True)
            return query.all()
            
        except Exception as e:
            logger.error(f"Failed to get user roles: {e}")
            return []
    
    def assign_permission_to_role(self, role_id: str, permission_id: str, granted_by: str,
                                expires_at: Optional[datetime] = None, conditions: Dict[str, Any] = None) -> RolePermission:
        """Assign a permission to a role."""
        try:
            # Check if permission is already assigned
            existing_assignment = self.db.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                    RolePermission.is_active == True
                )
            ).first()
            
            if existing_assignment:
                logger.warning(f"Permission already assigned to role: {role_id}, permission: {permission_id}")
                return existing_assignment
            
            role_permission = RolePermission(
                id=uuid.uuid4(),
                role_id=role_id,
                permission_id=permission_id,
                granted_by=granted_by,
                granted_at=datetime.utcnow(),
                expires_at=expires_at,
                is_active=True,
                conditions=conditions or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(role_permission)
            self.db.commit()
            self.db.refresh(role_permission)
            
            logger.info(f"Assigned permission {permission_id} to role {role_id} by {granted_by}")
            return role_permission
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to assign permission to role: {e}")
            raise
    
    def remove_permission_from_role(self, role_id: str, permission_id: str, removed_by: str) -> bool:
        """Remove a permission from a role."""
        try:
            role_permission = self.db.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                    RolePermission.is_active == True
                )
            ).first()
            
            if not role_permission:
                logger.warning(f"Permission assignment not found: role {role_id}, permission {permission_id}")
                return False
            
            role_permission.is_active = False
            role_permission.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Removed permission {permission_id} from role {role_id} by {removed_by}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove permission from role: {e}")
            return False
    
    def get_role_permissions(self, role_id: str, include_inactive: bool = False) -> List[RolePermission]:
        """Get all permissions assigned to a role."""
        try:
            query = self.db.query(RolePermission).filter(RolePermission.role_id == role_id)
            if not include_inactive:
                query = query.filter(RolePermission.is_active == True)
            return query.all()
            
        except Exception as e:
            logger.error(f"Failed to get role permissions: {e}")
            return []
    
    def get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for a user through their roles."""
        try:
            # Get user's active roles
            user_roles = self.get_user_roles(user_id)
            
            permissions = []
            for user_role in user_roles:
                # Get permissions for this role
                role_permissions = self.get_role_permissions(user_role.role_id)
                
                for role_permission in role_permissions:
                    permission = self.get_permission_by_id(role_permission.permission_id)
                    if permission:
                        permissions.append({
                            'permission': permission,
                            'role': user_role.role,
                            'granted_at': role_permission.granted_at,
                            'expires_at': role_permission.expires_at,
                            'conditions': role_permission.conditions
                        })
            
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []
    
    def check_user_permission(self, user_id: str, resource_type: str, action: str, 
                            resource_id: Optional[str] = None) -> bool:
        """Check if a user has a specific permission."""
        try:
            user_permissions = self.get_user_permissions(user_id)
            
            for perm_data in user_permissions:
                permission = perm_data['permission']
                
                # Check if permission matches
                if (permission.resource_type == resource_type and 
                    permission.action == action):
                    
                    # Check if permission is expired
                    if perm_data['expires_at'] and perm_data['expires_at'] < datetime.utcnow():
                        continue
                    
                    # Check conditions if any
                    conditions = perm_data.get('conditions', {})
                    if conditions:
                        # Implement condition checking logic here
                        pass
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check user permission: {e}")
            return False
    
    def create_hipaa_compliant_role(self, role_name: str, data_access_level: str, created_by: str) -> Role:
        """Create a HIPAA-compliant role with appropriate permissions."""
        try:
            role_data = {
                'name': role_name,
                'description': f'HIPAA-compliant role for {data_access_level} data access',
                'is_system_role': False,
                'is_active': True,
                'hipaa_compliant': True,
                'data_access_level': data_access_level
            }
            
            role = self.create_role(role_data, created_by)
            
            # Add HIPAA-specific permissions based on access level
            hipaa_permissions = self._get_hipaa_permissions(data_access_level)
            for permission in hipaa_permissions:
                self.assign_permission_to_role(role.id, permission.id, created_by)
            
            logger.info(f"Created HIPAA-compliant role: {role_name}")
            return role
            
        except Exception as e:
            logger.error(f"Failed to create HIPAA-compliant role: {e}")
            raise
    
    def _get_hipaa_permissions(self, data_access_level: str) -> List[Permission]:
        """Get HIPAA permissions based on data access level."""
        try:
            permissions = []
            
            if data_access_level == 'basic':
                # Basic patient data access
                permissions.extend(self.get_permissions_by_resource('patient_basic'))
            elif data_access_level == 'clinical':
                # Clinical data access
                permissions.extend(self.get_permissions_by_resource('patient_clinical'))
                permissions.extend(self.get_permissions_by_resource('patient_basic'))
            elif data_access_level == 'administrative':
                # Administrative data access
                permissions.extend(self.get_permissions_by_resource('patient_administrative'))
                permissions.extend(self.get_permissions_by_resource('patient_basic'))
            elif data_access_level == 'full':
                # Full data access (with audit requirements)
                permissions.extend(self.get_permissions_by_resource('patient_full'))
                permissions.extend(self.get_permissions_by_resource('audit'))
            
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get HIPAA permissions: {e}")
            return []
    
    def audit_role_changes(self, user_id: str, action: str, role_id: str, 
                          details: Dict[str, Any]) -> None:
        """Audit role changes for compliance."""
        try:
            # This would typically log to an audit system
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'action': action,
                'role_id': role_id,
                'details': details,
                'ip_address': details.get('ip_address'),
                'user_agent': details.get('user_agent')
            }
            
            logger.info(f"Role audit: {audit_entry}")
            
        except Exception as e:
            logger.error(f"Failed to audit role changes: {e}")
    
    def get_role_statistics(self) -> Dict[str, Any]:
        """Get role statistics for reporting."""
        try:
            total_roles = self.db.query(Role).count()
            active_roles = self.db.query(Role).filter(Role.is_active == True).count()
            hipaa_roles = self.db.query(Role).filter(Role.hipaa_compliant == True).count()
            system_roles = self.db.query(Role).filter(Role.is_system_role == True).count()
            
            return {
                'total_roles': total_roles,
                'active_roles': active_roles,
                'hipaa_compliant_roles': hipaa_roles,
                'system_roles': system_roles,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get role statistics: {e}")
            return {}
    
    def cleanup_expired_assignments(self) -> Dict[str, int]:
        """Clean up expired role and permission assignments."""
        try:
            now = datetime.utcnow()
            
            # Clean up expired user roles
            expired_user_roles = self.db.query(UserRole).filter(
                and_(
                    UserRole.expires_at < now,
                    UserRole.is_active == True
                )
            ).all()
            
            for user_role in expired_user_roles:
                user_role.is_active = False
                user_role.updated_at = now
            
            # Clean up expired role permissions
            expired_role_permissions = self.db.query(RolePermission).filter(
                and_(
                    RolePermission.expires_at < now,
                    RolePermission.is_active == True
                )
            ).all()
            
            for role_permission in expired_role_permissions:
                role_permission.is_active = False
                role_permission.updated_at = now
            
            self.db.commit()
            
            logger.info(f"Cleaned up {len(expired_user_roles)} expired user roles and {len(expired_role_permissions)} expired role permissions")
            
            return {
                'expired_user_roles': len(expired_user_roles),
                'expired_role_permissions': len(expired_role_permissions)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup expired assignments: {e}")
            return {} 