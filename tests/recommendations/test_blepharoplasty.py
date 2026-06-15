"""Blepharoplasty engine — fixtures derived directly from blepharoplastyLogic.ts."""

from app.recommendations.modules.blepharoplasty import assess


def _base() -> dict:
    return {
        "age": "60",
        "sex": "female",
        "procedureType": "upper-blepharoplasty",
        "visualFieldDefect": False,
        "superiorVisualFieldLoss": "0",
        "marginalReflexDistance": "4",
        "levatorFunction": "10",
        "visualObstruction": False,
        "ptosisPresent": False,
        "ptosisUnilateral": False,
        "dermatochalasis": False,
        "fatProlapse": False,
        "browPtosis": False,
        "ectropion": False,
        "entropion": False,
        "lagophthalmos": False,
        "difficultyReading": False,
        "difficultyDriving": False,
        "difficultyWithActivities": False,
        "headacheFromBrowCompensation": False,
        "eyeStrain": False,
        "symptomDurationMonths": "0",
        "marginalReflexToLidFold": "0",
        "excessSkinOverhang": False,
        "triedEyelidTaping": False,
        "triedPtosisProps": False,
        "asa": "2",
        "dryEye": False,
        "thyroidEyeDisease": False,
        "priorEyelidSurgery": False,
        "anticoagulation": False,
    }


def test_not_indicated_baseline():
    r = assess(_base())
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Indicated"
    assert r["functionalCriteriaMet"] is False
    assert r["ptosisGrade"] == "N/A"


def test_severe_ptosis_strongly_indicated():
    r = assess({**_base(), "ptosisPresent": True, "marginalReflexDistance": "1"})
    assert r["candidacyScore"] == 40
    assert r["functionalCriteriaMet"] is True
    assert r["ptosisGrade"] == "Severe ptosis (MRD1 ≤1mm)"
    assert r["recommendation"] == "Strongly Indicated (Functional)"
    assert any("Severe ptosis: MRD1 1mm" in f for f in r["keyFindings"])


def test_moderate_ptosis_indicated():
    r = assess({**_base(), "ptosisPresent": True, "marginalReflexDistance": "2"})
    assert r["candidacyScore"] == 30
    assert r["functionalCriteriaMet"] is True
    assert r["ptosisGrade"] == "Moderate ptosis (MRD1 ≤2mm)"
    # functionalCriteriaMet True but score 30 < 40 -> Indicated (Functional)
    assert r["recommendation"] == "Indicated (Functional)"


def test_mild_ptosis_cosmetic_only():
    r = assess({**_base(), "ptosisPresent": True, "marginalReflexDistance": "3"})
    assert r["candidacyScore"] == 15
    assert r["functionalCriteriaMet"] is False
    assert r["ptosisGrade"] == "Mild ptosis (MRD1 3mm)"
    assert r["recommendation"] == "Cosmetic Only"


def test_normal_mrd_with_ptosis_present():
    r = assess({**_base(), "ptosisPresent": True, "marginalReflexDistance": "4"})
    assert r["candidacyScore"] == 0
    assert r["ptosisGrade"] == "Normal (MRD1 >3mm)"
    assert r["recommendation"] == "Not Indicated"


def test_visual_field_loss_meets_cms():
    r = assess({**_base(), "visualFieldDefect": True, "superiorVisualFieldLoss": "15"})
    assert r["candidacyScore"] == 35
    assert r["functionalCriteriaMet"] is True
    # 35 >= 25 -> Indicated (Functional)
    assert r["recommendation"] == "Indicated (Functional)"
    assert any("meets CMS criterion of ≥12°" in f for f in r["keyFindings"])


def test_visual_field_loss_borderline():
    r = assess({**_base(), "visualFieldDefect": True, "superiorVisualFieldLoss": "9"})
    assert r["candidacyScore"] == 20
    assert r["functionalCriteriaMet"] is False
    assert r["recommendation"] == "Cosmetic Only"
    assert any("borderline" in f for f in r["keyFindings"])


def test_visual_field_defect_unquantified():
    r = assess({**_base(), "visualFieldDefect": True, "superiorVisualFieldLoss": "0"})
    assert r["candidacyScore"] == 10
    assert r["functionalCriteriaMet"] is False
    assert r["recommendation"] == "Cosmetic Only"


def test_dermatochalasis_with_obstruction():
    r = assess({**_base(), "dermatochalasis": True, "visualObstruction": True})
    assert r["candidacyScore"] == 25
    assert r["functionalCriteriaMet"] is True
    assert r["recommendation"] == "Indicated (Functional)"


def test_dermatochalasis_with_overhang_only():
    r = assess({**_base(), "dermatochalasis": True, "excessSkinOverhang": True})
    assert r["candidacyScore"] == 15
    assert r["functionalCriteriaMet"] is False
    assert r["recommendation"] == "Cosmetic Only"


def test_ectropion_functional_and_warning():
    r = assess({**_base(), "ectropion": True})
    assert r["candidacyScore"] == 30
    assert r["functionalCriteriaMet"] is True
    assert any("corneal exposure risk" in w for w in r["warnings"])


def test_lagophthalmos_warning():
    r = assess({**_base(), "lagophthalmos": True})
    assert r["candidacyScore"] == 25
    assert r["functionalCriteriaMet"] is True
    assert any("Lagophthalmos" in w for w in r["warnings"])


def test_strongly_indicated_full_functional():
    # severe ptosis (40) + VF >=12 (35) + reading (10) + driving (10) = 95
    r = assess({
        **_base(),
        "ptosisPresent": True,
        "marginalReflexDistance": "1",
        "visualFieldDefect": True,
        "superiorVisualFieldLoss": "20",
        "difficultyReading": True,
        "difficultyDriving": True,
    })
    assert r["candidacyScore"] == 95
    assert r["recommendation"] == "Strongly Indicated (Functional)"


def test_score_clamped_to_100():
    # 40 + 35 + 25(dermato+obstruction) + 10 + 10 + 8 + 5 + 8 = 141 -> clamped 100
    r = assess({
        **_base(),
        "ptosisPresent": True,
        "marginalReflexDistance": "1",
        "visualFieldDefect": True,
        "superiorVisualFieldLoss": "20",
        "dermatochalasis": True,
        "visualObstruction": True,
        "difficultyReading": True,
        "difficultyDriving": True,
        "headacheFromBrowCompensation": True,
        "eyeStrain": True,
        "difficultyWithActivities": True,
    })
    assert r["candidacyScore"] == 100


def test_thyroid_eye_disease_penalty():
    # ectropion 30 - thyroid 15 = 15, but functionalCriteriaMet True -> Indicated
    r = assess({**_base(), "ectropion": True, "thyroidEyeDisease": True})
    assert r["candidacyScore"] == 15
    assert r["functionalCriteriaMet"] is True
    assert r["recommendation"] == "Indicated (Functional)"
    assert any("Thyroid eye disease" in w for w in r["warnings"])


def test_asa4_penalty_and_score_floor():
    # baseline 0 - 15 (asa4) clamped to 0
    r = assess({**_base(), "asa": "4"})
    assert r["candidacyScore"] == 0
    assert any("ASA Class IV" in w for w in r["warnings"])


def test_symptom_duration_bonus():
    r = assess({**_base(), "difficultyReading": True, "symptomDurationMonths": "18"})
    # 10 (reading) + 5 (duration) = 15
    assert r["candidacyScore"] == 15
    assert any("18 months of functional symptoms" in f for f in r["keyFindings"])


def test_references_present():
    r = assess(_base())
    assert len(r["references"]) == 5
    assert r["references"][0].startswith("CMS LCD L34462")
