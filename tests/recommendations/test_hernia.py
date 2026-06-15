"""Tests for the Hernia Repair Clinical Compass engine.

No TS test covers herniaLogic.ts (new-modules.test.ts references lumbar disc
herniation, an unrelated module). Cases below are authored from the branches of
calculateHerniaScore in old_static_code/client/src/lib/herniaLogic.ts, covering
each major decision path plus contraindication/risk-deduction paths. Scores are
traced by hand from the TS arithmetic.
"""

from app.recommendations.modules.hernia import assess


def _base(**overrides) -> dict:
    data = {
        "age": 50,
        "sex": "male",
        "herniaType": "inguinal",
        "side": "left",
        "defectSize": 0,
        "symptomatic": False,
        "painLevel": 0,
        "reducible": True,
        "incarcerated": False,
        "strangulated": False,
        "durationMonths": 0,
        "worseningSymptoms": False,
        "priorRepair": False,
        "recurrent": False,
        "obesity": False,
        "bmi": 25,
        "diabetes": False,
        "smoking": False,
        "copd": False,
        "ascites": False,
        "immunosuppressed": False,
        "asa": 1,
        "priorAbdominalSurgery": False,
        "coagulopathy": False,
        "triedTruss": False,
        "watchfulWaiting": False,
        "watchfulWaitingDuration": 0,
    }
    data.update(overrides)
    return data


def test_strangulated_emergent():
    r = assess(_base(strangulated=True, defectSize=3))
    assert r["candidacyScore"] == 100
    assert r["urgency"] == "Emergent"
    assert r["recommendation"] == "Strongly Indicated"
    assert r["approach"] == (
        "Emergency open or laparoscopic repair — bowel viability assessment required"
    )
    assert r["meshRecommendation"].startswith("Mesh use in contaminated field")
    assert "Strangulated hernia — emergency surgery" in r["keyFindings"]


def test_incarcerated_semi_urgent():
    # incarcerated 50 + symptomatic 30 = 80 -> capped path strongly indicated
    r = assess(_base(incarcerated=True, symptomatic=True, defectSize=1))
    assert r["candidacyScore"] == 80
    assert r["urgency"] == "Semi-urgent"
    assert r["recommendation"] == "Strongly Indicated"
    assert r["approach"] == (
        "Urgent laparoscopic or open repair — TEP/TAPP or open inguinal repair"
    )
    # incarcerated/strangulated branch always uses contaminated-field mesh text
    assert r["meshRecommendation"].startswith("Mesh use in contaminated field")
    assert "Incarcerated hernia — semi-urgent repair" in r["keyFindings"]


def test_strongly_indicated_femoral():
    # symptomatic 30 + pain>=7 15 + femoral 20 = 65 -> strongly indicated
    r = assess(_base(symptomatic=True, painLevel=8, herniaType="femoral", side="na",
                     defectSize=0))
    assert r["candidacyScore"] == 65
    assert r["urgency"] == "Elective"
    assert r["recommendation"] == "Strongly Indicated"
    # non-inguinal/incisional/ventral -> generic approach
    assert r["approach"] == (
        "Laparoscopic or open repair per anatomy and surgeon experience"
    )
    # defectSize 0 < 2 -> small-defect mesh text
    assert r["meshRecommendation"].startswith("Mesh repair recommended; primary repair")
    assert any("Femoral hernia" in k for k in r["keyFindings"])
    assert any("Pain level 8/10" in k for k in r["keyFindings"])


def test_strongly_indicated_incisional_large_defect():
    # symptomatic 30 + pain>=7 15 + defect>=4 10 + worsening 10 = 65
    r = assess(_base(symptomatic=True, painLevel=9, herniaType="incisional",
                     side="midline", defectSize=5, worseningSymptoms=True))
    assert r["candidacyScore"] == 65
    assert r["recommendation"] == "Strongly Indicated"
    assert r["approach"] == (
        "Laparoscopic IPOM or open component separation — mesh required for defects >2cm"
    )
    assert r["meshRecommendation"] == (
        "Mesh repair strongly recommended — reduces recurrence from 15–20% to <5%"
    )
    assert any("Defect size 5cm" in k for k in r["keyFindings"])


def test_indicated_moderate():
    # symptomatic 30 only -> 30 indicated
    r = assess(_base(symptomatic=True, defectSize=1, painLevel=0))
    assert r["candidacyScore"] == 30
    assert r["recommendation"] == "Indicated"
    assert r["approach"] == (
        "Elective laparoscopic or open repair; optimize modifiable risk factors pre-operatively"
    )
    assert r["meshRecommendation"] == "Mesh repair recommended per hernia size and type"


def test_watchful_waiting_asymptomatic_inguinal():
    # asymptomatic inguinal, pain 0: only defect>=2 contributes -> score 5? need >=10.
    # pain 1-3 gives +3; defect>=2 gives +5; -> 8 still <10. Use pain 4 (8) -> not WW.
    # Build a 10-14 score: defect>=4 (10) only, asymptomatic.
    r = assess(_base(symptomatic=False, herniaType="inguinal", painLevel=0,
                     defectSize=4))
    assert r["candidacyScore"] == 10
    assert r["recommendation"] == "Watchful Waiting Acceptable"
    assert r["approach"].startswith("Watchful waiting is safe for asymptomatic")
    assert r["meshRecommendation"] == "Mesh repair if surgery elected"
    assert any("Asymptomatic inguinal hernia" in k for k in r["keyFindings"])


def test_not_recommended_low_score():
    r = assess(_base())  # all baseline -> score 0
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Recommended"
    assert r["approach"] == (
        "Conservative management; address contraindications; reassess in 3–6 months"
    )
    assert r["meshRecommendation"] == "N/A"
    assert r["urgency"] == "Elective"


def test_risk_deductions_clamp_to_zero():
    # symptomatic 30 - ascites 20 - asa4 20 = -10 -> clamped to 0
    r = assess(_base(symptomatic=True, ascites=True, asa=4, defectSize=0,
                     painLevel=0))
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Recommended"
    assert any("Ascites" in w for w in r["warnings"])
    assert any("ASA Class IV" in w for w in r["warnings"])


def test_morbid_obesity_deduction_and_warning():
    # symptomatic 30 + pain>=7 15 + defect>=4 10 = 55, - morbid obesity 10 = 45 -> Indicated
    r = assess(_base(symptomatic=True, painLevel=7, defectSize=4, obesity=True,
                     bmi=42))
    assert r["candidacyScore"] == 45
    assert r["recommendation"] == "Indicated"
    assert any("BMI 42" in w and "morbid obesity" in w for w in r["warnings"])


def test_inguinal_female_and_recurrent():
    # symptomatic 30 + inguinal-female 10 + recurrent 10 = 50 -> Indicated (>=30, <55)
    r = assess(_base(symptomatic=True, sex="female", herniaType="inguinal",
                     recurrent=True, painLevel=0, defectSize=0))
    assert r["candidacyScore"] == 50
    assert r["recommendation"] == "Indicated"
    assert any("Inguinal hernia in female" in k for k in r["keyFindings"])
    assert any("Recurrent hernia" in k for k in r["keyFindings"])
    assert any("experienced hernia surgeon" in w for w in r["warnings"])


def test_string_inputs_coerced():
    # form values arrive as strings; ensure numeric coercion matches
    r = assess(_base(symptomatic=True, painLevel="8", defectSize="5",
                     durationMonths="12", smoking=True, diabetes=True))
    # 30 + 15 + 10 (defect>=4) + 5 (duration>=12) = 60 -> Strongly Indicated
    assert r["candidacyScore"] == 60
    assert r["recommendation"] == "Strongly Indicated"
    assert any("Active smoking" in w for w in r["warnings"])
    assert any("Diabetes" in w for w in r["warnings"])
