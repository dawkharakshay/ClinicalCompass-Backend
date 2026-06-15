"""Parkinson's Disease clinical recommendation engine.

Ported 1:1 from old_static_code/client/src/lib/parkinsonsLogic.ts
(assessParkinsons). MDS 2025 / AAN 2023 evidence-based therapy selection,
motor-fluctuation management, DBS candidacy, and non-motor management.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "parkinsons"


_REFERENCES = [
    {
        "citation": "Fox SH, et al. International Parkinson and Movement Disorder Society Evidence-Based Medicine Review: Update on treatments for the motor symptoms of Parkinson's disease. Mov Disord. 2018;33(8):1248-1266.",
        "pmid": "29570866",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29570866/",
    },
    {
        "citation": "Fasano A, et al. Management of advanced therapies in Parkinson's disease patients in times of humanitarian crisis. NPJ Parkinsons Dis. 2020;6:20.",
        "pmid": "32665958",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32665958/",
    },
    {
        "citation": "Connolly BS, Lang AE. Pharmacological treatment of Parkinson disease: a review. JAMA. 2014;311(16):1670-1683.",
        "pmid": "24756517",
        "url": "https://pubmed.ncbi.nlm.nih.gov/24756517/",
    },
    {
        "citation": "Bhidayasiri R, et al. Evidence-based guideline: Treatment of tardive syndromes. Neurology. 2013;81(5):463-469.",
        "pmid": "23897874",
        "url": "https://pubmed.ncbi.nlm.nih.gov/23897874/",
    },
    {
        "citation": "MDS 2025 Evidence-Based Medicine Review: Parkinson's Disease. Movement Disorder Society.",
        "url": "https://www.movementdisorders.org/",
    },
    {
        "citation": "Deuschl G, et al. A randomized trial of deep-brain stimulation for Parkinson's disease. N Engl J Med. 2006;355(9):896-908.",
        "pmid": "16943402",
        "url": "https://pubmed.ncbi.nlm.nih.gov/16943402/",
    },
]


def _capitalize(s: str) -> str:
    """JS ``s.charAt(0).toUpperCase() + s.slice(1)``."""
    if not s:
        return s
    return s[0].upper() + s[1:]


def assess(data: dict) -> dict:
    stage = data.get("stage")
    age = num(data.get("age"), 0)
    updrs_motor_score = num(data.get("updrsMotorScore"), 0)
    hoehn_yahr_scale = data.get("hoehnYahrScale")
    motor_fluctuations = data.get("motorFluctuations")
    initial_therapy_history = data.get("initialTherapyHistory")
    tremor_dominant = truthy(data.get("tremorDominant"))
    has_hallucinations = truthy(data.get("hasHallucinations"))
    has_dementia = truthy(data.get("hasDementia"))
    has_orthostasis = truthy(data.get("hasOrthostasis"))
    has_impulse_control_disorder = truthy(data.get("hasImpulseControlDisorder"))
    is_dbs_candidate = truthy(data.get("isDBSCandidate"))
    dbs_contraindications = data.get("dbsContraindications") or []
    wants_non_oral_therapy = truthy(data.get("wantsNonOralTherapy"))

    urgent_flags: list[str] = []
    agents_to_avoid: list[str] = []
    recommended_agents: list[str] = []
    next_steps: list[str] = []

    # Safety flags
    if has_hallucinations:
        urgent_flags.append(
            "Hallucinations present: avoid dopamine agonists and MAO-B inhibitors if possible; consider clozapine 6.25–50mg or pimavanserin 34mg for psychosis"
        )
        agents_to_avoid.append("Dopamine agonists (worsen psychosis)")
        agents_to_avoid.append("MAO-B inhibitors (may worsen psychosis)")
        agents_to_avoid.append(
            "Typical antipsychotics (haloperidol, risperidone — worsen parkinsonism)"
        )
    if has_impulse_control_disorder:
        urgent_flags.append(
            "Impulse control disorder: reduce or discontinue dopamine agonist — ICD occurs in 10–15% of patients on agonists"
        )
        agents_to_avoid.append(
            "Dopamine agonists (ICD risk — pramipexole, ropinirole, rotigotine)"
        )
    if has_dementia:
        agents_to_avoid.append("Anticholinergics (worsen cognition)")
        agents_to_avoid.append("Amantadine (may worsen confusion)")
        urgent_flags.append(
            "Dementia present: avoid anticholinergics and amantadine; rivastigmine is evidence-based for PD dementia (AAN Level A)"
        )
    if has_orthostasis:
        agents_to_avoid.append("High-dose dopamine agonists (worsen orthostasis)")
        urgent_flags.append(
            "Orthostatic hypotension: review all antihypertensives; consider midodrine or droxidopa"
        )

    # DBS assessment
    dbs_assessment = ""
    dbs_candidacy_criteria = [
        stage == "moderate" or stage == "advanced",
        motor_fluctuations != "none",
        not has_dementia,
        len(dbs_contraindications) == 0,
        updrs_motor_score >= 20,
    ]
    dbs_criteria_met_count = sum(1 for c in dbs_candidacy_criteria if c)

    if is_dbs_candidate and dbs_criteria_met_count >= 4:
        dbs_assessment = (
            "DBS CANDIDATE: Patient meets criteria for deep brain stimulation evaluation. "
            "Refer to multidisciplinary DBS team (neurology, neurosurgery, neuropsychology). "
            "STN-DBS is preferred target for motor fluctuations + dyskinesia. "
            "GPi-DBS preferred if prominent dyskinesia or psychiatric comorbidity. "
            "Levodopa responsiveness (UPDRS improvement ≥30% on/off) is the strongest predictor of DBS benefit."
        )
        recommended_agents.append("DBS evaluation referral (STN or GPi target)")
        next_steps.append("Refer to DBS multidisciplinary team")
        next_steps.append("Levodopa challenge test (UPDRS Part III on vs off)")
        next_steps.append("Neuropsychological evaluation")
        next_steps.append("Psychiatric clearance")
    elif len(dbs_contraindications) > 0:
        dbs_assessment = (
            f"DBS contraindicated: {', '.join(dbs_contraindications)}. "
            "Consider levodopa-carbidopa intestinal gel (LCIG/Duopa) or subcutaneous apomorphine infusion as device-aided alternatives."
        )
        if wants_non_oral_therapy:
            recommended_agents.append("Levodopa-carbidopa intestinal gel (LCIG/Duopa)")
            recommended_agents.append("Subcutaneous apomorphine infusion")
    else:
        dbs_assessment = (
            "DBS not currently indicated. Optimize pharmacotherapy first. Reassess if motor fluctuations worsen despite optimized medical therapy."
        )

    # Pharmacotherapy by stage and fluctuations
    pharmacotherapy = ""

    if stage == "early" and motor_fluctuations == "none":
        if initial_therapy_history == "none":
            if age < 65 and not tremor_dominant:
                pharmacotherapy = (
                    "Early PD, age <65: dopamine agonist (pramipexole, ropinirole, rotigotine) as initial therapy to delay levodopa initiation and reduce dyskinesia risk. "
                    "MAO-B inhibitors (rasagiline, selegiline, safinamide) are an alternative for mild symptoms. "
                    "Levodopa remains most effective — initiate when functional impairment warrants."
                )
                recommended_agents.append("Pramipexole ER 0.375–4.5mg/day")
                recommended_agents.append("Ropinirole XL 2–24mg/day")
                recommended_agents.append("Rotigotine patch 2–8mg/24h")
                recommended_agents.append("Rasagiline 1mg/day (MAO-B inhibitor)")
                recommended_agents.append("Safinamide 50–100mg/day (add-on)")
            else:
                pharmacotherapy = (
                    "Early PD, age ≥65 or tremor-dominant: levodopa-carbidopa is preferred initial therapy. "
                    "Provides best symptomatic control with lowest neuropsychiatric risk in older patients. "
                    "Start low (25/100mg TID) and titrate to symptom control."
                )
                recommended_agents.append(
                    "Levodopa-carbidopa 25/100mg TID (titrate to response)"
                )
                recommended_agents.append("Rasagiline 1mg/day (adjunct for mild symptoms)")
        else:
            pharmacotherapy = (
                "Established early PD on therapy: optimize current regimen. "
                "If on MAO-B inhibitor with inadequate control, add levodopa or dopamine agonist. "
                "If on dopamine agonist with adequate control, continue and monitor for ICD."
            )
            recommended_agents.append("Optimize current therapy")
            recommended_agents.append("Add levodopa if functional impairment persists")
    elif motor_fluctuations == "wearing_off":
        pharmacotherapy = (
            "Wearing-off fluctuations: multiple strategies available (AAN Level A). "
            "1) Increase levodopa dose frequency (shorten dosing interval). "
            "2) Add MAO-B inhibitor (rasagiline, safinamide) to extend levodopa effect. "
            "3) Add COMT inhibitor (entacapone, opicapone) to extend levodopa half-life. "
            "4) Add dopamine agonist as adjunct. "
            "5) Consider extended-release carbidopa-levodopa (Rytary) for smoother coverage."
        )
        recommended_agents.append(
            "Rasagiline 1mg/day or Safinamide 50–100mg/day (MAO-B inhibitor add-on)"
        )
        recommended_agents.append(
            "Entacapone 200mg with each levodopa dose (COMT inhibitor)"
        )
        recommended_agents.append("Opicapone 50mg once daily (COMT inhibitor)")
        recommended_agents.append("Carbidopa-levodopa ER (Rytary) for smoother coverage")
        recommended_agents.append(
            "Istradefylline 20–40mg/day (adenosine A2A antagonist — adjunct)"
        )
        next_steps.append("Wearing-off diary to quantify off-time")
        next_steps.append("Adjust levodopa dosing interval before adding adjunct")
    elif motor_fluctuations == "dyskinesia":
        pharmacotherapy = (
            "Levodopa-induced dyskinesia (LID): "
            "1) Reduce individual levodopa dose, increase frequency (same total daily dose). "
            "2) Add amantadine (NMDA antagonist) — reduces dyskinesia by 50–60% (AAN Level B). "
            "3) Extended-release amantadine (Gocovri 137mg nightly) FDA-approved for LID. "
            "4) If refractory: DBS (GPi target preferred for dyskinesia) or LCIG."
        )
        if not has_dementia:
            recommended_agents.append("Amantadine 100mg BID–TID")
            recommended_agents.append(
                "Amantadine ER (Gocovri) 137mg nightly (FDA-approved for LID)"
            )
            recommended_agents.append("Reduce levodopa dose + increase frequency")
        recommended_agents.append("DBS evaluation (GPi target preferred for dyskinesia)")
    elif motor_fluctuations == "on_off" or stage == "advanced":
        pharmacotherapy = (
            "Advanced PD with on-off fluctuations: device-aided therapy should be considered. "
            "1) DBS (STN or GPi) — gold standard for motor fluctuations in appropriate candidates. "
            "2) Levodopa-carbidopa intestinal gel (LCIG/Duopa) — continuous duodenal infusion, reduces off-time by 4–6 hours/day. "
            "3) Subcutaneous apomorphine infusion — continuous SC pump, effective for on-off fluctuations. "
            "4) Subcutaneous levodopa (foslevodopa/foscarbidopa — Produodopa) — emerging SC continuous delivery."
        )
        recommended_agents.append("DBS evaluation (STN-DBS preferred for fluctuations)")
        recommended_agents.append("LCIG (Duopa) — continuous intestinal gel infusion")
        recommended_agents.append("Subcutaneous apomorphine infusion")
        recommended_agents.append(
            "Apomorphine SC injection (Apokyn) for rescue during off episodes"
        )
        next_steps.append("Refer to movement disorder specialist")
        next_steps.append("DBS multidisciplinary evaluation")
        next_steps.append("Off-time diary (hours/day)")
    elif motor_fluctuations == "freezing":
        pharmacotherapy = (
            "Freezing of gait (FOG): optimize levodopa timing (often occurs during off-state). "
            "Physical therapy with cueing strategies (auditory, visual). "
            "Avoid anticholinergics. DBS may improve FOG in some patients (less predictable than other motor symptoms)."
        )
        recommended_agents.append("Optimize levodopa timing")
        recommended_agents.append("Physical therapy with cueing")
        recommended_agents.append("DBS evaluation if refractory")
        agents_to_avoid.append("Anticholinergics (may worsen FOG and cognition)")
    else:
        pharmacotherapy = (
            "Moderate PD: optimize levodopa regimen. Consider adjunct therapy if wearing-off develops. "
            "Regular reassessment every 3–6 months."
        )
        recommended_agents.append("Optimize levodopa-carbidopa regimen")
        recommended_agents.append("Consider MAO-B or COMT inhibitor adjunct")

    # Non-motor management
    non_motor_management = (
        "Non-motor symptom management is essential in PD: "
        "Depression/anxiety: SSRIs (paroxetine, sertraline) or SNRIs. "
        "Dementia: rivastigmine (AAN Level A). "
        "Psychosis: pimavanserin 34mg/day (FDA-approved for PD psychosis) or low-dose clozapine. "
        "REM sleep behavior disorder: clonazepam 0.5–1mg or melatonin 3–12mg nightly. "
        "Constipation: polyethylene glycol, lubiprostone. "
        "Orthostatic hypotension: midodrine, droxidopa, fludrocortisone. "
        "Sialorrhea: botulinum toxin injection to parotid/submandibular glands."
    )

    if has_dementia:
        non_motor_management += (
            " Rivastigmine 3–12mg/day (patch or oral) is the only FDA-approved agent for PD dementia."
        )
        recommended_agents.append("Rivastigmine for PD dementia (AAN Level A)")

    if len(next_steps) == 0:
        next_steps.append("Movement disorder specialist referral")
        next_steps.append("MDS-UPDRS motor assessment (on and off state)")
        next_steps.append("Neuropsychological screening (MoCA)")
        next_steps.append("Physical, occupational, and speech therapy evaluation")
        next_steps.append("Fall risk assessment")
        next_steps.append("Driving safety evaluation")

    motor_fluctuations_label = (motor_fluctuations or "").replace("_", " ")
    initial_therapy_label = (initial_therapy_history or "").replace("_", " ")

    rationale = (
        f"PD stage: {stage}. "
        f"Age: {data.get('age')}. "
        f"Hoehn-Yahr: {hoehn_yahr_scale}. "
        f"MDS-UPDRS III: {data.get('updrsMotorScore')}. "
        f"Motor fluctuations: {motor_fluctuations_label}. "
        f"Prior therapy: {initial_therapy_label}. "
        f"Hallucinations: {'Yes' if has_hallucinations else 'No'}. "
        f"Dementia: {'Yes' if has_dementia else 'No'}."
    )

    if stage == "early":
        primary_recommendation = (
            f"Early PD: {'dopamine agonist or MAO-B inhibitor as initial therapy (age <65)' if age < 65 else 'levodopa-carbidopa preferred (age ≥65)'}. Optimize symptomatic control."
        )
    elif motor_fluctuations != "none":
        primary_recommendation = (
            f"{_capitalize(stage or '')} PD with {motor_fluctuations_label}: adjunct therapy or device-aided therapy indicated."
        )
    else:
        primary_recommendation = (
            f"{_capitalize(stage or '')} PD: optimize pharmacotherapy and monitor for fluctuations."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "pharmacotherapy": pharmacotherapy,
        "dbsAssessment": dbs_assessment,
        "nonMotorManagement": non_motor_management,
        "recommendedAgents": recommended_agents,
        "agentsToAvoid": agents_to_avoid,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }
