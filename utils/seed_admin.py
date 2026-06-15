"""Create or update the bootstrap admin user from env vars.

    ADMIN_EMAIL=... ADMIN_PASSWORD=... uv run python -m utils.seed_admin

The email must also be in ADMIN_EMAILS (or equal ADMIN_EMAIL) to log into
/admin — see app/admin.py.
"""

import os

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password
from app.usernames import find_available_username, slugify_full_name


def seed() -> None:
    email = (os.getenv("ADMIN_EMAIL") or "").strip()
    password = os.getenv("ADMIN_PASSWORD") or ""
    if not email or not password:
        raise SystemExit("ADMIN_EMAIL and ADMIN_PASSWORD must be set")

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            base = slugify_full_name(email.split("@")[0]) or "admin"
            username, _ = find_available_username(db, base)
            user = User(
                username=username,
                full_name="Administrator",
                email=email.lower(),
                role="licensed_professional",
                hashed_password=hash_password(password),
                is_active=True,
            )
            db.add(user)
            print(f"created admin user {email} (username '{username}')")
        else:
            user.hashed_password = hash_password(password)
            user.is_active = True
            print(f"updated admin user {email}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
