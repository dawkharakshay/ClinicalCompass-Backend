"""Tests for the PE Clinical Compass engine.

Ported 1:1 from old_static_code/server/pe-compass.test.ts (the oracle covering
peLogic.ts evaluatePE). Each vitest case maps to one test here. The base input
mirrors the test's spread over defaultPEInput.
"""

import re

from app.recommendations.modules.pe import assess

# ─── Base Input (stable, low-risk PE) — matches baseInput in the .test.ts ─────
BASE = {
    "presentation": "symptomatic_stable",
    "hemodynamicStatus": "stable",
    "peBurden": "segmental",
    "sPESI": 0,
    "hestiaScore": 0,
    "rvStatus": "normal",
    "troponinElevated": False,
    "bnpElevated": False,
    "lactateElevated": False,
    "lactateLevel": "normal",
    "ageOver75": False,
    "activeBleedingRisk": False,
    "recentSurgery": False,
    "priorICH": False,
    "isPregnant": False,
    "cancerActive": False,
    "priorPEorDVT": False,
    "unprovoked": False,
    "thrombophilia": False,
    "pertActivated": False,
    "echoAvailable": True,
    "ctpaPerformed": True,
    "rvLvRatio": 0.8,
    "considerECMO": False,
    "ecmoContraindications": [],
    "anticoagulationPreference": "doac_preferred",
    "creatinineClearance": 80,
}


def ev(**overrides):
    return assess({**BASE, **overrides})


# ─── Category A: Incidental Asymptomatic PE ───────────────────────────────────
def test_category_a_assignment():
    r = ev(
        presentation="incidental_asymptomatic",
        hemodynamicStatus="stable",
        rvStatus="normal",
        troponinElevated=False,
        bnpElevated=False,
    )
    assert r["accAhaCategory"] == "A"
    assert r["riskLevel"] == "low"
    assert "Incidental PE" in r["primaryRecommendation"]
    assert "Anticoagulation" in r["primaryRecommendation"]


def test_category_a_esc_low_risk():
    r = ev(presentation="incidental_asymptomatic")
    assert r["escEquivalent"] == "Low Risk"


def test_category_a_recommends_doac():
    r = ev(presentation="incidental_asymptomatic", anticoagulationPreference="doac_preferred")
    assert re.search(r"apixaban|rivaroxaban|DOAC", r["anticoagulationStrategy"], re.I)


# ─── Category B: Low-Risk Symptomatic PE ─────────────────────────────────────
def test_category_b_assignment():
    r = ev(
        presentation="symptomatic_stable",
        hemodynamicStatus="stable",
        sPESI=0,
        rvStatus="normal",
        troponinElevated=False,
        bnpElevated=False,
    )
    assert r["accAhaCategory"] == "B"
    assert r["riskLevel"] == "low"


def test_category_b_outpatient_doac():
    r = ev(
        presentation="symptomatic_stable",
        sPESI=0,
        hestiaScore=0,
        rvStatus="normal",
        troponinElevated=False,
        bnpElevated=False,
    )
    assert "Early discharge" in r["primaryRecommendation"]
    assert "outpatient DOAC" in r["primaryRecommendation"]
    assert "Early discharge" in r["dispositionRecommendation"]


def test_category_b_esc_low_risk():
    r = ev(presentation="symptomatic_stable", sPESI=0, rvStatus="normal")
    assert r["escEquivalent"] == "Low Risk"


def test_category_b_no_pert():
    r = ev(presentation="symptomatic_stable", sPESI=0, rvStatus="normal")
    assert r["pertClass"] != "Class 1"


# ─── Category C1 ─────────────────────────────────────────────────────────────
def test_category_c1_assignment():
    r = ev(
        presentation="symptomatic_elevated_risk",
        hemodynamicStatus="stable",
        sPESI=2,
        rvStatus="normal",
        troponinElevated=False,
        bnpElevated=False,
    )
    assert r["accAhaCategory"] == "C1"
    assert r["riskLevel"] == "intermediate_low"


def test_category_c1_inpatient_anticoag():
    r = ev(presentation="symptomatic_elevated_risk", sPESI=2, rvStatus="normal")
    assert "Inpatient anticoagulation" in r["primaryRecommendation"]


def test_category_c1_esc():
    r = ev(
        presentation="symptomatic_elevated_risk",
        sPESI=2,
        rvStatus="normal",
        troponinElevated=False,
        bnpElevated=False,
    )
    assert r["escEquivalent"] == "Intermediate-Low Risk"


# ─── Category C2 ─────────────────────────────────────────────────────────────
def test_category_c2_imaging_only():
    r = ev(
        presentation="symptomatic_elevated_risk",
        hemodynamicStatus="stable",
        sPESI=1,
        rvStatus="dysfunction_imaging",
        troponinElevated=False,
        bnpElevated=False,
    )
    assert r["accAhaCategory"] == "C2"
    assert r["riskLevel"] == "intermediate_low"


def test_category_c2_biomarker_only():
    r = ev(
        presentation="symptomatic_elevated_risk",
        sPESI=1,
        rvStatus="dysfunction_biomarker_only",
        troponinElevated=True,
        bnpElevated=False,
    )
    assert r["accAhaCategory"] == "C2"


# ─── Category C3 ─────────────────────────────────────────────────────────────
def _c3():
    return ev(
        presentation="symptomatic_elevated_risk",
        hemodynamicStatus="stable",
        sPESI=2,
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
    )


def test_category_c3_assignment():
    r = _c3()
    assert r["accAhaCategory"] == "C3"
    assert r["riskLevel"] == "intermediate_high"


def test_category_c3_pert_class1():
    r = _c3()
    assert "PERT" in r["pertRecommendation"]
    assert "Class 1" in r["pertClass"]


def test_category_c3_trials():
    r = _c3()
    names = [t["trial"] for t in r["trialEvidence"]]
    assert any("HI-PEITHO" in n or "STORM-PE" in n for n in names)


def test_category_c3_esc():
    r = _c3()
    assert r["escEquivalent"] == "Intermediate-High Risk"


def test_category_c3_advanced_therapy():
    r = _c3()
    assert re.search(r"2a|2b", r["advancedTherapyClass"])
    assert re.search(r"CDT|USAT|thrombectomy", r["preferredAdvancedTherapy"], re.I)


# ─── Category D1 ─────────────────────────────────────────────────────────────
def test_category_d1_assignment():
    r = ev(
        presentation="incipient_failure",
        hemodynamicStatus="borderline",
        sPESI=2,
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
        lactateElevated=False,
        lactateLevel="normal",
    )
    assert r["accAhaCategory"] == "D1"
    assert r["riskLevel"] == "intermediate_high"


def test_category_d1_pert_and_ufh():
    r = ev(
        presentation="incipient_failure",
        hemodynamicStatus="borderline",
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
        anticoagulationPreference="ufh_required",
    )
    assert "Class 1" in r["pertClass"]
    assert re.search(r"UFH|heparin", r["anticoagulationStrategy"], re.I)


def test_category_d1_primary_ufh():
    r = ev(
        presentation="incipient_failure",
        hemodynamicStatus="borderline",
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
    )
    assert re.search(r"UFH|heparin", r["primaryRecommendation"], re.I)


# ─── Category D2 ─────────────────────────────────────────────────────────────
def _d2():
    return ev(
        presentation="incipient_failure",
        hemodynamicStatus="shock_normotensive",
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
        lactateElevated=True,
        lactateLevel="elevated",
    )


def test_category_d2_assignment():
    r = _d2()
    assert r["accAhaCategory"] == "D2"
    assert r["riskLevel"] == "high"


def test_category_d2_ecmo():
    r = _d2()
    assert "ECMO" in r["primaryRecommendation"]


# ─── Category E1 ─────────────────────────────────────────────────────────────
def _e1():
    return ev(
        presentation="overt_failure",
        hemodynamicStatus="hypotensive_shock",
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
        lactateElevated=True,
        lactateLevel="elevated",
    )


def test_category_e1_assignment():
    r = _e1()
    assert r["accAhaCategory"] == "E1"
    assert r["riskLevel"] in ("high", "critical")


def test_category_e1_systemic_thrombolysis():
    r = _e1()
    assert re.search(r"alteplase|systemic thrombolysis", r["primaryRecommendation"], re.I)
    assert "Class 2a" in r["advancedTherapyClass"]


def test_category_e1_esc_high_risk():
    r = _e1()
    assert "High Risk" in r["escEquivalent"]


def test_category_e1_va_ecmo():
    r = _e1()
    assert re.search(r"VA-ECMO|ECMO", r["primaryRecommendation"], re.I)


# ─── Category E2 ─────────────────────────────────────────────────────────────
def _e2():
    return ev(
        presentation="overt_failure",
        hemodynamicStatus="refractory_arrest",
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
        lactateElevated=True,
        lactateLevel="elevated",
    )


def test_category_e2_assignment():
    r = _e2()
    assert r["accAhaCategory"] == "E2"
    assert r["riskLevel"] == "critical"


def test_category_e2_alteplase_bolus():
    r = _e2()
    assert re.search(r"50mg|bolus", r["primaryRecommendation"], re.I)


def test_category_e2_va_ecmo_bridge():
    r = _e2()
    assert re.search(r"VA-ECMO|ECMO", r["primaryRecommendation"], re.I)
    assert re.search(r"embolectomy|thrombectomy", r["primaryRecommendation"], re.I)


def test_category_e2_esc_high_risk():
    r = _e2()
    assert "High Risk" in r["escEquivalent"]


# ─── Anticoagulation Strategy ─────────────────────────────────────────────────
def test_anticoag_doac_normal_renal():
    r = ev(anticoagulationPreference="doac_preferred", creatinineClearance=80)
    assert re.search(r"apixaban|rivaroxaban", r["anticoagulationStrategy"], re.I)


def test_anticoag_lmwh_vka_preference():
    r = ev(anticoagulationPreference="lmwh_vka")
    assert re.search(r"LMWH|enoxaparin|warfarin", r["anticoagulationStrategy"], re.I)


def test_anticoag_ufh_required():
    r = ev(anticoagulationPreference="ufh_required")
    assert re.search(r"UFH|unfractionated heparin", r["anticoagulationStrategy"], re.I)


def test_anticoag_active_cancer():
    r = ev(cancerActive=True, anticoagulationPreference="doac_preferred")
    assert re.search(r"LMWH|enoxaparin|edoxaban|rivaroxaban", r["anticoagulationStrategy"], re.I)


def test_anticoag_pregnancy():
    r = ev(isPregnant=True)
    assert re.search(r"LMWH|enoxaparin", r["anticoagulationStrategy"], re.I)


def test_anticoag_reduced_renal():
    r = ev(anticoagulationPreference="doac_preferred", creatinineClearance=20)
    assert r["anticoagulationStrategy"]


# ─── Extended Anticoagulation ─────────────────────────────────────────────────
def test_extended_unprovoked():
    r = ev(unprovoked=True)
    assert re.search(r"extended|indefinite|≥3 months", r["extendedAnticoagulation"], re.I)


def test_extended_cancer():
    r = ev(cancerActive=True)
    assert re.search(r"extended|indefinite|cancer", r["extendedAnticoagulation"], re.I)


def test_extended_thrombophilia():
    r = ev(thrombophilia=True)
    assert re.search(r"extended|indefinite|thrombophilia", r["extendedAnticoagulation"], re.I)


def test_extended_provoked():
    r = ev(unprovoked=False, cancerActive=False, thrombophilia=False, priorPEorDVT=False)
    assert re.search(r"3 month|provoked|limited duration", r["extendedAnticoagulation"], re.I)


# ─── PERT Activation ──────────────────────────────────────────────────────────
def test_pert_not_low_risk():
    r = ev(presentation="symptomatic_stable", sPESI=0, rvStatus="normal")
    assert r["pertClass"] != "Class 1"


def test_pert_c3():
    r = _c3()
    assert "Class 1" in r["pertClass"]


def test_pert_incipient():
    r = ev(
        presentation="incipient_failure",
        hemodynamicStatus="borderline",
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
    )
    assert "Class 1" in r["pertClass"]


def test_pert_overt():
    r = _e1()
    assert "Class 1" in r["pertClass"]


# ─── Urgent Flags ─────────────────────────────────────────────────────────────
def test_flag_pregnancy():
    r = ev(isPregnant=True)
    assert any("PREGNANCY" in f for f in r["urgentFlags"])
    assert any("LMWH" in f for f in r["urgentFlags"])


def test_flag_subsegmental():
    r = ev(peBurden="subsegmental", sPESI=0)
    assert any("SUBSEGMENTAL" in f for f in r["urgentFlags"])


def test_flag_rv_dilation():
    r = ev(rvLvRatio=1.6)
    assert any("RV/LV RATIO" in f for f in r["urgentFlags"])


def test_no_flag_rv_below_threshold():
    r = ev(rvLvRatio=1.2)
    assert not any("RV/LV RATIO" in f for f in r["urgentFlags"])


def test_no_flag_subsegmental_elevated_spesi():
    r = ev(peBurden="subsegmental", sPESI=2)
    assert not any("SUBSEGMENTAL" in f for f in r["urgentFlags"])


# ─── ECMO Assessment ──────────────────────────────────────────────────────────
def test_ecmo_null_when_not_considered():
    r = ev(considerECMO=False)
    assert r["ecmoAssessment"] is None


def test_ecmo_present_when_considered():
    r = ev(
        considerECMO=True,
        ecmoContraindications=[],
        presentation="overt_failure",
        hemodynamicStatus="hypotensive_shock",
    )
    assert r["ecmoAssessment"] is not None
    assert r["ecmoAssessment"]["candidacy"] is not None


def test_ecmo_absolute_brain_injury():
    r = ev(
        considerECMO=True,
        ecmoContraindications=["severe_brain_injury"],
        presentation="overt_failure",
        hemodynamicStatus="hypotensive_shock",
    )
    assert r["ecmoAssessment"]["candidacy"] == "absolute_contraindication"


def test_ecmo_absolute_aortic_dissection():
    r = ev(
        considerECMO=True,
        ecmoContraindications=["aortic_dissection"],
        presentation="overt_failure",
        hemodynamicStatus="hypotensive_shock",
    )
    assert r["ecmoAssessment"]["candidacy"] == "absolute_contraindication"


def test_ecmo_candidate_no_contraindications():
    r = ev(
        considerECMO=True,
        ecmoContraindications=[],
        presentation="overt_failure",
        hemodynamicStatus="hypotensive_shock",
    )
    assert r["ecmoAssessment"]["candidacy"] == "candidate"


def test_ecmo_relative_age():
    r = ev(
        considerECMO=True,
        ecmoContraindications=["age_over_75"],
        presentation="overt_failure",
        hemodynamicStatus="hypotensive_shock",
    )
    assert r["ecmoAssessment"]["candidacy"] == "relative_contraindication"


def test_ecmo_not_indicated_low_risk():
    r = ev(
        considerECMO=True,
        ecmoContraindications=[],
        presentation="symptomatic_stable",
        hemodynamicStatus="stable",
        rvStatus="normal",
    )
    assert r["ecmoAssessment"]["candidacy"] == "not_indicated"


# ─── Trial Evidence ───────────────────────────────────────────────────────────
def test_trial_storm_pe_intermediate_high():
    r = _c3()
    names = [t["trial"] for t in r["trialEvidence"]]
    assert any("STORM-PE" in n for n in names)


def test_trial_hi_peitho():
    r = _c3()
    names = [t["trial"] for t in r["trialEvidence"]]
    assert any("HI-PEITHO" in n for n in names)


def test_trial_peerless_d():
    r = ev(
        presentation="incipient_failure",
        hemodynamicStatus="borderline",
        sPESI=2,
        rvStatus="dysfunction_both",
        troponinElevated=True,
        bnpElevated=True,
    )
    names = [t["trial"] for t in r["trialEvidence"]]
    assert any("PEERLESS" in n for n in names)


def test_trial_evidence_fields():
    r = _c3()
    for t in r["trialEvidence"]:
        assert t["trial"]
        assert t["year"] > 2000
        assert t["finding"]
        assert t["relevance"]


# ─── References ───────────────────────────────────────────────────────────────
def test_references_acc_aha_2026():
    r = ev()
    assert any("ACC" in x and "2026" in x for x in r["references"])


def test_references_esc_2019():
    r = ev()
    assert any("ESC" in x and "2019" in x for x in r["references"])


def test_references_at_least_3():
    r = ev()
    assert len(r["references"]) >= 3


# ─── Default Input ────────────────────────────────────────────────────────────
def test_default_input_no_error():
    assess({})


def test_default_input_required_fields():
    r = assess({})
    assert r["accAhaCategory"]
    assert r["escEquivalent"]
    assert r["riskLevel"]
    assert r["primaryRecommendation"]
    assert r["anticoagulationStrategy"]
    assert r["pertRecommendation"]
    assert r["monitoringPlan"]
    assert r["dispositionRecommendation"]
    assert isinstance(r["urgentFlags"], list)
    assert isinstance(r["references"], list)
    assert isinstance(r["trialEvidence"], list)
