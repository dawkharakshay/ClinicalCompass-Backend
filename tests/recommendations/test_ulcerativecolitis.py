"""Tests for the Ulcerative Colitis module.

Oracle cases ported 1:1 from old_static_code/server/gi-modules.test.ts
(describe "assessUlcerativeColitis"), plus additional branch-coverage fixtures
derived directly from ulcerativeColitisLogic.ts.
"""

import re

from app.recommendations.modules.ulcerativecolitis import assess

BASE_INPUT = {
    "extent": "extensive",
    "severity": "moderate",
    "hasBloodyStools": True,
    "stoolFrequencyPerDay": 5,
    "hasNocturnalSymptoms": False,
    "priorTherapy": "none",
    "hasLostResponseToBiologic": False,
    "hasAntiDrugAntibodies": False,
    "isOnSteroids": True,
    "isSteroidDependent": False,
    "isSteroidRefractory": False,
    "hasActiveTB": False,
    "hasLatentTB": False,
    "hasHepatitisB": False,
    "hasMalignancyHistory": False,
    "isPregnant": False,
    "hasHeartFailure": False,
    "hasDemyelinatingDisease": False,
    "hasAnemia": False,
    "ageYears": 38,
    "hasHighRiskFeatures": False,
    "hasColonoscopyConfirmed": True,
}


# ─── Oracle tests (1:1 from gi-modules.test.ts) ──────────────────────────────

def test_recommends_biologic_for_moderate_severe_steroid_dependent_uc():
    result = assess({**BASE_INPUT, "isSteroidDependent": True})
    assert result["primaryRecommendation"]
    assert result["biologicSelection"]
    assert re.match(r"^[ABC]$", result["evidenceLevel"])


def test_recommends_urgent_colectomy_evaluation_for_acute_severe_uc():
    result = assess(
        {**BASE_INPUT, "severity": "acute_severe", "isSteroidRefractory": True}
    )
    assert len(result["urgentFlags"]) > 0 or re.search(
        r"colect|surgery", result["primaryRecommendation"], re.IGNORECASE
    )


def test_recommends_il23_or_jak_after_anti_tnf_failure():
    result = assess(
        {**BASE_INPUT, "priorTherapy": "failed_anti_tnf", "hasLostResponseToBiologic": True}
    )
    assert result["biologicSelection"]


def test_flags_active_tb_as_contraindication():
    result = assess({**BASE_INPUT, "hasActiveTB": True})
    assert any(
        re.search(r"TB|tuberculosis", f, re.IGNORECASE) for f in result["urgentFlags"]
    )


def test_returns_references():
    result = assess(BASE_INPUT)
    assert len(result["references"]) > 0


# ─── Additional branch-coverage fixtures ─────────────────────────────────────

def test_mild_proctitis_first_line_5asa():
    result = assess(
        {**BASE_INPUT, "extent": "proctitis", "severity": "mild", "priorTherapy": "none"}
    )
    assert result["primaryRecommendation"] == (
        "Mild proctitis/left-sided UC: topical + oral 5-ASA is first-line therapy."
    )
    assert "FIRST-LINE" in result["inductionTherapy"]
    assert result["biologicSelection"] == ""
    assert "Mesalamine suppository 1g/day (proctitis)" in result["recommendedAgents"]


def test_perforation_emergency_colectomy():
    result = assess({**BASE_INPUT, "hasPerforation": True})
    assert any("BOWEL PERFORATION" in f for f in result["urgentFlags"])
    assert result["colectomyConsideration"].startswith("EMERGENCY COLECTOMY")


def test_toxic_megacolon_flag():
    result = assess({**BASE_INPUT, "hasColonDilation": True})
    assert any("TOXIC MEGACOLON" in f for f in result["urgentFlags"])
    assert result["colectomyConsideration"].startswith("EMERGENCY COLECTOMY")


def test_steroid_refractory_rescue_plan_day3():
    result = assess(
        {
            **BASE_INPUT,
            "severity": "acute_severe",
            "isHospitalized": True,
            "isSteroidRefractory": True,
            "daysOnIVSteroids": 4,
        }
    )
    assert result["acuteSevereUCPlan"].startswith("STEROID-REFRACTORY ACUTE SEVERE UC")
    assert "Infliximab 5mg/kg IV (rescue — CONSTRUCT trial)" in result["recommendedAgents"]
    assert result["colectomyConsideration"].startswith("Steroid-refractory acute severe UC")


def test_acute_severe_initial_management_no_rescue():
    # hospitalized + steroid refractory but days < 3 -> initial management branch
    result = assess(
        {
            **BASE_INPUT,
            "severity": "acute_severe",
            "isHospitalized": True,
            "isSteroidRefractory": True,
            "daysOnIVSteroids": 2,
        }
    )
    assert result["acuteSevereUCPlan"].startswith("ACUTE SEVERE UC — Initial management")


def test_failed_multiple_biologics_colectomy_discussion():
    result = assess({**BASE_INPUT, "priorTherapy": "failed_multiple_biologics"})
    assert result["primaryRecommendation"].startswith("Refractory UC after multiple")
    assert any("Multiple biologic failure" in f for f in result["urgentFlags"])
    assert result["colectomyConsideration"].startswith("Refractory UC after multiple")
    assert "Etrasimod 2mg QD (S1P modulator)" in result["recommendedAgents"]


def test_chf_avoids_anti_tnf():
    result = assess({**BASE_INPUT, "hasCongestiveHeartFailure": True})
    assert any("CHF (EF <35%)" in f for f in result["urgentFlags"])
    assert any("Anti-TNF agents" in a for a in result["agentsToAvoid"])


def test_jak_contraindication_avoided():
    result = assess({**BASE_INPUT, "hasThromboembolismHistory": True})
    assert any("JAK inhibitors" in a for a in result["agentsToAvoid"])


def test_failed_5asa_escalates_to_biologic():
    result = assess({**BASE_INPUT, "priorTherapy": "failed_5asa"})
    assert "escalate to biologic" in result["inductionTherapy"]
    assert "Vedolizumab preferred" in result["biologicSelection"]


def test_mild_extensive_goes_to_biologic_branch():
    # priorTherapy none, severity mild, extent extensive -> biologic branch
    # (extent === 'extensive' matches the 2nd condition before the else branch).
    result = assess({**BASE_INPUT, "severity": "mild", "extent": "extensive"})
    assert "Moderate-severe or extensive UC" in result["inductionTherapy"]
    assert result["biologicSelection"]


def test_oral_5asa_else_branch_unreachable_extent():
    # The 3rd (else) induction branch requires severity 'mild' AND an extent that
    # is none of proctitis/left_sided/extensive/pancolitis. No valid UCExtent
    # reaches it, but an out-of-enum extent does. Confirms the else literal.
    result = assess({**BASE_INPUT, "severity": "mild", "extent": "ileitis"})
    assert "Mild-moderate extensive UC" in result["inductionTherapy"]
    assert "Oral mesalamine 4.8g/day (MMX)" in result["recommendedAgents"]


def test_default_nextsteps_present():
    result = assess(BASE_INPUT)
    assert "IBD specialist referral" in result["nextSteps"]
    assert result["rationale"].startswith("UC extent: extensive.")
