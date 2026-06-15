"""Oracle tests for the Vestibular Schwannoma engine.

Cases ported 1:1 from old_static_code/server/neurosurgery.test.ts
("Vestibular Schwannoma Logic" describe block).
"""

from app.recommendations.modules.vestibularschwanoma import assess


def test_observation_small_intracanalicular_serviceable_hearing():
    data = {
        "tumorSizeClass": "intracanalicular",
        "tumorSizeCm": 0.8,
        "cysticComponent": False,
        "lateralIACInvolvement": False,
        "fundalCSFCap": True,
        "hearingClass": "class_a",
        "gardnerRobertsonGrade": "gr1",
        "serviceableHearing": True,
        "suddenSNHL": False,
        "asymmetricTinnitus": True,
        "asymmetricSNHL": False,
        "priorObservation": False,
        "tumorGrowthOnObservation": False,
        "ageYears": 55,
        "nf2Status": False,
        "contralateralHearingLoss": False,
        "trigeminalNeuralgiaSymptoms": False,
        "balanceProblems": False,
        "facialNerveFunctionHB": 1,
        "priorSRS": False,
        "priorSurgery": False,
        "hearingPreservationPriority": True,
        "preferMinimallyInvasive": False,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "observation_active_surveillance"


def test_srs_medium_non_serviceable_hearing():
    data = {
        "tumorSizeClass": "medium",
        "tumorSizeCm": 2.2,
        "cysticComponent": False,
        "lateralIACInvolvement": True,
        "fundalCSFCap": False,
        "hearingClass": "non_serviceable",
        "gardnerRobertsonGrade": "gr4",
        "serviceableHearing": False,
        "suddenSNHL": False,
        "asymmetricTinnitus": False,
        "asymmetricSNHL": True,
        "priorObservation": True,
        "tumorGrowthOnObservation": True,
        "observationDurationMonths": 18,
        "ageYears": 68,
        "nf2Status": False,
        "contralateralHearingLoss": False,
        "trigeminalNeuralgiaSymptoms": False,
        "balanceProblems": True,
        "facialNerveFunctionHB": 1,
        "priorSRS": False,
        "priorSurgery": False,
        "hearingPreservationPriority": False,
        "preferMinimallyInvasive": True,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "srs_gamma_knife"


def test_microsurgery_large_brainstem_compression():
    data = {
        "tumorSizeClass": "large",
        "tumorSizeCm": 3.8,
        "cysticComponent": False,
        "lateralIACInvolvement": True,
        "fundalCSFCap": False,
        "hearingClass": "non_serviceable",
        "gardnerRobertsonGrade": "gr5",
        "serviceableHearing": False,
        "suddenSNHL": False,
        "asymmetricTinnitus": False,
        "asymmetricSNHL": True,
        "priorObservation": False,
        "tumorGrowthOnObservation": False,
        "ageYears": 42,
        "nf2Status": False,
        "contralateralHearingLoss": False,
        "trigeminalNeuralgiaSymptoms": False,
        "balanceProblems": True,
        "facialNerveFunctionHB": 1,
        "priorSRS": False,
        "priorSurgery": False,
        "hearingPreservationPriority": False,
        "preferMinimallyInvasive": False,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "microsurgery_resection"
    assert len(result["urgentFlags"]) > 0


def test_nf2_multidisciplinary():
    data = {
        "tumorSizeClass": "small",
        "tumorSizeCm": 1.2,
        "cysticComponent": False,
        "lateralIACInvolvement": False,
        "fundalCSFCap": True,
        "hearingClass": "class_b",
        "gardnerRobertsonGrade": "gr2",
        "serviceableHearing": True,
        "suddenSNHL": False,
        "asymmetricTinnitus": True,
        "asymmetricSNHL": True,
        "priorObservation": False,
        "tumorGrowthOnObservation": False,
        "ageYears": 28,
        "nf2Status": True,
        "contralateralHearingLoss": True,
        "trigeminalNeuralgiaSymptoms": False,
        "balanceProblems": False,
        "facialNerveFunctionHB": 1,
        "priorSRS": False,
        "priorSurgery": False,
        "hearingPreservationPriority": True,
        "preferMinimallyInvasive": False,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "multidisciplinary_nf2"


def test_medium_serviceable_hearing_preservation_priority_srs():
    # Medium tumor, serviceable hearing, hearing preservation priority -> SRS branch
    data = {
        "tumorSizeClass": "medium",
        "tumorSizeCm": 2.0,
        "serviceableHearing": True,
        "hearingPreservationPriority": True,
        "nf2Status": False,
        "facialNerveFunctionHB": 1,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "srs_gamma_knife"


def test_medium_trigeminal_neuralgia_surgery():
    # Medium tumor, non-serviceable, trigeminal neuralgia -> surgery branch
    data = {
        "tumorSizeClass": "medium",
        "tumorSizeCm": 2.4,
        "serviceableHearing": False,
        "hearingPreservationPriority": False,
        "trigeminalNeuralgiaSymptoms": True,
        "nf2Status": False,
        "facialNerveFunctionHB": 1,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "microsurgery_resection"
    # surgicalNotes should carry the trigeminal note
    assert any("Trigeminal neuralgia" in n for n in result["surgicalNotes"])


def test_growing_small_tumor_defaults_to_srs():
    # Small tumor with documented growth, prior observation -> falls through to SRS
    data = {
        "tumorSizeClass": "small",
        "tumorSizeCm": 1.0,
        "serviceableHearing": False,
        "priorObservation": True,
        "tumorGrowthOnObservation": True,
        "nf2Status": False,
        "facialNerveFunctionHB": 1,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "srs_gamma_knife"
    assert any("Tumor growth documented" in w for w in result["warnings"])


def test_large_by_size_cm_only():
    # tumorSizeClass not "large" but tumorSizeCm > 3 triggers surgery pathway
    data = {
        "tumorSizeClass": "medium",
        "tumorSizeCm": 3.5,
        "serviceableHearing": False,
        "nf2Status": False,
        "facialNerveFunctionHB": 3,
    }
    result = assess(data)
    assert result["primaryRecommendation"] == "microsurgery_resection"
    # HB > 2 should add the compromised facial nerve warning
    assert any("HB >2" in w for w in result["warnings"])
