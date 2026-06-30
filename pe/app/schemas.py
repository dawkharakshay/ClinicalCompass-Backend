"""Pydantic request/response schemas for the PE Compass backend."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)


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
