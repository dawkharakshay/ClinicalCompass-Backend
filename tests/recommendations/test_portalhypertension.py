"""Portal Hypertension Clinical Compass — tests.

Ported 1:1 from old_static_code/server/portal-hypertension.test.ts.
"""

from __future__ import annotations

import copy

from app.recommendations.modules.portalhypertension import assess

# Base Input (stable compensated cirrhosis, no active complications)
BASE_INPUT = {
    "ageYears": 55,
    "primaryScenario": "primary_prophylaxis",
    "hasCirrhosis": True,
    "childPughClass": "A",
    "meldCategory": "low",
    "hasClinicallySignificantPH": True,
    "bavenoVIICriteriaMet": False,
    "pvtExtent": "none",
    "pvtAcuity": "unknown",
    "hasIntestinalIschemia": False,
    "hasThrombophilia": False,
    "isOnAnticoagulation": False,
    "hasAnticoagulationContraindication": False,
    "varicesGrade": "large",
    "hasRedWaleMarks": False,
    "hasActiveVaricealBleeding": False,
    "hasPriorVaricealBleeding": False,
    "isOnNSBB": False,
    "hasPriorEBL": False,
    "hasGastricVarices": False,
    "ascitesGrade": "none",
    "hasSBP": False,
    "hasPriorSBP": False,
    "saagHighGradient": True,
    "ascitesProteinLow": False,
    "isDiureticRefractory": False,
    "isDiureticIntolerant": False,
    "heGrade": "none",
    "hePrecipitantIdentified": False,
    "hasPriorHEEpisode": False,
    "isOnLactulose": False,
    "isOnRifaximin": False,
    "hasHRS": False,
    "hasPriorTIPS": False,
    "hasTIPSContraindication": False,
    "isTransplantCandidate": False,
    "isListedForTransplant": False,
}


def make(**overrides) -> dict:
    d = copy.deepcopy(BASE_INPUT)
    d.update(overrides)
    return d


# ─── 1. Primary Prophylaxis ───────────────────────────────────────────────────
def test_carvedilol_large_varices():
    r = assess(make())
    assert "carvedilol" in r["varicesProphylaxis"]
    assert "EBL" in r["varicesProphylaxis"]
    assert "carvedilol" in r["primaryRecommendation"]


def test_carvedilol_medium_varices_red_wale():
    r = assess(make(varicesGrade="medium", hasRedWaleMarks=True))
    assert "carvedilol" in r["varicesProphylaxis"]
    assert any("Carvedilol" in a for a in r["recommendedAgents"])


def test_baveno_avoids_endoscopy():
    r = assess(make(varicesGrade="small", bavenoVIICriteriaMet=True))
    assert "Baveno VII criteria met" in r["varicesProphylaxis"]
    assert "Endoscopy can be safely avoided" in r["varicesProphylaxis"]


def test_egd_screening_not_screened():
    r = assess(make(varicesGrade="not_screened"))
    assert "upper endoscopy" in r["varicesProphylaxis"]
    assert any("endoscopy" in s for s in r["nextSteps"])


def test_nsbb_small_varices_child_a():
    r = assess(make(varicesGrade="small", childPughClass="A", hasRedWaleMarks=False))
    assert "carvedilol" in r["varicesProphylaxis"]


# ─── 2. Acute Variceal Bleeding ───────────────────────────────────────────────
def test_urgent_flag_active_bleed():
    r = assess(make(primaryScenario="acute_variceal_bleed", hasActiveVaricealBleeding=True, childPughClass="B"))
    assert len(r["urgentFlags"]) > 0
    assert "ACTIVE VARICEAL BLEEDING" in r["urgentFlags"][0]
    assert "octreotide" in r["urgentFlags"][0]
    assert "ceftriaxone" in r["urgentFlags"][0]


def test_preemptive_tips_child_bc():
    r = assess(make(hasActiveVaricealBleeding=True, childPughClass="C", meldCategory="high"))
    assert "TIPS within 72h" in r["urgentFlags"][0]
    assert "Pre-emptive TIPS" in r["tipsIndication"]


def test_octreotide_ceftriaxone_agents():
    r = assess(make(hasActiveVaricealBleeding=True))
    assert any("Octreotide" in a for a in r["recommendedAgents"])
    assert any("Ceftriaxone" in a for a in r["recommendedAgents"])


def test_gastric_varices_gov2():
    r = assess(make(hasActiveVaricealBleeding=True, hasGastricVarices=True, gastricVaricesType="GOV2"))
    assert "GOV2" in r["acuteBleedManagement"]
    assert "BRTO" in r["acuteBleedManagement"]


def test_balloon_tamponade_mention():
    r = assess(make(hasActiveVaricealBleeding=True))
    assert "BALLOON TAMPONADE" in r["acuteBleedManagement"]


# ─── 3. Secondary Prophylaxis ─────────────────────────────────────────────────
def test_nsbb_ebl_combination():
    r = assess(make(primaryScenario="secondary_prophylaxis", hasPriorVaricealBleeding=True))
    assert "NSBB + EBL COMBINATION" in r["secondaryProphylaxis"]
    assert "carvedilol" in r["secondaryProphylaxis"]


def test_tips_rebleeding_despite_nsbb_ebl():
    r = assess(make(hasPriorVaricealBleeding=True, isOnNSBB=True, hasPriorEBL=True))
    assert "Secondary prophylaxis TIPS" in r["tipsIndication"]


def test_start_carvedilol_next_step():
    r = assess(make(hasPriorVaricealBleeding=True, isOnNSBB=False))
    assert any("carvedilol" in s for s in r["nextSteps"])


# ─── 4. Portal Vein Thrombosis ────────────────────────────────────────────────
def test_acute_pvt_anticoagulation():
    r = assess(make(primaryScenario="pvt_management", pvtExtent="complete_main", pvtAcuity="acute"))
    assert "anticoagulation is strongly recommended" in r["pvtManagement"]
    assert "ACUTE PVT" in r["primaryRecommendation"]
    assert any("Enoxaparin" in a for a in r["recommendedAgents"])


def test_lmwh_child_bc_cirrhotic_pvt():
    r = assess(make(pvtExtent="complete_main", pvtAcuity="acute", childPughClass="B"))
    assert "LMWH" in r["anticoagulationPlan"]
    assert "enoxaparin" in r["anticoagulationPlan"]


def test_doac_noncirrhotic_pvt():
    r = assess(make(pvtExtent="partial_main", pvtAcuity="acute", childPughClass="A", hasCirrhosis=False))
    assert "rivaroxaban" in r["anticoagulationPlan"]


def test_intestinal_ischemia_urgent():
    r = assess(make(pvtExtent="extending_smv", pvtAcuity="acute", hasIntestinalIschemia=True))
    assert any("INTESTINAL ISCHEMIA" in f for f in r["urgentFlags"])
    assert any("CT angiography" in s for s in r["nextSteps"])


def test_cavernous_transformation():
    r = assess(make(pvtExtent="cavernous_transformation", pvtAcuity="chronic"))
    assert "cavernous transformation" in r["pvtManagement"]
    assert "recanalization is not feasible" in r["pvtManagement"]


def test_tips_when_anticoag_contraindicated():
    r = assess(make(pvtExtent="complete_main", pvtAcuity="acute", hasAnticoagulationContraindication=True))
    assert "ANTICOAGULATION CONTRAINDICATED" in r["pvtManagement"]
    assert "Anticoagulation contraindicated" in r["anticoagulationPlan"]
    assert "PVT with anticoagulation contraindication" in r["tipsIndication"]


# ─── 5. Ascites Management ────────────────────────────────────────────────────
def test_spironolactone_grade1():
    r = assess(make(primaryScenario="ascites_management", ascitesGrade="grade1"))
    assert "spironolactone" in r["ascitesManagement"]
    assert any("Spironolactone" in a for a in r["recommendedAgents"])


def test_spiro_furosemide_grade2():
    r = assess(make(ascitesGrade="grade2"))
    assert "5:2 ratio" in r["ascitesManagement"]
    assert "furosemide" in r["ascitesManagement"]


def test_lvp_albumin_grade3():
    r = assess(make(ascitesGrade="grade3"))
    assert "large-volume paracentesis" in r["ascitesManagement"]
    assert "albumin 6–8g per liter" in r["ascitesManagement"]
    assert any("albumin" in a for a in r["recommendedAgents"])


def test_tips_refractory_ascites_low_meld():
    r = assess(make(primaryScenario="ascites_management", ascitesGrade="refractory", isDiureticRefractory=True, meldCategory="moderate"))
    assert "REFRACTORY ASCITES" in r["ascitesManagement"]
    assert "TIPS" in r["ascitesManagement"]
    assert "REFRACTORY ASCITES" in r["primaryRecommendation"]
    assert "Refractory ascites" in r["tipsIndication"]


def test_norfloxacin_prior_sbp():
    r = assess(make(ascitesGrade="grade2", hasPriorSBP=True))
    assert "norfloxacin" in r["sbpProphylaxis"]
    assert any("Norfloxacin" in a for a in r["recommendedAgents"])


def test_active_sbp_urgent_albumin():
    r = assess(make(ascitesGrade="grade2", hasSBP=True))
    assert any("SPONTANEOUS BACTERIAL PERITONITIS" in f for f in r["urgentFlags"])
    assert any("albumin" in f for f in r["urgentFlags"])


# ─── 6. Hepatic Encephalopathy ────────────────────────────────────────────────
def test_lactulose_minimal_he():
    r = assess(make(primaryScenario="hepatic_encephalopathy", heGrade="minimal"))
    assert "lactulose" in r["heManagement"]
    assert any("Lactulose" in a for a in r["recommendedAgents"])


def test_rifaximin_grade2_he():
    r = assess(make(heGrade="grade2"))
    assert "Rifaximin" in r["heManagement"]
    assert any("Rifaximin" in a for a in r["recommendedAgents"])


def test_grade3_he_urgent_tips_contra():
    r = assess(make(heGrade="grade3"))
    assert any("SEVERE HEPATIC ENCEPHALOPATHY" in f for f in r["urgentFlags"])
    assert any("TIPS" in f for f in r["urgentFlags"])


def test_grade4_he_urgent_icu():
    r = assess(make(heGrade="grade4"))
    assert any("Grade 4" in f for f in r["urgentFlags"])
    assert "SEVERE HEPATIC ENCEPHALOPATHY" in r["primaryRecommendation"]


def test_rifaximin_next_step_recurrent_he():
    r = assess(make(heGrade="grade1", hasPriorHEEpisode=True, isOnRifaximin=False))
    assert any("rifaximin" in s for s in r["nextSteps"])


def test_tips_contra_he_grade34():
    r = assess(make(heGrade="grade3", hasTIPSContraindication=True, tipsContraindications=["he_grade3_4"]))
    assert "HE Grade 3" in r["tipsContraindicationAssessment"]


# ─── 7. Hepatorenal Syndrome ──────────────────────────────────────────────────
def test_hrs_aki_urgent_terlipressin():
    r = assess(make(primaryScenario="hepatorenal_syndrome", hasHRS=True, hrsType="HRS_AKI"))
    assert any("HRS-AKI" in f for f in r["urgentFlags"])
    assert any("Terlipressin" in f for f in r["urgentFlags"])
    assert "HRS-AKI" in r["primaryRecommendation"]
    assert any("Terlipressin" in a for a in r["recommendedAgents"])


def test_hrs_aki_albumin_norepinephrine():
    r = assess(make(hasHRS=True, hrsType="HRS_AKI"))
    assert "albumin 1g/kg/day" in r["hrsManagement"]
    assert "norepinephrine" in r["hrsManagement"]
    assert "CONFIRM trial" in r["hrsManagement"]


def test_hrs_ckd_slk():
    r = assess(make(hasHRS=True, hrsType="HRS_CKD"))
    assert "HRS-CKD" in r["hrsManagement"]
    assert "liver-kidney transplant" in r["hrsManagement"]


def test_hrs_aki_transplant_next_step():
    r = assess(make(hasHRS=True, hrsType="HRS_AKI"))
    assert any("transplant" in s for s in r["nextSteps"])


# ─── 8. TIPS Assessment ───────────────────────────────────────────────────────
def test_no_tips_indication_stable():
    r = assess(make())
    assert "No current TIPS indication" in r["tipsIndication"]


def test_heart_failure_tips_contra():
    r = assess(make(hasTIPSContraindication=True, tipsContraindications=["heart_failure"]))
    assert "Congestive heart failure" in r["tipsContraindicationAssessment"]


def test_pulmonary_htn_tips_contra():
    r = assess(make(hasTIPSContraindication=True, tipsContraindications=["severe_pulmonary_htn"]))
    assert "pulmonary" in r["tipsContraindicationAssessment"]


def test_child_c_meld_high_mortality():
    r = assess(make(childPughClass="C", meldCategory="very_high"))
    assert "Child-Pugh C" in r["tipsContraindicationAssessment"]


def test_clears_tips_contra_when_none():
    r = assess(make(hasTIPSContraindication=False))
    assert "No absolute TIPS contraindications" in r["tipsContraindicationAssessment"]


# ─── 9. Transplant Consideration ─────────────────────────────────────────────
def test_transplant_eval_meld_high():
    r = assess(make(meldCategory="very_high", isTransplantCandidate=True))
    assert "LIVER TRANSPLANT EVALUATION RECOMMENDED" in r["transplantConsideration"]
    assert "MELD ≥20" in r["transplantConsideration"]
    assert any("MELD ≥20" in f for f in r["urgentFlags"])


def test_refractory_ascites_transplant_indication():
    r = assess(make(ascitesGrade="refractory", isTransplantCandidate=True))
    assert "Refractory ascites" in r["transplantConsideration"]


def test_stable_no_transplant_eval():
    r = assess(make())
    assert "No current decompensation events" in r["transplantConsideration"]


def test_urgent_listing_next_step():
    r = assess(make(meldCategory="very_high", isTransplantCandidate=True, isListedForTransplant=False))
    assert any("transplant" in s for s in r["nextSteps"])


# ─── 10. Evidence Level & References ─────────────────────────────────────────
def test_evidence_a_active_bleed():
    r = assess(make(hasActiveVaricealBleeding=True))
    assert r["evidenceLevel"] == "A"


def test_evidence_a_sbp():
    r = assess(make(hasSBP=True))
    assert r["evidenceLevel"] == "A"


def test_evidence_a_hrs_aki():
    r = assess(make(hasHRS=True, hrsType="HRS_AKI"))
    assert r["evidenceLevel"] == "A"


def test_baveno_reference():
    r = assess(make())
    assert any("Baveno VII" in ref["citation"] for ref in r["references"])


def test_confirm_reference():
    r = assess(make())
    assert any("CONFIRM" in ref["citation"] for ref in r["references"])


def test_rifaximin_reference():
    r = assess(make())
    assert any("Rifaximin" in ref["citation"] for ref in r["references"])


def test_preemptive_tips_reference():
    r = assess(make())
    assert any("Pre-emptive TIPS" in ref["citation"] for ref in r["references"])


def test_rationale_clinical_variables():
    r = assess(make())
    assert "Child-Pugh" in r["rationale"]
    assert "MELD" in r["rationale"]


def test_monitoring_plan_hcc():
    r = assess(make())
    assert "HCC surveillance" in r["monitoringPlan"]
    assert "Doppler ultrasound" in r["monitoringPlan"]
