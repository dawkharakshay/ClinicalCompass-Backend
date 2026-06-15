"""Form submission routes: submit a module's form and read back submissions.

A submission belongs to the authenticated user; users only ever see their own.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.appeal_letter import render_appeal_letter
from app.database import get_db
from app.dependencies import get_current_user
from app.models import FormSubmission, Module, User
from app.recommendations import coerce_submission, get_assessor, present_result
from app.schemas import (
    AppealLetterOut,
    ErrorResponse,
    FormSubmissionCreate,
    FormSubmissionOut,
    FormSubmissionPage,
    RecommendationResultOut,
)

router = APIRouter(
    prefix="/submissions",
    tags=["submissions"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.post(
    "",
    response_model=FormSubmissionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a module's form",
    description="Stores the authenticated user's answers for the given module's "
    "form. The answers are kept verbatim as a JSON object keyed by field name.",
    responses={404: {"model": ErrorResponse, "description": "Module not found"}},
)
def create_submission(
    payload: FormSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FormSubmission:
    if db.get(Module, payload.module_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
        )

    submission = FormSubmission(
        module_id=payload.module_id,
        user_id=current_user.id,
        data=payload.data,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get(
    "",
    response_model=FormSubmissionPage,
    summary="List my form submissions (paginated)",
    description="Returns a page of the authenticated user's own submissions, "
    "newest first. Filter to one module with `module_id`.",
)
def list_submissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    module_id: int | None = Query(None, ge=1, description="Filter to this module"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> FormSubmissionPage:
    stmt = (
        select(FormSubmission)
        .where(FormSubmission.user_id == current_user.id)
        .order_by(FormSubmission.id.desc())
    )
    if module_id is not None:
        stmt = stmt.where(FormSubmission.module_id == module_id)

    rows = db.scalars(stmt.offset(offset).limit(limit + 1)).all()
    has_next = len(rows) > limit
    items = rows[:limit]

    def page_url(new_offset: int) -> str:
        return str(request.url.include_query_params(limit=limit, offset=new_offset))

    next_url = page_url(offset + limit) if has_next else None
    previous_url = page_url(max(offset - limit, 0)) if offset > 0 else None
    return FormSubmissionPage(items=list(items), next=next_url, previous=previous_url)


def _own_submission(submission_id: int, db: Session, user: User) -> FormSubmission:
    submission = db.get(FormSubmission, submission_id)
    # Don't reveal existence of other users' submissions.
    if submission is None or submission.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )
    return submission


@router.get(
    "/{submission_id}",
    response_model=FormSubmissionOut,
    summary="Get one of my submissions",
    responses={404: {"model": ErrorResponse, "description": "Submission not found"}},
)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FormSubmission:
    return _own_submission(submission_id, db, current_user)


@router.get(
    "/{submission_id}/appeal-letter",
    response_model=AppealLetterOut,
    summary="Get the personalized appeal letter for a submission",
    description="Builds a personalized appeal letter from the submission's "
    "answers using the module's stored appeal-letter template (defaults, derived "
    "values, conditional sections, and {{placeholder}} substitution). Falls back "
    "to the module's plain-text appeal letter (with placeholder substitution) "
    "when no template is configured.",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Submission not found, or no appeal letter configured",
        },
    },
)
def get_submission_appeal_letter(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AppealLetterOut:
    submission = _own_submission(submission_id, db, current_user)
    module = db.get(Module, submission.module_id)

    template = module.appeal_letter_template if module else None
    if not template and module and module.appeal_letter:
        # Legacy fallback: treat the plain-text letter as a placeholder template.
        template = {"template": module.appeal_letter}
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No appeal letter configured for this module",
        )

    letter = render_appeal_letter(template, submission.data or {})
    return AppealLetterOut(
        submission_id=submission.id,
        module_id=submission.module_id,
        letter=letter,
    )


@router.get(
    "/{submission_id}/recommendation",
    response_model=RecommendationResultOut,
    summary="Compute the recommendation for a submission",
    description="Runs the module's result-generation logic (ported 1:1 from the "
    "legacy engine) over the submission's answers and returns the engine's native "
    "output. The logic is selected by the module form's `logicKey`. Returns 404 "
    "when the submission's module has no ported recommendation engine.",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Submission not found, or no recommendation logic available",
        },
    },
)
def get_submission_recommendation(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResultOut:
    submission = _own_submission(submission_id, db, current_user)
    module = db.get(Module, submission.module_id)
    form = (module.form if module else None) or {}
    logic_key = form.get("logicKey")

    assessor = get_assessor(logic_key)
    if assessor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendation logic available for this module",
        )

    coerced = coerce_submission(submission.data or {}, form)
    result = present_result(logic_key, assessor(coerced))
    return RecommendationResultOut(
        submission_id=submission.id,
        module_id=submission.module_id,
        logic_key=logic_key,
        result=result,
    )
