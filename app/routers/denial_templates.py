"""Denial Template Library routes: read-only.

A cross-module catalog of pre-written appeal paragraphs organized by denial
reason. Mirrors the legacy client logic (denialTemplates.ts):
  - by category      (getTemplatesByCategory)
  - by procedure     (getTemplatesForProcedure: applicable_to ∋ procedure OR "General")
  - free-text search (searchTemplates: title / denial reason / text)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import DenialCategory, DenialTemplate
from app.schemas import (
    CountOut,
    DenialCategoryOut,
    DenialTemplateOut,
    DenialTemplatePage,
    ErrorResponse,
)

router = APIRouter(
    prefix="/denial-templates",
    tags=["denial-templates"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)

_NOT_FOUND = {404: {"model": ErrorResponse, "description": "Denial template not found"}}

# "General" templates apply to every procedure (matches the legacy client).
_GENERAL = "General"


def _matches_procedure(template: DenialTemplate, procedure: str) -> bool:
    applicable = template.applicable_to or []
    return procedure in applicable or _GENERAL in applicable


def _filtered(
    db: Session, category: str | None, procedure: str | None, search: str | None
) -> list[DenialTemplate]:
    """Apply category + search in SQL, then the JSON-list procedure filter in
    Python (the catalog is tiny, and this stays portable across SQLite/Postgres)."""
    stmt = select(DenialTemplate).order_by(DenialTemplate.id)
    if category:
        stmt = stmt.where(DenialTemplate.category == category)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                DenialTemplate.title.ilike(pattern),
                DenialTemplate.denial_reason.ilike(pattern),
                DenialTemplate.text.ilike(pattern),
            )
        )
    rows = list(db.scalars(stmt).all())
    if procedure:
        rows = [t for t in rows if _matches_procedure(t, procedure)]
    return rows


@router.get(
    "",
    response_model=DenialTemplatePage,
    summary="List/search denial templates (paginated)",
    description="Returns a page of denial-appeal templates. Filter by `category`, "
    "`procedure` (templates tagged for that procedure or `General`), and/or "
    "`search` (case-insensitive match on title, denial reason, or text). "
    "Paginate with `limit`/`offset`; `next`/`previous` are URLs.",
)
def list_denial_templates(
    request: Request,
    db: Session = Depends(get_db),
    category: str | None = Query(None, description="Filter to a denial category value"),
    procedure: str | None = Query(
        None, description='Filter to templates tagged for this procedure (or "General")'
    ),
    search: str | None = Query(None, description="Case-insensitive match on title/denial reason/text"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> DenialTemplatePage:
    rows = _filtered(db, category, procedure, search)
    page = rows[offset : offset + limit]
    has_next = offset + limit < len(rows)

    def page_url(new_offset: int) -> str:
        return str(request.url.include_query_params(limit=limit, offset=new_offset))

    return DenialTemplatePage(
        items=[DenialTemplateOut.model_validate(t) for t in page],
        next=page_url(offset + limit) if has_next else None,
        previous=page_url(max(offset - limit, 0)) if offset > 0 else None,
    )


@router.get(
    "/count",
    response_model=CountOut,
    summary="Count of denial templates",
    description="Total number of denial templates, after any `category`/`procedure`/`search` filter.",
)
def count_denial_templates(
    db: Session = Depends(get_db),
    category: str | None = Query(None),
    procedure: str | None = Query(None),
    search: str | None = Query(None),
) -> CountOut:
    return CountOut(
        resource="denial-templates",
        count=len(_filtered(db, category, procedure, search)),
    )


@router.get(
    "/categories",
    response_model=list[DenialCategoryOut],
    summary="List denial categories (with template counts)",
    description="Returns the denial-reason categories in source order, each with a "
    "count of templates. Pass `procedure` to count only templates applicable to that "
    "procedure (matches the legacy category chips).",
)
def list_denial_categories(
    db: Session = Depends(get_db),
    procedure: str | None = Query(
        None, description='Count only templates for this procedure (or "General")'
    ),
) -> list[DenialCategoryOut]:
    categories = db.scalars(
        select(DenialCategory).order_by(DenialCategory.position, DenialCategory.value)
    ).all()
    templates = list(db.scalars(select(DenialTemplate)).all())
    if procedure:
        templates = [t for t in templates if _matches_procedure(t, procedure)]
    counts: dict[str, int] = {}
    for t in templates:
        counts[t.category] = counts.get(t.category, 0) + 1
    return [
        DenialCategoryOut(value=c.value, label=c.label, color=c.color, count=counts.get(c.value, 0))
        for c in categories
    ]


@router.get(
    "/{template_id}",
    response_model=DenialTemplateOut,
    summary="Get a single denial template",
    responses=_NOT_FOUND,
)
def get_denial_template(template_id: str, db: Session = Depends(get_db)) -> DenialTemplateOut:
    template = db.get(DenialTemplate, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Denial template not found"
        )
    return DenialTemplateOut.model_validate(template)
