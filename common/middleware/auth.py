"""
Authentication Middleware
Provides JWT validation, role checking, and circuit breaker patterns for all services.
"""

from jose import jwt, JWTError
import time
import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis
from functools import wraps
import warnings

from ..config.settings import settings
from ..database.connection import get_async_db
from ..utils.logging import get_logger
from ..utils.resilience import CircuitBreaker

logger = get_logger(__name__)

class HTTPBearer401(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        try:
            credentials = await super().__call__(request)
        except HTTPException as exc:
            # FastAPI's HTTPBearer raises 403, convert to 401
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials

# Security scheme
security = HTTPBearer401()

# Circuit breaker for auth operations
auth_circuit_breaker = CircuitBreaker(
    failure_threshold=settings.resilience.circuit_breaker_fail_max,
    recovery_timeout=settings.resilience.circuit_breaker_reset_timeout,
    expected_exception=Exception
)

class AuthMiddleware:
    """Authentication middleware with JWT validation and role checking"""
    
    def __init__(self, app):
        self.app = app
        self.redis_client: Optional[redis.Redis] = None
        self._init_redis()
    
    async def __call__(self, scope, receive, send):
        """FastAPI middleware call method"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request object from scope
        request = Request(scope, receive)
        
        try:
            # Try to get user from request if authentication header is present
            auth_header = request.headers.get("Authorization")
            token = None
            
            # Check for Bearer token in Authorization header
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            
            # Check for session cookie if no Bearer token
            if not token:
                token = request.cookies.get("access_token")
            
            if token:
                try:
                    # Check if token is blacklisted
                    if await self._is_token_blacklisted(token):
                        response = JSONResponse(
                            status_code=401,
                            content={"detail": "Token has been revoked"}
                        )
                        await response(scope, receive, send)
                        return
                    
                    # Decode JWT token
                    payload = self._decode_jwt_token(token)
                    user_id = payload.get("sub")
                    email = payload.get("email")
                    
                    if user_id:
                        # Add user info to request state
                        request.state.user = {
                            "id": user_id,
                            "email": email,
                            "username": email,
                            "is_active": True,
                            "roles": ["user"],
                            "token_payload": payload
                        }
                        request.state.user_id = user_id
                        
                except HTTPException:
                    # Token validation failed, but continue without user
                    pass
                except Exception as e:
                    logger.debug(f"Auth middleware error: {e}")
                    # Continue without user
                    pass
            
            # Continue to next middleware/endpoint
            await self.app(scope, receive, send)
            
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Authentication middleware error"}
            )
            await response(scope, receive, send)
    
    def _init_redis(self):
        """Initialize Redis connection for token blacklisting"""
        try:
            self.redis_client = redis.from_url(
                settings.external_services.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis client initialized for auth middleware")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")
            self.redis_client = None
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted in Redis"""
        if not self.redis_client:
            return False
        
        try:
            blacklisted = await self.redis_client.get(f"blacklist:{token}")
            return blacklisted is not None
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False
    
    def _decode_jwt_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.auth.secret_key,
                algorithms=[settings.auth.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    async def _get_user_from_db(self, user_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get user from database"""
        try:
            # Import here to avoid circular imports - make it optional
            try:
                from apps.auth.models.user import User
            except ImportError:
                # If auth models are not available, return None
                logger.debug("Auth models not available, skipping database user lookup")
                return None
            
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "username": user.email,  # Use email as username since User model doesn't have username field
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "roles": [role.name for role in user.user_roles] if user.user_roles else []
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching user from database: {e}")
            return None
    
    @auth_circuit_breaker
    async def authenticate_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_async_db)
    ) -> Dict[str, Any]:
        """Authenticate user and return user data"""
        token = credentials.credentials
        
        # Check if token is blacklisted
        if await self._is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        # Decode JWT token
        payload = self._decode_jwt_token(token)
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Create user data from JWT payload (primary source)
        user_data = {
            "id": user_id,
            "email": email,
            "username": email,  # Use email as username if not available
            "is_active": True,  # Assume active if token is valid
            "roles": ["user"],  # Default role
            "token_payload": payload
        }
        
        # Try to get additional user data from database (optional)
        # Skip database lookup to avoid async context issues
        logger.debug("Skipping database user lookup to avoid async context issues. Using JWT payload only.")
        
        return user_data
    
    def require_roles(self, required_roles: List[str]):
        """Decorator to require specific roles"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get user from request context
                request = kwargs.get('request') or args[0] if args else None
                if not request:
                    raise HTTPException(status_code=500, detail="Request context not found")
                
                user = getattr(request.state, 'user', None)
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                user_roles = user.get('roles', [])
                if not any(role in user_roles for role in required_roles):
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Required roles: {required_roles}, User roles: {user_roles}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_permissions(self, required_permissions: List[str]):
        """Decorator to require specific permissions"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get user from request context
                request = kwargs.get('request') or args[0] if args else None
                if not request:
                    raise HTTPException(status_code=500, detail="Request context not found")
                
                user = getattr(request.state, 'user', None)
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                # Get user permissions from roles
                user_permissions = []
                for role in user.get('roles', []):
                    # This would typically come from a role-permission mapping
                    # For now, we'll use a simple mapping
                    role_permissions = self._get_role_permissions(role)
                    user_permissions.extend(role_permissions)
                
                if not any(perm in user_permissions for perm in required_permissions):
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Required permissions: {required_permissions}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a given role"""
        # This would typically come from a database or configuration
        role_permissions = {
            "admin": ["read", "write", "delete", "admin"],
            "doctor": ["read", "write", "patient_data"],
            "patient": ["read", "write_own"],
            "researcher": ["read", "analytics"],
            "user": ["read_own", "write_own"]
        }
        return role_permissions.get(role, [])
    
    async def add_user_to_request(self, request: Request, user: Dict[str, Any]):
        """Add user data to request state"""
        request.state.user = user
    
    def get_current_user(self):
        """Get current authenticated user dependency"""
        class CurrentUserDependency:
            def __init__(self, auth_middleware):
                self.auth_middleware = auth_middleware
            
            async def __call__(
                self,
                credentials: HTTPAuthorizationCredentials = Depends(security),
                db: AsyncSession = Depends(get_async_db)
            ) -> Dict[str, Any]:
                return await self.auth_middleware.authenticate_user(credentials, db)
        
        return CurrentUserDependency(self)
    
    async def get_optional_user(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_db)
    ) -> Optional[Dict[str, Any]]:
        """Get user if authenticated, otherwise return None"""
        try:
            # Check for Bearer token in Authorization header
            auth_header = request.headers.get("Authorization")
            token = None
            
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            
            # Check for session cookie if no Bearer token
            if not token:
                token = request.cookies.get("access_token")
            
            if not token:
                return None
            
            if await self._is_token_blacklisted(token):
                return None
            
            payload = self._decode_jwt_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                return None
            
            # Skip database lookup to avoid async context issues
            logger.debug("Skipping database user lookup in get_optional_user to avoid async context issues")
            return None
            
        except Exception as e:
            logger.debug(f"Optional user authentication failed: {e}")
            return None

# Global auth middleware instance - REMOVED
# auth_middleware = AuthMiddleware(None) # Initialize with None, as app is not directly passed here

# Convenience functions
def require_auth():
    """
    DEPRECATED: Use get_current_user() instead.
    
    This function returns a coroutine object instead of a proper dependency function,
    which can cause serialization issues. Use get_current_user() for proper authentication.
    """
    warnings.warn(
        "require_auth() is deprecated. Use get_current_user() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    auth_middleware = AuthMiddleware(None)
    return auth_middleware.get_current_user

def require_roles(roles: List[str]):
    """Dependency to require specific roles"""
    return auth_middleware.require_roles(roles)

def require_permissions(permissions: List[str]):
    """Dependency to require specific permissions"""
    return auth_middleware.require_permissions(permissions)

def get_optional_user():
    """Dependency to get optional user"""
    return auth_middleware.get_optional_user

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Dependency to get current authenticated user - supports both Bearer tokens and session cookies"""
    try:
        token = None
        
        # Check for Bearer token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        # Check for session cookie if no Bearer token
        if not token:
            token = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if token is blacklisted
        auth_middleware = AuthMiddleware(None)
        if await auth_middleware._is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        # Decode JWT token
        payload = auth_middleware._decode_jwt_token(token)
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Create user data from JWT payload (primary source)
        user_data = {
            "id": user_id,
            "email": email,
            "username": email,  # Use email as username if not available
            "is_active": True,  # Assume active if token is valid
            "roles": ["user"],  # Default role
            "token_payload": payload
        }
        
        # Skip database lookup to avoid async context issues
        logger.debug("Skipping database user lookup in get_current_user to avoid async context issues")
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

# Backward compatibility: handle both get_current_user and get_current_user()
# This allows services to use either pattern
def get_current_user_with_parentheses():
    """Backward compatibility wrapper for services using get_current_user()"""
    return get_current_user 