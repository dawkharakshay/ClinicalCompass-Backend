"""Psychiatry engine — fixtures derived directly from psychiatryLogic.ts branches.

Covers each condition's major decision paths plus contraindication/urgent paths.
"""

from app.recommendations.modules.psychiatry import assess


# ─── Dispatch / fallback ─────────────────────────────────────────────────────


def test_unknown_condition_is_insufficient_data():
    r = assess({"condition": "wat"})
    assert r["condition"] == "unknown"
    assert r["primaryRecommendation"]["indication"] == "Insufficient data"
    assert r["primaryRecommendation"]["cor"] == "N/A"
    assert r["guidelineYear"] == "N/A"


# ─── Delirium ────────────────────────────────────────────────────────────────


def test_delirium_prevention_avoids_antipsychotics():
    r = assess({"condition": "delirium", "preventionContext": True, "deliriumSubtype": "mixed"})
    assert "AVOID antipsychotics for prevention" in r["primaryRecommendation"]["pharmacotherapy"]
    assert "(prevention context)" in r["primaryRecommendation"]["indication"]
    assert "PARADIGM SHIFT" in r["practiceChangingNote"]


def test_delirium_withdrawal_uses_benzodiazepines():
    r = assess({"condition": "delirium", "substanceWithdrawal": True, "deliriumSubtype": "hyperactive"})
    assert "CONTRAINDICATED" in r["primaryRecommendation"]["pharmacotherapy"]
    assert any("withdrawal delirium" in u for u in r["urgentFlags"])
    assert "(withdrawal)" in r["primaryRecommendation"]["indication"]


def test_delirium_severe_safety_risk_reserves_antipsychotics():
    r = assess({"condition": "delirium", "severeSafetyRisk": True, "deliriumSubtype": ""})
    assert "Reserve for severe agitation only" in r["primaryRecommendation"]["pharmacotherapy"]
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient Medical Unit with 1:1 sitter"
    assert "unspecified subtype" in r["primaryRecommendation"]["indication"]


def test_delirium_routine_and_icu_and_age_safety():
    r = assess({"condition": "delirium", "icuPatient": True, "age": "70", "dementiaDiagnosis": True})
    assert r["primaryRecommendation"]["levelOfCare"] == "ICU/Critical Care"
    assert "AVOID antipsychotics for routine delirium treatment" in r["primaryRecommendation"]["pharmacotherapy"]
    assert any("Older adults" in s for s in r["safetyConsiderations"])
    assert any("black box warning" in s for s in r["safetyConsiderations"])


# ─── BPD ─────────────────────────────────────────────────────────────────────


def test_bpd_no_prior_therapy_dbt_first_line():
    r = assess({"condition": "bpd"})
    assert "Dialectical Behavior Therapy (DBT) — first-line (strongest evidence)" in r["primaryRecommendation"]["firstLineIntervention"]
    assert r["primaryRecommendation"]["levelOfCare"] == "Outpatient structured psychotherapy"


def test_bpd_prior_dbt_only():
    r = assess({"condition": "bpd", "priorDBT": True})
    assert "Continue/optimize DBT" in r["primaryRecommendation"]["firstLineIntervention"]


def test_bpd_prior_dbt_and_mbt_higher_care():
    r = assess({"condition": "bpd", "priorDBT": True, "priorMBT": True})
    assert r["primaryRecommendation"]["levelOfCare"] == "Intensive outpatient or partial hospitalization"


def test_bpd_crisis_and_substance_use():
    r = assess({"condition": "bpd", "currentCrisis": True, "substanceUse": True, "polypharmacy": True})
    assert "— Acute Crisis" in r["primaryRecommendation"]["indication"]
    assert r["primaryRecommendation"]["levelOfCare"] == "Crisis stabilization / brief inpatient if safety concern"
    assert any("Comorbid substance use disorder" in u for u in r["urgentFlags"])
    assert any("Polypharmacy" in s for s in r["safetyConsiderations"])


# ─── Depression ──────────────────────────────────────────────────────────────


def test_depression_trd_by_trials_failed():
    r = assess({"condition": "depression", "trialsFailed": "3", "severity": "moderate"})
    assert "Esketamine (SPRAVATO) intranasal" in r["primaryRecommendation"]["firstLineIntervention"][0]
    assert "TRD (3 failed adequate trials)" in r["primaryRecommendation"]["pharmacotherapy"]


def test_depression_trd_flag_indication_and_loc():
    r = assess({"condition": "depression", "trd": True, "severity": "moderate"})
    assert "(Treatment-Resistant)" in r["primaryRecommendation"]["indication"]
    assert r["primaryRecommendation"]["levelOfCare"] == "Outpatient with close follow-up (2–4 weeks) or partial hospitalization"


def test_depression_psychotic_requires_combination():
    r = assess({"condition": "depression", "severity": "severe", "psychoticFeatures": True})
    assert "Antidepressant + antipsychotic combination" in r["primaryRecommendation"]["pharmacotherapy"]
    assert any("Psychotic depression" in u for u in r["urgentFlags"])


def test_depression_perinatal():
    r = assess({"condition": "depression", "pregnancyOrPostpartum": True, "severity": "moderate"})
    assert "(Perinatal)" in r["primaryRecommendation"]["indication"]
    assert "Brexanolone or zuranolone" in r["primaryRecommendation"]["pharmacotherapy"]


def test_depression_mild_moderate_default():
    r = assess({"condition": "depression", "severity": "mild", "measurementBasedCare": True})
    assert r["primaryRecommendation"]["levelOfCare"] == "Outpatient"
    assert "Measurement-based care (PHQ-9 at every visit) is being used" in r["primaryRecommendation"]["notes"]


def test_depression_suicidal_and_bipolar_flags():
    r = assess({"condition": "depression", "severity": "moderate", "suicidalIdeation": True, "bipolarHistory": True})
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient or crisis stabilization"
    assert any("Bipolar history" in u for u in r["urgentFlags"])
    assert any("Do NOT use antidepressant monotherapy" in s for s in r["safetyConsiderations"])


# ─── Schizophrenia ───────────────────────────────────────────────────────────


def test_schizophrenia_trs_clozapine():
    r = assess({"condition": "schizophrenia", "treatmentResistant": True, "clozapineEligible": True})
    assert "Clozapine" in r["primaryRecommendation"]["firstLineIntervention"][0]
    assert "— Treatment-Resistant" in r["primaryRecommendation"]["indication"]
    assert r["primaryRecommendation"]["levelOfCare"] == "Intensive outpatient or ACT"


def test_schizophrenia_trs_not_clozapine_eligible_urgent():
    r = assess({"condition": "schizophrenia", "treatmentResistant": True, "clozapineEligible": False})
    assert any("clozapine evaluation required" in u for u in r["urgentFlags"])


def test_schizophrenia_first_episode():
    r = assess({"condition": "schizophrenia", "firstEpisode": True})
    assert "— First Episode" in r["primaryRecommendation"]["indication"]
    assert "Coordinated Specialty Care" in r["primaryRecommendation"]["notes"]


def test_schizophrenia_nonadherence_lai_with_current():
    r = assess({"condition": "schizophrenia", "nonadherence": True, "currentAntipsychotic": "olanzapine"})
    assert "Current oral: olanzapine — consider LAI equivalent." in r["primaryRecommendation"]["pharmacotherapy"]


def test_schizophrenia_maintenance_metabolic_and_acute():
    r = assess({"condition": "schizophrenia", "acuteExacerbation": True, "metabolicConcerns": True, "currentAntipsychotic": "risperidone"})
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient stabilization"
    assert "Continue risperidone at therapeutic dose." in r["primaryRecommendation"]["pharmacotherapy"]
    assert any("Metabolic monitoring required" in s for s in r["safetyConsiderations"])
    assert any("metabolically neutral antipsychotic" in f for f in r["primaryRecommendation"]["firstLineIntervention"])


# ─── Eating Disorders ────────────────────────────────────────────────────────


def test_ed_anorexia_pediatric_fbt():
    r = assess({"condition": "eating_disorder", "edType": "AN", "pediatric": True, "bmi": "16", "age": "15"})
    assert "Family-Based Treatment (FBT/Maudsley)" in r["primaryRecommendation"]["firstLineIntervention"][0]
    assert r["primaryRecommendation"]["psychotherapy"] == "FBT (Maudsley) — first-line for adolescents"
    assert any("Refeeding syndrome risk" in s for s in r["safetyConsiderations"])


def test_ed_anorexia_severe_bmi_inpatient():
    r = assess({"condition": "eating_disorder", "edType": "AN", "bmi": "14", "age": "30"})
    assert any("Severe anorexia nervosa (BMI <15)" in u for u in r["urgentFlags"])
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient psychiatric/residential"
    assert r["primaryRecommendation"]["psychotherapy"] == "CBT-E or SSCM"


def test_ed_bulimia_fluoxetine():
    r = assess({"condition": "eating_disorder", "edType": "BN", "bmi": "22", "age": "25"})
    assert "Fluoxetine 60 mg/day" in r["primaryRecommendation"]["pharmacotherapy"]
    assert r["primaryRecommendation"]["psychotherapy"] == "CBT-BN — first-line"


def test_ed_bed_lisdexamfetamine():
    r = assess({"condition": "eating_disorder", "edType": "BED", "bmi": "30", "age": "40"})
    assert "Lisdexamfetamine (Vyvanse)" in r["primaryRecommendation"]["pharmacotherapy"]


def test_ed_medically_unstable_and_arfid():
    r = assess({"condition": "eating_disorder", "edType": "ARFID", "medicallyUnstable": True, "bmi": "19", "age": "20"})
    assert any("Medically unstable" in u for u in r["urgentFlags"])
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient medical"
    assert "(Medically Unstable)" in r["primaryRecommendation"]["indication"]


# ─── Benzo Tapering ──────────────────────────────────────────────────────────


def test_benzo_long_duration_very_slow_taper_alprazolam():
    r = assess({"condition": "benzo_tapering", "benzoName": "Alprazolam", "durationYears": "8", "dailyDoseMg": "2"})
    assert "Very slow taper" in r["primaryRecommendation"]["pharmacotherapy"]
    assert "Alprazolam → diazepam equivalent" in r["primaryRecommendation"]["pharmacotherapy"]
    assert "8 years of use" in r["primaryRecommendation"]["indication"]


def test_benzo_one_year_singular_and_standard_taper():
    r = assess({"condition": "benzo_tapering", "benzoName": "lorazepam", "durationYears": "1", "dailyDoseMg": "1"})
    assert "1 year of use" in r["primaryRecommendation"]["indication"]  # singular
    assert "Standard taper" in r["primaryRecommendation"]["pharmacotherapy"]
    assert "Lorazepam → diazepam equivalent" in r["primaryRecommendation"]["pharmacotherapy"]


def test_benzo_seizure_history_urgent_inpatient():
    r = assess({"condition": "benzo_tapering", "benzoName": "clonazepam", "durationYears": "3", "dailyDoseMg": "1", "seizureHistory": True, "patientMotivated": True})
    assert any("Prior seizure or withdrawal history" in u for u in r["urgentFlags"])
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient or residential medical detox"


def test_benzo_not_motivated_safety():
    r = assess({"condition": "benzo_tapering", "benzoName": "diazepam", "durationYears": "2", "dailyDoseMg": "5", "patientMotivated": False})
    assert any("Patient not motivated for taper" in s for s in r["safetyConsiderations"])
    assert "Slow taper" in r["primaryRecommendation"]["pharmacotherapy"]


# ─── PTSD ────────────────────────────────────────────────────────────────────


def test_ptsd_no_prior_therapy_first_line():
    r = assess({"condition": "ptsd", "severity": "moderate", "traumaType": "combat"})
    assert "Prolonged Exposure (PE)" in r["primaryRecommendation"]["firstLineIntervention"][0]
    assert "(combat)" in r["primaryRecommendation"]["indication"]


def test_ptsd_prior_therapy_lists_tried():
    r = assess({"condition": "ptsd", "severity": "severe", "priorPE": True, "priorEMDR": True, "traumaType": "sexual_assault"})
    assert "Prior therapies: PE, EMDR" in r["primaryRecommendation"]["firstLineIntervention"][0]
    assert "(sexual assault)" in r["primaryRecommendation"]["indication"]


def test_ptsd_dissociative_and_veteran_and_sud():
    r = assess({"condition": "ptsd", "severity": "moderate", "dissociativeSubtype": True, "militaryVeteran": True, "comorbidSUD": True})
    assert "Phase-based treatment" in r["primaryRecommendation"]["firstLineIntervention"][0]
    assert "(Military Veteran)" in r["primaryRecommendation"]["indication"]
    assert r["primaryRecommendation"]["levelOfCare"] == "Integrated dual-diagnosis outpatient"
    assert any("Comorbid substance use disorder" in u for u in r["urgentFlags"])


def test_ptsd_suicidal_inpatient():
    r = assess({"condition": "ptsd", "severity": "severe", "suicidalIdeation": True})
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient or crisis stabilization"


# ─── Suicide Risk ────────────────────────────────────────────────────────────


def test_suicide_imminent_by_plan_means_intent():
    r = assess({"condition": "suicide_risk", "plan": True, "means": True, "intent": True})
    assert "Imminent/High Risk" in r["primaryRecommendation"]["indication"]
    assert any("IMMINENT SUICIDE RISK" in u for u in r["urgentFlags"])
    assert r["primaryRecommendation"]["levelOfCare"] == "Emergency psychiatric evaluation / inpatient hospitalization"


def test_suicide_imminent_by_score():
    # 3+3+3 = 9 -> imminent even without all of plan/means/intent
    r = assess({"condition": "suicide_risk", "currentSI": True, "plan": True, "means": True})
    assert "Imminent/High Risk" in r["primaryRecommendation"]["indication"]
    assert "Risk score: 9" in r["primaryRecommendation"]["notes"]


def test_suicide_high_by_prior_attempt():
    r = assess({"condition": "suicide_risk", "priorAttempt": True})
    assert "High Risk" in r["primaryRecommendation"]["indication"]
    assert r["primaryRecommendation"]["levelOfCare"] == "Urgent outpatient evaluation or crisis stabilization unit"


def test_suicide_moderate_by_current_si():
    r = assess({"condition": "suicide_risk", "currentSI": True})
    # score 3 -> not >=5, not plan/priorAttempt -> Moderate (>=2 or currentSI)
    assert "Moderate Risk" in r["primaryRecommendation"]["indication"]
    assert any("Safety planning required" in s for s in r["safetyConsiderations"])


def test_suicide_low_with_protective_factors():
    r = assess({"condition": "suicide_risk", "protectiveFactors": True})
    assert "Low Risk" in r["primaryRecommendation"]["indication"]
    assert "Risk score: -2" in r["primaryRecommendation"]["notes"]
    assert "Strengthen protective factors" in r["primaryRecommendation"]["firstLineIntervention"][5]
    assert "none identified" in r["primaryRecommendation"]["notes"]


# ─── Bipolar ─────────────────────────────────────────────────────────────────


def test_bipolar_manic_severe_inpatient():
    r = assess({"condition": "bipolar", "currentPhase": "manic", "severity": "severe", "bipolarType": "I"})
    assert r["primaryRecommendation"]["levelOfCare"] == "Inpatient stabilization"
    assert any("Severe mania" in u for u in r["urgentFlags"])


def test_bipolar_manic_psychotic_pharmacotherapy():
    r = assess({"condition": "bipolar", "currentPhase": "manic", "psychoticFeatures": True})
    assert "ECT for severe/refractory mania" in r["primaryRecommendation"]["pharmacotherapy"]
    assert "with Psychotic Features" in r["primaryRecommendation"]["indication"]


def test_bipolar_depressed_type_ii_lamotrigine():
    r = assess({"condition": "bipolar", "currentPhase": "depressed", "bipolarType": "II"})
    assert "Lamotrigine is preferred for bipolar II depression." in r["primaryRecommendation"]["pharmacotherapy"]
    assert "AVOID antidepressant monotherapy" in r["primaryRecommendation"]["pharmacotherapy"]


def test_bipolar_rapid_cycling():
    r = assess({"condition": "bipolar", "currentPhase": "euthymic", "rapidCycling": True})
    assert "Lithium + valproate combination" in r["primaryRecommendation"]["firstLineIntervention"][0]
    assert "(Rapid Cycling)" in r["primaryRecommendation"]["indication"]


def test_bipolar_maintenance_lithium_tried():
    r = assess({"condition": "bipolar", "currentPhase": "euthymic", "lithiumTried": True})
    assert "Lithium (target 0.6–0.8 mEq/L for maintenance)" in r["primaryRecommendation"]["pharmacotherapy"]


def test_bipolar_pregnancy_urgent_and_safety():
    r = assess({"condition": "bipolar", "currentPhase": "euthymic", "pregnancyOrPostpartum": True})
    assert any("reproductive psychiatry consultation required" in u for u in r["urgentFlags"])
    assert any("avoid valproate" in s for s in r["safetyConsiderations"])
