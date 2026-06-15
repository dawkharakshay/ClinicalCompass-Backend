"""Build the PAD Clinical Performance & Quality Measures auth guide.

This module had no *AuthGuide.tsx in the legacy code (see forms/auth_guides/_map.json
"no_guide_modules"), so it is assembled here from its real legacy sources:

  - 15 measures (PM-1..PM-7, QM-1..QM-8) parsed verbatim from
    old_static_code/client/src/lib/padQMLogic.ts (PAD_QM_MEASURES)
  - CPT/ICD-10 codes verbatim from
    old_static_code/client/src/pages/PADQualityAppealLetter.tsx
  - Guideline citations verbatim from
    old_static_code/client/src/pages/PADQualityMeasures.tsx
  - Payer-specific authorization blocks reused from the already-extracted
    sibling guide forms/auth_guides/pad.json (same disease, real source =
    PADAuthGuide.tsx). CPT/ICD descriptions are standard CPT/ICD-10 descriptors
    (flagged in each note), since the legacy appeal letter carries bare codes only.

Output: forms/auth_guides/padqualitymeasures.json (seeded by scripts/seed_auth_guides.py).

    uv run python scripts/build_padqm_authguide.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / "old_static_code"
GEN = ROOT / "forms" / "auth_guides"

MODULE_TITLE = "PAD Clinical Performance & Quality Measures Clinical Compass"
LOGIC_SRC = OLD / "client" / "src" / "lib" / "padQMLogic.ts"

_MEASURE_KEYS = (
    "id", "type", "title", "description", "numerator", "denominator",
    "exclusions", "guidelineClass", "loe", "rationale", "isNew2026",
)


def parse_measures() -> list[dict]:
    """Parse the PAD_QM_MEASURES array out of padQMLogic.ts into JSON objects."""
    text = LOGIC_SRC.read_text(encoding="utf-8")
    start = text.index("export const PAD_QM_MEASURES")
    # Skip past the `: PADQMMeasure[] =` type annotation to the assignment's `[`.
    body = text[text.index("= [", start) + 2:]
    # Find the matching close of the top-level array.
    depth = 0
    for i, ch in enumerate(body):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                arr = body[: i + 1]
                break
    else:  # pragma: no cover
        raise RuntimeError("could not find end of PAD_QM_MEASURES array")

    # Strip whole-line `//` comments (none appear inside string literals here).
    arr = re.sub(r"(?m)^\s*//.*$", "", arr)
    # Quote the (unquoted) object keys.
    arr = re.sub(
        r"(?m)^(\s*)(" + "|".join(_MEASURE_KEYS) + r"):",
        r'\1"\2":',
        arr,
    )
    # Drop trailing commas before } or ].
    arr = re.sub(r",(\s*[}\]])", r"\1", arr)
    measures = json.loads(arr)
    # Sanity: 7 PM + 8 QM.
    assert len(measures) == 15, f"expected 15 measures, got {len(measures)}"
    return measures


# ── Codes (verbatim from PADQualityAppealLetter.tsx; descriptions = standard CPT/ICD-10) ──
_STD = "Standard CPT descriptor (legacy appeal letter carried the bare code)."
_STD_ICD = "Standard ICD-10 descriptor (legacy appeal letter carried the bare code)."

CPT_CODES = [
    {"code": "93922", "description": "Limited bilateral noninvasive physiologic studies of upper or lower extremity arteries (e.g., ABI with Doppler waveforms, 1–2 levels)", "note": _STD},
    {"code": "93923", "description": "Complete bilateral noninvasive physiologic studies of upper or lower extremity arteries (3 or more levels, or with provocative functional maneuvers)", "note": _STD},
    {"code": "93924", "description": "Noninvasive physiologic studies of lower extremity arteries, at rest and following treadmill stress testing", "note": _STD},
    {"code": "37228", "description": "Revascularization, endovascular, tibial/peroneal artery, unilateral, initial vessel; with transluminal angioplasty", "note": _STD},
    {"code": "37229", "description": "Revascularization, endovascular, tibial/peroneal artery, unilateral, initial vessel; with atherectomy (includes angioplasty when performed)", "note": _STD},
    {"code": "37230", "description": "Revascularization, endovascular, tibial/peroneal artery, unilateral, initial vessel; with transluminal stent placement(s) (includes angioplasty when performed)", "note": _STD},
    {"code": "37231", "description": "Revascularization, endovascular, tibial/peroneal artery, unilateral, initial vessel; with transluminal stent placement(s) and atherectomy (includes angioplasty when performed)", "note": _STD},
]

ICD10_CODES = [
    {"code": "I73.9", "description": "Peripheral vascular disease, unspecified", "notes": _STD_ICD, "required": False},
    {"code": "I70.201", "description": "Unspecified atherosclerosis of native arteries of extremities, right leg", "notes": _STD_ICD, "required": True},
    {"code": "I70.211", "description": "Atherosclerosis of native arteries of extremities with intermittent claudication, right leg", "notes": _STD_ICD, "required": True},
    {"code": "I70.221", "description": "Atherosclerosis of native arteries of extremities with rest pain, right leg", "notes": _STD_ICD, "required": True},
]

# ── Guideline citations (verbatim from PADQualityMeasures.tsx) ──
REFERENCES = [
    "Goodney PP, Ross EG, Bruckel JT, et al. 2026 ACC/AHA Clinical Performance and Quality Measures for Patients With Peripheral Artery Disease. J Am Coll Cardiol. 2026 Jan 8. DOI: 10.1016/j.jacc.2025.09.003. PMID: 41505788",
    "Gornik HL, Aronow HD, Goodney PP, et al. 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS Guideline for the Management of Lower Extremity Peripheral Artery Disease. Circulation. 2024;149(24):e1313–e410. PMID: 38743805",
]

_COR_LABEL = {
    "1": "Class 1 (Strong)",
    "2a": "Class 2a (Moderate)",
    "2b": "Class 2b (Weak)",
    "3_harm": "Class 3 (Harm)",
    "3_no_benefit": "Class 3 (No Benefit)",
}


def measure_section(m: dict) -> dict:
    kind = "Performance Measure" if m["type"] == "performance" else "Quality Measure"
    cor = _COR_LABEL.get(m["guidelineClass"], m["guidelineClass"])
    lines = [
        m["description"],
        "",
        f"**Numerator:** {m['numerator']}",
        f"**Denominator:** {m['denominator']}",
        "**Exclusions:** " + ("; ".join(m["exclusions"]) if m["exclusions"] else "None"),
        f"**Guideline class / LOE:** COR {cor} / LOE {m['loe']}"
        + ("  ·  New in 2026" if m["isNew2026"] else ""),
        f"**Rationale:** {m['rationale']}",
    ]
    return {
        "heading": f"{m['id']} — {m['title']} ({kind})",
        "kind": "prose",
        "text": "\n".join(lines),
    }


def build_markdown(measures: list[dict]) -> str:
    out = [
        "# PAD Clinical Performance & Quality Measures Clinical Compass",
        "## Peripheral Artery Disease — Performance & Quality Measures Authorization & Documentation Guide",
        "",
        "Assembled from legacy sources (no dedicated *AuthGuide page existed): "
        "padQMLogic.ts (measures), PADQualityAppealLetter.tsx (codes), "
        "PADQualityMeasures.tsx (citations), and the sibling PADAuthGuide.tsx "
        "payer blocks (reused from pad.json).",
        "",
        "## CPT Procedure / Diagnostic Codes",
    ]
    for c in CPT_CODES:
        out.append(f"- **{c['code']}** — {c['description']}")
    out += ["", "## ICD-10 Diagnosis Codes"]
    for c in ICD10_CODES:
        flag = " (primary)" if c["required"] else ""
        out.append(f"- **{c['code']}**{flag} — {c['description']}")
    out += ["", "## Performance Measures (PM-1 – PM-7)"]
    for m in measures:
        if m["type"] == "performance":
            out += [f"### {m['id']} — {m['title']}", measure_section(m)["text"], ""]
    out += ["## Quality Measures (QM-1 – QM-8)"]
    for m in measures:
        if m["type"] == "quality":
            out += [f"### {m['id']} — {m['title']}", measure_section(m)["text"], ""]
    out += ["## Guideline References"]
    for i, r in enumerate(REFERENCES, 1):
        out.append(f"{i}. {r}")
    return "\n".join(out)


def build_tables(measures: list[dict]) -> list[dict]:
    return [
        {
            "name": "CPT Procedure / Diagnostic Codes",
            "header": ["CPT", "Description"],
            "rows": [[c["code"], c["description"]] for c in CPT_CODES],
        },
        {
            "name": "ICD-10 Diagnosis Codes",
            "header": ["ICD-10", "Description", "Primary"],
            "rows": [[c["code"], c["description"], "Yes" if c["required"] else "No"] for c in ICD10_CODES],
        },
        {
            "name": "Performance & Quality Measures",
            "header": ["ID", "Type", "Title", "COR", "LOE", "New 2026"],
            "rows": [
                [m["id"], m["type"], m["title"], _COR_LABEL.get(m["guidelineClass"], m["guidelineClass"]),
                 m["loe"], "Yes" if m["isNew2026"] else "No"]
                for m in measures
            ],
        },
    ]


def run() -> None:
    measures = parse_measures()
    payers = json.loads((GEN / "pad.json").read_text(encoding="utf-8"))["auth_guide"]["payers"]

    custom_sections = [
        {
            "heading": "Back to Assessment",
            "kind": "link",
            "text": "Back to Assessment — opens the PAD Quality Measures assessment.",
            "href": "/pad-quality-measures",
        },
        {
            "heading": "About these measures",
            "kind": "prose",
            "text": (
                "Seven Performance Measures (PM-1 – PM-7), appropriate for public reporting and "
                "pay-for-performance, and eight Quality Measures (QM-1 – QM-8), for internal quality "
                "improvement, derived from the 2026 ACC/AHA Clinical Performance and Quality Measures "
                "for PAD and the 2024 ACC/AHA PAD Guideline. General exclusion rule: for all measures "
                "except PM-6 and PM-7, a clinician-documented determination that care is inappropriate "
                "excludes the patient; for all measures, patients who decline care are excluded. "
                "Supervised exercise therapy (PM-7) is Medicare-covered for symptomatic PAD."
            ),
        },
    ]
    custom_sections += [measure_section(m) for m in measures]
    custom_sections.append({
        "heading": "Guideline References",
        "kind": "prose",
        "text": "\n".join(f"{i}. {r}" for i, r in enumerate(REFERENCES, 1)),
    })

    auth_guide = {
        "sourceFile": "PADQualityMeasures.tsx (+ padQMLogic.ts, PADQualityAppealLetter.tsx; payers reused from PADAuthGuide.tsx)",
        "title": "PAD Clinical Performance & Quality Measures Clinical Compass",
        "subtitle": "Peripheral Artery Disease — Performance & Quality Measures Authorization & Documentation Guide",
        "cptCodes": CPT_CODES,
        "icd10Codes": ICD10_CODES,
        "payers": payers,
        "customSections": custom_sections,
        "raw": {
            "markdown": build_markdown(measures),
            "tables": build_tables(measures),
        },
    }

    payload = {"title": MODULE_TITLE, "auth_guide": auth_guide}
    out = GEN / "padqualitymeasures.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[build_padqm_authguide] wrote {out.relative_to(ROOT)} "
          f"({len(measures)} measures, {len(CPT_CODES)} CPT, {len(ICD10_CODES)} ICD, {len(payers)} payers)")


if __name__ == "__main__":
    run()
