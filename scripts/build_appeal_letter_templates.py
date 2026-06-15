"""Convert the legacy static appeal letters into data-driven appeal_letter_template
recipes (one JSON per module), the mechanical/faithful baseline.

Source: scripts/appeal_letters.json  ->  {"<File>AppealLetter.tsx": "<letter body with [[placeholders]]>"}
Map:    scripts/migrate_appeal_letters.py  ->  FILE_TO_TITLE (legacy file stem -> module title)

For each letter we:
  1. Canonicalize the recurring admin/provider placeholders ([[PATIENT_NAME]],
     [[Date]], [[NPI]], [[CPT_CODES]] ... and all their messy variants) into a
     single canonical {{snake_case}} placeholder the renderer understands
     (app/appeal_letter.py — placeholder regex only matches {{word.dots}}).
  2. Leave every other [[...]] (bespoke clinical free-text fill-ins like
     "[[DESCRIBE — arm pain, numbness…]]") as a literal single-bracket [..]
     marker, exactly as a provider would hand-complete it.
  3. Emit defaults only for the canonical keys actually used; CPT/ICD defaults
     are pulled from the module's already-extracted auth guide when available.

No clinical logic is authored — derived rules / conditional sections are left to
the richer hand-authored recipes (see forms/appeal_letter_templates/renalcryoablation.json).

Output: forms/appeal_letter_templates/<slug>.json
        + forms/appeal_letter_templates/_normalization_report.json

    uv run python scripts/build_appeal_letter_templates.py
"""

import ast
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LETTERS = ROOT / "scripts" / "appeal_letters.json"
MIGRATE = ROOT / "scripts" / "migrate_appeal_letters.py"
AUTH_DIR = ROOT / "forms" / "auth_guides"
OUT_DIR = ROOT / "forms" / "appeal_letter_templates"

# Cyrillic / other homoglyphs that crept into a couple of legacy names.
_HOMOGLYPHS = {"т": "t", "о": "o", "н": "n", "а": "a",
               "е": "e", "с": "c", "р": "p", "х": "x"}


def _deglyph(s: str) -> str:
    return "".join(_HOMOGLYPHS.get(ch, ch) for ch in s)


# ── Canonical placeholder vocabulary ────────────────────────────────────────
# canonical key -> (default value, {lowercased variant strings})
CANON: dict[str, tuple[str, set[str]]] = {
    "letter_date": ("[Date]", {"date"}),
    "patient_name": ("[Patient Name]", {"patient_name", "patient name", "patientname"}),
    "patient_dob": ("[Date of Birth]", {"patient_dob", "date of birth", "dob", "patientdob"}),
    "member_id": ("[Member ID]", {"member id", "member_id", "memberid", "insurance id", "insurance_id"}),
    "policy_number": ("[Policy Number]", {"policy_number", "policy number"}),
    "claim_number": ("[Claim Number]", {"claim number", "claimnumber", "claim_number"}),
    "npi": ("[NPI]", {"npi", "npi number", "physician_npi"}),
    "physician_name": ("[Physician Name]", {"physician_name", "physician name", "provider name",
                                            "provider_name", "physicianname"}),
    "credentials": ("[Credentials]", {"credentials", "physician_credentials", "physiciancredentials"}),
    "practice_name": ("[Practice Name]", {"practice_name", "practice name", "practicename",
                                          "physician_practice"}),
    "practice_phone": ("[Phone]", {"phone", "practice_phone", "physician_phone", "practicephone"}),
    "practice_email": ("[Email]", {"email", "practice_email", "physician_email", "practiceemail"}),
    "practice_fax": ("[Fax]", {"fax", "physician_fax"}),
    "practice_address": ("[Practice Address]", {"physician_address", "practiceaddress"}),
    "insurance_name": ("the plan", {"insurance company name", "insurer name", "insurancecompany"}),
    "insurance_address": ("[Insurance Address]", {"insurance address", "insuranceaddress"}),
    "medical_director": ("Medical Director", {"medicaldirector"}),
    "specialty": ("[Specialty]", {"specialty"}),
    "procedure_description": ("[Procedure Description]", {"proceduredescription", "procedure_description"}),
    "cpt_codes": ("[CPT Code(s)]", {"cpt_codes", "cptcodes"}),
    "icd_codes": ("[ICD-10 Code(s)]", {"icd_codes", "icd10_codes", "icdcodes"}),
    "additional_clinical_notes": ("", {"additional clinical notes", "additional_clinical_notes",
                                       "additionalclinicalnotes"}),
}
_VARIANT_TO_KEY = {v: k for k, (_, vs) in CANON.items() for v in vs}


def load_file_to_title() -> dict[str, str]:
    src = MIGRATE.read_text(encoding="utf-8")
    m = re.search(r"FILE_TO_TITLE\s*=\s*\{(.*?)\n\}", src, re.S)
    return ast.literal_eval("{" + m.group(1) + "\n}")


def auth_codes(slug: str) -> tuple[str | None, str | None]:
    """Return (cpt, icd) default strings from the module's auth guide, if any."""
    f = AUTH_DIR / f"{slug}.json"
    if not f.exists():
        return None, None
    try:
        ag = json.loads(f.read_text(encoding="utf-8")).get("auth_guide") or {}
    except json.JSONDecodeError:
        return None, None
    cpt = ", ".join(c["code"] for c in (ag.get("cptCodes") or []) if c.get("code")) or None
    icd = ", ".join(c["code"] for c in (ag.get("icd10Codes") or []) if c.get("code")) or None
    return cpt, icd


def convert(body: str, slug: str, norm_counter: Counter) -> tuple[str, dict]:
    used: set[str] = set()
    literal: list[str] = []

    def repl(m: "re.Match[str]") -> str:
        inner = m.group(1).strip()
        key = _VARIANT_TO_KEY.get(inner.lower())
        if key:
            norm_counter[f"[[{inner}]] -> {{{{{key}}}}}"] += 1
            used.add(key)
            return f"{{{{{key}}}}}"
        # bespoke clinical fill-in: collapse [[ ... ]] back to a single bracket
        literal.append(inner)
        return f"[{inner}]"

    template = re.sub(r"\[\[([^\]]+)\]\]", repl, body)

    defaults: dict[str, str] = {}
    cpt, icd = auth_codes(slug)
    for key in sorted(used):
        val = CANON[key][0]
        if key == "cpt_codes" and cpt:
            val = cpt
        elif key == "icd_codes" and icd:
            val = icd
        defaults[key] = val

    return template, defaults


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    letters = json.loads(LETTERS.read_text(encoding="utf-8"))
    file_to_title = load_file_to_title()
    # Match keys after de-homoglyphing both sides.
    title_by_clean = {_deglyph(k): v for k, v in file_to_title.items()}

    norm = Counter()
    written = unmatched = 0
    missing_titles: list[str] = []
    literal_only: list[str] = []

    for raw_file, body in sorted(letters.items()):
        stem = raw_file[:-4] if raw_file.endswith(".tsx") else raw_file  # drop .tsx
        clean_stem = _deglyph(stem)
        title = title_by_clean.get(clean_stem)
        if not title:
            unmatched += 1
            missing_titles.append(raw_file)
            continue
        slug = _deglyph(clean_stem.replace("AppealLetter", "")).lower()

        template, defaults = convert(body, slug, norm)
        if "{{" not in template:
            literal_only.append(slug)

        payload = {
            "title": title,
            "appeal_letter_template": {"defaults": defaults, "template": template},
        }
        (OUT_DIR / f"{slug}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        written += 1

    report = {
        "written": written,
        "unmatched": unmatched,
        "unmatched_files": missing_titles,
        "templates_without_canonical_placeholders": sorted(literal_only),
        "normalizations": dict(norm.most_common()),
    }
    (OUT_DIR / "_normalization_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[build_appeal_letter_templates] written: {written} | unmatched: {unmatched} | "
          f"distinct normalizations: {len(norm)}")
    if missing_titles:
        print("  unmatched files:", missing_titles)
    if literal_only:
        print(f"  note: {len(literal_only)} letters had no canonical admin placeholders")


if __name__ == "__main__":
    run()
