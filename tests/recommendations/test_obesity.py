"""Obesity engine tests.

Oracle cases ported 1:1 from old_static_code/server/new-modules.test.ts
("Obesity Logic" describe block), plus branch-coverage fixtures derived
directly from obesityLogic.ts.
"""

from app.recommendations.modules.obesity import (
    assess,
    is_surgical_candidate,
)


def _base() -> dict:
    return {
        "bmi": 38,
        "waistCircumference": 110,
        "t2dm": True,
        "hypertension": True,
        "osa": False,
        "nafld": False,
        "gerd": False,
        "dyslipidemia": False,
        "cardiovascularDisease": False,
        "heartFailure": False,
        "lifestyleInterventionAttempted": True,
        "glp1Attempted": False,
        "glp1Response": "not_tried",
        "priorBariatricSurgery": "none",
        "age": 45,
        "sex": "female",
        "pregnant": False,
        "surgicalRisk": "low",
        "patientPreference": "no_preference",
        "ibd": False,
        "cirrhosis": False,
        "eatingDisorder": False,
        "substanceAbuse": False,
    }


# ─── Oracle cases (new-modules.test.ts) ──────────────────────────────────────


def test_identifies_bmi38_t2dm_as_surgical_candidate():
    assert is_surgical_candidate(_base()) is True


def test_recommends_surgery_or_glp1_for_bmi38_t2dm():
    r = assess(_base())
    assert r["primaryApproach"] in (
        "bariatric_surgery_sleeve",
        "bariatric_surgery_rygb",
        "bariatric_surgery_bpd_ds",
        "glp1_agonist",
        "glp1_plus_lifestyle",
    )
    assert r["evidenceLevel"] is not None


def test_recommends_glp1_for_bmi32_t2dm_expanded():
    r = assess({**_base(), "bmi": 32})
    assert r["primaryApproach"] in (
        "glp1_agonist",
        "glp1_plus_lifestyle",
        "bariatric_surgery_sleeve",
        "bariatric_surgery_rygb",
        "esg_endoscopic",
    )


def test_flags_gerd_for_surgical_selection():
    r = assess({**_base(), "gerd": True})
    has_gerd = any(
        ("GERD" in w or "reflux" in w or "sleeve" in w) for w in r["keyWarnings"]
    ) or (
        "RYGB" in (r.get("surgicalProcedure") or "")
        or "Roux" in (r.get("surgicalProcedure") or "")
        or "bypass" in (r.get("surgicalProcedure") or "")
    )
    assert has_gerd is True


def test_returns_next_steps_array_nonempty():
    r = assess(_base())
    assert isinstance(r["nextSteps"], list)
    assert len(r["nextSteps"]) >= 1


def test_returns_contraindications_array():
    r = assess(_base())
    assert isinstance(r["contraindications"], list)


# ─── Branch-coverage fixtures ────────────────────────────────────────────────


def test_lifestyle_only_for_overweight():
    # BMI < 30 -> lifestyle_only branch
    r = assess({**_base(), "bmi": 28, "t2dm": False, "hypertension": False})
    assert r["primaryApproach"] == "lifestyle_only"
    assert r["evidenceLevel"] == "Class I"


def test_lifestyle_only_class1_no_comorbidities():
    # Class 1 (30-34.9), no comorbidities, no t2dm -> lifestyle_only
    r = assess(
        {**_base(), "bmi": 32, "t2dm": False, "hypertension": False}
    )
    assert r["primaryApproach"] == "lifestyle_only"


def test_glp1_plus_lifestyle_when_naive():
    # BMI 38, glp1 not attempted -> glp1_plus_lifestyle
    r = assess(_base())
    assert r["primaryApproach"] == "glp1_plus_lifestyle"
    assert r["glp1Agent"].startswith("Tirzepatide")  # t2dm path
    # surgical candidate at BMI>=35 -> extra referral step
    assert any("Discuss bariatric surgery" in s for s in r["nextSteps"])


def test_glp1_naive_alt_includes_esg_when_candidate():
    r = assess(_base())  # esg candidate (BMI 38, lifestyle attempted, no prior surgery)
    assert "esg_endoscopic" in r["alternativeApproaches"]


def test_surgical_rygb_for_intolerant_t2dm():
    # glp1 attempted + intolerant, surgical candidate, t2dm -> RYGB preferred
    r = assess(
        {**_base(), "glp1Attempted": True, "glp1Response": "intolerant"}
    )
    assert r["primaryApproach"] == "bariatric_surgery_rygb"
    assert r["surgicalProcedure"] == "Roux-en-Y Gastric Bypass"


def test_surgical_sleeve_for_intolerant_no_rygb_factors():
    # intolerant, surgical candidate via BMI>=40, no gerd/t2dm/bmi>=50 -> sleeve
    r = assess(
        {
            **_base(),
            "bmi": 42,
            "t2dm": False,
            "glp1Attempted": True,
            "glp1Response": "intolerant",
        }
    )
    assert r["primaryApproach"] == "bariatric_surgery_sleeve"
    assert r["surgicalProcedure"] == "Sleeve Gastrectomy"


def test_esg_branch_for_inadequate_nonlow_risk():
    # inadequate, esg candidate, BMI 30-39.9, surgicalRisk != low.
    # Make NOT a surgical candidate (BMI 32, no t2dm) so surgical branch skipped.
    r = assess(
        {
            **_base(),
            "bmi": 32,
            "t2dm": False,
            "hypertension": True,  # keeps comorbidity but surgical needs bmi>=35
            "glp1Attempted": True,
            "glp1Response": "inadequate",
            "surgicalRisk": "moderate",
        }
    )
    assert r["primaryApproach"] == "esg_endoscopic"
    assert r["evidenceLevel"] == "Class IIa"


def test_alt_glp1_when_intolerant_not_surgical_candidate():
    # intolerant, NOT surgical candidate, NOT esg path (surgicalRisk low) -> glp1_agonist
    r = assess(
        {
            **_base(),
            "bmi": 32,
            "t2dm": False,
            "glp1Attempted": True,
            "glp1Response": "intolerant",
            "surgicalRisk": "low",
        }
    )
    assert r["primaryApproach"] == "glp1_agonist"
    assert any(
        "Surgical risk prohibitive" in w for w in r["keyWarnings"]
    )


def test_revision_surgery_branch():
    # adequate response (not naive/intolerant/inadequate), prior surgery != none
    r = assess(
        {
            **_base(),
            "glp1Attempted": True,
            "glp1Response": "adequate",
            "priorBariatricSurgery": "sleeve",
        }
    )
    assert r["primaryApproach"] == "revision_surgery"


def test_multidisciplinary_default():
    # adequate response, no prior surgery -> default multidisciplinary
    r = assess(
        {
            **_base(),
            "glp1Attempted": True,
            "glp1Response": "adequate",
        }
    )
    assert r["primaryApproach"] == "multidisciplinary"


def test_pregnancy_contraindication():
    r = assess({**_base(), "pregnant": True})
    assert any("Pregnancy" in c for c in r["contraindications"])


def test_bmi50_warning_and_rygb():
    r = assess(
        {
            **_base(),
            "bmi": 52,
            "t2dm": False,
            "gerd": False,
            "glp1Attempted": True,
            "glp1Response": "intolerant",
        }
    )
    assert any("BMI ≥50" in w for w in r["keyWarnings"])
    # bmi>=50 -> prefer_rygb true
    assert r["primaryApproach"] == "bariatric_surgery_rygb"


def test_glp1_agent_selection_cvd_no_t2dm():
    # cvd true, t2dm false -> semaglutide SELECT agent in glp1_plus_lifestyle naive path
    r = assess(
        {
            **_base(),
            "bmi": 38,
            "t2dm": False,
            "cardiovascularDisease": True,
        }
    )
    assert r["primaryApproach"] == "glp1_plus_lifestyle"
    assert "Semaglutide (Wegovy)" in r["glp1Agent"]
