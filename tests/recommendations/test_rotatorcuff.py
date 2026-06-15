"""Tests for the rotator cuff repair port.

Fixtures derived from old_static_code/client/src/lib/rotatorCuffLogic.ts
branches (no TS test oracle existed).
"""

from app.recommendations.modules.rotatorcuff import assess


def _base(**over):
    data = {
        "age": "55",
        "affectedSide": "right",
        "tearSize": "small",
        "symptomDurationMonths": "4",
        "painScore": "5",
        "symptoms": [],
        "conservativeTherapyMonths": "4",
        "conservativeTherapies": [],
        "tearCharacteristics": [],
        "acuteTear": False,
        "dominantArm": False,
        "highDemandActivity": False,
        "activeInfection": False,
        "severeGlenohumeralArthritis": False,
    }
    data.update(over)
    return data


def test_active_infection_contraindicated():
    r = assess(_base(activeInfection=True))
    assert r["cor"] == "III"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "Arthroscopic Repair Contraindicated"
    assert r["loe"] == "C"
    assert "Active shoulder infection — absolute contraindication" in r["contraindications"]
    assert r["optimizationSteps"] == []


def test_severe_arthritis_contraindicated():
    r = assess(_base(severeGlenohumeralArthritis=True))
    assert r["cor"] == "III"
    assert (
        "Severe glenohumeral arthritis — consider shoulder arthroplasty instead"
        in r["contraindications"]
    )


def test_acute_full_thickness_urgent():
    r = assess(_base(acuteTear=True, tearCharacteristics=["full-thickness"]))
    assert r["cor"] == "I"
    assert r["urgency"] == "Urgent"
    assert r["recommendation"] == "Rotator Cuff Repair Recommended"
    assert r["loe"] == "A"
    assert any("early repair (within 6 weeks)" in s for s in r["rationale"])


def test_full_thickness_conservative_failed_appropriate():
    r = assess(
        _base(
            tearCharacteristics=["full-thickness"],
            conservativeTherapyMonths="3",
            painScore="6",
        )
    )
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["loe"] == "A"
    assert any("per AAOS guidelines" in s for s in r["rationale"])


def test_large_or_massive_reasonable():
    r = assess(_base(tearSize="massive"))
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "Repair Reasonable"
    assert r["loe"] == "B"
    assert r["optimizationSteps"] == []


def test_large_with_retraction_adds_tendon_transfer_step():
    r = assess(_base(tearSize="large", tearCharacteristics=["retraction"]))
    assert r["cor"] == "IIa"
    assert any("tendon transfer" in s for s in r["optimizationSteps"])


def test_insufficient_conservative_continue():
    r = assess(_base(conservativeTherapyMonths="1", acuteTear=False))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert r["recommendation"] == "Continue Conservative Therapy"
    assert len(r["optimizationSteps"]) == 2


def test_default_reasonable_branch():
    # conservMonths >= 3, not full-thickness, not large/massive -> final else
    r = assess(_base(conservativeTherapyMonths="6", tearSize="small"))
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["loe"] == "B"
    assert any("reasonable given tear characteristics" in s for s in r["rationale"])


def test_dominant_arm_and_high_demand_appends_rationale():
    r = assess(
        _base(
            conservativeTherapyMonths="6",
            dominantArm=True,
            highDemandActivity=True,
        )
    )
    assert any("Dominant arm affected" in s for s in r["rationale"])
    assert any("High-demand overhead activity" in s for s in r["rationale"])
