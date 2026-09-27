"""
Authentication routes - Login, logout, user profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from database import get_db
from services.auth import auth_service
from schemas import LoginRequest, LoginResponse, UserResponse
from models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user

    Validates JWT token and returns user object
    """
    token = credentials.credentials
    user_id = auth_service.verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with Windows AD credentials

    Returns JWT access token if credentials are valid
    """
    logger.info(f"Login attempt for user: {credentials.username}")

    # Validate AD credentials
    ad_user_info = auth_service.validate_ad_credentials(
        credentials.username,
        credentials.password
    )

    if not ad_user_info:
        logger.warning(f"Failed login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Get or create user in database
    user = auth_service.get_or_create_user(db, ad_user_info)

    # Create JWT token
    access_token = auth_service.create_access_token(user.id)

    logger.info(f"User {user.email} logged in successfully")

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/user", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile

    Requires valid JWT token in Authorization header
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout - invalidate session

    Note: JWT tokens are stateless, this endpoint is mainly for logging
    """
    logger.info(f"User {current_user.email} logged out")

    return {
        "message": "Logged out successfully",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if current token is still valid

    Returns user info if token is valid
    """
    return {
        "valid": True,
        "user": UserResponse.model_validate(current_user),
        "timestamp": datetime.utcnow().isoformat()
    }
