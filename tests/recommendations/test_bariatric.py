"""Tests for the bariatric module port.

No oracle test exists in old_static_code/server for calculateBariatricScore;
fixtures below are derived directly from the TypeScript branches in
old_static_code/client/src/lib/bariatricLogic.ts to cover each major decision
path plus a contraindication edge case.
"""

from app.recommendations.modules.bariatric import assess


def test_strongly_recommended_class3_with_gerd_sleeve():
    # BMI 42 (+40), T2DM+HTN -> 2 comorbidities (+20), T2DM (+15),
    # supervised 6mo (+10), psych clearance (+10), nutrition (+5) = 100 (capped).
    result = assess(
        {
            "bmi": 42,
            "type2Diabetes": True,
            "hypertension": True,
            "hba1c": 9,
            "gerd": True,
            "procedureType": "sleeve",
            "supervisedProgramDuration": 6,
            "psychologicalClearance": True,
            "nutritionConsultCompleted": True,
        }
    )
    assert result["candidacyScore"] == 100
    assert result["recommendation"] == "Strongly Recommended"
    assert result["bmiCategory"] == "Class III Obesity (BMI ≥40)"
    assert result["preferredProcedure"] == (
        "Roux-en-Y Gastric Bypass (RYGB) — preferred given GERD; also superior for T2DM remission"
    )
    assert any("Sleeve gastrectomy may worsen GERD" in w for w in result["warnings"])
    assert any("poorly controlled" in f for f in result["keyFindings"])


def test_strongly_recommended_t2dm_bmi35_no_gerd():
    # BMI 37 (+30), T2DM only (1 comorbidity +10), T2DM (+15),
    # supervised 6 (+10), psych (+10), nutrition (+5) = 80.
    result = assess(
        {
            "bmi": 37,
            "type2Diabetes": True,
            "hba1c": 7.2,
            "supervisedProgramDuration": 6,
            "psychologicalClearance": True,
            "nutritionConsultCompleted": True,
        }
    )
    assert result["candidacyScore"] == 80
    assert result["recommendation"] == "Strongly Recommended"
    assert result["preferredProcedure"] == (
        "Roux-en-Y Gastric Bypass or Sleeve Gastrectomy — RYGB preferred for T2DM remission (80% vs 60%)"
    )
    assert any("ADA Standards of Care 2023" in f for f in result["keyFindings"])


def test_strongly_recommended_no_gerd_no_t2dm():
    # BMI 41 (+40), HTN+sleepApnea (2 comorbidities +20),
    # supervised 6 (+10), psych (+10) = 80.
    result = assess(
        {
            "bmi": 41,
            "hypertension": True,
            "sleepApnea": True,
            "supervisedProgramDuration": 6,
            "psychologicalClearance": True,
        }
    )
    assert result["candidacyScore"] == 80
    assert result["recommendation"] == "Strongly Recommended"
    assert result["preferredProcedure"] == (
        "Sleeve Gastrectomy (SG) or Roux-en-Y Gastric Bypass (RYGB) — discuss with patient based on anatomy, comorbidities, and preference"
    )


def test_recommended_band():
    # BMI 36 (+30), sleepApnea (1 comorbidity +10), supervised 6 (+10),
    # psych (+10) = 60.
    result = assess(
        {
            "bmi": 36,
            "sleepApnea": True,
            "supervisedProgramDuration": 6,
            "psychologicalClearance": True,
        }
    )
    assert result["candidacyScore"] == 60
    assert result["recommendation"] == "Recommended"
    assert result["bmiCategory"] == "Class II Obesity (BMI 35–39.9)"
    assert result["preferredProcedure"] == (
        "Sleeve Gastrectomy or RYGB — complete pre-operative workup including supervised program and psychological clearance"
    )


def test_may_be_appropriate_class1():
    # BMI 32 (+15), osteoarthritis (1 comorbidity +10), supervised 4 (+5),
    # no psych (-10), nutrition (+5) = 25.
    result = assess(
        {
            "bmi": 32,
            "osteoarthritis": True,
            "supervisedProgramDuration": 4,
            "psychologicalClearance": False,
            "nutritionConsultCompleted": True,
        }
    )
    assert result["candidacyScore"] == 25
    assert result["recommendation"] == "May Be Appropriate"
    assert result["bmiCategory"] == "Class I Obesity (BMI 30–34.9)"
    assert any("most payers require 6 months" in w for w in result["warnings"])
    assert any("Psychological evaluation not completed" in w for w in result["warnings"])


def test_not_recommended_low_bmi_with_contraindication():
    # BMI 28 (-20), no comorbidities (warning), supervised 0 (-10),
    # no psych (-10), active substance abuse (-30) -> clamped to 0.
    result = assess(
        {
            "bmi": 28,
            "supervisedProgramDuration": 0,
            "psychologicalClearance": False,
            "nutritionConsultCompleted": False,
            "activeSubstanceAbuse": True,
            "cirrhosis": True,
            "esophagealMotilityDisorder": True,
        }
    )
    assert result["candidacyScore"] == 0
    assert result["recommendation"] == "Not Recommended"
    assert result["bmiCategory"] == "BMI <30 — Below standard surgical threshold"
    assert any("Below standard threshold" in w for w in result["warnings"])
    assert any("No obesity-related comorbidities documented" in w for w in result["warnings"])
    assert any("Active substance abuse" in w for w in result["warnings"])
    assert any("Cirrhosis" in w for w in result["warnings"])
    assert any("Esophageal motility disorder" in w for w in result["warnings"])
    assert result["preferredProcedure"] == (
        "Address contraindications; optimize medical management; reassess in 6–12 months"
    )


def test_string_inputs_and_prior_bariatric():
    # Form fields arrive as strings; truthy/num must coerce them.
    # BMI 40 (+40), T2DM+HTN+sleepApnea (3 comorbidities +20), T2DM (+15),
    # supervised "6" (+10), psych "true" (+10), nutrition "true" (+5) = 100.
    result = assess(
        {
            "bmi": "40",
            "type2Diabetes": "true",
            "hypertension": "true",
            "sleepApnea": "true",
            "hba1c": "8",
            "supervisedProgramDuration": "6",
            "psychologicalClearance": "true",
            "nutritionConsultCompleted": "true",
            "priorBariatricSurgery": "true",
        }
    )
    assert result["candidacyScore"] == 100
    assert result["recommendation"] == "Strongly Recommended"
    assert any("3 obesity-related comorbidities" in f for f in result["keyFindings"])
    assert any("Prior bariatric surgery" in f for f in result["keyFindings"])
    # HbA1c exactly 8 -> poorly controlled branch.
    assert any("poorly controlled" in f for f in result["keyFindings"])


def test_bmi_integer_formatting_no_trailing_decimal():
    result = assess({"bmi": 42})
    assert any("BMI 42 —" in f for f in result["keyFindings"])


def test_bmi_float_formatting_preserved():
    result = assess({"bmi": 36.5})
    assert any("BMI 36.5 —" in f for f in result["keyFindings"])
