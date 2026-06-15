"""Spinal Fusion engine — fixtures derived from spinalFusionLogic.ts branches."""

from app.recommendations.modules.spinalfusion import assess


def _base() -> dict:
    return {
        "conservativeTherapyMonths": "0",
        "odiScore": "",
        "ndiScore": "",
        "painScore": "0",
        "symptoms": [],
        "instability": False,
        "myelopathy": False,
        "progressiveNeurologicDeficit": False,
        "activeInfection": False,
        "severeOsteoporosis": False,
        "medicallyUnfit": False,
    }


def test_active_infection_contraindicated():
    r = assess({**_base(), "activeInfection": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "Spinal Fusion Contraindicated or Requires Optimization"
    assert any("Active infection" in c for c in r["contraindications"])


def test_severe_osteoporosis_contraindicated():
    r = assess({**_base(), "severeOsteoporosis": True})
    assert r["cor"] == "III"
    assert any("Severe osteoporosis" in c for c in r["contraindications"])


def test_medically_unfit_contraindicated():
    r = assess({**_base(), "medicallyUnfit": True})
    assert r["cor"] == "III"
    assert any("Medically unfit" in c for c in r["contraindications"])


def test_progressive_deficit_class_i_urgent():
    r = assess({**_base(), "progressiveNeurologicDeficit": True})
    assert r["cor"] == "I"
    assert r["urgency"] == "Urgent"
    assert r["recommendation"] == "Spinal Fusion Recommended"
    assert r["loe"] == "B"


def test_myelopathy_class_i_urgent():
    r = assess({**_base(), "myelopathy": True})
    assert r["cor"] == "I"
    assert r["urgency"] == "Urgent"


def test_instability_class_i_appropriate():
    r = assess({**_base(), "instability": True, "conservativeTherapyMonths": "6",
                "odiScore": "40"})
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "Spinal Fusion Recommended"
    assert r["loe"] == "A"


def test_instability_via_ndi():
    r = assess({**_base(), "instability": True, "conservativeTherapyMonths": "6",
                "ndiScore": "30"})
    assert r["cor"] == "I"
    assert r["loe"] == "A"


def test_class_iia_reasonable():
    r = assess({**_base(), "conservativeTherapyMonths": "6", "odiScore": "40",
                "painScore": "6"})
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["recommendation"] == "Spinal Fusion Reasonable"
    assert r["loe"] == "B"


def test_iia_requires_pain_score():
    # 6 months + odi 40 but pain 5 -> not IIa; conserv >= 6 so falls to else (Insufficient)
    r = assess({**_base(), "conservativeTherapyMonths": "6", "odiScore": "40",
                "painScore": "5"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"


def test_iib_continue_conservative_short_trial():
    r = assess({**_base(), "conservativeTherapyMonths": "3", "odiScore": "40",
                "painScore": "8"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert r["recommendation"] == "Spinal Fusion — Additional Criteria Needed"
    steps = " ".join(r["optimizationSteps"])
    assert "Continue PT" in steps


def test_iib_insufficient_criteria():
    # 6 months but low functional scores -> Insufficient Criteria branch
    r = assess({**_base(), "conservativeTherapyMonths": "6", "odiScore": "20",
                "painScore": "8"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    steps = " ".join(r["optimizationSteps"])
    assert "ODI (lumbar) or NDI (cervical)" in steps


def test_smoking_and_diabetes_optimization():
    r = assess({**_base(), "conservativeTherapyMonths": "3",
                "symptoms": ["smoking", "diabetes"]})
    steps = " ".join(r["optimizationSteps"])
    assert "Smoking cessation required" in steps
    assert "glycemic control" in steps
