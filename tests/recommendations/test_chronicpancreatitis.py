"""Tests for chronic pancreatitis port.

Cases ported 1:1 from old_static_code/server/gi-modules.test.ts
(describe "assessChronicPancreatitis"), plus branch-coverage fixtures.
"""

import re

from app.recommendations.modules.chronicpancreatitis import assess

BASE_INPUT = {
    "diagnosisConfirmed": True,
    "diagnosisMethod": "imaging",
    "cambridgeGrade": "III",
    "etiology": "alcohol",
    "isSmoker": True,
    "hasGeneticMutation": False,
    "painPattern": "type_b",
    "vasScore": 7,
    "hasPainRelatedHospitalizations": True,
    "isOnOpioids": False,
    "ductAnatomy": "dilated_with_stricture",
    "mpdDiameterMm": 8,
    "hasStones": True,
    "stoneSizeMm": 10,
    "stoneLocation": "head",
    "hasCalcifications": True,
    "hasStricture": True,
    "strictureLocation": "head",
    "hasPseudocyst": False,
    "hasBiliaryStenosis": False,
    "hasDuodenalObstruction": False,
    "hasSplenicVeinThrombosis": False,
    "hasPancreaticFistula": False,
    "hasPancreaticAscites": False,
    "suspectedMalignancy": False,
    "hasExocrineInsufficiency": True,
    "hasSteatorrhea": True,
    "hasMalnutrition": False,
    "isOnPERT": False,
    "hasType3cDiabetes": False,
    "isOnInsulin": False,
    "hasPriorERCP": False,
    "hasPriorESWL": False,
    "hasPriorSurgery": False,
    "hasPriorEndoscopicDrainage": False,
    "endoscopicDrainageResponse": None,
    "ageYears": 52,
    "isSurgicalCandidate": True,
    "performanceStatus": "good",
}


# ─── Ported oracle cases ──────────────────────────────────────────────────────
def test_eswl_ercp_for_large_obstructive_stones():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"]
    assert result["endoscopicTherapy"]
    assert re.match(r"^[ABC]$", result["evidenceLevel"])


def test_pert_for_exocrine_insufficiency_with_steatorrhea():
    result = assess(BASE_INPUT)
    assert result["exocrineSupportPlan"]
    assert re.search(r"PERT|enzyme|lipase", result["exocrineSupportPlan"], re.IGNORECASE)


def test_surgery_for_failed_endoscopic_therapy():
    result = assess({
        **BASE_INPUT,
        "hasPriorERCP": True,
        "hasPriorESWL": True,
        "hasPriorEndoscopicDrainage": True,
        "endoscopicDrainageResponse": "none",
    })
    assert result["surgicalConsideration"]


def test_flags_suspected_malignancy():
    result = assess({**BASE_INPUT, "suspectedMalignancy": True})
    assert any(re.search(r"malign|cancer|EUS|biopsy", f, re.IGNORECASE) for f in result["urgentFlags"])


def test_recommends_alcohol_and_smoking_cessation():
    result = assess(BASE_INPUT)
    assert result["lifestyleModification"]
    assert re.search(r"alcohol|smoking|cessation", result["lifestyleModification"], re.IGNORECASE)


def test_returns_references():
    result = assess(BASE_INPUT)
    assert len(result["references"]) > 0


# ─── Branch-coverage fixtures ─────────────────────────────────────────────────
def test_primary_recommendation_malignancy_priority():
    result = assess({**BASE_INPUT, "suspectedMalignancy": True})
    assert result["primaryRecommendation"] == (
        "Suspected malignancy in chronic pancreatitis: EUS-FNB + CT staging required urgently."
    )


def test_igg4_autoimmune_flag_and_primary():
    result = assess({**BASE_INPUT, "igg4Level": 200, "ductAnatomy": "normal"})
    assert any("IgG4 200 mg/dL (>135)" in f for f in result["urgentFlags"])
    assert result["primaryRecommendation"] == (
        "Autoimmune pancreatitis type 1 (IgG4 >135): prednisone trial before invasive intervention."
    )
    assert "Prednisone 40mg/day x4 weeks (autoimmune pancreatitis type 1)" in result["nextSteps"]


def test_igg4_at_threshold_not_flagged():
    # 135 is NOT > 135
    result = assess({**BASE_INPUT, "igg4Level": 135, "ductAnatomy": "normal", "suspectedMalignancy": False})
    assert not any("IgG4" in f for f in result["urgentFlags"])


def test_infected_pseudocyst_primary_and_flag():
    result = assess({
        **BASE_INPUT,
        "hasPseudocyst": True,
        "pseudocystSymptoms": "infected",
        "ductAnatomy": "normal",
    })
    assert result["primaryRecommendation"] == (
        "Infected pseudocyst: urgent EUS-guided drainage + IV antibiotics."
    )
    assert any("Infected pancreatic pseudocyst" in f for f in result["urgentFlags"])


def test_endoscopic_candidate_primary():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"] == (
        "Obstructive chronic pancreatitis: ERCP with pancreatic duct stenting ± ESWL for stones."
    )


def test_normal_duct_default_primary_and_nextsteps():
    result = assess({
        **BASE_INPUT,
        "ductAnatomy": "normal",
        "isSurgicalCandidate": False,
        "hasExocrineInsufficiency": False,
        "hasSteatorrhea": False,
    })
    assert result["primaryRecommendation"] == (
        "Chronic pancreatitis: alcohol/smoking cessation + pain management + PERT if exocrine insufficiency."
    )
    # No nextSteps triggered by any branch -> default fallback list
    assert "Alcohol and smoking cessation counseling" in result["nextSteps"]
    assert "Endoscopic therapy not indicated" in result["endoscopicTherapy"]


def test_divisum_endoscopic_branch():
    result = assess({**BASE_INPUT, "ductAnatomy": "divisum"})
    assert "PANCREAS DIVISUM" in result["endoscopicTherapy"]
    assert "Minor papilla sphincterotomy + dorsal duct stenting" in result["nextSteps"]


def test_disrupted_duct_branch():
    result = assess({**BASE_INPUT, "ductAnatomy": "disrupted_duct"})
    assert "DISCONNECTED PANCREATIC DUCT SYNDROME" in result["endoscopicTherapy"]


def test_asymptomatic_small_pseudocyst_observation():
    result = assess({
        **BASE_INPUT,
        "hasPseudocyst": True,
        "pseudocystSymptoms": "none",
        "pseudocystSizeCm": 4,
    })
    assert "observation" in result["pseudocystManagement"]


def test_large_pseudocyst_drainage():
    result = assess({
        **BASE_INPUT,
        "hasPseudocyst": True,
        "pseudocystSymptoms": "none",
        "pseudocystSizeCm": 7,
    })
    assert "drainage indicated" in result["pseudocystManagement"]
    assert "EUS-guided pseudocyst drainage with LAMS or double-pigtail stents" in result["nextSteps"]


def test_opioid_dose_string_with_unknown_fallback():
    result = assess({**BASE_INPUT, "isOnOpioids": True, "opioidDoseEquivalent": None})
    assert "Current opioid dose: unknown MME/day" in result["painManagement"]


def test_opioid_dose_with_value():
    result = assess({**BASE_INPUT, "isOnOpioids": True, "opioidDoseEquivalent": 90})
    assert "Current opioid dose: 90 MME/day" in result["painManagement"]


def test_type3c_diabetes_plan():
    result = assess({**BASE_INPUT, "hasType3cDiabetes": True})
    assert "TYPE 3c DIABETES" in result["endocrineSupportPlan"]


def test_not_surgical_candidate():
    result = assess({**BASE_INPUT, "isSurgicalCandidate": False})
    assert "not surgical candidate" in result["surgicalConsideration"]


def test_rationale_mpd_not_measured_when_zero():
    result = assess({**BASE_INPUT, "mpdDiameterMm": 0})
    assert "MPD diameter: not measured" in result["rationale"]
