"""Request dependencies: resolve the current user from a Bearer access token."""

import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import PUSH_ADMIN_KEY
from app.database import get_db
from app.models import User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=True)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _UNAUTHORIZED

    try:
        pk = uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise _UNAUTHORIZED

    user = db.get(User, pk)
    if user is None:
        raise _UNAUTHORIZED
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )
    return user


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """Gate server-to-server / admin endpoints on the shared PUSH_ADMIN_KEY.

    Fails closed: if no key is configured, the endpoint is unusable rather than open.
    """
    if not PUSH_ADMIN_KEY or x_admin_key != PUSH_ADMIN_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin key")
