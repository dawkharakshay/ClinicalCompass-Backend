"""Tests for the Meniscus Repair port.

Fixtures derived from the branches of
old_static_code/client/src/lib/meniscusRepairLogic.ts (assessMeniscusRepair),
since no .test.ts oracle exists.
"""

from app.recommendations.modules.meniscusrepair import assess


def _base(**overrides):
    data = {
        "age": "40",
        "affectedSide": "left",
        "tearLocation": "medial",
        "tearPattern": "longitudinal",
        "symptomDurationMonths": "6",
        "painScore": "5",
        "symptoms": [],
        "conservativeTherapyMonths": "6",
        "conservativeTherapies": [],
        "tearCharacteristics": [],
        "acuteTear": False,
        "activeSports": False,
        "osteoarthritis": False,
        "activeInfection": False,
        "severeOA": False,
    }
    data.update(overrides)
    return data


def test_active_infection_contraindicated():
    r = assess(_base(activeInfection=True))
    assert r["recommendation"] == "Knee Arthroscopy Contraindicated"
    assert r["cor"] == "III"
    assert r["loe"] == "B"
    assert r["urgency"] == "Contraindicated"
    assert r["contraindications"] == [
        "Active knee infection — absolute contraindication"
    ]
    assert r["optimizationSteps"] == []


def test_severe_oa_contraindicated():
    r = assess(_base(severeOA=True))
    assert r["cor"] == "III"
    assert r["contraindications"] == [
        "Severe knee osteoarthritis (bone-on-bone) — meniscectomy/repair unlikely to benefit; consider TKA"
    ]


def test_bucket_handle_mechanical_urgent():
    r = assess(_base(tearPattern="bucket-handle", symptoms=["locking"]))
    assert r["cor"] == "I"
    assert r["urgency"] == "Urgent"
    assert r["loe"] == "A"
    assert r["recommendation"] == "Knee Arthroscopy Recommended"
    assert "Delay risks irreversible cartilage damage from locked fragment" in r["rationale"]


def test_mechanical_repairable_peripheral_young():
    r = assess(
        _base(
            symptoms=["giving-way"],
            tearCharacteristics=["peripheral-zone"],
            age="30",
        )
    )
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["loe"] == "B"
    assert r["recommendation"] == "Knee Arthroscopy Recommended"
    assert (
        "Peripheral (vascular) zone tear in younger patient — repair preferred over meniscectomy"
        in r["rationale"]
    )


def test_mechanical_peripheral_older_no_repair_note():
    r = assess(
        _base(
            symptoms=["locking"],
            tearCharacteristics=["peripheral-zone"],
            age="55",
        )
    )
    assert r["cor"] == "I"
    assert (
        "Peripheral (vascular) zone tear in younger patient — repair preferred over meniscectomy"
        not in r["rationale"]
    )


def test_complex_tear_limited_benefit():
    r = assess(_base(tearPattern="complex"))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Limited Benefit Expected"
    assert r["recommendation"] == "Continue Conservative Therapy"
    assert "Continue PT and weight management as first-line treatment" in r["optimizationSteps"]


def test_osteoarthritis_limited_benefit():
    r = assess(_base(osteoarthritis=True))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Limited Benefit Expected"


def test_non_mechanical_inadequate_conservative():
    r = assess(_base(conservativeTherapyMonths="1"))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert r["recommendation"] == "Continue Conservative Therapy"
    assert "Continue PT for ≥3 months before considering surgery" in r["optimizationSteps"]


def test_reasonable_adequate_conservative_failure():
    r = assess(_base(conservativeTherapyMonths="6"))
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["recommendation"] == "Arthroscopy Reasonable"


def test_active_sports_peripheral_optimization():
    r = assess(
        _base(
            conservativeTherapyMonths="6",
            activeSports=True,
            tearCharacteristics=["peripheral-zone"],
        )
    )
    assert (
        "Active athlete with peripheral tear — repair preferred to preserve meniscal function"
        in r["optimizationSteps"]
    )
