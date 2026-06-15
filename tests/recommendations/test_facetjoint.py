"""Facet Joint Injection engine — fixtures derived directly from facetJointLogic.ts branches."""

from app.recommendations.modules.facetjoint import assess


def _base() -> dict:
    return {
        "age": "55",
        "spineRegion": "lumbar",
        "procedureType": "facet-injection",
        "symptomDurationMonths": "6",
        "painScore": "5",
        "symptoms": [],
        "conservativeTherapyMonths": "0",
        "conservativeTherapies": [],
        "priorFacetResponse": "",
        "priorFacetCount": "0",
        "activeInfection": False,
        "coagulopathy": False,
        "allergy": False,
        "diagnosticBlockPositive": False,
    }


def test_active_infection_contraindicated():
    r = assess({**_base(), "activeInfection": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "Facet Injection Contraindicated"
    assert any("Active infection" in c for c in r["contraindications"])
    assert r["optimizationSteps"] == []


def test_coagulopathy_contraindicated():
    r = assess({**_base(), "coagulopathy": True})
    assert r["cor"] == "III"
    assert any("coagulopathy" in c for c in r["contraindications"])


def test_allergy_contraindicated():
    r = assess({**_base(), "allergy": True})
    assert r["cor"] == "III"
    assert any("Allergy" in c for c in r["contraindications"])


def test_multiple_contraindications_collected():
    r = assess({**_base(), "activeInfection": True, "coagulopathy": True, "allergy": True})
    assert len(r["contraindications"]) == 3


def test_frequency_limit_reached():
    r = assess({**_base(), "priorFacetCount": "3"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Frequency Limit Reached"
    assert r["recommendation"] == "Continue Conservative Therapy"
    assert any("3 per region per year" in s for s in r["rationale"])
    assert any("medial branch block" in s for s in r["optimizationSteps"])
    assert any("other pain generators" in s for s in r["optimizationSteps"])


def test_frequency_limit_precedes_mbb():
    # priorCount >= 3 takes precedence over a positive MBB path
    r = assess({**_base(), "priorFacetCount": "4", "procedureType": "medial-branch-block",
                "diagnosticBlockPositive": True})
    assert r["urgency"] == "Frequency Limit Reached"
    assert r["cor"] == "IIb"


def test_mbb_with_positive_diagnostic_block():
    r = assess({**_base(), "procedureType": "medial-branch-block",
                "diagnosticBlockPositive": True})
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "Facet Injection / MBB Recommended"
    assert any("Positive prior diagnostic block" in s for s in r["rationale"])
    assert any("Two positive diagnostic blocks" in s for s in r["rationale"])


def test_mbb_without_positive_block_falls_through():
    # MBB but block not positive -> not Class I; conserv 0 < 3 -> continue conservative
    r = assess({**_base(), "procedureType": "medial-branch-block",
                "diagnosticBlockPositive": False})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"


def test_facetogenic_pattern_reasonable():
    r = assess({**_base(),
                "symptoms": ["axial-pain", "pain-extension", "no-neurologic"],
                "conservativeTherapyMonths": "3"})
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["recommendation"] == "Facet Injection Reasonable"
    assert any("Axial spine pain" in s for s in r["rationale"])
    assert any("facetogenic pain" in s for s in r["rationale"])
    assert any("Conservative therapy trial completed" in s for s in r["rationale"])


def test_facetogenic_pattern_but_insufficient_conservative():
    # full symptom pattern but conserv < 3 -> falls to conservative branch
    r = assess({**_base(),
                "symptoms": ["axial-pain", "pain-extension", "no-neurologic"],
                "conservativeTherapyMonths": "2"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert any("Conservative therapy trial insufficient" in s for s in r["rationale"])


def test_insufficient_conservative_therapy():
    r = assess({**_base(), "conservativeTherapyMonths": "1"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert any("Continue PT and analgesics" in s for s in r["optimizationSteps"])


def test_insufficient_criteria():
    # conserv >= 3 but symptom pattern not met -> Insufficient Criteria
    r = assess({**_base(), "conservativeTherapyMonths": "4"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    assert any("not clearly met" in s for s in r["rationale"])
    assert any("Document axial pain pattern" in s for s in r["optimizationSteps"])


def test_severe_pain_appended():
    r = assess({**_base(), "conservativeTherapyMonths": "4", "painScore": "8"})
    assert any("Severe pain (NRS ≥7)" in s for s in r["rationale"])


def test_severe_pain_not_appended_below_threshold():
    r = assess({**_base(), "conservativeTherapyMonths": "4", "painScore": "6"})
    assert not any("Severe pain" in s for s in r["rationale"])


def test_good_prior_response_appended():
    r = assess({**_base(), "conservativeTherapyMonths": "4", "priorFacetResponse": "good"})
    assert any("Prior facet injection response was good" in s for s in r["rationale"])


def test_result_shape():
    r = assess(_base())
    assert set(r.keys()) == {
        "recommendation", "cor", "loe", "urgency",
        "rationale", "contraindications", "optimizationSteps",
    }
