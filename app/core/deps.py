"""FastAPI dependencies: DB session, current user, role guards."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_access_token
from app.db.base import get_db
from app.models.models import User, UserRole

from typing import Annotated
from fastapi import Depends

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DBDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBDep,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """Factory: returns a dependency that enforces role membership."""
    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return Depends(_check)


# Pre-built role dependencies
AdminRequired = require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)
ManagerRequired = require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)

from fastapi import HTTPException

async def require_editor(current_user: CurrentUser):
    """Bloquea acceso a viewers — solo lectura"""
    if current_user.role in ["viewer", "VIEWER"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para realizar esta acción"
        )
    return current_user

# Type alias
EditorUser = Annotated[User, Depends(require_editor)]