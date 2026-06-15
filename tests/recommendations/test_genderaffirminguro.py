"""Tests for the Gender-Affirming Urologic Procedures port.

Oracle: the inline ``evaluate()`` in
old_static_code/client/src/pages/GenderAffirmingUroCompass.tsx. No TS unit test
exists for this module, so fixtures are derived from the TS branches and cover
each major decision path plus the hormone-therapy and minor edge cases.
"""

from app.recommendations.modules.genderaffirminguro import assess


def _fully_met_orchiectomy() -> dict:
    """An adult, non-hormone-requiring procedure (orchiectomy) with all criteria
    met and the two-letter requirement satisfied — should be 'indicated'."""
    return {
        "genderIdentity": "trans_woman",
        "proposedProcedure": "orchiectomy",
        "patientAge": 32,
        "diagnosisGenderDysphoria": True,
        "persistentDysphoria": True,
        "durationMonths": 24,
        "mentalHealthEvaluation": True,
        "mentalHealthClearance": True,
        "hormoneTherapyMonths": 0,
        "hormoneTherapyContraindicated": False,
        "realLifeExperienceMonths": 18,
        "comorbidMentalHealthTreated": True,
        "informedConsent": True,
        "twoLettersObtained": True,
    }


def test_indicated_non_hormone_procedure_all_met():
    r = assess(_fully_met_orchiectomy())
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Orchiectomy"
    assert r["missingCriteria"] == []
    # No hormone criterion appended for orchiectomy.
    assert "Persistent gender dysphoria for 24 months" in r["metCriteria"]
    assert "Gender dysphoria diagnosis documented" in r["metCriteria"]
    assert "Mental health evaluation with surgical clearance obtained" in r["metCriteria"]
    assert "Comorbid mental health conditions treated/stable" in r["metCriteria"]
    assert "Informed consent documented" in r["metCriteria"]
    # twoLetters satisfied -> rationale entry, no two-letter warning, adult -> no minor warning.
    assert r["warnings"] == []
    assert any("Two letters of support" in s for s in r["rationale"])
    assert len(r["references"]) == 5


def test_hormone_procedure_twelve_months_met():
    data = _fully_met_orchiectomy()
    data["proposedProcedure"] = "vaginoplasty"
    data["hormoneTherapyMonths"] = 14
    r = assess(data)
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Vaginoplasty"
    assert "14 months of hormone therapy completed" in r["metCriteria"]
    assert r["missingCriteria"] == []


def test_hormone_procedure_insufficient_months_not_indicated():
    data = _fully_met_orchiectomy()
    data["proposedProcedure"] = "phalloplasty"
    data["hormoneTherapyMonths"] = 6
    r = assess(data)
    assert r["recommendation"] == "not_yet_indicated"
    assert r["procedure"] == "Phalloplasty"
    assert (
        "≥12 months of hormone therapy required before genital surgery (WPATH SOC-8)"
        in r["missingCriteria"]
    )


def test_hormone_contraindicated_exception():
    data = _fully_met_orchiectomy()
    data["proposedProcedure"] = "metoidioplasty"
    data["hormoneTherapyMonths"] = 0
    data["hormoneTherapyContraindicated"] = True
    r = assess(data)
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Metoidioplasty"
    assert "Hormone therapy contraindicated — documented exception" in r["metCriteria"]
    assert r["missingCriteria"] == []


def test_persistent_dysphoria_requires_six_months():
    data = _fully_met_orchiectomy()
    data["durationMonths"] = 5  # < 6 -> not met
    r = assess(data)
    assert r["recommendation"] == "not_yet_indicated"
    assert "Persistent, well-documented gender dysphoria required" in r["missingCriteria"]
    assert not any("Persistent gender dysphoria for" in s for s in r["metCriteria"])


def test_minor_warning_and_two_letter_warning():
    data = _fully_met_orchiectomy()
    data["patientAge"] = 16
    data["twoLettersObtained"] = False
    r = assess(data)
    # Minor warning is pushed before the two-letter warning.
    assert r["warnings"][0].startswith("Patient is a minor")
    assert any("Most payers require 2 letters" in s for s in r["warnings"])
    assert not any("Two letters of support" in s for s in r["rationale"])


def test_all_criteria_missing_underscore_procedure_titlecase():
    data = {
        "genderIdentity": "trans_man",
        "proposedProcedure": "hysterectomy_oophorectomy",
        "patientAge": 0,
        "diagnosisGenderDysphoria": False,
        "persistentDysphoria": False,
        "durationMonths": 0,
        "mentalHealthEvaluation": False,
        "mentalHealthClearance": False,
        "hormoneTherapyMonths": 0,
        "hormoneTherapyContraindicated": False,
        "realLifeExperienceMonths": 0,
        "comorbidMentalHealthTreated": False,
        "informedConsent": False,
        "twoLettersObtained": False,
    }
    r = assess(data)
    assert r["recommendation"] == "not_yet_indicated"
    # Underscore -> space, each word capitalized.
    assert r["procedure"] == "Hysterectomy Oophorectomy"
    # Five core criteria missing (hysterectomy is not hormone-requiring).
    assert "Gender dysphoria diagnosis required (DSM-5 F64.0 or ICD-11 HA60)" in r["missingCriteria"]
    assert "Persistent, well-documented gender dysphoria required" in r["missingCriteria"]
    assert "Mental health evaluation and clearance required" in r["missingCriteria"]
    assert "Comorbid mental health conditions must be stable before surgery" in r["missingCriteria"]
    assert "Informed consent process required" in r["missingCriteria"]
    assert len(r["missingCriteria"]) == 5
    assert r["metCriteria"] == []
    # Age 0 (default) < 18 -> minor warning fires.
    assert any("Patient is a minor" in s for s in r["warnings"])
