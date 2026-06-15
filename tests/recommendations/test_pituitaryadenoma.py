"""Tests for the Pituitary Adenoma logic engine.

Cases 1-5 ported 1:1 from old_static_code/server/neurosurgery.test.ts
("Pituitary Adenoma Logic"). The remission edge case is derived from the
TS postoperative-cortisol branch.
"""

from app.recommendations.modules.pituitaryadenoma import assess


def _base() -> dict:
    return {
        "tumorType": "nonfunctioning",
        "tumorSize": "macroadenoma",
        "tumorSizeMm": 20,
        "cavernousSinusInvasion": "none",
        "suprasellarExtension": False,
        "cysticComponent": False,
        "visualFieldDefect": False,
        "cranialNervePalsy": False,
        "hypopituitarism": False,
        "pituitaryApoplexy": False,
        "priorSurgery": False,
        "priorRadiation": False,
        "priorMedicalTherapy": False,
        "ageYears": 45,
        "pregnancyDesired": False,
        "surgicalRisk": "low",
        "preferMinimallyInvasive": False,
    }


def test_prolactinoma_medical_first():
    data = _base()
    data.update(
        {
            "tumorType": "prolactinoma",
            "tumorSize": "macroadenoma",
            "tumorSizeMm": 20,
            "prolactinLevelNgMl": 350,
            "ageYears": 38,
        }
    )
    result = assess(data)
    assert result["primaryRecommendation"] == "medical_therapy_first"
    assert "medicalOptions" in result
    assert len(result["medicalOptions"]) > 0


def test_apoplexy_with_visual_field_defect():
    data = _base()
    data.update(
        {
            "tumorType": "nonfunctioning",
            "tumorSize": "macroadenoma",
            "tumorSizeMm": 25,
            "suprasellarExtension": True,
            "visualFieldDefect": True,
            "cranialNervePalsy": True,
            "hypopituitarism": True,
            "pituitaryApoplexy": True,
            "ageYears": 55,
            "surgicalRisk": "moderate",
        }
    )
    result = assess(data)
    assert result["primaryRecommendation"] in ("surgery_first", "urgent_surgery")
    assert len(result["urgentFlags"]) > 0


def test_acromegaly_macroadenoma_surgery_first():
    data = _base()
    data.update(
        {
            "tumorType": "acromegaly_gh",
            "tumorSize": "macroadenoma",
            "tumorSizeMm": 22,
            "igf1Elevated": True,
        }
    )
    result = assess(data)
    assert result["primaryRecommendation"] == "surgery_first"
    assert len(result["surgicalApproach"]) > 0


def test_radiosurgery_residual_cushings():
    data = _base()
    data.update(
        {
            "tumorType": "cushings_acth",
            "tumorSize": "microadenoma",
            "tumorSizeMm": 7,
            "cavernousSinusInvasion": "unilateral",
            "lateNightSalivaryCortisolElevated": True,
            "priorSurgery": True,
            "ageYears": 40,
        }
    )
    result = assess(data)
    assert result["primaryRecommendation"] in ("surgery_first", "radiosurgery_adjuvant")


def test_cushings_perioperative_management():
    data = _base()
    data.update(
        {
            "tumorType": "cushings_acth",
            "tumorSize": "microadenoma",
            "tumorSizeMm": 6,
            "lateNightSalivaryCortisolElevated": True,
            "ageYears": 35,
        }
    )
    result = assess(data)
    assert len(result["perioperativeNotes"]) > 0


# ── Edge case derived from TS postop cortisol remission branch ──────────────
def test_cushings_postop_remission_confirmed():
    data = _base()
    data.update(
        {
            "tumorType": "cushings_acth",
            "tumorSize": "microadenoma",
            "postopCortisolUgDl": 1.0,
            "hoursPostSurgery": 48,
        }
    )
    result = assess(data)
    assert result["primaryRecommendation"] == "surgery_first"
    assert (
        result["recommendationTitle"]
        == "Biochemical Remission Confirmed — Glucocorticoid Replacement Required"
    )
    assert any("Adrenal insufficiency risk" in w for w in result["warnings"])


def test_recurrent_with_partial_response_radiosurgery():
    data = _base()
    data.update(
        {
            "tumorType": "acromegaly_gh",
            "tumorSize": "macroadenoma",
            "priorSurgery": True,
            "medicalTherapyResponse": "partial",
        }
    )
    result = assess(data)
    assert result["primaryRecommendation"] == "radiosurgery_adjuvant"
