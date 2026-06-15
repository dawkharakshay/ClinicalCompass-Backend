"""Tests for the Biliary Strictures Clinical Compass port.

Cases ported 1:1 from old_static_code/server/gi-modules.test.ts
(describe "assessBiliaryStricture") plus additional branch-coverage fixtures.
"""

from __future__ import annotations

import re

import pytest

from app.recommendations.modules.biliarystrictures import assess

BASE_INPUT = {
    "strictureLocation": "distal_cbd",
    "suspectedEtiology": "unknown_malignant_suspected",
    "hasProximalDilation": True,
    "proximalDuctDiameterMm": 14,
    "hasJaundice": True,
    "bilirubinMgDl": 9.5,
    "hasAbdominalPain": True,
    "hasWeightLoss": True,
    "hasFever": False,
    "hasChills": False,
    "hasPruritus": True,
    "ca199": 380,
    "hasCTScan": True,
    "hasMRCP": False,
    "hasERCP": False,
    "hasEUSPerformed": False,
    "hasPETScan": False,
    "imagingFindingsMalignantFeatures": False,
    "tissueAcquisitionResult": "not_performed",
    "hasPSC": False,
    "hasIBDWithPSC": False,
    "hasDominantStricture": False,
    "hasCholangiocarcInPSC": False,
    "hasBiliaryStenosis": True,
    "hasBiliaryStent": False,
    "hasStentOcclusion": False,
    "isResectable": False,
    "hasVascularInvolvement": False,
    "hasLymphadenopathy": False,
    "hasDistantMetastases": False,
    "hasLiverMetastases": False,
    "ageYears": 68,
    "isSurgicalCandidate": True,
    "performanceStatus": "good",
    "hasCoagulopathy": False,
    "isOnAnticoagulation": False,
}


def _with(**overrides):
    out = dict(BASE_INPUT)
    out.update(overrides)
    return out


# ─── Ported TS oracle cases ──────────────────────────────────────────────────


def test_eus_fnb_distal_cbd_elevated_ca199():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"]
    assert result["tissueAcquisitionStrategy"]
    assert re.match(r"^[ABC]$", result["evidenceLevel"])


def test_mrcp_before_ercp_initial_workup():
    result = assess(BASE_INPUT)
    assert result["diagnosticWorkup"]
    assert re.search(r"MRCP|EUS|imaging", result["diagnosticWorkup"], re.I)


def test_cholangioscopy_after_nondiagnostic_brush():
    result = assess(
        _with(
            hasERCP=True,
            tissueAcquisitionResult="non_diagnostic",
            tissueMethod="ercp_brush_cytology",
            numberOfPriorBiopsyAttempts=1,
        )
    )
    assert result["tissueAcquisitionStrategy"]


def test_flags_cholangitis_urgent():
    result = assess(_with(hasFever=True, hasChills=True))
    assert any(
        re.search(r"cholangitis|urgent|sepsis", f, re.I) for f in result["urgentFlags"]
    )


def test_psc_surveillance_dominant_stricture():
    result = assess(
        _with(
            hasPSC=True,
            pscType="large_duct",
            hasDominantStricture=True,
            suspectedEtiology="psc",
        )
    )
    assert result["pscManagement"]


def test_returns_references():
    result = assess(BASE_INPUT)
    assert len(result["references"]) > 0


# ─── Additional branch-coverage fixtures ─────────────────────────────────────


def test_malignancy_risk_high_scoring():
    # imaging(2)+ca199>100(2)+weightloss(1)+age>60(1) = 6 -> HIGH
    result = assess(_with(imagingFindingsMalignantFeatures=True))
    assert "MALIGNANCY RISK: HIGH" in result["malignancyRiskAssessment"]
    assert result["primaryRecommendation"].startswith("High malignancy risk")


def test_malignancy_risk_low_when_no_features():
    result = assess(
        _with(
            ca199=10,
            hasWeightLoss=False,
            ageYears=40,
            imagingFindingsMalignantFeatures=False,
        )
    )
    assert "MALIGNANCY RISK: LOW" in result["malignancyRiskAssessment"]


def test_acute_cholangitis_primary_recommendation():
    result = assess(_with(hasFever=True, hasChills=True, hasJaundice=True))
    assert result["primaryRecommendation"].startswith("ACUTE CHOLANGITIS")


def test_igg4_elevated_steroid_trial():
    # No fever/chills triad, no PSC dominant -> igg4 branch wins for primary rec
    result = assess(_with(igg4=200))
    assert any("IgG4 200 mg/dL (>135)" in f for f in result["urgentFlags"])
    assert result["primaryRecommendation"].startswith("IgG4-related sclerosing cholangitis")
    assert "IgG4 elevated" in result["malignancyRiskAssessment"]


def test_severe_jaundice_urgent_flag():
    result = assess(_with(bilirubinMgDl=18))
    assert any("Severe jaundice (bilirubin 18 mg/dL)" in f for f in result["urgentFlags"])


def test_stent_occlusion_urgent_flag():
    result = assess(_with(hasStentOcclusion=True))
    assert any("Biliary stent occlusion" in f for f in result["urgentFlags"])


def test_hilar_tissue_and_drainage():
    result = assess(_with(strictureLocation="hilar_bismuth_III"))
    assert "HILAR STRICTURE" in result["tissueAcquisitionStrategy"]
    assert "HILAR STRICTURE (Klatskin tumor)" in result["biliarDrainageStrategy"]


def test_anastomotic_drainage():
    result = assess(_with(strictureLocation="anastomotic"))
    assert "POST-TRANSPLANT ANASTOMOTIC STRICTURE" in result["biliarDrainageStrategy"]


def test_no_drainage_when_no_jaundice_or_stenosis():
    result = assess(_with(hasJaundice=False, hasBiliaryStenosis=False))
    assert result["biliarDrainageStrategy"] == (
        "No biliary drainage required at this time. Monitor bilirubin and LFTs."
    )


def test_imaging_required_when_no_ct_no_mrcp():
    result = assess(_with(hasCTScan=False, hasMRCP=False))
    assert result["diagnosticWorkup"].startswith("IMAGING REQUIRED (ASGE 2024)")


def test_imaging_complete_when_mrcp_present():
    result = assess(_with(hasMRCP=True))
    assert result["diagnosticWorkup"].startswith("Cross-sectional imaging performed")


def test_resectable_oncology():
    result = assess(_with(tissueAcquisitionResult="malignant", isResectable=True))
    assert "RESECTABLE BILIARY TRACT CANCER" in result["resectabilityAndOncology"]


def test_unresectable_oncology():
    result = assess(
        _with(tissueAcquisitionResult="malignant", isResectable=False, hasDistantMetastases=True)
    )
    assert "UNRESECTABLE/METASTATIC" in result["resectabilityAndOncology"]


def test_benign_tissue_strategy():
    result = assess(_with(tissueAcquisitionResult="benign"))
    assert "Benign tissue result" in result["tissueAcquisitionStrategy"]


def test_malignant_tissue_confirmed_strategy():
    result = assess(_with(tissueAcquisitionResult="malignant"))
    assert "Tissue acquisition confirmed: malignant" in result["tissueAcquisitionStrategy"]


def test_rationale_uses_not_measured_when_markers_absent():
    inp = _with()
    inp.pop("ca199")
    result = assess(inp)
    assert "CA 19-9: not measured" in result["rationale"]
    assert "IgG4: not measured" in result["rationale"]


def test_result_shape_keys():
    result = assess(BASE_INPUT)
    expected = {
        "primaryRecommendation",
        "malignancyRiskAssessment",
        "diagnosticWorkup",
        "tissueAcquisitionStrategy",
        "biliarDrainageStrategy",
        "pscManagement",
        "resectabilityAndOncology",
        "surveillancePlan",
        "urgentFlags",
        "nextSteps",
        "evidenceLevel",
        "rationale",
        "references",
    }
    assert set(result.keys()) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
