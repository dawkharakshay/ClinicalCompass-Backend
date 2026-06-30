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


class PasswordResetToken(Base):
    """Single-use, expiring password-reset token (only its hash is stored)."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
