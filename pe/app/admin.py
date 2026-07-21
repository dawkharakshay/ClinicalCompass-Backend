"""SQLAdmin UI for the PE Compass backend, mounted at ``/pe/admin``.

Same shape as the main ClinicalCompass admin: a Django-style CRUD UI gated by an
email allowlist. Allowlisted users log in with their normal account password
(verified against ``users.password_hash``); the session cookie is signed with
``ADMIN_SECRET_KEY``. User-submitted rows (feedback, tokens, assessments) are
review-and-delete only — never created or edited here.
"""

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.config import ADMIN_EMAIL, ADMIN_EMAILS, ADMIN_SECRET_KEY
from app.database import SessionLocal
from app.models import (
    DeviceToken,
    Discussion,
    DiscussionComment,
    DiscussionVote,
    EcmoCandidacyAssessment,
    Feedback,
    PasswordResetToken,
    PatientClassification,
    Profile,
    RefreshToken,
    User,
)
from app.security import hash_password, verify_password

_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def _admin_allowlist() -> set[str]:
    """Emails permitted to log into /pe/admin (ADMIN_EMAILS + ADMIN_EMAIL)."""
    emails = {e.strip().lower() for e in ADMIN_EMAILS.split(",") if e.strip()}
    if ADMIN_EMAIL:
        emails.add(ADMIN_EMAIL.strip().lower())
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
        if not verify_password(password, user.password_hash):
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
        User.id, User.email, User.is_active,
        User.oauth_provider, User.created_at,
    ]
    column_searchable_list = [User.email]
    column_sortable_list = [User.email, User.created_at]
    form_excluded_columns = [User.profile, User.created_at]
    column_labels = {User.password_hash: "Password (type plaintext to set)"}

    async def on_model_change(self, data, model, is_created, request) -> None:
        # Treat the password field as plaintext unless it's already a bcrypt hash.
        pwd = data.get("password_hash")
        if pwd and not pwd.startswith(_BCRYPT_PREFIXES):
            data["password_hash"] = hash_password(pwd)


class ProfileAdmin(ModelView, model=Profile):
    name = "Profile"
    name_plural = "Profiles"
    icon = "fa-solid fa-id-card"
    column_list = [
        Profile.id, Profile.user_id, Profile.display_name,
        Profile.hospital_affiliation, Profile.updated_at,
    ]
    column_searchable_list = [Profile.display_name, Profile.hospital_affiliation]
    column_sortable_list = [Profile.created_at, Profile.updated_at]
    form_excluded_columns = [Profile.user, Profile.created_at, Profile.updated_at]


class FeedbackAdmin(ModelView, model=Feedback):
    name = "Feedback"
    name_plural = "Feedback"
    icon = "fa-solid fa-comment-dots"
    column_list = [
        Feedback.id, Feedback.usefulness, Feedback.clinical_judgment,
        Feedback.flagged, Feedback.subject_type, Feedback.created_at,
    ]
    column_searchable_list = [Feedback.comments, Feedback.concern, Feedback.subject_type]
    column_sortable_list = [Feedback.usefulness, Feedback.flagged, Feedback.created_at]
    column_default_sort = ("created_at", True)  # newest first
    # User-submitted feedback: review and remove only.
    can_create = False
    can_edit = False
    can_delete = True


class PatientClassificationAdmin(ModelView, model=PatientClassification):
    name = "Patient Classification"
    name_plural = "Patient Classifications"
    icon = "fa-solid fa-stethoscope"
    column_list = [
        PatientClassification.id, PatientClassification.user_id,
        PatientClassification.category, PatientClassification.risk_level,
        PatientClassification.created_at,
    ]
    column_sortable_list = [
        PatientClassification.category, PatientClassification.risk_level,
        PatientClassification.created_at,
    ]
    column_default_sort = ("created_at", True)
    can_create = False
    can_edit = False
    can_delete = True


class EcmoCandidacyAssessmentAdmin(ModelView, model=EcmoCandidacyAssessment):
    name = "ECMO Assessment"
    name_plural = "ECMO Assessments"
    icon = "fa-solid fa-heart-pulse"
    column_list = [
        EcmoCandidacyAssessment.id, EcmoCandidacyAssessment.user_id,
        EcmoCandidacyAssessment.pe_category, EcmoCandidacyAssessment.candidacy_result,
        EcmoCandidacyAssessment.save_score, EcmoCandidacyAssessment.created_at,
    ]
    column_sortable_list = [
        EcmoCandidacyAssessment.pe_category, EcmoCandidacyAssessment.save_score,
        EcmoCandidacyAssessment.created_at,
    ]
    column_default_sort = ("created_at", True)
    can_create = False
    can_edit = False
    can_delete = True


class DeviceTokenAdmin(ModelView, model=DeviceToken):
    name = "Device Token"
    name_plural = "Device Tokens"
    icon = "fa-solid fa-mobile-screen"
    column_list = [
        DeviceToken.id, DeviceToken.user_id, DeviceToken.platform,
        DeviceToken.created_at,
    ]
    column_sortable_list = [DeviceToken.platform, DeviceToken.created_at]
    can_create = False
    can_edit = False
    can_delete = True  # allow removing stale tokens


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    name = "Refresh Token"
    name_plural = "Refresh Tokens"
    icon = "fa-solid fa-key"
    column_list = [
        RefreshToken.id, RefreshToken.user_id, RefreshToken.revoked,
        RefreshToken.expires_at, RefreshToken.created_at,
    ]
    column_sortable_list = [RefreshToken.revoked, RefreshToken.expires_at]
    column_default_sort = ("created_at", True)
    can_create = False
    can_edit = False
    can_delete = True  # allow revoking sessions


class PasswordResetTokenAdmin(ModelView, model=PasswordResetToken):
    name = "Password Reset Token"
    name_plural = "Password Reset Tokens"
    icon = "fa-solid fa-unlock-keyhole"
    column_list = [
        PasswordResetToken.id, PasswordResetToken.user_id,
        PasswordResetToken.attempts, PasswordResetToken.expires_at,
        PasswordResetToken.created_at,
    ]
    column_sortable_list = [PasswordResetToken.attempts, PasswordResetToken.expires_at]
    column_default_sort = ("created_at", True)
    can_create = False
    can_edit = False
    can_delete = True


class DiscussionAdmin(ModelView, model=Discussion):
    name = "Discussion"
    name_plural = "Discussions"
    icon = "fa-solid fa-comments"
    column_list = [
        Discussion.id, Discussion.assessment_result, Discussion.complication,
        Discussion.created_at,
    ]
    column_searchable_list = [Discussion.assessment_result, Discussion.complication]
    column_sortable_list = [Discussion.created_at]
    column_default_sort = ("created_at", True)
    form_excluded_columns = [Discussion.votes, Discussion.created_at, Discussion.updated_at]
    # Admins author the discussion topics users vote on.
    can_create = True
    can_edit = True
    can_delete = True


class DiscussionVoteAdmin(ModelView, model=DiscussionVote):
    name = "Discussion Vote"
    name_plural = "Discussion Votes"
    icon = "fa-solid fa-check-to-slot"
    column_list = [
        DiscussionVote.id, DiscussionVote.discussion_id, DiscussionVote.user_id,
        DiscussionVote.vote, DiscussionVote.created_at,
    ]
    column_labels = {DiscussionVote.vote: "Vote (yes=✓)"}
    column_sortable_list = [DiscussionVote.vote, DiscussionVote.created_at]
    column_default_sort = ("created_at", True)
    # User-submitted votes: review and remove only.
    can_create = False
    can_edit = False
    can_delete = True


class DiscussionCommentAdmin(ModelView, model=DiscussionComment):
    name = "Discussion Comment"
    name_plural = "Discussion Comments"
    icon = "fa-solid fa-comment-medical"
    column_list = [
        DiscussionComment.id, DiscussionComment.discussion_id,
        DiscussionComment.user_id, DiscussionComment.created_at,
    ]
    column_searchable_list = [DiscussionComment.body]
    column_sortable_list = [DiscussionComment.created_at]
    column_default_sort = ("created_at", True)
    # User-submitted content: review and remove only.
    can_create = False
    can_edit = False
    can_delete = True


def setup_admin(app, engine) -> Admin:
    """Mount the SQLAdmin UI at ``/admin`` (public ``/pe/admin`` behind nginx)."""
    admin = Admin(
        app,
        engine,
        authentication_backend=AdminAuth(secret_key=ADMIN_SECRET_KEY),
        title="PE Compass Admin",
    )
    for view in (
        UserAdmin, ProfileAdmin, FeedbackAdmin,
        DiscussionAdmin, DiscussionVoteAdmin, DiscussionCommentAdmin,
        PatientClassificationAdmin, EcmoCandidacyAssessmentAdmin,
        DeviceTokenAdmin, RefreshTokenAdmin, PasswordResetTokenAdmin,
    ):
        admin.add_view(view)
    return admin
