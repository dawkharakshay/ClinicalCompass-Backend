from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User,
    Feedback,
    Discussion,
    PatientClassification,
    EcmoCandidacyAssessment,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)
@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    try:

        users = db.query(func.count(User.id)).scalar() or 0

        discussions = db.query(
            func.count(Discussion.id)
        ).scalar() or 0

        feedback = db.query(
            func.count(Feedback.id)
        ).scalar() or 0

        patient_assessments = db.query(
            func.count(PatientClassification.id)
        ).scalar() or 0

        ecmo_assessments = db.query(
            func.count(EcmoCandidacyAssessment.id)
        ).scalar() or 0

    # MONTHLY USERS

        monthly_users = (
            db.query(
                func.to_char(User.created_at, "Mon").label("month"),
                func.count(User.id).label("count"),
            )
            .group_by("month")
            .order_by(func.min(User.created_at))
            .all()
        )

        # MONTHLY PATIENT ASSESSMENTS

        monthly_assessments = (
            db.query(
                func.to_char(
                    PatientClassification.created_at,
                    "Mon",
                ).label("month"),
                func.count(
                    PatientClassification.id
                ).label("count"),
            )
            .group_by("month")
            .order_by(func.min(PatientClassification.created_at))
            .all()
        )

        # DISCUSSION ACTIVITY

        discussion_activity = (
            db.query(
                func.date(Discussion.created_at).label("date"),
                func.count(Discussion.id).label("count"),
            )
            .group_by("date")
            .order_by("date")
            .all()
        )

        # FEEDBACK

        useful = (
            db.query(func.count(Feedback.id))
            .filter(
                Feedback.usefulness == "useful"
            )
            .scalar()
            or 0
        )

        not_useful = (
            db.query(func.count(Feedback.id))
            .filter(
                Feedback.usefulness == "not_useful"
            )
            .scalar()
            or 0
        )

        potential_issue = (
            db.query(func.count(Feedback.id))
            .filter(
                Feedback.usefulness == "potential_issue"
            )
            .scalar()
            or 0
        )

        flagged = (
            db.query(func.count(Feedback.id))
            .filter(
                Feedback.flagged.is_(True)
            )
            .scalar()
            or 0
        )

        # RESPONSE

        return {
            "success": True,

            "kpis": {
                "users": users,
                "feedback": feedback,
                "discussions": discussions,
                "patient_assessments": patient_assessments,
                "ecmo_assessments": ecmo_assessments,
                "total_assessments": patient_assessments + ecmo_assessments,
            },

            "monthly_users": [
                {
                    "month": month,
                    "count": count,
                }
                for month, count in monthly_users
            ],

            "monthly_assessments": [
                {
                    "month": month,
                    "count": count,
                }
                for month, count in monthly_assessments
            ],

            "discussion_activity": [
                {
                    "date": str(date),
                    "count": count,
                }
                for date, count in discussion_activity
            ],

            "feedback_summary": {
                "useful": useful,
                "not_useful": not_useful,
                "potential_issue": potential_issue,
                "flagged": flagged,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )