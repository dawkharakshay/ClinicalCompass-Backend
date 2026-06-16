"""Profile photo upload for the authenticated user.

The photo is stored on local disk via :mod:`app.storage` (the same backing
store as speciality/module images) and served read-only from ``/uploads``. The
uploaded file is validated to be a real image by Pillow before it is persisted.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi_storages.exceptions import ValidationException
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import ErrorResponse, ProfileUpdate, UserOut
from app.security import generate_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.put(
    "",
    response_model=UserOut,
    summary="Set the current user's medical speciality and current institution",
    description="Updates the authenticated user's free-text profile details: "
    "`medical_speciality` and `current_institution`. Only the fields included "
    "in the request body are changed; send an explicit `null` to clear a field. "
    "Returns the updated user.",
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
    },
)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    # Only touch fields the client actually sent, so an omitted field is left
    # untouched while an explicit null clears it.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

# Upload guard rails. The content type and extension are checked up front; the
# bytes are then verified to decode as a real image (see ImageType.save).
MAX_AVATAR_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _delete_quietly(image) -> None:
    """Best-effort removal of a previously stored avatar file."""
    if not image:
        return
    try:
        image.delete()
    except Exception:  # pragma: no cover - cleanup must never fail the request
        logger.warning("Failed to delete old avatar file %r", getattr(image, "name", image))


@router.put(
    "/photo",
    response_model=UserOut,
    summary="Upload or replace the current user's profile photo",
    description="Uploads a profile photo for the authenticated user as "
    "`multipart/form-data` (field name `file`). Replaces any existing photo. "
    "Accepts JPEG, PNG, WebP, or GIF up to 5 MB. Returns the updated user, "
    "whose `avatar_url` points at the stored image under `/uploads`.",
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        413: {"model": ErrorResponse, "description": "File exceeds the 5 MB limit"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        422: {"model": ErrorResponse, "description": "File is not a valid image"},
    },
)
def upload_profile_photo(
    file: UploadFile = File(..., description="The image file to use as the profile photo."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Allowed types: JPEG, PNG, WebP, GIF.",
        )

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file extension. Allowed: .jpg, .jpeg, .png, .webp, .gif.",
        )

    if file.size is not None and file.size > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum size is 5 MB.",
        )

    # Non-guessable, per-user filename so uploads never overwrite another user's
    # avatar (the storage backend overwrites files of the same name).
    file.filename = f"avatars/user_{current_user.id}_{generate_token()[:16]}{ext}"

    old_avatar = current_user.avatar
    try:
        current_user.avatar = file
        db.add(current_user)
        # The image is validated by Pillow when the column is flushed; an invalid
        # file surfaces as a ValidationException wrapped in a StatementError.
        db.commit()
    except StatementError as exc:
        db.rollback()
        if isinstance(exc.orig, ValidationException):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Uploaded file is not a valid image.",
            ) from exc
        raise

    db.refresh(current_user)
    _delete_quietly(old_avatar)
    return current_user


@router.delete(
    "/photo",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove the current user's profile photo",
    description="Deletes the authenticated user's profile photo, if any. "
    "Always succeeds (no-op when no photo is set).",
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
    },
)
def delete_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    old_avatar = current_user.avatar
    if old_avatar is None:
        return

    current_user.avatar = None
    db.add(current_user)
    db.commit()
    _delete_quietly(old_avatar)
