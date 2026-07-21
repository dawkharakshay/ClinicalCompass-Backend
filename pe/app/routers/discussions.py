"""Discussions and yes/no voting — tables ``discussions`` / ``discussion_votes``.

Admins author discussions (an assessment result paired with a complication) in
/pe/admin. App users list them and cast a yes/no vote; each user has at most one
vote per discussion, and re-voting updates it. Every response carries the running
yes/no tally plus the caller's own vote.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Discussion, DiscussionComment, DiscussionVote, Profile, User
from app.schemas import (
    DiscussionCommentCreate,
    DiscussionCommentOut,
    DiscussionOut,
    DiscussionVoteRequest,
    PaginatedDiscussionComments,
)

router = APIRouter(prefix="/discussions", tags=["discussions"])


def _single_out(db: Session, discussion: Discussion, user_id) -> DiscussionOut:
    """Build a DiscussionOut for one discussion (tally + the caller's vote)."""
    yes_count = (
        db.scalar(
            select(func.count())
            .select_from(DiscussionVote)
            .where(DiscussionVote.discussion_id == discussion.id, DiscussionVote.vote.is_(True))
        )
        or 0
    )
    no_count = (
        db.scalar(
            select(func.count())
            .select_from(DiscussionVote)
            .where(DiscussionVote.discussion_id == discussion.id, DiscussionVote.vote.is_(False))
        )
        or 0
    )
    my_vote = db.scalar(
        select(DiscussionVote.vote).where(
            DiscussionVote.discussion_id == discussion.id,
            DiscussionVote.user_id == user_id,
        )
    )
    return DiscussionOut(
        id=discussion.id,
        assessment_result=discussion.assessment_result,
        complication=discussion.complication,
        yes_count=yes_count,
        no_count=no_count,
        my_vote=my_vote,
        created_at=discussion.created_at,
    )


@router.get("", response_model=list[DiscussionOut])
def list_discussions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[DiscussionOut]:
    """All discussions, newest first, with yes/no tallies and the caller's vote."""
    # One grouped query for the tallies (yes/no counts per discussion)...
    rows = db.execute(
        select(
            Discussion,
            func.count(case((DiscussionVote.vote.is_(True), 1))).label("yes_count"),
            func.count(case((DiscussionVote.vote.is_(False), 1))).label("no_count"),
        )
        .outerjoin(DiscussionVote, DiscussionVote.discussion_id == Discussion.id)
        .group_by(Discussion.id)
        .order_by(Discussion.created_at.desc())
    ).all()
    # ...and one query for the caller's own votes across all discussions.
    my_votes = {
        discussion_id: vote
        for discussion_id, vote in db.execute(
            select(DiscussionVote.discussion_id, DiscussionVote.vote).where(
                DiscussionVote.user_id == user.id
            )
        ).all()
    }
    return [
        DiscussionOut(
            id=discussion.id,
            assessment_result=discussion.assessment_result,
            complication=discussion.complication,
            yes_count=yes_count,
            no_count=no_count,
            my_vote=my_votes.get(discussion.id),
            created_at=discussion.created_at,
        )
        for discussion, yes_count, no_count in rows
    ]


@router.post("/{discussion_id}/vote", response_model=DiscussionOut)
def cast_vote(
    discussion_id: uuid.UUID,
    payload: DiscussionVoteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiscussionOut:
    """Cast (or change) the caller's yes/no vote on a discussion."""
    discussion = db.get(Discussion, discussion_id)
    if discussion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discussion not found")

    existing = db.scalar(
        select(DiscussionVote).where(
            DiscussionVote.discussion_id == discussion.id,
            DiscussionVote.user_id == user.id,
        )
    )
    if existing is not None:
        existing.vote = payload.vote  # re-voting updates the existing row
    else:
        db.add(
            DiscussionVote(discussion_id=discussion.id, user_id=user.id, vote=payload.vote)
        )
    db.commit()
    return _single_out(db, discussion, user.id)


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
