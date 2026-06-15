"""Module routes: read-only. Create/edit/delete is done in the admin panel."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Module
from app.schemas import (
    AuthGuideOut,
    CountOut,
    ErrorResponse,
    ModuleDetail,
    ModuleForm,
    ModulePage,
    RecommendationOut,
)

router = APIRouter(
    prefix="/modules",
    tags=["modules"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)

_NOT_FOUND = {404: {"model": ErrorResponse, "description": "Module not found"}}


@router.get(
    "",
    response_model=ModulePage,
    summary="List/search modules (paginated)",
    description="Returns a page of modules. Filter by `specialities` (one or "
    "more speciality ids, repeatable) and/or `search_query` (case-insensitive "
    "title match). Paginate with `limit`/`offset`; `next`/`previous` are URLs.",
)
def list_modules(
    request: Request,
    db: Session = Depends(get_db),
    specialities: list[int] | None = Query(
        None, description="Filter to these speciality ids (repeatable)"
    ),
    search_query: str | None = Query(None, description="Case-insensitive match on title or description"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> ModulePage:
    stmt = select(Module).order_by(Module.id)
    if specialities:
        stmt = stmt.where(Module.speciality_id.in_(specialities))
    if search_query:
        pattern = f"%{search_query}%"
        stmt = stmt.where(
            or_(Module.title.ilike(pattern), Module.description.ilike(pattern))
        )

    rows = db.scalars(stmt.offset(offset).limit(limit + 1)).all()
    has_next = len(rows) > limit
    items = rows[:limit]

    def page_url(new_offset: int) -> str:
        return str(request.url.include_query_params(limit=limit, offset=new_offset))

    next_url = page_url(offset + limit) if has_next else None
    previous_url = page_url(max(offset - limit, 0)) if offset > 0 else None
    return ModulePage(items=list(items), next=next_url, previous=previous_url)


@router.get(
    "/count",
    response_model=CountOut,
    summary="Count of modules",
    description="Returns the total number of modules across all specialities.",
)
def count_modules(db: Session = Depends(get_db)) -> CountOut:
    total = db.scalar(select(func.count()).select_from(Module)) or 0
    return CountOut(resource="modules", count=total)


def _get_module(module_id: int, db: Session) -> Module:
    module = db.get(Module, module_id)
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return module


@router.get(
    "/{module_id}",
    response_model=ModuleDetail,
    summary="Get a module (including its form)",
    responses=_NOT_FOUND,
)
def get_module(module_id: int, db: Session = Depends(get_db)) -> ModuleDetail:
    module = _get_module(module_id, db)
    return ModuleDetail(
        id=module.id,
        speciality_id=module.speciality_id,
        title=module.title,
        description=module.description,
        image_url=module.image_url,
        form=ModuleForm.model_validate(module.form) if module.form else ModuleForm(),
        appeal_letter=module.appeal_letter,
        appeal_letter_template=module.appeal_letter_template,
        auth_guide=module.auth_guide,
        recommendation=module.recommendation,
    )


@router.get(
    "/{module_id}/form",
    response_model=ModuleForm,
    summary="Get a module's form (stages -> fields)",
    responses=_NOT_FOUND,
)
def get_module_form(module_id: int, db: Session = Depends(get_db)) -> ModuleForm:
    module = _get_module(module_id, db)
    return ModuleForm.model_validate(module.form) if module.form else ModuleForm()


@router.get(
    "/{module_id}/auth-guide",
    response_model=AuthGuideOut | None,
    summary="Get a module's authorization guide (CPT/ICD/payer reference)",
    description="Returns the module's prior-authorization guide (CPT codes, "
    "ICD-10 codes, payer rules, plus a verbatim `raw` block), or `null` when the "
    "module has no guide configured.",
    responses=_NOT_FOUND,
)
def get_module_auth_guide(
    module_id: int, db: Session = Depends(get_db)
) -> dict | None:
    module = _get_module(module_id, db)
    return module.auth_guide


@router.get(
    "/{module_id}/recommendation",
    response_model=RecommendationOut | None,
    summary="Get a module's result-generation logic (reference)",
    description="Returns the module's recommendation logic reference (source "
    "files, a `hasLogic` flag, and a verbatim `raw.markdown` block), or `null` "
    "when the module has none. Documentation only — the backend does not execute it.",
    responses=_NOT_FOUND,
)
def get_module_recommendation(
    module_id: int, db: Session = Depends(get_db)
) -> dict | None:
    module = _get_module(module_id, db)
    return module.recommendation
