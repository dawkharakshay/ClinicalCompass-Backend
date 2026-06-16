"""Appeal-letter ratings.

Public endpoint: a user rates a generated appeal letter (letter quality and
effectiveness, both 1-5) with an optional appeal outcome and free-text comments.
Each rating is stored for admin review.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AppealLetterRating
from app.schemas import AppealLetterRatingCreate, AppealLetterRatingOut

router = APIRouter(prefix="/appeal-letter-ratings", tags=["appeal-letter-ratings"])


@router.post(
    "",
    response_model=AppealLetterRatingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Rate an appeal letter",
    description="Public endpoint. Stores a rating for a generated appeal letter: "
    "`letter_quality` and `effectiveness` (1-5), with optional `appeal_outcome` "
    "and `comments`. Returns the stored rating.",
)
def create_rating(
    payload: AppealLetterRatingCreate,
    db: Session = Depends(get_db),
) -> AppealLetterRatingOut:
    row = AppealLetterRating(
        letter_quality=payload.letter_quality,
        effectiveness=payload.effectiveness,
        appeal_outcome=payload.appeal_outcome,
        comments=payload.comments,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
