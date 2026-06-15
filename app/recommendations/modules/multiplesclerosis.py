"""Multiple Sclerosis Clinical Logic Engine.

Ported 1:1 from old_static_code/client/src/lib/multipleSclerosisLogic.ts
(assessMS).

Based on AAN 2025 DMT Guidelines, ECTRIMS/EAN 2023, CMSC 2024.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import parse_float

LOGIC_KEY = "multiplesclerosis"

_REFERENCES = [
    {
        "citation": "Rae-Grant A, et al. Practice guideline recommendations summary: Disease-modifying therapies for adults with multiple sclerosis. Neurology. 2018;90(17):777-788.",
        "pmid": "29686116",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29686116/",
    },
    {
        "citation": "Montalban X, et al. ECTRIMS/EAN guideline on the pharmacological treatment of people with multiple sclerosis. Eur J Neurol. 2018;25(2):215-237.",
        "pmid": "29352526",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29352526/",
    },
    {
        "citation": "Hauser SL, et al. Ofatumumab versus Teriflunomide in Multiple Sclerosis. N Engl J Med. 2020;383(6):546-557.",
        "pmid": "32757523",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32757523/",
    },
    {
        "citation": "Montalban X, et al. Ocrelizumab versus Placebo in Primary Progressive Multiple Sclerosis. N Engl J Med. 2017;376(3):209-220.",
        "pmid": "28002688",
        "url": "https://pubmed.ncbi.nlm.nih.gov/28002688/",
    },
    {
        "citation": "AAN 2025 Multiple Sclerosis DMT Guideline Update. American Academy of Neurology.",
        "url": "https://www.aan.com/Guidelines/",
    },
    {
        "citation": "Kappos L, et al. Siponimod versus placebo in secondary progressive multiple sclerosis (EXPAND). Lancet. 2018;391(10127):1263-1273.",
        "pmid": "29576505",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29576505/",
    },
]


def _numf(value: object) -> float:
    """parseFloat-style coercion preserving a literal 0 (NaN -> 0)."""
    v = parse_float(value)
    return 0.0 if math.isnan(v) else v


def _replace_underscores(s: object) -> str:
    return str(s).replace("_", " ")


def assess(data: dict) -> dict:
    ms_type = data.get("msType")
    disease_course = data.get("diseaseCourse")
    relapse_count = _numf(data.get("relapseCountPast2Years"))
    new_t2_lesions = _numf(data.get("newT2LesionsPast12Months"))
    gad_enhancing = _numf(data.get("gadEnhancingLesions"))
    edss_score = data.get("edssScore")
    prior_dmt = data.get("priorDMT")
    jcv_status = data.get("jcvStatus")
    is_pregnant = bool(data.get("isPregnantOrPlanning"))
    has_cardiac = bool(data.get("hasCardiacHistory"))
    has_active_malignancy = bool(data.get("hasActiveMalignancy"))
    wants_high_efficacy = bool(data.get("wantsHighEfficacyFirstLine"))

    urgent_flags: list[str] = []
    agents_to_avoid: list[str] = []
    monitoring_requirements: list[str] = []
    recommended_agents: list[str] = []
    next_steps: list[str] = []

    # Absolute contraindications
    if has_active_malignancy:
        urgent_flags.append(
            "Active malignancy: most DMTs contraindicated — consult neuro-oncology before initiating"
        )
        agents_to_avoid.extend(["Alemtuzumab", "Cladribine", "Natalizumab"])

    # Pregnancy
    pregnancy_considerations = "No pregnancy-specific restrictions identified."
    if is_pregnant:
        pregnancy_considerations = (
            "Pregnancy planning: glatiramer acetate and IFN-beta are safest options (Category B/limited data). "
            "Natalizumab may be continued through 34 weeks with close monitoring. "
            "S1P modulators, cladribine, alemtuzumab, teriflunomide are CONTRAINDICATED — require washout. "
            "Ocrelizumab: limited data, generally held 6 months before conception."
        )
        agents_to_avoid.extend(
            [
                "Teriflunomide (teratogenic)",
                "Cladribine (teratogenic)",
                "Alemtuzumab (limited data)",
                "S1P modulators (teratogenic)",
            ]
        )
        urgent_flags.append(
            "Pregnancy/planning: review DMT safety profile urgently with MS specialist"
        )

    # Cardiac history — S1P modulators
    if has_cardiac:
        urgent_flags.append(
            "Cardiac history: S1P modulators (fingolimod, siponimod, ozanimod, ponesimod) require cardiology clearance — first-dose monitoring mandatory"
        )
        agents_to_avoid.append("S1P modulators without cardiology clearance")

    # JC virus / PML risk
    pml_risk_assessment = "PML risk: low (JCV negative or not on natalizumab)."
    if prior_dmt == "natalizumab" or jcv_status != "negative":
        if jcv_status == "positive_high" and _numf(data.get("jcvIndexValue")) > 1.5:
            pml_risk_assessment = (
                "HIGH PML RISK: JCV index >1.5 on natalizumab — risk >1:100 after 24 months. "
                "Strongly consider switching to anti-CD20 (ocrelizumab/ofatumumab) or cladribine. "
                "MRI surveillance every 3–4 months if continuing natalizumab."
            )
            urgent_flags.append(
                "JCV index >1.5: HIGH PML risk — discuss switching strategy urgently"
            )
        elif jcv_status == "positive_low":
            pml_risk_assessment = (
                "Moderate PML risk: JCV positive, index ≤1.5. Annual MRI surveillance. "
                "Reassess index every 6 months. Risk increases significantly if index rises >1.5."
            )
        elif jcv_status == "unknown":
            pml_risk_assessment = (
                "JCV status unknown: test before initiating natalizumab. "
                "If already on natalizumab, test immediately."
            )

    # Determine efficacy tier and agents based on MS type and disease course
    primary_recommendation = ""
    efficacy_tier = "moderate"

    if ms_type == "radiologically_isolated" or ms_type == "cis":
        if new_t2_lesions >= 2 or gad_enhancing >= 1:
            primary_recommendation = (
                "CIS/RIS with high-risk features (≥2 T2 lesions or Gad+ lesions): initiate DMT to delay conversion to clinically definite MS (AAN Level A)."
            )
            efficacy_tier = "moderate"
            recommended_agents.extend(
                [
                    "Interferon beta-1a/1b",
                    "Glatiramer acetate",
                    "Dimethyl fumarate",
                    "Teriflunomide",
                ]
            )
            next_steps.extend(
                [
                    "MRI brain + spine with contrast at baseline",
                    "Confirm McDonald 2017 criteria",
                    "Discuss DMT initiation with patient",
                ]
            )
        else:
            primary_recommendation = (
                "CIS/RIS with low-risk features: observation vs. low-efficacy DMT — shared decision-making. Annual MRI surveillance."
            )
            efficacy_tier = "moderate"
            recommended_agents.extend(
                [
                    "Observation with annual MRI",
                    "Interferon beta (if patient prefers treatment)",
                ]
            )
            next_steps.extend(
                [
                    "Annual MRI brain + spine",
                    "Repeat clinical assessment every 6 months",
                ]
            )
    elif ms_type == "ppms":
        primary_recommendation = (
            "PPMS: Ocrelizumab is the only FDA-approved DMT (ORATORIO trial, 2017). Indicated for adults with active PPMS (Gad+ lesions or new T2 lesions). "
            "BTK inhibitors (tolebrutinib, fenebrutinib) in Phase 3 trials — not yet approved."
        )
        efficacy_tier = "high"
        recommended_agents.append("Ocrelizumab 600mg IV every 6 months")
        monitoring_requirements.extend(
            [
                "Hepatitis B screening before initiation",
                "CBC before each infusion",
                "Infusion reaction monitoring",
            ]
        )
        next_steps.extend(
            [
                "Confirm active PPMS (Gad+ or new T2 lesions in past year)",
                "Hepatitis B serology",
                "Ocrelizumab REMS enrollment",
            ]
        )
    elif ms_type == "spms_inactive":
        primary_recommendation = (
            "Non-active SPMS: no DMT has demonstrated benefit in non-active SPMS. Symptomatic management and rehabilitation are priorities. "
            "Siponimod approved for active SPMS only."
        )
        efficacy_tier = "moderate"
        recommended_agents.extend(
            [
                "Symptomatic management (spasticity, fatigue, bladder)",
                "Physical/occupational therapy",
            ]
        )
        next_steps.extend(
            [
                "Annual MRI to reassess for activity",
                "Symptomatic therapy optimization",
                "Rehabilitation referral",
            ]
        )
    else:
        # RRMS or active SPMS
        if (
            disease_course == "rapidly_evolving"
            or relapse_count >= 2
            or gad_enhancing >= 2
            or wants_high_efficacy
        ):
            # High/very high efficacy
            if prior_dmt == "natalizumab" or prior_dmt == "fingolimod_siponimod":
                # Escalation after moderate-high efficacy failure
                primary_recommendation = (
                    "Highly active RRMS with prior moderate-high efficacy DMT failure: escalate to very high efficacy — "
                    "anti-CD20 therapy (ocrelizumab/ofatumumab) preferred. Alemtuzumab or cladribine as alternatives. "
                    "BTK inhibitors (tolebrutinib) emerging — Phase 3 data expected 2025–2026."
                )
                efficacy_tier = "very_high"
                recommended_agents.extend(
                    [
                        "Ocrelizumab 600mg IV q6m",
                        "Ofatumumab 20mg SC monthly",
                        "Cladribine (2 annual courses)",
                        "Alemtuzumab (if above not tolerated)",
                    ]
                )
                monitoring_requirements.extend(
                    [
                        "CBC with differential",
                        "Hepatitis B/C serology",
                        "Immunoglobulin levels (anti-CD20)",
                        "Thyroid function (alemtuzumab)",
                    ]
                )
            elif prior_dmt == "none" and wants_high_efficacy:
                primary_recommendation = (
                    "Highly active RRMS, treatment-naive, high-efficacy first-line preferred: "
                    "Anti-CD20 (ocrelizumab/ofatumumab) or natalizumab (if JCV negative) are first-line high-efficacy options. "
                    "AAN 2025 supports early high-efficacy therapy in highly active disease."
                )
                efficacy_tier = "high"
                if jcv_status == "negative":
                    recommended_agents.extend(
                        [
                            "Natalizumab 300mg IV monthly",
                            "Ocrelizumab 600mg IV q6m",
                            "Ofatumumab 20mg SC monthly",
                        ]
                    )
                else:
                    recommended_agents.extend(
                        [
                            "Ocrelizumab 600mg IV q6m",
                            "Ofatumumab 20mg SC monthly",
                        ]
                    )
                    agents_to_avoid.append("Natalizumab (JCV positive — PML risk)")
                monitoring_requirements.extend(
                    [
                        "JCV antibody index every 6 months (if on natalizumab)",
                        "MRI brain + spine at 6 and 12 months",
                        "CBC before each anti-CD20 infusion",
                    ]
                )
            else:
                primary_recommendation = (
                    "Highly active RRMS: high-efficacy DMT recommended. "
                    "Natalizumab (JCV negative), ocrelizumab, or ofatumumab preferred. "
                    "Cladribine or alemtuzumab for patients who fail or cannot tolerate anti-CD20."
                )
                efficacy_tier = "high"
                if jcv_status == "negative":
                    recommended_agents.extend(
                        [
                            "Natalizumab 300mg IV monthly",
                            "Ocrelizumab 600mg IV q6m",
                            "Ofatumumab 20mg SC monthly",
                        ]
                    )
                else:
                    recommended_agents.extend(
                        [
                            "Ocrelizumab 600mg IV q6m",
                            "Ofatumumab 20mg SC monthly",
                        ]
                    )
                monitoring_requirements.extend(
                    [
                        "MRI at 6 and 12 months",
                        "JCV index every 6 months (natalizumab)",
                        "CBC before infusions",
                    ]
                )
        elif disease_course == "mild_moderate":
            if prior_dmt == "none":
                primary_recommendation = (
                    "Mild-moderate RRMS, treatment-naive: moderate-efficacy DMT as first-line. "
                    "Dimethyl fumarate, teriflunomide, or S1P modulators (ozanimod, siponimod) are reasonable options. "
                    "Platform therapy (IFN-beta, glatiramer) remains appropriate for patients preferring injectable therapy."
                )
                efficacy_tier = "moderate"
                recommended_agents.extend(
                    [
                        "Dimethyl fumarate 240mg BID",
                        "Teriflunomide 14mg daily",
                        "Ozanimod 0.92mg daily",
                        "Siponimod 2mg daily (CYP2C9 genotyping required)",
                    ]
                )
                if not has_cardiac:
                    recommended_agents.append(
                        "Fingolimod 0.5mg daily (first-dose monitoring required)"
                    )
                monitoring_requirements.extend(
                    [
                        "CBC, LFTs at baseline and 3–6 months (dimethyl fumarate)",
                        "Ophthalmology exam (S1P modulators — macular edema)",
                        "CYP2C9 genotyping before siponimod",
                    ]
                )
            else:
                primary_recommendation = (
                    "Mild-moderate RRMS with prior platform therapy failure: switch to moderate-high efficacy oral agent or consider escalation. "
                    "Dimethyl fumarate, teriflunomide, or S1P modulator if not previously tried. "
                    "If ≥1 relapse or new MRI activity on moderate-efficacy therapy, escalate to high-efficacy."
                )
                efficacy_tier = "moderate"
                recommended_agents.extend(
                    [
                        "Dimethyl fumarate",
                        "Teriflunomide",
                        "Ozanimod",
                        "Siponimod",
                    ]
                )
                next_steps.extend(
                    [
                        "Reassess MRI activity at 6 months",
                        "If breakthrough activity, escalate to high-efficacy DMT",
                    ]
                )
        else:
            # highly_active
            primary_recommendation = (
                "Highly active RRMS: high-efficacy DMT recommended. "
                "Natalizumab (JCV negative), ocrelizumab, or ofatumumab preferred per AAN 2025."
            )
            efficacy_tier = "high"
            if jcv_status == "negative":
                recommended_agents.extend(
                    [
                        "Natalizumab 300mg IV monthly",
                        "Ocrelizumab 600mg IV q6m",
                        "Ofatumumab 20mg SC monthly",
                    ]
                )
            else:
                recommended_agents.extend(
                    [
                        "Ocrelizumab 600mg IV q6m",
                        "Ofatumumab 20mg SC monthly",
                    ]
                )
            monitoring_requirements.extend(
                [
                    "MRI at 6 and 12 months",
                    "JCV index every 6 months (natalizumab)",
                    "CBC before infusions",
                ]
            )

    # Standard monitoring additions
    if any("Ocrelizumab" in a or "Ofatumumab" in a for a in recommended_agents):
        monitoring_requirements.extend(
            [
                "Hepatitis B serology before initiation",
                "Immunoglobulin levels annually",
                "COVID-19 vaccination before initiation",
            ]
        )

    # Next steps defaults
    if len(next_steps) == 0:
        next_steps.extend(
            [
                "Baseline MRI brain + spine with contrast",
                "Complete blood count, comprehensive metabolic panel, LFTs",
                "Hepatitis B/C, HIV serology",
                "Discuss DMT options, efficacy tiers, and side effect profiles with patient",
                "Refer to MS specialist if not already under care",
            ]
        )

    rationale = (
        f"MS type: {_replace_underscores(ms_type).upper()}. "
        f"Disease course: {_replace_underscores(disease_course)}. "
        f"Relapses in past 2 years: {data.get('relapseCountPast2Years')}. "
        f"Gad+ lesions: {data.get('gadEnhancingLesions')}. "
        f"EDSS: {edss_score}. "
        f"Prior DMT: {_replace_underscores(prior_dmt)}. "
        f"JCV status: {_replace_underscores(jcv_status)}."
    )

    return {
        "primaryRecommendation": primary_recommendation,
        "efficacyTier": efficacy_tier,
        "recommendedAgents": recommended_agents,
        "agentsToAvoid": agents_to_avoid,
        "monitoringRequirements": monitoring_requirements,
        "urgentFlags": urgent_flags,
        "pregnancyConsiderations": pregnancy_considerations,
        "pmlRiskAssessment": pml_risk_assessment,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }
