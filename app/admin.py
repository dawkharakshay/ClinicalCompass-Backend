"""Django-style admin UI (SQLAdmin), gated by an ADMIN_EMAILS allowlist."""

import os

from markupsafe import Markup
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.database import SessionLocal
from app.models import (
    AppealLetterRating,
    Collaboration,
    DenialCategory,
    DenialTemplate,
    Feedback,
    FormSubmission,
    Module,
    Speciality,
    Token,
    User,
)
from app.security import hash_password, verify_password


def _image_thumb(model, attribute) -> Markup | str:
    """Render an uploaded image as a thumbnail in the admin (via /uploads)."""
    url = getattr(model, "image_url", None)
    if not url:
        return ""
    return Markup(f'<a href="{url}" target="_blank"><img src="{url}" height="48"></a>')

ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "dev-only-change-me")
_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def _admin_allowlist() -> set[str]:
    """Emails permitted to log into /admin (ADMIN_EMAILS + ADMIN_EMAIL)."""
    emails = {
        e.strip().lower()
        for e in os.getenv("ADMIN_EMAILS", "").split(",")
        if e.strip()
    }
    bootstrap = os.getenv("ADMIN_EMAIL")
    if bootstrap:
        emails.add(bootstrap.strip().lower())
    return emails


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = (form.get("username") or "").strip().lower()
        password = form.get("password") or ""
        if email not in _admin_allowlist():
            return False
        db = SessionLocal()
        try:
            user = db.scalar(select(User).where(User.email == email))
        finally:
            db.close()
        if user is None or not user.is_active:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        request.session["admin_email"] = email
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        email = request.session.get("admin_email")
        return bool(email and email in _admin_allowlist())


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_list = [
        User.id, User.username, User.full_name, User.email,
        User.role, User.medical_speciality, User.current_institution,
        User.is_active, User.created_at,
    ]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.created_at]
    form_excluded_columns = [User.tokens, User.created_at]
    column_labels = {User.hashed_password: "Password (type plaintext to set)"}

    async def on_model_change(self, data, model, is_created, request) -> None:
        # Treat the password field as plaintext unless it's already a bcrypt hash.
        pwd = data.get("hashed_password")
        if pwd and not pwd.startswith(_BCRYPT_PREFIXES):
            data["hashed_password"] = hash_password(pwd)


class SpecialityAdmin(ModelView, model=Speciality):
    name = "Speciality"
    name_plural = "Specialities"
    icon = "fa-solid fa-layer-group"
    column_list = [Speciality.id, Speciality.title, Speciality.image, Speciality.created_at]
    column_searchable_list = [Speciality.title]
    column_formatters = {Speciality.image: _image_thumb}
    column_formatters_detail = {Speciality.image: _image_thumb}
    form_excluded_columns = [Speciality.modules, Speciality.created_at, Speciality.updated_at]


class ModuleAdmin(ModelView, model=Module):
    name = "Module"
    name_plural = "Modules"
    icon = "fa-solid fa-cubes"
    column_list = [Module.id, Module.title, Module.speciality, Module.image, Module.created_at]
    column_searchable_list = [Module.title]
    column_formatters = {Module.image: _image_thumb}
    column_formatters_detail = {Module.image: _image_thumb}
    form_excluded_columns = [Module.created_at, Module.updated_at]


class TokenAdmin(ModelView, model=Token):
    name = "Token"
    name_plural = "Tokens"
    icon = "fa-solid fa-key"
    column_list = [Token.id, Token.user, Token.created_at, Token.expires_at]
    can_create = False
    can_edit = False
    can_delete = True  # allow revoking tokens


class FormSubmissionAdmin(ModelView, model=FormSubmission):
    name = "Form Submission"
    name_plural = "Form Submissions"
    icon = "fa-solid fa-file-lines"
    column_list = [
        FormSubmission.id, FormSubmission.module, FormSubmission.user,
        FormSubmission.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = True


class DenialCategoryAdmin(ModelView, model=DenialCategory):
    name = "Denial Category"
    name_plural = "Denial Categories"
    icon = "fa-solid fa-tags"
    column_list = [DenialCategory.value, DenialCategory.label, DenialCategory.position]
    column_sortable_list = [DenialCategory.position, DenialCategory.value]


class DenialTemplateAdmin(ModelView, model=DenialTemplate):
    name = "Denial Template"
    name_plural = "Denial Templates"
    icon = "fa-solid fa-file-shield"
    column_list = [
        DenialTemplate.id, DenialTemplate.category,
        DenialTemplate.title, DenialTemplate.denial_reason,
    ]
    column_searchable_list = [DenialTemplate.title, DenialTemplate.denial_reason]
    column_sortable_list = [DenialTemplate.id, DenialTemplate.category]


class CollaborationAdmin(ModelView, model=Collaboration):
    name = "Collaboration"
    name_plural = "Collaborations"
    icon = "fa-solid fa-handshake"
    column_list = [
        Collaboration.id, Collaboration.name, Collaboration.email,
        Collaboration.speciality, Collaboration.created_at,
    ]
    column_searchable_list = [
        Collaboration.name, Collaboration.email, Collaboration.speciality,
    ]
    column_sortable_list = [Collaboration.id, Collaboration.created_at]
    column_default_sort = ("id", True)  # newest first
    # User-submitted: review and remove only, never create/edit.
    can_create = False
    can_edit = False
    can_delete = True


class AppealLetterRatingAdmin(ModelView, model=AppealLetterRating):
    name = "Appeal Letter Rating"
    name_plural = "Appeal Letter Ratings"
    icon = "fa-solid fa-star"
    column_list = [
        AppealLetterRating.id, AppealLetterRating.letter_quality,
        AppealLetterRating.effectiveness, AppealLetterRating.appeal_outcome,
        AppealLetterRating.created_at,
    ]
    column_searchable_list = [AppealLetterRating.appeal_outcome, AppealLetterRating.comments]
    column_sortable_list = [
        AppealLetterRating.id, AppealLetterRating.letter_quality,
        AppealLetterRating.effectiveness, AppealLetterRating.created_at,
    ]
    column_default_sort = ("id", True)  # newest first
    # User-submitted feedback: review and remove only.
    can_create = False
    can_edit = False
    can_delete = True


class FeedbackAdmin(ModelView, model=Feedback):
    name = "Feedback"
    name_plural = "Feedback"
    icon = "fa-solid fa-comment-dots"
    column_list = [
        Feedback.id, Feedback.category, Feedback.subject, Feedback.created_at,
    ]
    column_searchable_list = [Feedback.category, Feedback.subject, Feedback.message]
    column_sortable_list = [Feedback.id, Feedback.category, Feedback.created_at]
    column_default_sort = ("id", True)  # newest first
    # User-submitted feedback: review and remove only.
    can_create = False
    can_edit = False
    can_delete = True


def setup_admin(app, engine) -> Admin:
    admin = Admin(
        app,
        engine,
        authentication_backend=AdminAuth(secret_key=ADMIN_SECRET_KEY),
        title="ClinicalCompass Admin",
    )
    for view in (
        UserAdmin, SpecialityAdmin, ModuleAdmin, TokenAdmin, FormSubmissionAdmin,
        DenialCategoryAdmin, DenialTemplateAdmin, CollaborationAdmin,
        AppealLetterRatingAdmin, FeedbackAdmin,
    ):
        admin.add_view(view)
    return admin
