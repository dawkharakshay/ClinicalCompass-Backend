"""Idempotently rename legacy module titles to their current canonical titles.

Modules are matched throughout the seed pipeline by **title** (see
``seed_modules.py`` and ``seed_forms.py``). Renaming a module in the source
seed alone would therefore create a *duplicate* on any existing database — the
old-titled row survives and a new row is inserted. This seed closes that gap:
it renames the existing row in place, so it must run **before** ``seed_modules``
and ``seed_forms`` (which then match the new title and update, rather than
insert).

Idempotent: a rename is applied only when the old title still exists and the new
title does not. Once renamed (or on a fresh DB seeded directly with the new
title) it is a no-op. If both titles somehow exist, the row is left untouched
and a warning is printed for manual reconciliation.

Usage (from the API container / with PYTHONPATH=/app):
    python scripts/seed_module_renames.py
"""

from __future__ import annotations

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Module

# Each entry renames one module. ``new_description`` is applied only when set.
RENAMES: list[dict] = [
    {
        "old_title": "Women's Health Clinical Compass",
        "new_title": "Pelvic Venous Disease Clinical Compass",
        "new_description": "Pelvic Venous Disorder (PeVD) decision support with SVP classification",
    },
]


def run() -> None:
    db = SessionLocal()
    renamed = skipped = 0
    try:
        for entry in RENAMES:
            old_title = entry["old_title"]
            new_title = entry["new_title"]
            old_mod = db.scalar(select(Module).where(Module.title == old_title))
            new_mod = db.scalar(select(Module).where(Module.title == new_title))

            if old_mod and not new_mod:
                old_mod.title = new_title
                if entry.get("new_description"):
                    old_mod.description = entry["new_description"]
                renamed += 1
                print(f"    + renamed: {old_title!r} -> {new_title!r}")
            elif old_mod and new_mod:
                skipped += 1
                print(
                    f"  ! both {old_title!r} and {new_title!r} exist (id {old_mod.id} & "
                    f"{new_mod.id}) — left untouched; reconcile the duplicate manually"
                )
            else:
                skipped += 1  # already renamed, or neither present — no-op
        db.commit()
        print(f"[seed_module_renames] renamed: {renamed} | unchanged: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
