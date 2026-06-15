"""Tests for the pAVF Clinical Compass port.

Oracle: old_static_code/client/src/lib/pavfLogic.ts (assessPAVF). The legacy
server test (old_static_code/server/pavf.test.ts) only covers router auth and
module registry, not the clinical logic, so these fixtures are derived from the
TS decision branches: each eligibility tier, device/CPT mapping, vessel-mapping
warnings, and the post-procedure maturation paths.
"""

from __future__ import annotations

from app.recommendations.modules.pavf import assess


def _base(**overrides) -> dict:
    """A fully eligible, anatomically adequate patient with no surgical option.

    Defaults yield ELIGIBLE_PREFERRED unless overridden. All thresholds met:
    perforator >=2, superficial depth <=6, all patency/doppler good, no calc.
    """
    data = {
        "patientName": "Test",
        "patientAge": 60,
        "priorCentralVenousDevices": False,
        "priorAVAccessSurgeries": False,
        "superficialChestCollaterals": False,
        "arterialCalcification": "none",
        "barbeauTest": "B",
        "radialPulsePresent": True,
        "ulnarPulsePresent": True,
        "brachialPulsePresent": True,
        "arterialDopplerNormal": True,
        "perforatorVeinDiameter": 2.5,
        "perforatorVeinPatent": True,
        "superficialVeinDepth": 4,
        "superficialVeinPatent": True,
        "deepVeinDiameter": 2,
        "centralVeinsPatent": True,
        "surgicalAVFFeasible": False,
        "surgicalAvailability": False,
        "patientPrefersPAVF": False,
        "urgentDialysisNeeded": False,
        "armThickness": "normal",
        "activeInfection": False,
        "anticoagulated": False,
    }
    data.update(overrides)
    return data


# ── Eligibility tiers ──────────────────────────────────────────────────────────

def test_eligible_preferred_no_surgical_option():
    r = assess(_base())
    assert r["eligibility"] == "ELIGIBLE_PREFERRED"
    assert r["eligibilityLabel"] == "pAVF Preferred — Proceed"
    assert r["eligibilityColor"] == "green"
    assert r["deviceSuggestion"] == "WavelinQ"
    assert r["cptCode"] == "36837"
    assert r["vesselMappingAdequate"] is True
    assert "forearm veins unsuitable for surgical AVF" in r["clinicalSummary"]
    assert "no local surgical expertise" in r["clinicalSummary"]


def test_consider_surgical_first():
    r = assess(_base(surgicalAVFFeasible=True, surgicalAvailability=True))
    assert r["eligibility"] == "CONSIDER_SURGICAL_FIRST"
    assert r["eligibilityColor"] == "yellow"
    # Surgical Referral recommendation appended only in this branch
    assert any(rec["category"] == "Surgical Referral" for rec in r["recommendations"])


def test_eligible_when_surgical_feasible_but_patient_prefers_pavf():
    # surgical feasible + available but patient prefers pAVF -> ELIGIBLE_PREFERRED
    r = assess(_base(surgicalAVFFeasible=True, surgicalAvailability=True, patientPrefersPAVF=True))
    assert r["eligibility"] == "ELIGIBLE_PREFERRED"
    assert "patient preference" in r["clinicalSummary"]


def test_plain_eligible_unreachable_branch_documented():
    # The trailing ELIGIBLE branch is structurally unreachable: if surgical is
    # feasible+available and patient doesn't prefer pAVF and not urgent, it is
    # CONSIDER_SURGICAL_FIRST; otherwise ELIGIBLE_PREFERRED. Confirm we never
    # land on plain ELIGIBLE for the surgical-first inputs minus one condition.
    r = assess(_base(surgicalAVFFeasible=True, surgicalAvailability=True, urgentDialysisNeeded=True))
    assert r["eligibility"] == "ELIGIBLE_PREFERRED"
    assert "urgent dialysis need (pAVF achievable within 1 week)" in r["clinicalSummary"]


# ── Absolute contraindications -> INELIGIBLE ────────────────────────────────────

def test_barbeau_d_ineligible():
    r = assess(_base(barbeauTest="D"))
    assert r["eligibility"] == "INELIGIBLE"
    assert r["eligibilityColor"] == "red"
    assert r["cptCode"] == "N/A"
    assert any(c["id"] == "barbeau_d" for c in r["contraindications"])
    assert "Consider upper arm AV graft." in r["clinicalSummary"]
    # No recommendations generated when ineligible
    assert r["recommendations"] == []


def test_active_infection_ineligible():
    r = assess(_base(activeInfection=True))
    assert r["eligibility"] == "INELIGIBLE"
    assert any(c["id"] == "active_infection" for c in r["contraindications"])
    assert "Alternative access strategy required." in r["clinicalSummary"]


def test_central_vein_obstruction_ineligible():
    r = assess(_base(superficialChestCollaterals=True, centralVeinsPatent=False))
    assert r["eligibility"] == "INELIGIBLE"
    assert any(c["id"] == "central_vein_obstruction" for c in r["contraindications"])


def test_severe_calcification_ineligible_no_device():
    r = assess(_base(arterialCalcification="severe"))
    assert r["eligibility"] == "INELIGIBLE"
    assert r["deviceSuggestion"] == "None"
    assert r["deviceRationale"] == "Severe calcification prevents radiofrequency activation. Neither device is suitable."
    assert r["cptCode"] == "N/A"
    assert any(c["id"] == "severe_calcification" for c in r["contraindications"])
    assert r["vesselMappingAdequate"] is False


def test_no_perforator_ineligible():
    r = assess(_base(perforatorVeinPatent=False))
    assert r["eligibility"] == "INELIGIBLE"
    assert any(c["id"] == "no_perforator" for c in r["contraindications"])


def test_no_superficial_vein_ineligible():
    r = assess(_base(superficialVeinPatent=False))
    assert r["eligibility"] == "INELIGIBLE"
    assert any(c["id"] == "no_superficial_vein" for c in r["contraindications"])


# ── NEEDS_FURTHER_WORKUP (vessel mapping issues, no absolute contra) ────────────

def test_perforator_too_small_needs_workup():
    r = assess(_base(perforatorVeinDiameter=1.5))
    assert r["eligibility"] == "NEEDS_FURTHER_WORKUP"
    assert r["eligibilityColor"] == "orange"
    assert any("Perforator vein diameter 1.5 mm" in i for i in r["vesselMappingIssues"])
    assert any("Perforator vein <2 mm" in w for w in r["warnings"])


def test_superficial_vein_too_deep_needs_workup():
    r = assess(_base(superficialVeinDepth=8))
    assert r["eligibility"] == "NEEDS_FURTHER_WORKUP"
    assert any("Superficial vein depth 8 mm" in i for i in r["vesselMappingIssues"])


def test_abnormal_doppler_needs_workup():
    r = assess(_base(arterialDopplerNormal=False))
    assert r["eligibility"] == "NEEDS_FURTHER_WORKUP"
    assert "Abnormal arterial Doppler waveforms or velocities" in r["vesselMappingIssues"]


def test_moderate_calcification_warning_and_device_note():
    r = assess(_base(arterialCalcification="moderate"))
    assert r["eligibility"] == "NEEDS_FURTHER_WORKUP"  # moderate adds a vessel mapping issue
    assert "Moderate arterial calcification noted" in r["vesselMappingIssues"]
    assert "have rescue PTA balloon" in r["deviceRationale"]
    assert r["deviceSuggestion"] == "WavelinQ"


# ── Warnings that do NOT change eligibility ─────────────────────────────────────

def test_prior_devices_and_surgeries_warnings_only():
    r = assess(_base(priorCentralVenousDevices=True, priorAVAccessSurgeries=True))
    assert r["eligibility"] == "ELIGIBLE_PREFERRED"
    assert any("pacemakers/catheters" in w for w in r["warnings"])
    assert any("Prior AV access surgeries" in w for w in r["warnings"])


def test_central_patency_uncertain_warning():
    # not patent and no chest collaterals -> warning but NOT the absolute contra
    r = assess(_base(centralVeinsPatent=False))
    assert any("Central vein patency uncertain" in w for w in r["warnings"])
    # centralVeinsPatent False makes vesselMappingAdequate False
    assert r["vesselMappingAdequate"] is False


# ── Intraoperative recommendation gated on deepVeinDiameter ─────────────────────

def test_intraoperative_rec_present_when_deep_vein_positive():
    r = assess(_base(deepVeinDiameter=2))
    assert any(rec["category"] == "Intraoperative" for rec in r["recommendations"])


def test_intraoperative_rec_absent_when_deep_vein_zero():
    r = assess(_base(deepVeinDiameter=0))
    assert not any(rec["category"] == "Intraoperative" for rec in r["recommendations"])


def test_urgency_recommendation_present():
    r = assess(_base(urgentDialysisNeeded=True))
    assert any(rec["category"] == "Urgency" for rec in r["recommendations"])


# ── Maturation (post-procedure) paths ──────────────────────────────────────────

def test_maturation_early_followup():
    r = assess(_base(isPostProcedure=True, weeksPostProcedure=0))
    assert r["maturationStatus"] == "EARLY_FOLLOW_UP_NEEDED"
    assert r["maturationLabel"] == "Schedule 1–2 Week Follow-Up Visit + US Study"


def test_maturation_too_early():
    r = assess(_base(isPostProcedure=True, weeksPostProcedure=2))
    assert r["maturationStatus"] == "TOO_EARLY_TO_ASSESS"


def test_maturation_mature_ready():
    r = assess(_base(
        isPostProcedure=True,
        weeksPostProcedure=6,
        cannulationVeinDiameterMm=7,
        cannulationVeinDepthMm=4,
        fistulaPalpableWithTourniquet=True,
    ))
    assert r["maturationStatus"] == "MATURE_READY_FOR_CANNULATION"
    assert r["maturationInterventions"] is None


def test_maturation_deep_vein_diversion():
    r = assess(_base(
        isPostProcedure=True,
        weeksPostProcedure=6,
        cannulationVeinDiameterMm=5,  # rule of 6 not met
        deepVeinDiversionPresent=True,
    ))
    assert r["maturationStatus"] == "IMMATURE_DEEP_VEIN_DIVERSION"
    assert any("Coil embolization" in i for i in r["maturationInterventions"])


def test_maturation_superficial_diversion():
    r = assess(_base(
        isPostProcedure=True,
        weeksPostProcedure=6,
        cannulationVeinDiameterMm=5,
        superficialVeinDiversionPresent=True,
    ))
    assert r["maturationStatus"] == "IMMATURE_SUPERFICIAL_DIVERSION"


def test_maturation_vein_too_deep():
    r = assess(_base(
        isPostProcedure=True,
        weeksPostProcedure=6,
        cannulationVeinDiameterMm=7,
        cannulationVeinDepthMm=8,  # too deep -> rule of 6 fails
        cannulationVeinTooDeep=True,
    ))
    assert r["maturationStatus"] == "IMMATURE_VEIN_TOO_DEEP"


def test_maturation_default_inflow_stenosis():
    r = assess(_base(
        isPostProcedure=True,
        weeksPostProcedure=6,
        cannulationVeinDiameterMm=5,  # nothing else flagged
    ))
    assert r["maturationStatus"] == "IMMATURE_INFLOW_STENOSIS"


def test_maturation_absent_when_not_post_procedure():
    r = assess(_base())
    assert r["maturationStatus"] is None
    assert r["maturationLabel"] is None
    assert r["maturationInterventions"] is None


def test_rule_of_six_missing_optional_fields_defaults():
    # No diameter/depth/palpable provided -> defaults (0, 99, False) fail rule of 6
    r = assess(_base(isPostProcedure=True, weeksPostProcedure=6))
    assert r["maturationStatus"] == "IMMATURE_INFLOW_STENOSIS"


# ── Result shape ───────────────────────────────────────────────────────────────

def test_result_keys():
    r = assess(_base())
    expected = {
        "eligibility", "eligibilityLabel", "eligibilityColor", "contraindications",
        "warnings", "recommendations", "vesselMappingAdequate", "vesselMappingIssues",
        "deviceSuggestion", "deviceRationale", "maturationStatus", "maturationLabel",
        "maturationInterventions", "cptCode", "cptDescription", "followUpSchedule",
        "clinicalSummary",
    }
    assert set(r.keys()) == expected
    assert len(r["followUpSchedule"]) == 5
