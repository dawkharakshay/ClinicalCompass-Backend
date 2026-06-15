"""THA engine — fixtures derived directly from thaLogic.ts branches."""

from app.recommendations.modules.tha import assess


def _base() -> dict:
    return {
        "bmi": "28",
        "harrisPainScore": "",
        "kellgrenLawrence": "0",
        "conservativeTherapyMonths": "0",
        "comorbidities": [],
        "activeInfection": False,
        "activeHipInfection": False,
        "severeVascularDisease": False,
        "medicallyUnfit": False,
        "avascularNecrosis": False,
    }


def test_contraindication_wins():
    r = assess({**_base(), "activeInfection": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert any("Active systemic infection" in c for c in r["contraindications"])


def test_avascular_necrosis_is_class_i():
    r = assess({**_base(), "avascularNecrosis": True})
    assert r["cor"] == "I"
    assert r["recommendation"] == "THA Recommended"
    assert r["urgency"] == "Appropriate"


def test_severe_oa_class_i():
    r = assess({**_base(), "kellgrenLawrence": "4", "harrisPainScore": "10",
                "conservativeTherapyMonths": "4"})
    assert r["cor"] == "I"
    assert r["loe"] == "A"  # kl >= 3


def test_moderate_oa_class_iia():
    r = assess({**_base(), "kellgrenLawrence": "2", "harrisPainScore": "25",
                "conservativeTherapyMonths": "3"})
    assert r["cor"] == "IIa"
    assert r["recommendation"] == "THA Reasonable"
    assert r["loe"] == "B"


def test_criteria_not_met_class_iib():
    r = assess({**_base(), "kellgrenLawrence": "1"})
    assert r["cor"] == "IIb"
    assert r["recommendation"] == "THA — Additional Criteria Needed"
    assert any("continue conservative" in s.lower() for s in r["rationale"])


def test_optimization_steps_bmi_and_comorbidities():
    r = assess({**_base(), "bmi": "42", "comorbidities": ["diabetes", "smoking"]})
    steps = " ".join(r["optimizationSteps"])
    assert "BMI >40" in steps
    assert "glycemic" in steps
    assert "Smoking cessation" in steps


def test_default_harris_pain_blocks_class_i():
    # harrisPainScore missing -> defaults to 44, so even with high KL the
    # severe-OA branch (needs <=20) is NOT taken.
    r = assess({**_base(), "kellgrenLawrence": "4", "conservativeTherapyMonths": "6"})
    assert r["cor"] == "IIb"
