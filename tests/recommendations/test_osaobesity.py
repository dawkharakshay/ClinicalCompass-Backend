"""Tests for the OSA + Obesity Clinical Compass port.

Oracle: old_static_code/client/src/pages/OSAObesityCompass.tsx
(inline ``getRecommendation`` function). No *.test.ts exists for this module;
fixtures derived 1:1 from the TS decision branches.
"""

from app.recommendations.modules.osaobesity import assess

# A complete, fully-eligible baseline answer set.
ELIGIBLE = {
    "osa_severity": "moderate",
    "obesity_status": "bmi_35_39",
    "diabetes_status": "no_dm",
    "pap_status": "pap_current",
    "contraindications": "none",
    "prior_weight_loss": "prior_attempt",
    "glp1_preference": "tirzepatide",
}


def test_incomplete_missing_steps():
    res = assess({"osa_severity": "moderate"})
    assert res["level"] == "incomplete"
    assert res["title"] == "Assessment Incomplete"
    assert res["details"] == []


def test_mtc_men2_absolute_contraindication():
    data = {**ELIGIBLE, "contraindications": "mtc_men2"}
    res = assess(data)
    assert res["level"] == "not_indicated"
    assert res["title"] == "Tirzepatide Contraindicated — MTC/MEN2 History"
    assert len(res["warnings"]) == 1


def test_osa_pending():
    data = {**ELIGIBLE, "osa_severity": "pending"}
    res = assess(data)
    assert res["level"] == "conditional"
    assert res["title"] == "OSA Diagnosis Must Be Confirmed First"


def test_mild_osa_not_indicated():
    data = {**ELIGIBLE, "osa_severity": "mild"}
    res = assess(data)
    assert res["level"] == "not_indicated"
    assert res["title"] == "Mild OSA — Zepbound OSA Indication Not Met"


def test_bmi_under_27_not_indicated():
    data = {**ELIGIBLE, "obesity_status": "bmi_under_27"}
    res = assess(data)
    assert res["level"] == "not_indicated"
    assert res["title"] == "BMI Does Not Meet Threshold for Zepbound OSA Indication"


def test_t2dm_pathway():
    data = {**ELIGIBLE, "diabetes_status": "t2dm"}
    res = assess(data)
    assert res["level"] == "conditional"
    assert "Mounjaro" in res["title"]


def test_eligible_approved_on_pap():
    res = assess(ELIGIBLE)
    assert res["level"] == "approved"
    assert res["title"] == "Zepbound (Tirzepatide) Indicated — OSA + Obesity"
    # PAP-current note is the first detail.
    assert res["details"][0].startswith("Patient is on PAP therapy")
    assert "obesity (BMI 35–39.9 kg/m²)" in res["summary"]
    assert res["warnings"] == []


def test_eligible_severe_bmi40_standalone_pap():
    data = {
        **ELIGIBLE,
        "osa_severity": "severe",
        "obesity_status": "bmi_40plus",
        "pap_status": "pap_intolerant",
    }
    res = assess(data)
    assert res["level"] == "approved"
    assert res["details"][0].startswith("Patient is not using PAP")
    assert "severe OSA confirmed" in res["summary"]
    assert "≥40 kg/m²" in res["summary"]


def test_eligible_no_prior_attempt_warning_and_note():
    data = {**ELIGIBLE, "prior_weight_loss": "no_attempt"}
    res = assess(data)
    assert res["level"] == "approved"
    assert res["warnings"] == [
        "Document prior dietary/lifestyle weight loss attempt before PA submission — required by most payers."
    ]
    # The missing-attempt note is appended to details.
    assert any("documentation is missing" in d for d in res["details"])


def test_eligible_semaglutide_agent_note():
    data = {**ELIGIBLE, "glp1_preference": "semaglutide"}
    res = assess(data)
    assert res["level"] == "approved"
    assert any("Semaglutide (Wegovy) is NOT FDA-approved for OSA" in d for d in res["details"])


def test_eligible_other_glp1_agent_note():
    data = {**ELIGIBLE, "glp1_preference": "other_glp1"}
    res = assess(data)
    assert res["level"] == "approved"
    assert any("Other GLP-1 RAs" in d for d in res["details"])


def test_bmi_27_29_borderline_conditional():
    data = {**ELIGIBLE, "obesity_status": "bmi_27_29"}
    res = assess(data)
    assert res["level"] == "conditional"
    assert res["title"] == "BMI 27–29.9 — Overweight, Not Obese: Borderline Eligibility"


def test_pancreatitis_relative_contra_falls_to_further_eval():
    # contraindications != "none" => not eligible; obese BMI, moderate OSA,
    # no T2DM => falls through to the final "Further Evaluation Needed" branch.
    data = {**ELIGIBLE, "contraindications": "pancreatitis"}
    res = assess(data)
    assert res["level"] == "conditional"
    assert res["title"] == "Further Evaluation Needed"
