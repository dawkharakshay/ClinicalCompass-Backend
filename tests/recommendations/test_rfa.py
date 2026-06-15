"""RFA engine — fixtures derived directly from rfaLogic.ts branches."""

from app.recommendations.modules.rfa import assess


def _base() -> dict:
    return {
        "age": "60",
        "spineRegion": "lumbar",
        "symptomDurationMonths": "0",
        "painScore": "0",
        "symptoms": [],
        "diagnosticBlock1Relief": "0",
        "diagnosticBlock2Relief": "0",
        "activeInfection": False,
        "coagulopathy": False,
        "allergy": False,
        "pacemaker": False,
        "pregnancy": False,
    }


def test_hard_contraindication_active_infection():
    r = assess({**_base(), "activeInfection": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "RFA Contraindicated"
    assert r["optimizationSteps"] == []
    assert any("Active infection" in c for c in r["contraindications"])


def test_pacemaker_alone_is_not_hard_contraindication():
    # Pacemaker is a relative contraindication; it must NOT trigger the hard
    # contraindication early return. With no blocks -> default IIb branch.
    r = assess({**_base(), "pacemaker": True})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Diagnostic Blocks Required"
    assert any("Pacemaker/ICD" in c for c in r["contraindications"])
    assert any("bipolar RFA technique" in s for s in r["optimizationSteps"])


def test_both_blocks_positive_chronic_class_i():
    r = assess({**_base(), "diagnosticBlock1Relief": "85",
                "diagnosticBlock2Relief": "80", "symptomDurationMonths": "6"})
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "RFA Recommended"
    assert any("gold standard" in s for s in r["rationale"])


def test_one_block_positive_chronic_class_iia():
    r = assess({**_base(), "diagnosticBlock1Relief": "90",
                "diagnosticBlock2Relief": "50", "symptomDurationMonths": "4"})
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"
    assert r["urgency"] == "Reasonable"
    assert r["recommendation"] == "RFA Reasonable (Second Block Needed)"
    assert any("second diagnostic medial branch block" in s.lower()
               for s in r["optimizationSteps"])


def test_blocks_failed_not_indicated_class_iii():
    # Both < 80 but at least one > 0 -> Not Indicated.
    r = assess({**_base(), "diagnosticBlock1Relief": "60",
                "diagnosticBlock2Relief": "40", "symptomDurationMonths": "6"})
    assert r["cor"] == "III"
    assert r["loe"] == "B"
    assert r["urgency"] == "Not Indicated"
    assert r["recommendation"] == "RFA Not Indicated"


def test_no_blocks_default_class_iib():
    r = assess({**_base(), "symptomDurationMonths": "6"})
    assert r["cor"] == "IIb"
    assert r["loe"] == "B"
    assert r["urgency"] == "Diagnostic Blocks Required"
    assert r["recommendation"] == "Diagnostic Blocks Required First"


def test_both_positive_but_acute_falls_through_to_iib():
    # symptomMonths < 3 fails both the bothBlocks and oneBlock branches; both
    # blocks >= 80 so the III branch's (block<80) guard is false -> default IIb.
    r = assess({**_base(), "diagnosticBlock1Relief": "90",
                "diagnosticBlock2Relief": "90", "symptomDurationMonths": "1"})
    assert r["cor"] == "IIb"
    assert r["loe"] == "A"  # bothBlocksPositive is still True
    assert r["urgency"] == "Diagnostic Blocks Required"


def test_severe_pain_rationale_appended():
    r = assess({**_base(), "diagnosticBlock1Relief": "85",
                "diagnosticBlock2Relief": "85", "symptomDurationMonths": "6",
                "painScore": "8"})
    assert any("Severe pain (NRS ≥7)" in s for s in r["rationale"])


def test_coagulopathy_hard_contraindication():
    r = assess({**_base(), "coagulopathy": True})
    assert r["cor"] == "III"
    assert r["urgency"] == "Contraindicated"
    assert any("coagulopathy" in c for c in r["contraindications"])
