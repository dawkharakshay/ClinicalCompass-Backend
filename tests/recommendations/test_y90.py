"""Tests for Y-90 Radioembolization Clinical Compass.

Ported 1:1 from:
  old_static_code/server/y90.candidacy.test.ts
  old_static_code/server/y90.tace.test.ts
"""

from app.recommendations.modules.y90 import assess

# Strong Y90 candidate - BCLC B, Child-Pugh A, TACE-refractory
eligible_candidate = {
    "diagnosis": "hcc",
    "bclcStage": "b",
    "childPughScore": "a",
    "ecogPerformanceStatus": 0,
    "portalVeinInvolvement": "none",
    "taceFeasibility": "refractory",
    "extrahepticSpread": False,
    "liverFunction": "preserved",
    "tumorSize": 4,
    "tumorCount": 2,
    "priorTACE": True,
    "taceRefractory": True,
}

# Not a candidate - Child-Pugh C, BCLC D, poor function
not_eligible_candidate = {
    "diagnosis": "hcc",
    "bclcStage": "d",
    "childPughScore": "c",
    "ecogPerformanceStatus": 3,
    "portalVeinInvolvement": "main",
    "taceFeasibility": "eligible",
    "extrahepticSpread": True,
    "liverFunction": "advanced",
    "tumorSize": 12,
    "tumorCount": 5,
    "priorTACE": False,
    "taceRefractory": False,
}


# ---- Candidacy test file ----

def test_bclc_b_tace_refractory_is_eligible_or_caution():
    result = assess(eligible_candidate)
    assert result["candidacy"] in ("eligible", "caution")


def test_eligible_candidate_has_recommendations():
    result = assess(eligible_candidate)
    assert len(result["recommendations"]) > 0


def test_eligible_candidate_has_dosimetry_notes():
    result = assess(eligible_candidate)
    assert result["dosimetryNotes"] is not None
    assert len(result["dosimetryNotes"]) > 0


def test_eligible_candidate_has_follow_up_schedule():
    result = assess(eligible_candidate)
    assert len(result["followUpSchedule"]) > 0


def test_child_pugh_c_is_not_eligible_or_caution():
    result = assess(not_eligible_candidate)
    assert result["candidacy"] in ("not-eligible", "caution")


def test_not_eligible_has_contraindications():
    result = assess(not_eligible_candidate)
    assert len(result["contraindications"]) > 0


def test_branch_pvt_assessed():
    data = {**eligible_candidate, "bclcStage": "c", "portalVeinInvolvement": "branch"}
    result = assess(data)
    assert result["candidacy"] in ("eligible", "caution", "not-eligible")


def test_main_pvt_cautious_or_not_eligible():
    data = {**eligible_candidate, "bclcStage": "c", "portalVeinInvolvement": "main"}
    result = assess(data)
    assert result["candidacy"] in ("caution", "not-eligible")


def test_no_pvt_most_favorable():
    data = {**eligible_candidate, "portalVeinInvolvement": "none"}
    result = assess(data)
    assert result["candidacy"] in ("eligible", "caution")


def test_result_has_all_required_fields():
    result = assess(eligible_candidate)
    for key in (
        "candidacy",
        "summary",
        "recommendations",
        "contraindications",
        "dosimetryNotes",
        "followUpSchedule",
        "references",
    ):
        assert key in result


def test_candidacy_is_valid_value():
    result = assess(eligible_candidate)
    assert result["candidacy"] in ("eligible", "not-eligible", "caution")


def test_recommendations_is_list():
    result = assess(eligible_candidate)
    assert isinstance(result["recommendations"], list)


def test_references_is_list():
    result = assess(eligible_candidate)
    assert isinstance(result["references"], list)


# ---- TACE feasibility test file ----

def test_tace_eligible_discuss_tace_vs_y90():
    data = {
        "diagnosis": "hcc",
        "bclcStage": "b",
        "taceFeasibility": "eligible",
        "tumorSize": 7,
    }
    result = assess(data)
    assert result["candidacy"] == "caution"
    assert "TACE remains standard first-line" in result["summary"]
    assert "EASL 2024" in result["summary"]
    assert any("TACE vs. Y90" in r for r in result["recommendations"])


def test_tace_refractory_intermediate_hcc():
    data = {
        "diagnosis": "hcc",
        "bclcStage": "b",
        "taceFeasibility": "refractory",
        "tumorSize": 8,
    }
    result = assess(data)
    assert result["candidacy"] == "eligible"
    assert "TACE-refractory" in result["summary"]
    assert "EASL 2024" in result["summary"]
    assert "Y90 recommended" in result["summary"]
    assert "≥205 Gy" in result["dosimetryNotes"]


def test_diffuse_infiltrative_hcc():
    data = {
        "diagnosis": "hcc",
        "bclcStage": "b",
        "taceFeasibility": "diffuse",
        "tumorSize": 10,
    }
    result = assess(data)
    assert result["candidacy"] == "caution"
    assert "Diffuse/infiltrative" in result["summary"]
    assert "TACE efficacy" in result["summary"]
    assert any("diffuse" in r for r in result["recommendations"])


def test_branch_pvt_safety_evidence():
    data = {
        "diagnosis": "hcc",
        "bclcStage": "c",
        "portalVeinInvolvement": "branch",
        "taceFeasibility": "refractory",
    }
    result = assess(data)
    assert result["candidacy"] == "eligible"
    assert "branch portal vein" in result["summary"]
    assert "safe" in result["summary"]
    assert any("YES-P" in r for r in result["recommendations"])


def test_references_include_easl_and_yesp():
    data = {
        "diagnosis": "hcc",
        "bclcStage": "b",
        "taceFeasibility": "refractory",
    }
    result = assess(data)
    assert "EASL Clinical Practice Guidelines: HCC (2024 Update)" in result["references"]
    assert "YES-P Trial (Salem et al., 2024)" in result["references"]


def test_legacy_trial_reference_early_hcc():
    data = {
        "diagnosis": "hcc",
        "bclcStage": "0",
        "tumorSize": 4,
        "tumorCount": 1,
    }
    result = assess(data)
    assert "LEGACY Trial (Lewandowski et al., 2023)" in result["references"]
    assert "LEGACY Trial" in result["summary"]
