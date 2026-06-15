"""Tests for the Oocyte Cryopreservation Clinical Compass port.

Fixtures authored from the TS branches in
old_static_code/client/src/pages/OocyteFreezeCompass.tsx (no TS test exists).
"""

from app.recommendations.modules.oocytefreeze import assess


def test_oncofertility_with_gonadotoxic_therapy():
    r = assess({"indication": "oncofertility", "gonadotoxicTherapy": True})
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Oocyte cryopreservation — oncofertility (medical indication)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert len(r["rationale"]) == 2
    assert r["warnings"] == []


def test_oncofertility_with_therapy_timeline_warning():
    r = assess(
        {
            "indication": "oncofertility",
            "gonadotoxicTherapy": True,
            "therapyTimeline": "chemotherapy starting in 3 weeks",
        }
    )
    assert r["recommendation"] == "indicated"
    assert r["warnings"] == [
        "Treatment timeline: chemotherapy starting in 3 weeks. Coordinate with oncology — IVF stimulation typically requires 10–14 days."
    ]


def test_oncofertility_without_gonadotoxic_falls_through_to_not_indicated():
    r = assess({"indication": "oncofertility", "gonadotoxicTherapy": False})
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Oocyte cryopreservation — indication not established"
    assert r["cor"] == "I"
    assert r["loe"] == "A"


def test_medical_poi_indicated():
    r = assess({"indication": "medical", "prematureOvarianInsufficiency": True})
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Oocyte cryopreservation — medical indication (POI/genetic condition)"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert len(r["rationale"]) == 1


def test_medical_genetic_condition_indicated():
    r = assess({"indication": "medical", "geneticCondition": True})
    assert r["recommendation"] == "indicated"
    assert r["loe"] == "B"


def test_medical_without_poi_or_genetic_falls_through():
    r = assess({"indication": "medical"})
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Oocyte cryopreservation — indication not established"


def test_elective_under_38():
    r = assess({"indication": "elective", "femaleAge": 32})
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "Elective oocyte cryopreservation — patient counseling required"
    assert r["cor"] == "IIb"
    assert r["loe"] == "C"
    assert r["warnings"] == [
        "Insurance coverage for elective egg freezing is rare. Most payers require a medical indication (oncofertility, POI, genetic condition)."
    ]


def test_elective_age_38_or_older_adds_warning():
    r = assess({"indication": "elective", "femaleAge": 40})
    assert r["recommendation"] == "consider"
    assert len(r["warnings"]) == 2
    assert r["warnings"][1] == (
        "Age 40: success rates decline significantly with age. "
        "Discuss realistic expectations — fewer usable eggs per cycle expected."
    )


def test_elective_age_exactly_38_boundary():
    r = assess({"indication": "elective", "femaleAge": 38})
    assert len(r["warnings"]) == 2
    assert r["warnings"][1].startswith("Age 38:")


def test_donor_not_indicated():
    r = assess({"indication": "donor"})
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Oocyte cryopreservation — indication not established"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert len(r["rationale"]) == 1


def test_references_always_present():
    r = assess({"indication": "donor"})
    assert len(r["references"]) == 4
    assert r["references"][0].startswith("Practice Committees of ASRM and SART")
