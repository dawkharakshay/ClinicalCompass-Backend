"""Community forum — posts/questions, threaded comments, and Yes/No polls.

Tables ``community_posts`` / ``community_comments`` / ``community_poll_votes``.
Authenticated users create posts (optionally a question) and can attach a Yes/No
poll; anyone can list posts (paginated), comment or reply, list a post's comments
(paginated), and vote on a poll. Users may delete only their own posts and
comments — deleting a post cascades to its comments and poll votes.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import CommunityComment, CommunityPollVote, CommunityPost, Profile, User
from app.schemas import (
    CommunityCommentCreate,
    CommunityCommentOut,
    CommunityPollAdd,
    CommunityPollVoteRequest,
    CommunityPostCreate,
    CommunityPostOut,
    PaginatedComments,
    PaginatedPosts,
)

router = APIRouter(prefix="/community", tags=["community"])


def _author_names(db: Session, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, str | None]:
    """Map user_id -> profile display name for a set of authors (one query)."""
    if not user_ids:
        return {}
    rows = db.execute(
        select(Profile.user_id, Profile.display_name).where(Profile.user_id.in_(user_ids))
    ).all()
    return {uid: name for uid, name in rows}


def _post_out(db: Session, post: CommunityPost, user_id: uuid.UUID) -> CommunityPostOut:
    """Assemble a single post's output (poll tally, caller's vote, comment count)."""
    yes = db.scalar(
        select(func.count()).select_from(CommunityPollVote).where(
            CommunityPollVote.post_id == post.id, CommunityPollVote.vote.is_(True)
        )
    ) or 0
    no = db.scalar(
        select(func.count()).select_from(CommunityPollVote).where(
            CommunityPollVote.post_id == post.id, CommunityPollVote.vote.is_(False)
        )
    ) or 0
    my_vote = db.scalar(
        select(CommunityPollVote.vote).where(
            CommunityPollVote.post_id == post.id, CommunityPollVote.user_id == user_id
        )
    )
    comment_count = db.scalar(
        select(func.count()).select_from(CommunityComment).where(
            CommunityComment.post_id == post.id
        )
    ) or 0
    name = db.scalar(select(Profile.display_name).where(Profile.user_id == post.user_id))
    return CommunityPostOut(
        id=post.id,
        user_id=post.user_id,
        author_name=name,
        title=post.title,
        type=post.type,
        body=post.body,
        has_poll=post.poll_question is not None,
        poll_question=post.poll_question,
        poll_yes_count=yes,
        poll_no_count=no,
        my_vote=my_vote,
        comment_count=comment_count,
        created_at=post.created_at,
    )


def _comment_out(comment: CommunityComment, author_name: str | None) -> CommunityCommentOut:
    return CommunityCommentOut(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        author_name=author_name,
        parent_comment_id=comment.parent_comment_id,
        body=comment.body,
        created_at=comment.created_at,
    )


# --- Posts / questions --------------------------------------------------------
@router.post("/posts", response_model=CommunityPostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: CommunityPostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommunityPostOut:
    """Ask a question or create a community post (optionally with a Yes/No poll)."""
    post = CommunityPost(
        user_id=user.id,
        title=payload.title,
        type=payload.type,
        body=payload.body,
        poll_question=payload.poll_question,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_out(db, post, user.id)


@router.get("/posts", response_model=PaginatedPosts)
def list_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedPosts:
    """All community posts, newest first, paginated with a total count."""
    total = db.scalar(select(func.count()).select_from(CommunityPost)) or 0
    posts = list(
        db.scalars(
            select(CommunityPost)
            .order_by(CommunityPost.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    if not posts:
        return PaginatedPosts(items=[], total=total, limit=limit, offset=offset)

    ids = [p.id for p in posts]
    names = _author_names(db, {p.user_id for p in posts})
    # Poll tallies per post (yes/no counts) in one grouped query.
    yes_map: dict[uuid.UUID, int] = {}
    no_map: dict[uuid.UUID, int] = {}
    for pid, y, n in db.execute(
        select(
            CommunityPollVote.post_id,
            func.count(case((CommunityPollVote.vote.is_(True), 1))),
            func.count(case((CommunityPollVote.vote.is_(False), 1))),
        )
        .where(CommunityPollVote.post_id.in_(ids))
        .group_by(CommunityPollVote.post_id)
    ).all():
        yes_map[pid] = y
        no_map[pid] = n
    # Comment counts per post.
    cc_map = {
        pid: c
        for pid, c in db.execute(
            select(CommunityComment.post_id, func.count())
            .where(CommunityComment.post_id.in_(ids))
            .group_by(CommunityComment.post_id)
        ).all()
    }
    # The caller's own votes across this page.
    mv_map = {
        pid: v
        for pid, v in db.execute(
            select(CommunityPollVote.post_id, CommunityPollVote.vote).where(
                CommunityPollVote.user_id == user.id,
                CommunityPollVote.post_id.in_(ids),
            )
        ).all()
    }
    items = [
        CommunityPostOut(
            id=p.id,
            user_id=p.user_id,
            author_name=names.get(p.user_id),
            title=p.title,
            type=p.type,
            body=p.body,
            has_poll=p.poll_question is not None,
            poll_question=p.poll_question,
            poll_yes_count=yes_map.get(p.id, 0),
            poll_no_count=no_map.get(p.id, 0),
            my_vote=mv_map.get(p.id),
            comment_count=cc_map.get(p.id, 0),
            created_at=p.created_at,
        )
        for p in posts
    ]
    return PaginatedPosts(items=items, total=total, limit=limit, offset=offset)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a post you authored (cascades to its comments and poll votes)."""
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own posts")
    db.delete(post)
    db.commit()


# --- Polls --------------------------------------------------------------------
@router.post("/posts/{post_id}/poll", response_model=CommunityPostOut)
def add_poll(
    post_id: uuid.UUID,
    payload: CommunityPollAdd,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommunityPostOut:
    """Attach (or replace) a Yes/No poll on a post you authored."""
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only add a poll to your own post")
    post.poll_question = payload.poll_question
    db.commit()
    db.refresh(post)
    return _post_out(db, post, user.id)


@router.post("/posts/{post_id}/poll/vote", response_model=CommunityPostOut)
def vote_poll(
    post_id: uuid.UUID,
    payload: CommunityPollVoteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommunityPostOut:
    """Cast (or change) your Yes/No vote on a post's poll."""
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.poll_question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This post has no poll")
    existing = db.scalar(
        select(CommunityPollVote).where(
            CommunityPollVote.post_id == post.id, CommunityPollVote.user_id == user.id
        )
    )
    if existing is not None:
        existing.vote = payload.vote
    else:
        db.add(CommunityPollVote(post_id=post.id, user_id=user.id, vote=payload.vote))
    db.commit()
    return _post_out(db, post, user.id)


# --- Comments / replies -------------------------------------------------------
@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityCommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    post_id: uuid.UUID,
    payload: CommunityCommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommunityCommentOut:
    """Add a comment on a post, or a reply (set ``parent_comment_id``)."""
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if payload.parent_comment_id is not None:
        parent = db.get(CommunityComment, payload.parent_comment_id)
        if parent is None or parent.post_id != post.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "parent_comment_id does not belong to this post",
            )
    comment = CommunityComment(
        post_id=post.id,
        user_id=user.id,
        parent_comment_id=payload.parent_comment_id,
        body=payload.body,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    name = db.scalar(select(Profile.display_name).where(Profile.user_id == user.id))
    return _comment_out(comment, name)


@router.get("/posts/{post_id}/comments", response_model=PaginatedComments)
def list_comments(
    post_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedComments:
    """A post's comments and replies, oldest first, paginated with a total count."""
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    total = db.scalar(
        select(func.count()).select_from(CommunityComment).where(
            CommunityComment.post_id == post_id
        )
    ) or 0
    rows = list(
        db.scalars(
            select(CommunityComment)
            .where(CommunityComment.post_id == post_id)
            .order_by(CommunityComment.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
    )
    names = _author_names(db, {c.user_id for c in rows})
    items = [_comment_out(c, names.get(c.user_id)) for c in rows]
    return PaginatedComments(items=items, total=total, limit=limit, offset=offset)


@router.delete(
    "/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a comment or reply you authored (cascades to its replies)."""
    comment = db.get(CommunityComment, comment_id)
    if comment is None or comment.post_id != post_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You can only delete your own comments"
        )
    db.delete(comment)
    db.commit()
