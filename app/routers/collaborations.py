"""Collaboration / contact requests.

Public, unauthenticated endpoint: anyone can submit a request to collaborate
(name, email, optional speciality, message). Each request is stored for admin
follow-up and, when SMTP is configured, emailed to the admins.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import email
from app.database import get_db
from app.models import Collaboration
from app.schemas import CollaborationCreate, CollaborationOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collaborations", tags=["collaborations"])


@router.post(
    "",
    response_model=CollaborationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a collaboration request",
    description="Public endpoint. Stores a collaboration/contact request "
    "(`name`, `email`, optional `speciality`, `message`) and notifies the "
    "admins by email when SMTP is configured. Returns the stored request.",
)
def create_collaboration(
    payload: CollaborationCreate,
    db: Session = Depends(get_db),
) -> CollaborationOut:
    row = Collaboration(
        name=payload.name,
        email=str(payload.email),
        speciality=payload.speciality,
        message=payload.message,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # Best-effort notification — a mail failure must not fail the submission.
    try:
        email.send_collaboration_request(
            payload.name, str(payload.email), payload.speciality, payload.message
        )
    except Exception:  # noqa: BLE001
        logger.exception("collaboration email notification failed (request still saved)")

    return row
