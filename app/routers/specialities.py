"""Speciality routes: read-only. Create/edit/delete is done in the admin panel."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Module, Speciality
from app.schemas import (
    CountOut,
    ErrorResponse,
    ModuleOut,
    SpecialityPage,
    SpecialityWithModules,
)

router = APIRouter(
    prefix="/specialities",
    tags=["specialities"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)

_NOT_FOUND = {404: {"model": ErrorResponse, "description": "Speciality not found"}}


def _get_speciality(speciality_id: int, db: Session) -> Speciality:
    speciality = db.get(Speciality, speciality_id)
    if speciality is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speciality not found")
    return speciality


@router.get(
    "",
    response_model=SpecialityPage,
    summary="List specialities (paginated)",
    description="Returns a page of specialities. Use `limit` (1-100) and "
    "`offset` to paginate; `total` is the full count and `next`/`previous` "
    "are page URLs.",
)
def list_specialities(
    request: Request,
    db: Session = Depends(get_db),
    search_query: str | None = Query(None, description="Case-insensitive match on title or description"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> SpecialityPage:
    stmt = select(Speciality).order_by(Speciality.id)
    if search_query:
        pattern = f"%{search_query}%"
        stmt = stmt.where(
            or_(Speciality.title.ilike(pattern), Speciality.description.ilike(pattern))
        )

    # Fetch one extra row to know whether a next page exists (no count query).
    rows = db.scalars(stmt.offset(offset).limit(limit + 1)).all()
    has_next = len(rows) > limit
    items = rows[:limit]

    def page_url(new_offset: int) -> str:
        # include_query_params keeps search_query while updating limit/offset.
        return str(request.url.include_query_params(limit=limit, offset=new_offset))

    next_url = page_url(offset + limit) if has_next else None
    previous_url = page_url(max(offset - limit, 0)) if offset > 0 else None

    return SpecialityPage(items=list(items), next=next_url, previous=previous_url)


@router.get(
    "/count",
    response_model=CountOut,
    summary="Count of specialities",
    description="Returns the total number of specialities.",
)
def count_specialities(db: Session = Depends(get_db)) -> CountOut:
    total = db.scalar(select(func.count()).select_from(Speciality)) or 0
    return CountOut(resource="specialities", count=total)


@router.get(
    "/{speciality_id}",
    response_model=SpecialityWithModules,
    summary="Get a speciality with its modules",
    responses=_NOT_FOUND,
)
def get_speciality(speciality_id: int, db: Session = Depends(get_db)) -> Speciality:
    return _get_speciality(speciality_id, db)


@router.get(
    "/{speciality_id}/modules",
    response_model=list[ModuleOut],
    summary="List modules in a speciality",
    responses=_NOT_FOUND,
)
def list_modules(speciality_id: int, db: Session = Depends(get_db)) -> list[Module]:
    speciality = _get_speciality(speciality_id, db)
    return list(speciality.modules)
