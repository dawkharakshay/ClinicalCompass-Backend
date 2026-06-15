"""Tests for the CCM (Cerebral Cavernous Malformation) compass.

Oracle cases ported 1:1 from
old_static_code/server/neurosurgery.test.ts ("Cerebral Cavernous Malformation Logic"),
plus additional fixtures covering each major decision branch.
"""

from app.recommendations.modules.ccm import assess


# ─── Oracle cases (ported 1:1 from neurosurgery.test.ts) ───────────────────────


def test_observation_incidental_noneloquent_no_hemorrhage():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "noneloquent_cortical",
            "cmSizeCm": 1.0,
            "associatedDVA": False,
            "multiplelesions": False,
            "symptomatic": False,
            "hemorrhageStatus": "no_hemorrhage",
            "seizureStatus": "no_seizure",
            "neurologicDeficit": False,
            "headacheOnly": False,
            "incidentalFinding": True,
            "familyHistory": False,
            "priorSurgery": False,
            "priorSRS": False,
            "priorASM": False,
            "ageYears": 45,
            "pregnancyPlanned": False,
        }
    )
    assert result["primaryRecommendation"] == "observation"


def test_surgery_brainstem_recurrent_hemorrhage():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "brainstem",
            "cmSizeCm": 1.5,
            "associatedDVA": False,
            "multiplelesions": False,
            "symptomatic": True,
            "hemorrhageStatus": "recurrent_hemorrhage",
            "seizureStatus": "no_seizure",
            "neurologicDeficit": True,
            "headacheOnly": False,
            "incidentalFinding": False,
            "familyHistory": False,
            "priorSurgery": False,
            "priorSRS": False,
            "priorASM": False,
            "ageYears": 38,
            "pregnancyPlanned": False,
        }
    )
    assert result["primaryRecommendation"] == "surgical_resection"
    assert len(result["urgentFlags"]) > 0


def test_genetic_testing_familial():
    result = assess(
        {
            "ccmType": "familial",
            "location": "noneloquent_cortical",
            "cmSizeCm": 0.8,
            "associatedDVA": False,
            "multiplelesions": True,
            "symptomatic": False,
            "hemorrhageStatus": "no_hemorrhage",
            "seizureStatus": "no_seizure",
            "neurologicDeficit": False,
            "headacheOnly": False,
            "incidentalFinding": True,
            "familyHistory": True,
            "priorSurgery": False,
            "priorSRS": False,
            "priorASM": False,
            "ageYears": 32,
            "pregnancyPlanned": False,
        }
    )
    assert len(result["geneticCounseling"]) > 0


def test_asm_for_refractory_seizures():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "eloquent_cortical",
            "cmSizeCm": 2.0,
            "associatedDVA": False,
            "multiplelesions": False,
            "symptomatic": True,
            "hemorrhageStatus": "single_hemorrhage",
            "seizureStatus": "refractory_seizure",
            "neurologicDeficit": False,
            "headacheOnly": False,
            "incidentalFinding": False,
            "familyHistory": False,
            "priorSurgery": False,
            "priorSRS": False,
            "priorASM": True,
            "asmResponse": "refractory",
            "ageYears": 40,
            "pregnancyPlanned": False,
        }
    )
    # seizureManagement is in medicalManagement for CCM
    assert len(result["medicalManagement"]) > 0


# ─── Additional branch coverage ────────────────────────────────────────────────


def test_genetic_testing_first_returns_when_no_known_variant():
    # familial + no knownCCMGeneVariant -> genetic_testing_first
    result = assess(
        {
            "ccmType": "familial",
            "location": "noneloquent_cortical",
            "hemorrhageStatus": "no_hemorrhage",
            "seizureStatus": "no_seizure",
            "symptomatic": True,  # not asymptomatic -> falls past asymptomatic block
        }
    )
    assert result["primaryRecommendation"] == "genetic_testing_first"
    assert result["evidenceClass"] == "IIa"


def test_familial_with_known_variant_does_not_short_circuit_genetic():
    # familial but knownCCMGeneVariant set -> skip genetic_testing_first.
    # symptomatic noneloquent -> surgical_resection.
    result = assess(
        {
            "ccmType": "familial",
            "knownCCMGeneVariant": "ccm1",
            "location": "noneloquent_cortical",
            "hemorrhageStatus": "single_hemorrhage",
            "seizureStatus": "controlled_seizure",
            "symptomatic": True,
        }
    )
    assert result["primaryRecommendation"] == "surgical_resection"
    assert result["recommendationTitle"] == "Surgical Resection — Symptomatic Accessible CCM"


def test_asymptomatic_eloquent_observation_class_iii():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "eloquent_cortical",
            "hemorrhageStatus": "no_hemorrhage",
            "seizureStatus": "no_seizure",
            "symptomatic": False,
            "incidentalFinding": True,
        }
    )
    assert result["primaryRecommendation"] == "observation"
    assert result["evidenceClass"] == "III"


def test_ccm3_warning_appears_in_asymptomatic_eloquent():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "deep_subcortical",
            "knownCCMGeneVariant": "ccm3",
            "hemorrhageStatus": "no_hemorrhage",
            "seizureStatus": "no_seizure",
            "symptomatic": False,
            "incidentalFinding": True,
        }
    )
    assert result["primaryRecommendation"] == "observation"
    assert any("CCM3 mutation: Higher hemorrhage rate" in w for w in result["warnings"])


def test_asymptomatic_noneloquent_observation_surgery_may_be_considered():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "noneloquent_cortical",
            "hemorrhageStatus": "no_hemorrhage",
            "seizureStatus": "no_seizure",
            "symptomatic": False,
            "incidentalFinding": True,
        }
    )
    assert result["primaryRecommendation"] == "observation"
    assert result["evidenceClass"] == "IIb"
    assert any("easily accessible noneloquent" in s for s in result["surgicalConsiderations"])


def test_radiosurgery_eloquent_high_risk_prior_hemorrhage():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "eloquent_cortical",
            "hemorrhageStatus": "single_hemorrhage",
            "seizureStatus": "controlled_seizure",
            "symptomatic": True,
            "surgicalRisk": "high",
        }
    )
    assert result["primaryRecommendation"] == "radiosurgery_srs"
    assert result["evidenceClass"] == "IIb"


def test_default_observation_active_surveillance():
    # symptomatic eloquent, hemorrhage, but surgicalRisk not high -> default observation
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "eloquent_cortical",
            "hemorrhageStatus": "single_hemorrhage",
            "seizureStatus": "controlled_seizure",
            "symptomatic": True,
            "surgicalRisk": "moderate",
        }
    )
    assert result["primaryRecommendation"] == "observation"
    assert result["recommendationTitle"] == "Observation — Active Surveillance"


def test_urgent_flag_spinal_acute_impairment():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "spinal_dorsal_dorsolateral",
            "hemorrhageStatus": "single_hemorrhage",
            "seizureStatus": "no_seizure",
            "symptomatic": True,
            "spinalCM": True,
            "acuteNeurologicImpairment": True,
            "progressiveNeurologicDeterioration": True,
        }
    )
    assert result["primaryRecommendation"] == "surgical_resection"
    assert any("Acute spinal CM hemorrhage" in f for f in result["urgentFlags"])
    assert any(
        "Single acute neurological impairing event" in s
        for s in result["surgicalConsiderations"]
    )
    assert any(
        "Progressive neurological deterioration" in s
        for s in result["surgicalConsiderations"]
    )


def test_headache_only_medical_management():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "eloquent_cortical",
            "hemorrhageStatus": "single_hemorrhage",
            "seizureStatus": "controlled_seizure",
            "symptomatic": False,
            "headacheOnly": True,
            "incidentalFinding": False,
        }
    )
    # asymptomatic eloquent block fires (symptomatic False) -> observation,
    # but medicalManagement carries the headache guidance forward.
    assert any("standard headache practice" in m for m in result["medicalManagement"])


def test_pregnancy_warnings_and_folate():
    result = assess(
        {
            "ccmType": "sporadic",
            "location": "noneloquent_cortical",
            "hemorrhageStatus": "single_hemorrhage",
            "seizureStatus": "controlled_seizure",
            "symptomatic": True,
            "pregnancyStatus": True,
        }
    )
    assert any("Pregnancy:" in w for w in result["warnings"])
    assert any("Folate supplementation" in m for m in result["medicalManagement"])
