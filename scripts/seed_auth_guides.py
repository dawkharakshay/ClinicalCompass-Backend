"""Load authorization-guide data (forms/auth_guides/*.json) into Module.auth_guide.

Each file is {"title": <module title>, "auth_guide": {<guide content>}}. Matches
the module by title and sets its `auth_guide` column. Idempotent; no-op for
titles not present in the DB (reported). Files whose name starts with "_"
(e.g. _map.json, _authguide_gaps.json, _orphan_*.json) are skipped.

    uv run python scripts/seed_auth_guides.py
    # or against local SQLite:
    DATABASE_URL=sqlite:///./clinicalcompass.db uv run python scripts/seed_auth_guides.py
"""

import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Module

GEN_DIR = Path(__file__).resolve().parent.parent / "forms" / "auth_guides"


def run() -> None:
    files = sorted(GEN_DIR.glob("*.json"))
    db = SessionLocal()
    updated = skipped = unmatched = 0
    missing: list[str] = []
    try:
        for f in files:
            if f.name.startswith("_"):
                continue
            try:
                payload = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"  ! {f.name}: invalid JSON ({exc}) — skipped")
                skipped += 1
                continue

            title = payload.get("title")
            guide = payload.get("auth_guide")
            if not title or not isinstance(guide, dict):
                print(f"  ! {f.name}: missing title/auth_guide — skipped")
                skipped += 1
                continue

            mod = db.scalar(select(Module).where(Module.title == title))
            if mod is None:
                unmatched += 1
                missing.append(title)
                continue

            if mod.auth_guide == guide:  # JSON round-trips to a dict; stay idempotent
                continue
            mod.auth_guide = guide
            updated += 1
        db.commit()
        print(
            f"[seed_auth_guides] files: {len(files)} | updated: {updated} | "
            f"unmatched: {unmatched} | skipped(bad): {skipped}"
        )
        if missing:
            print("  unmatched titles:")
            for t in missing:
                print(f"    - {t}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
