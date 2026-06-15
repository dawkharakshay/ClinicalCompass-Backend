"""Oracle tests for the Acute Ischemic Stroke engine.

Ported 1:1 from old_static_code/server/neuro-ophtho.test.ts
("Acute Ischemic Stroke Logic" describe block).
"""

from __future__ import annotations

import copy

from app.recommendations.modules.stroke import assess

BASE_INPUT = {
    "onsetWindow": "within_3h",
    "lastKnownWellMinutes": 90,
    "nihssScore": 12,
    "isDisabling": True,
    "vesselOcclusion": "no_occlusion",
    "aspectsScore": 9,
    "imagingAvailability": "ct_only",
    "perfusionMismatchRatio": 1.0,
    "coreInfarctVolumeMl": 20,
    "ageYears": 65,
    "hasAnticoagulation": False,
    "anticoagulantType": "none",
    "inrIfWarfarin": 1.0,
    "plateletCount": 200,
    "bloodGlucose": 120,
    "systolicBP": 160,
    "hasRecentSurgery": False,
    "hasRecentIntracranialSurgery": False,
    "hasHistoryICH": False,
    "hasActiveBleeding": False,
    "hasEndocarditis": False,
    "isPregnant": False,
    "isPostAcutePhase": False,
    "strokeMechanism": "unknown",
    "hasAtrialFibrillation": False,
    "nihssAtPresentation": 12,
}


def _input(**overrides) -> dict:
    data = copy.deepcopy(BASE_INPUT)
    data.update(overrides)
    return data


def test_tpa_eligible_disabling_within_3h_no_contraindications():
    result = assess(_input())
    assert result["ivThrombolysisEligibility"] == "eligible"
    assert "alteplase" in result["ivThrombolysisRationale"]


def test_tpa_ineligible_prior_ich():
    result = assess(_input(hasHistoryICH=True))
    assert result["ivThrombolysisEligibility"] == "ineligible"
    assert "ICH" in result["ivThrombolysisRationale"]


def test_tpa_ineligible_doac():
    result = assess(_input(hasAnticoagulation=True, anticoagulantType="doac"))
    assert result["ivThrombolysisEligibility"] == "ineligible"
    assert "DOAC" in result["ivThrombolysisRationale"]


def test_thrombectomy_eligible_anterior_lvo_within_6h():
    result = assess(
        _input(vesselOcclusion="lvo_anterior", nihssScore=14, aspectsScore=8)
    )
    assert result["thrombectomyEligibility"] == "eligible"
    assert "Thrombectomy" in result["primaryRecommendation"]


def test_extended_window_thrombectomy_anterior_lvo_9_to_24h():
    result = assess(
        _input(
            vesselOcclusion="lvo_anterior",
            onsetWindow="9_to_24h",
            nihssScore=14,
            aspectsScore=8,
            ageYears=70,
        )
    )
    assert result["thrombectomyEligibility"] == "consider_extended_window"
    assert "DAWN" in result["thrombectomyRationale"]


def test_thrombectomy_eligible_basilar_nihss_ge_10():
    result = assess(_input(vesselOcclusion="lvo_posterior", nihssScore=15))
    assert result["thrombectomyEligibility"] == "eligible"
    assert "Basilar" in result["thrombectomyRationale"]


def test_sbp_over_185_urgent_flag():
    result = assess(_input(systolicBP=195))
    assert any("SBP" in f for f in result["urgentFlags"])


def test_early_anticoagulation_mild_af_stroke_48_72h():
    result = assess(
        _input(
            isPostAcutePhase=True,
            hasAtrialFibrillation=True,
            nihssAtPresentation=6,
            strokeMechanism="cardioembolic",
        )
    )
    assert "48-72h" in result["anticoagulationTiming"]


def test_delays_anticoagulation_14_days_severe_af_stroke():
    result = assess(
        _input(
            isPostAcutePhase=True,
            hasAtrialFibrillation=True,
            nihssAtPresentation=20,
            strokeMechanism="cardioembolic",
        )
    )
    assert "14 days" in result["anticoagulationTiming"]


def test_returns_evidence_level_and_references():
    result = assess(_input())
    assert "Class I" in result["evidenceLevel"]
    assert len(result["references"]) > 0
