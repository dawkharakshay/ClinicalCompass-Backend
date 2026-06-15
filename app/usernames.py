"""Derive a clean, available username from a person's full name."""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

# Honorifics / titles to strip before building the username.
_TITLES = {"dr", "mr", "mrs", "ms", "miss", "prof", "professor", "sir", "dame"}


def slugify_full_name(full_name: str) -> str:
    """Turn a full name into a base username, e.g. 'Dr. Jane Smith' -> 'jane.smith'."""
    # Normalize accents (José -> Jose) and lowercase.
    normalized = unicodedata.normalize("NFKD", full_name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()

    # Keep only letters/numbers/spaces, then split into tokens.
    cleaned = re.sub(r"[^a-z0-9\s]", " ", ascii_only)
    tokens = [t for t in cleaned.split() if t and t not in _TITLES]

    if not tokens:
        return "user"
    return ".".join(tokens)


def find_available_username(db: Session, base: str, limit: int = 5) -> tuple[str, list[str]]:
    """Return the first free username for `base` plus up to `limit` alternatives.

    If `base` itself is free it is returned as the chosen username. Otherwise a
    numeric suffix is appended (base1, base2, ...). Alternatives are always
    suffixed variants that are also currently free.
    """
    taken = set(
        db.scalars(
            select(User.username).where(User.username.like(f"{base}%"))
        ).all()
    )

    chosen: str | None = None
    alternatives: list[str] = []

    # base, base1, base2, ... — collect the first free one and a few spares.
    candidate = base
    suffix = 0
    while len(alternatives) < limit:
        if candidate not in taken:
            if chosen is None:
                chosen = candidate
            else:
                alternatives.append(candidate)
        suffix += 1
        candidate = f"{base}{suffix}"

    return chosen, alternatives  # type: ignore[return-value]
