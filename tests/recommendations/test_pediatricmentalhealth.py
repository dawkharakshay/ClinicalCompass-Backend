"""Tests for the Pediatric Mental Health port.

Cases ported 1:1 from old_static_code/server/pediatrics.test.ts
(describe "Pediatric Mental Health Logic").
"""

import re

from app.recommendations.modules.pediatricmentalhealth import assess

BASE_INPUT = {
    "ageGroup": "school_age",
    "ageYears": 10,
    "sex": "male",
    "phq2Score": None,
    "phq9Score": None,
    "phq9ItemNineScore": None,
    "gad7Score": None,
    "scaredScore": None,
    "mchatScore": None,
    "asqScore": None,
    "vanderbiltScore": None,
    "crafftScore": None,
    "hasPriorMentalHealthDiagnosis": False,
    "priorDiagnoses": [],
    "currentMedications": [],
    "hasActiveSuicidalIdeation": False,
    "hasSuicidePlan": False,
    "hasSuicideAttemptHistory": False,
    "hasFirearmInHome": False,
    "hasMedicationsInHome": False,
    "hasTraumaHistory": False,
    "hasChronicMedicalCondition": False,
    "hasLGBTQIdentity": False,
    "hasFamilyHistoryMentalIllness": False,
    "hasFamilyHistorySuicide": False,
    "hasSchoolProblems": False,
    "hasSocialIsolation": False,
    "hasBullyingExposure": False,
    "hasSleepProblems": False,
    "screenTimeHoursPerDay": 3,
    "physicalActivityMinutesPerDay": 30,
    "familySupportLevel": "moderate",
}


def _merge(**overrides):
    out = dict(BASE_INPUT)
    out.update(overrides)
    return out


def test_routine_guidance_low_risk_school_age():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"]
    assert len(result["references"]) > 0


def test_active_suicidal_ideation_with_plan_urgent():
    result = assess(_merge(hasActiveSuicidalIdeation=True, hasSuicidePlan=True))
    assert re.search(r"suicidal|EMERGENCY|plan", " ".join(result["urgentFlags"]), re.I)


def test_firearm_in_home_means_restriction():
    result = assess(_merge(hasActiveSuicidalIdeation=True, hasFirearmInHome=True))
    assert result["meansRestrictionCounseling"]
    assert re.search(r"firearm|gun|lock", result["meansRestrictionCounseling"], re.I)


def test_depression_diagnosis_phq9_ge_10():
    result = assess(
        _merge(
            ageGroup="early_adolescent",
            ageYears=13,
            phq2Score=4,
            phq9Score=12,
            phq9ItemNineScore=0,
        )
    )
    screening_text = " ".join(s["interpretation"] for s in result["screeningResults"])
    assert re.search(r"moderate|depression|PHQ", screening_text, re.I)


def test_anxiety_gad7_ge_10():
    result = assess(_merge(ageGroup="early_adolescent_12_14", ageYears=13, gad7Score=12))
    screening_text = " ".join(s["interpretation"] for s in result["screeningResults"])
    assert re.search(r"anxiety|GAD", screening_text, re.I)


def test_crafft_ge_2_substance_use():
    result = assess(_merge(ageGroup="late_adolescent", ageYears=16, crafftScore=3))
    screening_text = " ".join(
        s["interpretation"] + s["action"] for s in result["screeningResults"]
    )
    assert re.search(r"CRAFFT|substance|brief intervention", screening_text, re.I)


def test_adhd_evaluation_vanderbilt_positive():
    result = assess(_merge(vanderbiltScore="adhd"))
    all_text = " ".join(result["treatmentRecommendations"]) + " ".join(result["diagnoses"])
    assert re.search(r"ADHD|attention", all_text, re.I)


def test_lgbtq_identity_elevated_suicide_risk():
    result = assess(
        _merge(
            ageGroup="late_adolescent",
            ageYears=16,
            hasLGBTQIdentity=True,
            hasActiveSuicidalIdeation=True,
        )
    )
    assert re.search(r"suicidal|LGBTQ|risk", " ".join(result["urgentFlags"]), re.I)


# ─── Additional branch coverage (derived from TS branches) ───────────────────

def test_phq9_severe_flags_urgent_and_diagnosis():
    result = assess(_merge(phq9Score=22))
    assert any("SEVERE depression" == s["interpretation"] for s in result["screeningResults"])
    assert "Major Depressive Disorder — severe" in result["diagnoses"]
    assert any("PHQ-9 SEVERE (22)" in f for f in result["urgentFlags"])


def test_phq9_item_nine_positive_triggers_si_flag():
    result = assess(_merge(phq9ItemNineScore=1))
    assert any("ACTIVE SUICIDAL IDEATION" in f for f in result["urgentFlags"])


def test_mchat_high_risk_referral():
    result = assess(_merge(mchatScore=3))
    assert any("HIGH risk for autism" == s["interpretation"] for s in result["screeningResults"])
    assert any("M-CHAT HIGH RISK" in f for f in result["urgentFlags"])


def test_prior_attempt_priority_referral():
    result = assess(_merge(hasSuicideAttemptHistory=True))
    assert any("prior suicide attempt" in r for r in result["referrals"])
    assert result["meansRestrictionCounseling"].startswith(
        "MEANS RESTRICTION COUNSELING REQUIRED (AAP 2024)"
    )


def test_universal_means_restriction_when_low_risk():
    result = assess(BASE_INPUT)
    assert result["meansRestrictionCounseling"].startswith(
        "Universal means restriction counseling"
    )
