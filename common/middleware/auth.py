"""
Authentication Middleware
Provides JWT validation, role checking, and circuit breaker patterns for all services.
"""

# pylint: disable=missing-class-docstring,too-few-public-methods,invalid-name,broad-except,too-many-locals,too-many-branches,too-many-statements,import-outside-toplevel,protected-access,raise-missing-from,line-too-long,unused-argument,unnecessary-pass

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
import warnings
from functools import wraps
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import settings
from ..database.connection import get_async_db
from ..utils.logging import get_logger
from ..utils.resilience import CircuitBreaker

logger = get_logger(__name__)

_DEFAULT_JWKS_CACHE_TTL_S = 600  # keep <= Supabase edge cache window
_JWKS_CACHE: Dict[str, Dict[str, Any]] = {}


def _certifi_ssl_context() -> ssl.SSLContext:
    """
    Create an SSL context using certifi CA bundle.

    This avoids local dev issues where the Python runtime can't locate system CAs
    (common on macOS python.org installs).
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


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
    expected_exception=Exception,
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
                            content={"detail": "Token has been revoked"},
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
                            "token_payload": payload,
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
                status_code=500, content={"detail": "Authentication middleware error"}
            )
            await response(scope, receive, send)

    def _init_redis(self):
        """Initialize Redis connection for token blacklisting. Skips connection when
        REDIS_URL is unset or points to localhost (e.g. on Render/Vercel without Redis)."""
        redis_url = (
            os.environ.get("REDIS_URL")
            or getattr(settings.external_services, "redis_url", None)
            or ""
        ).strip()
        if not redis_url or "localhost" in redis_url or "127.0.0.1" in redis_url:
            self.redis_client = None
            logger.info(
                "Redis not configured for auth (token blacklist disabled). "
                "Set REDIS_URL to a remote Redis (e.g. Render Redis or Upstash) to enable blacklisting."
            )
            return
        try:
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
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
            self.redis_client = None  # Disable so we don't retry every request
            return False

    def _decode_jwt_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        # Supabase can sign access tokens with:
        # - Legacy/shared secret: HS256 (verify with SUPABASE_JWT_SECRET)
        # - Signing keys: ES256/RS256 (verify via JWKS at `/auth/v1/.well-known/jwks.json`)
        #
        # We support both, to be compatible with projects in migration.
        candidate_secrets: List[str] = []

        # Primary (shared platform) secret from settings
        if getattr(settings, "auth", None) and getattr(
            settings.auth, "secret_key", None
        ):
            candidate_secrets.append(settings.auth.secret_key)

        # Legacy/alternate env var names used across services and deployments
        for env_name in (
            "JWT_SECRET_KEY",
            "JWT_SECRET",
            "SUPABASE_JWT_SECRET",
            "SUPABASE_JWT_SECRET_KEY",
        ):
            v = os.environ.get(env_name)
            if v:
                candidate_secrets.append(v)

        # If token is asymmetric (e.g. ES256/RS256), verify via JWKS.
        try:
            header = jwt.get_unverified_header(token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token header: {e}")

        alg = str(header.get("alg") or "")
        kid = str(header.get("kid") or "")
        if alg and alg.upper() != "HS256":
            # Prefer local JWKS verification, but fall back to Supabase Auth `/user`
            # endpoint if JWKS verification fails (keeps MVP reliable during key migrations).
            try:
                return self._decode_with_jwks(token=token, alg=alg, kid=kid)
            except HTTPException:
                return self._decode_with_supabase_auth_user(token=token)

        # Deduplicate while preserving order
        seen = set()
        secrets = []
        for s in candidate_secrets:
            if s not in seen:
                seen.add(s)
                secrets.append(s)

        last_error: Optional[Exception] = None
        for secret in secrets:
            try:
                payload = jwt.decode(
                    token,
                    secret,
                    algorithms=[settings.auth.algorithm],
                    options={"verify_aud": False},
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except JWTError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue

        # HS256 fallback: if we're missing the legacy shared secret (or keys were migrated),
        # validate against Supabase Auth server directly.
        try:
            return self._decode_with_supabase_auth_user(token=token)
        except HTTPException:
            pass

        detail = "Invalid token"
        if last_error:
            detail = f"Invalid token: {str(last_error)}"
        raise HTTPException(status_code=401, detail=detail)

    def _decode_with_supabase_auth_user(self, token: str) -> Dict[str, Any]:
        """
        Validate a Supabase access token by calling the Auth server.

        Supabase docs recommend this approach when not using asymmetric signing keys,
        but it also works as a robust fallback during signing key transitions.

        Requires:
        - `SUPABASE_URL` (or a valid `iss` claim in the JWT)
        - an API key for the `apikey` header (prefer `SUPABASE_PUBLISHABLE_KEY`)
        """
        unverified_claims = self._get_unverified_claims(token)
        iss = str(unverified_claims.get("iss") or "").rstrip("/")

        expected_issuer = os.environ.get("SUPABASE_ISSUER")
        if not expected_issuer:
            supabase_url = os.environ.get("SUPABASE_URL")
            if supabase_url:
                expected_issuer = supabase_url.rstrip("/") + "/auth/v1"

        if expected_issuer and iss and iss != expected_issuer.rstrip("/"):
            raise HTTPException(status_code=401, detail="Invalid token issuer")

        issuer_base = expected_issuer.rstrip("/") if expected_issuer else iss
        if not issuer_base:
            raise HTTPException(status_code=401, detail="Missing issuer (iss) claim")

        api_key = (
            os.environ.get("SUPABASE_PUBLISHABLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
        )
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Supabase API key missing for token validation",
            )

        url = issuer_base + "/user"
        req = urllib.request.Request(
            url,
            method="GET",
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(
                req, timeout=6, context=_certifi_ssl_context()
            ) as resp:
                body = resp.read().decode("utf-8")
                if resp.status != 200:
                    raise HTTPException(status_code=401, detail="Invalid token")
                user_obj = json.loads(body)
        except urllib.error.HTTPError as e:
            raise HTTPException(status_code=401, detail="Invalid token") from e
        except Exception as e:
            raise HTTPException(
                status_code=401, detail="Token validation failed"
            ) from e

        user_id = user_obj.get("id") or user_obj.get("sub")
        email = user_obj.get("email")
        user_metadata = user_obj.get("user_metadata") or {}

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Return a token-like payload to keep downstream code consistent.
        return {
            "sub": user_id,
            "email": email,
            "user_metadata": user_metadata,
            "iss": issuer_base,
        }

    def _decode_with_jwks(self, token: str, alg: str, kid: str) -> Dict[str, Any]:
        """
        Verify a Supabase JWT using JWKS (public key discovery).
        Uses SUPABASE_JWKS_URL if set, else derives from token `iss` claim.
        """
        unverified_claims = self._get_unverified_claims(token)
        iss = str(unverified_claims.get("iss") or "").rstrip("/")

        expected_issuer = os.environ.get("SUPABASE_ISSUER")
        if not expected_issuer:
            supabase_url = os.environ.get("SUPABASE_URL")
            if supabase_url:
                expected_issuer = supabase_url.rstrip("/") + "/auth/v1"

        if expected_issuer and iss != expected_issuer.rstrip("/"):
            raise HTTPException(status_code=401, detail="Invalid token issuer")

        jwks_url = os.environ.get("SUPABASE_JWKS_URL")
        if not jwks_url:
            if not iss:
                raise HTTPException(
                    status_code=401, detail="Missing issuer (iss) claim"
                )
            jwks_url = iss + "/.well-known/jwks.json"

        jwks = self._get_cached_jwks(jwks_url)
        keys = jwks.get("keys") or []
        if not isinstance(keys, list) or not keys:
            raise HTTPException(
                status_code=401,
                detail="JWKS has no keys (project may be using HS256 legacy secret)",
            )

        # Find matching kid; if none, use first key matching alg (or any key).
        key = None
        if kid:
            for k in keys:
                if isinstance(k, dict) and str(k.get("kid") or "") == kid:
                    key = k
                    break
        if key is None:
            for k in keys:
                if isinstance(k, dict) and (
                    not k.get("alg") or str(k.get("alg")).upper() == str(alg).upper()
                ):
                    key = k
                    break
        if key is None:
            raise HTTPException(
                status_code=401, detail="No matching JWKS key found for token"
            )

        try:
            # Convert JWK to PEM for python-jose verification
            from jose import jwk  # import here to avoid circular import issues

            constructed = jwk.construct(key, algorithm=alg)
            pem = constructed.to_pem()
            return jwt.decode(
                token,
                pem,
                algorithms=[alg],
                options={"verify_aud": False},
                issuer=expected_issuer.rstrip("/") if expected_issuer else None,
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    def _get_unverified_claims(self, token: str) -> Dict[str, Any]:
        """Read JWT payload without verifying signature (iss routing only)."""
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return {}
            payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            return json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return {}

    def _get_cached_jwks(self, jwks_url: str) -> Dict[str, Any]:
        ttl_s = float(
            os.environ.get("SUPABASE_JWKS_CACHE_TTL_S", str(_DEFAULT_JWKS_CACHE_TTL_S))
        )
        now = time.time()
        cached = _JWKS_CACHE.get(jwks_url)
        if (
            cached
            and float(cached.get("expires_at", 0)) > now
            and isinstance(cached.get("jwks"), dict)
        ):
            return cached["jwks"]

        req = urllib.request.Request(
            jwks_url, method="GET", headers={"Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(
                req, timeout=5, context=_certifi_ssl_context()
            ) as resp:
                jwks = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise HTTPException(status_code=401, detail=f"Failed to fetch JWKS: {e}")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Failed to fetch JWKS: {e}")

        # Do not cache longer than the default window.
        _JWKS_CACHE[jwks_url] = {
            "jwks": jwks,
            "expires_at": now + max(1.0, min(ttl_s, _DEFAULT_JWKS_CACHE_TTL_S)),
        }
        return jwks

    async def _get_user_from_db(
        self, user_id: str, db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
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
                    "roles": [role.name for role in user.user_roles]
                    if user.user_roles
                    else [],
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching user from database: {e}")
            return None

    @auth_circuit_breaker
    async def authenticate_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_async_db),
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
            "token_payload": payload,
        }

        # Try to get additional user data from database (optional)
        # Skip database lookup to avoid async context issues
        logger.debug(
            "Skipping database user lookup to avoid async context issues. Using JWT payload only."
        )

        return user_data

    def require_roles(self, required_roles: List[str]):
        """Decorator to require specific roles"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get user from request context
                request = kwargs.get("request") or args[0] if args else None
                if not request:
                    raise HTTPException(
                        status_code=500, detail="Request context not found"
                    )

                user = getattr(request.state, "user", None)
                if not user:
                    raise HTTPException(
                        status_code=401, detail="Authentication required"
                    )

                user_roles = user.get("roles", [])
                if not any(role in user_roles for role in required_roles):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Required roles: {required_roles}, User roles: {user_roles}",
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
                request = kwargs.get("request") or args[0] if args else None
                if not request:
                    raise HTTPException(
                        status_code=500, detail="Request context not found"
                    )

                user = getattr(request.state, "user", None)
                if not user:
                    raise HTTPException(
                        status_code=401, detail="Authentication required"
                    )

                # Get user permissions from roles
                user_permissions = []
                for role in user.get("roles", []):
                    # This would typically come from a role-permission mapping
                    # For now, we'll use a simple mapping
                    role_permissions = self._get_role_permissions(role)
                    user_permissions.extend(role_permissions)

                if not any(perm in user_permissions for perm in required_permissions):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Required permissions: {required_permissions}",
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
            "user": ["read_own", "write_own"],
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
                db: AsyncSession = Depends(get_async_db),
            ) -> Dict[str, Any]:
                return await self.auth_middleware.authenticate_user(credentials, db)

        return CurrentUserDependency(self)

    async def get_optional_user(
        self, request: Request, db: AsyncSession = Depends(get_async_db)
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
            logger.debug(
                "Skipping database user lookup in get_optional_user to avoid async context issues"
            )
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
        stacklevel=2,
    )
    auth_middleware = AuthMiddleware(None)
    return auth_middleware.get_current_user


def require_roles(roles: List[str]):
    """Dependency to require specific roles"""
    return AuthMiddleware(None).require_roles(roles)


def require_permissions(permissions: List[str]):
    """Dependency to require specific permissions"""
    return AuthMiddleware(None).require_permissions(permissions)


def get_optional_user():
    """Dependency to get optional user"""
    return AuthMiddleware(None).get_optional_user


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_async_db)
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
            "token_payload": payload,
        }

        # Skip database lookup to avoid async context issues
        logger.debug(
            "Skipping database user lookup in get_current_user to avoid async context issues"
        )

        return user_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


# Backward compatibility: handle both get_current_user and get_current_user()
# This allows services to use either pattern
def get_current_user_with_parentheses():
    """Backward compatibility wrapper for services using get_current_user()"""
    return get_current_user
