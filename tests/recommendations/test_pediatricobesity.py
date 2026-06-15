"""Oracle tests for the Pediatric Obesity module.

Ported 1:1 from old_static_code/server/pediatrics.test.ts
(describe "Pediatric Obesity Logic").
"""

import re

from app.recommendations.modules.pediatricobesity import assess

BASE_INPUT = {
    "ageYears": 10,
    "sex": "male",
    "bmiPercentile": 75,
    "bmiPercentOfP95": 85,
    "obesityCategory": "healthy_weight",
    "durationOfObesityYears": 0,
    "priorTreatmentAttempts": 0,
    "hasType2Diabetes": False,
    "hasPrediabetes": False,
    "hasHypertension": False,
    "hasDyslipidemia": False,
    "hasNASH": False,
    "hasOSA": False,
    "hasPCOS": False,
    "hasOrthopedicComplications": False,
    "hasIdiopathicIntracranialHypertension": False,
    "hasDepression": False,
    "hasBingeEatingDisorder": False,
    "familyHistoryObesity": False,
    "familyHistoryT2DM": False,
    "familyMotivation": "moderate",
    "priorGLP1Use": False,
    "priorMetforminUse": False,
    "hasContraindicationToGLP1": False,
    "isReadyForBariatric": False,
    "hasBariatricContraindication": False,
}


def _merge(**over):
    return {**BASE_INPUT, **over}


def test_healthy_weight_guidance():
    result = assess(BASE_INPUT)
    assert re.search(r"healthy|prevention", result["primaryRecommendation"], re.I)
    assert len(result["urgentFlags"]) == 0


def test_overweight_stage1_prevention_plus():
    result = assess(_merge(bmiPercentile=88, obesityCategory="overweight"))
    assert re.search(r"STAGE 1|Prevention Plus", result["treatmentIntensity"], re.I)


def test_class1_no_prior_attempts_stage2():
    result = assess(
        _merge(
            bmiPercentile=97,
            bmiPercentOfP95=100,
            obesityCategory="class1_obesity",
            priorTreatmentAttempts=0,
        )
    )
    assert re.search(r"STAGE 2|Structured", result["treatmentIntensity"], re.I)


def test_iih_flagged_urgent():
    result = assess(
        _merge(
            bmiPercentile=99,
            bmiPercentOfP95=120,
            obesityCategory="class2_obesity",
            hasIdiopathicIntracranialHypertension=True,
        )
    )
    assert re.search(r"intracranial|IIH|neurology", " ".join(result["urgentFlags"]), re.I)


def test_t2dm_urgent_with_metformin():
    result = assess(
        _merge(
            bmiPercentile=99,
            obesityCategory="class2_obesity",
            hasType2Diabetes=True,
        )
    )
    assert re.search(r"diabetes|metformin", " ".join(result["urgentFlags"]), re.I)


def test_bariatric_surgery_severe_obesity_with_comorbidities():
    result = assess(
        _merge(
            ageYears=16,
            bmiPercentile=99.9,
            bmiPercentOfP95=145,
            obesityCategory="class3_obesity",
            isReadyForBariatric=True,
            hasType2Diabetes=True,
        )
    )
    assert re.search(r"bariatric|surgery", result["bariatricConsideration"], re.I)
