"""Patient-classification endpoints — table ``patient_classifications``.

Every query is scoped to the authenticated user (application-level ownership,
replacing Supabase RLS).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import PatientClassification, User
from app.schemas import PatientClassificationCreate, PatientClassificationOut

router = APIRouter(prefix="/patient-classifications", tags=["patient-classifications"])


@router.get("", response_model=list[PatientClassificationOut])
def list_classifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[PatientClassification]:
    return list(
        db.scalars(
            select(PatientClassification)
            .where(PatientClassification.user_id == user.id)
            .order_by(PatientClassification.created_at.desc())
        )
    )


@router.post("", response_model=PatientClassificationOut, status_code=status.HTTP_201_CREATED)
def create_classification(
    payload: PatientClassificationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientClassification:
    record = PatientClassification(user_id=user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classification(
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    record = db.get(PatientClassification, record_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
