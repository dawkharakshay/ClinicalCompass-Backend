"""Functional Seizures (PNES) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/functionalSeizuresLogic.ts
(assessFunctionalSeizures).

Based on: AAN 2025 Guideline — Functional Seizures / Psychogenic Nonepileptic
Seizures. Reference: Neurology 2025; DOI:10.1212/WNL.0000000000213604.
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "functionalseizures"

_REFERENCES = [
    {
        "citation": (
            "LaFrance WC Jr, et al. Cognitive behavioral therapy for psychogenic "
            "nonepileptic seizures (CODES): a pragmatic, multicentre, randomised "
            "controlled trial. Lancet Psychiatry. 2022;9(4):313-324."
        ),
        "pmid": "34195556",
        "url": "https://pubmed.ncbi.nlm.nih.gov/34195556/",
    },
    {
        "citation": (
            "Goldstein LH, et al. Cognitive-behavioural therapy for adults with "
            "dissociative seizures (CODES): a pragmatic, multicentre, randomised "
            "controlled trial. Lancet Psychiatry. 2020;7(6):491-505."
        ),
        "pmid": "20624924",
        "url": "https://pubmed.ncbi.nlm.nih.gov/20624924/",
    },
    {
        "citation": (
            "American Academy of Neurology. Practice Guideline: Functional Seizures. "
            "Neurology. 2025."
        ),
        "pmid": "34195556",
        "url": "https://www.aan.com/Guidelines/home/GuidelineDetail/1097",
    },
    {
        "citation": (
            "Reuber M, et al. Outcome in psychogenic nonepileptic seizures: 1 to "
            "10-year follow-up in 164 patients. Ann Neurol. 2003;53(3):305-311."
        ),
        "pmid": "12601698",
        "url": "https://pubmed.ncbi.nlm.nih.gov/12601698/",
    },
    {
        "citation": (
            "Bodde NM, et al. Psychogenic non-epileptic seizures--definition, "
            "etiology, treatment and prognostic issues: a critical review. Seizure. "
            "2009;18(8):543-553."
        ),
        "pmid": "19616979",
        "url": "https://pubmed.ncbi.nlm.nih.gov/19616979/",
    },
]


def assess(data: dict) -> dict:
    diagnostic_certainty = data.get("diagnosticCertainty")
    veeg_performed = to_bool(data.get("veegPerformed"))
    veeg_result = data.get("veegResult")
    psychiatric_comorbidity = data.get("psychiatricComorbidity")
    psychotherapy_type = data.get("psychotherapyType")

    has_co_occurring_epilepsy = to_bool(data.get("hasCoOccurringEpilepsy"))
    antiseizure_meds_for_functional_only = to_bool(data.get("antiseizureMedsForFunctionalOnly"))
    currently_on_antiseizure_meds = to_bool(data.get("currentlyOnAntiseizureMeds"))
    currently_in_psychotherapy = to_bool(data.get("currentlyInPsychotherapy"))
    has_emergency_presentations = to_bool(data.get("hasEmergencyPresentations"))
    # Legacy form derived isPediatric from the age input
    # (FunctionalSeizuresCompass.tsx: update("isPediatric", age < 18)); the seeded
    # form submits patientAgeYears but not isPediatric, so reproduce when absent.
    is_pediatric = (
        num(data.get("patientAgeYears"), 0) < 18
        if data.get("isPediatric") is None
        else to_bool(data.get("isPediatric"))
    )

    diagnosis_delay_years = num(data.get("diagnosisDelayYears"), 0)

    urgent_flags: list[str] = []
    medication_guidance: list[str] = []
    multidisciplinary_referrals: list[str] = []
    next_steps: list[str] = []
    monitoring_plan: list[str] = []

    # ─── Urgent Flags ───────────────────────────────────────────────────────
    if has_co_occurring_epilepsy and diagnostic_certainty == "not_yet_assessed":
        urgent_flags.append(
            "Co-occurring epilepsy suspected but not yet assessed — VEEG required to "
            "distinguish seizure types before modifying antiseizure medications"
        )
    if antiseizure_meds_for_functional_only and not has_co_occurring_epilepsy:
        urgent_flags.append(
            "Antiseizure medications prescribed for functional seizures without "
            "co-occurring epilepsy — AAN 2025 strongly recommends against; plan "
            "supervised taper"
        )
    if has_emergency_presentations:
        urgent_flags.append(
            "Recurrent ED presentations — high risk of iatrogenic harm from "
            "benzodiazepines; educate ED team on PNES management protocol"
        )
    if diagnosis_delay_years > 5:
        urgent_flags.append(
            f"Diagnosis delayed {_js_number(diagnosis_delay_years)} years "
            "(average 7-8 years nationally) — expedite VEEG and psychiatric referral "
            "to reduce ongoing harm"
        )

    # ─── Diagnostic Plan ────────────────────────────────────────────────────
    if veeg_result == "pnes_confirmed":
        diagnostic_plan = (
            "Definite PNES confirmed by VEEG. Communicate diagnosis clearly and "
            "compassionately. "
            "Evaluate for co-occurring epilepsy if any clinical suspicion. "
            "Screen for co-occurring psychiatric disorders (PTSD, depression, somatic "
            "symptom disorder, dissociative disorder)."
        )
    elif veeg_result == "not_done" or veeg_result == "non_diagnostic":
        diagnostic_plan = (
            "VEEG is the gold standard — obtain VEEG capture of a typical event if "
            "diagnostic ambiguity persists. "
            "If VEEG not feasible: use ambulatory EEG, interictal EEG, smartphone "
            "video of events, and detailed semiology. "
            "Evaluate cardiac causes: ECG monitoring and/or tilt-table testing if "
            "syncope cannot be excluded. "
            "Serum prolactin, lactate, CK have limited utility (false "
            "positives/negatives) — do not use as sole diagnostic criterion."
        )
    elif veeg_result == "epilepsy_confirmed":
        diagnostic_plan = (
            "Epilepsy confirmed on VEEG. Evaluate for co-occurring PNES if clinical "
            "features suggest mixed etiology. "
            "Up to 12% of people with epilepsy have co-occurring functional seizures."
        )
    else:
        diagnostic_plan = (
            "Functional seizures are a positive clinical diagnosis — not a diagnosis "
            "of exclusion. "
            "Include PNES in the differential from initial workup. Seek detailed "
            "history from patient and witnesses. "
            "Perform brief ictal physical examination during prolonged events in "
            "emergency settings."
        )

    # ─── Treatment Pathway ──────────────────────────────────────────────────
    psychotherapy_recommendation = ""

    if diagnostic_certainty == "definite" or veeg_result == "pnes_confirmed":
        primary_recommendation = (
            "Cognitive Behavioral Therapy (CBT) — first-line treatment for functional "
            "seizures (AAN 2025, Level B)"
        )
        treatment_pathway = (
            "Step 1: Communicate diagnosis clearly — use the term 'functional "
            "seizures' and explain the neurological basis. "
            "Step 2: Initiate CBT-based psychotherapy — strongest evidence base "
            "(CODES RCT: CBT reduced seizure frequency vs standard care). "
            "Step 3: Mindfulness-based therapy or neuro-behavioral therapy as "
            "alternatives if CBT unavailable. "
            "Step 4: Address underlying psychological factors (trauma, dissociation, "
            "somatic amplification). "
            "Step 5: Involve family in treatment, especially for pediatric patients."
        )

        if not currently_in_psychotherapy:
            next_steps.append(
                "Refer to psychologist/psychiatrist experienced in functional "
                "neurological disorder (FND)"
            )
            next_steps.append(
                "Provide patient education materials about functional seizures (FND "
                "Hope, FND Society resources)"
            )
        elif psychotherapy_type != "cbt":
            next_steps.append(
                "Consider transition to CBT — highest evidence for functional "
                "seizures (CODES trial, PMID:34195556)"
            )
    elif diagnostic_certainty == "probable":
        primary_recommendation = (
            "Probable PNES — proceed with psychotherapy while completing diagnostic "
            "workup"
        )
        treatment_pathway = (
            "Clinical diagnosis of probable PNES based on semiology and history. "
            "Do not delay psychotherapy initiation pending VEEG if clinical "
            "confidence is high. "
            "Continue VEEG workup to achieve definite diagnosis."
        )
    else:
        primary_recommendation = (
            "Diagnostic workup required before initiating PNES-specific treatment"
        )
        treatment_pathway = (
            "Insufficient diagnostic certainty — complete VEEG workup. "
            "Do not initiate or continue antiseizure medications solely for suspected "
            "PNES without confirmed co-occurring epilepsy."
        )

    # ─── Psychotherapy Recommendation ───────────────────────────────────────
    if psychotherapy_type == "cbt" and currently_in_psychotherapy:
        psychotherapy_recommendation = (
            "Currently receiving CBT — continue and optimize. Ensure therapist has "
            "FND/PNES experience. "
            "Target: ≥50% reduction in seizure frequency at 12 months (CODES trial "
            "benchmark)."
        )
    elif currently_in_psychotherapy:
        psychotherapy_recommendation = (
            "Currently in psychotherapy but not CBT. Consider transition to CBT — "
            "strongest evidence for PNES. "
            "Mindfulness-based therapy and neuro-behavioral therapy are acceptable "
            "alternatives."
        )
    else:
        psychotherapy_recommendation = (
            "Not currently in psychotherapy. Refer to CBT-trained therapist with FND "
            "experience. "
            "If CBT unavailable: mindfulness-based therapy or neuro-behavioral "
            "therapy. "
            "Involve family in treatment for pediatric patients (AAN 2025 "
            "recommendation)."
        )

    # ─── Medication Guidance ────────────────────────────────────────────────
    if not has_co_occurring_epilepsy:
        medication_guidance.append(
            "Do NOT prescribe antiseizure medications for functional seizures "
            "without co-occurring epilepsy (AAN 2025, Level A)"
        )
        if currently_on_antiseizure_meds:
            medication_guidance.append(
                "Supervised taper of antiseizure medications recommended — risks "
                "include fatigue, dizziness, Stevens-Johnson syndrome, aplastic "
                "anemia, hepatic failure"
            )
            medication_guidance.append(
                "Avoid benzodiazepines in acute settings — habit-forming, cognitive "
                "impairment, risk of intubation and iatrogenic harm"
            )
    else:
        medication_guidance.append(
            "Co-occurring epilepsy present — prescribe appropriate antiseizure "
            "medications for epileptic seizures only"
        )
        medication_guidance.append(
            "Use VEEG to identify and distinguish different seizure types — counsel "
            "patient that antiseizure medications treat epileptic seizures, not "
            "functional seizures"
        )
        medication_guidance.append(
            "Avoid benzodiazepines as standing treatment for functional seizures "
            "even in co-occurring epilepsy"
        )

    # ─── Multidisciplinary Referrals ────────────────────────────────────────
    if psychiatric_comorbidity != "none":
        multidisciplinary_referrals.append(
            f"Psychiatry referral — {psychiatric_comorbidity} identified; concurrent "
            "psychiatric treatment required"
        )
    if not currently_in_psychotherapy:
        multidisciplinary_referrals.append(
            "Psychology/FND specialist — CBT-based therapy is first-line treatment"
        )
    if has_emergency_presentations:
        multidisciplinary_referrals.append(
            "Emergency department liaison — educate ED team on PNES protocol to "
            "prevent iatrogenic harm from benzodiazepines"
        )
    if is_pediatric:
        multidisciplinary_referrals.append(
            "Pediatric neurology + child/adolescent psychiatry — family involvement "
            "in treatment is specifically recommended (AAN 2025)"
        )
    multidisciplinary_referrals.append(
        "Social work — address psychosocial stressors, disability, and "
        "return-to-work/school planning"
    )

    # ─── Monitoring Plan ────────────────────────────────────────────────────
    monitoring_plan.append(
        "Track seizure frequency with seizure diary — target ≥50% reduction at "
        "3-6 months"
    )
    monitoring_plan.append(
        "Reassess psychiatric comorbidities at each visit — PTSD, depression, "
        "anxiety are common drivers"
    )
    monitoring_plan.append("Monitor psychotherapy adherence and engagement")
    if currently_on_antiseizure_meds and not has_co_occurring_epilepsy:
        monitoring_plan.append(
            "Monitor antiseizure medication taper — slow taper over weeks to months "
            "to prevent withdrawal"
        )
    if has_co_occurring_epilepsy:
        monitoring_plan.append(
            "Monitor both seizure types separately — functional and epileptic "
            "seizures may have different trajectories"
        )

    # ─── Next Steps ─────────────────────────────────────────────────────────
    if not veeg_performed:
        next_steps.append(
            "Schedule VEEG monitoring — gold standard for definite PNES diagnosis"
        )
    next_steps.append(
        "Provide written diagnosis explanation — patients who understand their "
        "diagnosis have better outcomes"
    )
    next_steps.append(
        "Refer to FND Society (fndhope.org) and FND Action patient resources"
    )
    if has_co_occurring_epilepsy:
        next_steps.append(
            "Epilepsy clinic follow-up — optimize antiseizure therapy for epileptic "
            "component"
        )

    # ─── Evidence Level ─────────────────────────────────────────────────────
    evidence_level = (
        "Level B — AAN 2025 (probable recommendation based on Class II evidence)"
    )
    if veeg_result == "pnes_confirmed" and psychotherapy_type == "cbt":
        evidence_level = (
            "Level B — AAN 2025; CODES RCT (LaFrance et al., Lancet Psychiatry 2022, "
            "PMID:34195556)"
        )

    rationale = (
        "Functional seizures (PNES) are a common neurological condition affecting "
        "2-33 per 100,000 people, "
        "with an average diagnostic delay of 7-8 years. The AAN 2025 guideline "
        "emphasizes positive diagnosis "
        "(not exclusion), VEEG as the gold standard, CBT as first-line treatment, "
        "and strongly recommends "
        "against antiseizure medications for functional seizures without co-occurring "
        "epilepsy. "
        "Multidisciplinary care integrating neurology, psychiatry, and psychology is "
        "essential."
    )

    return {
        "primaryRecommendation": primary_recommendation,
        "diagnosticPlan": diagnostic_plan,
        "treatmentPathway": treatment_pathway,
        "urgentFlags": urgent_flags,
        "medicationGuidance": medication_guidance,
        "psychotherapyRecommendation": psychotherapy_recommendation,
        "multidisciplinaryReferrals": multidisciplinary_referrals,
        "nextSteps": next_steps,
        "monitoringPlan": monitoring_plan,
        "evidenceLevel": evidence_level,
        "rationale": rationale,
        "references": _REFERENCES,
    }


def _js_number(x: float) -> str:
    """Render a number as JS template-literal interpolation would (integers
    without a trailing ``.0``)."""
    if x == int(x):
        return str(int(x))
    return str(x)
