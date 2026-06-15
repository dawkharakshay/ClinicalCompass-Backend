"""Tests for the Functional Seizures (PNES) engine.

Cases ported 1:1 from old_static_code/server/neuro-ophtho.test.ts
("Functional Seizures (PNES) Logic" describe block), plus an
edge/contraindication path.
"""

from app.recommendations.modules.functionalseizures import assess


def _base(**overrides) -> dict:
    data = {
        "diagnosticCertainty": "definite",
        "veegPerformed": True,
        "veegResult": "pnes_confirmed",
        "semiology": "motor_thrashing",
        "hasCoOccurringEpilepsy": False,
        "epilepsySeizureType": "",
        "psychiatricComorbidity": "none",
        "hasOtherFunctionalNeurologicSymptoms": False,
        "currentlyOnAntiseizureMeds": False,
        "antiseizureMedsForFunctionalOnly": False,
        "currentlyInPsychotherapy": False,
        "psychotherapyType": "none",
        "patientAgeYears": 32,
        "isPediatric": False,
        "diagnosisDelayYears": 2,
        "hasEmergencyPresentations": False,
        "familyInvolvedInCare": False,
    }
    data.update(overrides)
    return data


def test_recommends_cbt_first_line_for_definite_pnes_confirmed_by_veeg():
    result = assess(_base())
    assert "Cognitive Behavioral Therapy" in result["primaryRecommendation"]
    assert "CBT" in result["treatmentPathway"]
    assert len(result["references"]) > 0


def test_flags_antiseizure_meds_without_cooccurring_epilepsy_as_urgent():
    result = assess(
        _base(
            currentlyOnAntiseizureMeds=True,
            antiseizureMedsForFunctionalOnly=True,
        )
    )
    assert any("Antiseizure medications" in f for f in result["urgentFlags"])
    assert any("Do NOT prescribe" in m for m in result["medicationGuidance"])


def test_flags_recurrent_ed_presentations_as_urgent():
    result = assess(_base(hasEmergencyPresentations=True))
    assert any("ED" in f for f in result["urgentFlags"])


def test_flags_long_diagnosis_delay_as_urgent():
    result = assess(_base(diagnosisDelayYears=8))
    assert any("8 years" in f for f in result["urgentFlags"])


def test_recommends_veeg_when_not_yet_performed():
    result = assess(
        _base(
            veegPerformed=False,
            veegResult="not_done",
            diagnosticCertainty="possible",
        )
    )
    assert "VEEG" in result["diagnosticPlan"]
    assert any("VEEG" in s for s in result["nextSteps"])


def test_adds_pediatric_neurology_referral_for_pediatric_patients():
    result = assess(_base(isPediatric=True, patientAgeYears=14))
    assert any("Pediatric" in r for r in result["multidisciplinaryReferrals"])


def test_adds_psychiatric_referral_when_comorbidity_present():
    result = assess(_base(psychiatricComorbidity="ptsd"))
    assert any("Psychiatry" in r for r in result["multidisciplinaryReferrals"])


def test_returns_evidence_level_and_references():
    result = assess(_base())
    assert "Level B" in result["evidenceLevel"]
    assert len(result["references"]) > 0
    assert result["references"][0].get("pmid") is not None


# ─── Edge / additional decision-path coverage ────────────────────────────────


def test_long_delay_renders_integer_without_trailing_decimal():
    result = assess(_base(diagnosisDelayYears=8))
    flag = next(f for f in result["urgentFlags"] if "Diagnosis delayed" in f)
    assert "8 years" in flag
    assert "8.0 years" not in flag


def test_cooccurring_epilepsy_changes_medication_and_monitoring():
    result = assess(_base(hasCoOccurringEpilepsy=True, veegResult="epilepsy_confirmed"))
    assert any("Co-occurring epilepsy present" in m for m in result["medicationGuidance"])
    assert any("Monitor both seizure types" in m for m in result["monitoringPlan"])
    assert any("Epilepsy clinic follow-up" in s for s in result["nextSteps"])
    # No "Do NOT prescribe" guidance when epilepsy co-occurs.
    assert not any("Do NOT prescribe" in m for m in result["medicationGuidance"])


def test_probable_certainty_proceeds_with_psychotherapy():
    result = assess(_base(diagnosticCertainty="probable", veegResult="non_diagnostic"))
    assert "Probable PNES" in result["primaryRecommendation"]
    assert "probable PNES" in result["treatmentPathway"]


def test_insufficient_certainty_requires_workup():
    result = assess(_base(diagnosticCertainty="possible", veegResult="not_done"))
    assert "Diagnostic workup required" in result["primaryRecommendation"]


def test_evidence_level_upgraded_for_pnes_cbt_combination():
    result = assess(_base(psychotherapyType="cbt", currentlyInPsychotherapy=True))
    assert "CODES RCT" in result["evidenceLevel"]
    assert "Currently receiving CBT" in result["psychotherapyRecommendation"]
