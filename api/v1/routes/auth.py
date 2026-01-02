from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.auth import verify_password, get_password_hash, create_access_token
from ..core.tracing import trace_function
from ..core.metrics import metrics
from ..models.user import User
from ..schemas.auth import UserCreate, UserLogin, UserResponse
from ..schemas.response import (
    success_response,
    user_exists_error,
    invalid_credentials_error,
    user_inactive_error,
)

router = APIRouter()
security = HTTPBearer()


@router.post("/register", status_code=status.HTTP_201_CREATED)
@trace_function("user_registration")
async def register(
    user_data: UserCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    request_id = getattr(request.state, "request_id", None)

    # Check if user already exists
    metrics.record_database_query("select", "users")
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=user_exists_error(request_id),
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(email=user_data.email, hashed_password=hashed_password)

    db.add(db_user)
    metrics.record_database_query("insert", "users")
    await db.commit()
    await db.refresh(db_user)

    # Record metrics
    metrics.record_user_registration()

    # Convert to response model
    user_response = UserResponse(
        id=str(db_user.id),
        email=db_user.email,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
    )

    return success_response(
        data=user_response.model_dump(),
        message="User registered successfully",
        request_id=request_id,
    )


@router.post("/login")
@trace_function("user_login")
async def login(
    user_data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token."""
    request_id = getattr(request.state, "request_id", None)

    # Find user by email
    metrics.record_database_query("select", "users")
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.hashed_password):
        metrics.record_auth_attempt("invalid_credentials")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=invalid_credentials_error(request_id),
        )

    if not user.is_active:
        metrics.record_auth_attempt("user_inactive")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=user_inactive_error(request_id),
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    metrics.record_auth_attempt("success")

    token_data = {"access_token": access_token, "token_type": "bearer"}

    return success_response(
        data=token_data, message="Login successful", request_id=request_id
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(security)
):
    """Get current user information."""
    # This endpoint requires authentication via middleware
    # The user_id will be available in request.state.user_id
    # For now, we'll implement a simple version

    # This is a placeholder - in real implementation, we'd get user_id from request.state
    # after the auth middleware processes the token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not fully implemented yet",
    )
