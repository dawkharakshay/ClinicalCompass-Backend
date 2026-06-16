"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import UserRole

USERNAME_PATTERN = r"^[a-zA-Z0-9._-]+$"


class UserCreate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=USERNAME_PATTERN,
        description="Optional. If omitted, one is generated from the full name.",
        examples=["jane.smith"],
    )
    full_name: str = Field(..., min_length=1, max_length=255, examples=["Dr. Jane Smith"])
    email: EmailStr = Field(..., examples=["drsmith@example.com"])
    password: str = Field(..., min_length=8, examples=["s3cret-pass"])
    role: UserRole = Field(..., examples=[UserRole.licensed_professional])


class UserOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "drsmith",
                "full_name": "Dr. Jane Smith",
                "role": "licensed_professional",
                "email": "drsmith@example.com",
                "avatar_url": "/uploads/avatars/user_1_a1b2c3d4.png",
                "medical_speciality": "Radiation Oncology",
                "current_institution": "Mayo Clinic",
                "is_active": True,
                "created_at": "2026-06-01T11:32:04.715581Z",
            }
        },
    )

    id: int
    username: str
    full_name: str | None
    role: UserRole
    email: EmailStr | None
    avatar_url: str | None = Field(
        default=None,
        description="Public URL of the user's profile photo, or null if none is set.",
        examples=["/uploads/avatars/user_1_a1b2c3d4.png"],
    )
    medical_speciality: str | None = Field(
        default=None,
        description="The user's medical speciality (free text), or null if not set.",
        examples=["Radiation Oncology"],
    )
    current_institution: str | None = Field(
        default=None,
        description="The user's current institution (free text), or null if not set.",
        examples=["Mayo Clinic"],
    )
    is_active: bool
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Update the authenticated user's free-text profile details.

    Both fields are optional; only the fields present in the request are
    changed. Send an explicit ``null`` to clear a field.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "medical_speciality": "Radiation Oncology",
                "current_institution": "Mayo Clinic",
            }
        }
    )

    medical_speciality: str | None = Field(
        default=None,
        max_length=255,
        description="The user's medical speciality (free text).",
        examples=["Radiation Oncology"],
    )
    current_institution: str | None = Field(
        default=None,
        max_length=255,
        description="The user's current institution (free text).",
        examples=["Mayo Clinic"],
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["drsmith@example.com"])
    password: str = Field(..., examples=["s3cret-pass"])


class TokenOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "MDJ3cy0P_g5Rk8VD_fnkMAc_VSG2kU1MJRY34Ic52oU",
                "token_type": "bearer",
                "expires_at": "2026-06-02T11:32:05.227328Z",
            }
        }
    )

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class GoogleOAuthRequest(BaseModel):
    id_token: str = Field(
        ...,
        description="The Google ID token (JWT) obtained from the native "
        "Google Sign-In SDK. The user's identity (subject, email, name) is read "
        "from inside the verified token, not from the request body.",
        examples=["eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."],
    )
    role: UserRole | None = Field(
        default=None,
        description="Required when this is a first sign-in (a new account is "
        "created). Ignored for users who already exist.",
        examples=[UserRole.licensed_professional],
    )


class AppleOAuthRequest(BaseModel):
    identity_token: str = Field(
        ...,
        description="The Apple identity token (JWT) from Sign in with Apple. "
        "The subject and email are read from inside the verified token.",
        examples=["eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."],
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="The user's name. Apple returns this only on the FIRST "
        "authorization and never inside the token, so the client must forward "
        "it then or it is lost. Ignored for users who already exist.",
        examples=["Jane Smith"],
    )
    role: UserRole | None = Field(
        default=None,
        description="Required when this is a first sign-in (a new account is "
        "created). Ignored for users who already exist.",
        examples=[UserRole.licensed_professional],
    )


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., examples=["drsmith@example.com"])


class ForgotPasswordResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "If the email is registered, a reset code has been sent.",
                "expires_at": "2026-06-08T11:42:05.227328Z",
            }
        }
    )

    message: str = Field(
        ...,
        description="Generic confirmation, the same regardless of whether the "
        "email exists, to avoid account enumeration.",
    )
    expires_at: datetime | None = Field(
        default=None, description="When the code expires (null when no code was issued)."
    )


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., examples=["drsmith@example.com"])
    otp: str = Field(
        ...,
        min_length=4,
        max_length=10,
        description="The one-time code sent to the user's email by /auth/forgot-password.",
        examples=["482915"],
    )
    new_password: str = Field(..., min_length=8, examples=["n3w-s3cret-pass"])


class UsernameAvailableResponse(BaseModel):
    username: str = Field(..., examples=["jane.smith"])
    available: bool = Field(..., description="Whether the username is free to use", examples=[True])


class UsernameGenerateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, examples=["Dr. Jane Smith"])


class UsernameGenerateResponse(BaseModel):
    full_name: str = Field(..., examples=["Dr. Jane Smith"])
    username: str = Field(..., description="A free username derived from the full name", examples=["jane.smith"])
    alternatives: list[str] = Field(default_factory=list, examples=[["jane.smith1", "jane.smith2"]])


class ErrorResponse(BaseModel):
    """Standard FastAPI error envelope."""

    detail: str = Field(..., examples=["Invalid username or password"])


# --- Module form (stored verbatim: form -> steps -> fields) -----------------

_FORM_EXAMPLE = {
    "steps": [
        {
            "id": "staging",
            "shortLabel": "Staging",
            "title": "Tumor Staging (MRI-based)",
            "fields": [
                {
                    "id": "t-stage",
                    "name": "tStage",
                    "label": "T Stage",
                    "type": "select",
                    "required": True,
                    "defaultValue": "T3",
                    "options": [
                        {"label": "T1 — Submucosa", "value": "T1"},
                        {"label": "T3 — Through muscularis propria", "value": "T3"},
                    ],
                },
                {
                    "id": "tumor-size",
                    "name": "tumorSize",
                    "label": "Tumor Size",
                    "type": "slider",
                    "defaultValue": 0,
                    "min": 0,
                    "max": 15,
                    "step": 0.5,
                    "unit": "cm",
                },
            ],
        }
    ]
}


class ModuleForm(BaseModel):
    """A module's form, stored and returned verbatim.

    Shape: {"steps": [{"id", "shortLabel", "title", "fields": [field, ...]}]}.
    Each field is free-form (id, name, label, type, required, defaultValue,
    options, optionLayout, min, max, step, unit, placeholder, keyboardType,
    multiline, ...), so the frontend owns the exact field schema.
    """

    model_config = ConfigDict(extra="allow", json_schema_extra={"example": _FORM_EXAMPLE})

    steps: list[dict[str, Any]] = Field(default_factory=list)


# --- Specialities & Modules -------------------------------------------------


class ModuleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Rectal Cancer"])
    description: str | None = Field(default=None, examples=["Staging and treatment pathways"])


class ModuleCreate(ModuleBase):
    appeal_letter: str | None = Field(
        default=None, description="Medical-necessity appeal letter template for this module."
    )


class ModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    appeal_letter: str | None = None


class ModuleOut(ModuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    speciality_id: int
    image_url: str | None = Field(default=None, examples=["/uploads/images/abc123.png"])


class ModuleDetail(ModuleOut):
    """A single module including its form."""

    form: ModuleForm = Field(default_factory=ModuleForm)
    appeal_letter: str | None = None
    appeal_letter_template: dict[str, Any] | None = Field(
        default=None,
        description="Data-driven recipe for personalizing the appeal letter from "
        "a submission's answers (defaults, derived values, conditional sections, "
        "and a {{placeholder}} template).",
    )
    auth_guide: dict[str, Any] | None = Field(
        default=None,
        description="Prior-authorization guide: CPT codes, ICD-10 codes, "
        "payer-specific coverage/documentation rules, plus a verbatim `raw` block.",
    )
    recommendation: dict[str, Any] | None = Field(
        default=None,
        description="Reference copy of the module's result-generation logic "
        "(form data -> recommendation): source files, a `hasLogic` flag, and a "
        "verbatim `raw.markdown` block. Documentation only — not executed.",
    )


class RecommendationOut(BaseModel):
    """A module's result-generation logic, stored and returned verbatim.

    Reference documentation (not executed): ``sourceFiles`` (the legacy *Logic.ts
    paths), ``hasLogic`` (false for coming-soon stubs), and a verbatim
    ``raw.markdown`` block. Extra keys are allowed so the shape can evolve without
    rejecting stored content at the API boundary.
    """

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "sourceFiles": ["client/src/lib/acsLogic.ts"],
                "hasLogic": True,
                "raw": {"markdown": "## 3. Result-Generation Logic ..."},
            }
        },
    )


class AuthGuideOut(BaseModel):
    """A module's authorization guide, stored and returned verbatim.

    Hybrid free-form shape: structured ``cptCodes``/``icd10Codes``/``payers``/
    ``customSections`` for querying, plus a verbatim ``raw`` block (markdown +
    tables) that guarantees no source content is lost. Extra keys are allowed so
    heterogeneous guides are never rejected at the API boundary.
    """

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "sourceFile": "RenalCryoablationAuthGuide.tsx",
                "title": "Renal Cryoablation — Authorization Guide",
                "cptCodes": [{"code": "50593", "description": "Ablation, renal tumor(s)..."}],
                "icd10Codes": [{"code": "C64.1", "description": "Malignant neoplasm of right kidney"}],
                "payers": [{"key": "cms", "label": "CMS / Medicare (LCD L35041)", "sections": []}],
                "raw": {"markdown": "...", "tables": []},
            }
        },
    )


class RecommendationResultOut(BaseModel):
    """A computed recommendation for a submission.

    ``result`` is the module's native, free-form engine output (the shape varies
    per module — risk levels, tiers, scores, recommendation lists, etc.), ported
    1:1 from the legacy logic. Extra keys are allowed so no engine's output is
    rejected at the API boundary.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "submission_id": 1,
                "module_id": 1,
                "logic_key": "tha",
                "result": {
                    "recommendation": "THA Recommended",
                    "cor": "I",
                    "loe": "A",
                    "urgency": "Appropriate",
                    "rationale": ["Severe hip OA (KL ≥3) with significant pain ..."],
                    "contraindications": [],
                    "optimizationSteps": [],
                },
            }
        }
    )

    submission_id: int
    module_id: int
    logic_key: str = Field(..., description="The module's form logicKey that selected the engine.")
    result: dict[str, Any] = Field(..., description="The engine's native output (free-form).")


class AppealLetterOut(BaseModel):
    """A rendered, personalized appeal letter for a submission."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "submission_id": 1,
                "module_id": 1,
                "letter": "Dear UnitedHealthcare,\n\nRe: Jane Doe ...",
            }
        }
    )

    submission_id: int
    module_id: int
    letter: str = Field(..., description="The personalized appeal letter text.")


class ModulePage(BaseModel):
    """A page of modules with next/previous page links."""

    items: list[ModuleOut]
    next: str | None = Field(
        default=None,
        description="URL of the next page, or null on the last page",
        examples=["http://localhost/modules?limit=20&offset=20"],
    )
    previous: str | None = Field(
        default=None,
        description="URL of the previous page, or null on the first page",
        examples=[None],
    )


class FormSubmissionCreate(BaseModel):
    """A user's answers for a module's form."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "module_id": 1,
                "data": {"tStage": "T3", "tumorSize": 4.5},
            }
        }
    )

    module_id: int = Field(..., ge=1, description="The module whose form is being submitted.")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="The submitted answers keyed by field name. Stored verbatim.",
    )


class FormSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    user_id: int
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class FormSubmissionPage(BaseModel):
    """A page of form submissions with next/previous page links."""

    items: list[FormSubmissionOut]
    next: str | None = Field(
        default=None,
        description="URL of the next page, or null on the last page",
        examples=["http://localhost/submissions?limit=20&offset=20"],
    )
    previous: str | None = Field(
        default=None,
        description="URL of the previous page, or null on the first page",
        examples=[None],
    )


class CountOut(BaseModel):
    """A labeled count of a resource."""

    resource: str = Field(..., examples=["specialities"])
    count: int = Field(..., examples=[42])


# --- Denial Template Library ------------------------------------------------


class DenialTemplateOut(BaseModel):
    """A pre-written appeal paragraph rebutting a specific denial reason."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "mn-001",
                "category": "medical-necessity",
                "title": "General Medical Necessity — Chronic Pain with Functional Impairment",
                "denial_reason": "Procedure deemed not medically necessary",
                "applicable_to": ["ESI", "Facet Joint", "RFA", "SCS", "PAD", "General"],
                "text": "This procedure is medically necessary for the treatment of [PATIENT NAME]'s ...",
                "references": ["ASIPP Guidelines 2013", "CMS LCD L35937"],
            }
        },
    )

    id: str
    category: str
    title: str
    denial_reason: str | None = None
    applicable_to: list[str] = Field(default_factory=list)
    text: str
    references: list[str] = Field(default_factory=list)


class DenialCategoryOut(BaseModel):
    """A denial-reason category, with a count of the templates it contains."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": "medical-necessity",
                "label": "Medical Necessity",
                "color": "bg-red-100 text-red-800",
                "count": 4,
            }
        }
    )

    value: str
    label: str
    color: str | None = None
    count: int = Field(..., description="Number of templates in this category (after any procedure filter).")


class DenialTemplatePage(BaseModel):
    """A page of denial templates with next/previous page links."""

    items: list[DenialTemplateOut]
    next: str | None = Field(
        default=None,
        description="URL of the next page, or null on the last page",
        examples=["http://localhost/denial-templates?limit=20&offset=20"],
    )
    previous: str | None = Field(
        default=None,
        description="URL of the previous page, or null on the first page",
        examples=[None],
    )


class SpecialityBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Oncology"])
    description: str | None = Field(default=None, examples=["Cancer care pathways"])


class SpecialityCreate(SpecialityBase):
    pass


class SpecialityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class SpecialityOut(SpecialityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str | None = Field(default=None, examples=["/uploads/images/abc123.png"])


class SpecialityWithModules(SpecialityOut):
    modules: list[ModuleOut] = Field(default_factory=list)


class SpecialityPage(BaseModel):
    """A page of specialities with next/previous page links."""

    items: list[SpecialityOut]
    next: str | None = Field(
        default=None,
        description="URL of the next page, or null on the last page",
        examples=["http://localhost/specialities?limit=20&offset=20"],
    )
    previous: str | None = Field(
        default=None,
        description="URL of the previous page, or null on the first page",
        examples=[None],
    )


class CollaborationCreate(BaseModel):
    """A collaboration / contact request from the public site."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Dr. Jane Smith"])
    email: EmailStr = Field(..., examples=["jane@example.com"])
    speciality: str | None = Field(
        default=None, max_length=255, examples=["Radiation Oncology"]
    )
    message: str = Field(..., min_length=1, max_length=5000,
                         examples=["I'd like to collaborate on the rectal cancer module."])


class CollaborationOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Dr. Jane Smith",
                "email": "jane@example.com",
                "speciality": "Radiation Oncology",
                "message": "I'd like to collaborate on the rectal cancer module.",
                "created_at": "2026-06-16T10:15:00Z",
            }
        },
    )

    id: int
    name: str
    email: EmailStr
    speciality: str | None
    message: str
    created_at: datetime


class AppealLetterRatingCreate(BaseModel):
    """A user's rating/feedback for a generated appeal letter."""

    letter_quality: int = Field(..., ge=1, le=5, description="Letter quality (1-5)", examples=[4])
    effectiveness: int = Field(..., ge=1, le=5, description="Effectiveness for the appeal (1-5)", examples=[5])
    appeal_outcome: str | None = Field(
        default=None, max_length=255,
        description="Optional outcome of the appeal (e.g. approved, denied, pending).",
        examples=["approved"],
    )
    comments: str | None = Field(default=None, max_length=5000, examples=["Clear and well structured."])


class AppealLetterRatingOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "letter_quality": 4,
                "effectiveness": 5,
                "appeal_outcome": "approved",
                "comments": "Clear and well structured.",
                "created_at": "2026-06-16T10:20:00Z",
            }
        },
    )

    id: int
    letter_quality: int
    effectiveness: int
    appeal_outcome: str | None
    comments: str | None
    created_at: datetime


class FeedbackCreate(BaseModel):
    """General user feedback submission."""

    category: str = Field(..., min_length=1, max_length=255, examples=["Bug report"])
    subject: str = Field(..., min_length=1, max_length=255, examples=["Score bar not showing"])
    message: str = Field(..., min_length=1, max_length=5000,
                         examples=["The organ score bar doesn't render on the rectal module."])


class FeedbackOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "category": "Bug report",
                "subject": "Score bar not showing",
                "message": "The organ score bar doesn't render on the rectal module.",
                "created_at": "2026-06-16T10:25:00Z",
            }
        },
    )

    id: int
    category: str
    subject: str
    message: str
    created_at: datetime
