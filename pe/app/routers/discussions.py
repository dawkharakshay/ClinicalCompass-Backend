"""Discussions and yes/no voting — tables ``discussions`` / ``discussion_votes``.

Admins author discussions (an assessment result paired with a complication) —
either in /pe/admin or via the ``X-Admin-Key``-gated create/delete API here.
App users list them and cast a yes/no vote; each user has at most one vote per
discussion, and re-voting updates it. Every response carries the running yes/no
tally plus the caller's own vote.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin_key
from app.models import Discussion, DiscussionComment, DiscussionVote, Profile, User
from app.schemas import (
    DiscussionCommentCreate,
    DiscussionCommentOut,
    DiscussionCreate,
    DiscussionOut,
    DiscussionVoteSummary,
    PaginatedDiscussionComments,
    PaginatedDiscussions,
)

router = APIRouter(prefix="/discussions", tags=["discussions"])


@router.get("", response_model=PaginatedDiscussions)
def list_discussions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedDiscussions:
    """Discussions (topic only), newest first, paginated.

    Vote tallies are NOT included here — fetch them per discussion via
    ``GET /discussions/{id}/vote``.
    """
    total = db.scalar(select(func.count()).select_from(Discussion)) or 0
    rows = list(
        db.scalars(
            select(Discussion)
            .order_by(Discussion.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    items = [
        DiscussionOut(
            id=d.id,
            assessment_result=d.assessment_result,
            complication=d.complication,
            created_at=d.created_at,
        )
        for d in rows
    ]
    return PaginatedDiscussions(items=items, total=total, limit=limit, offset=offset)


def _discussion_or_404(db: Session, discussion_id: uuid.UUID) -> Discussion:
    discussion = db.get(Discussion, discussion_id)
    if discussion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion not found")
    return discussion


def _discussion_out(d: Discussion) -> DiscussionOut:
    return DiscussionOut(
        id=d.id,
        assessment_result=d.assessment_result,
        complication=d.complication,
        created_at=d.created_at,
    )


@router.post(
    "",
    response_model=DiscussionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_key)],
)
def create_discussion(
    payload: DiscussionCreate,
    db: Session = Depends(get_db),
) -> DiscussionOut:
    """Author a new discussion topic (admin-gated via ``X-Admin-Key``).

    Discussions are ownerless topics users vote on, so creation is restricted to
    admins rather than app users.
    """
    discussion = Discussion(
        assessment_result=payload.assessment_result,
        complication=payload.complication,
    )
    db.add(discussion)
    db.commit()
    db.refresh(discussion)
    return _discussion_out(discussion)


@router.delete(
    "/{discussion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin_key)],
)
def delete_discussion(
    discussion_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a discussion and its votes/comments (admin-gated via ``X-Admin-Key``).

    Votes and comments are removed by the ``ON DELETE CASCADE`` FKs / relationship
    cascade on :class:`~app.models.Discussion`.
    """
    discussion = _discussion_or_404(db, discussion_id)
    db.delete(discussion)
    db.commit()


def _my_vote(db: Session, discussion_id: uuid.UUID, user_id: uuid.UUID) -> DiscussionVote | None:
    return db.scalar(
        select(DiscussionVote).where(
            DiscussionVote.discussion_id == discussion_id,
            DiscussionVote.user_id == user_id,
        )
    )


def _set_vote(db: Session, discussion: Discussion, user_id: uuid.UUID, value: bool) -> None:
    """Upsert the caller's vote to ``value`` (True=yes, False=no)."""
    existing = _my_vote(db, discussion.id, user_id)
    if existing is not None:
        existing.vote = value
    else:
        db.add(DiscussionVote(discussion_id=discussion.id, user_id=user_id, vote=value))


def _vote_summary(
    db: Session, discussion_id: uuid.UUID, user_id: uuid.UUID
) -> DiscussionVoteSummary:
    """Build the yes/no tally + the caller's own vote for one discussion."""
    yes_count = db.scalar(
        select(func.count()).select_from(DiscussionVote).where(
            DiscussionVote.discussion_id == discussion_id, DiscussionVote.vote.is_(True)
        )
    ) or 0
    no_count = db.scalar(
        select(func.count()).select_from(DiscussionVote).where(
            DiscussionVote.discussion_id == discussion_id, DiscussionVote.vote.is_(False)
        )
    ) or 0
    existing = _my_vote(db, discussion_id, user_id)
    return DiscussionVoteSummary(
        discussion_id=discussion_id,
        yes_count=yes_count,
        no_count=no_count,
        my_vote=existing.vote if existing is not None else None,
    )


@router.post(
    "/{discussion_id}/vote",
    response_model=DiscussionVoteSummary,
    status_code=status.HTTP_201_CREATED,
)
def vote_yes(
    discussion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiscussionVoteSummary:
    """Cast a **YES** vote (creates or sets the caller's vote to yes)."""
    discussion = _discussion_or_404(db, discussion_id)
    _set_vote(db, discussion, user.id, True)
    db.commit()
    return _vote_summary(db, discussion.id, user.id)


@router.delete("/{discussion_id}/vote", response_model=DiscussionVoteSummary)
def vote_no(
    discussion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiscussionVoteSummary:
    """Cast a **NO** vote (creates or sets the caller's vote to no)."""
    discussion = _discussion_or_404(db, discussion_id)
    _set_vote(db, discussion, user.id, False)
    db.commit()
    return _vote_summary(db, discussion.id, user.id)


@router.put("/{discussion_id}/vote", response_model=DiscussionVoteSummary)
def change_vote(
    discussion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiscussionVoteSummary:
    """Flip the caller's existing vote to the opposite (404 if not voted yet)."""
    discussion = _discussion_or_404(db, discussion_id)
    existing = _my_vote(db, discussion.id, user.id)
    if existing is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "You have not voted on this discussion yet"
        )
    existing.vote = not existing.vote  # flip yes<->no
    db.commit()
    return _vote_summary(db, discussion.id, user.id)


@router.get("/{discussion_id}/vote", response_model=DiscussionVoteSummary)
def get_vote_summary(
    discussion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiscussionVoteSummary:
    """The yes/no tally for a discussion plus the caller's own vote."""
    _discussion_or_404(db, discussion_id)
    return _vote_summary(db, discussion_id, user.id)


@router.delete("/{discussion_id}/vote/me", response_model=DiscussionVoteSummary)
def retract_vote(
    discussion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiscussionVoteSummary:
    """Retract the caller's vote entirely, so ``my_vote`` returns to null.

    Idempotent — a no-op (still 200) if the caller hasn't voted.
    """
    _discussion_or_404(db, discussion_id)
    existing = _my_vote(db, discussion_id, user.id)
    if existing is not None:
        db.delete(existing)
        db.commit()
    return _vote_summary(db, discussion_id, user.id)


# --- Comments (flat) ----------------------------------------------------------
def _comment_out(comment: DiscussionComment, author_name: str | None) -> DiscussionCommentOut:
    return DiscussionCommentOut(
        id=comment.id,
        discussion_id=comment.discussion_id,
        user_id=comment.user_id,
        author_name=author_name,
        body=comment.body,
        created_at=comment.created_at,
    )


@router.post(
    "/{discussion_id}/comments",
    response_model=DiscussionCommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    discussion_id: uuid.UUID,
    payload: DiscussionCommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiscussionCommentOut:
    """Add a comment to a discussion."""
    discussion = db.get(Discussion, discussion_id)
    if discussion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion not found")
    comment = DiscussionComment(
        discussion_id=discussion.id, user_id=user.id, body=payload.body
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    name = db.scalar(select(Profile.display_name).where(Profile.user_id == user.id))
    return _comment_out(comment, name)


@router.get("/{discussion_id}/comments", response_model=PaginatedDiscussionComments)
def list_comments(
    discussion_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedDiscussionComments:
    """A discussion's comments, oldest first, paginated with a total count."""
    discussion = db.get(Discussion, discussion_id)
    if discussion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion not found")
    total = db.scalar(
        select(func.count()).select_from(DiscussionComment).where(
            DiscussionComment.discussion_id == discussion_id
        )
    ) or 0
    rows = list(
        db.scalars(
            select(DiscussionComment)
            .where(DiscussionComment.discussion_id == discussion_id)
            .order_by(DiscussionComment.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
    )
    # Resolve author display names in one query.
    names = {}
    if rows:
        names = {
            uid: name
            for uid, name in db.execute(
                select(Profile.user_id, Profile.display_name).where(
                    Profile.user_id.in_({c.user_id for c in rows})
                )
            ).all()
        }
    items = [_comment_out(c, names.get(c.user_id)) for c in rows]
    return PaginatedDiscussionComments(items=items, total=total, limit=limit, offset=offset)


@router.delete(
    "/{discussion_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    discussion_id: uuid.UUID,
    comment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a comment you authored on a discussion."""
    comment = db.get(DiscussionComment, comment_id)
    if comment is None or comment.discussion_id != discussion_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You can only delete your own comments"
        )
    db.delete(comment)
    db.commit()
