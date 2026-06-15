"""Tests for Bright Futures Well-Child logic.

Ported 1:1 from old_static_code/server/pediatrics.test.ts
("Bright Futures Well-Child Logic" describe block).
"""

import re

from app.recommendations.modules.brightfutures import assess

BASE_INPUT = {
    "visitAge": "9_months",
    "sex": "male",
    "bmiPercentile": None,
    "weightForLengthPercentile": 50,
    "developmentalConcerns": False,
    "m_chatScore": None,
    "phq2Score": None,
    "phq9Score": None,
    "asqScore": None,
    "hasVisionConcerns": False,
    "hasHearingConcerns": False,
    "leadRiskFactors": False,
    "ironDeficiencyRisk": False,
    "tbExposureRisk": False,
    "dyslipidemiRisk": False,
    "sexuallyActive": False,
    "substanceUseScreenPositive": False,
    "tobaccoExposure": False,
    "familySocialRisks": False,
    "isAdolescent": False,
    "hasChronicCondition": False,
}


def _with(**overrides):
    return {**BASE_INPUT, **overrides}


def test_returns_well_child_recommendation_for_9_month_visit():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"]
    assert len(result["screeningsRequired"]) > 0
    assert len(result["references"]) > 0


def test_flags_developmental_concerns_for_early_intervention_referral():
    result = assess(_with(visitAge="9_months", developmentalConcerns=True, asqScore="refer"))
    assert re.search(r"DEVELOPMENTAL|early intervention", " ".join(result["urgentFlags"]), re.I)


def test_includes_m_chat_screening_at_18_month_visit():
    result = assess(_with(visitAge="18_months", m_chatScore=2))
    screening_names = " ".join(s["screening"] for s in result["screeningsRequired"])
    assert re.search(r"M-CHAT|autism", screening_names, re.I)


def test_flags_food_insecurity_for_wic_referral():
    result = assess(_with(familySocialRisks=True))
    all_text = " ".join([*result["urgentFlags"], *result["anticipatoryGuidance"]])
    assert re.search(r"WIC|food|SDOH", all_text, re.I)


def test_flags_phq2_positive_at_adolescent_visit():
    result = assess(_with(visitAge="15_years", isAdolescent=True, phq2Score=4, phq9Score=12))
    assert re.search(r"PHQ|depression|mental health", " ".join(result["urgentFlags"]), re.I)
