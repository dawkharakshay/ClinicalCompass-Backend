"""Discussions and yes/no voting — tables ``discussions`` / ``discussion_votes``.

Admins author discussions (an assessment result paired with a complication) in
/pe/admin. App users list them and cast a yes/no vote; each user has at most one
vote per discussion, and re-voting updates it. Every response carries the running
yes/no tally plus the caller's own vote.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Discussion, DiscussionVote, User
from app.schemas import DiscussionOut, DiscussionVoteRequest

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
