"""Pydantic request/response schemas for the PE Compass backend."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

Usefulness = Literal["useful", "not_useful", "potential_issue"]
ClinicalJudgment = Literal["yes", "partial", "no"]


# --- Auth ---------------------------------------------------------------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    hospital_affiliation: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = Field(
        description="Generic confirmation, the same regardless of whether the "
        "email exists, to avoid account enumeration."
    )
    expires_at: datetime | None = Field(
        default=None, description="When the code expires (null when no code was issued)."
    )


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        min_length=4,
        max_length=10,
        description="The one-time code sent to the user's email by /auth/forgot-password.",
        examples=["482915"],
    )
    new_password: str = Field(min_length=8)


class GoogleOAuthRequest(BaseModel):
    id_token: str = Field(
        description="The Google ID token (JWT) from the native Google Sign-In SDK. "
        "Identity (subject, email, name) is read from the verified token."
    )
    # Optional: set the profile's hospital affiliation on first sign-in.
    hospital_affiliation: str | None = None


class AppleOAuthRequest(BaseModel):
    identity_token: str = Field(
        description="The Apple identity token (JWT) from Sign in with Apple."
    )
    full_name: str | None = Field(
        default=None,
        description="The user's name. Apple returns this only on the FIRST "
        "authorization, so the client must send it then.",
    )
    hospital_affiliation: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut


class AccessRefresh(BaseModel):
    access_token: str
    refresh_token: str


class SessionOut(BaseModel):
    user: UserOut


# --- Profiles -----------------------------------------------------------------
class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str | None = None
    hospital_affiliation: str | None = None


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    hospital_affiliation: str | None = None


# --- Patient classifications --------------------------------------------------
class PatientClassificationCreate(BaseModel):
    patient_name: str | None = None
    patient_data: dict[str, Any] = Field(default_factory=dict)
    classification_result: dict[str, Any] = Field(default_factory=dict)
    category: str | None = None
    risk_level: str | None = None
    respiratory_modifier: bool = False


class PatientClassificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_name: str | None
    patient_data: dict[str, Any]
    classification_result: dict[str, Any]
    category: str | None
    risk_level: str | None
    respiratory_modifier: bool
    created_at: datetime


# --- ECMO assessments ---------------------------------------------------------
class EcmoAssessmentCreate(BaseModel):
    patient_name: str | None = None
    patient_data: dict[str, Any] = Field(default_factory=dict)
    pe_category: str | None = None
    indications: list[Any] = Field(default_factory=list)
    contraindications: list[Any] = Field(default_factory=list)
    save_score: int | None = None
    save_risk_class: str | None = None
    recommended_config: str | None = None
    candidacy_result: str | None = None
    assessment_details: dict[str, Any] = Field(default_factory=dict)


class EcmoAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_name: str | None
    patient_data: dict[str, Any]
    pe_category: str | None
    indications: list[Any]
    contraindications: list[Any]
    save_score: int | None
    save_risk_class: str | None
    recommended_config: str | None
    candidacy_result: str | None
    assessment_details: dict[str, Any]
    created_at: datetime


# --- Device tokens ------------------------------------------------------------
class DeviceTokenCreate(BaseModel):
    token: str
    platform: Literal["ios", "android", "web"]


# --- Notifications ------------------------------------------------------------
class NotificationSend(BaseModel):
    user_id: uuid.UUID
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)


class NotificationResult(BaseModel):
    success: bool
    sent: int


# --- Feedback -----------------------------------------------------------------
class FeedbackCreate(BaseModel):
    usefulness: Usefulness  # 👍 useful | 👎 not_useful | ⚠️ potential_issue
    clinical_judgment: ClinicalJudgment | None = None  # matched judgment?
    comments: str | None = None
    # Required when usefulness == "potential_issue": describe the concern.
    concern: str | None = None
    # Optional context: what was rated (e.g. "classification" / "ecmo") + its id.
    subject_type: str | None = None
    subject_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _concern_required_for_issue(self) -> "FeedbackCreate":
        if self.usefulness == "potential_issue" and not (self.concern and self.concern.strip()):
            raise ValueError("concern is required when usefulness is 'potential_issue'")
        return self


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    usefulness: str
    clinical_judgment: str | None
    comments: str | None
    concern: str | None
    flagged: bool
    subject_type: str | None
    subject_id: uuid.UUID | None
    created_at: datetime


class FlaggedFeedbackOut(BaseModel):
    """A flagged potential-issue report, with the submitting user + time."""

    id: uuid.UUID
    user_id: uuid.UUID
    user_email: EmailStr
    usefulness: str
    clinical_judgment: str | None
    comments: str | None
    concern: str | None
    subject_type: str | None
    subject_id: uuid.UUID | None
    created_at: datetime


# --- Discussions --------------------------------------------------------------
class DiscussionOut(BaseModel):
    """A discussion topic. Vote tallies are NOT here — fetch them separately via
    ``GET /discussions/{id}/vote`` (see :class:`DiscussionVoteSummary`)."""

    id: uuid.UUID
    assessment_result: str
    complication: str
    created_at: datetime


class PaginatedDiscussions(BaseModel):
    items: list[DiscussionOut]
    total: int
    limit: int
    offset: int


class DiscussionVoteSummary(BaseModel):
    """Just the vote tally for one discussion + the caller's own vote."""

    discussion_id: uuid.UUID
    yes_count: int
    no_count: int
    my_vote: bool | None  # true=yes | false=no | null=not voted


class DiscussionCommentCreate(BaseModel):
    body: str = Field(min_length=1)


class DiscussionCommentOut(BaseModel):
    id: uuid.UUID
    discussion_id: uuid.UUID
    user_id: uuid.UUID
    author_name: str | None  # author's profile display name, if set
    body: str
    created_at: datetime


class PaginatedDiscussionComments(BaseModel):
    items: list[DiscussionCommentOut]
    total: int
    limit: int
    offset: int
