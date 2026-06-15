"""Tests for the sacroplasty recommendation module.

Fixtures derived 1:1 from the TS branches in
old_static_code/client/src/lib/sacroplastyLogic.ts (no TS oracle test exists).
"""

from app.recommendations.modules.sacroplasty import assess


def _base() -> dict:
    return {
        "age": "72",
        "vasScore": "0",
        "functionalImpairment": "moderate",
        "denisZone": "",
        "bilateral": False,
        "mriEdema": False,
        "ctFractureLine": False,
        "fractureAgeWeeks": "0",
        "hShapeFracture": False,
        "osteoporosis": False,
        "malignancy": False,
        "radiation": False,
        "conservativeWeeks": "0",
        "analgesicsUsed": False,
        "ptUsed": False,
        "mobilityAids": False,
        "activeInfection": False,
        "coagulopathy": False,
        "sacralNerveCompression": False,
        "bowelBladderDysfunction": False,
        "allergy": False,
        "pregnancy": False,
    }


def test_contraindication_active_infection():
    data = _base()
    data["activeInfection"] = True
    out = assess(data)
    assert out["cor"] == "III"
    assert out["recommendation"] == "Sacroplasty Contraindicated"
    assert out["urgency"] == "Contraindicated"
    assert out["loe"] == "C"
    assert out["denisZoneNote"] == ""
    assert out["contraindications"] == [
        "Active systemic or local infection — absolute contraindication to sacroplasty"
    ]
    assert out["optimizationSteps"] == [
        "Resolve contraindication(s) before reassessing candidacy"
    ]


def test_multiple_contraindications_collected():
    data = _base()
    data["coagulopathy"] = True
    data["pregnancy"] = True
    out = assess(data)
    assert out["cor"] == "III"
    assert len(out["contraindications"]) == 2
    assert out["contraindications"][0].startswith("Uncorrected coagulopathy")
    assert out["contraindications"][1].startswith("Pregnancy")


def test_class_i_zone1_osteoporosis():
    data = _base()
    data.update(
        {
            "denisZone": "zone1",
            "mriEdema": True,
            "vasScore": "7",
            "conservativeWeeks": "6",
            "osteoporosis": True,
            "bilateral": True,
        }
    )
    out = assess(data)
    assert out["cor"] == "I"
    assert out["urgency"] == "Appropriate"
    assert out["recommendation"] == "Sacroplasty Recommended"
    assert out["loe"] == "B"  # mriEdema True
    assert (
        "Sacral insufficiency fracture — Denis Zone 1 (sacral ala) with imaging-confirmed fracture"
        in out["rationale"]
    )
    assert "VAS pain score 7/10 — severe pain supporting intervention" in out["rationale"]
    assert any("Bilateral sacral fractures" in r for r in out["rationale"])
    assert out["denisZoneNote"].startswith("Denis Zone 1")


def test_class_i_zone2_malignancy_expedited():
    data = _base()
    data.update(
        {
            "denisZone": "zone2",
            "ctFractureLine": True,
            "vasScore": "8",
            "conservativeWeeks": "3",
            "malignancy": True,
            "radiation": True,
            "hShapeFracture": True,
        }
    )
    out = assess(data)
    assert out["cor"] == "I"
    assert out["urgency"] == "Pathologic Fracture — Expedited"
    assert out["loe"] == "C"  # mriEdema False (ctFractureLine only)
    assert (
        "Sacral insufficiency fracture — Denis Zone 2 (sacral foramina) with imaging-confirmed fracture"
        in out["rationale"]
    )
    assert any("H-shaped (Honda sign)" in r for r in out["rationale"])
    assert any("Pathologic fracture from malignancy" in r for r in out["rationale"])
    assert any("Radiation-induced insufficiency fracture" in r for r in out["rationale"])
    assert out["denisZoneNote"].startswith("Denis Zone 2")


def test_class_iia_with_zone3():
    data = _base()
    data.update(
        {
            "denisZone": "zone3",
            "mriEdema": True,
            "vasScore": "3",
            "conservativeWeeks": "2",
        }
    )
    out = assess(data)
    assert out["cor"] == "IIa"
    assert out["urgency"] == "Reasonable"
    assert out["recommendation"] == "Sacroplasty Reasonable"
    assert any("Denis Zone 3 (central canal)" in r for r in out["rationale"])
    assert any("Zone 3 fractures: Neurosurgical" in s for s in out["optimizationSteps"])
    assert out["denisZoneNote"].startswith("Denis Zone 3")


def test_class_iia_zone1_low_vas_falls_to_iia():
    # VAS 3 (>=3 but <4) with osteoporosis/zone1 — fails Class I (vas>=4), hits IIa
    data = _base()
    data.update(
        {
            "denisZone": "zone1",
            "mriEdema": True,
            "vasScore": "3",
            "conservativeWeeks": "6",
            "osteoporosis": True,
        }
    )
    out = assess(data)
    assert out["cor"] == "IIa"
    assert out["urgency"] == "Reasonable"


def test_conservative_insufficient():
    data = _base()
    data.update(
        {
            "denisZone": "zone1",
            "mriEdema": True,
            "vasScore": "8",
            "conservativeWeeks": "1",
            "osteoporosis": True,
        }
    )
    out = assess(data)
    assert out["cor"] == "IIb"
    assert out["urgency"] == "Continue Conservative Therapy"
    assert out["recommendation"] == "Continue Conservative Therapy — Sacroplasty Premature"
    assert out["loe"] == "B"
    assert any("Conservative therapy trial insufficient" in r for r in out["rationale"])
    assert len(out["optimizationSteps"]) == 3


def test_imaging_confirmation_required():
    # conservWeeks >= 2 but no imaging
    data = _base()
    data.update(
        {
            "denisZone": "zone1",
            "vasScore": "8",
            "conservativeWeeks": "6",
            "osteoporosis": True,
        }
    )
    out = assess(data)
    assert out["cor"] == "IIb"
    assert out["urgency"] == "Imaging Confirmation Required"
    assert out["recommendation"] == "MRI/CT Imaging Required Before Proceeding"
    assert out["loe"] == "C"
    assert any("not documented" in r for r in out["rationale"])


def test_insufficient_criteria():
    # imaging present, conservWeeks >= 2, but vas < 3 -> falls through to else
    data = _base()
    data.update(
        {
            "denisZone": "zone1",
            "mriEdema": True,
            "vasScore": "2",
            "conservativeWeeks": "6",
            "osteoporosis": True,
        }
    )
    out = assess(data)
    assert out["cor"] == "IIb"
    assert out["urgency"] == "Insufficient Criteria"
    assert out["recommendation"] == "Insufficient Criteria for Sacroplasty"
    assert out["loe"] == "B"
    assert out["rationale"] == []
    assert len(out["optimizationSteps"]) == 3


def test_denis_zone_note_default_when_blank():
    data = _base()
    data.update({"vasScore": "1", "conservativeWeeks": "0"})
    out = assess(data)
    assert out["denisZoneNote"].startswith(
        "Denis zone classification required for procedural planning"
    )
