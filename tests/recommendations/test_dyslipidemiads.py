"""Tests for the Dyslipidemia Clinical Compass engine.

Ported 1:1 from old_static_code/server/dyslipidemia.logic.test.ts.
"""

from __future__ import annotations

import copy

from app.recommendations.modules.dyslipidemiads import (
    assess,
    calculate_ascvd_risk,
    determine_ldl_c_goal,
    determine_prevention_category,
    determine_risk_level,
    determine_statin_intensity,
    get_statin_recommendation,
    recommend_non_statin_therapies,
)


def _flat(patient: dict) -> dict:
    """Flatten a nested PatientData into the flat keys the seeded form emits."""
    flat = {k: v for k, v in patient.items() if k != "lipidPanel"}
    flat.update(patient.get("lipidPanel", {}))
    return flat

BASE_PATIENT = {
    "age": 55,
    "sex": "male",
    "smoker": False,
    "diabetic": False,
    "hypertensive": False,
    "familyHistoryPrematureCAD": False,
    "priorMI": False,
    "priorStroke": False,
    "priorPAD": False,
    "aorticAneurysm": False,
    "lipidPanel": {
        "ldlC": 150,
        "hdlC": 40,
        "triglycerides": 150,
        "totalCholesterol": 250,
    },
}


def _patient(**overrides) -> dict:
    p = copy.deepcopy(BASE_PATIENT)
    panel = overrides.pop("lipidPanel", None)
    if panel is not None:
        p["lipidPanel"].update(panel)
    p.update(overrides)
    return p


# --- determinePreventionCategory ---


def test_secondary_for_prior_mi():
    assert determine_prevention_category(_patient(priorMI=True)) == "secondary"


def test_secondary_for_prior_stroke():
    assert determine_prevention_category(_patient(priorStroke=True)) == "secondary"


def test_primary_for_diabetic():
    assert determine_prevention_category(_patient(diabetic=True)) == "primary"


def test_primordial_for_young_healthy():
    assert determine_prevention_category(_patient(age=30)) == "primordial"


# --- determineRiskLevel ---


def test_risk_very_high_secondary():
    p = _patient(priorMI=True)
    cat = determine_prevention_category(p)
    assert determine_risk_level(p, cat) == "very-high"


def test_risk_very_high_severe_hyperchol():
    p = _patient(lipidPanel={"ldlC": 200})
    cat = determine_prevention_category(p)
    assert determine_risk_level(p, cat) == "very-high"


def test_risk_high_diabetic_with_factors():
    p = _patient(diabetic=True, age=45, smoker=True)
    cat = determine_prevention_category(p)
    assert determine_risk_level(p, cat) == "high"


def test_risk_low_primordial():
    p = _patient(age=30)
    cat = determine_prevention_category(p)
    assert determine_risk_level(p, cat) == "low"


# --- determineLDLCGoal ---


def test_ldl_goal_very_high():
    assert determine_ldl_c_goal("very-high") == 55


def test_ldl_goal_high():
    assert determine_ldl_c_goal("high") == 70


def test_ldl_goal_moderate():
    assert determine_ldl_c_goal("moderate") == 100


def test_ldl_goal_low():
    assert determine_ldl_c_goal("low") == 130


# --- determineStatinIntensity ---


def test_statin_high_for_very_high():
    assert determine_statin_intensity("very-high", 150, 55) == "high"


def test_statin_high_for_high_above_goal():
    assert determine_statin_intensity("high", 100, 70) == "high"


def test_statin_moderate_for_high_at_goal():
    assert determine_statin_intensity("high", 65, 70) == "moderate"


def test_statin_low_for_moderate_at_goal():
    assert determine_statin_intensity("moderate", 95, 100) == "low"


def test_statin_none_for_low():
    assert determine_statin_intensity("low", 120, 130) == "none"


# --- getStatinRecommendation ---


def test_rec_high_intensity():
    assert "Atorvastatin 40-80 mg" in get_statin_recommendation("high")


def test_rec_moderate_intensity():
    assert "Moderate-intensity" in get_statin_recommendation("moderate")


def test_rec_low_intensity():
    assert "Low-intensity" in get_statin_recommendation("low")


def test_rec_none_lifestyle():
    assert "lifestyle modifications" in get_statin_recommendation("none")


# --- recommendNonStatinTherapies ---


def test_ezetimibe_when_not_at_goal():
    therapies = recommend_non_statin_therapies("high", 100, 70)
    assert any("Ezetimibe" in t for t in therapies)


def test_pcsk9_for_very_high_not_at_goal():
    therapies = recommend_non_statin_therapies("very-high", 120, 55)
    assert any("PCSK9" in t for t in therapies)


def test_inclisiran_for_elevated_lpa():
    therapies = recommend_non_statin_therapies("high", 80, 70, 100)
    assert any("Inclisiran" in t for t in therapies)


def test_empty_when_at_goal():
    therapies = recommend_non_statin_therapies("low", 120, 130)
    assert len(therapies) == 0


# --- generateDyslipidemiaPlan (assess) ---


def test_plan_secondary_prevention():
    plan = assess(_patient(priorMI=True))
    assert plan["preventionCategory"] == "secondary"
    assert plan["riskLevel"] == "very-high"
    assert plan["ldlCGoal"] == 55
    assert plan["statinIntensity"] == "high"
    assert "ASCVD" in plan["reasoning"]


def test_plan_severe_hypercholesterolemia():
    plan = assess(_patient(lipidPanel={"ldlC": 250}))
    assert plan["riskLevel"] == "very-high"
    assert plan["ldlCGoal"] == 55
    assert "Severe hypercholesterolemia" in plan["reasoning"]


def test_plan_diabetic_patient():
    plan = assess(_patient(diabetic=True, age=50))
    assert plan["preventionCategory"] == "primary"
    assert "Diabetic" in plan["reasoning"]


def test_plan_lpa_recommendation_when_elevated():
    plan = assess(_patient(lipidPanel={"lpa": 100}))
    assert plan["lipaRecommendation"] is not None
    assert "Lp(a)" in plan["lipaRecommendation"]


def test_plan_monitoring_interval():
    plan = assess(_patient(priorMI=True))
    assert plan["monitoringInterval"] == "4-12 weeks"


# --- flat submission keys (the real seeded form) ---


def test_plan_flat_secondary_prevention():
    plan = assess(_flat(_patient(priorMI=True)))
    assert plan["preventionCategory"] == "secondary"
    assert plan["riskLevel"] == "very-high"
    assert plan["ldlCGoal"] == 55
    assert plan["statinIntensity"] == "high"


def test_plan_flat_lipids_are_read():
    # ldlC 250 via flat keys must trigger severe-hypercholesterolemia path,
    # proving the engine reads the flat lipid fields (regression guard).
    plan = assess(_flat(_patient(lipidPanel={"ldlC": 250})))
    assert plan["riskLevel"] == "very-high"
    assert "Severe hypercholesterolemia" in plan["reasoning"]
    assert "250" in plan["reasoning"]


# --- ASCVD numeric path + reasoning float formatting ---


def test_calculate_ascvd_risk_value():
    # male age 55, TC 250, HDL 40: (55-45)*.5 + (250-170)*.02 - (40-50)*.03
    #  = 5 + 1.6 + 0.3 = 6.9 (IEEE-754: 6.8999999999999995, same as JS)
    assert calculate_ascvd_risk(_patient()) == 6.8999999999999995


def test_plan_primary_moderate_path_reasoning():
    plan = assess(_flat(_patient()))
    assert plan["preventionCategory"] == "primary"
    assert plan["riskLevel"] == "moderate"
    assert plan["ldlCGoal"] == 100
    assert "10-year ASCVD risk ~6.9%" in plan["reasoning"]
    assert plan["monitoringInterval"] == "3-6 months"


def test_plan_no_lpa_recommendation_when_absent():
    assert assess(_flat(_patient()))["lipaRecommendation"] is None
