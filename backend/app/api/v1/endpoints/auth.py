from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.core.deps import CurrentUser, DBDep
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.models import User
from app.schemas.schemas import LoginRequest, RefreshRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DBDep):
    result = await db.execute(
        select(User).where(User.email == payload.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    user.last_login = datetime.now(timezone.utc)
    access_token = create_access_token(user.id, {"role": user.role, "name": user.full_name})
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: DBDep):
    from jose import JWTError
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id: str = data["sub"]
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token = create_access_token(user.id, {"role": user.role, "name": user.full_name})
    new_refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user