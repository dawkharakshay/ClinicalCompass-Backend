"""ECMO-candidacy endpoints — table ``ecmo_candidacy_assessments``.

The spec requires only POST; GET (list) and DELETE are included for parity with
patient-classifications and cost nothing to support.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import EcmoCandidacyAssessment, User
from app.schemas import EcmoAssessmentCreate, EcmoAssessmentOut

router = APIRouter(prefix="/ecmo-assessments", tags=["ecmo-assessments"])


@router.get("", response_model=list[EcmoAssessmentOut])
def list_assessments(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[EcmoCandidacyAssessment]:
    return list(
        db.scalars(
            select(EcmoCandidacyAssessment)
            .where(EcmoCandidacyAssessment.user_id == user.id)
            .order_by(EcmoCandidacyAssessment.created_at.desc())
        )
    )


@router.post("", response_model=EcmoAssessmentOut, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: EcmoAssessmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EcmoCandidacyAssessment:
    record = EcmoCandidacyAssessment(user_id=user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    record = db.get(EcmoCandidacyAssessment, record_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
