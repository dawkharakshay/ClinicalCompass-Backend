"""Tests for the Gastroparesis Clinical Compass port.

Cases 1:1 from old_static_code/server/gi-modules.test.ts
(describe "assessGastroparesis"), plus edge/contraindication paths derived
from the TypeScript branches.
"""

import re

from app.recommendations.modules.gastroparesis import assess

# Mirrors baseInput in gi-modules.test.ts. Note diagnosticStatus and
# isOnProkinetics deliberately use the legacy test's values (which fall through
# to the default branches in the TS engine).
BASE_INPUT = {
    "diagnosticStatus": "confirmed_4h_ges",
    "gastricRetentionPercent4h": 38,
    "hasNausea": True,
    "hasVomiting": True,
    "hasEarlyFullness": True,
    "hasPostprandialFullness": True,
    "hasAbdominalPain": False,
    "etiology": "diabetic",
    "hasType1Diabetes": True,
    "hasType2Diabetes": False,
    "hba1cPercent": 9.2,
    "hasPriorGastricSurgery": False,
    "severity": "moderate",
    "hasHospitalizationsInPastYear": False,
    "hasWeightLoss": True,
    "weightLossKg": 5,
    "hasDehydration": False,
    "requiresNutritionalSupport": False,
    "isOnMetoclopramide": False,
    "isOnDomperidone": False,
    "isOnErythromycin": False,
    "isOnProkinetics": False,
    "hasTriedDietaryModification": True,
    "ageYears": 45,
    "isSurgicalCandidate": True,
}


def test_dietary_and_prokinetic_for_moderate_diabetic():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"]
    assert result["dietaryModification"]
    assert re.match(r"^[ABC]$", result["evidenceLevel"])


def test_glycemic_optimization_for_diabetic():
    result = assess(BASE_INPUT)
    pat = re.compile(r"glycemi|HbA1c|diabetes", re.IGNORECASE)
    assert any(pat.search(f) for f in result["urgentFlags"]) or pat.search(
        result["primaryRecommendation"]
    )


def test_severe_flags_hospitalization():
    result = assess(
        {
            **BASE_INPUT,
            "severity": "severe",
            "hasDehydration": True,
            "requiresNutritionalSupport": True,
            "hasHospitalizationsInPastYear": True,
        }
    )
    assert len(result["urgentFlags"]) > 0 or re.search(
        r"hospital|IV|nutrition", result["primaryRecommendation"], re.IGNORECASE
    )


def test_returns_references():
    result = assess(BASE_INPUT)
    assert len(result["references"]) > 0


# ─── Edge / branch coverage derived from the TS source ────────────────────────


def test_not_tested_requires_4h_ges():
    result = assess({**BASE_INPUT, "diagnosticStatus": "not_tested"})
    assert "4-hour gastric emptying scintigraphy required for diagnosis" in (
        result["primaryRecommendation"]
    )
    assert "4-hour gastric emptying scintigraphy (standardized protocol)" in (
        result["nextSteps"]
    )
    # None of the nextSteps strings contain the substring "GES", so the default
    # nextSteps block IS appended (matches TS: !nextSteps.some(s => s.includes('GES'))).
    assert "Gastroenterology/motility specialist referral" in result["nextSteps"]


def test_ges_4h_confirmed_branch():
    result = assess({**BASE_INPUT, "diagnosticStatus": "ges_4h_confirmed"})
    assert "4-hour GES confirmed gastroparesis (38% retention at 4h)" in (
        result["diagnosticPlan"]
    )


def test_ges_4h_confirmed_missing_retention_uses_question_mark():
    inp = {**BASE_INPUT, "diagnosticStatus": "ges_4h_confirmed"}
    del inp["gastricRetentionPercent4h"]
    result = assess(inp)
    assert "(?% retention at 4h)" in result["diagnosticPlan"]


def test_opioids_flag_and_avoid():
    result = assess({**BASE_INPUT, "isOnOpioids": True})
    assert any("OPIOIDS" in f for f in result["urgentFlags"])
    assert any("Opioids" in m for m in result["medicationsToAvoid"])


def test_tardive_dyskinesia_contraindicates_metoclopramide():
    result = assess({**BASE_INPUT, "hasTardivedyskinesia": True})
    assert any("Tardive dyskinesia" in f for f in result["urgentFlags"])
    assert any("contraindicated with tardive dyskinesia" in m for m in result["medicationsToAvoid"])
    # Metoclopramide should NOT be recommended.
    assert not any("Metoclopramide 5" in a for a in result["recommendedAgents"])


def test_qt_prolongation_excludes_domperidone_recommendation():
    result = assess({**BASE_INPUT, "hasQTProlongation": True})
    assert any("QT prolongation" in f for f in result["urgentFlags"])
    assert not any("Domperidone 10mg" in a for a in result["recommendedAgents"])


def test_weight_loss_over_5_flags_when_nutritional_support():
    result = assess({**BASE_INPUT, "requiresNutritionalSupport": True, "weightLossKg": 8})
    assert any("Significant weight loss (8kg)" in f for f in result["urgentFlags"])


def test_weight_loss_exactly_5_not_flagged():
    # weightLossKg > 5 required; 5 is not flagged.
    result = assess({**BASE_INPUT, "requiresNutritionalSupport": True, "weightLossKg": 5})
    assert not any("Significant weight loss" in f for f in result["urgentFlags"])


def test_severe_triggers_interventional_options():
    result = assess({**BASE_INPUT, "severity": "severe"})
    assert "INTERVENTIONAL OPTIONS for refractory/severe gastroparesis" in (
        result["interventionalOptions"]
    )
    assert any("G-POEM" in a for a in result["recommendedAgents"])


def test_on_prokinetic_non_mild_uses_alt_pharmacotherapy():
    result = assess({**BASE_INPUT, "isOnProkinetic": True, "severity": "moderate"})
    assert result["pharmacotherapy"].startswith("Currently on prokinetic therapy")


def test_hba1c_at_threshold_not_flagged():
    # hba1cPercent > 9 required; exactly 9 is not flagged.
    result = assess({**BASE_INPUT, "hba1cPercent": 9})
    assert not any("Poorly controlled diabetes" in f for f in result["urgentFlags"])
