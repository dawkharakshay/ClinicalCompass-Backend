"""Tests for the OSA Clinical Compass port.

Cases ported 1:1 from old_static_code/server/new-modules.test.ts ("OSA Logic"),
plus branch-coverage fixtures derived from the TS decision tree.
"""

from __future__ import annotations

from app.recommendations.modules.osa import (
    assess,
    classify_osa_severity,
    is_hns_eligible,
)

BASE = {
    "ahi": 22,
    "odiLevel": 18,
    "minO2Sat": 85,
    "cpapAdherence": "naive",
    "cpapTrialDuration": 0,
    "ess": 13,
    "snoring": True,
    "witnessedApneas": True,
    "nocturia": False,
    "morningHeadaches": False,
    "hypertension": True,
    "afib": False,
    "heartFailure": False,
    "stroke": False,
    "t2dm": False,
    "depression": False,
    "bmi": 31,
    "neckCircumference": 42,
    "anatomicObstruction": "palatal",
    "tonsilSize": 2,
    "mallampatiScore": 2,
    "priorUPPP": False,
    "priorNasalSurgery": False,
    "age": 50,
    "sex": "male",
    "pregnant": False,
    "patientPrefersSurgery": False,
    "patientPrefersMedical": False,
    "positionalOSA": False,
    "centralComponent": False,
}


# ── Ported 1:1 from new-modules.test.ts ──────────────────────────────────────

def test_classifies_ahi_22_as_moderate():
    assert classify_osa_severity(22) == "moderate"


def test_classifies_ahi_8_as_mild():
    assert classify_osa_severity(8) == "mild"


def test_classifies_ahi_45_as_severe():
    assert classify_osa_severity(45) == "severe"


def test_cpap_first_line_for_cpap_naive_moderate():
    result = assess(dict(BASE))
    assert result["primaryTreatment"] == "cpap_first_line"
    assert result["evidenceLevel"] is not None


def test_alternative_to_cpap_for_cpap_intolerant_moderate():
    result = assess({**BASE, "cpapAdherence": "intolerant", "cpapTrialDuration": 3})
    assert result["primaryTreatment"] != "cpap_first_line"


def test_hns_ineligible_for_cpap_naive():
    hns = is_hns_eligible({**BASE, "ahi": 35, "centralComponent": False, "cpapAdherence": "naive"})
    assert hns["eligible"] is False
    assert any(
        ("CPAP naive" in c) or ("CPAP trial" in c) for c in hns["contraindications"]
    )


def test_hns_eligible_for_cpap_intolerant_ahi_35():
    hns = is_hns_eligible(
        {**BASE, "ahi": 35, "centralComponent": False, "cpapAdherence": "intolerant", "bmi": 28}
    )
    assert hns["eligible"] is True


def test_hns_ineligible_for_central_predominant():
    hns = is_hns_eligible({**BASE, "centralComponent": True})
    assert hns["eligible"] is False


def test_returns_keywarnings_and_nextsteps_arrays():
    result = assess(dict(BASE))
    assert isinstance(result["keyWarnings"], list)
    assert isinstance(result["nextSteps"], list)
    assert len(result["nextSteps"]) >= 1


# ── Branch-coverage fixtures from the TS decision tree ───────────────────────

def test_mild_low_symptom_weight_loss():
    result = assess({**BASE, "ahi": 8, "ess": 5, "hypertension": False})
    assert result["primaryTreatment"] == "weight_loss"
    assert result["evidenceLevel"] == "Moderate"


def test_mild_low_symptom_positional_therapy():
    result = assess({**BASE, "ahi": 8, "ess": 5, "hypertension": False, "positionalOSA": True})
    assert result["primaryTreatment"] == "positional_therapy"
    assert result["primaryLabel"] == "Positional Therapy + Lifestyle Modification"


def test_cpap_adherent_optimization():
    result = assess({**BASE, "cpapAdherence": "adherent"})
    assert result["primaryTreatment"] == "cpap_optimization"
    assert result["oralApplianceSuitable"] is False


def test_hns_inspire_cpap_intolerant_moderate():
    # AHI 22 (moderate, oral appliance suitable since <=30) -> alt treatments include oral_appliance
    result = assess({**BASE, "cpapAdherence": "intolerant", "bmi": 28})
    assert result["primaryTreatment"] == "hns_inspire"
    assert result["hnsEligible"] is True
    assert "oral_appliance" in result["alternativeTreatments"]


def test_hns_inspire_severe_intolerant_oral_alts():
    # severe + intolerant -> oral appliance suitable (intolerant), HNS primary,
    # alternatives include oral_appliance + surgical_uppp
    result = assess({**BASE, "ahi": 40, "cpapAdherence": "intolerant", "bmi": 28})
    assert result["primaryTreatment"] == "hns_inspire"
    assert result["alternativeTreatments"] == ["oral_appliance", "surgical_uppp"]


def test_oral_appliance_when_hns_ineligible_high_bmi():
    # bmi >=40 -> hns ineligible; moderate + oral suitable -> oral_appliance
    result = assess({**BASE, "ahi": 22, "cpapAdherence": "intolerant", "bmi": 42})
    assert result["primaryTreatment"] == "oral_appliance"
    assert result["oralApplianceSuitable"] is True


def test_surgical_tonsillectomy_palatal_large_tonsils():
    # hns ineligible (bmi 42), severe so oral not suitable, palatal + tonsil>=3
    result = assess(
        {
            **BASE,
            "ahi": 40,
            "cpapAdherence": "intolerant",
            "bmi": 42,
            "anatomicObstruction": "palatal",
            "tonsilSize": 3,
        }
    )
    assert result["primaryTreatment"] == "surgical_tonsillectomy"


def test_surgical_mma_retrognathia():
    # retrognathia -> oral not suitable, hns ineligible due to central? no.
    # severe ahi so oral not suitable; hns ineligible because... use prior UPPP path.
    result = assess(
        {
            **BASE,
            "ahi": 40,
            "cpapAdherence": "intolerant",
            "bmi": 42,
            "anatomicObstruction": "retrognathia",
        }
    )
    assert result["primaryTreatment"] == "surgical_mma"


def test_combination_therapy_default():
    # non_adherent, severe, hns ineligible (bmi 42), no anatomic surgical path
    result = assess(
        {
            **BASE,
            "ahi": 40,
            "cpapAdherence": "non_adherent",
            "bmi": 42,
            "anatomicObstruction": "none_identified",
            "tonsilSize": 0,
            "priorUPPP": False,
        }
    )
    assert result["primaryTreatment"] == "combination_therapy"


def test_cv_risk_high_with_stroke():
    result = assess({**BASE, "stroke": True})
    assert result["cvRisk"] == "high"


def test_warnings_populated_for_afib_and_hypoxemia():
    result = assess({**BASE, "afib": True, "minO2Sat": 75})
    assert any("Atrial fibrillation" in w for w in result["keyWarnings"])
    assert any("hypoxemia" in w for w in result["keyWarnings"])
