"""Make the page-fill keys uniform across every appeal-letter template.

Every forms/appeal_letter_templates/<slug>.json gets the FULL canonical key set
(see CANON in scripts/build_appeal_letter_templates.py) in its ``defaults`` block,
so all modules expose the same fillable fields. Existing values are preserved —
only missing keys are added. For a missing ``cpt_codes`` / ``icd_codes`` the value
is pulled from the module's auth guide when available, else the canonical fallback.
Keys are written sorted, matching the build script's output style. Idempotent.

    uv run python scripts/uniform_appeal_letter_keys.py

After running, rebuild + restart the API (entrypoint reseeds Postgres):
    docker compose up -d --build api      # or: bash scripts/deploy_auth_guides.sh
"""

import json
from pathlib import Path

# Reuse the single source of truth for the canonical vocabulary + auth-guide codes.
from scripts.build_appeal_letter_templates import CANON, auth_codes

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "forms" / "appeal_letter_templates"


def canonical_default(key: str, slug: str, cpt: str | None, icd: str | None) -> str:
    """Default value for a missing key (auth-guide codes win for cpt/icd)."""
    if key == "cpt_codes" and cpt:
        return cpt
    if key == "icd_codes" and icd:
        return icd
    return CANON[key][0]


def run() -> None:
    all_keys = sorted(CANON)  # the 22 canonical page-fill keys
    files = sorted(f for f in OUT_DIR.glob("*.json") if not f.name.startswith("_"))

    changed = unchanged = 0
    added_counter: dict[str, int] = {k: 0 for k in all_keys}

    for f in files:
        payload = json.loads(f.read_text(encoding="utf-8"))
        tmpl = payload.get("appeal_letter_template")
        if not isinstance(tmpl, dict):
            continue

        slug = f.stem
        cpt, icd = auth_codes(slug)
        defaults: dict = dict(tmpl.get("defaults") or {})

        added = [k for k in all_keys if k not in defaults]
        for k in added:
            defaults[k] = canonical_default(k, slug, cpt, icd)
            added_counter[k] += 1

        # Rewrite defaults sorted for a uniform, stable ordering.
        new_defaults = {k: defaults[k] for k in sorted(defaults)}
        if new_defaults != (tmpl.get("defaults") or {}):
            tmpl["defaults"] = new_defaults
            f.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            changed += 1
        else:
            unchanged += 1

    print(f"[uniform_appeal_letter_keys] files: {len(files)} | "
          f"changed: {changed} | already-uniform: {unchanged}")
    print(f"  canonical key set ({len(all_keys)}): {', '.join(all_keys)}")
    print("  keys added (key -> #files):")
    for k in all_keys:
        if added_counter[k]:
            print(f"    {k}: {added_counter[k]}")


if __name__ == "__main__":
    run()
