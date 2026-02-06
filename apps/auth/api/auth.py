"""
Main authentication API endpoints for the Personal Health Assistant.

This module provides comprehensive authentication endpoints including:
- Local authentication (email/password)
- Supabase authentication
- Auth0 OAuth authentication
- Session management
- Security features
"""

from datetime import timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from common.database.connection import get_async_db
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger

from ..models.user import User, UserCreate, UserResponse, UserStatus, MFAStatus, PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest, EmailVerificationConfirm
from ..models.session import SessionResponse
from ..models.mfa import MFAVerificationRequest, MFASetupRequest, MFASetupResponse
from ..services.auth_service import AuthService, get_auth_service

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()
basic_auth = HTTPBasic()

# Local dependency to get the current authenticated user as a User ORM object
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    try:
        logger.warning(f"[DEBUG] get_current_user: credentials={credentials}")
        token = credentials.credentials
        logger.warning(f"[DEBUG] get_current_user: token={token[:12]}...")
        payload = auth_service.verify_token(token)
        logger.warning(f"[DEBUG] get_current_user: payload={payload}")
        if not payload:
            logger.error("[DEBUG] get_current_user: Invalid token (no payload)")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = payload.get("sub")
        if not user_id:
            logger.error("[DEBUG] get_current_user: Invalid token payload (no sub)")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user = await auth_service._get_user_by_id(UUID(user_id))
        if not user:
            logger.error("[DEBUG] get_current_user: User not found")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not user.is_active:
            logger.error("[DEBUG] get_current_user: User inactive")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] get_current_user: Exception: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")


@router.post("/login", response_model=dict)
@rate_limit(requests_per_minute=5)  # 5 attempts per minute
@security_headers
async def login(
    request: Request,
    response: Response,
    credentials: HTTPBasicCredentials = Depends(basic_auth),
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user with email and password.
    
    This endpoint supports both local authentication and OAuth providers.
    """
    try:
        email = credentials.username
        password = credentials.password
        
        logger.info(f"Login attempt for email: {email}")
        
        # Get client information
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        # Authenticate user
        user = await auth_service.authenticate_user(email, password, ip_address, user_agent)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        # Check if MFA is required
        if user.mfa_status != "disabled":
            return {
                "message": "MFA verification required",
                "mfa_required": True,
                "user_id": str(user.id),
                "mfa_status": user.mfa_status
            }
        
        # Create session
        session = await auth_service.create_session(user, ip_address, user_agent)
        
        # Set secure cookies - use secure=False for local development
        response.set_cookie(
            key="access_token",
            value=session.session_token,
            httponly=True,
            secure=False,  # Set to False for local development over HTTP
            samesite="strict",
            max_age=900
        )
        response.set_cookie(
            key="refresh_token",
            value=session.refresh_token,
            httponly=True,
            secure=False,  # Set to False for local development over HTTP
            samesite="strict",
            max_age=604800
        )
        
        return {
            "message": "Login successful",
            "user": UserResponse.from_orm(user),
            "session": SessionResponse.from_orm(session),
            "mfa_required": False
        }
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/login/supabase", response_model=dict)
@rate_limit(requests_per_minute=10)
@security_headers
async def login_with_supabase(
    request: Request,
    response: Response,
    supabase_token: str,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user with Supabase token.
    """
    try:
        logger.info("Supabase login attempt")
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        user = await auth_service.authenticate_with_supabase(supabase_token, ip_address, user_agent)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token"
            )
        
        # Create session
        session = await auth_service.create_session(user, ip_address, user_agent)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=session.session_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=900
        )
        response.set_cookie(
            key="refresh_token",
            value=session.refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=604800
        )
        
        return {
            "message": "Supabase login successful",
            "user": UserResponse.from_orm(user),
            "session": SessionResponse.from_orm(session)
        }
        
    except Exception as e:
        logger.error(f"Supabase login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase authentication failed"
        )


@router.post("/login/auth0", response_model=dict)
@rate_limit(requests_per_minute=10)
@security_headers
async def login_with_auth0(
    request: Request,
    response: Response,
    auth0_token: str,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user with Auth0 token.
    """
    try:
        logger.info("Auth0 login attempt")
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        user = await auth_service.authenticate_with_auth0(auth0_token, ip_address, user_agent)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Auth0 token"
            )
        
        # Create session
        session = await auth_service.create_session(user, ip_address, user_agent)
        
        # Set secure cookies - use secure=False for local development
        response.set_cookie(
            key="access_token",
            value=session.session_token,
            httponly=True,
            secure=False,  # Set to False for local development over HTTP
            samesite="strict",
            max_age=900
        )
        response.set_cookie(
            key="refresh_token",
            value=session.refresh_token,
            httponly=True,
            secure=False,  # Set to False for local development over HTTP
            samesite="strict",
            max_age=604800
        )
        
        return {
            "message": "Auth0 login successful",
            "user": UserResponse.from_orm(user),
            "session": SessionResponse.from_orm(session)
        }
        
    except Exception as e:
        logger.error(f"Auth0 login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth0 authentication failed"
        )


@router.post("/register", response_model=dict)
@rate_limit(requests_per_hour=3)  # 3 registrations per hour
@security_headers
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    """
    logger.info(f"Registration endpoint called with email: {user_data.email}")
    try:
        # Check if user already exists
        from sqlalchemy import select
        from ..models.user import User
        
        query = select(User).where(User.email == user_data.email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Create new user
        import uuid
        from ..models.user import UserStatus, MFAStatus
        
        user = User(
            supabase_user_id=str(uuid.uuid4()),  # Generate a unique supabase_user_id
            email=user_data.email,
            password_hash=auth_service.get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            user_type=user_data.user_type,
            phone=user_data.phone,
            date_of_birth=user_data.date_of_birth,
            gender=user_data.gender,
            status=UserStatus.ACTIVE,
            email_verified=False,
            phone_verified=False,
            mfa_status=MFAStatus.DISABLED,
            hipaa_consent_given=False
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create user profile in user profile service
        # try:
        #     from ..services.user_profile_integration import get_user_profile_integration_service
        #     profile_service = get_user_profile_integration_service()
        #     
        #     profile_result = await profile_service.create_user_profile(
        #         user_id=str(user.id),
        #         email=user.email,
        #         first_name=user.first_name,
        #         last_name=user.last_name,
        #         user_type=user.user_type,
        #         phone=user.phone,
        #         date_of_birth=user.date_of_birth,
        #         gender=user.gender
        #     )
        #     
        #     if "error" in profile_result:
        #         logger.warning(f"User profile creation failed for user {user.id}: {profile_result['error']}")
        #     else:
        #         logger.info(f"User profile created successfully for user {user.id}")
        #         
        # except Exception as profile_error:
        #     logger.error(f"Failed to create user profile for user {user.id}: {profile_error}")
        #     # Don't fail the registration if profile creation fails
        #     # The user can create their profile later
        
        # Log user creation
        # await auth_service.audit_service.log_event(
        #     user_id=user.id,
        #     event_type="user_created",
        #     description=f"User registered: {user.email}",
        #     ip_address=request.client.host,
        #     user_agent=request.headers.get("user-agent")
        # )
        
        return {
            "message": "User registration successful",
            "user_id": str(user.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/logout")
@security_headers
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user and revoke session.
    """
    try:
        logger.info(f"Logout attempt for user: {current_user.email}")
        # Get session from cookies
        session_token = request.cookies.get("access_token")
        if session_token:
            # Revoke session
            # TODO: Implement session revocation logic
            pass
        
        # Clear cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=dict)
@rate_limit(requests_per_minute=10)
@security_headers
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    """
    try:
        logger.info("Token refresh attempt")
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        session = await auth_service.refresh_session(refresh_token, ip_address, user_agent)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Update cookies
        response.set_cookie(
            key="access_token",
            value=session.session_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=900
        )
        response.set_cookie(
            key="refresh_token",
            value=session.refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=604800
        )
        
        return {
            "message": "Token refreshed successfully",
            "session": SessionResponse.from_orm(session)
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/mfa/verify", response_model=dict)
@rate_limit(requests_per_minute=5)
@security_headers
async def verify_mfa(
    request: Request,
    response: Response,
    mfa_request: MFAVerificationRequest,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify MFA code for user authentication.
    """
    try:
        logger.info(f"MFA verification attempt for user_id: {mfa_request.user_id}")
        # Get user from session or request
        user_id = mfa_request.user_id  # This should come from session in real implementation
        user = await auth_service._get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify MFA code
        is_valid = await auth_service.verify_mfa(user, mfa_request.code, mfa_request.device_id)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
        
        # Create session if MFA verification successful
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        session = await auth_service.create_session(user, ip_address, user_agent)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=session.session_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=900
        )
        response.set_cookie(
            key="refresh_token",
            value=session.refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=604800
        )
        
        return {
            "message": "MFA verification successful",
            "user": UserResponse.from_orm(user),
            "session": SessionResponse.from_orm(session)
        }
        
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )


@router.post("/mfa/setup", response_model=MFASetupResponse)
@security_headers
async def setup_mfa(
    mfa_request: MFASetupRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Setup MFA for user account.
    """
    try:
        logger.info(f"MFA setup attempt for user: {current_user.email}")
        result = await auth_service.setup_mfa(current_user, mfa_request.device_name)
        return MFASetupResponse(**result)
        
    except Exception as e:
        logger.error(f"MFA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA setup failed"
        )


@router.get("/me", response_model=UserResponse)
@security_headers
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    authorization: str = Header(None)
):
    logger.warning(f"[DEBUG] /me endpoint: Authorization header: {authorization}")
    return UserResponse.from_orm(current_user)


@router.get("/validate")
async def validate_token(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Forward authentication endpoint for Traefik.
    Validates JWT tokens and returns user information for Traefik forward auth.
    """
    try:
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                headers={
                    "X-User-Id": "",
                    "X-User-Roles": "",
                    "X-User-Email": "",
                    "X-Auth-Status": "unauthenticated"
                }
            )
        
        token = auth_header.split(" ")[1]
        
        # Validate token
        try:
            user = await auth_service.validate_token(token, db)
            
            # Return success with user headers for Traefik
            return JSONResponse(
                status_code=200,
                content={"status": "authenticated", "user_id": user.id},
                headers={
                    "X-User-Id": str(user.id),
                    "X-User-Roles": ",".join(user.roles) if user.roles else "user",
                    "X-User-Email": user.email,
                    "X-Auth-Status": "authenticated"
                }
            )
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"status": "invalid_token", "detail": e.detail},
                headers={
                    "X-User-Id": "",
                    "X-User-Roles": "",
                    "X-User-Email": "",
                    "X-Auth-Status": "invalid_token"
                }
            )
            
    except Exception as e:
        logger.error(f"Forward auth validation error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": "Internal server error"},
            headers={
                "X-User-Id": "",
                "X-User-Roles": "",
                "X-User-Email": "",
                "X-Auth-Status": "error"
            }
        )


@router.post("/reset-password/request")
@rate_limit(requests_per_hour=3)  # 3 requests per hour
@security_headers
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request a password reset for the specified email.
    
    This endpoint sends a password reset email with a secure token.
    """
    try:
        logger.info(f"Password reset request for email: {reset_request.email}")
        
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        # Request password reset
        success = await auth_service.request_password_reset(
            reset_request.email, 
            ip_address, 
            user_agent
        )
        
        if success:
            return {
                "message": "Password reset email sent successfully",
                "email": reset_request.email
            }
        else:
            # Don't reveal if email exists or not for security
            return {
                "message": "If the email exists, a password reset link has been sent",
                "email": reset_request.email
            }
            
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/reset-password/confirm")
@rate_limit(requests_per_minute=5)  # 5 attempts per minute
@security_headers
async def confirm_password_reset(
    request: Request,
    reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm password reset with token and set new password.
    """
    try:
        logger.info(f"Password reset confirmation for email: {reset_confirm.email}")
        
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        # Confirm password reset
        success = await auth_service.confirm_password_reset(
            reset_confirm.email,
            reset_confirm.token,
            reset_confirm.new_password,
            ip_address,
            user_agent
        )
        
        if success:
            return {
                "message": "Password reset successfully",
                "email": reset_confirm.email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/verify-email/request")
@rate_limit(requests_per_hour=5)  # 5 requests per hour
@security_headers
async def request_email_verification(
    request: Request,
    verification_request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request email verification for the specified email.
    
    This endpoint sends a verification email with a secure token.
    """
    try:
        logger.info(f"Email verification request for email: {verification_request.email}")
        
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        # Request email verification
        success = await auth_service.request_email_verification(
            verification_request.email,
            ip_address,
            user_agent
        )
        
        if success:
            return {
                "message": "Email verification link sent successfully",
                "email": verification_request.email
            }
        else:
            # Don't reveal if email exists or not for security
            return {
                "message": "If the email exists, a verification link has been sent",
                "email": verification_request.email
            }
            
    except Exception as e:
        logger.error(f"Email verification request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process email verification request"
        )


@router.post("/verify-email/confirm")
@rate_limit(requests_per_minute=5)  # 5 attempts per minute
@security_headers
async def confirm_email_verification(
    request: Request,
    verification_confirm: EmailVerificationConfirm,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm email verification with token.
    """
    try:
        logger.info(f"Email verification confirmation for email: {verification_confirm.email}")
        
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        
        # Confirm email verification
        success = await auth_service.confirm_email_verification(
            verification_confirm.email,
            verification_confirm.token,
            ip_address,
            user_agent
        )
        
        if success:
            return {
                "message": "Email verified successfully",
                "email": verification_confirm.email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the authentication service.
    """
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for the authentication service.
    """
    return {
        "status": "ready",
        "service": "auth-service",
        "timestamp": "2024-01-01T00:00:00Z"
    } 