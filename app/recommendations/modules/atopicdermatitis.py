"""Atopic Dermatitis Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/atopicDermatitisLogic.ts
(assessAtopicDermatitis).

Based on:
- AAD 2025 Focused Update: Tapinarof, Roflumilast, Lebrikizumab, Nemolizumab
  (PMID: 40531067)
- AAD 2023 Guidelines: Phototherapy and Systemic Therapies
  (PMID: 37943241, PMID: 38108679)
- AAD 2026 Systemic Therapy Refinement (JAK inhibitors vs biologics)
- SOLO 1 & SOLO 2 Dupilumab Trials (PMID: 27760005)
- Dupilumab in ages 6-12 (PMID: 33007469)
"""

from __future__ import annotations

from app.recommendations.jslib import intnum, num, to_bool

LOGIC_KEY = "atopicdermatitis"

_REFERENCES = [
    {
        "citation": "AAD 2025 Focused Update: Tapinarof, Roflumilast, Lebrikizumab, Nemolizumab for Atopic Dermatitis",
        "pmid": "40531067",
        "url": "https://pubmed.ncbi.nlm.nih.gov/40531067/",
    },
    {
        "citation": "AAD 2023 Guidelines: Phototherapy and Systemic Therapies for AD",
        "pmid": "37943241",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37943241/",
    },
    {
        "citation": "AAD 2023 Guidelines: Systemic Therapies Part 2",
        "pmid": "38108679",
        "url": "https://pubmed.ncbi.nlm.nih.gov/38108679/",
    },
    {
        "citation": "Dupilumab SOLO 1 & SOLO 2 Trials — Simpson EL et al., NEJM 2016",
        "pmid": "27760005",
        "url": "https://pubmed.ncbi.nlm.nih.gov/27760005/",
    },
    {
        "citation": "Dupilumab in Patients Aged 6-12 Years — Cork MJ et al., NEJM 2021",
        "pmid": "33007469",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33007469/",
    },
    {
        "citation": "AAD 2023 Guidelines Highlights — Silverberg JI et al.",
        "pmid": "39251015",
        "url": "https://pubmed.ncbi.nlm.nih.gov/39251015/",
    },
]


def _classify_severity(iga_score: int, easi_score: float) -> str:
    # IGA-based primary classification
    if iga_score <= 1:
        return "mild"
    if iga_score == 2:
        return "mild"
    if iga_score == 3:
        return "moderate"
    if iga_score == 4:
        return "severe"

    # EASI-based fallback
    if easi_score < 7:
        return "mild"
    if easi_score < 21:
        return "moderate"
    return "severe"


def assess(data: dict) -> dict:
    iga_score = intnum(data.get("igaScore"), 0)
    easi_score = num(data.get("easiScore"), 0)
    bsa_percent = num(data.get("bsaPercent"), 0)  # noqa: F841 (parity with TS input)
    pruritus_nrs = num(data.get("pruritusNrs"), 0)

    age_group = data.get("ageGroup")
    failed_therapy = data.get("failedTherapy")

    has_ocular_disease = to_bool(data.get("hasOcularDisease"))
    has_cardiovascular_risk = to_bool(data.get("hasCardiovascularRisk"))
    has_thromboembolism_history = to_bool(data.get("hasThromboembolismHistory"))
    has_malignancy_history = to_bool(data.get("hasMalignancyHistory"))
    is_pregnant_or_planning = to_bool(data.get("isPregnantOrPlanning"))
    has_significant_pruritus = to_bool(data.get("hasSignificantPruritus"))
    has_eczema_herpeticum = to_bool(data.get("hasEczemaHerpeticum"))
    has_bacterial_superinfection = to_bool(data.get("hasBacterialSuperinfection"))

    severity = _classify_severity(iga_score, easi_score)

    urgent_flags: list[str] = []
    specific_agents: list[str] = []
    agents_to_avoid: list[str] = []
    next_steps: list[str] = []
    monitoring_plan: list[str] = []
    shared_decision_points: list[str] = []

    # Urgent flags
    if has_eczema_herpeticum:
        urgent_flags.append(
            "URGENT: Eczema herpeticum suspected — initiate systemic acyclovir/valacyclovir immediately before advancing AD therapy"
        )
    if has_bacterial_superinfection:
        urgent_flags.append(
            "URGENT: Bacterial superinfection (S. aureus) — treat with appropriate antibiotics before escalating AD therapy"
        )

    # Contraindication flags
    if has_cardiovascular_risk or has_thromboembolism_history or has_malignancy_history:
        agents_to_avoid.append(
            "JAK inhibitors (upadacitinib, abrocitinib, baricitinib) — FDA Boxed Warning: increased risk of MACE, thromboembolism, and malignancy"
        )
    if is_pregnant_or_planning:
        agents_to_avoid.append("JAK inhibitors — contraindicated in pregnancy")
        agents_to_avoid.append(
            "Systemic immunosuppressants (cyclosporine, methotrexate) — teratogenic"
        )
        shared_decision_points.append(
            "Dupilumab has the most safety data in pregnancy; discuss risk-benefit with patient"
        )

    primary_recommendation = ""
    treatment_pathway = ""
    evidence_level = ""

    if severity == "mild":
        primary_recommendation = "Topical therapy with non-steroidal agents preferred for long-term management"
        treatment_pathway = (
            "Step 1: Optimize skincare baseline (fragrance-free emollients, lukewarm bathing, trigger avoidance). "
            "Step 2: Topical corticosteroids (TCS) for acute flares — lowest effective potency. "
            "Step 3: Non-steroidal topicals for maintenance: roflumilast cream 0.15% (PDE-4i, IGA 2-3) or crisaborole 2% ointment (ages ≥3 months). "
            "Step 4: Topical calcineurin inhibitors (pimecrolimus 1% cream) for sensitive areas (face, intertriginous)."
        )

        specific_agents.append(
            "Roflumilast cream 0.15% once daily — AAD 2025 strong recommendation for mild-moderate AD (IGA 2-3)"
        )
        specific_agents.append(
            "Crisaborole 2% ointment — FDA approved ≥3 months; mild-moderate AD"
        )
        specific_agents.append(
            "Pimecrolimus 1% cream — face, eyelids, intertriginous areas"
        )
        specific_agents.append(
            "Ruxolitinib 1.5% cream — mild-moderate AD, ages ≥12"
        )
        specific_agents.append(
            "Tapinarof cream 1% — AhR agonist; approved mild-severe AD (once daily, 'remittive effect')"
        )

        monitoring_plan.append("Reassess IGA and NRS at 4-8 weeks")
        monitoring_plan.append("Escalate if no response to topicals after 4-6 weeks")
        evidence_level = "Strong recommendation (AAD 2025, Level A)"

    elif severity == "moderate":
        primary_recommendation = "Escalate to biologic or JAK inhibitor if topicals and phototherapy insufficient"
        treatment_pathway = (
            "Step 1: Optimize topical regimen (TCS + non-steroidal topicals). "
            "Step 2: Phototherapy (narrowband UVB) if topicals inadequate. "
            "Step 3: Biologic therapy — dupilumab (IL-4Rα, ages ≥6 months), tralokinumab (IL-13, ages ≥12), lebrikizumab (IL-13, adults), nemolizumab (IL-31Rα, ages ≥12 with significant pruritus). "
            "Step 4: JAK inhibitors if no CV/thromboembolism/malignancy risk — upadacitinib, abrocitinib, baricitinib."
        )

        if has_ocular_disease:
            specific_agents.append(
                "Nemolizumab (IL-31Rα) — preferred over IL-4/13 biologics in patients with ocular comorbidity (conjunctivitis)"
            )
            specific_agents.append(
                "JAK inhibitor (if no CV risk) — upadacitinib or abrocitinib"
            )
            agents_to_avoid.append(
                "Dupilumab, tralokinumab, lebrikizumab — may worsen conjunctivitis in patients with pre-existing ocular disease"
            )
        elif has_significant_pruritus and pruritus_nrs >= 7:
            specific_agents.append(
                "Nemolizumab (IL-31Rα, SC monthly) — specifically targets IL-31-mediated pruritus; AAD 2025 strong recommendation for ages ≥12"
            )
            specific_agents.append(
                "Dupilumab (IL-4Rα) — first-line biologic, broadest age approval (≥6 months)"
            )
        else:
            specific_agents.append(
                "Dupilumab (IL-4Rα) — first-line biologic; strong recommendation AAD 2025; ages ≥6 months"
            )
            specific_agents.append(
                "Lebrikizumab (IL-13) — AAD 2025 strong recommendation; adults; Q2W then Q4W maintenance"
            )
            specific_agents.append(
                "Tralokinumab (IL-13) — AAD 2023 strong recommendation; ages ≥12"
            )

        if (
            not has_cardiovascular_risk
            and not has_thromboembolism_history
            and not has_malignancy_history
        ):
            specific_agents.append(
                "Upadacitinib 15mg or 30mg daily — JAK1 inhibitor; strong recommendation AAD 2026"
            )
            specific_agents.append(
                "Abrocitinib 100mg or 200mg daily — JAK1 inhibitor; strong recommendation AAD 2026"
            )
            specific_agents.append(
                "Baricitinib 2mg or 4mg daily — JAK1/2 inhibitor; strong recommendation AAD 2026"
            )

        monitoring_plan.append(
            "Reassess EASI and IGA at 16 weeks (biologic) or 12 weeks (JAK inhibitor)"
        )
        monitoring_plan.append(
            "Monitor for injection site reactions, conjunctivitis (dupilumab/tralokinumab/lebrikizumab)"
        )
        monitoring_plan.append(
            "JAK inhibitors: CBC, lipids, LFTs at baseline and periodically; screen for TB and hepatitis B"
        )
        evidence_level = "Strong recommendation (AAD 2025/2026, Level A)"

    else:
        # Severe
        primary_recommendation = "Biologic or JAK inhibitor therapy required; consider combination with topicals"
        treatment_pathway = (
            "Step 1: Initiate biologic therapy — dupilumab preferred first-line (broadest evidence, all ages ≥6 months). "
            "Step 2: Alternative biologics: lebrikizumab, tralokinumab, nemolizumab (pruritus-dominant). "
            "Step 3: JAK inhibitors (if no CV/thromboembolism/malignancy risk): upadacitinib 30mg, abrocitinib 200mg. "
            "Step 4: Short-course systemic corticosteroids only as bridge — not for maintenance (AAD strongly recommends against). "
            "Step 5: Phototherapy adjunct for recalcitrant disease."
        )

        if has_ocular_disease:
            specific_agents.append(
                "Nemolizumab — preferred in ocular comorbidity; avoids IL-4/13 pathway"
            )
            if (
                not has_cardiovascular_risk
                and not has_thromboembolism_history
                and not has_malignancy_history
            ):
                specific_agents.append(
                    "Upadacitinib 30mg daily — highest efficacy JAK inhibitor for severe AD"
                )
        else:
            specific_agents.append(
                "Dupilumab — first-line; 300mg Q2W (adults); weight-based dosing in children"
            )
            specific_agents.append(
                "Lebrikizumab — 500mg Q2W x2 loading, then 250mg Q2W, then 250mg Q4W maintenance"
            )
            specific_agents.append("Tralokinumab — 600mg loading, then 300mg Q2W")
            if (
                not has_cardiovascular_risk
                and not has_thromboembolism_history
                and not has_malignancy_history
            ):
                specific_agents.append(
                    "Upadacitinib 30mg daily — JAK1 inhibitor; highest EASI-75 rates in head-to-head vs dupilumab"
                )
                specific_agents.append("Abrocitinib 200mg daily — JAK1 inhibitor")

        agents_to_avoid.append(
            "Long-term systemic corticosteroids — strongly recommended against by AAD"
        )
        agents_to_avoid.append(
            "Cyclosporine — short-term bridge only; not for maintenance"
        )

        monitoring_plan.append("Reassess EASI, IGA, and pruritus NRS at 16 weeks")
        monitoring_plan.append(
            "If inadequate response at 16 weeks: switch biologic class or add JAK inhibitor"
        )
        monitoring_plan.append(
            "JAK inhibitors: CBC, lipids, LFTs, TB screening, hepatitis B at baseline"
        )
        monitoring_plan.append("Annual skin cancer surveillance on JAK inhibitors")
        evidence_level = "Strong recommendation (AAD 2025/2026, Level A)"

    # Age-specific adjustments
    if age_group == "child_6mo_5yr":
        next_steps.append(
            "Age ≥6 months: dupilumab is the only approved biologic; weight-based dosing"
        )
        next_steps.append(
            "Crisaborole 2% ointment approved ≥3 months for mild-moderate AD"
        )
        next_steps.append("Avoid JAK inhibitors — not approved in this age group")
    elif age_group == "child_6_11":
        next_steps.append(
            "Age 6-11: dupilumab approved (PMID: 33007469); IGA=4, EASI≥21, NRS≥4, BSA≥15% criteria"
        )
        next_steps.append(
            "Crisaborole and pimecrolimus available for mild-moderate disease"
        )
    elif age_group == "adolescent_12_17":
        next_steps.append(
            "Age 12-17: dupilumab, tralokinumab, nemolizumab, abrocitinib, upadacitinib all approved"
        )
        next_steps.append(
            "Ruxolitinib 1.5% cream approved for mild-moderate AD ages ≥12"
        )

    # Prior treatment failure adjustments
    if failed_therapy == "prior_biologic":
        next_steps.append(
            "Prior biologic failure: switch biologic class (e.g., IL-4Rα → IL-13 or IL-31Rα) or escalate to JAK inhibitor"
        )
        shared_decision_points.append(
            "Discuss mechanism of action differences between biologic classes; JAK inhibitors may achieve faster response"
        )
    if failed_therapy == "prior_jak":
        next_steps.append(
            "Prior JAK inhibitor failure: switch to biologic; consider combination therapy with topical non-steroidal agents"
        )

    # Universal next steps
    next_steps.append("Confirm diagnosis: patch testing if contact allergy suspected")
    next_steps.append(
        "Optimize emollient regimen: apply within 3 minutes of bathing ('soak and smear')"
    )
    next_steps.append("Assess and address psychosocial burden (DLQI, PHQ-9)")
    next_steps.append("Refer to dermatology if not responding to step 2 therapy")

    shared_decision_points.append(
        "Route of administration: biologics (SC injection) vs oral JAK inhibitors — patient preference matters"
    )
    shared_decision_points.append(
        "Pregnancy planning: dupilumab has most safety data; JAK inhibitors contraindicated"
    )
    shared_decision_points.append(
        "Cost and insurance: prior authorization typically required for biologics and JAK inhibitors"
    )

    return {
        "severity": severity,
        "primaryRecommendation": primary_recommendation,
        "treatmentPathway": treatment_pathway,
        "specificAgents": specific_agents,
        "agentsToAvoid": agents_to_avoid,
        "monitoringPlan": monitoring_plan,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": evidence_level,
        "sharedDecisionPoints": shared_decision_points,
        "references": [dict(ref) for ref in _REFERENCES],
    }
