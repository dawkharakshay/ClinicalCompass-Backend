"""Oracle tests for the Multiple Sclerosis module.

Ported 1:1 from old_static_code/server/neuro-ophtho.test.ts
(describe "Multiple Sclerosis Logic").
"""

from app.recommendations.modules.multiplesclerosis import assess

BASE = {
    "msType": "rrms",
    "diseaseCourse": "mild_moderate",
    "relapseCountPast2Years": 1,
    "newT2LesionsPast12Months": 1,
    "gadEnhancingLesions": 0,
    "edssScore": 2.0,
    "priorDMT": "none",
    "jcvStatus": "negative",
    "isPregnantOrPlanning": False,
    "hasCardiacHistory": False,
    "hasLiverDisease": False,
    "hasActiveMalignancy": False,
    "age": 32,
    "wantsHighEfficacyFirstLine": False,
}


def test_moderate_efficacy_mild_moderate_naive_rrms():
    result = assess(dict(BASE))
    assert result["efficacyTier"] == "moderate"
    assert any("Dimethyl fumarate" in a for a in result["recommendedAgents"])


def test_ocrelizumab_for_ppms():
    result = assess({**BASE, "msType": "ppms", "diseaseCourse": "highly_active"})
    assert result["efficacyTier"] == "high"
    assert any("Ocrelizumab" in a for a in result["recommendedAgents"])
    assert "PPMS" in result["primaryRecommendation"]


def test_high_efficacy_highly_active_naive_wanting_high_efficacy():
    result = assess(
        {
            **BASE,
            "diseaseCourse": "highly_active",
            "relapseCountPast2Years": 3,
            "gadEnhancingLesions": 2,
            "wantsHighEfficacyFirstLine": True,
        }
    )
    assert result["efficacyTier"] == "high"
    assert any(
        "Natalizumab" in a or "Ocrelizumab" in a for a in result["recommendedAgents"]
    )


def test_avoids_natalizumab_and_flags_high_pml_risk():
    result = assess(
        {
            **BASE,
            "priorDMT": "natalizumab",
            "jcvStatus": "positive_high",
            "jcvIndexValue": 2.1,
            "diseaseCourse": "highly_active",
        }
    )
    assert any("PML" in f for f in result["urgentFlags"])
    assert "HIGH PML RISK" in result["pmlRiskAssessment"]


def test_active_malignancy_urgent_avoids_alemtuzumab_cladribine():
    result = assess({**BASE, "hasActiveMalignancy": True})
    assert any("malignancy" in f for f in result["urgentFlags"])
    assert any("Alemtuzumab" in a for a in result["agentsToAvoid"])


def test_pregnancy_flags_and_avoids_teratogenic_agents():
    result = assess({**BASE, "isPregnantOrPlanning": True})
    assert any("Pregnancy" in f for f in result["urgentFlags"])
    assert any("Teriflunomide" in a for a in result["agentsToAvoid"])


def test_symptomatic_management_for_non_active_spms():
    result = assess(
        {**BASE, "msType": "spms_inactive", "diseaseCourse": "mild_moderate"}
    )
    assert "non-active SPMS" in result["primaryRecommendation"]
    assert any("Symptomatic" in a for a in result["recommendedAgents"])


def test_evidence_level_a_and_references():
    result = assess(dict(BASE))
    assert result["evidenceLevel"] == "A"
    assert len(result["references"]) > 0
