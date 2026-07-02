"""Tests for the Therapeutic EUS module.

Cases ported 1:1 from old_static_code/server/gi-modules.test.ts
(describe "assessTherapeuticEUS").
"""

import re

import pytest

from app.recommendations.modules.therapeuticeus import assess

BASE_INPUT = {
    "indication": "ercp_failure",
    "erpFailureReason": "failed_cannulation",
    "obstructionLevel": "distal_cbd",
    "hasAlteredAnatomy": False,
    "hasIntrahepticDilation": False,
    "hasAscites": False,
    "hasPriorBiliaryStent": False,
    "hasMalignantObstruction": True,
    "malignancyType": "pancreatic_cancer",
    "isResectable": False,
    "hasAcuteCholecystitis": False,
    "isSurgicalHighRisk": False,
    "hasCysticDuctObstruction": False,
    "gallbladderAccessibleByEUS": False,
    "hasPancreaticDuctDilation": False,
    "hasPancreaticDuctStricture": False,
    "hasPancreaticFistula": False,
    "hasDisconnectedPancreaticDuctSyndrome": False,
    "hasCoagulopathy": False,
    "isOnAnticoagulation": False,
    "performanceStatus": "good",
    "ageYears": 68,
    "hasPriorEUSBD": False,
    "hasPriorPercutaneousDrainage": False,
    "hasPriorERCP": True,
    "numberOfPriorERCPAttempts": 1,
}


def test_recommends_eus_cds_for_distal_cbd_after_failed_ercp():
    result = assess(BASE_INPUT)
    assert result["primaryRecommendation"]
    assert result["eusBDApproach"]
    assert re.match(r"^[ABC]$", result["evidenceLevel"])
    # distal_cbd + ercp_failure -> EUS-CDS preferred primary recommendation
    assert "EUS-CDS" in result["primaryRecommendation"]


def test_recommends_eus_hgs_for_hilar_with_intrahepatic_dilation():
    result = assess({**BASE_INPUT, "obstructionLevel": "hilar", "hasIntrahepticDilation": True})
    assert result["eusBDApproach"]
    assert "EUS-HEPATICOGASTROSTOMY" in result["eusBDApproach"]


def test_recommends_eus_gbd_for_acute_cholecystitis_high_surgical_risk():
    result = assess(
        {
            **BASE_INPUT,
            "indication": "gallbladder_drainage",
            "hasAcuteCholecystitis": True,
            "isSurgicalHighRisk": True,
            "gallbladderAccessibleByEUS": True,
        }
    )
    assert result["primaryRecommendation"]
    assert "EUS-GBD" in result["primaryRecommendation"]
    assert "EUS-GUIDED GALLBLADDER DRAINAGE" in result["eusBDApproach"]


def test_recommends_eus_hgs_for_altered_anatomy_roux_en_y():
    result = assess(
        {
            **BASE_INPUT,
            "indication": "altered_anatomy",
            "erpFailureReason": "altered_anatomy_access",
            "hasAlteredAnatomy": True,
            "alteredAnatomyType": "roux_en_y",
            "obstructionLevel": "hilar",
        }
    )
    assert result["eusBDApproach"]
    assert "EUS-HEPATICOGASTROSTOMY" in result["eusBDApproach"]
    assert result["primaryRecommendation"].startswith("Altered anatomy")


def test_returns_references():
    result = assess(BASE_INPUT)
    assert len(result["references"]) > 0


# ─── Additional branch / edge coverage derived from the TS source ─────────────


def test_urgent_flags_coagulopathy_and_thrombocytopenia():
    result = assess(
        {
            **BASE_INPUT,
            "hasCoagulopathy": True,
            "inrValue": 2.0,
            "plateletCount": 40000,
        }
    )
    flags = " ".join(result["urgentFlags"])
    # TS interpolates `${input.inrValue}` where inrValue is a number, so JS
    # renders 2.0 as "2" (String(2.0) === "2"). Match the TS source exactly.
    assert "Coagulopathy (INR 2)" in flags
    assert "Thrombocytopenia (platelets 40000)" in flags


def test_no_coagulopathy_flag_when_inr_at_or_below_threshold():
    result = assess({**BASE_INPUT, "hasCoagulopathy": True, "inrValue": 1.5})
    assert all("Coagulopathy" not in f for f in result["urgentFlags"])


def test_acute_cholecystitis_in_surgical_candidate_flag():
    result = assess(
        {
            **BASE_INPUT,
            "indication": "gallbladder_drainage",
            "hasAcuteCholecystitis": True,
            "isSurgicalHighRisk": False,
        }
    )
    assert any("laparoscopic cholecystectomy is preferred" in f for f in result["urgentFlags"])


def test_resectable_malignancy_flag():
    result = assess(
        {
            **BASE_INPUT,
            "indication": "malignant_biliary_obstruction",
            "isResectable": True,
        }
    )
    assert any("Resectable malignancy" in f for f in result["urgentFlags"])


def test_ascites_flag_in_hgs_path():
    result = assess(
        {
            **BASE_INPUT,
            "obstructionLevel": "hilar",
            "hasIntrahepticDilation": True,
            "hasAscites": True,
        }
    )
    assert any("Ascites:" in f for f in result["urgentFlags"])


def test_choledocholithiasis_rendezvous_path():
    result = assess(
        {
            **BASE_INPUT,
            "indication": "choledocholithiasis_ercp_failed",
            "obstructionLevel": "intrahepatic",
            "hasIntrahepticDilation": False,
            "hasAlteredAnatomy": False,
        }
    )
    assert "EUS-RENDEZVOUS" in result["eusBDApproach"]


def test_pancreatic_duct_path():
    result = assess(
        {
            **BASE_INPUT,
            "indication": "benign_biliary_stricture",
            "obstructionLevel": "pancreatic_duct",
            "hasIntrahepticDilation": False,
            "hasAlteredAnatomy": False,
            "hasPancreaticDuctDilation": True,
        }
    )
    assert "EUS-GUIDED PANCREATIC DUCT DRAINAGE" in result["eusBDApproach"]


def test_fallback_approach_when_no_branch_matches():
    result = assess(
        {
            **BASE_INPUT,
            "indication": "benign_biliary_stricture",
            "obstructionLevel": "intrahepatic",
            "hasIntrahepticDilation": False,
            "hasAlteredAnatomy": False,
            "hasPancreaticDuctDilation": False,
        }
    )
    assert "to be determined" in result["eusBDApproach"]
    # default nextSteps populated when none added
    assert "Confirm ERCP failure documentation" in result["nextSteps"]


def test_distal_cbd_requires_cbd_diameter_present():
    # distal_cbd with no cbdDiameterMm -> falls through (not EUS-CDS approach)
    result = assess(
        {
            **BASE_INPUT,
            "obstructionLevel": "distal_cbd",
            "hasIntrahepticDilation": False,
            "hasAlteredAnatomy": False,
        }
    )
    assert "EUS-CHOLEDOCHODUODENOSTOMY" not in result["eusBDApproach"]
    # but primaryRecommendation still flags ercp_failure + distal_cbd
    assert "EUS-CDS" in result["primaryRecommendation"]


def test_distal_cbd_dilated_uses_cds_approach():
    result = assess({**BASE_INPUT, "cbdDiameterMm": 14})
    assert "EUS-CHOLEDOCHODUODENOSTOMY" in result["eusBDApproach"]
    assert "CBD diameter: 14mm" in result["rationale"]


def test_rationale_not_measured_when_no_cbd():
    result = assess(BASE_INPUT)
    assert "CBD diameter: not measured" in result["rationale"]


def test_rationale_underscores_replaced():
    result = assess({**BASE_INPUT, "indication": "ercp_failure"})
    assert "Indication: ercp failure" in result["rationale"]
    assert "ERCP failure reason: failed cannulation" in result["rationale"]


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
