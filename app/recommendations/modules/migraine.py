"""Migraine clinical recommendation engine.

Ported 1:1 from old_static_code/client/src/lib/migraineLogic.ts (assessMigraine).
Based on: AAN/AHS 2025 CGRP Guidelines, AHS Consensus 2021, AAN 2012 Prevention.
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "migraine"

_REFERENCES = [
    {
        "citation": (
            "Ailani J, et al. The American Headache Society Consensus Statement: "
            "Update on integrating new migraine treatments into clinical practice. "
            "Headache. 2021;61(7):1021-1039."
        ),
        "pmid": "34160823",
        "url": "https://pubmed.ncbi.nlm.nih.gov/34160823/",
    },
    {
        "citation": (
            "Silberstein SD, et al. Evidence-based guideline update: Pharmacologic "
            "treatment for episodic migraine prevention in adults. Neurology. "
            "2012;78(17):1337-1345."
        ),
        "pmid": "22529202",
        "url": "https://pubmed.ncbi.nlm.nih.gov/22529202/",
    },
    {
        "citation": (
            "Dodick DW, et al. ARISE: A Phase 3 randomized trial of erenumab for "
            "episodic migraine. Cephalalgia. 2018;38(6):1026-1037."
        ),
        "pmid": "29471679",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29471679/",
    },
    {
        "citation": (
            "Goadsby PJ, et al. A Controlled Trial of Erenumab for Episodic Migraine. "
            "N Engl J Med. 2017;377(22):2123-2132."
        ),
        "pmid": "29171821",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29171821/",
    },
    {
        "citation": "AAN/AHS 2025 CGRP Guideline Update. American Academy of Neurology.",
        "url": "https://www.aan.com/Guidelines/",
    },
    {
        "citation": (
            "Diener HC, et al. Medication-overuse headache: a worldwide problem. "
            "Lancet Neurol. 2019;18(3):291-302."
        ),
        "pmid": "30773457",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30773457/",
    },
]


def assess(data: dict) -> dict:
    migraine_subtype = data.get("migraineSubtype")
    frequency = data.get("frequency")
    headache_days_per_month = num(data.get("headacheDaysPerMonth"), 0)
    acute_therapy_response = data.get("acuteTherapyResponse")
    preventive_history = data.get("preventiveHistory")
    has_cardiovascular_disease = to_bool(data.get("hasCardiovascularDisease"))
    has_uncontrolled_hypertension = to_bool(data.get("hasUncontrolledHypertension"))
    has_hemiplegic_migraine = to_bool(data.get("hasHemiplegicMigraine"))
    has_basilar_migraine = to_bool(data.get("hasBasilarMigraine"))
    is_pregnant_or_planning = to_bool(data.get("isPregnantOrPlanning"))
    has_moh = to_bool(data.get("hasMOH"))
    acute_medication_days_per_month = num(data.get("acuteMedicationDaysPerMonth"), 0)
    has_depression = to_bool(data.get("hasDepression"))
    has_epilepsy = to_bool(data.get("hasEpilepsy"))
    has_weight_concerns = to_bool(data.get("hasWeightConcerns"))

    urgent_flags: list[str] = []
    agents_to_avoid: list[str] = []
    recommended_agents: list[str] = []
    next_steps: list[str] = []

    # Red flags
    if headache_days_per_month >= 15:
        urgent_flags.append(
            "Chronic migraine (≥15 headache days/month): preventive therapy is mandatory"
        )
    if has_moh or acute_medication_days_per_month >= 10:
        urgent_flags.append(
            "Medication overuse headache (MOH) suspected: acute medication use ≥10 days/month. "
            "Withdrawal and preventive therapy are required before acute therapy can be optimized."
        )

    # Contraindications
    if has_cardiovascular_disease or has_uncontrolled_hypertension:
        agents_to_avoid.append(
            "Triptans (vasoconstrictive — contraindicated in CAD, uncontrolled HTN, stroke history)"
        )
        agents_to_avoid.append("Ergotamines")
    if has_hemiplegic_migraine or has_basilar_migraine:
        agents_to_avoid.append("Triptans (contraindicated in hemiplegic and basilar migraine)")
        agents_to_avoid.append("Ergotamines")
    if is_pregnant_or_planning:
        agents_to_avoid.append("Topiramate (teratogenic — Category D)")
        agents_to_avoid.append("Valproate (teratogenic — Category X)")
        agents_to_avoid.append("Ergotamines")
        agents_to_avoid.append("NSAIDs (3rd trimester)")
    if has_epilepsy:
        agents_to_avoid.append("Amitriptyline (lowers seizure threshold at high doses)")
    if has_weight_concerns:
        agents_to_avoid.append("Valproate (weight gain)")
        agents_to_avoid.append("Amitriptyline (weight gain)")

    # Acute therapy
    if has_cardiovascular_disease or has_hemiplegic_migraine or has_basilar_migraine:
        acute_therapy = (
            "Triptan-contraindicated: use gepants (ubrogepant 50–100mg, rimegepant 75mg) "
            "or lasmiditan 50–200mg (ditan). "
            "NSAIDs + antiemetics (metoclopramide, prochlorperazine) as first-line alternatives. "
            "Gepants can also be used as preventive (rimegepant 75mg every other day — FDA approved 2021)."
        )
        recommended_agents.append("Ubrogepant 50–100mg (acute)")
        recommended_agents.append("Rimegepant 75mg (acute or preventive)")
        recommended_agents.append("Lasmiditan 50–200mg (acute)")
        recommended_agents.append("Naproxen sodium 500–550mg + metoclopramide")
    elif acute_therapy_response == "triptan_effective":
        acute_therapy = (
            "Continue effective triptan. Ensure early treatment (within 1 hour of onset). "
            "If incomplete response, consider combination triptan + NSAID or switch triptan class."
        )
        recommended_agents.append("Current effective triptan (continue)")
        recommended_agents.append("Sumatriptan + naproxen combination tablet")
    elif acute_therapy_response == "triptan_ineffective" or acute_therapy_response == "none_tried":
        acute_therapy = (
            "Triptans are first-line acute therapy for moderate-severe migraine (AAN Level A). "
            "If one triptan fails, trial a different triptan class before declaring class failure. "
            "Gepants (ubrogepant, rimegepant) are effective alternatives with no cardiovascular contraindications."
        )
        recommended_agents.append("Sumatriptan 50–100mg PO or 6mg SC")
        recommended_agents.append("Rizatriptan 10mg PO")
        recommended_agents.append("Eletriptan 40mg PO")
        recommended_agents.append("Zolmitriptan 2.5–5mg PO or nasal")
        recommended_agents.append("Ubrogepant 50–100mg (if triptan fails or contraindicated)")
        recommended_agents.append("Rimegepant 75mg ODT")
    else:
        acute_therapy = (
            "NSAIDs (naproxen 500mg, ibuprofen 400–800mg) with antiemetic for mild-moderate attacks. "
            "Triptans for moderate-severe attacks."
        )
        recommended_agents.append("Naproxen sodium 500mg")
        recommended_agents.append("Ibuprofen 400–800mg")
        recommended_agents.append("Sumatriptan 50mg")

    # Preventive therapy
    needs_preventive = (
        frequency == "high"
        or frequency == "chronic"
        or headache_days_per_month >= 4
        or has_moh
    )

    if needs_preventive:
        if (
            preventive_history == "failed_2plus_preventives"
            or preventive_history == "failed_topiramate"
            or preventive_history == "failed_valproate"
        ):
            preventive_therapy = (
                "Failed ≥2 oral preventives: CGRP monoclonal antibodies are indicated "
                "(AAN/AHS 2025 Level A). "
                "Erenumab 70–140mg SC monthly, fremanezumab 225mg SC monthly or 675mg quarterly, "
                "galcanezumab 240mg loading then 120mg SC monthly, eptinezumab 100–300mg IV quarterly. "
                "All have similar efficacy (~50% responder rate). "
                "Select based on administration preference and formulary."
            )
            recommended_agents.append("Erenumab 70–140mg SC monthly (anti-CGRP receptor)")
            recommended_agents.append("Fremanezumab 225mg SC monthly or 675mg quarterly")
            recommended_agents.append("Galcanezumab 120mg SC monthly (240mg loading dose)")
            recommended_agents.append("Eptinezumab 100–300mg IV quarterly")
            next_steps.append("Prior authorization for CGRP mAb")
            next_steps.append("Document failure of ≥2 oral preventives")
            next_steps.append(
                "Reassess at 3 months (≥50% reduction in headache days = response)"
            )
        elif preventive_history == "none":
            if is_pregnant_or_planning:
                preventive_therapy = (
                    "Pregnancy/planning: oral preventives with teratogenic risk are contraindicated. "
                    "Magnesium glycinate 400mg daily is safest option. "
                    "Propranolol (low dose) may be considered with OB/GYN guidance. "
                    "CGRP mAbs: insufficient safety data — generally held during pregnancy."
                )
                recommended_agents.append("Magnesium glycinate 400mg daily")
                recommended_agents.append("Propranolol 40–80mg daily (with OB guidance)")
            elif has_depression:
                preventive_therapy = (
                    "Migraine with comorbid depression: amitriptyline 10–75mg nightly addresses both conditions. "
                    "Venlafaxine 75–150mg daily is an alternative (SNRI with migraine prevention evidence). "
                    "Topiramate and beta-blockers are alternatives if antidepressants not preferred."
                )
                recommended_agents.append("Amitriptyline 10–75mg nightly")
                recommended_agents.append("Venlafaxine 75–150mg daily")
                recommended_agents.append("Topiramate 25–100mg daily")
            elif has_epilepsy:
                preventive_therapy = (
                    "Migraine with comorbid epilepsy: valproate 500–1500mg/day and "
                    "topiramate 25–100mg/day have dual indication. "
                    "Avoid if pregnancy is planned (both teratogenic)."
                )
                recommended_agents.append("Valproate 500–1500mg/day (if not planning pregnancy)")
                recommended_agents.append("Topiramate 25–100mg/day")
            else:
                preventive_therapy = (
                    "First-line oral preventives: topiramate 25–100mg/day, propranolol 40–160mg/day, "
                    "metoprolol 50–200mg/day, "
                    "amitriptyline 10–75mg nightly, or venlafaxine 75–150mg/day (AAN Level A). "
                    "Select based on comorbidities, tolerability, and patient preference."
                )
                recommended_agents.append("Topiramate 25–100mg/day")
                recommended_agents.append("Propranolol 40–160mg/day")
                recommended_agents.append("Metoprolol 50–200mg/day")
                recommended_agents.append("Amitriptyline 10–75mg nightly")
                recommended_agents.append("Candesartan 8–16mg/day (Level B)")
            next_steps.append(
                "Trial preventive for minimum 8–12 weeks at therapeutic dose before assessing response"
            )
            next_steps.append("Headache diary to track frequency and response")
        else:
            preventive_therapy = (
                "Prior preventive failure: switch to different class or escalate to CGRP mAb. "
                "Document prior failures for insurance prior authorization. "
                "CGRP mAbs are indicated after failure of 2 oral preventives."
            )
            recommended_agents.append("Trial different oral preventive class")
            recommended_agents.append("Consider CGRP mAb if ≥2 failures documented")
    else:
        preventive_therapy = (
            "Low-frequency migraine (<4 days/month): preventive therapy not currently indicated. "
            "Optimize acute therapy."
        )

    # MOH management
    moh_management = "No medication overuse headache identified."
    if has_moh or acute_medication_days_per_month >= 10:
        moh_management = (
            "Medication overuse headache (MOH): acute medication must be withdrawn. "
            "Abrupt withdrawal preferred for triptans, ergotamines, and NSAIDs. "
            "Gradual taper for opioids and barbiturates (withdrawal seizure risk). "
            "Bridge therapy: naproxen 500mg BID x 2 weeks or prednisone taper during withdrawal. "
            "Initiate preventive therapy simultaneously. "
            "Warn patient of rebound headache during first 2 weeks of withdrawal. "
            "Inpatient detoxification for severe cases or opioid/barbiturate overuse."
        )
        urgent_flags.append(
            "MOH: acute medication withdrawal required before preventive therapy can be effective"
        )

    # Pregnancy considerations
    pregnancy_considerations = "No pregnancy-specific restrictions identified."
    if is_pregnant_or_planning:
        pregnancy_considerations = (
            "Pregnancy: acetaminophen is safest acute therapy. "
            "Avoid NSAIDs (3rd trimester — premature ductus arteriosus closure). "
            "Triptans: limited data, generally avoided especially in 1st trimester. "
            "Preventive: magnesium glycinate 400mg/day is safest. Propranolol with OB guidance. "
            "CGRP mAbs: insufficient safety data — hold during pregnancy and breastfeeding."
        )

    if len(next_steps) == 0:
        next_steps.append(
            "Headache diary for 4–8 weeks to characterize frequency and triggers"
        )
        next_steps.append("Review acute medication use (days/month) to screen for MOH")
        next_steps.append("Assess disability with MIDAS or HIT-6 questionnaire")
        next_steps.append(
            "Neuroimaging only if red flag features present (thunderclap, new pattern, focal deficits)"
        )

    _atr = acute_therapy_response if acute_therapy_response is not None else ""
    _ph = preventive_history if preventive_history is not None else ""
    rationale = (
        f"Migraine subtype: {migraine_subtype}. "
        f"Frequency: {frequency} ({_fmt_num(headache_days_per_month)} days/month). "
        f"Acute therapy response: {str(_atr).replace('_', ' ')}. "
        f"Preventive history: {str(_ph).replace('_', ' ')}. "
        f"MOH: {'Yes' if has_moh else 'No'} "
        f"({_fmt_num(acute_medication_days_per_month)} acute med days/month). "
        f"CV disease: {'Yes' if has_cardiovascular_disease else 'No'}."
    )

    if needs_preventive:
        _chronic = "Chronic" if frequency == "chronic" else "High-frequency"
        _cgrp = (
            "CGRP mAb recommended after ≥2 oral preventive failures."
            if preventive_history == "failed_2plus_preventives"
            else "First-line oral preventive recommended."
        )
        primary_recommendation = (
            f"{_chronic} migraine: preventive therapy indicated. {_cgrp}"
        )
    else:
        primary_recommendation = (
            "Episodic migraine: optimize acute therapy. Preventive therapy not currently indicated."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "acuteTherapy": acute_therapy,
        "preventiveTherapy": preventive_therapy,
        "recommendedAgents": recommended_agents,
        "agentsToAvoid": agents_to_avoid,
        "mohManagement": moh_management,
        "urgentFlags": urgent_flags,
        "pregnancyConsiderations": pregnancy_considerations,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }


def _fmt_num(x: float) -> str:
    """Mirror JS template-literal number stringification (3.0 -> '3')."""
    if x == int(x):
        return str(int(x))
    return str(x)
