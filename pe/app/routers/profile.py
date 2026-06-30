"""Profile endpoints — table ``profiles`` (row created at signup)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Profile, User
from app.schemas import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profiles"])


def _get_or_create(db: Session, user: User) -> Profile:
    if user.profile is None:
        user.profile = Profile()
        db.flush()
    return user.profile


@router.get("", response_model=ProfileOut)
def get_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Profile:
    return _get_or_create(db, user)


@router.patch("", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    profile = _get_or_create(db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
