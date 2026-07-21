"""ORM models for the PE Compass backend.

These mirror the tables described in BACKEND_API.md (originally Supabase
migrations). ``users`` replaces Supabase's ``auth.users``; every other table
hangs off it via ``user_id``. JSON payloads use JSONB on Postgres and plain JSON
elsewhere (e.g. SQLite in tests).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    UniqueConstraint,
)
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# JSONB on Postgres, JSON everywhere else (keeps SQLite-based tests working).
JsonB = JSON().with_variant(JSONB, "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    """Authentication record — replaces Supabase ``auth.users``.

    Accounts authenticate either by password or by a federated identity
    (Google / Apple). ``password_hash`` is null for OAuth-only accounts.
    """

    __tablename__ = "users"
    # A given provider identity (sub) maps to at most one user.
    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_subject", name="uq_users_oauth_identity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    # Federated identity: provider ("google"/"apple") + its stable subject claim.
    oauth_provider: Mapped[str | None] = mapped_column(String(16), nullable=True)
    oauth_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)

    profile: Mapped["Profile"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class Profile(Base):
    """One-to-one profile row, created during signup (old ``handle_new_user``)."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hospital_affiliation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    user: Mapped[User] = relationship(back_populates="profile")


class PatientClassification(Base):
    __tablename__ = "patient_classifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_data: Mapped[dict] = mapped_column(JsonB, nullable=False, default=dict)
    classification_result: Mapped[dict] = mapped_column(JsonB, nullable=False, default=dict)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    respiratory_modifier: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class EcmoCandidacyAssessment(Base):
    __tablename__ = "ecmo_candidacy_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_data: Mapped[dict] = mapped_column(JsonB, nullable=False, default=dict)
    pe_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    indications: Mapped[list] = mapped_column(JsonB, nullable=False, default=list)
    contraindications: Mapped[list] = mapped_column(JsonB, nullable=False, default=list)
    save_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    save_risk_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recommended_config: Mapped[str | None] = mapped_column(String(100), nullable=True)
    candidacy_result: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assessment_details: Mapped[dict] = mapped_column(JsonB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class DeviceToken(Base):
    __tablename__ = "device_tokens"
    __table_args__ = (UniqueConstraint("user_id", "token", name="uq_device_tokens_user_token"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(512), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class RefreshToken(Base):
    """Opaque, revocable refresh token (only its hash is stored)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class Feedback(Base):
    """Feedback on a clinical recommendation.

    ``usefulness`` is the 👍/👎/⚠️ tap; ``clinical_judgment`` is the match
    question. A "potential_issue" sets ``flagged=True`` so those reports are easy
    to find and review separately, alongside the submitting user and timestamp.
    ``subject_type``/``subject_id`` optionally tie the feedback to what was rated
    (e.g. a patient_classification or ecmo_candidacy_assessment).
    """

    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "useful" | "not_useful" | "potential_issue"
    usefulness: Mapped[str] = mapped_column(String(20), nullable=False)
    # "yes" | "partial" | "no"
    clinical_judgment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Description of the concern, captured when usefulness == "potential_issue".
    concern: Mapped[str | None] = mapped_column(Text, nullable=True)
    # True for potential-issue reports — indexed so the review queue is cheap.
    flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    subject_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    user: Mapped[User] = relationship()


class Discussion(Base):
    """A discussion topic authored by an admin in /pe/admin.

    Pairs an ``assessment_result`` with a ``complication``; app users then vote
    yes/no on it (see :class:`DiscussionVote`). One vote per user per discussion.
    """

    __tablename__ = "discussions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    assessment_result: Mapped[str] = mapped_column(Text, nullable=False)
    complication: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    votes: Mapped[list["DiscussionVote"]] = relationship(
        back_populates="discussion", cascade="all, delete-orphan"
    )


class DiscussionVote(Base):
    """One user's yes/no vote on a :class:`Discussion`.

    ``vote`` is True for yes, False for no. A user may vote at most once per
    discussion (enforced by the unique constraint); re-voting updates the row.
    """

    __tablename__ = "discussion_votes"
    __table_args__ = (
        UniqueConstraint(
            "discussion_id", "user_id", name="uq_discussion_votes_discussion_user"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    discussion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vote: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True=yes, False=no
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    discussion: Mapped["Discussion"] = relationship(back_populates="votes")
    user: Mapped[User] = relationship()


class CommunityPost(Base):
    """A community post or question authored by a user.

    ``type`` distinguishes a "question" from a general "post". An optional
    ``poll_question`` turns the post into a Yes/No poll other users vote on (see
    :class:`CommunityPollVote`); threaded discussion lives in
    :class:`CommunityComment`. Deleting a post cascades to its comments and poll
    votes (``ON DELETE CASCADE``). A user may delete only their own posts.
    """

    __tablename__ = "community_posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="post")  # "question"|"post"
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # When set, the post carries a Yes/No poll asking this question.
    poll_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    user: Mapped[User] = relationship()


class CommunityComment(Base):
    """A comment on a post, or a reply to another comment.

    ``parent_comment_id`` is null for top-level comments and points at the parent
    comment for replies. Deleting a post — or a parent comment — cascades to the
    replies (``ON DELETE CASCADE``). A user may delete only their own comments.
    """

    __tablename__ = "community_comments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("community_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    user: Mapped[User] = relationship()


class CommunityPollVote(Base):
    """One user's Yes/No vote on a post's poll.

    ``vote`` is True for yes, False for no. A user may vote at most once per post
    (unique constraint); re-voting updates the row.
    """

    __tablename__ = "community_poll_votes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_community_poll_votes_post_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vote: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True=yes, False=no
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class PasswordResetToken(Base):
    """One-time, short-lived OTP authorizing a password reset.

    ``token_hash`` stores a bcrypt hash of the numeric OTP (never the code
    itself), so a database leak does not expose live reset codes. ``attempts``
    caps how many times a code may be guessed before it is invalidated. The row
    is deleted once the code is consumed, expires, or the guess budget runs out.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
