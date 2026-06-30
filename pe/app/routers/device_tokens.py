"""Device-token endpoints — table ``device_tokens`` (mobile push)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import DeviceToken, User
from app.schemas import DeviceTokenCreate

router = APIRouter(prefix="/device-tokens", tags=["device-tokens"])


@router.post("", status_code=status.HTTP_200_OK)
def upsert_device_token(
    payload: DeviceTokenCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Upsert on conflict of (user_id, token)."""
    existing = db.scalar(
        select(DeviceToken).where(
            DeviceToken.user_id == user.id, DeviceToken.token == payload.token
        )
    )
    if existing is not None:
        existing.platform = payload.platform
        existing.updated_at = datetime.now(timezone.utc)
    else:
        db.add(DeviceToken(user_id=user.id, token=payload.token, platform=payload.platform))
    db.commit()
    return {"status": "ok"}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_tokens(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    """Delete all of the current user's tokens (used on sign-out)."""
    db.execute(delete(DeviceToken).where(DeviceToken.user_id == user.id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
