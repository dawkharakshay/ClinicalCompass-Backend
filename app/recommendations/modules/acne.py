"""Acne Vulgaris clinical recommendation engine.

Ported 1:1 from old_static_code/client/src/lib/acneLogic.ts (assessAcne).

Based on:
- AAD 2024 Guidelines of Care for the Management of Acne Vulgaris (PMID: 38300170)
- AAD 2016 Acne Guidelines (PMID: 26897386)
- Antibiotic Stewardship in Acne; Isotretinoin REMS (iPLEDGE).
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "acne"


def _classify_acne_severity(data: dict) -> str:
    pga_score = num(data.get("pgaScore"), 0)
    has_scarring = to_bool(data.get("hasScarring"))
    has_psychosocial_burden = to_bool(data.get("hasPsychosocialBurden"))

    # PGA-based primary classification
    if pga_score <= 2:
        # Override to severe if scarring or psychosocial burden present
        if has_scarring or has_psychosocial_burden:
            return "severe"
        return "mild"
    if pga_score == 3:
        if has_scarring or has_psychosocial_burden:
            return "severe"
        return "moderate"
    # PGA 4-5 or nodulocystic
    return "severe"


def assess(data: dict) -> dict:
    severity = _classify_acne_severity(data)

    acne_type = data.get("acneType")
    patient_sex = data.get("patientSex")
    prior_antibiotic_months = num(data.get("priorAntibioticMonths"), 0)

    has_scarring = to_bool(data.get("hasScarring"))
    is_pregnant = to_bool(data.get("isPregnant"))
    is_breastfeeding = to_bool(data.get("isBreastfeeding"))
    has_drug_induced_acne = to_bool(data.get("hasDrugInducedAcne"))
    has_pcos = to_bool(data.get("hasPCOS"))
    desire_contraception = to_bool(data.get("desireContraception"))
    has_hyperkalemia_risk = to_bool(data.get("hasHyperkalemiaRisk"))

    urgent_flags: list[str] = []
    specific_agents: list[str] = []
    agents_to_avoid: list[str] = []
    hormonal_options: list[str] = []
    isotretinoin_notes: list[str] = []
    antibiotic_stewardship_notes: list[str] = []
    next_steps: list[str] = []
    monitoring_plan: list[str] = []
    shared_decision_points: list[str] = []
    isotretinoin_indicated = False

    # Urgent flags
    if is_pregnant:
        urgent_flags.append(
            "PREGNANCY: Isotretinoin is absolutely contraindicated. Avoid tetracyclines (doxycycline, minocycline). Topical azelaic acid and erythromycin are safest options."
        )
    if has_drug_induced_acne:
        urgent_flags.append(
            "Drug-induced acne suspected — review medications (corticosteroids, lithium, anticonvulsants, anabolic steroids) before initiating acne therapy"
        )

    primary_recommendation = ""
    treatment_pathway = ""
    evidence_level = ""

    if severity == "mild":
        primary_recommendation = "Topical multimodal combination therapy — avoid antibiotic monotherapy"
        treatment_pathway = (
            "Step 1: Topical retinoid (adapalene 0.1-0.3%, tretinoin 0.025-0.1%, or tazarotene) — cornerstone of acne therapy. "
            "Step 2: Add benzoyl peroxide (BPO) 2.5-10% — antibiotic resistance prevention. "
            "Step 3: Fixed-dose combination (retinoid + BPO, or antibiotic + BPO) for convenience and adherence. "
            "Step 4: Reassess at 8-12 weeks; escalate if inadequate response."
        )

        specific_agents.append("Adapalene 0.1% gel — first-line retinoid; OTC available; well tolerated")
        specific_agents.append("Benzoyl peroxide 2.5-5% — essential for antibiotic resistance prevention")
        specific_agents.append("Fixed-dose adapalene 0.1% + BPO 2.5% (Epiduo) — convenient combination")
        specific_agents.append("Azelaic acid 15-20% — comedolytic + anti-inflammatory; safe in pregnancy")
        specific_agents.append("Salicylic acid 0.5-2% — comedolytic; OTC option for mild comedonal acne")

        if acne_type == "comedonal":
            specific_agents.append("Topical retinoid monotherapy acceptable for pure comedonal acne")

        evidence_level = "Strong recommendation (AAD 2024, Level A)"

    elif severity == "moderate":
        primary_recommendation = "Combination topical + systemic therapy; antibiotic stewardship is mandatory"
        treatment_pathway = (
            "Step 1: Topical retinoid + BPO (continue throughout). "
            "Step 2: Add oral antibiotic (doxycycline 100mg daily preferred) — limit to ≤3-6 months; always combine with BPO. "
            "Step 3: Add hormonal therapy in females (spironolactone 50-200mg or COC). "
            "Step 4: If inadequate response after 3 months of antibiotics: escalate to isotretinoin. "
            "Step 5: Intralesional corticosteroids for individual large nodules (rapid response)."
        )

        specific_agents.append("Doxycycline 100mg daily — preferred oral antibiotic (AAD 2024 conditional recommendation over azithromycin)")
        specific_agents.append("Fixed-dose topical antibiotic + BPO (clindamycin 1% + BPO 5%) — reduces resistance")
        specific_agents.append("Adapalene 0.3% + BPO 2.5% (Epiduo Forte) — for moderate-severe papulopustular")
        specific_agents.append("Sarecycline 1.5mg/kg/day — narrow-spectrum tetracycline; less GI side effects")
        specific_agents.append("Intralesional triamcinolone 2.5-5mg/mL — for individual nodules/cysts")

        antibiotic_stewardship_notes.append("Limit oral antibiotic duration to ≤3-6 months (AAD 2024 strong recommendation)")
        antibiotic_stewardship_notes.append("NEVER use topical antibiotic monotherapy — always combine with BPO")
        antibiotic_stewardship_notes.append("Do not use oral and topical antibiotics simultaneously")
        antibiotic_stewardship_notes.append("Continue BPO throughout antibiotic course to prevent resistance")

        agents_to_avoid.append("Oral antibiotic monotherapy — strongly not recommended (AAD 2024)")
        agents_to_avoid.append("Topical antibiotic monotherapy — promotes resistance")
        agents_to_avoid.append("Azithromycin — less preferred than doxycycline per AAD 2024")

        evidence_level = "Strong recommendation (AAD 2024, Level A)"

    else:
        # Severe
        primary_recommendation = "Oral isotretinoin is strongly recommended for severe acne or treatment-refractory moderate acne"
        treatment_pathway = (
            "Step 1: Oral isotretinoin 0.5-1mg/kg/day — standard daily dosing preferred over intermittent (AAD 2024). "
            "Step 2: Target cumulative dose 120-150mg/kg for sustained remission. "
            "Step 3: Continue topical retinoid + BPO during and after isotretinoin course. "
            "Step 4: Intralesional corticosteroids for acute nodule management during initiation. "
            "Step 5: Hormonal therapy (females) as adjunct or maintenance after isotretinoin."
        )

        isotretinoin_indicated = True
        isotretinoin_notes.append("Isotretinoin strongly recommended for severe acne (PGA 4-5), nodulocystic acne, or acne with scarring/psychosocial burden (AAD 2024)")
        isotretinoin_notes.append("iPLEDGE REMS enrollment required for all patients in the US")
        isotretinoin_notes.append("Pregnancy prevention mandatory for persons of childbearing potential — 2 forms of contraception or abstinence")
        isotretinoin_notes.append("Standard isotretinoin or lidose-isotretinoin (Absorica LD) — both conditionally recommended by AAD 2024")
        isotretinoin_notes.append("Traditional daily dosing conditionally recommended over intermittent/low-dose for severe acne")
        isotretinoin_notes.append("AAD 2024: No proven increased risk of neuropsychiatric conditions or IBD in population-based studies")

        specific_agents.append("Isotretinoin 0.5-1mg/kg/day orally — standard daily dosing")
        specific_agents.append("Intralesional triamcinolone — bridge therapy for acute nodule flare")
        specific_agents.append("Topical retinoid + BPO — continue throughout course")

        monitoring_plan.append("Isotretinoin: LFTs and lipids at baseline and monthly (or as clinically indicated)")
        monitoring_plan.append("CBC monitoring not needed in healthy patients (AAD 2024)")
        monitoring_plan.append("Monthly pregnancy test for persons of childbearing potential (iPLEDGE)")
        monitoring_plan.append("Reassess at 1 month, then every 1-2 months during course")

        evidence_level = "Strong recommendation (AAD 2024, Level A)"

    # Hormonal therapy (females)
    if patient_sex == "female" and not is_pregnant and not is_breastfeeding:
        if has_pcos or desire_contraception or severity != "mild":
            hormonal_options.append("Spironolactone 50-200mg daily — conditionally recommended; anti-androgen; effective for hormonal acne")
            hormonal_options.append("Combined oral contraceptive (COC) — FDA-approved for acne; ethinyl estradiol-based")
            hormonal_options.append("Clascoterone 1% cream — topical anti-androgen; FDA approved for acne ages ≥12")

            if has_hyperkalemia_risk:
                monitoring_plan.append("Spironolactone: check potassium at baseline if risk factors for hyperkalemia (AAD 2024 — routine monitoring not needed in healthy patients)")

            shared_decision_points.append("Hormonal therapy effective for females with hormonal acne patterns (jawline, chin, perimenstrual flares)")
            shared_decision_points.append("Spironolactone: potassium monitoring only needed with risk factors per AAD 2024")

    # Pregnancy-specific
    if is_pregnant or is_breastfeeding:
        agents_to_avoid.append("Isotretinoin — absolutely contraindicated in pregnancy (Category X)")
        agents_to_avoid.append("Doxycycline, minocycline, tetracycline — contraindicated in pregnancy")
        agents_to_avoid.append("Spironolactone — avoid in pregnancy")
        specific_agents.append("Topical azelaic acid 15-20% — safe in pregnancy")
        specific_agents.append("Topical erythromycin + BPO — safe in pregnancy")
        specific_agents.append("Topical clindamycin + BPO — generally considered safe in pregnancy")

    # Prior antibiotic overuse
    if prior_antibiotic_months > 6:
        antibiotic_stewardship_notes.append(
            f"Prior antibiotic use: {_fmt_months(prior_antibiotic_months)} months — consider antibiotic holiday; escalate to isotretinoin or hormonal therapy"
        )
        urgent_flags.append("Extended prior antibiotic use detected — antibiotic resistance risk; prioritize non-antibiotic systemic options")

    # Scarring
    if has_scarring:
        next_steps.append("Active scarring: expedite isotretinoin referral — early treatment prevents progressive scarring")
        next_steps.append("Consider dermatology referral for scar treatment (fractional laser, chemical peels, microneedling) after acne control")

    # Universal next steps
    next_steps.append("Reassess at 8-12 weeks; document PGA score at each visit")
    next_steps.append("Counsel on realistic expectations: 6-8 weeks for topical response, 3 months for systemic")
    next_steps.append("Sunscreen daily — retinoids increase photosensitivity")
    next_steps.append("Gentle non-comedogenic skincare; avoid abrasive scrubs")

    shared_decision_points.append("Antibiotic stewardship: limit duration, always combine with BPO")
    shared_decision_points.append("Isotretinoin: discuss iPLEDGE requirements, side effect profile, and expected remission rates")
    shared_decision_points.append("Psychosocial impact: screen for depression/anxiety; acne significantly affects quality of life")

    return {
        "severity": severity,
        "primaryRecommendation": primary_recommendation,
        "treatmentPathway": treatment_pathway,
        "specificAgents": specific_agents,
        "agentsToAvoid": agents_to_avoid,
        "hormonalOptions": hormonal_options,
        "isotretinoinIndicated": isotretinoin_indicated,
        "isotretinoinNotes": isotretinoin_notes,
        "antibioticStewardshipNotes": antibiotic_stewardship_notes,
        "monitoringPlan": monitoring_plan,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": evidence_level,
        "sharedDecisionPoints": shared_decision_points,
        "references": [
            {
                "citation": "AAD 2024 Guidelines of Care for the Management of Acne Vulgaris — Zaenglein AL et al.",
                "pmid": "38300170",
                "url": "https://pubmed.ncbi.nlm.nih.gov/38300170/",
            },
            {
                "citation": "AAD 2016 Guidelines of Care for the Management of Acne Vulgaris — Zaenglein AL et al.",
                "pmid": "26897386",
                "url": "https://pubmed.ncbi.nlm.nih.gov/26897386/",
            },
            {
                "citation": "Topical Retinoids in Acne Vulgaris: A Systematic Review — Leyden J et al.",
                "pmid": "30674002",
                "url": "https://pubmed.ncbi.nlm.nih.gov/30674002/",
            },
            {
                "citation": "Topical Benzoyl Peroxide for Acne — Dréno B et al.",
                "pmid": "32175593",
                "url": "https://pubmed.ncbi.nlm.nih.gov/32175593/",
            },
            {
                "citation": "Oral Doxycycline in the Management of Acne Vulgaris — Garner SE et al.",
                "pmid": "4445892",
                "url": "https://pubmed.ncbi.nlm.nih.gov/4445892/",
            },
        ],
    }


def _fmt_months(value: float) -> str:
    """Render a number the way JS template-literal coercion would (integers
    without a trailing ``.0``)."""
    if value == int(value):
        return str(int(value))
    return str(value)
