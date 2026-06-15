"""ESI engine — fixtures derived directly from epiduralSteroidLogic.ts branches."""

from app.recommendations.modules.epiduralsteroid import assess


def _base() -> dict:
    return {
        "age": "55",
        "spineRegion": "lumbar",
        "approachType": "transforaminal",
        "symptomDurationWeeks": "0",
        "painScore": "0",
        "symptoms": [],
        "conservativeTherapyWeeks": "0",
        "conservativeTherapies": [],
        "imagingFindings": [],
        "activeInfection": False,
        "coagulopathy": False,
        "allergy": False,
        "priorInjectionResponse": "",
        "priorInjectionCount": "0",
    }


def test_contraindication_wins():
    r = assess({**_base(), "coagulopathy": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "ESI Contraindicated"
    assert any("coagulopathy" in c for c in r["contraindications"])
    assert "Bridge anticoagulation per procedural guidelines" in r["optimizationSteps"]


def test_frequency_limit_reached():
    r = assess({**_base(), "priorInjectionCount": "3"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Frequency Limit Reached"
    assert r["recommendation"] == "Frequency Limit — Consider Alternatives"
    assert r["loe"] == "B"
    assert any("3 injections per region" in s for s in r["rationale"])


def test_class_i_radicular_disc_herniation():
    r = assess({
        **_base(),
        "symptoms": ["radicular-pain"],
        "imagingFindings": ["disc-herniation"],
        "conservativeTherapyWeeks": "4",
    })
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "ESI Recommended"
    assert r["loe"] == "A"  # disc herniation present


def test_class_iia_stenosis_with_claudication():
    r = assess({
        **_base(),
        "symptoms": ["neurogenic-claudication"],
        "imagingFindings": ["central-stenosis"],
        "conservativeTherapyWeeks": "6",
    })
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["recommendation"] == "ESI Reasonable"
    assert r["loe"] == "B"  # no disc herniation


def test_class_iia_foraminal_stenosis_with_radicular():
    r = assess({
        **_base(),
        "symptoms": ["radicular-pain"],
        "imagingFindings": ["foraminal-stenosis"],
        "conservativeTherapyWeeks": "4",
    })
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"


def test_continue_conservative_when_weeks_insufficient():
    r = assess({
        **_base(),
        "symptoms": ["radicular-pain"],
        "imagingFindings": ["disc-herniation"],
        "conservativeTherapyWeeks": "2",
    })
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert r["recommendation"] == "Continue Conservative Therapy"
    assert any("≥4 weeks" in s for s in r["optimizationSteps"])


def test_insufficient_criteria_branch():
    # conservWeeks >= 4 but no qualifying symptoms/imaging
    r = assess({**_base(), "conservativeTherapyWeeks": "6"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    assert r["recommendation"] == "Continue Conservative Therapy"
    assert any("Obtain MRI" in s for s in r["optimizationSteps"])


def test_prior_response_good_and_severe_pain_rationale():
    r = assess({
        **_base(),
        "symptoms": ["radicular-pain"],
        "imagingFindings": ["disc-herniation"],
        "conservativeTherapyWeeks": "4",
        "priorInjectionResponse": "good",
        "painScore": "9",
    })
    assert r["cor"] == "I"
    assert any("Prior ESI response was good" in s for s in r["rationale"])
    assert any("Severe pain (NRS ≥8)" in s for s in r["rationale"])


def test_prior_response_none_adds_optimization():
    r = assess({**_base(), "conservativeTherapyWeeks": "6", "priorInjectionResponse": "none"})
    assert any("no response" in s for s in r["optimizationSteps"])


def test_frequency_limit_takes_precedence_over_class_i():
    # priorCount >= 3 short-circuits even with class-I qualifying inputs
    r = assess({
        **_base(),
        "priorInjectionCount": "4",
        "symptoms": ["radicular-pain"],
        "imagingFindings": ["disc-herniation"],
        "conservativeTherapyWeeks": "8",
    })
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Frequency Limit Reached"
    # loe still reflects disc herniation
    assert r["loe"] == "A"
