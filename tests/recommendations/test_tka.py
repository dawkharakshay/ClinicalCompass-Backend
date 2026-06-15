"""TKA engine — fixtures derived directly from tkaLogic.ts branches."""

from app.recommendations.modules.tka import assess


def _base() -> dict:
    # age 60 avoids the age<55 step; koos defaults to 100 unless set.
    return {
        "age": "60",
        "bmi": "28",
        "koosPainScore": "",
        "koosADLScore": "",
        "klGrade": "",
        "kellgrenLawrence": "0",
        "painScore": "",
        "conservativeTherapyMonths": "0",
        "comorbidities": [],
        "functionalLimitations": [],
        "activeInfection": False,
        "activeKneeInfection": False,
        "severeVascularDisease": False,
        "extensorMechanismDeficiency": False,
        "priorKneeInfection": False,
        "medicallyUnfit": False,
    }


def test_contraindication_wins():
    r = assess({**_base(), "activeKneeInfection": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert any("Active knee joint infection" in c for c in r["contraindications"])
    assert r["recommendation"] == "TKA Contraindicated or Requires Optimization"


def test_severe_oa_class_i():
    r = assess({
        **_base(),
        "klGrade": "4",
        "koosPainScore": "30",
        "koosADLScore": "40",
        "conservativeTherapyMonths": "4",
    })
    assert r["cor"] == "I"
    assert r["recommendation"] == "TKA Recommended"
    assert r["urgency"] == "Appropriate"
    assert r["loe"] == "A"  # kl >= 3
    assert any("strongly recommended per AAOS" in s for s in r["rationale"])


def test_moderate_oa_class_iia():
    r = assess({
        **_base(),
        "klGrade": "2",
        "koosPainScore": "50",
        "conservativeTherapyMonths": "3",
    })
    assert r["cor"] == "IIa"
    assert r["recommendation"] == "TKA Reasonable"
    assert r["urgency"] == "Reasonable"
    assert r["loe"] == "B"


def test_insufficient_conservative_class_iib():
    # kl >= 2 but conserv < 3 -> Continue Conservative Therapy branch.
    r = assess({**_base(), "klGrade": "3", "koosPainScore": "30",
                "koosADLScore": "30", "conservativeTherapyMonths": "1"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert r["recommendation"] == "TKA — Additional Criteria Needed"
    assert r["loe"] == "A"  # kl 3 -> A even when IIb
    steps = " ".join(r["optimizationSteps"])
    assert "Continue physical therapy" in steps


def test_insufficient_criteria_class_iib():
    # kl < 2 -> else branch.
    r = assess({**_base(), "klGrade": "1"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    assert r["loe"] == "B"
    steps = " ".join(r["optimizationSteps"])
    assert "Repeat weight-bearing X-rays" in steps


def test_kellgren_fallback_when_klgrade_empty():
    # klGrade empty -> parseInt falls back to kellgrenLawrence.
    r = assess({
        **_base(),
        "klGrade": "",
        "kellgrenLawrence": "4",
        "koosPainScore": "20",
        "koosADLScore": "20",
        "conservativeTherapyMonths": "6",
    })
    assert r["cor"] == "I"


def test_default_koos_blocks_class_i():
    # koos scores missing -> default 100, so KL>=3 + conserv>=3 still NOT class I
    # (needs koosPain<=45 and koosADL<=45). Falls to else (insufficient criteria).
    r = assess({**_base(), "klGrade": "4", "conservativeTherapyMonths": "6"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"


def test_optimization_steps_bmi_age_comorbidities():
    r = assess({
        **_base(),
        "age": "40",
        "bmi": "42",
        "comorbidities": ["diabetes", "smoking"],
    })
    steps = " ".join(r["optimizationSteps"])
    assert "BMI >40" in steps
    assert "Age <55" in steps
    assert "glycemic control" in steps
    assert "Smoking cessation" in steps
