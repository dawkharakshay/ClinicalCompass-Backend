"""Age-Related Macular Degeneration (AMD) recommendation engine.

Ported 1:1 from old_static_code/client/src/lib/amdLogic.ts (assessAMD).

Based on: AAO 2024 Preferred Practice Pattern (PPP), AREDS2 formulation,
CATT, HARBOR, TENAYA/LUCERNE, PULSAR, PHOTON trials.
"""

from __future__ import annotations

LOGIC_KEY = "amd"

_REFERENCES = [
    {
        "citation": "AREDS2 Research Group. Lutein + zeaxanthin and omega-3 fatty acids for age-related macular degeneration. JAMA. 2013;309(19):2005-2015.",
        "pmid": "23644932",
        "url": "https://pubmed.ncbi.nlm.nih.gov/23644932/",
    },
    {
        "citation": "CATT Research Group. Ranibizumab and Bevacizumab for Neovascular Age-Related Macular Degeneration. N Engl J Med. 2011;364(20):1897-1908.",
        "pmid": "21526923",
        "url": "https://pubmed.ncbi.nlm.nih.gov/21526923/",
    },
    {
        "citation": "Heier JS, et al. Intravitreal Aflibercept (VEGF Trap-Eye) in Wet Age-related Macular Degeneration. Ophthalmology. 2012;119(12):2537-2548.",
        "pmid": "23084240",
        "url": "https://pubmed.ncbi.nlm.nih.gov/23084240/",
    },
    {
        "citation": "Khanani AM, et al. Efficacy and durability of faricimab with extended dosing up to every 16 weeks in patients with neovascular AMD (TENAYA and LUCERNE). Lancet. 2022;399(10326):729-740.",
        "pmid": "35085503",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35085503/",
    },
    {
        "citation": "Liao DS, et al. Complement C3 Inhibitor Pegcetacoplan for Geographic Atrophy Secondary to Age-Related Macular Degeneration (OAKS). Ophthalmology. 2023;130(1):11-21.",
        "pmid": "36058317",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36058317/",
    },
    {
        "citation": "AAO Preferred Practice Pattern: Age-Related Macular Degeneration. American Academy of Ophthalmology. 2024.",
        "url": "https://www.aao.org/preferred-practice-pattern/age-related-macular-degeneration-ppp",
    },
]


def assess(data: dict) -> dict:
    stage = data.get("stage")
    cnv_type = data.get("cnvType")
    visual_acuity = data.get("visualAcuity")
    anti_vegf_history = data.get("antiVEGFHistory")
    has_geographic_atrophy = bool(data.get("hasGeographicAtrophy"))
    has_pcv_or_rap = bool(data.get("hasPCVorRAP"))
    is_on_areds2 = bool(data.get("isOnAREDS2Supplements"))
    smoking_status = data.get("smokingStatus")

    urgent_flags: list[str] = []
    next_steps: list[str] = []
    recommended_agents: list[str] = []

    # Urgent flags
    if stage == "advanced_wet" and anti_vegf_history == "none":
        urgent_flags.append(
            "NEW WET AMD: urgent anti-VEGF injection required — delay worsens prognosis. Initiate within 1–2 weeks of diagnosis."
        )
    if smoking_status == "current":
        urgent_flags.append(
            "Active smoking significantly accelerates AMD progression — smoking cessation counseling is mandatory"
        )
    if visual_acuity == "count_fingers_or_worse" and stage == "advanced_wet":
        urgent_flags.append(
            "Very poor VA (CF or worse): prognosis for visual recovery is limited but treatment may stabilize or modestly improve vision — do not withhold anti-VEGF"
        )

    # Supplement recommendation
    if stage == "early":
        supplement_recommendation = (
            "Early AMD: AREDS2 supplements NOT indicated (insufficient evidence for early AMD). "
            "Dietary counseling: Mediterranean diet, leafy greens (lutein/zeaxanthin), omega-3 fatty acids. "
            "Smoking cessation if applicable."
        )
    elif stage in ("intermediate", "advanced_dry", "advanced_wet"):
        supplement_recommendation = (
            "AREDS2 formula RECOMMENDED (AREDS2 trial, 2013): reduces risk of progression to advanced AMD by 25%. "
            "Formulation: Vitamin C 500mg + Vitamin E 400 IU + Lutein 10mg + Zeaxanthin 2mg + Zinc 80mg + Copper 2mg. "
            "Note: Beta-carotene REMOVED from AREDS2 (increases lung cancer risk in smokers). "
            "Use zinc 25mg formulation if GI intolerance to 80mg zinc."
        )
        if not is_on_areds2:
            urgent_flags.append(
                "AREDS2 supplements not yet initiated — strongly recommended for intermediate/advanced AMD"
            )
    else:
        supplement_recommendation = (
            "No AMD identified: routine dietary counseling. AREDS2 supplements not indicated."
        )

    # Anti-VEGF selection
    anti_vegf_selection = ""
    treatment_strategy = ""

    if stage == "advanced_wet":
        if anti_vegf_history in ("none", "on_bevacizumab"):
            anti_vegf_selection = (
                "First-line anti-VEGF options (all FDA-approved, similar efficacy per CATT trial): "
                "1) Faricimab (Vabysmo) 6mg — dual VEGF-A/Ang-2 inhibitor; TENAYA/LUCERNE trials show extended dosing (up to Q16W in ~45% of patients). PREFERRED for extended interval potential. "
                "2) Aflibercept (Eylea) 2mg Q4W x3, then Q8W — HARBOR trial. High-dose aflibercept 8mg (Eylea HD) approved 2023 — PULSAR trial shows Q12–16W dosing. "
                "3) Ranibizumab (Lucentis) 0.5mg — MARINA/ANCHOR trials. Monthly dosing. "
                "4) Bevacizumab (Avastin) — off-label, similar efficacy to ranibizumab (CATT), lower cost. "
                "5) Brolucizumab (Beovu) 6mg — Q12W after loading; risk of intraocular inflammation/vasculitis — use with caution."
            )
            recommended_agents.extend(
                [
                    "Faricimab 6mg IVT (preferred — extended interval)",
                    "Aflibercept 8mg IVT (Eylea HD — extended interval)",
                    "Aflibercept 2mg IVT (Q4W x3, then Q8W)",
                    "Ranibizumab 0.5mg IVT monthly",
                ]
            )
        elif anti_vegf_history == "suboptimal_response":
            anti_vegf_selection = (
                "Suboptimal anti-VEGF response: switch to a different anti-VEGF agent. "
                "If on ranibizumab/bevacizumab → switch to aflibercept or faricimab (different receptor binding). "
                "If on aflibercept → switch to faricimab (dual mechanism — VEGF-A + Ang-2). "
                "Persistent subretinal fluid may be tolerated if intraretinal fluid is resolved. "
                "Ensure adequate dosing frequency before declaring treatment failure."
            )
            recommended_agents.extend(
                [
                    "Faricimab 6mg (switch — dual VEGF-A/Ang-2)",
                    "Aflibercept 8mg HD (switch from lower-dose agents)",
                ]
            )
        else:
            current_agent = str(anti_vegf_history).replace("on_", "").replace("_", " ")
            anti_vegf_selection = (
                f"Currently on {current_agent}: "
                "Assess treatment response at each visit (VA, OCT fluid). "
                "Treat-and-extend protocol: extend interval by 2 weeks if dry at visit; shorten by 2 weeks if fluid recurs. "
                "Target maximum dry interval (Q12–16W for faricimab/aflibercept HD, Q8–12W for aflibercept 2mg)."
            )

        if has_pcv_or_rap:
            anti_vegf_selection += (
                " PCV/RAP subtype: photodynamic therapy (PDT) + anti-VEGF combination may be considered for PCV (EVEREST II trial). "
                "Faricimab and aflibercept are effective for RAP lesions."
            )

        treatment_strategy = (
            "Loading phase: 3 monthly injections, then reassess. Treat-and-extend thereafter based on OCT fluid response."
            if anti_vegf_history == "none"
            else "Treat-and-extend: adjust interval based on OCT fluid status at each visit. Target longest dry interval."
        )

        next_steps.extend(
            [
                "OCT macula at each visit (assess intraretinal and subretinal fluid)",
                "Fluorescein angiography (FA) + OCTA at baseline to characterize CNV type",
                "Best-corrected visual acuity at each visit",
                "Contralateral eye monitoring (OCT annually if intermediate AMD)",
            ]
        )
    elif stage == "advanced_dry" and has_geographic_atrophy:
        anti_vegf_selection = (
            "Geographic atrophy (GA): two complement inhibitors FDA-approved (2023): "
            "1) Pegcetacoplan (Syfovre) 15mg IVT Q25–60 days — C3 inhibitor; OAKS/DERBY trials show 22% reduction in GA growth rate. "
            "2) Avacincaptad pegol (Izervay) 2mg IVT monthly — C5 inhibitor; GATHER1/GATHER2 trials show 14–18% reduction in GA growth rate. "
            "Neither restores lost vision — goal is to slow progression. "
            "Discuss realistic expectations with patient. Consider for GA area ≥2.5mm² outside fovea."
        )
        recommended_agents.extend(
            [
                "Pegcetacoplan (Syfovre) 15mg IVT Q25–60 days",
                "Avacincaptad pegol (Izervay) 2mg IVT monthly",
            ]
        )
        treatment_strategy = (
            "GA treatment: complement inhibitor to slow progression. Baseline FA/OCTA to exclude occult CNV."
        )
        next_steps.extend(
            [
                "FA/OCTA to exclude concurrent CNV",
                "Fundus autofluorescence (FAF) to map GA area",
                "Baseline OCT for GA area measurement",
                "Discuss realistic expectations — no vision restoration",
            ]
        )
    elif stage == "intermediate":
        treatment_strategy = (
            "Intermediate AMD: AREDS2 supplements, smoking cessation, monitoring. No treatment beyond supplements currently indicated."
        )
        anti_vegf_selection = "Anti-VEGF not indicated for intermediate AMD without CNV."
        next_steps.extend(
            [
                "OCT macula every 6–12 months",
                "Amsler grid home monitoring (daily)",
                "Instruct patient to report any sudden vision change, metamorphopsia, or new scotoma immediately",
            ]
        )
    else:
        treatment_strategy = (
            "Early AMD or no AMD: observation, lifestyle modification, and dietary counseling."
        )
        anti_vegf_selection = "Anti-VEGF not indicated."
        next_steps.extend(
            [
                "Annual dilated fundus exam",
                "Amsler grid home monitoring",
                "Dietary counseling (Mediterranean diet, leafy greens)",
            ]
        )

    # Monitoring plan
    if stage == "advanced_wet":
        monitoring_plan = (
            "Active nAMD: OCT + VA at every injection visit. "
            "FA/OCTA annually or when CNV activity changes. "
            "Contralateral eye: OCT annually (high risk for conversion to nAMD — 10-year risk ~40% if fellow eye has advanced AMD)."
        )
    elif stage == "intermediate":
        monitoring_plan = (
            "Intermediate AMD: OCT macula every 6–12 months. Amsler grid daily at home. "
            "Educate patient: any sudden change in vision, metamorphopsia, or new scotoma requires urgent evaluation within 24–48 hours."
        )
    else:
        monitoring_plan = "Annual dilated fundus exam. Amsler grid monitoring at home."

    rationale = (
        f"AMD stage: {str(stage).replace('_', ' ')}. "
        f"CNV type: {str(cnv_type).replace('_', ' ')}. "
        f"Visual acuity: {str(visual_acuity).replace('_', ' ')}. "
        f"Anti-VEGF history: {str(anti_vegf_history).replace('_', ' ')}. "
        f"Geographic atrophy: {'Yes' if has_geographic_atrophy else 'No'}. "
        f"Smoking: {smoking_status}. "
        f"AREDS2: {'Yes' if is_on_areds2 else 'No'}."
    )

    if stage == "advanced_wet":
        primary_recommendation = (
            "Neovascular AMD: anti-VEGF therapy indicated. "
            + (
                "Urgent initiation recommended."
                if anti_vegf_history == "none"
                else "Continue/optimize current regimen."
            )
        )
    elif stage == "advanced_dry":
        primary_recommendation = (
            "Geographic atrophy: complement inhibitor therapy available to slow progression. AREDS2 supplements mandatory."
        )
    elif stage == "intermediate":
        primary_recommendation = (
            "Intermediate AMD: AREDS2 supplements recommended. Close monitoring for conversion to advanced AMD."
        )
    else:
        primary_recommendation = (
            "Early AMD: lifestyle modification and annual monitoring. AREDS2 supplements not yet indicated."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "treatmentStrategy": treatment_strategy,
        "antiVEGFSelection": anti_vegf_selection,
        "supplementRecommendation": supplement_recommendation,
        "monitoringPlan": monitoring_plan,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }
