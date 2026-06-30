"""Feedback on clinical recommendations — table ``feedback``.

Users rate a recommendation (👍 useful / 👎 not useful / ⚠️ potential issue) and
whether it matched their clinical judgment. A "potential issue" requires a
description of the concern and is stored ``flagged=True`` so it surfaces in a
separate review queue (with the submitting user + timestamp).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin_key
from app.models import Feedback, User
from app.schemas import FeedbackCreate, FeedbackOut, FlaggedFeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Feedback:
    """Submit feedback. A "potential_issue" is auto-flagged for review."""
    row = Feedback(
        user_id=user.id,
        usefulness=payload.usefulness,
        clinical_judgment=payload.clinical_judgment,
        comments=payload.comments,
        concern=payload.concern,
        flagged=payload.usefulness == "potential_issue",
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[FeedbackOut])
def list_my_feedback(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Feedback]:
    """The caller's own feedback, newest first."""
    return list(
        db.scalars(
            select(Feedback)
            .where(Feedback.user_id == user.id)
            .order_by(Feedback.created_at.desc())
        )
    )


@router.get(
    "/flagged",
    response_model=list[FlaggedFeedbackOut],
    dependencies=[Depends(require_admin_key)],
    summary="Review flagged potential-issue reports (admin)",
)
def list_flagged(db: Session = Depends(get_db)) -> list[FlaggedFeedbackOut]:
    """All flagged potential-issue reports, newest first, with user + time.

    Admin endpoint, gated by the ``X-Admin-Key`` header (PUSH_ADMIN_KEY).
    """
    rows = db.execute(
        select(Feedback, User.email)
        .join(User, User.id == Feedback.user_id)
        .where(Feedback.flagged.is_(True))
        .order_by(Feedback.created_at.desc())
    ).all()
    return [
        FlaggedFeedbackOut(
            id=fb.id,
            user_id=fb.user_id,
            user_email=email,
            usefulness=fb.usefulness,
            clinical_judgment=fb.clinical_judgment,
            comments=fb.comments,
            concern=fb.concern,
            subject_type=fb.subject_type,
            subject_id=fb.subject_id,
            created_at=fb.created_at,
        )
        for fb, email in rows
    ]
