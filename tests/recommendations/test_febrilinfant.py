"""Oracle tests for the Febrile Infant engine.

Cases ported 1:1 from old_static_code/server/pediatrics.test.ts
("Febrile Infant Logic" describe block) plus branch-coverage fixtures
derived directly from febrilInfantLogic.ts.
"""

from __future__ import annotations

import re

from app.recommendations.modules.febrilinfant import assess

BASE_INPUT = {
    "ageGroup": "29_60_days",
    "ageDays": 35,
    "temperatureCelsius": 38.5,
    "wellAppearing": True,
    "pretermBirth": False,
    "gestationalAgeWeeks": 39,
    "priorAntibiotics": False,
    "priorHospitalization": False,
    "immunocompromised": False,
    "wbcCount": None,
    "absoluteNeutrophilCount": None,
    "bandCount": None,
    "cReactiveProtein": None,
    "procalcitonin": None,
    "urinalysisPositive": None,
    "csfWBC": None,
    "csfProtein": None,
    "csfGlucose": None,
    "sourceFocusFound": False,
    "hsvRiskFactors": False,
    "hasSeizures": False,
    "hasSkinLesions": False,
    "hasEyeDischarge": False,
    "pecarnLowRisk": None,
}


def _with(**overrides):
    return {**BASE_INPUT, **overrides}


# ─── Ported oracle cases ───────────────────────────────────────────────────


def test_well_appearing_35_day_infant():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"]
    assert len(result["workupRequired"]) > 0
    assert len(result["references"]) > 0


def test_flags_hsv_risk_factors():
    result = assess(_with(hsvRiskFactors=True))
    assert re.search(r"HSV|acyclovir", " ".join(result["urgentFlags"]), re.I)
    assert result["hsvManagement"]


def test_flags_neonate_full_sepsis():
    result = assess(_with(ageGroup="0_7_days", ageDays=5))
    blob = " ".join(result["urgentFlags"]) + result["primaryRecommendation"]
    assert re.search(r"NEONATE|sepsis|ADMISSION", blob, re.I)


def test_ill_appearing_high_risk():
    result = assess(_with(wellAppearing=False))
    assert result["riskCategory"] == "high"
    assert re.search(r"ILL-APPEARING", " ".join(result["urgentFlags"]), re.I)


def test_pecarn_low_risk():
    result = assess(_with(
        pecarnLowRisk=True,
        urinalysisPositive=False,
        procalcitonin=0.3,
        absoluteNeutrophilCount=3000,
    ))
    assert result["riskCategory"] == "low"


def test_positive_urinalysis_uti_workup():
    result = assess(_with(urinalysisPositive=True))
    workup_text = " ".join(result["workupRequired"])
    assert re.search(r"urine|UTI|culture", workup_text, re.I)


# ─── Additional branch-coverage fixtures ───────────────────────────────────


def test_neonate_shape():
    result = assess(_with(ageGroup="0_7_days", ageDays=5))
    assert result["riskCategory"] == "very_high"
    assert result["evidenceLevel"] == "A"
    assert "HSV surface swabs (eye, nasopharynx, rectum)" in result["workupRequired"]
    assert len(result["references"]) == 1


def test_8_21_days_high_risk():
    result = assess(_with(ageGroup="8_21_days", ageDays=14))
    assert result["riskCategory"] == "high"
    assert "FEBRILE INFANT 14 DAYS" in result["primaryRecommendation"]
    # Low HSV risk branch for the 8-28 day group.
    assert result["hsvManagement"].startswith("Low HSV risk.")


def test_22_28_days_with_hsv_risk():
    result = assess(_with(ageGroup="22_28_days", ageDays=25, hasSeizures=True))
    assert result["riskCategory"] == "high"
    assert result["hsvManagement"].startswith("HSV RISK PRESENT")


def test_intermediate_ua_positive_anc_high():
    # ua_positive and NOT anc_low (anc >= 4090) -> UTI-source intermediate branch
    result = assess(_with(urinalysisPositive=True, absoluteNeutrophilCount=5000))
    assert result["riskCategory"] == "intermediate"
    assert "If UTI source" in result["antibioticRecommendation"]
    assert any("AAP 2021 — intermediate risk" in w for w in result["workupRequired"])


def test_intermediate_default_branch():
    # well-appearing, not low-risk, ua not positive -> default intermediate
    result = assess(_with(absoluteNeutrophilCount=5000, procalcitonin=1.0))
    assert result["riskCategory"] == "intermediate"
    assert result["admissionDecision"].startswith("INTERMEDIATE RISK: Clinical judgment")
    assert "Lumbar puncture recommended" in result["workupRequired"]


def test_low_risk_disposition_and_followup():
    result = assess(_with(
        pecarnLowRisk=True,
        urinalysisPositive=False,
        procalcitonin=0.3,
        absoluteNeutrophilCount=3000,
    ))
    assert result["riskCategory"] == "low"
    assert result["dispositionPlan"].startswith("DISCHARGE")
    assert result["followUpPlan"].startswith("Mandatory 24-hour follow-up")
    assert "FEBRILE INFANT 35 DAYS — LOW RISK" in result["primaryRecommendation"]


def test_pecarn_threshold_anc_boundary():
    # ANC exactly 4090 is NOT < 4090 -> not low risk even with PECARN true
    result = assess(_with(
        pecarnLowRisk=True,
        urinalysisPositive=False,
        procalcitonin=0.3,
        absoluteNeutrophilCount=4090,
    ))
    assert result["riskCategory"] == "intermediate"


def test_pecarn_threshold_procal_boundary():
    # PCT exactly 0.5 is NOT < 0.5 -> not low risk
    result = assess(_with(
        pecarnLowRisk=True,
        urinalysisPositive=False,
        procalcitonin=0.5,
        absoluteNeutrophilCount=3000,
    ))
    assert result["riskCategory"] == "intermediate"


def test_rationale_renders_not_obtained_and_nulls():
    result = assess(BASE_INPUT)
    assert "ANC: not obtained" in result["rationale"]
    assert "PCT: not obtained" in result["rationale"]
    assert "UA positive: null" in result["rationale"]
    assert "PECARN low risk: null" in result["rationale"]
    assert "Well-appearing: true" in result["rationale"]


def test_ill_appearing_primary_rec_uses_urgent_flag():
    result = assess(_with(wellAppearing=False))
    assert result["primaryRecommendation"] == result["urgentFlags"][0]
    assert "Lumbar puncture (CSF analysis + culture + HSV PCR)" in result["workupRequired"]
