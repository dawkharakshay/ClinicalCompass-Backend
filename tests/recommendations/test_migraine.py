"""Oracle tests for migraine module.

Ported 1:1 from old_static_code/server/neuro-ophtho.test.ts (describe "Migraine Logic").
"""

from app.recommendations.modules.migraine import assess

BASE = {
    "migraineSubtype": "episodic",
    "frequency": "moderate",
    "headacheDaysPerMonth": 6,
    "acuteTherapyResponse": "none_tried",
    "preventiveHistory": "none",
    "hasCardiovascularDisease": False,
    "hasUncontrolledHypertension": False,
    "hasHemiplegicMigraine": False,
    "hasBasilarMigraine": False,
    "isPregnantOrPlanning": False,
    "hasMOH": False,
    "acuteMedicationDaysPerMonth": 3,
    "hasDepression": False,
    "hasEpilepsy": False,
    "hasWeightConcerns": False,
    "wantsInjectable": False,
    "age": 35,
}


def test_triptans_first_line_acute_for_moderate_severe():
    result = assess(dict(BASE))
    assert "Triptans" in result["acuteTherapy"]
    assert any("Sumatriptan" in a for a in result["recommendedAgents"])


def test_gepants_ditans_when_triptans_contraindicated_by_cv():
    result = assess({**BASE, "hasCardiovascularDisease": True})
    assert "gepants" in result["acuteTherapy"]
    assert any("Triptans" in a for a in result["agentsToAvoid"])


def test_cgrp_mabs_after_failure_of_2plus_oral_preventives():
    result = assess(
        {
            **BASE,
            "frequency": "high",
            "headacheDaysPerMonth": 10,
            "preventiveHistory": "failed_2plus_preventives",
        }
    )
    assert "CGRP" in result["preventiveTherapy"]
    assert any("Erenumab" in a for a in result["recommendedAgents"])


def test_chronic_migraine_requires_preventive_therapy():
    result = assess({**BASE, "frequency": "chronic", "headacheDaysPerMonth": 18})
    assert any("Chronic migraine" in f for f in result["urgentFlags"])
    assert "preventive therapy" in result["primaryRecommendation"]


def test_moh_flagged_and_withdrawal_recommended():
    result = assess({**BASE, "hasMOH": True, "acuteMedicationDaysPerMonth": 14})
    assert any("MOH" in f for f in result["urgentFlags"])
    assert "withdrawal" in result["mohManagement"]


def test_magnesium_safest_preventive_in_pregnancy():
    result = assess(
        {
            **BASE,
            "frequency": "high",
            "headacheDaysPerMonth": 9,
            "isPregnantOrPlanning": True,
        }
    )
    assert any("Magnesium" in a for a in result["recommendedAgents"])
    assert any("Topiramate" in a for a in result["agentsToAvoid"])


def test_amitriptyline_for_migraine_with_comorbid_depression():
    result = assess(
        {**BASE, "frequency": "high", "headacheDaysPerMonth": 9, "hasDepression": True}
    )
    assert any("Amitriptyline" in a for a in result["recommendedAgents"])


def test_evidence_level_a_and_references():
    result = assess(dict(BASE))
    assert result["evidenceLevel"] == "A"
    assert len(result["references"]) > 0
