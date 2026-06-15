"""VTE Clinical Compass — ported 1:1 from old_static_code/server/vte.test.ts.

Each TS ``assess*`` entry maps to a pathway selected via the ``pathway`` field.
"""

from __future__ import annotations

from app.recommendations.modules.vte import assess


def _dvt_pe(**overrides):
    data = {
        "pathway": "dvt_pe_treatment",
        "vteType": "dvt_proximal",
        "provoked": "unprovoked",
        "priorVTEHistory": "none",
        "cancerPresent": False,
        "antiphospholipidSyndrome": False,
        "renalFunction": "normal",
        "liverDisease": "none",
        "highBleedingRisk": False,
        "currentlyOnVKA": False,
        "currentlyOnDOAC": False,
        "distalDVTSymptoms": "symptomatic",
    }
    data.update(overrides)
    return assess(data)


def _cat(**overrides):
    data = {
        "pathway": "cancer_associated_thrombosis",
        "cancerType": "other_solid_tumor",
        "highBleedingRisk": False,
        "recurrentVTEOnLMWH": False,
        "recurrentVTEOnAnticoagulation": False,
    }
    data.update(overrides)
    return assess(data)


def _thrombo(**overrides):
    data = {
        "pathway": "thrombophilia_testing",
        "familyHistoryHighRiskThrombophilia": False,
    }
    data.update(overrides)
    return assess(data)


def _ped(**overrides):
    data = {"pathway": "pediatric_vte"}
    data.update(overrides)
    return assess(data)


def _preg(**overrides):
    data = {
        "pathway": "pregnancy_vte",
        "priorVTEHistory": False,
        "priorVTEProvoked": False,
        "highBleedingRisk": False,
    }
    data.update(overrides)
    return assess(data)


# ─── Pathway 1: DVT/PE Treatment ─────────────────────────────────────────────


def test_uncomplicated_proximal_dvt_home_treatment():
    r = _dvt_pe(vteType="dvt_proximal", provoked="unprovoked", priorVTEHistory="none")
    assert r["pathway"] == "dvt_pe_treatment"
    assert r["primaryRecommendation"]["id"] == "dvt_pe_rec1"
    assert r["primaryRecommendation"]["strength"] == "conditional"
    assert r["primaryRecommendation"]["certainty"] == "low"


def test_stable_pe_home_treatment():
    r = _dvt_pe(vteType="pe", peHemodynamicStatus="stable", provoked="provoked_transient")
    assert r["primaryRecommendation"]["id"] == "dvt_pe_rec2"
    assert r["primaryRecommendation"]["strength"] == "conditional"
    assert r["primaryRecommendation"]["certainty"] == "very_low"


def test_massive_pe_thrombolysis_strong():
    r = _dvt_pe(vteType="pe", peHemodynamicStatus="massive")
    assert r["primaryRecommendation"]["id"] == "dvt_pe_rec6"
    assert r["primaryRecommendation"]["strength"] == "strong"
    assert r["primaryRecommendation"].get("alert") is not None


def test_submassive_pe_anticoagulation_alone():
    r = _dvt_pe(vteType="pe", peHemodynamicStatus="submassive")
    assert r["primaryRecommendation"]["id"] == "dvt_pe_rec7"
    assert r["primaryRecommendation"]["strength"] == "conditional"


def test_aps_doac_contraindicated():
    r = _dvt_pe(antiphospholipidSyndrome=True)
    assert any("Antiphospholipid" in a for a in r["clinicalAlerts"])
    ac = next((x for x in r["additionalRecommendations"] if x["id"] == "dvt_pe_rec3_exception"), None)
    assert ac is not None


def test_severe_renal_impairment_alert():
    r = _dvt_pe(renalFunction="severe_impairment")
    assert any("CrCl <30" in a for a in r["clinicalAlerts"])


def test_provoked_transient_no_prior_3_months():
    r = _dvt_pe(provoked="provoked_transient", priorVTEHistory="none")
    d = next((x for x in r["additionalRecommendations"] if x["id"] == "dvt_pe_rec12"), None)
    assert d is not None
    assert "3 months" in d["statement"]


def test_first_unprovoked_no_bleed_indefinite():
    r = _dvt_pe(provoked="unprovoked", priorVTEHistory="none")
    d = next((x for x in r["additionalRecommendations"] if x["id"] == "dvt_pe_rec19"), None)
    assert d is not None
    assert d["strength"] == "conditional"
    assert d["certainty"] == "moderate"


def test_recurrent_unprovoked_indefinite_strong():
    r = _dvt_pe(provoked="unprovoked", priorVTEHistory="prior_unprovoked")
    d = next((x for x in r["additionalRecommendations"] if x["id"] == "dvt_pe_rec25"), None)
    assert d is not None
    assert d["strength"] == "strong"
    assert d["certainty"] == "moderate"


def test_symptomatic_distal_dvt_anticoagulation():
    r = _dvt_pe(vteType="dvt_distal", distalDVTSymptoms="symptomatic")
    d = next((x for x in r["additionalRecommendations"] if x["id"] == "dvt_pe_rec9"), None)
    assert d is not None


def test_asymptomatic_distal_dvt_no_anticoagulation():
    r = _dvt_pe(vteType="dvt_distal", distalDVTSymptoms="asymptomatic")
    d = next((x for x in r["additionalRecommendations"] if x["id"] == "dvt_pe_rec10"), None)
    assert d is not None


def test_breakthrough_vte_on_vka_lmwh():
    r = _dvt_pe(currentlyOnVKA=True)
    rec23 = next((x for x in r["additionalRecommendations"] if x["id"] == "dvt_pe_rec23"), None)
    assert rec23 is not None
    assert any("LMWH" in a for a in r["clinicalAlerts"])


def test_cancer_present_redirect_alert():
    r = _dvt_pe(cancerPresent=True)
    assert any("Cancer-Associated Thrombosis" in a for a in r["clinicalAlerts"])


# ─── Pathway 2: Cancer-Associated Thrombosis ──────────────────────────────────


def test_hospitalized_medical_lmwh_prophylaxis():
    r = _cat(clinicalContext="hospitalized_medical")
    assert r["pathway"] == "cancer_associated_thrombosis"
    assert r["primaryRecommendation"]["id"] == "cat_rec1"
    assert r["primaryRecommendation"]["strength"] == "conditional"


def test_ambulatory_khorana_high():
    r = _cat(clinicalContext="ambulatory_systemic_therapy", khoranaScore=3)
    assert r["primaryRecommendation"]["id"] == "cat_rec6"
    assert "≥2" in r["primaryRecommendation"]["statement"]


def test_ambulatory_khorana_low():
    r = _cat(clinicalContext="ambulatory_systemic_therapy", khoranaScore=1)
    assert r["primaryRecommendation"]["id"] == "cat_rec7"
    assert "<2" in r["primaryRecommendation"]["statement"]


def test_surgical_high_bleed_mechanical():
    r = _cat(clinicalContext="surgical", surgicalProcedure="high_bleed_risk", highBleedingRisk=True)
    assert r["primaryRecommendation"]["id"] == "cat_rec14"


def test_major_abdominal_pelvic_extended():
    r = _cat(clinicalContext="surgical", surgicalProcedure="major_abdominal_pelvic")
    assert r["primaryRecommendation"]["id"] == "cat_rec16"
    assert "4 weeks" in r["primaryRecommendation"]["statement"]


def test_cvc_no_prophylaxis():
    r = _cat(clinicalContext="cvc_related")
    assert r["primaryRecommendation"]["id"] == "cat_rec18_19"


def test_initial_cat_treatment():
    r = _cat(clinicalContext="treatment_of_vte", vteType="dvt", treatmentPhase="initial_first_week")
    assert r["primaryRecommendation"]["id"] == "cat_rec20_21"
    assert "LMWH is RECOMMENDED over UFH" in r["primaryRecommendation"]["statement"]


def test_short_term_cat_treatment():
    r = _cat(clinicalContext="treatment_of_vte", vteType="dvt", treatmentPhase="short_term_3_6mo")
    assert r["primaryRecommendation"]["id"] == "cat_rec23_24"


def test_gi_cancer_bleeding_alert():
    r = _cat(
        clinicalContext="treatment_of_vte",
        cancerType="gi_cancer",
        vteType="dvt",
        treatmentPhase="short_term_3_6mo",
    )
    assert any("GI" in a for a in r["clinicalAlerts"])


def test_long_term_cat_treatment():
    r = _cat(clinicalContext="treatment_of_vte", vteType="dvt", treatmentPhase="long_term_over_6mo")
    assert r["primaryRecommendation"]["id"] == "cat_rec32_33_34"
    assert "indefinite" in r["primaryRecommendation"]["statement"].lower()


def test_recurrent_vte_on_anticoagulation_ivc_filter():
    r = _cat(
        clinicalContext="treatment_of_vte",
        vteType="dvt",
        treatmentPhase="short_term_3_6mo",
        recurrentVTEOnAnticoagulation=True,
    )
    rec31 = next((x for x in r["additionalRecommendations"] if x["id"] == "cat_rec31"), None)
    assert rec31 is not None
    assert "NOT" in rec31["statement"]


# ─── Pathway 3: Thrombophilia Testing ────────────────────────────────────────


def test_unprovoked_do_not_test():
    r = _thrombo(vteType="unprovoked")
    assert r["pathway"] == "thrombophilia_testing"
    assert r["primaryRecommendation"]["id"] == "thrombo_r1"
    assert "NOT" in r["primaryRecommendation"]["statement"]


def test_surgical_do_not_test():
    r = _thrombo(vteType="provoked_surgical")
    assert r["primaryRecommendation"]["id"] == "thrombo_r2"
    assert "NOT" in r["primaryRecommendation"]["statement"]


def test_nonsurgical_major_transient_test():
    r = _thrombo(vteType="provoked_nonsurgical_major_transient")
    assert r["primaryRecommendation"]["id"] == "thrombo_r3"
    assert "IS suggested" in r["primaryRecommendation"]["statement"]


def test_pregnancy_postpartum_test():
    r = _thrombo(vteType="provoked_pregnancy_postpartum")
    assert r["primaryRecommendation"]["id"] == "thrombo_r4"
    assert "IS suggested" in r["primaryRecommendation"]["statement"]


def test_coc_test():
    r = _thrombo(vteType="provoked_coc")
    assert r["primaryRecommendation"]["id"] == "thrombo_r5"


def test_cvt_would_stop_test():
    r = _thrombo(vteType="unusual_site_cvt", standardOfCareAnticoagulation="would_stop")
    assert r["primaryRecommendation"]["id"] == "thrombo_r7"
    assert "IS suggested" in r["primaryRecommendation"]["statement"]


def test_cvt_would_continue_no_test():
    r = _thrombo(
        vteType="unusual_site_cvt", standardOfCareAnticoagulation="would_continue_indefinitely"
    )
    assert r["primaryRecommendation"]["id"] == "thrombo_r8"
    assert "NOT" in r["primaryRecommendation"]["statement"]


def test_asymptomatic_high_risk_family_history():
    r = _thrombo(vteType="asymptomatic_family_history", familyHistoryHighRiskThrombophilia=True)
    assert r["primaryRecommendation"]["id"] == "thrombo_r11"


def test_thrombophilia_panel_note():
    r = _thrombo(vteType="provoked_nonsurgical_major_transient")
    panel = next((x for x in r["additionalRecommendations"] if x["id"] == "thrombo_panel_note"), None)
    assert panel is not None
    assert "factor V Leiden" in panel["statement"]


# ─── Pathway 4: Pediatric VTE ─────────────────────────────────────────────────


def test_ped_symptomatic_dvt_pe():
    r = _ped(ageGroup="infant_child", vteType="symptomatic_dvt_or_pe", hemodynamicCompromise=False)
    assert r["pathway"] == "pediatric_vte"
    assert r["primaryRecommendation"]["id"] == "ped_rec1"
    assert r["primaryRecommendation"]["strength"] == "conditional"
    doac = next((x for x in r["additionalRecommendations"] if x["id"] == "ped_rec17_20"), None)
    assert doac is not None
    assert "rivaroxaban or dabigatran" in doac["statement"]


def test_ped_pe_hemodynamic_compromise():
    r = _ped(ageGroup="adolescent", vteType="symptomatic_dvt_or_pe", hemodynamicCompromise=True)
    rec15 = next((x for x in r["additionalRecommendations"] if x["id"] == "ped_rec15"), None)
    assert rec15 is not None
    assert "thrombolysis" in rec15["statement"]


def test_ped_provoked_no_exclusions():
    r = _ped(ageGroup="infant_child", vteType="provoked_vte", provokedExclusions=False)
    assert r["primaryRecommendation"]["id"] == "ped_rec3"
    assert "6 weeks" in r["primaryRecommendation"]["statement"]


def test_ped_provoked_with_exclusions():
    r = _ped(ageGroup="infant_child", vteType="provoked_vte", provokedExclusions=True)
    assert r["primaryRecommendation"]["id"] == "ped_rec3_excluded"
    assert "3 months" in r["primaryRecommendation"]["statement"]


def test_ped_unprovoked():
    r = _ped(ageGroup="adolescent", vteType="unprovoked_vte")
    assert r["primaryRecommendation"]["id"] == "ped_rec4"
    assert "6 to 12 months" in r["primaryRecommendation"]["statement"]


def test_ped_csvt():
    r = _ped(ageGroup="infant_child", vteType="csvt", csvtHemorrhage=False)
    assert r["primaryRecommendation"]["id"] == "ped_rec5_6"
    assert "anticoagulation alone" in r["primaryRecommendation"]["statement"]


def test_ped_rat_high_risk_low_bleed():
    r = _ped(
        ageGroup="neonate",
        vteType="rat_right_atrial_thrombus",
        ratHighRiskFeatures=True,
        ratBleedingRisk="low",
    )
    assert r["primaryRecommendation"]["id"] == "ped_rec7a"
    assert "anticoagulation is suggested" in r["primaryRecommendation"]["statement"]


def test_ped_rat_no_high_risk():
    r = _ped(
        ageGroup="neonate",
        vteType="rat_right_atrial_thrombus",
        ratHighRiskFeatures=False,
        ratBleedingRisk="low",
    )
    assert r["primaryRecommendation"]["id"] == "ped_rec7b"
    assert "no anticoagulation" in r["primaryRecommendation"]["statement"]


def test_ped_rvt_non_life_threatening_strong():
    r = _ped(ageGroup="neonate", vteType="rvt_renal_vein_thrombosis", rvtLifeThreatening=False)
    rec10a = next((x for x in r["additionalRecommendations"] if x["id"] == "ped_rec10a"), None)
    assert rec10a is not None
    assert rec10a["strength"] == "strong"


def test_ped_rvt_life_threatening():
    r = _ped(ageGroup="neonate", vteType="rvt_renal_vein_thrombosis", rvtLifeThreatening=True)
    rec10b = next((x for x in r["additionalRecommendations"] if x["id"] == "ped_rec10b"), None)
    assert rec10b is not None
    assert "thrombolysis" in rec10b["statement"]


def test_ped_cvad_no_longer_needed():
    r = _ped(ageGroup="infant_child", vteType="cvad_related", cvadFunctioning=False)
    assert r["primaryRecommendation"]["id"] == "ped_rec16"
    assert r["primaryRecommendation"]["certainty"] == "low"


def test_ped_hematology_alert_always():
    r = _ped(ageGroup="infant_child", vteType="symptomatic_dvt_or_pe")
    assert any("pediatric hematology" in a for a in r["clinicalAlerts"])


# ─── Pathway 5: Pregnancy-Associated VTE ─────────────────────────────────────


def test_preg_acute_vte_therapeutic_lmwh_strong():
    r = _preg(
        clinicalContext="treatment_acute_vte",
        trimester="second",
        thrombophiliaType="none",
        priorVTEProvoked=True,
    )
    assert r["pathway"] == "pregnancy_vte"
    assert r["primaryRecommendation"]["id"] == "preg_treatment"
    assert r["primaryRecommendation"]["strength"] == "strong"
    assert "LMWH" in r["primaryRecommendation"]["statement"]


def test_preg_doac_contraindicated_alert_always():
    r = _preg(
        clinicalContext="treatment_acute_vte",
        trimester="first",
        thrombophiliaType="none",
        priorVTEProvoked=True,
    )
    assert any("CONTRAINDICATED" in a for a in r["clinicalAlerts"])


def test_preg_prophylaxis_prior_unprovoked():
    r = _preg(
        clinicalContext="prophylaxis_prior_vte",
        trimester="first",
        thrombophiliaType="none",
        priorVTEHistory=True,
        priorVTEProvoked=False,
    )
    assert r["primaryRecommendation"]["id"] == "preg_prophylaxis_unprovoked"
    assert "LMWH" in r["primaryRecommendation"]["statement"]


def test_preg_prophylaxis_prior_provoked_no_thrombophilia():
    # "none" is a truthy string -> falls to unprovoked branch (matches TS)
    r = _preg(
        clinicalContext="prophylaxis_prior_vte",
        trimester="second",
        thrombophiliaType="none",
        priorVTEHistory=True,
        priorVTEProvoked=True,
    )
    assert r["primaryRecommendation"]["id"] in (
        "preg_prophylaxis_provoked",
        "preg_prophylaxis_unprovoked",
    )
    # Empty string for no thrombophilia -> provoked branch
    r2 = _preg(
        clinicalContext="prophylaxis_prior_vte",
        trimester="second",
        thrombophiliaType="",
        priorVTEHistory=True,
        priorVTEProvoked=True,
    )
    assert r2["primaryRecommendation"]["id"] == "preg_prophylaxis_provoked"
    assert "surveillance" in r2["primaryRecommendation"]["statement"]


def test_preg_high_risk_thrombophilia():
    r = _preg(
        clinicalContext="prophylaxis_thrombophilia",
        trimester="first",
        thrombophiliaType="high_risk",
    )
    assert r["primaryRecommendation"]["id"] == "preg_thrombophilia_high"
    assert "LMWH" in r["primaryRecommendation"]["statement"]


def test_preg_aps_aspirin_alert():
    r = _preg(
        clinicalContext="prophylaxis_thrombophilia",
        trimester="first",
        thrombophiliaType="antiphospholipid_syndrome",
    )
    assert any("aspirin" in a for a in r["clinicalAlerts"])


def test_preg_low_risk_thrombophilia_surveillance():
    r = _preg(
        clinicalContext="prophylaxis_thrombophilia",
        trimester="second",
        thrombophiliaType="low_risk",
    )
    assert r["primaryRecommendation"]["id"] == "preg_thrombophilia_low"
    assert "surveillance" in r["primaryRecommendation"]["statement"]


def test_preg_postpartum_management():
    r = _preg(
        clinicalContext="postpartum_management",
        trimester="postpartum",
        thrombophiliaType="none",
    )
    assert r["primaryRecommendation"]["id"] == "preg_postpartum"
    assert "warfarin" in r["primaryRecommendation"]["statement"]
    assert "breastfeeding" in r["primaryRecommendation"]["statement"]
