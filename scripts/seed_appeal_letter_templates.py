"""Load data-driven appeal-letter templates (forms/appeal_letter_templates/*.json)
into Module.appeal_letter_template.

Each file is {"title": <module title>, "appeal_letter_template": {<recipe>}}.
Matches the module by title and sets its `appeal_letter_template` column. See
app/appeal_letter.py for the recipe shape and renderer. Idempotent; no-op for
titles not present in the DB (reported).

    uv run python scripts/seed_appeal_letter_templates.py
    # or against local SQLite:
    DATABASE_URL=sqlite:///./clinicalcompass.db uv run python scripts/seed_appeal_letter_templates.py
"""

import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Module

GEN_DIR = Path(__file__).resolve().parent.parent / "forms" / "appeal_letter_templates"


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
            template = payload.get("appeal_letter_template")
            if not title or not isinstance(template, dict):
                print(f"  ! {f.name}: missing title/appeal_letter_template — skipped")
                skipped += 1
                continue

            mod = db.scalar(select(Module).where(Module.title == title))
            if mod is None:
                unmatched += 1
                missing.append(title)
                continue

            if mod.appeal_letter_template == template:  # JSON round-trips to a dict; stay idempotent
                continue
            mod.appeal_letter_template = template
            updated += 1
        db.commit()
        print(
            f"[seed_appeal_letter_templates] files: {len(files)} | updated: {updated} | "
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
