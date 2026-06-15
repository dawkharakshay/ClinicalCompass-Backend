"""Psoriasis Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/psoriasisLogic.ts
(assessPsoriasis).

Based on:
- AAD-NPF 2019/2026 Joint Guidelines of Care for Psoriasis with Biologics
  (PMID: 30772097)
- AAD-NPF 2026 Update: TYK2 inhibitors, IL-23 evolution, treat-to-target
- Translating 2019 AAD-NPF Guidelines to Clinical Practice (PMID: 31634385)
- PASI/BSA/DLQI severity framework (IPC criteria)
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num, to_bool

LOGIC_KEY = "psoriasis"

_REFERENCES = [
    {
        "citation": (
            "Joint AAD-NPF Guidelines of Care for the Management and Treatment of "
            "Psoriasis with Biologics — Menter A et al., JAAD 2019"
        ),
        "pmid": "30772097",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30772097/",
    },
    {
        "citation": (
            "Translating the 2019 AAD-NPF Guidelines of Care for Psoriasis with "
            "Biologics to Clinical Practice — Armstrong AW et al., JAAD 2020"
        ),
        "pmid": "31634385",
        "url": "https://pubmed.ncbi.nlm.nih.gov/31634385/",
    },
    {
        "citation": (
            "Deucravacitinib vs Placebo and Apremilast in Moderate-to-Severe "
            "Plaque Psoriasis — Armstrong AW et al., NEJM 2023"
        ),
        "pmid": "36720134",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36720134/",
    },
    {
        "citation": "Bimekizumab vs Secukinumab in Plaque Psoriasis — Reich K et al., NEJM 2021",
        "pmid": "34161699",
        "url": "https://pubmed.ncbi.nlm.nih.gov/34161699/",
    },
    {
        "citation": (
            "Risankizumab vs Ustekinumab for Moderate-to-Severe Plaque "
            "Psoriasis — Gordon KB et al., Lancet 2018"
        ),
        "pmid": "29961678",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29961678/",
    },
]


def _classify_severity(bsa_percent, dlqi, pga_score, subtype, special_sites, has_psa):
    # Rule of Tens: BSA >10, PASI >10, or DLQI >10 = severe
    # Special sites always qualify for systemic therapy regardless of BSA
    has_special_site = (
        includes(special_sites, "palmoplantar")
        or includes(special_sites, "nails")
        or includes(special_sites, "genitalia")
        or has_psa
    )

    if subtype == "erythrodermic" or subtype == "pustular_generalized":
        return "severe"

    if bsa_percent > 10 or dlqi > 10 or pga_score >= 4:
        return "severe"

    if bsa_percent >= 3 or dlqi >= 6 or pga_score == 3 or has_special_site:
        return "moderate"

    return "mild"


def assess(data: dict) -> dict:
    bsa_percent = num(data.get("bsaPercent"), 0)
    dlqi = num(data.get("dlqi"), 0)
    pga_score = num(data.get("pgaScore"), 0)

    subtype = data.get("subtype")
    special_sites = data.get("specialSites") or []

    has_psoriatic_arthritis = to_bool(data.get("hasPsoriaticArthritis"))
    has_cardiovascular_disease = to_bool(data.get("hasCardiovascularDisease"))  # noqa: F841 (parity with TS input)
    has_inflammatory_bowel_disease = to_bool(data.get("hasInflammatoryBowelDisease"))
    has_demyelinating_disease = to_bool(data.get("hasDemyelinatingDisease"))
    has_active_tuberculosis = to_bool(data.get("hasActiveTuberculosis"))
    has_chronic_hbv = to_bool(data.get("hasChronicHBV"))
    has_malignancy_history = to_bool(data.get("hasMalignancyHistory"))
    is_pregnant = to_bool(data.get("isPregnant"))

    prefers_oral_therapy = to_bool(data.get("prefersOralTherapy"))
    has_obesity = to_bool(data.get("hasObesity"))
    has_metabolic_syndrome = to_bool(data.get("hasMetabolicSyndrome"))

    severity = _classify_severity(
        bsa_percent, dlqi, pga_score, subtype, special_sites, has_psoriatic_arthritis
    )

    urgent_flags: list[str] = []
    first_line_agents: list[str] = []
    alternative_agents: list[str] = []
    agents_to_avoid: list[str] = []
    special_site_management: list[str] = []
    psoriatic_arthritis_notes: list[str] = []
    next_steps: list[str] = []
    monitoring_plan: list[str] = []
    shared_decision_points: list[str] = []

    # Urgent flags
    if subtype == "erythrodermic":
        urgent_flags.append(
            "URGENT: Erythrodermic psoriasis — hospitalization may be required; "
            "avoid abrupt withdrawal of systemic therapy; cyclosporine or "
            "infliximab for rapid control"
        )
    if subtype == "pustular_generalized":
        urgent_flags.append(
            "URGENT: Generalized pustular psoriasis — systemic therapy required "
            "urgently; cyclosporine or infliximab; biologics (IL-17, IL-23) "
            "emerging as preferred"
        )
    if has_active_tuberculosis:
        urgent_flags.append(
            "ACTIVE TB: All biologics and JAK inhibitors contraindicated until TB "
            "fully treated; consult infectious disease"
        )
    if has_chronic_hbv:
        urgent_flags.append(
            "Chronic HBV: Antiviral prophylaxis required before initiating "
            "biologics; consult hepatology"
        )

    # Contraindications
    if has_inflammatory_bowel_disease:
        agents_to_avoid.append(
            "IL-17 inhibitors (secukinumab, ixekizumab, bimekizumab, brodalumab) "
            "— may worsen IBD"
        )
        agents_to_avoid.append("Brodalumab — IL-17RA blocker; avoid in IBD")
    if has_demyelinating_disease:
        agents_to_avoid.append(
            "TNF inhibitors (etanercept, adalimumab, infliximab, certolizumab) — "
            "contraindicated in demyelinating disease"
        )
    if has_malignancy_history:
        agents_to_avoid.append(
            "TNF inhibitors — avoid in patients with recent malignancy history"
        )
    if is_pregnant:
        agents_to_avoid.append(
            "Acitretin — absolutely contraindicated in pregnancy (teratogenic)"
        )
        agents_to_avoid.append("Methotrexate — contraindicated in pregnancy")
        agents_to_avoid.append(
            "Most biologics — limited safety data; certolizumab has best pregnancy "
            "safety profile"
        )

    primary_recommendation = ""
    treatment_pathway = ""
    evidence_level = ""
    treat_to_target_goal = ""

    if severity == "mild":
        primary_recommendation = (
            "Topical therapy — corticosteroids, vitamin D analogs, and "
            "non-steroidal topicals"
        )
        treatment_pathway = (
            "Step 1: Topical corticosteroids (mid-to-high potency for body; low "
            "potency for face/intertriginous). "
            "Step 2: Vitamin D analogs (calcipotriene, calcitriol) — steroid-sparing; "
            "combine with TCS for additive effect. "
            "Step 3: Fixed-dose calcipotriene + betamethasone dipropionate "
            "(Taclonex/Enstilar) — once-daily convenience. "
            "Step 4: Tazarotene — retinoid; effective for plaques; irritating on "
            "sensitive skin. "
            "Step 5: Roflumilast foam 0.3% (Zoryve) — for scalp and intertriginous "
            "areas. "
            "Step 6: Tapinarof cream 1% — AhR agonist; approved for plaque psoriasis."
        )

        first_line_agents.append(
            "Calcipotriene + betamethasone dipropionate (Taclonex) — fixed-dose "
            "combination; once daily"
        )
        first_line_agents.append("Topical corticosteroids (class II-IV for body plaques)")
        first_line_agents.append(
            "Roflumilast foam 0.3% (Zoryve) — scalp and intertriginous; non-steroidal"
        )
        first_line_agents.append(
            "Tapinarof cream 1% — plaque psoriasis; 'remittive effect' after stopping"
        )
        first_line_agents.append(
            "Calcipotriene 0.005% cream/solution — vitamin D analog; steroid-sparing"
        )

        treat_to_target_goal = "Clear or near-clear (BSA <1%) within 3 months"
        evidence_level = "Strong recommendation (AAD-NPF 2019/2026, Level A)"

    elif severity == "moderate":
        primary_recommendation = (
            "Systemic therapy — biologic preferred over conventional systemic for "
            "moderate-severe plaque psoriasis"
        )
        treatment_pathway = (
            "Step 1: Topical therapy + phototherapy (narrowband UVB) if accessible. "
            "Step 2: Conventional systemic: methotrexate (first-line non-biologic), "
            "apremilast (oral PDE-4i; no lab monitoring). "
            "Step 3: Biologic therapy — IL-23 inhibitors preferred for sustained "
            "efficacy and safety profile. "
            "Step 4: TYK2 inhibitor (deucravacitinib 6mg daily) — oral; "
            "biologic-level efficacy; no immunosuppression boxed warning. "
            "Step 5: IL-17 inhibitors for rapid clearance (bimekizumab, secukinumab, "
            "ixekizumab). "
            "Step 6: TNF inhibitors (adalimumab) — effective but lower efficacy vs "
            "IL-17/IL-23."
        )

        if prefers_oral_therapy:
            first_line_agents.append(
                "Deucravacitinib 6mg daily — TYK2 inhibitor; oral; biologic-level "
                "PASI 75 rates; no boxed warning"
            )
            first_line_agents.append(
                "Apremilast 30mg BID — oral PDE-4 inhibitor; no lab monitoring "
                "required; suitable for mild-moderate"
            )
            first_line_agents.append(
                "Methotrexate 7.5-25mg weekly — conventional systemic; less "
                "effective than biologics"
            )
        else:
            first_line_agents.append(
                "Risankizumab (IL-23 p19) — Q12W maintenance; high PASI 90/100 "
                "rates; AAD-NPF 2026 preferred"
            )
            first_line_agents.append(
                "Guselkumab (IL-23 p19) — Q8W; also approved for psoriatic arthritis"
            )
            first_line_agents.append(
                "Tildrakizumab (IL-23 p19) — Q12W; effective for moderate-severe plaque"
            )
            first_line_agents.append(
                "Bimekizumab (IL-17A/F) — highest PASI 90/100 rates; Q4W then Q8W"
            )
            first_line_agents.append("Secukinumab (IL-17A) — 300mg Q4W; rapid clearance")
            first_line_agents.append(
                "Ixekizumab (IL-17A) — Q4W then Q8W; effective for nails and PsA"
            )

        if has_psoriatic_arthritis:
            psoriatic_arthritis_notes.append(
                "PsA present: IL-17 inhibitors (secukinumab, ixekizumab) and IL-23 "
                "inhibitors (guselkumab, risankizumab) treat both skin and joints"
            )
            psoriatic_arthritis_notes.append(
                "TNF inhibitors (adalimumab, certolizumab) — well-established for "
                "PsA; consider if IBD or CV disease present"
            )
            psoriatic_arthritis_notes.append(
                "Deucravacitinib — approved for both plaque psoriasis and PsA"
            )
            psoriatic_arthritis_notes.append(
                "Rheumatology co-management recommended for PsA"
            )

        treat_to_target_goal = (
            "PASI 90 or BSA <1% within 3 months of starting new therapy (AAD-NPF "
            "treat-to-target)"
        )
        evidence_level = "Strong recommendation (AAD-NPF 2019/2026, Level A)"

    else:
        # Severe
        primary_recommendation = (
            "Biologic therapy — IL-23 or IL-17 inhibitors are preferred first-line "
            "for severe plaque psoriasis"
        )
        treatment_pathway = (
            "Step 1: IL-23 inhibitors (risankizumab, guselkumab, tildrakizumab) — "
            "preferred for sustained remission, Q12W maintenance. "
            "Step 2: IL-17 inhibitors (bimekizumab, secukinumab, ixekizumab) — "
            "fastest clearance; preferred for palmoplantar/nail/PsA. "
            "Step 3: TYK2 inhibitor (deucravacitinib) — oral option with "
            "biologic-level efficacy; no immunosuppression boxed warning. "
            "Step 4: TNF inhibitors (adalimumab, infliximab, certolizumab) — "
            "effective; consider if CV disease or IBD present. "
            "Step 5: Ustekinumab (IL-12/23) — less preferred vs IL-23 selective "
            "agents; approved ≥12 years. "
            "Step 6: Cyclosporine — for rapid control of severe/erythrodermic; "
            "short-term only (≤1 year)."
        )

        if has_inflammatory_bowel_disease:
            first_line_agents.append(
                "IL-23 inhibitors (risankizumab, guselkumab) — safe in IBD; "
                "preferred over IL-17"
            )
            first_line_agents.append(
                "TNF inhibitors (adalimumab, infliximab) — treat both psoriasis and IBD"
            )
        elif has_psoriatic_arthritis:
            first_line_agents.append(
                "Bimekizumab (IL-17A/F) — highest skin clearance + PsA efficacy"
            )
            first_line_agents.append(
                "Secukinumab (IL-17A) — established for both psoriasis and PsA"
            )
            first_line_agents.append(
                "Guselkumab (IL-23 p19) — FDA approved for PsA + psoriasis"
            )
        else:
            first_line_agents.append(
                "Risankizumab (IL-23 p19) — highest PASI 90/100 rates; Q12W "
                "maintenance; preferred AAD-NPF 2026"
            )
            first_line_agents.append(
                "Bimekizumab (IL-17A/F) — fastest clearance; Q4W loading then Q8W"
            )
            first_line_agents.append("Guselkumab (IL-23 p19) — Q8W; approved for PsA")

        if prefers_oral_therapy:
            first_line_agents.append(
                "Deucravacitinib 6mg daily — oral TYK2 inhibitor; PASI 75 rates "
                "comparable to adalimumab; no boxed warning"
            )
            alternative_agents.append(
                "Apremilast — less effective for severe disease; use if biologic "
                "contraindicated"
            )

        alternative_agents.append(
            "Ustekinumab (IL-12/23) — less preferred vs selective IL-23 agents; "
            "approved ≥12 years"
        )
        alternative_agents.append(
            "Adalimumab (TNF) — well-established; preferred if IBD or CV disease"
        )
        alternative_agents.append(
            "Infliximab — fastest TNF response; IV infusion; for erythrodermic/pustular"
        )

        if subtype == "erythrodermic" or subtype == "pustular_generalized":
            first_line_agents.append(
                "Cyclosporine 3-5mg/kg/day — rapid control; bridge to biologic"
            )
            first_line_agents.append(
                "Infliximab 5mg/kg IV — fastest biologic response for "
                "erythrodermic/pustular"
            )

        treat_to_target_goal = (
            "PASI 90 or BSA <1% within 3 months; reassess and switch if PASI 75 not "
            "achieved at 16 weeks"
        )
        evidence_level = "Strong recommendation (AAD-NPF 2019/2026, Level A)"

    # Special site management
    if includes(special_sites, "scalp"):
        special_site_management.append(
            "Scalp: Roflumilast foam 0.3% (Zoryve) — non-steroidal; once daily; "
            "AAD 2026 preferred"
        )
        special_site_management.append(
            "Scalp: Clobetasol propionate shampoo or foam — high-potency TCS for scalp"
        )
        special_site_management.append(
            "Scalp: Calcipotriene + betamethasone dipropionate foam (Enstilar) — "
            "once daily"
        )
    if includes(special_sites, "nails"):
        special_site_management.append(
            "Nails: IL-17 inhibitors (ixekizumab, secukinumab) most effective for "
            "nail psoriasis"
        )
        special_site_management.append(
            "Nails: Intralesional triamcinolone — for isolated nail disease"
        )
        special_site_management.append(
            "Nails: Tazarotene gel under occlusion — topical option"
        )
    if includes(special_sites, "palmoplantar"):
        special_site_management.append(
            "Palmoplantar: IL-17 inhibitors (secukinumab, ixekizumab, bimekizumab) "
            "most effective"
        )
        special_site_management.append(
            "Palmoplantar: Acitretin — consider for pustular palmoplantar; combine "
            "with PUVA"
        )
        special_site_management.append(
            "Palmoplantar: High-potency TCS under occlusion for localized disease"
        )
    if includes(special_sites, "intertriginous") or includes(special_sites, "genitalia"):
        special_site_management.append(
            "Intertriginous/genital: Roflumilast foam 0.3% — non-steroidal; safe "
            "for sensitive areas"
        )
        special_site_management.append(
            "Intertriginous/genital: Low-potency TCS (hydrocortisone 1-2.5%) — "
            "avoid high-potency"
        )
        special_site_management.append(
            "Intertriginous/genital: Tacrolimus ointment 0.1% — off-label but effective"
        )

    # Obesity / metabolic syndrome
    if has_obesity or has_metabolic_syndrome:
        shared_decision_points.append(
            "Obesity: GLP-1 receptor agonists (tirzepatide, semaglutide) may have "
            "immunometabolic synergy in psoriasis — emerging evidence"
        )
        shared_decision_points.append(
            "Ustekinumab: weight-based dosing (>100kg: 90mg; ≤100kg: 45mg) — "
            "consider higher-efficacy agents in obese patients"
        )
        shared_decision_points.append(
            "Weight loss improves psoriasis severity independently — lifestyle "
            "counseling recommended"
        )

    # Monitoring
    monitoring_plan.append(
        "Reassess BSA, PGA, and DLQI at 3 months after initiating new therapy"
    )
    monitoring_plan.append(
        "Treat-to-target: switch therapy if PASI 75 not achieved at 16 weeks"
    )
    monitoring_plan.append(
        "Biologics: TB screening (IGRA/PPD), hepatitis B/C, CBC, LFTs at baseline"
    )
    monitoring_plan.append(
        "Methotrexate: LFTs, CBC, renal function every 4-8 weeks initially"
    )
    monitoring_plan.append(
        "Cyclosporine: BP, renal function, CBC every 2 weeks for first 3 months"
    )
    monitoring_plan.append(
        "Annual cardiovascular risk assessment — psoriasis is an independent CV "
        "risk factor"
    )

    # Next steps
    next_steps.append(
        "Screen for psoriatic arthritis at every visit (PEST or PASE questionnaire)"
    )
    next_steps.append(
        "Assess DLQI — if >10, qualifies for systemic therapy regardless of BSA"
    )
    next_steps.append(
        "Dermatology referral if not responding to topicals or phototherapy"
    )
    next_steps.append(
        "Counsel on cardiovascular risk — psoriasis associated with increased MACE risk"
    )

    shared_decision_points.append(
        "Route of administration: oral (deucravacitinib, apremilast, methotrexate) "
        "vs SC injection (biologics) — patient preference"
    )
    shared_decision_points.append(
        "Dosing frequency: Q12W (risankizumab) vs Q4-8W (IL-17 agents) — adherence "
        "consideration"
    )
    shared_decision_points.append(
        "Prior authorization: biologics require documentation of topical failure "
        "and/or phototherapy failure"
    )
    shared_decision_points.append(
        "Biosimilars available for adalimumab, etanercept, infliximab, ustekinumab "
        "— cost consideration"
    )

    return {
        "severity": severity,
        "primaryRecommendation": primary_recommendation,
        "treatmentPathway": treatment_pathway,
        "firstLineAgents": first_line_agents,
        "alternativeAgents": alternative_agents,
        "agentsToAvoid": agents_to_avoid,
        "specialSiteManagement": special_site_management,
        "psoriaticArthritisNotes": psoriatic_arthritis_notes,
        "monitoringPlan": monitoring_plan,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "treatToTargetGoal": treat_to_target_goal,
        "evidenceLevel": evidence_level,
        "sharedDecisionPoints": shared_decision_points,
        "references": _REFERENCES,
    }
