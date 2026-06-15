"""Exercise the *dynamic* appeal-letter logic (app/appeal_letter.py).

renalcryoablation is the best-suited module for this: its clinical inputs
(tumor size -> cT1a/cT1b stage, R.E.N.A.L. nephrometry complexity, comorbidities,
contralateral kidney status) map directly onto the renderer's two dynamic
features that the mechanical baseline templates never use:

  * ``derived``  - computed values whose first matching rule wins (here: tumor
                   stage, complexity tier, the recommendation phrasing and the
                   guideline class/LOE that follow from the stage), and
  * ``sections`` - conditional paragraphs included only when their ``when``
                   condition matches the (defaults + answers + derived) context.

The recipe below is keyed off the SAME fields the module's ``assess()`` uses, so
two different submissions to this one module produce two materially different
letters. The ``test_two_letters_differ_*`` tests assert those differences, and
running this file directly prints the unified diff between the two letters.

    uv run pytest tests/recommendations/test_renalcryoablation_appeal_letter.py -s
    uv run python  tests/recommendations/test_renalcryoablation_appeal_letter.py
"""

from __future__ import annotations

import difflib

from app.appeal_letter import render_appeal_letter

# ── A dynamic appeal-letter recipe for renal cryoablation ────────────────────
# Unlike the mechanical baseline (defaults + flat template), this uses derived
# rules and conditional sections so the letter adapts to the clinical picture.
TEMPLATE: dict = {
    "defaults": {
        "letter_date": "[Date]",
        "patient_name": "[Patient Name]",
        "patient_dob": "[Date of Birth]",
        "member_id": "[Member ID]",
        "physician_name": "[Physician Name]",
        "credentials": "[Credentials]",
        "npi": "[NPI]",
    },
    "derived": [
        # First matching rule wins; rules are tried top-to-bottom.
        {
            "name": "tumor_stage",
            "rules": [
                {"when": {"field": "tumorSizeCm", "op": "lte", "value": 4}, "value": "T1a"},
                {"when": {"field": "tumorSizeCm", "op": "lte", "value": 7}, "value": "T1b"},
            ],
            "default": "T2",
        },
        {
            "name": "complexity",
            "rules": [
                {"when": {"field": "renalNephrometryScore", "op": "lte", "value": 6}, "value": "low"},
                {"when": {"field": "renalNephrometryScore", "op": "lte", "value": 9}, "value": "intermediate"},
            ],
            "default": "high",
        },
        # Derived-on-derived: these reference ``tumor_stage`` computed above
        # (derived specs are evaluated in order, each updating the context).
        {
            "name": "recommendation_phrase",
            "rules": [
                {"when": {"field": "tumor_stage", "op": "eq", "value": "T1a"},
                 "value": "is medically indicated as a guideline-endorsed alternative to partial nephrectomy"},
                {"when": {"field": "tumor_stage", "op": "eq", "value": "T1b"},
                 "value": "should be authorized as a nephron-sparing alternative for this higher-risk patient"},
            ],
            "default": "is requested for individualized review",
        },
        {
            "name": "guideline_class",
            "rules": [
                {"when": {"field": "tumor_stage", "op": "eq", "value": "T1a"}, "value": "Class I, Level of Evidence B"},
                {"when": {"field": "tumor_stage", "op": "eq", "value": "T1b"}, "value": "Class IIa, Level of Evidence B-NR"},
            ],
            "default": "individualized clinical judgment",
        },
    ],
    "section_separator": "\n\n",
    "sections": [
        {
            "when": {"field": "tumor_stage", "op": "eq", "value": "T1a"},
            "text": "Per the AUA 2021 Renal Mass Guideline, thermal ablation is a recommended "
                    "alternative to partial nephrectomy for cT1a tumors (≤4 cm). Cryoablation "
                    "achieves 5-year local recurrence-free survival of 90-95% in appropriately "
                    "selected T1a patients (Psutka SP, et al. J Urol 2013).",
        },
        {
            "when": {"all": [
                {"field": "tumor_stage", "op": "eq", "value": "T1b"},
                {"any": [
                    {"field": "patientAge", "op": "gte", "value": 70},
                    {"field": "cardiopulmonaryDisease", "op": "truthy"},
                    {"field": "contralateralKidneyFunction", "op": "ne", "value": "normal"},
                    {"field": "priorNephrectomy", "op": "truthy"},
                ]},
            ]},
            "text": "This is a cT1b mass (4-7 cm) in a patient at elevated surgical risk. AUA 2021 "
                    "supports ablation for T1b tumors in poor surgical candidates where partial "
                    "nephrectomy carries prohibitive risk.",
        },
        {
            "when": {"any": [
                {"field": "contralateralKidneyFunction", "op": "eq", "value": "solitary"},
                {"field": "ckd", "op": "truthy"},
            ]},
            "text": "The patient has a solitary kidney or CKD stage 3+. Nephron-sparing ablation is "
                    "preferred over radical nephrectomy to preserve renal function and reduce the "
                    "risk of dialysis dependence (AUA 2021, Grade A).",
        },
        {
            "when": {"field": "hereditarySyndrome", "op": "truthy"},
            "text": "The patient carries a hereditary RCC syndrome (e.g., VHL, HLRCC, BHD). "
                    "Nephron preservation is essential given the high likelihood of future "
                    "ipsilateral or contralateral tumors.",
        },
        {
            "when": {"field": "anticoagulation", "op": "truthy"},
            "text": "The patient is on anticoagulation; cryoablation is favored over RFA given its "
                    "cryogenic hemostatic effect and lower bleeding risk. A peri-procedural bridging "
                    "plan will be coordinated with the prescribing physician.",
        },
    ],
    "template": (
        "{{letter_date}}\n\n"
        "To Whom It May Concern,\n\n"
        "I am writing to appeal the denial of prior authorization for percutaneous renal "
        "cryoablation for my patient {{patient_name}} (DOB {{patient_dob}}, Member ID "
        "{{member_id}}).\n\n"
        "This is a {{tumor_stage}} renal mass with {{complexity}} R.E.N.A.L. nephrometry "
        "complexity. Cryoablation {{recommendation_phrase}} ({{guideline_class}}).\n\n"
        "{{sections}}\n\n"
        "I respectfully request reconsideration and approval.\n\n"
        "Sincerely,\n{{physician_name}}, {{credentials}}\nNPI: {{npi}}"
    ),
}


# ── Two submissions to the SAME module ───────────────────────────────────────
# Case A: small, low-complexity tumor in a fit patient -> straightforward T1a.
CASE_A = {
    "letter_date": "2026-06-11",
    "patient_name": "Jane Doe",
    "patient_dob": "1972-03-04",
    "member_id": "A1234567",
    "physician_name": "Dr. Alex Rivera",
    "credentials": "MD",
    "npi": "1112223334",
    "tumorSizeCm": 3.0,
    "renalNephrometryScore": 5,
    "patientAge": 54,
    "contralateralKidneyFunction": "normal",
    "cardiopulmonaryDisease": False,
    "priorNephrectomy": False,
    "ckd": False,
    "hereditarySyndrome": False,
    "anticoagulation": False,
}

# Case B: larger, high-complexity tumor, solitary kidney, comorbid, anticoagulated
# -> T1b with high surgical risk and several conditional sections triggered.
CASE_B = {
    "letter_date": "2026-06-11",
    "patient_name": "Jane Doe",
    "patient_dob": "1972-03-04",
    "member_id": "A1234567",
    "physician_name": "Dr. Alex Rivera",
    "credentials": "MD",
    "npi": "1112223334",
    "tumorSizeCm": 5.5,
    "renalNephrometryScore": 11,
    "patientAge": 74,
    "contralateralKidneyFunction": "solitary",
    "cardiopulmonaryDisease": True,
    "priorNephrectomy": False,
    "ckd": True,
    "hereditarySyndrome": False,
    "anticoagulation": True,
}


def _diff(a: str, b: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            a.splitlines(), b.splitlines(),
            fromfile="case_A_T1a_low_complexity",
            tofile="case_B_T1b_high_risk",
            lineterm="",
        )
    )


# ── Tests of the dynamic logic itself ────────────────────────────────────────

def test_derived_values_resolve_from_clinical_inputs():
    """derived rules: stage + complexity computed from numeric inputs."""
    letter_a = render_appeal_letter(TEMPLATE, CASE_A)
    letter_b = render_appeal_letter(TEMPLATE, CASE_B)

    assert "This is a T1a renal mass with low R.E.N.A.L." in letter_a
    assert "This is a T1b renal mass with high R.E.N.A.L." in letter_b


def test_derived_on_derived_recommendation_and_guideline_class():
    """recommendation_phrase / guideline_class derive off the derived stage."""
    letter_a = render_appeal_letter(TEMPLATE, CASE_A)
    letter_b = render_appeal_letter(TEMPLATE, CASE_B)

    assert "is medically indicated as a guideline-endorsed alternative" in letter_a
    assert "Class I, Level of Evidence B" in letter_a

    assert "should be authorized as a nephron-sparing alternative" in letter_b
    assert "Class IIa, Level of Evidence B-NR" in letter_b


def test_conditional_sections_included_only_when_matched():
    """sections appear/disappear based on the (answers + derived) context."""
    letter_a = render_appeal_letter(TEMPLATE, CASE_A)
    letter_b = render_appeal_letter(TEMPLATE, CASE_B)

    # Case A: only the T1a paragraph; none of the risk/solitary/anticoag ones.
    assert "thermal ablation is a recommended alternative" in letter_a
    assert "solitary kidney or CKD" not in letter_a
    assert "elevated surgical risk" not in letter_a
    assert "anticoagulation" not in letter_a

    # Case B: T1b risk + solitary/CKD + anticoagulation paragraphs all present;
    # the T1a paragraph is absent.
    assert "elevated surgical risk" in letter_b
    assert "solitary kidney or CKD" in letter_b
    assert "cryogenic hemostatic effect" in letter_b
    assert "thermal ablation is a recommended alternative" not in letter_b


def test_two_letters_differ():
    """The same module yields two materially different letters."""
    letter_a = render_appeal_letter(TEMPLATE, CASE_A)
    letter_b = render_appeal_letter(TEMPLATE, CASE_B)
    assert letter_a != letter_b

    diff = _diff(letter_a, letter_b)
    # Body text changes (not just the admin placeholders that are identical here).
    assert "T1a" in diff and "T1b" in diff
    print("\n===== Appeal-letter diff (Case A vs Case B, single module) =====\n")
    print(diff)


if __name__ == "__main__":
    a = render_appeal_letter(TEMPLATE, CASE_A)
    b = render_appeal_letter(TEMPLATE, CASE_B)
    print("################## CASE A (T1a, low complexity) ##################\n")
    print(a)
    print("\n################## CASE B (T1b, high risk) ##################\n")
    print(b)
    print("\n################## UNIFIED DIFF (A -> B) ##################\n")
    print(_diff(a, b))
