"""Ensure every module's form captures patient age and weight.

The General Update mandates that every module include fields for patient age
and patient weight. This script injects two standardized numeric fields:

    age    -> number, years   (name: "age")
    weight -> number, kg       (name: "weight")

These mirror the canonical shape already used by modules like ``acs`` so we
introduce no third convention. Both go into a "Patient Information" step placed
first in the wizard.

The script is **idempotent** and **additive**: it never edits or removes an
existing field. A module is left untouched for a given measure if it already
captures it. Duplicate detection is camelCase-token based so genuine captures
(``age``, ``ageYears``, ``patientAge``, ``weight``, ``weightKg``,
``weightForLengthPercentile``) are recognized while false positives
(``bclcStage``, ``lineage``, ``hemorrhage``, ``storageYears``) and weight-loss
*symptom* flags (``hasWeightLoss``, ``triedWeightLoss``) are not — the latter
do not record a weight, so those modules still get a weight field.

Usage:
    # Patch the live DB (all modules). Run from the API container / with PYTHONPATH=/app.
    python scripts/seed_demographics.py

    # Rewrite only the source form files under forms/generated/*.json (no DB).
    python scripts/seed_demographics.py --generated

    # Do both (source files + DB).
    python scripts/seed_demographics.py --all
"""

import json
import re
import sys
from pathlib import Path

GEN_DIR = Path(__file__).resolve().parent.parent / "forms" / "generated"

AGE_FIELD = {
    "id": "age",
    "name": "age",
    "label": "Patient Age (years)",
    "type": "number",
    "required": True,
    "defaultValue": 0,
    "min": 0,
    "max": 120,
    "unit": "years",
    "keyboardType": "decimal",
}

WEIGHT_FIELD = {
    "id": "weight",
    "name": "weight",
    "label": "Patient Weight (kg)",
    "type": "number",
    "required": True,
    "defaultValue": 0,
    "min": 0,
    "max": 500,
    "unit": "kg",
    "keyboardType": "decimal",
}

PATIENT_STEP_ID = "patientInfo"

# Tokens that, alongside "weight", mark a weight-loss *symptom* rather than a
# weight measurement — these must NOT count as "already has a weight field".
_WEIGHT_LOSS_TOKENS = {"loss", "lost", "concern", "concerns", "attempt", "attempts"}


def _tokens(name: str) -> set[str]:
    """Split a field name into lowercased tokens (camelCase + non-alnum)."""
    if not name:
        return set()
    parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return {t for t in re.split(r"[^A-Za-z0-9]+", parts.lower()) if t}


def _is_age_field(name: str) -> bool:
    return "age" in _tokens(name)


def _is_weight_field(name: str) -> bool:
    toks = _tokens(name)
    return "weight" in toks and not (toks & _WEIGHT_LOSS_TOKENS)


def _field_names(form: dict) -> list[str]:
    names: list[str] = []
    for step in (form or {}).get("steps", []) or []:
        for fld in step.get("fields", []) or []:
            n = fld.get("name")
            if n:
                names.append(n)
    return names


def inject(form: dict) -> tuple[dict, list[str]]:
    """Return (new_form, added) — a copy of ``form`` with missing age/weight
    fields added to a leading Patient Information step. ``added`` lists the
    measures injected (subset of {"age", "weight"}); empty means no change."""
    form = json.loads(json.dumps(form or {}))  # deep copy; never mutate input
    steps = form.setdefault("steps", [])

    names = _field_names(form)
    has_age = any(_is_age_field(n) for n in names)
    has_weight = any(_is_weight_field(n) for n in names)

    missing: list[dict] = []
    added: list[str] = []
    if not has_age:
        missing.append(AGE_FIELD)
        added.append("age")
    if not has_weight:
        missing.append(WEIGHT_FIELD)
        added.append("weight")
    if not missing:
        return form, []

    # Reuse an existing Patient Information step if a prior run created one,
    # otherwise prepend a fresh step so demographics are collected first.
    step = next((s for s in steps if s.get("id") == PATIENT_STEP_ID), None)
    if step is None:
        step = {
            "id": PATIENT_STEP_ID,
            "shortLabel": "Patient",
            "title": "Patient Information",
            "fields": [],
        }
        steps.insert(0, step)
    existing = {f.get("name") for f in step.get("fields", [])}
    step.setdefault("fields", [])
    for fld in missing:
        if fld["name"] not in existing:
            step["fields"].append(json.loads(json.dumps(fld)))
    return form, added


def patch_db() -> None:
    # Imported lazily so ``--generated`` can run with no app/DB dependencies.
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import Module

    db = SessionLocal()
    updated = unchanged = 0
    changes: list[str] = []
    try:
        for mod in db.scalars(select(Module)).all():
            new_form, added = inject(mod.form or {"steps": []})
            if not added:
                unchanged += 1
                continue
            mod.form = new_form
            updated += 1
            changes.append(f"    + {mod.title}: {', '.join(added)}")
        db.commit()
        print(f"[seed_demographics] db modules updated: {updated} | unchanged: {unchanged}")
        for line in changes:
            print(line)
    finally:
        db.close()


def patch_generated() -> None:
    files = sorted(GEN_DIR.glob("*.json"))
    updated = unchanged = skipped = 0
    for f in files:
        if f.name.startswith("_"):
            continue
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"  ! {f.name}: invalid JSON ({exc}) — skipped")
            skipped += 1
            continue
        form = payload.get("form")
        if not isinstance(form, dict):
            skipped += 1
            continue
        new_form, added = inject(form)
        if not added:
            unchanged += 1
            continue
        payload["form"] = new_form
        f.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        updated += 1
        print(f"    + {f.name}: {', '.join(added)}")
    print(
        f"[seed_demographics] generated files updated: {updated} | "
        f"unchanged: {unchanged} | skipped(bad): {skipped}"
    )


def run() -> None:
    args = sys.argv[1:]
    generated = "--generated" in args or "--all" in args
    # Default (no args, as called from the entrypoint) patches the DB. Pass
    # --generated to rewrite source files only; --all to do both.
    do_db = not generated or "--all" in args
    if generated:
        patch_generated()
    if do_db:
        patch_db()


if __name__ == "__main__":
    run()
