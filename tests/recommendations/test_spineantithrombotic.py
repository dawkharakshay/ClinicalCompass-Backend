"""Spine Antithrombotic engine — oracle cases ported 1:1 from
old_static_code/server/neurosurgery.test.ts (Spine Antithrombotic Logic),
plus branch coverage derived from spineAntithromboticLogic.ts."""

from app.recommendations.modules.spineantithrombotic import assess


def _base() -> dict:
    return {
        "procedureType": "lumbar_fusion",
        "emergencyProcedure": False,
        "estimatedBloodLossHigh": False,
        "currentAnticoagulant": "none",
        "indicationForAnticoagulation": "none",
        "vteRiskLevel": "moderate",
        "priorVTE": False,
        "activeCancer": False,
        "immobility": False,
        "obesity": False,
        "age65plus": False,
        "bleedingRiskLevel": "moderate",
        "priorSpinalEpiduralHematoma": False,
        "coagulopathy": False,
        "renalImpairment": False,
        "hepaticImpairment": False,
        "bridgingRequired": False,
        "ageYears": 60,
        "weightKg": 80,
    }


# ── Oracle cases (1:1 from neurosurgery.test.ts) ─────────────────────────────


def test_apixaban_48h_hold_standard_renal():
    r = assess({
        **_base(),
        "currentAnticoagulant": "apixaban",
        "indicationForAnticoagulation": "af_moderate_risk",
        "vteRiskLevel": "moderate",
        "ageYears": 62,
        "weightKg": 82,
    })
    assert "48" in r["holdDuration"]
    assert len(r["vteProphylaxis"]) > 0


def test_warfarin_bridging_mechanical_valve():
    r = assess({
        **_base(),
        "currentAnticoagulant": "warfarin",
        "indicationForAnticoagulation": "mechanical_heart_valve_high",
        "vteRiskLevel": "high",
        "age65plus": True,
        "bridgingRequired": True,
        "ageYears": 68,
        "weightKg": 78,
    })
    assert "bridg" in r["bridgingRecommendation"].lower()


def test_prior_epidural_hematoma_urgent():
    r = assess({
        **_base(),
        "procedureType": "cervical_posterior",
        "estimatedBloodLossHigh": True,
        "currentAnticoagulant": "rivaroxaban",
        "indicationForAnticoagulation": "af_high_risk",
        "vteRiskLevel": "high",
        "priorVTE": True,
        "age65plus": True,
        "bleedingRiskLevel": "high",
        "priorSpinalEpiduralHematoma": True,
        "ageYears": 72,
        "weightKg": 85,
    })
    assert len(r["urgentFlags"]) > 0


def test_dabigatran_renal_impairment_extended_hold():
    r = assess({
        **_base(),
        "procedureType": "complex_multilevel",
        "estimatedBloodLossHigh": True,
        "currentAnticoagulant": "dabigatran",
        "indicationForAnticoagulation": "af_moderate_risk",
        "vteRiskLevel": "high",
        "immobility": True,
        "obesity": True,
        "age65plus": True,
        "bleedingRiskLevel": "high",
        "renalImpairment": True,
        "ageYears": 75,
        "weightKg": 92,
    })
    assert "4–5 day" in r["holdDuration"] or "renal" in r["holdDuration"].lower()
    assert any("renal" in w.lower() for w in r["warnings"])


def test_aspirin81_lumbar_decompression_no_hold():
    r = assess({
        **_base(),
        "procedureType": "lumbar_decompression",
        "currentAnticoagulant": "aspirin_81",
        "indicationForAnticoagulation": "cad_stable",
        "vteRiskLevel": "low",
        "bleedingRiskLevel": "low",
        "ageYears": 58,
        "weightKg": 75,
    })
    assert len(r["preoperativeManagement"]) > 0
    assert r["holdDuration"] is not None


# ── Branch coverage ─────────────────────────────────────────────────────────


def test_emergency_warfarin_reversal_flags():
    r = assess({
        **_base(),
        "emergencyProcedure": True,
        "currentAnticoagulant": "warfarin",
    })
    flags = " ".join(r["urgentFlags"])
    assert "Emergency spine surgery" in flags
    assert "4-factor PCC" in flags


def test_emergency_doac_reversal_flag():
    r = assess({
        **_base(),
        "emergencyProcedure": True,
        "currentAnticoagulant": "apixaban",
    })
    assert any("Andexanet alfa" in f for f in r["urgentFlags"])


def test_warfarin_moderate_af_bridge_warning():
    r = assess({
        **_base(),
        "currentAnticoagulant": "warfarin",
        "indicationForAnticoagulation": "af_moderate_risk",
    })
    assert "Individualized" in r["bridgingRecommendation"]
    assert any("BRIDGE trial" in w for w in r["warnings"])


def test_warfarin_low_risk_no_bridge():
    r = assess({
        **_base(),
        "currentAnticoagulant": "warfarin",
        "indicationForAnticoagulation": "af_low_risk",
    })
    assert "NOT recommended" in r["bridgingRecommendation"]


def test_apixaban_renal_72h_hold():
    r = assess({
        **_base(),
        "currentAnticoagulant": "apixaban",
        "renalImpairment": True,
    })
    assert "72 hours" in r["holdDuration"]


def test_clopidogrel_recent_des_urgent_flag():
    r = assess({
        **_base(),
        "currentAnticoagulant": "clopidogrel",
        "indicationForAnticoagulation": "recent_pci_des",
    })
    assert any("stent thrombosis" in f for f in r["urgentFlags"])


def test_dapt_urgent_flag():
    r = assess({
        **_base(),
        "currentAnticoagulant": "aspirin_plus_p2y12",
    })
    assert "DAPT" in r["holdDuration"]
    assert any("DAPT" in f for f in r["urgentFlags"])


def test_high_risk_vte_extended_with_cancer_and_priorvte():
    r = assess({
        **_base(),
        "vteRiskLevel": "very_high",
        "activeCancer": True,
        "priorVTE": True,
    })
    joined = " ".join(r["vteProphylaxis"])
    assert "Active cancer" in joined
    assert "Prior VTE" in joined


def test_restart_label_mechanical_valve():
    r = assess({
        **_base(),
        "indicationForAnticoagulation": "mechanical_heart_valve_high",
    })
    assert r["restartTiming"] == "24–48 hours postoperatively (high-risk valve)"
    assert "Cardiology consultation required" in r["restartRecommendation"]


def test_prophylaxis_timing_high_bleeding_risk():
    r = assess({**_base(), "bleedingRiskLevel": "high"})
    assert "Delay pharmacologic prophylaxis 48–72 hours" in r["prophylaxisTiming"]


def test_next_steps_high_vte_adds_pharmacy():
    r = assess({**_base(), "vteRiskLevel": "high"})
    assert any("Pharmacy consultation" in s for s in r["nextSteps"])


def test_default_no_anticoagulant():
    r = assess(_base())
    assert r["holdDuration"] == "No anticoagulation to hold"
    assert r["bridgingRecommendation"] == "Bridging not required"
    assert r["evidenceLevel"] == "II"
    # Persistent epidural hematoma warning always appended.
    assert any("Spinal epidural hematoma" in w for w in r["warnings"])
    assert len(r["references"]) == 7
