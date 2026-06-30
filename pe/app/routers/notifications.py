"""Push-notification sender — replaces the ``send-push-notification`` edge fn.

This is a server-to-server / admin endpoint: it is NOT scoped to the caller's
own user. It is gated by the ``X-Admin-Key`` header (compared to PUSH_ADMIN_KEY)
rather than a user JWT.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import push
from app.config import PUSH_ADMIN_KEY
from app.database import get_db
from app.models import DeviceToken
from app.schemas import NotificationResult, NotificationSend

router = APIRouter(prefix="/notifications", tags=["notifications"])


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    # Fail closed: if no key is configured, the endpoint is unusable rather than open.
    if not PUSH_ADMIN_KEY or x_admin_key != PUSH_ADMIN_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin key")


@router.post("/send", response_model=NotificationResult, dependencies=[Depends(require_admin_key)])
def send_notification(
    payload: NotificationSend, db: Session = Depends(get_db)
) -> NotificationResult:
    tokens = list(
        db.scalars(select(DeviceToken.token).where(DeviceToken.user_id == payload.user_id))
    )
    sent = push.send_to_tokens(tokens, payload.title, payload.body, payload.data)
    return NotificationResult(success=True, sent=sent)
