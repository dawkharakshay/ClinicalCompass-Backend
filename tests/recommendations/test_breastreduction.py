"""Tests for the Breast Reduction port.

No TS oracle test existed for breastReductionLogic.ts; fixtures are derived
from the branches of calculateBreastReductionScore, covering each scoring path
plus a contraindication/high-risk path.
"""

from app.recommendations.modules.breastreduction import (
    assess,
    calculate_bsa,
    calculate_schnur_minimum,
)


def test_schnur_minimum_bounds_and_interpolation():
    assert calculate_schnur_minimum(1.4) == 300
    assert calculate_schnur_minimum(1.5) == 300
    assert calculate_schnur_minimum(2.5) == 1150
    assert calculate_schnur_minimum(2.6) == 1150
    # interpolation between 1.6 (360) and 1.7 (420)
    assert calculate_schnur_minimum(1.65) == 390
    # exact table value
    assert calculate_schnur_minimum(2.0) == 660


def test_calculate_bsa_mosteller():
    # 70 in, 200 lbs -> Mosteller
    bsa = calculate_bsa(70, 200)
    assert abs(bsa - 2.1167) < 0.001


def test_strongly_indicated_clearly_eligible():
    data = {
        "bsaM2": 1.8,  # schnur min 500
        "estimatedResectionGrams": 600,  # ratio >= 1.0 -> +35
        "neckPain": True,
        "shoulderPain": True,
        "backPain": True,
        "shoulderGrooving": True,  # 4 symptoms -> +30
        "painLevel": 8,  # +15
        "symptomDurationMonths": 14,  # +10
        "triedPhysicalTherapy": True,
        "ptDurationMonths": 4,  # +15
    }
    r = assess(data)
    assert r["schnurCategory"] == "Clearly Eligible"
    assert r["candidacyScore"] == 100  # capped: 35+30+15+10+15 = 105 -> 100
    assert r["recommendation"] == "Strongly Indicated"
    assert r["conservativeTreatmentMet"] is True
    assert "Estimated resection 600g per breast — meets Schnur Scale minimum of 500g for BSA 1.80m²" in r["keyFindings"]


def test_borderline_schnur_and_consider():
    data = {
        "bsaM2": 1.8,  # schnur min 500
        "estimatedResectionGrams": 300,  # ratio 0.6 -> borderline -> +15
        "neckPain": True,  # 1 symptom -> +10
    }
    r = assess(data)
    assert r["schnurCategory"] == "Borderline"
    assert r["candidacyScore"] == 25  # 15 + 10
    assert r["recommendation"] == "Consider"
    assert any("borderline for Schnur Scale" in f for f in r["keyFindings"])


def test_no_resection_provided_borderline():
    data = {
        "bsaM2": 1.8,
        "estimatedResectionGrams": 0,
    }
    r = assess(data)
    assert r["schnurCategory"] == "Borderline"
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Indicated"
    assert any("Resection weight estimate not provided" in f for f in r["keyFindings"])


def test_not_eligible_by_weight_alone():
    data = {
        "bsaM2": 1.8,  # min 500
        "estimatedResectionGrams": 200,  # ratio 0.4 -> not eligible
    }
    r = assess(data)
    assert r["schnurCategory"] == "Not Eligible by Weight Alone"
    assert any("below Schnur Scale minimum" in f for f in r["keyFindings"])


def test_high_risk_warnings_reduce_score():
    data = {
        "bsaM2": 1.8,
        "estimatedResectionGrams": 600,  # +35 clearly eligible
        "smoking": True,  # -5
        "diabetes": True,  # warning only
        "bmi": 41,  # -10
        "asa": 4,  # -15
    }
    r = assess(data)
    assert r["schnurCategory"] == "Clearly Eligible"
    # 35 - 5 - 10 - 15 = 5
    assert r["candidacyScore"] == 5
    assert r["recommendation"] == "Not Indicated"
    assert any("Active smoking" in w for w in r["warnings"])
    assert any("Diabetes" in w for w in r["warnings"])
    assert any("BMI 41" in w and "morbid obesity" in w for w in r["warnings"])
    assert any("ASA Class IV" in w for w in r["warnings"])


def test_indicated_midrange_with_pt_attempted():
    data = {
        "bsaM2": 1.8,
        "estimatedResectionGrams": 600,  # +35
        "neckPain": True,
        "backPain": True,  # 2 symptoms -> +20
        "triedPhysicalTherapy": True,
        "ptDurationMonths": 2,  # attempted only -> +8, not met
    }
    r = assess(data)
    assert r["conservativeTreatmentMet"] is False
    # 35 + 20 + 8 = 63 -> Strongly Indicated
    assert r["candidacyScore"] == 63
    assert r["recommendation"] == "Strongly Indicated"
    assert any("Physical therapy attempted" in f for f in r["keyFindings"])


def test_bmi_35_band_and_supportive_measures():
    data = {
        "bsaM2": 1.8,
        "estimatedResectionGrams": 600,  # +35
        "painLevel": 5,  # +8
        "symptomDurationMonths": 7,  # +5
        "triedSupportiveBra": True,  # +5
        "triedMedications": True,  # +5
        "triedWeightLoss": True,
        "weightLossAttemptMonths": 7,  # +5
        "bmi": 36,  # -5
    }
    r = assess(data)
    # 35 + 8 + 5 + 5 + 5 + 5 - 5 = 58 -> Indicated
    assert r["candidacyScore"] == 58
    assert r["recommendation"] == "Indicated"
    assert any("BMI 36" in w and "obesity increases surgical risk" in w for w in r["warnings"])


def test_string_inputs_coerced():
    # Form values typically arrive as strings; ensure parsing matches numbers.
    data = {
        "bsaM2": "1.8",
        "estimatedResectionGrams": "600",
        "painLevel": "8",
        "neckPain": "true",
    }
    r = assess(data)
    assert r["schnurCategory"] == "Clearly Eligible"
    # 35 + 10 (1 symptom) + 15 (pain>=7) = 60
    assert r["candidacyScore"] == 60
    assert r["recommendation"] == "Strongly Indicated"
    assert "Estimated resection 600g per breast — meets Schnur Scale minimum of 500g for BSA 1.80m²" in r["keyFindings"]


def test_bsa_computed_when_not_provided():
    data = {
        "height": 70,
        "weight": 200,
        "estimatedResectionGrams": 2000,  # well above min -> clearly eligible
    }
    r = assess(data)
    assert r["schnurCategory"] == "Clearly Eligible"
    # BSA ~2.12 -> schnur min ~ 855
    assert any("BSA 2.12m²" in f for f in r["keyFindings"])
