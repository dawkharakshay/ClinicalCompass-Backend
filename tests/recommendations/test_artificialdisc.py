"""ADR engine — fixtures derived directly from artificialDiscLogic.ts branches."""

from app.recommendations.modules.artificialdisc import assess


def _base() -> dict:
    return {
        "conservativeTherapyMonths": "0",
        "ndiScore": "",
        "levels": "1",
        "imagingFindings": [],
        "neurologicDeficits": [],
        "comorbidities": [],
        "facetArthrosis": False,
        "instability": False,
        "osteoporosis": False,
        "priorSpineSurgery": False,
        "spondylolisthesis": False,
        "activeInfection": False,
        "medicallyUnfit": False,
    }


def test_active_infection_contraindicated():
    r = assess({**_base(), "activeInfection": True})
    assert r["cor"] == "III"
    assert r["loe"] == "B"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "Artificial Disc Replacement Contraindicated"
    assert any("Active infection" in c for c in r["contraindications"])


def test_osteoporosis_contraindicated():
    r = assess({**_base(), "osteoporosis": True})
    assert r["cor"] == "III"
    assert any("Osteoporosis" in c for c in r["contraindications"])


def test_more_than_two_levels_contraindicated():
    r = assess({**_base(), "levels": "3"})
    assert r["cor"] == "III"
    assert any("More than 2 levels" in c for c in r["contraindications"])


def test_class_i_full_criteria():
    r = assess({**_base(), "conservativeTherapyMonths": "6", "ndiScore": "30",
                "imagingFindings": ["disc-herniation"]})
    assert r["cor"] == "I"
    assert r["recommendation"] == "ADR Recommended"
    assert r["urgency"] == "Appropriate"
    assert r["loe"] == "A"


def test_class_i_requires_disc_herniation():
    # High conserv + ndi but no disc-herniation imaging -> falls to IIa
    r = assess({**_base(), "conservativeTherapyMonths": "6", "ndiScore": "30",
                "imagingFindings": ["spinal-stenosis"]})
    assert r["cor"] == "IIa"
    assert r["recommendation"] == "ADR Reasonable"
    assert r["urgency"] == "Reasonable"


def test_class_iia_moderate():
    r = assess({**_base(), "conservativeTherapyMonths": "6", "ndiScore": "20"})
    assert r["cor"] == "IIa"
    assert r["recommendation"] == "ADR Reasonable"


def test_class_iib_insufficient():
    r = assess({**_base(), "conservativeTherapyMonths": "3", "ndiScore": "25"})
    assert r["cor"] == "IIb"
    assert r["recommendation"] == "ADR — Additional Criteria Needed"
    assert r["urgency"] == "Continue Conservative Therapy"
    steps = " ".join(r["optimizationSteps"])
    assert "Continue PT" in steps
    assert "NDI" in steps


def test_default_ndi_blocks_class_iia():
    # ndiScore missing -> defaults to 0, so even with 6 months conserv the
    # IIa branch (needs ndi >= 20) is NOT taken.
    r = assess({**_base(), "conservativeTherapyMonths": "6"})
    assert r["cor"] == "IIb"
