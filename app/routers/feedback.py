"""User feedback.

Public endpoint: anyone can submit feedback (category, subject, message). Each
submission is stored for admin review.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback",
    description="Public endpoint. Stores user feedback (`category`, `subject`, "
    "`message`) and returns the stored record.",
)
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackOut:
    row = Feedback(
        category=payload.category,
        subject=payload.subject,
        message=payload.message,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
