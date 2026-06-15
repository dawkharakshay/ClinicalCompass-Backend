"""Psychiatry Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/psychiatryLogic.ts
(evaluatePsychiatry and all condition evaluators).

Guidelines: APA 2025-2026, VA/DoD 2023-2024, SAMHSA, NICE.
Conditions: Delirium, BPD, Depression/TRD, Schizophrenia, Eating Disorders,
            Benzo Tapering, PTSD, Suicide Risk, Bipolar Disorder.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "psychiatry"


def assess(data: dict) -> dict:
    condition = data.get("condition")
    if condition == "delirium":
        return _evaluate_delirium(data)
    if condition == "bpd":
        return _evaluate_bpd(data)
    if condition == "depression":
        return _evaluate_depression(data)
    if condition == "schizophrenia":
        return _evaluate_schizophrenia(data)
    if condition == "eating_disorder":
        return _evaluate_eating_disorder(data)
    if condition == "benzo_tapering":
        return _evaluate_benzo_tapering(data)
    if condition == "ptsd":
        return _evaluate_ptsd(data)
    if condition == "suicide_risk":
        return _evaluate_suicide_risk(data)
    if condition == "bipolar":
        return _evaluate_bipolar(data)
    return _insufficient_data("unknown")


def _str(x) -> str:
    """JS-style `value || ""` for string fields (None/"" -> "")."""
    return x if (isinstance(x, str) and x != "") else ""


# ─────────────────────────────────────────────────────────────────────────────
# DELIRIUM — APA 2025 (PRACTICE-CHANGING)
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_delirium(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []
    monitoring: list[str] = []
    mdt_consult = ["Geriatrics or Palliative Care", "Nursing (reorientation protocols)", "Pharmacy (medication review)"]

    age = parse_float(input.get("age"))

    if truthy(input.get("substanceWithdrawal")):
        urgent.append("Alcohol/benzo withdrawal delirium — benzodiazepines are FIRST-LINE; antipsychotics are contraindicated")
    if truthy(input.get("dementiaDiagnosis")):
        urgent.append("Dementia increases delirium risk — minimize anticholinergics and sedatives")
        safety.append("Avoid antipsychotics in dementia-related delirium (increased mortality risk — FDA black box warning)")
    if age >= 65:
        safety.append("Older adults: higher risk of antipsychotic-related falls, QTc prolongation, and extrapyramidal symptoms")

    monitoring.extend([
        "CAM or CAM-ICU score q8h",
        "Vital signs and oxygenation",
        "Medication reconciliation for deliriogenic agents",
        "Sleep-wake cycle monitoring",
    ])

    pharmacotherapy = ""
    first_line: list[str] = []
    notes = ""
    practice_changing_note = ""

    if truthy(input.get("preventionContext")):
        first_line = ["Non-pharmacologic prevention bundle (HELP protocol)", "Sleep hygiene optimization", "Early mobilization", "Sensory aids (glasses, hearing aids)", "Hydration and nutrition optimization", "Reorientation interventions"]
        pharmacotherapy = "AVOID antipsychotics for prevention (APA 2025 — no benefit, potential harm)"
        notes = "APA 2025 PRACTICE CHANGE: Antipsychotics are NOT recommended for delirium prevention. Non-pharmacologic multicomponent interventions (HELP protocol) remain the standard of care."
        practice_changing_note = "APA 2025 PARADIGM SHIFT: Antipsychotics should NOT be used for delirium prevention or routine treatment. This is a major departure from prior practice."
    elif truthy(input.get("substanceWithdrawal")):
        first_line = ["Benzodiazepines (CIWA-Ar protocol)", "Thiamine 100 mg IV before glucose", "Electrolyte replacement"]
        pharmacotherapy = "Lorazepam or diazepam per CIWA-Ar protocol. Antipsychotics CONTRAINDICATED."
        notes = "Alcohol/benzo withdrawal delirium requires benzodiazepines. Antipsychotics lower seizure threshold and are contraindicated."
    elif truthy(input.get("severeSafetyRisk")) and not truthy(input.get("substanceWithdrawal")):
        first_line = ["Non-pharmacologic de-escalation (first)", "Environmental modification", "One-to-one sitter"]
        pharmacotherapy = "Antipsychotics (haloperidol 0.5–1 mg IV/IM or quetiapine 12.5–25 mg PO) ONLY if severe distress or immediate safety risk — use lowest effective dose for shortest duration. APA 2025: Reserve for severe agitation only."
        notes = "APA 2025: Antipsychotics are reserved ONLY for severe distress or immediate safety risk. Not for routine delirium management. Use lowest dose, shortest duration."
        practice_changing_note = "APA 2025 PRACTICE CHANGE: Antipsychotics are no longer recommended for routine delirium treatment. Use only for severe agitation posing immediate safety risk."
    else:
        first_line = ["Non-pharmacologic multicomponent care (HELP protocol)", "Treat underlying cause", "Reorientation and cognitive stimulation", "Sleep-wake cycle optimization", "Early mobilization", "Minimize deliriogenic medications"]
        pharmacotherapy = "AVOID antipsychotics for routine delirium treatment (APA 2025). Address underlying etiology."
        notes = "APA 2025 PRACTICE CHANGE: Antipsychotics do not improve outcomes in delirium and may cause harm. Focus on identifying and treating the underlying cause."
        practice_changing_note = "APA 2025 PARADIGM SHIFT: First major delirium guideline update in >20 years. Antipsychotics should NOT be used for prevention or routine treatment of delirium."

    subtype = _str(input.get("deliriumSubtype")) or "unspecified subtype"
    indication = f"Delirium — {subtype}"
    if truthy(input.get("preventionContext")):
        indication += " (prevention context)"
    if truthy(input.get("substanceWithdrawal")):
        indication += " (withdrawal)"

    if truthy(input.get("icuPatient")):
        level_of_care = "ICU/Critical Care"
    elif truthy(input.get("severeSafetyRisk")):
        level_of_care = "Inpatient Medical Unit with 1:1 sitter"
    else:
        level_of_care = "Medical unit with delirium bundle"

    return {
        "condition": "delirium",
        "primaryRecommendation": {
            "indication": indication,
            "firstLineIntervention": first_line,
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": "Not applicable — behavioral/environmental interventions are primary",
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "APA Practice Guideline for Delirium 2025",
            "notes": notes,
        },
        "alternativeRecommendations": [
            {
                "indication": "Refractory agitation in ICU delirium (not withdrawal)",
                "intervention": "Dexmedetomidine (alpha-2 agonist) — preferred over antipsychotics in mechanically ventilated patients (MENDS2 trial)",
                "notes": "Dexmedetomidine reduces delirium duration vs lorazepam in ICU. Consult critical care.",
            },
            {
                "indication": "Melatonin for sleep-wake cycle disruption",
                "intervention": "Melatonin 0.5–5 mg at bedtime (low-risk adjunct)",
                "notes": "May help with sleep-wake cycle normalization. Not proven to reduce delirium duration.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "QTc prolongation risk with haloperidol and other antipsychotics",
            "Fall prevention — bed alarms, low bed position",
            "Aspiration precautions",
            "Avoid physical restraints if possible (worsen delirium)",
        ],
        "monitoringParameters": monitoring,
        "multidisciplinaryConsult": mdt_consult,
        "references": [
            {"citation": "American Psychiatric Association. Practice Guideline for the Treatment of Patients with Delirium. 2025 (First update in >20 years)", "year": 2025},
            {"citation": "Inouye SK et al. NEJM 1999 (HELP protocol — Hospital Elder Life Program)", "year": 1999},
            {"citation": "Girard TD et al. NEJM 2018 (MIND-USA trial — haloperidol vs ziprasidone vs placebo in ICU delirium)", "year": 2018},
            {"citation": "Skrobik Y et al. Crit Care Med 2018 (MENDS2 — dexmedetomidine vs lorazepam)", "year": 2018},
        ],
        "guidelineYear": "2025",
        "practiceChangingNote": practice_changing_note,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BPD — APA 2025
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_bpd(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []

    if truthy(input.get("currentCrisis")):
        urgent.append("Acute suicidal/self-harm crisis — safety assessment and crisis plan required immediately")
    if truthy(input.get("polypharmacy")):
        safety.append("Polypharmacy (≥3 psychiatric medications) — APA 2025 recommends medication reduction; no medication is FDA-approved for BPD")

    first_line: list[str] = []
    pharmacotherapy = ""
    notes = ""
    practice_changing_note = "APA 2025 PRACTICE CHANGE: Psychotherapy is the primary treatment for BPD. Pharmacotherapy should be adjunctive only, targeting specific symptoms (not BPD itself). Avoid polypharmacy."

    prior_dbt = truthy(input.get("priorDBT"))
    prior_mbt = truthy(input.get("priorMBT"))

    if not prior_dbt and not prior_mbt:
        first_line = ["Dialectical Behavior Therapy (DBT) — first-line (strongest evidence)", "Mentalization-Based Therapy (MBT) — first-line alternative", "Transference-Focused Psychotherapy (TFP)", "Schema-Focused Therapy"]
        pharmacotherapy = "No medication is FDA-approved for BPD. Adjunctive pharmacotherapy only for specific comorbid symptoms (e.g., mood instability: low-dose mood stabilizer; impulsivity: low-dose antipsychotic). Avoid polypharmacy."
        notes = "APA 2025: Psychotherapy-first approach. DBT has the strongest evidence base. Pharmacotherapy is adjunctive and symptom-targeted, not disorder-targeted."
    elif prior_dbt and not prior_mbt:
        first_line = ["Continue/optimize DBT", "Consider MBT as alternative", "Transference-Focused Psychotherapy (TFP)", "Good Psychiatric Management (GPM)"]
        pharmacotherapy = "Review and minimize current medications. Target specific symptoms only."
        notes = "Prior DBT — consider MBT or TFP as alternatives. Medication review recommended to reduce polypharmacy."
    else:
        first_line = ["Optimize current evidence-based psychotherapy", "Consider step-up to intensive outpatient or partial hospitalization", "Peer support and skills groups"]
        pharmacotherapy = "Medication review and reduction if polypharmacy present. Consider consultation with BPD specialist."
        notes = "Prior DBT and MBT — consider higher level of care or specialist consultation."

    if truthy(input.get("comorbidMDD")):
        first_line.append("Treat comorbid MDD with SSRI/SNRI (standard MDD guidelines apply)")
    if truthy(input.get("substanceUse")):
        first_line.append("Integrated dual-diagnosis treatment for comorbid SUD")
        urgent.append("Comorbid substance use disorder — integrated treatment required")

    indication = "Borderline Personality Disorder"
    if truthy(input.get("currentCrisis")):
        indication += " — Acute Crisis"

    if truthy(input.get("currentCrisis")):
        level_of_care = "Crisis stabilization / brief inpatient if safety concern"
    elif prior_dbt and prior_mbt:
        level_of_care = "Intensive outpatient or partial hospitalization"
    else:
        level_of_care = "Outpatient structured psychotherapy"

    return {
        "condition": "bpd",
        "primaryRecommendation": {
            "indication": indication,
            "firstLineIntervention": first_line,
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": "DBT (first-line), MBT, TFP, or Schema Therapy — all evidence-based. Minimum 1 year of structured psychotherapy recommended.",
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "APA Practice Guideline for Borderline Personality Disorder 2025",
            "notes": notes,
        },
        "alternativeRecommendations": [
            {
                "indication": "Acute crisis / self-harm episode",
                "intervention": "Brief crisis stabilization (not prolonged hospitalization — may reinforce maladaptive patterns). Crisis safety plan. DBT crisis coaching.",
                "notes": "APA 2025: Avoid prolonged hospitalization for BPD crises unless immediate safety risk. Brief stabilization preferred.",
            },
            {
                "indication": "Comorbid bipolar disorder",
                "intervention": "Mood stabilizer (lithium, lamotrigine, or valproate) for bipolar component. Psychotherapy continues.",
                "notes": "Distinguish BPD mood instability from bipolar disorder — different treatment targets.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "Suicide risk is elevated in BPD — assess at every visit",
            "Non-suicidal self-injury (NSSI) requires safety planning, not automatic hospitalization",
            "Avoid benzodiazepines (high misuse potential in BPD)",
            "Therapeutic alliance is critical — rupture repair is part of treatment",
        ],
        "monitoringParameters": ["PHQ-9 for comorbid depression", "Columbia Suicide Severity Rating Scale (C-SSRS)", "Medication side effects if pharmacotherapy used", "Functional outcomes and quality of life"],
        "multidisciplinaryConsult": ["Psychotherapy specialist (DBT-trained therapist)", "Social work (housing, safety planning)", "Substance use treatment if SUD comorbid"],
        "references": [
            {"citation": "American Psychiatric Association. Practice Guideline for Borderline Personality Disorder. 2025", "year": 2025},
            {"citation": "Linehan MM et al. Arch Gen Psychiatry 1991 (Original DBT RCT)", "year": 1991},
            {"citation": "Bateman A, Fonagy P. Am J Psychiatry 1999 (MBT RCT)", "year": 1999},
            {"citation": "Cristea IA et al. JAMA Psychiatry 2017 (Meta-analysis of psychotherapies for BPD)", "year": 2017},
        ],
        "guidelineYear": "2025",
        "practiceChangingNote": practice_changing_note,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DEPRESSION — APA 2025-2026 UPDATE + TRD
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_depression(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []

    if truthy(input.get("suicidalIdeation")):
        urgent.append("Active suicidal ideation — safety assessment required; consider hospitalization")
    if truthy(input.get("bipolarHistory")):
        urgent.append("Bipolar history — antidepressant monotherapy may precipitate mania; mood stabilizer required")
        safety.append("Do NOT use antidepressant monotherapy in bipolar depression without mood stabilizer")
    if truthy(input.get("psychoticFeatures")):
        urgent.append("Psychotic depression — antidepressant + antipsychotic combination required; consider ECT")

    trials_failed = parse_float(input.get("trialsFailed"))
    severity = _str(input.get("severity"))

    first_line: list[str] = []
    pharmacotherapy = ""
    notes = ""
    practice_changing_note = ""

    if truthy(input.get("trd")) or trials_failed >= 2:
        first_line = [
            "Esketamine (SPRAVATO) intranasal — FDA-approved for TRD (2019) and MDD with acute SI (2020)",
            "Electroconvulsive Therapy (ECT) — most effective for severe/TRD/psychotic depression",
            "Augmentation: lithium + antidepressant (evidence-based)",
            "Augmentation: atypical antipsychotic (aripiprazole, quetiapine, brexpiprazole)",
            "Transcranial Magnetic Stimulation (TMS) — FDA-cleared for TRD",
            "MAOIs (phenelzine, tranylcypromine) — highly effective, require dietary restrictions",
        ]
        pharmacotherapy = f"TRD ({input.get('trialsFailed')} failed adequate trials): Esketamine (SPRAVATO) if eligible, or ECT for severe cases. Augmentation with lithium, atypical antipsychotic, or thyroid hormone. Consider MAOI if other strategies fail."
        notes = "APA 2025-2026 UPDATE: TRD pathway now includes esketamine as a first-line option after ≥2 failed trials. ECT remains the gold standard for severe TRD. Measurement-based care (PHQ-9 at every visit) is recommended."
        practice_changing_note = "APA 2025-2026 UPDATE: Esketamine (SPRAVATO) is now incorporated into the TRD pathway. Measurement-based care is a core recommendation."
    elif severity == "severe" or truthy(input.get("psychoticFeatures")):
        first_line = [
            "SSRI or SNRI (first-line pharmacotherapy)",
            "Psychotherapy (CBT or IPT) — combination with pharmacotherapy preferred for severe MDD",
            "ECT if psychotic features, catatonia, or severe suicidality",
        ]
        pharmacotherapy = (
            "Antidepressant + antipsychotic combination (e.g., sertraline + olanzapine). ECT preferred for psychotic depression."
            if truthy(input.get("psychoticFeatures"))
            else "SSRI (sertraline, escitalopram) or SNRI (venlafaxine, duloxetine). Combination with psychotherapy."
        )
        notes = "Severe MDD: combination of pharmacotherapy + psychotherapy is more effective than either alone. ECT for psychotic features."
    elif truthy(input.get("pregnancyOrPostpartum")):
        first_line = [
            "Psychotherapy (CBT, IPT) — preferred first-line for mild-moderate PPD",
            "SSRI (sertraline preferred — lowest breast milk transfer) for moderate-severe PPD",
            "Brexanolone (Zulresso) IV — FDA-approved for postpartum depression",
            "Zuranolone (Zurzuvae) oral — FDA-approved 2023 for PPD",
        ]
        pharmacotherapy = "Sertraline (preferred SSRI in pregnancy/lactation). Brexanolone or zuranolone for PPD. Avoid paroxetine in pregnancy (cardiac defects). Avoid benzodiazepines."
        notes = "Postpartum depression: brexanolone and zuranolone are FDA-approved specifically for PPD. Shared decision-making regarding breastfeeding and medication."
    else:
        first_line = [
            "SSRI (escitalopram, sertraline) — first-line",
            "SNRI (venlafaxine, duloxetine) — first-line alternative",
            "Psychotherapy (CBT, IPT, behavioral activation) — equivalent to medication for mild-moderate MDD",
            "Combination therapy for moderate-severe MDD",
        ]
        pharmacotherapy = "SSRI (escitalopram 10–20 mg or sertraline 50–200 mg) or SNRI. Adequate trial = 4–8 weeks at therapeutic dose. Reassess at 4 weeks."
        notes = "Mild-moderate MDD: psychotherapy alone is equivalent to medication. Combination preferred for moderate-severe. Measurement-based care (PHQ-9 at every visit) recommended by APA 2025-2026."

    if truthy(input.get("measurementBasedCare")):
        notes += " Measurement-based care (PHQ-9 at every visit) is being used — this is a core APA 2025-2026 recommendation."

    indication = f"Major Depressive Disorder — {severity or 'unspecified severity'}"
    if truthy(input.get("trd")):
        indication += " (Treatment-Resistant)"
    if truthy(input.get("pregnancyOrPostpartum")):
        indication += " (Perinatal)"

    if truthy(input.get("suicidalIdeation")):
        level_of_care = "Inpatient or crisis stabilization"
    elif truthy(input.get("trd")) or severity == "severe":
        level_of_care = "Outpatient with close follow-up (2–4 weeks) or partial hospitalization"
    else:
        level_of_care = "Outpatient"

    psychotherapy = (
        "CBT, IPT, or behavioral activation as adjunct to pharmacotherapy/ECT/TMS"
        if truthy(input.get("trd"))
        else "CBT or IPT — equivalent to medication for mild-moderate MDD; combination preferred for severe MDD"
    )

    return {
        "condition": "depression",
        "primaryRecommendation": {
            "indication": indication,
            "firstLineIntervention": first_line,
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": psychotherapy,
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "APA Practice Guideline for Major Depressive Disorder 2025-2026 Update",
            "notes": notes,
        },
        "alternativeRecommendations": [
            {
                "indication": "Inadequate response after 4–8 weeks",
                "intervention": "Optimize dose → switch within class → augment (lithium, atypical antipsychotic, buspirone) → switch class → TRD pathway",
                "notes": "Sequential treatment algorithm. Reassess diagnosis before declaring TRD.",
            },
            {
                "indication": "Seasonal affective disorder (SAD)",
                "intervention": "Light therapy (10,000 lux, 30 min morning) ± bupropion XL (FDA-approved for SAD prevention)",
                "notes": "Light therapy is first-line for SAD. Bupropion XL started in fall for prevention.",
            },
            {
                "indication": "Anxious depression",
                "intervention": "SSRI/SNRI + buspirone or low-dose benzodiazepine (short-term). Avoid benzodiazepine long-term.",
                "notes": "Anxious depression may respond better to SNRI than SSRI.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "Black box warning: increased suicidality in children/adolescents/young adults on antidepressants — monitor closely",
            "SSRI discontinuation syndrome — taper gradually",
            "Serotonin syndrome risk with combination serotonergic agents",
            "QTc prolongation with citalopram >40 mg/day",
            "Esketamine (SPRAVATO): REMS program required; monitor for dissociation and BP for 2 hours post-dose",
        ],
        "monitoringParameters": ["PHQ-9 at every visit (measurement-based care)", "Columbia C-SSRS for suicidality", "Side effect assessment at 2 and 4 weeks", "Metabolic monitoring if atypical antipsychotic augmentation"],
        "multidisciplinaryConsult": ["Psychotherapy (CBT/IPT therapist)", "ECT service if severe/TRD/psychotic", "Reproductive psychiatry if perinatal"],
        "references": [
            {"citation": "American Psychiatric Association. Practice Guideline for Major Depressive Disorder. 2025-2026 Update", "year": 2025},
            {"citation": "Papakostas GI et al. NEJM 2020 (Esketamine for TRD — TRANSFORM trials)", "year": 2020},
            {"citation": "UK ECT Review Group. Lancet 2003 (ECT meta-analysis)", "year": 2003},
            {"citation": "Brexanolone FDA approval 2019 (Zulresso for PPD)", "year": 2019},
            {"citation": "Zuranolone FDA approval 2023 (Zurzuvae for MDD and PPD)", "year": 2023},
        ],
        "guidelineYear": "2025-2026",
        "practiceChangingNote": practice_changing_note,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SCHIZOPHRENIA — APA 2020 (STILL DOMINANT)
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_schizophrenia(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []

    treatment_resistant = truthy(input.get("treatmentResistant"))
    clozapine_eligible = truthy(input.get("clozapineEligible"))
    first_episode = truthy(input.get("firstEpisode"))
    current_antipsychotic = _str(input.get("currentAntipsychotic"))

    if truthy(input.get("acuteExacerbation")):
        urgent.append("Acute psychotic exacerbation — assess safety, consider inpatient stabilization")
    if treatment_resistant and not clozapine_eligible:
        urgent.append("Treatment-resistant schizophrenia — clozapine evaluation required (failed ≥2 adequate antipsychotic trials)")
    if truthy(input.get("tardiveDyskinesia")):
        safety.append("Tardive dyskinesia present — consider VMAT2 inhibitor (valbenazine or deutetrabenazine); review antipsychotic necessity")

    first_line: list[str] = []
    pharmacotherapy = ""
    notes = ""

    if treatment_resistant and clozapine_eligible:
        first_line = ["Clozapine — only antipsychotic with evidence for treatment-resistant schizophrenia", "Psychosocial rehabilitation", "Assertive Community Treatment (ACT) if available"]
        pharmacotherapy = "Clozapine (titrate to 300–450 mg/day; target trough 350–600 ng/mL). Requires REMS enrollment (ANC monitoring). Most effective antipsychotic for TRS."
        notes = "APA 2020: Clozapine is the only evidence-based treatment for treatment-resistant schizophrenia. Underutilized in practice. REMS monitoring required (ANC weekly × 6 months, then biweekly × 6 months, then monthly)."
    elif first_episode:
        first_line = ["Second-generation antipsychotic (SGA) — first-line for first-episode psychosis", "Coordinated Specialty Care (CSC) program", "Family psychoeducation", "Cognitive Behavioral Therapy for Psychosis (CBTp)"]
        pharmacotherapy = "SGA: aripiprazole, risperidone, olanzapine, or quetiapine. Start low, titrate slowly. First-episode patients often respond to lower doses."
        notes = "First-episode psychosis: Coordinated Specialty Care (CSC) programs (e.g., NAVIGATE, OnTrackNY) significantly improve outcomes. Early intervention is critical."
    elif truthy(input.get("nonadherence")) or truthy(input.get("laiCandidate")):
        first_line = ["Long-Acting Injectable (LAI) antipsychotic — strongly preferred for nonadherence", "Motivational interviewing for medication adherence", "Assertive Community Treatment (ACT)"]
        _lai_suffix = f"Current oral: {current_antipsychotic} — consider LAI equivalent." if current_antipsychotic else ""
        pharmacotherapy = f"LAI options: aripiprazole lauroxil (Aristada), paliperidone palmitate (Invega Sustenna/Trinza), risperidone LAI (Risperdal Consta), haloperidol decanoate. {_lai_suffix}"
        notes = "LAI antipsychotics reduce relapse rates by 30–50% vs oral in nonadherent patients. APA 2020 strongly recommends LAI discussion with all patients."
    else:
        _maint = f"Continue {current_antipsychotic} at therapeutic dose. " if current_antipsychotic else "SGA: aripiprazole, risperidone, olanzapine, quetiapine, or lurasidone. "
        first_line = ["Second-generation antipsychotic (SGA) — continue/optimize", "Psychosocial interventions (CBTp, social skills training, supported employment)", "Family psychoeducation"]
        pharmacotherapy = f"{_maint}Assess response at 4–6 weeks. Consider LAI if adherence concern."
        notes = "Maintenance antipsychotic therapy is essential for relapse prevention. Psychosocial interventions are additive to pharmacotherapy."

    if truthy(input.get("metabolicConcerns")):
        safety.append("Metabolic monitoring required: weight, BMI, fasting glucose, lipids, BP at baseline and every 3 months")
        first_line.append("Consider metabolically neutral antipsychotic (aripiprazole, lurasidone, ziprasidone) if metabolic concerns")

    indication = "Schizophrenia"
    if first_episode:
        indication += " — First Episode"
    if treatment_resistant:
        indication += " — Treatment-Resistant"
    if truthy(input.get("acuteExacerbation")):
        indication += " — Acute Exacerbation"

    if truthy(input.get("acuteExacerbation")):
        level_of_care = "Inpatient stabilization"
    elif treatment_resistant:
        level_of_care = "Intensive outpatient or ACT"
    else:
        level_of_care = "Outpatient with regular follow-up"

    return {
        "condition": "schizophrenia",
        "primaryRecommendation": {
            "indication": indication,
            "firstLineIntervention": first_line,
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": "Cognitive Behavioral Therapy for Psychosis (CBTp), social skills training, supported employment (IPS), family psychoeducation — all evidence-based adjuncts",
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "APA Practice Guideline for Schizophrenia 2020 (current standard 2026)",
            "notes": notes,
        },
        "alternativeRecommendations": [
            {
                "indication": "Clozapine-refractory schizophrenia",
                "intervention": "Clozapine + amisulpride augmentation (CATIE-like strategy). ECT augmentation for refractory cases.",
                "notes": "Limited evidence for clozapine augmentation. Specialist consultation recommended.",
            },
            {
                "indication": "Tardive dyskinesia",
                "intervention": "Valbenazine (Ingrezza) or deutetrabenazine (Austedo) — FDA-approved VMAT2 inhibitors for TD",
                "notes": "Do not abruptly discontinue antipsychotic (may worsen TD). VMAT2 inhibitors are first-line for TD.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "Clozapine: agranulocytosis risk — mandatory ANC monitoring (REMS)",
            "Clozapine: seizure risk at high doses (>600 mg/day)",
            "Neuroleptic Malignant Syndrome (NMS) — rare but life-threatening",
            "QTc prolongation with ziprasidone, haloperidol, and thioridazine",
        ],
        "monitoringParameters": ["PANSS or BPRS for symptom severity", "Metabolic panel (weight, BMI, glucose, lipids, BP) at baseline and q3 months", "ANC monitoring if clozapine", "AIMS for tardive dyskinesia q6 months", "Medication adherence assessment"],
        "multidisciplinaryConsult": ["Coordinated Specialty Care (CSC) team for first episode", "Assertive Community Treatment (ACT) for high-risk patients", "Vocational rehabilitation (IPS)", "Social work for housing and benefits"],
        "references": [
            {"citation": "American Psychiatric Association. Practice Guideline for Schizophrenia. 2020", "year": 2020},
            {"citation": "Kane JM et al. Arch Gen Psychiatry 1988 (Clozapine for TRS — landmark trial)", "year": 1988},
            {"citation": "Leucht S et al. Lancet 2013 (Antipsychotic meta-analysis — 212 trials)", "year": 2013},
            {"citation": "Kishimoto T et al. Schizophr Bull 2018 (LAI vs oral meta-analysis)", "year": 2018},
        ],
        "guidelineYear": "2020 (current standard 2026)",
    }


# ─────────────────────────────────────────────────────────────────────────────
# EATING DISORDERS — APA 2023
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_eating_disorder(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []

    ed_type = _str(input.get("edType"))
    age = parse_float(input.get("age"))
    bmi = parse_float(input.get("bmi"))
    pediatric = truthy(input.get("pediatric"))

    if truthy(input.get("medicallyUnstable")):
        urgent.append("Medically unstable — inpatient medical stabilization required before psychiatric treatment")
    if ed_type == "AN" and bmi < 15:
        urgent.append("Severe anorexia nervosa (BMI <15) — high mortality risk; consider inpatient or residential treatment")
    if ed_type == "AN" and bmi < 17.5:
        safety.append("Refeeding syndrome risk — medical monitoring required during nutritional rehabilitation")

    first_line: list[str] = []
    pharmacotherapy = ""
    notes = ""

    if ed_type == "AN":
        if pediatric or age < 18:
            first_line = ["Family-Based Treatment (FBT/Maudsley) — first-line for adolescent AN (strongest evidence)", "Nutritional rehabilitation (supervised refeeding)", "Medical monitoring (vitals, ECG, labs)"]
            pharmacotherapy = "No medication is FDA-approved for AN. Olanzapine may be used adjunctively for weight gain and anxiety (limited evidence). Avoid SSRIs in underweight AN (ineffective)."
            notes = "APA 2023: FBT (Maudsley approach) is the most evidence-based treatment for adolescent AN. Nutritional rehabilitation is the primary intervention."
        else:
            first_line = ["Cognitive Behavioral Therapy for Eating Disorders (CBT-E)", "Specialist Supportive Clinical Management (SSCM)", "Nutritional rehabilitation with dietitian", "Higher level of care (IOP, residential, inpatient) based on BMI and medical stability"]
            pharmacotherapy = "No FDA-approved medication for AN. Olanzapine (2.5–10 mg) may support weight restoration in adults. Avoid SSRIs in underweight patients."
            notes = "Adult AN: CBT-E and SSCM have the best evidence. Higher level of care is often required. Medical monitoring essential during refeeding."
    elif ed_type == "BN":
        first_line = ["Cognitive Behavioral Therapy for Bulimia (CBT-BN) — first-line (strongest evidence)", "Interpersonal Therapy (IPT) — alternative", "Nutritional counseling"]
        pharmacotherapy = "Fluoxetine 60 mg/day — only FDA-approved medication for BN (Category 1). Higher dose than for MDD. Avoid bupropion (seizure risk in BN)."
        notes = "APA 2023: CBT-BN is the most effective treatment for bulimia. Fluoxetine 60 mg is FDA-approved and additive to CBT. Avoid bupropion (lowers seizure threshold in purging behavior)."
    elif ed_type == "BED":
        first_line = ["Cognitive Behavioral Therapy for BED (CBT-BED) — first-line", "Dialectical Behavior Therapy (DBT) — alternative", "Interpersonal Therapy (IPT)"]
        pharmacotherapy = "Lisdexamfetamine (Vyvanse) 50–70 mg — only FDA-approved medication for moderate-severe BED. SSRIs (sertraline, fluoxetine) as second-line. Topiramate (weight loss + binge reduction, but cognitive side effects)."
        notes = "APA 2023: CBT-BED is first-line. Lisdexamfetamine is FDA-approved for BED — assess for stimulant misuse history before prescribing."
    else:
        first_line = ["Multidisciplinary assessment", "Nutritional rehabilitation", "CBT or FBT based on age and presentation"]
        pharmacotherapy = "No FDA-approved medication for ARFID. Address comorbid anxiety/OCD if present."
        notes = "ARFID: emerging evidence base. Multidisciplinary approach with dietitian, psychologist, and occupational therapy."

    if truthy(input.get("comorbidMDD")):
        first_line.append("Treat comorbid MDD (SSRI after weight restoration in AN; fluoxetine preferred in BN/BED)")

    indication = f"{ed_type or 'Eating Disorder'} — {'Pediatric/Adolescent' if pediatric else 'Adult'}"
    if truthy(input.get("medicallyUnstable")):
        indication += " (Medically Unstable)"

    if ed_type == "AN":
        psychotherapy = "FBT (Maudsley) — first-line for adolescents" if pediatric else "CBT-E or SSCM"
    elif ed_type == "BN":
        psychotherapy = "CBT-BN — first-line"
    else:
        psychotherapy = "CBT-BED — first-line"

    if truthy(input.get("medicallyUnstable")):
        level_of_care = "Inpatient medical"
    elif ed_type == "AN" and bmi < 15:
        level_of_care = "Inpatient psychiatric/residential"
    elif truthy(input.get("priorIOP")):
        level_of_care = "Residential or higher level of care"
    else:
        level_of_care = "Outpatient or IOP"

    return {
        "condition": "eating_disorder",
        "primaryRecommendation": {
            "indication": indication,
            "firstLineIntervention": first_line,
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": psychotherapy,
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "APA Practice Guideline for Eating Disorders 2023",
            "notes": notes,
        },
        "alternativeRecommendations": [
            {
                "indication": "AN with severe medical compromise",
                "intervention": "Inpatient medical stabilization → residential eating disorder program → step-down to IOP/outpatient",
                "notes": "Stepped-care model. Medical clearance before psychiatric treatment.",
            },
            {
                "indication": "BN/BED with comorbid obesity",
                "intervention": "Integrated treatment addressing both ED and weight management. Avoid weight-focused interventions that may worsen ED.",
                "notes": "Weight management should not be primary focus during active ED treatment.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "Cardiac monitoring (QTc, bradycardia) in AN",
            "Electrolyte monitoring (hypokalemia in BN/purging)",
            "Bone density monitoring in chronic AN",
            "Avoid bupropion in BN (seizure risk with purging behavior)",
        ],
        "monitoringParameters": ["Weight and BMI weekly during refeeding", "Electrolytes (K, Mg, Phos) during refeeding", "ECG in AN (QTc, bradycardia)", "EDE-Q (Eating Disorder Examination Questionnaire) for symptom monitoring"],
        "multidisciplinaryConsult": ["Registered Dietitian (nutritional rehabilitation)", "Medical internist/pediatrician (medical monitoring)", "Family therapy (especially for adolescents)", "Occupational therapy for ARFID"],
        "references": [
            {"citation": "American Psychiatric Association. Practice Guideline for Eating Disorders. 2023", "year": 2023},
            {"citation": "Lock J et al. Arch Gen Psychiatry 2010 (FBT vs individual therapy for adolescent AN)", "year": 2010},
            {"citation": "Fairburn CG et al. Arch Gen Psychiatry 1993 (CBT-BN landmark trial)", "year": 1993},
            {"citation": "McElroy SL et al. NEJM 2003 (Topiramate for BED)", "year": 2003},
        ],
        "guidelineYear": "2023",
    }


# ─────────────────────────────────────────────────────────────────────────────
# BENZODIAZEPINE TAPERING — 2025 JOINT GUIDELINE
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_benzo_tapering(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []

    seizure_history = truthy(input.get("seizureHistory"))
    withdrawal_history = truthy(input.get("withdrawalHistory"))
    duration_years = parse_float(input.get("durationYears"))
    benzo_name = _str(input.get("benzoName"))
    daily_dose_mg = input.get("dailyDoseMg")

    if seizure_history or withdrawal_history:
        urgent.append("Prior seizure or withdrawal history — medically supervised taper required; consider inpatient or residential detox")
    if not truthy(input.get("patientMotivated")):
        safety.append("Patient not motivated for taper — motivational interviewing recommended before initiating taper")

    if duration_years > 5:
        taper_rate = "Very slow taper: 5–10% dose reduction every 2–4 weeks (Ashton protocol). Total duration may be 1–2+ years."
    elif duration_years > 1:
        taper_rate = "Slow taper: 10% dose reduction every 1–2 weeks. Total duration typically 3–12 months."
    else:
        taper_rate = "Standard taper: 10–25% dose reduction every 1–2 weeks. Total duration typically 4–8 weeks."

    diazepam_conversion = ""
    benzo_lower = benzo_name.lower()
    if "alprazolam" in benzo_lower or "xanax" in benzo_lower:
        diazepam_conversion = "Alprazolam → diazepam equivalent: 0.5 mg alprazolam ≈ 10 mg diazepam. Consider switching to diazepam for smoother taper (longer half-life)."
    elif "lorazepam" in benzo_lower or "ativan" in benzo_lower:
        diazepam_conversion = "Lorazepam → diazepam equivalent: 1 mg lorazepam ≈ 10 mg diazepam. Consider switching to diazepam for smoother taper."
    elif "clonazepam" in benzo_lower or "klonopin" in benzo_lower:
        diazepam_conversion = "Clonazepam → diazepam equivalent: 0.5 mg clonazepam ≈ 10 mg diazepam. Clonazepam has longer half-life — may taper directly."

    # JS template: `${input.durationYears} year${input.durationYears !== 1 ? "s" : ""}`
    # durationYears is the raw submitted value; pluralize unless it equals 1.
    dur_display = input.get("durationYears")
    plural = "" if duration_years == 1 else "s"

    first_line = [
        x for x in [
            "Gradual, individualized taper — NEVER abrupt discontinuation",
            diazepam_conversion or "Consider switching to longer-acting benzodiazepine (diazepam) for smoother taper",
            taper_rate,
            "Cognitive Behavioral Therapy for Insomnia (CBT-I) if insomnia is the indication",
            "CBT for anxiety if anxiety is the indication",
            "Patient education on withdrawal symptoms and expected timeline",
        ]
        if truthy(x)
    ]

    if seizure_history or withdrawal_history:
        level_of_care = "Inpatient or residential medical detox"
    elif truthy(input.get("substanceUseDisorder")):
        level_of_care = "Intensive outpatient with addiction medicine"
    else:
        level_of_care = "Outpatient with close monitoring"

    return {
        "condition": "benzo_tapering",
        "primaryRecommendation": {
            "indication": f"Benzodiazepine Tapering — {benzo_name or 'unspecified benzo'} ({dur_display} year{plural} of use, {daily_dose_mg} mg/day)",
            "firstLineIntervention": first_line,
            "pharmacotherapy": f"{taper_rate} {diazepam_conversion} Adjuncts: carbamazepine or valproate may reduce withdrawal severity. Propranolol for autonomic symptoms. Melatonin for sleep.",
            "psychotherapy": "CBT-I (insomnia), CBT for anxiety, or mindfulness-based stress reduction — address the underlying indication for benzodiazepine use",
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "Benzodiazepine Tapering Guideline 2025 (Joint APA/ASAM/AAFP)",
            "notes": "2025 GUIDELINE: Gradual, individualized tapering is the standard of care. Abrupt discontinuation is dangerous and contraindicated. Patient motivation and shared decision-making are essential. Address the underlying indication with non-pharmacologic therapy.",
        },
        "alternativeRecommendations": [
            {
                "indication": "Severe withdrawal or seizure risk",
                "intervention": "Inpatient medical detox with phenobarbital or diazepam taper under medical supervision",
                "notes": "CIWA-B scale for monitoring withdrawal severity.",
            },
            {
                "indication": "Comorbid opioid use disorder",
                "intervention": "Buprenorphine/naloxone (Suboxone) for opioid component; separate benzo taper with addiction medicine",
                "notes": "Concurrent benzo + opioid use significantly increases overdose risk.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "NEVER abruptly discontinue benzodiazepines — risk of life-threatening seizures",
            "Withdrawal symptoms: anxiety, insomnia, tremor, sweating, seizures (severe cases)",
            "CIWA-B scale for monitoring withdrawal severity",
            "Avoid driving during taper (sedation, cognitive impairment)",
            "Increased fall risk in elderly during taper",
        ],
        "monitoringParameters": ["CIWA-B (Clinical Institute Withdrawal Assessment for Benzodiazepines) weekly", "Vital signs during taper", "Sleep diary and anxiety scales", "Urine drug screen to confirm compliance"],
        "multidisciplinaryConsult": ["Addiction medicine (if SUD comorbid)", "Primary care physician (medical monitoring)", "CBT therapist (for underlying anxiety/insomnia)"],
        "references": [
            {"citation": "Ashton H. J Psychiatr Res 2005 (Ashton Manual — benzodiazepine tapering protocol)", "year": 2005},
            {"citation": "Benzodiazepine Tapering Guideline 2025 (Joint APA/ASAM/AAFP)", "year": 2025},
            {"citation": "Morin CM et al. JAMA 2009 (CBT-I for insomnia — reduces benzo use)", "year": 2009},
        ],
        "guidelineYear": "2025",
        "practiceChangingNote": "2025 JOINT GUIDELINE: Emphasizes gradual, individualized tapering and avoidance of abrupt discontinuation. Non-pharmacologic treatment of the underlying indication is essential.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# PTSD — VA/DoD 2023 + APA
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_ptsd(input: dict) -> dict:
    urgent: list[str] = []

    prior_pe = truthy(input.get("priorPE"))
    prior_cpt = truthy(input.get("priorCPT"))
    prior_emdr = truthy(input.get("priorEMDR"))
    current_medication = _str(input.get("currentMedication"))
    severity = _str(input.get("severity"))
    trauma_type = _str(input.get("traumaType"))

    if truthy(input.get("suicidalIdeation")):
        urgent.append("Active suicidal ideation — safety assessment required; consider hospitalization")
    if truthy(input.get("comorbidSUD")):
        urgent.append("Comorbid substance use disorder — integrated dual-diagnosis treatment required")

    first_line: list[str] = []
    pharmacotherapy = ""
    notes = ""

    if not prior_pe and not prior_cpt and not prior_emdr:
        first_line = [
            "Prolonged Exposure (PE) — first-line (VA/DoD 2023, Strong recommendation)",
            "Cognitive Processing Therapy (CPT) — first-line (VA/DoD 2023, Strong recommendation)",
            "EMDR (Eye Movement Desensitization and Reprocessing) — first-line (VA/DoD 2023)",
            "Written Exposure Therapy (WET) — first-line alternative (shorter protocol)",
        ]
        pharmacotherapy = "Sertraline or paroxetine (only FDA-approved medications for PTSD). Venlafaxine as alternative. Pharmacotherapy is adjunctive to trauma-focused psychotherapy, not a substitute."
        notes = "VA/DoD 2023: Trauma-focused psychotherapy (PE, CPT, EMDR) is strongly recommended as first-line. Pharmacotherapy alone is less effective than psychotherapy for PTSD."
    else:
        tried_therapies = ", ".join(
            x for x in [prior_pe and "PE", prior_cpt and "CPT", prior_emdr and "EMDR"] if truthy(x)
        )
        first_line = [
            f"Prior therapies: {tried_therapies} — consider alternative trauma-focused therapy",
            "Cognitive Behavioral Therapy (CBT) — alternative",
            "Narrative Exposure Therapy (NET) — especially for refugee/complex trauma",
            "Intensive outpatient PTSD program",
        ]
        _med_prefix = f"Current: {current_medication}. " if current_medication else ""
        pharmacotherapy = f"{_med_prefix}Consider sertraline, paroxetine, or venlafaxine if not already tried. Prazosin for nightmares (VA/DoD 2023 — conditional recommendation)."
        notes = "Prior trauma-focused therapy — consider alternative evidence-based therapy or intensive program. Prazosin may help with PTSD nightmares."

    if truthy(input.get("dissociativeSubtype")):
        first_line.insert(0, "Phase-based treatment — stabilization before trauma processing (for dissociative subtype)")
        notes += " Dissociative subtype: phase-based approach recommended. Stabilization and grounding skills before trauma-focused therapy."

    if truthy(input.get("militaryVeteran")):
        first_line.append("VA PTSD specialty clinic referral if available")
        notes += " Military veteran: VA PTSD specialty care is available and recommended."

    indication = f"PTSD — {severity or 'unspecified severity'}"
    if trauma_type:
        indication += f" ({trauma_type.replace('_', ' ')})"
    if truthy(input.get("militaryVeteran")):
        indication += " (Military Veteran)"

    if truthy(input.get("suicidalIdeation")):
        level_of_care = "Inpatient or crisis stabilization"
    elif truthy(input.get("comorbidSUD")):
        level_of_care = "Integrated dual-diagnosis outpatient"
    else:
        level_of_care = "Outpatient specialty PTSD care"

    return {
        "condition": "ptsd",
        "primaryRecommendation": {
            "indication": indication,
            "firstLineIntervention": first_line,
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": "PE, CPT, or EMDR — all strongly recommended by VA/DoD 2023 and APA. Trauma-focused psychotherapy is the most effective treatment for PTSD.",
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "VA/DoD Clinical Practice Guideline for PTSD 2023 + APA Practice Guideline",
            "notes": notes,
        },
        "alternativeRecommendations": [
            {
                "indication": "PTSD with prominent nightmares",
                "intervention": "Prazosin 1–15 mg at bedtime (VA/DoD 2023 conditional recommendation for nightmares)",
                "notes": "Prazosin reduces trauma-related nightmares. Start low (1 mg), titrate slowly. Monitor for orthostatic hypotension.",
            },
            {
                "indication": "Complex PTSD / childhood trauma",
                "intervention": "Phase-based treatment: Phase 1 (stabilization/safety) → Phase 2 (trauma processing) → Phase 3 (integration). EMDR or CPT for trauma phase.",
                "notes": "Complex PTSD may require longer treatment and stabilization phase before trauma processing.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            "Suicide risk is elevated in PTSD — assess at every visit (C-SSRS)",
            "Avoid benzodiazepines for PTSD (VA/DoD 2023 — not recommended; may worsen outcomes)",
            "Trauma processing may temporarily increase distress — psychoeducation essential",
            "Means restriction counseling if suicidal ideation present",
        ],
        "monitoringParameters": ["PCL-5 (PTSD Checklist) at baseline and every 4 weeks", "Columbia C-SSRS for suicidality", "PHQ-9 for comorbid depression", "Alcohol Use Disorders Identification Test (AUDIT) if SUD comorbid"],
        "multidisciplinaryConsult": ["Trauma-focused psychotherapist (PE/CPT/EMDR trained)", "VA PTSD specialty clinic (if veteran)", "Substance use treatment (if SUD comorbid)", "Social work (safety planning, housing)"],
        "references": [
            {"citation": "VA/DoD Clinical Practice Guideline for PTSD. 2023", "year": 2023},
            {"citation": "Foa EB et al. JAMA 2007 (Prolonged Exposure for PTSD)", "year": 2007},
            {"citation": "Resick PA et al. J Consult Clin Psychol 2002 (CPT for PTSD)", "year": 2002},
            {"citation": "Shapiro F. J Traumatic Stress 1989 (EMDR original study)", "year": 1989},
            {"citation": "Raskind MA et al. NEJM 2018 (Prazosin for PTSD nightmares — MIRECC trial)", "year": 2018},
        ],
        "guidelineYear": "2023",
    }


# ─────────────────────────────────────────────────────────────────────────────
# SUICIDE RISK — VA/DoD 2019 + ZERO SUICIDE FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_suicide_risk(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []

    current_si = truthy(input.get("currentSI"))
    plan = truthy(input.get("plan"))
    means = truthy(input.get("means"))
    intent = truthy(input.get("intent"))
    prior_attempt = truthy(input.get("priorAttempt"))
    hopelessness = truthy(input.get("hopelessness"))
    protective_factors = truthy(input.get("protectiveFactors"))
    comorbid_mdd = truthy(input.get("comorbidMDD"))

    risk_level = "Low"
    risk_score = 0
    if current_si:
        risk_score += 3
    if plan:
        risk_score += 3
    if means:
        risk_score += 3
    if intent:
        risk_score += 3
    if prior_attempt:
        risk_score += 2
    if hopelessness:
        risk_score += 2
    if truthy(input.get("socialIsolation")):
        risk_score += 1
    if truthy(input.get("substanceUse")):
        risk_score += 1
    if truthy(input.get("recentLoss")):
        risk_score += 1
    if comorbid_mdd:
        risk_score += 1
    if truthy(input.get("comorbidBPD")):
        risk_score += 1
    if protective_factors:
        risk_score -= 2

    if risk_score >= 9 or (plan and means and intent):
        risk_level = "Imminent/High"
        urgent.append("IMMINENT SUICIDE RISK — Emergency psychiatric evaluation required. Consider involuntary hospitalization if patient refuses.")
        urgent.append("Means restriction: remove/secure firearms, medications, and other lethal means immediately")
    elif risk_score >= 5 or plan or prior_attempt:
        risk_level = "High"
        urgent.append("HIGH SUICIDE RISK — Urgent psychiatric evaluation within 24 hours. Safety planning required.")
        safety.append("Means restriction counseling — discuss with patient and family")
    elif risk_score >= 2 or current_si:
        risk_level = "Moderate"
        safety.append("Safety planning required. Follow-up within 1 week.")

    protective_line = "Strengthen protective factors (family support, reasons for living)" if protective_factors else "Identify and build protective factors"

    key_factors = ", ".join(
        x for x in [
            current_si and "current SI",
            plan and "plan",
            means and "means access",
            intent and "intent",
            prior_attempt and "prior attempt",
            hopelessness and "hopelessness",
        ]
        if truthy(x)
    ) or "none identified"

    if risk_level == "Imminent/High":
        level_of_care = "Emergency psychiatric evaluation / inpatient hospitalization"
    elif risk_level == "High":
        level_of_care = "Urgent outpatient evaluation or crisis stabilization unit"
    else:
        level_of_care = "Outpatient with safety plan and close follow-up"

    pharmacotherapy = f"Treat underlying disorder. Lithium has the strongest evidence for suicide prevention in mood disorders. Clozapine for suicidality in schizophrenia. Ketamine/esketamine for acute SI in MDD. {'Antidepressant for MDD component.' if comorbid_mdd else ''}"

    return {
        "condition": "suicide_risk",
        "primaryRecommendation": {
            "indication": f"Suicide Risk Assessment — {risk_level} Risk",
            "firstLineIntervention": [
                f"Risk Level: {risk_level}",
                "Safety Planning Intervention (Stanley-Brown Safety Planning) — evidence-based",
                "Means restriction counseling (especially firearms — most lethal method)",
                "Crisis resources: 988 Suicide & Crisis Lifeline, Crisis Text Line (text HOME to 741741)",
                "Follow-up contact within 24–72 hours (high risk) or 1 week (moderate risk)",
                protective_line,
                "Treat underlying psychiatric disorder (MDD, BPD, PTSD, SUD)",
            ],
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": "Dialectical Behavior Therapy (DBT) — strongest evidence for reducing suicidal behavior. Cognitive Behavioral Therapy for Suicide Prevention (CBT-SP). Safety Planning Intervention.",
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "VA/DoD Clinical Practice Guideline for Assessment and Management of Patients at Risk for Suicide 2019 + Zero Suicide Framework",
            "notes": f"Risk score: {risk_score}. Risk level: {risk_level}. Key risk factors present: {key_factors}.",
        },
        "alternativeRecommendations": [
            {
                "indication": "Acute suicidal crisis with MDD",
                "intervention": "Esketamine (SPRAVATO) — FDA-approved for MDD with acute suicidal ideation. Rapid onset (hours). Requires REMS monitoring.",
                "notes": "Esketamine provides rapid reduction in suicidal ideation. Does not replace safety planning or hospitalization if needed.",
            },
            {
                "indication": "Chronic suicidality in BPD",
                "intervention": "DBT — reduces suicidal behavior by 50% vs treatment as usual. Minimum 1 year of treatment.",
                "notes": "DBT is the most evidence-based treatment for chronic suicidality in BPD.",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "Document risk assessment, safety plan, and clinical reasoning at every visit",
            "Firearms are the most lethal method — means restriction counseling is essential",
            "Involuntary hospitalization criteria: imminent danger to self or others",
            "Warm handoff to emergency services if patient refuses care and is at imminent risk",
        ],
        "monitoringParameters": ["Columbia C-SSRS at every visit", "PHQ-9 item 9 (suicidal ideation)", "Safety plan review at every visit", "Means restriction follow-up"],
        "multidisciplinaryConsult": ["Emergency psychiatry (if imminent risk)", "Social work (safety planning, means restriction, housing)", "Primary care (means restriction — medication quantities)", "Family/support system involvement"],
        "references": [
            {"citation": "VA/DoD Clinical Practice Guideline for Assessment and Management of Patients at Risk for Suicide. 2019", "year": 2019},
            {"citation": "Stanley B, Brown GK. Cogn Behav Pract 2012 (Safety Planning Intervention)", "year": 2012},
            {"citation": "Linehan MM et al. Arch Gen Psychiatry 2006 (DBT for suicidal BPD)", "year": 2006},
            {"citation": "Cipriani A et al. BMJ 2013 (Lithium for suicide prevention — meta-analysis)", "year": 2013},
        ],
        "guidelineYear": "2019 (current standard 2026)",
    }


# ─────────────────────────────────────────────────────────────────────────────
# BIPOLAR DISORDER — APA + CANMAT 2023
# ─────────────────────────────────────────────────────────────────────────────


def _evaluate_bipolar(input: dict) -> dict:
    urgent: list[str] = []
    safety: list[str] = []

    current_phase = _str(input.get("currentPhase"))
    severity = _str(input.get("severity"))
    bipolar_type = _str(input.get("bipolarType"))
    psychotic_features = truthy(input.get("psychoticFeatures"))
    rapid_cycling = truthy(input.get("rapidCycling"))
    lithium_tried = truthy(input.get("lithiumTried"))
    suicidal_ideation = truthy(input.get("suicidalIdeation"))

    if suicidal_ideation:
        urgent.append("Active suicidal ideation — safety assessment required")
    if current_phase == "manic" and severity == "severe":
        urgent.append("Severe mania — consider inpatient stabilization; remove access to finances, vehicles, and other high-risk activities")
    if truthy(input.get("pregnancyOrPostpartum")):
        safety.append("Pregnancy/postpartum: avoid valproate (teratogenic — Category X). Lithium requires careful monitoring. Consult reproductive psychiatry.")
        urgent.append("Pregnancy with bipolar disorder — reproductive psychiatry consultation required")

    first_line: list[str] = []
    pharmacotherapy = ""
    notes = ""

    if current_phase == "manic" or current_phase == "hypomanic":
        first_line = ["Mood stabilizer (lithium or valproate) — first-line for mania", "Atypical antipsychotic (olanzapine, quetiapine, risperidone, aripiprazole) — first-line for acute mania", "Discontinue antidepressants if present (may worsen cycling)"]
        pharmacotherapy = (
            "Atypical antipsychotic (olanzapine, risperidone, or quetiapine) + mood stabilizer (lithium or valproate). ECT for severe/refractory mania."
            if psychotic_features
            else "Lithium (target level 0.8–1.2 mEq/L for acute mania) or valproate (target 85–125 mcg/mL). Atypical antipsychotic as monotherapy or adjunct."
        )
        notes = "Acute mania: discontinue antidepressants (may precipitate cycling). Mood stabilizer + atypical antipsychotic combination for severe mania."
    elif current_phase == "depressed":
        first_line = ["Quetiapine — first-line for bipolar depression (FDA-approved)", "Lurasidone + lithium or valproate (FDA-approved for bipolar I depression)", "Lithium or lamotrigine as mood stabilizer for depression", "AVOID antidepressant monotherapy (risk of switching to mania)"]
        _lam = "Lamotrigine is preferred for bipolar II depression." if bipolar_type == "II" else ""
        pharmacotherapy = f"Quetiapine 50–300 mg/day or lurasidone 20–120 mg/day (with food). Lamotrigine for bipolar II depression (titrate slowly — SJS risk). {_lam} AVOID antidepressant monotherapy."
        notes = "Bipolar depression: antidepressant monotherapy is contraindicated (risk of switching to mania/rapid cycling). Quetiapine and lurasidone are FDA-approved for bipolar I depression."
    elif rapid_cycling:
        first_line = ["Lithium + valproate combination", "Lamotrigine for depressive phase", "Atypical antipsychotic (quetiapine, olanzapine)", "Discontinue antidepressants and stimulants"]
        pharmacotherapy = "Lithium + valproate combination. Lamotrigine for depressive cycling. Thyroid optimization (hypothyroidism worsens rapid cycling). Avoid antidepressants."
        notes = "Rapid cycling (≥4 episodes/year): antidepressants worsen rapid cycling. Optimize thyroid function. Combination mood stabilizer therapy often required."
    else:
        first_line = ["Continue mood stabilizer (lithium preferred for maintenance — suicide prevention)", "Psychoeducation (most evidence-based psychotherapy for bipolar)", "Interpersonal and Social Rhythm Therapy (IPSRT)", "Family-Focused Therapy (FFT)"]
        _lith = "Lithium (target 0.6–0.8 mEq/L for maintenance)" if lithium_tried else "Lithium — first-line for maintenance (strongest evidence for relapse prevention and suicide prevention)"
        pharmacotherapy = f"{_lith}. Lamotrigine for depressive relapse prevention. Valproate for manic relapse prevention."
        notes = "Maintenance: lithium has the strongest evidence for relapse prevention and suicide prevention in bipolar disorder. Psychoeducation significantly reduces relapse rates."

    indication = f"Bipolar {bipolar_type or 'Disorder'} — {current_phase or 'unspecified phase'}"
    if rapid_cycling:
        indication += " (Rapid Cycling)"
    if psychotic_features:
        indication += " with Psychotic Features"

    if current_phase == "manic" and severity == "severe":
        level_of_care = "Inpatient stabilization"
    elif suicidal_ideation:
        level_of_care = "Inpatient or crisis stabilization"
    else:
        level_of_care = "Outpatient with close follow-up"

    return {
        "condition": "bipolar",
        "primaryRecommendation": {
            "indication": indication,
            "firstLineIntervention": first_line,
            "pharmacotherapy": pharmacotherapy,
            "psychotherapy": "Psychoeducation (most evidence-based for bipolar), IPSRT, Family-Focused Therapy (FFT), CBT — all as adjuncts to pharmacotherapy",
            "levelOfCare": level_of_care,
            "cor": "Strong",
            "loe": "A",
            "guidelineSource": "APA Practice Guideline for Bipolar Disorder + CANMAT 2023 Bipolar Guidelines",
            "notes": notes,
        },
        "alternativeRecommendations": [
            {
                "indication": "Lithium-refractory bipolar",
                "intervention": "Valproate + atypical antipsychotic combination. Consider ECT for severe refractory mania or depression.",
                "notes": "ECT is highly effective for severe bipolar depression and mania. Consider when pharmacotherapy fails.",
            },
            {
                "indication": "Bipolar disorder in pregnancy",
                "intervention": "Lamotrigine (safest mood stabilizer in pregnancy — avoid valproate). Quetiapine for acute episodes. Reproductive psychiatry consultation.",
                "notes": "Valproate is Category X in pregnancy. Lithium requires careful monitoring (Ebstein anomaly risk — lower than historically reported).",
            },
        ],
        "urgentFlags": urgent,
        "safetyConsiderations": [
            *safety,
            "Lithium toxicity: narrow therapeutic index — monitor levels, renal function, thyroid",
            "Valproate: teratogenic (Category X in pregnancy), hepatotoxicity, thrombocytopenia",
            "Lamotrigine: Stevens-Johnson Syndrome (SJS) risk — titrate slowly, avoid rapid dose escalation",
            "Atypical antipsychotics: metabolic monitoring required",
        ],
        "monitoringParameters": ["Mood diary / life chart", "Lithium level (q3-6 months maintenance)", "Renal function and thyroid (lithium — q6 months)", "Valproate level and LFTs", "Metabolic monitoring if atypical antipsychotic"],
        "multidisciplinaryConsult": ["Psychotherapy (psychoeducation, IPSRT, FFT)", "Reproductive psychiatry (if pregnancy)", "Social work (disability, employment support)"],
        "references": [
            {"citation": "Yatham LN et al. Bipolar Disord 2023 (CANMAT/ISBD Guidelines for Bipolar Disorder)", "year": 2023},
            {"citation": "Cipriani A et al. Lancet 2013 (Lithium for bipolar — meta-analysis)", "year": 2013},
            {"citation": "Calabrese JR et al. J Clin Psychiatry 1999 (Lamotrigine for bipolar depression)", "year": 1999},
            {"citation": "Geddes JR et al. NEJM 2004 (Quetiapine for bipolar depression — BOLDER trial)", "year": 2004},
        ],
        "guidelineYear": "2023",
    }


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK
# ─────────────────────────────────────────────────────────────────────────────


def _insufficient_data(condition: str) -> dict:
    return {
        "condition": condition,
        "primaryRecommendation": {
            "indication": "Insufficient data",
            "firstLineIntervention": ["Complete clinical assessment required"],
            "pharmacotherapy": "Cannot determine without complete clinical information",
            "psychotherapy": "Cannot determine without complete clinical information",
            "levelOfCare": "Cannot determine",
            "cor": "N/A",
            "loe": "N/A",
            "guidelineSource": "N/A",
            "notes": "Please complete all required fields for a clinical recommendation.",
        },
        "alternativeRecommendations": [],
        "urgentFlags": [],
        "safetyConsiderations": [],
        "monitoringParameters": [],
        "multidisciplinaryConsult": [],
        "references": [],
        "guidelineYear": "N/A",
    }
