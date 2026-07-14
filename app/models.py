"""SQLAlchemy ORM models: users and their authentication tokens."""

from datetime import datetime, timezone

from fastapi_storages.integrations.sqlalchemy import ImageType
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import UserRole
from app.storage import storage


def _image_url(image) -> str | None:
    """Build a public /uploads URL from a stored image filename."""
    if not image:
        return None
    name = getattr(image, "name", None) or str(image)
    return f"/uploads/{name}" if name else None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    # A given provider identity (sub) maps to at most one user.
    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_subject", name="uq_users_oauth_identity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    # Null for OAuth-only accounts, which authenticate via a provider instead.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Federated identity: provider ("google"/"apple") + its stable subject claim.
    # Both null for password-only accounts; both set once an identity is linked.
    oauth_provider: Mapped[str | None] = mapped_column(String(16), nullable=True)
    oauth_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Profile photo, stored on local disk and served from /uploads (see app.storage).
    avatar = Column(ImageType(storage=storage), nullable=True)
    # Free-text profile details the user can set on themselves.
    medical_speciality: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_institution: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    @property
    def avatar_url(self) -> str | None:
        return _image_url(self.avatar)

    tokens: Mapped[list["Token"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Token(Base):
    """Opaque session token (random string) stored server-side — no JWT."""

    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="tokens")


class PasswordResetToken(Base):
    """One-time, short-lived OTP authorizing a password reset.

    ``token`` stores a bcrypt hash of the numeric OTP (never the OTP itself), so
    a database leak does not expose live reset codes. ``attempts`` caps how many
    times a code may be guessed before it is invalidated.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    attempts: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="reset_tokens")


class PendingRegistration(Base):
    """A short-lived, OTP-verified pending registration (registration v2).

    Step 1 of the two-step v2 sign-up stores the emailed OTP here (as a bcrypt
    hash, never the code itself) keyed by ``email``. Step 2 verifies the code
    and creates the real ``User`` — this row is a throwaway that is deleted once
    the code is consumed or expires. ``attempts`` caps how many times a code may
    be guessed before it is invalidated.

    No password or profile data is persisted here: the client re-sends the full
    registration payload on step 2, so a database leak never exposes a pending
    account's credentials.
    """

    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    token: Mapped[str] = mapped_column(String(64), index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Speciality(Base):
    """A top-level grouping that contains many modules."""

    __tablename__ = "specialities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image = Column(ImageType(storage=storage), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    modules: Mapped[list["Module"]] = relationship(
        back_populates="speciality",
        cascade="all, delete-orphan",
    )

    @property
    def image_url(self) -> str | None:
        return _image_url(self.image)


class Module(Base):
    """A module belonging to a single speciality."""

    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    speciality_id: Mapped[int] = mapped_column(
        ForeignKey("specialities.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image = Column(ImageType(storage=storage), nullable=True)
    # Embedded form, stored verbatim: {"steps": [{"id", "shortLabel", "title", "fields": [...]}]}
    form: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=lambda: {"steps": []},
    )
    appeal_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Data-driven recipe for building a personalized appeal letter from a
    # submission's answers. See app/appeal_letter.py for the shape and renderer.
    appeal_letter_template: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    # Prior-authorization reference (CPT/ICD-10 codes, payer rules), extracted
    # from the legacy *AuthGuide pages. Hybrid shape: structured sections plus a
    # verbatim ``raw`` block. See scripts/seed_auth_guides.py.
    auth_guide: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    # Reference copy of the module's result-generation logic (form data ->
    # recommendation), extracted verbatim from the legacy *Logic.ts pages as
    # documentation. Stored, not executed. See scripts/seed_recommendations.py.
    recommendation: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    speciality: Mapped["Speciality"] = relationship(back_populates="modules")

    @property
    def image_url(self) -> str | None:
        return _image_url(self.image)


class FormSubmission(Base):
    """A user's filled-in answers for a module's form, stored verbatim."""

    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # The submitted answers, stored verbatim: {fieldName: value, ...}
    data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    module: Mapped["Module"] = relationship()
    user: Mapped["User"] = relationship()


class DenialCategory(Base):
    """A denial-reason category for the Denial Template Library (presentation
    metadata: a stable ``value`` plus a human ``label`` and a UI ``color``)."""

    __tablename__ = "denial_categories"

    value: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    position: Mapped[int] = mapped_column(default=0)  # preserves source ordering

    templates: Mapped[list["DenialTemplate"]] = relationship(back_populates="category_obj")


class DenialTemplate(Base):
    """A pre-written appeal paragraph rebutting a specific denial reason.

    Cross-module catalog extracted from the legacy denialTemplates.ts. The
    ``text`` carries [BRACKET] fill-ins a clinician completes; ``applicable_to``
    tags the procedures it fits (``"General"`` = any). See
    scripts/seed_denial_templates.py.
    """

    __tablename__ = "denial_templates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # e.g. "mn-001"
    category: Mapped[str] = mapped_column(
        ForeignKey("denial_categories.value", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    denial_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    # JSON string lists. "references" is a SQL reserved word, so the column is
    # named explicitly to avoid dialect-quoting surprises.
    applicable_to: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list
    )
    references: Mapped[list] = mapped_column(
        "reference_list", JSON().with_variant(JSONB, "postgresql"), default=list
    )

    category_obj: Mapped["DenialCategory"] = relationship(back_populates="templates")


class Collaboration(Base):
    """A collaboration / contact request submitted from the public site.

    Public, unauthenticated submission (name, email, optional speciality,
    message). Stored for admin follow-up; admins are also notified by email when
    SMTP is configured.
    """

    __tablename__ = "collaborations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    speciality: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AppealLetterRating(Base):
    """User rating/feedback for a generated appeal letter.

    ``letter_quality`` and ``effectiveness`` are 1-5 ratings; ``appeal_outcome``
    and ``comments`` are optional free text. Stored for admin review.
    """

    __tablename__ = "appeal_letter_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    letter_quality: Mapped[int] = mapped_column()
    effectiveness: Mapped[int] = mapped_column()
    appeal_outcome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Feedback(Base):
    """General user feedback (category, subject, message). Stored for admin review."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
