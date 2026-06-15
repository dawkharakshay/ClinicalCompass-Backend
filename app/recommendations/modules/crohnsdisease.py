"""Crohn's Disease Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/crohnsDiseaseLogic.ts
(assessCrohnsDisease).

Based on:
- ACG Clinical Guideline: Management of Crohn's Disease in Adults (2025 Update)
- AGA Clinical Practice Update on Positioning of Biologics and Small Molecules (2025)
- IOIBD Consensus on Treat-to-Target in Crohn's Disease (2024)
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, to_bool

LOGIC_KEY = "crohnsdisease"

_REFERENCES = [
    {
        "citation": "Lichtenstein GR, et al. ACG Clinical Guideline: Management of Crohn's Disease in Adults. Am J Gastroenterol. 2018;113(4):481-517. (Updated 2025)",
        "pmid": "29610508",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29610508/",
    },
    {
        "citation": "Peyrin-Biroulet L, et al. Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE-II): An Update on Selecting Therapeutic Targets for Treat-to-Target Strategies in IBD. Gastroenterology. 2021;162(7):2090-2112.",
        "pmid": "33359090",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33359090/",
    },
    {
        "citation": "D'Haens G, et al. Risankizumab as Induction Therapy for Crohn's Disease (ADVANCE and MOTIVATE). Lancet. 2022;399(10340):2015-2030.",
        "pmid": "35644166",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35644166/",
    },
    {
        "citation": "Colombel JF, et al. Infliximab, Azathioprine, or Combination Therapy for Crohn's Disease (SONIC). N Engl J Med. 2010;362(15):1383-1395.",
        "pmid": "20393175",
        "url": "https://pubmed.ncbi.nlm.nih.gov/20393175/",
    },
    {
        "citation": "Sandborn WJ, et al. Upadacitinib as Induction and Maintenance Therapy for Crohn's Disease (U-EXCEED). N Engl J Med. 2023;388(21):1966-1980.",
        "pmid": "37224198",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37224198/",
    },
    {
        "citation": "Feagan BG, et al. Ustekinumab as Induction and Maintenance Therapy for Crohn's Disease. N Engl J Med. 2016;375(20):1946-1960.",
        "pmid": "27959607",
        "url": "https://pubmed.ncbi.nlm.nih.gov/27959607/",
    },
]


def assess(data: dict) -> dict:
    location = data.get("location")
    pattern = data.get("pattern")
    severity = data.get("severity")
    prior_therapy = data.get("priorTherapy")
    crp_status = data.get("crpStatus")
    endoscopic_activity = data.get("endoscopicActivity")

    has_perianaldisease = to_bool(data.get("hasPerianaldisease"))
    has_fistula = to_bool(data.get("hasFistula"))
    has_abscess = to_bool(data.get("hasAbscess"))
    has_stricture = to_bool(data.get("hasStricture"))
    has_penetrating = to_bool(data.get("hasPenetrating"))
    has_deep_ulcers = to_bool(data.get("hasDeepUlcers"))
    has_extensive_disease = to_bool(data.get("hasExtensiveDisease"))

    has_smoking = to_bool(data.get("hasSmoking"))
    has_perineal_disease = to_bool(data.get("hasPerinealDisease"))
    has_upper_gi_involvement = to_bool(data.get("hasUpperGIInvolvement"))
    has_previous_surgery = to_bool(data.get("hasPreviousSurgery"))
    has_extraintestinal_manifestations = to_bool(
        data.get("hasExtraintestinalManifestations")
    )

    has_active_tb = to_bool(data.get("hasActiveTB"))
    has_latent_tb = to_bool(data.get("hasLatentTB"))
    has_hepatitis_b = to_bool(data.get("hasHepatitisB"))
    has_malignancy_history = to_bool(data.get("hasMalignancyHistory"))
    has_demyelinating_disease = to_bool(data.get("hasDemyelinatingDisease"))
    has_congestive_heart_failure = to_bool(data.get("hasCongestiveHeartFailure"))
    has_jak_contraindication = to_bool(data.get("hasJAKContraindication"))

    wants_top_down = to_bool(data.get("wantsTopDown"))

    urgent_flags: list[str] = []
    recommended_agents: list[str] = []
    agents_to_avoid: list[str] = []
    next_steps: list[str] = []

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if has_abscess:
        urgent_flags.append(
            "ABSCESS: surgical/IR drainage required before initiating or continuing biologic therapy — do not start immunosuppression with undrained abscess"
        )
    if severity == "severe" and crp_status == "markedly_elevated":
        urgent_flags.append(
            "Severe active Crohn's disease with markedly elevated CRP — consider hospitalization, IV steroids, and urgent GI consultation"
        )
    if has_active_tb:
        urgent_flags.append(
            "ACTIVE TB: all biologic therapy contraindicated until TB treatment completed and cleared by infectious disease"
        )
        agents_to_avoid.append(
            "All biologics (anti-TNF, vedolizumab, ustekinumab, risankizumab, JAK inhibitors) — contraindicated with active TB"
        )
    if has_congestive_heart_failure:
        urgent_flags.append(
            "CHF (EF <35%): anti-TNF agents are contraindicated — use vedolizumab, ustekinumab, or IL-23 inhibitors"
        )
        agents_to_avoid.append(
            "Anti-TNF agents (infliximab, adalimumab, certolizumab) — contraindicated in CHF with EF <35%"
        )
    if has_demyelinating_disease:
        urgent_flags.append(
            "Demyelinating disease (MS/optic neuritis): anti-TNF agents are contraindicated"
        )
        agents_to_avoid.append(
            "Anti-TNF agents — contraindicated with demyelinating disease"
        )
    if has_malignancy_history:
        urgent_flags.append(
            "Prior malignancy: avoid JAK inhibitors (increased malignancy risk per FDA Black Box Warning); use vedolizumab or ustekinumab preferentially"
        )
        agents_to_avoid.append(
            "JAK inhibitors (upadacitinib) — relative contraindication with prior malignancy (FDA Black Box Warning)"
        )
    if has_jak_contraindication:
        agents_to_avoid.append(
            "JAK inhibitors (upadacitinib) — contraindicated with DVT/PE history, high CV risk, or active malignancy (FDA Black Box Warning 2023)"
        )
    if has_latent_tb:
        urgent_flags.append(
            "Latent TB: LTBI treatment required before starting anti-TNF therapy (INH 9 months or rifampin 4 months). Vedolizumab/ustekinumab/IL-23 have lower TB reactivation risk."
        )
    if has_hepatitis_b:
        urgent_flags.append(
            "Hepatitis B: antiviral prophylaxis (entecavir or tenofovir) required before starting any biologic — risk of HBV reactivation"
        )

    # ─── Risk Stratification ──────────────────────────────────────────────────
    age_at_diagnosis = data.get("ageAtDiagnosis")
    age_marker = age_at_diagnosis is not None and parse_float(age_at_diagnosis) < 30

    poor_prognosis_markers = sum(
        1
        for flag in [
            age_marker,
            has_smoking,
            has_perineal_disease or has_perianaldisease,
            has_upper_gi_involvement,
            has_deep_ulcers,
            has_extensive_disease,
            has_penetrating or pattern == "penetrating",
            has_stricture or pattern == "stricturing",
            has_previous_surgery,
        ]
        if flag
    )

    is_high_risk = (
        poor_prognosis_markers >= 3 or severity == "severe" or has_deep_ulcers
    )

    # ─── Treatment Strategy ────────────────────────────────────────────────────
    treatment_strategy = ""
    biologic_selection = ""

    if prior_therapy in ("none", "on_5asa", "on_steroids_only"):
        if (
            is_high_risk
            or wants_top_down
            or severity == "moderate"
            or severity == "severe"
        ):
            treatment_strategy = (
                "TOP-DOWN STRATEGY RECOMMENDED (ACG 2025 Strong Recommendation): Early advanced therapy with biologic ± immunomodulator. "
                "High-risk features or moderate-severe disease warrant early biologic initiation to prevent bowel damage and surgery. "
                "Avoid prolonged steroid dependence — steroids are bridge therapy only, not maintenance."
            )

            if has_perianaldisease or has_fistula:
                biologic_selection = (
                    "Perianal/fistulizing Crohn's: anti-TNF therapy is FIRST-LINE (infliximab has most evidence for fistula closure — ACCENT II trial). "
                    "Infliximab 5mg/kg IV (induction weeks 0, 2, 6, then Q8W) — superior fistula closure rates vs adalimumab. "
                    "Combination with azathioprine/6-MP improves durability (SONIC trial). "
                    "Ustekinumab and risankizumab are alternatives if anti-TNF contraindicated or failed."
                )
                recommended_agents.extend(
                    [
                        "Infliximab 5mg/kg IV (induction + maintenance) — PREFERRED for fistulizing disease",
                        "Adalimumab 160/80/40mg SC — alternative if IV not preferred",
                        "Certolizumab pegol 400mg SC — option in pregnancy (no placental transfer)",
                        "Ustekinumab 260–520mg IV then 90mg SC Q8W — anti-TNF alternative",
                        "Combination with azathioprine 2–2.5mg/kg or 6-MP 1–1.5mg/kg (SONIC trial)",
                    ]
                )
            elif location == "colonic" or has_extraintestinal_manifestations:
                biologic_selection = (
                    "Colonic Crohn's or prominent EIM: vedolizumab (gut-selective) is preferred for colonic disease without systemic EIM. "
                    "For joint/skin/eye EIM: anti-TNF or ustekinumab preferred (systemic mechanism). "
                    "Risankizumab (IL-23 inhibitor) — ADVANCE/MOTIVATE trials: superior to placebo, strong remission rates. "
                    "Upadacitinib (JAK1 inhibitor) — U-EXCEED trial: effective for moderate-severe CD, oral administration."
                )
                recommended_agents.extend(
                    [
                        "Vedolizumab 300mg IV (induction weeks 0, 2, 6, then Q8W) — preferred for colonic CD",
                        "Risankizumab 600mg IV x3 then 360mg SC Q8W — IL-23 inhibitor (ADVANCE/MOTIVATE)",
                        "Ustekinumab 260–520mg IV then 90mg SC Q8W — IL-12/23 inhibitor",
                        "Upadacitinib 45mg QD x12 weeks then 30mg QD (JAK1 inhibitor — oral)",
                        "Anti-TNF (infliximab, adalimumab) — if EIM present or rapid response needed",
                    ]
                )
            else:
                biologic_selection = (
                    "Ileal/ileocolonic Crohn's (most common): anti-TNF or IL-23 inhibitors are preferred first-line. "
                    "Risankizumab (IL-23): ADVANCE trial — 45% endoscopic remission at 52 weeks. "
                    "Ustekinumab: UNIFI/CERTIFI trials — effective for moderate-severe CD. "
                    "Anti-TNF (infliximab, adalimumab): established efficacy, most long-term data. "
                    "Vedolizumab: slower onset, preferred when gut-selective mechanism desired."
                )
                recommended_agents.extend(
                    [
                        "Risankizumab 600mg IV x3 then 360mg SC Q8W — IL-23 inhibitor (preferred — ADVANCE trial)",
                        "Ustekinumab 260–520mg IV then 90mg SC Q8W — IL-12/23 inhibitor",
                        "Infliximab 5mg/kg IV Q8W ± azathioprine (SONIC trial)",
                        "Adalimumab 160/80/40mg SC — convenient SC dosing",
                        "Upadacitinib 45mg QD x12w then 30mg QD — oral JAK1 inhibitor (if no contraindications)",
                    ]
                )
        else:
            treatment_strategy = (
                "Mild-moderate Crohn's without high-risk features: step-up approach acceptable. "
                "Budesonide 9mg/day for ileal/right colonic disease (induction only — not maintenance). "
                "Immunomodulator (azathioprine, 6-MP, methotrexate) for steroid-sparing maintenance. "
                "Reassess at 3 months — escalate to biologic if not in clinical/biochemical remission."
            )
            recommended_agents.extend(
                [
                    "Budesonide 9mg/day x8–12 weeks (ileal/right colonic — induction)",
                    "Azathioprine 2–2.5mg/kg/day (maintenance — check TPMT/NUDT15 before starting)",
                    "6-Mercaptopurine 1–1.5mg/kg/day (alternative to AZA)",
                    "Methotrexate 15–25mg SC/IM weekly (if AZA/6-MP intolerant)",
                ]
            )
    elif prior_therapy == "failed_anti_tnf":
        treatment_strategy = (
            "Anti-TNF failure: switch to non-anti-TNF mechanism. "
            "Assess reason for failure: primary non-response (switch mechanism) vs secondary loss of response (check drug levels/antibodies). "
            "If anti-drug antibodies present → switch mechanism. "
            "If low drug levels, no antibodies → optimize dose before switching."
        )
        biologic_selection = (
            "Post-anti-TNF options (ACG 2025): "
            "1) Risankizumab (IL-23) — ADVANCE/MOTIVATE: superior to placebo post-anti-TNF failure. "
            "2) Ustekinumab (IL-12/23) — UNIFI: effective post-anti-TNF. "
            "3) Vedolizumab (gut-selective integrin) — effective post-anti-TNF for colonic disease. "
            "4) Upadacitinib (JAK1) — U-EXCEED: 39% endoscopic remission at 52 weeks post-anti-TNF."
        )
        recommended_agents.extend(
            [
                "Risankizumab 600mg IV x3 then 360mg SC Q8W (preferred — ADVANCE trial)",
                "Upadacitinib 45mg QD x12w then 30mg QD (oral — U-EXCEED trial)",
                "Ustekinumab 260–520mg IV then 90mg SC Q8W",
                "Vedolizumab 300mg IV Q8W (colonic disease preferred)",
            ]
        )
    elif prior_therapy in ("failed_anti_tnf_and_vedolizumab", "failed_multiple_biologics"):
        treatment_strategy = (
            "Multiple biologic failure: consider remaining mechanisms and combination strategies. "
            "Upadacitinib (JAK1) is effective even after multiple biologic failures. "
            "Risankizumab if IL-23 not yet tried. "
            "Ozanimod (S1P modulator) — FDA approved 2023 for CD. "
            "Consider surgery for refractory disease with limited bowel involvement."
        )
        biologic_selection = (
            "Refractory CD options: "
            "1) Upadacitinib 45mg QD (JAK1 — effective post-multiple biologic failure). "
            "2) Risankizumab (if IL-23 not yet tried). "
            "3) Ozanimod 0.92mg QD (S1P modulator — True North extension study). "
            "4) Etrasimod (S1P modulator — Phase 3 data emerging). "
            "5) Surgical resection for localized refractory disease."
        )
        recommended_agents.extend(
            [
                "Upadacitinib 45mg QD x12w then 30mg QD (oral JAK1 — if no contraindications)",
                "Risankizumab 600mg IV x3 then 360mg SC Q8W (if IL-23 naive)",
                "Ozanimod 0.92mg QD (S1P modulator)",
                "Surgical consultation for refractory localized disease",
            ]
        )
        urgent_flags.append(
            "Multiple biologic failure: multidisciplinary IBD team review recommended — consider clinical trial enrollment"
        )
    else:
        treatment_strategy = (
            "Optimize current therapy. Check drug levels and anti-drug antibodies before switching."
        )
        recommended_agents.append(
            "Therapeutic drug monitoring (TDM) — check trough levels and antibodies before switching"
        )

    # ─── Maintenance Therapy ──────────────────────────────────────────────────
    maintenance_therapy = (
        "Maintenance principles (ACG 2025): "
        "1) Biologic monotherapy or combination with immunomodulator (combination reduces immunogenicity for anti-TNF). "
        "2) Steroids are NOT maintenance therapy — taper and discontinue. "
        "3) Treat-to-target: target endoscopic remission (SES-CD ≤2) + CRP normalization + fecal calprotectin <150μg/g. "
        "4) Therapeutic drug monitoring (TDM) to optimize dosing and detect antibody formation."
    )

    # ─── Treat-to-Target Plan ─────────────────────────────────────────────────
    treat_to_target_plan = (
        "TREAT-TO-TARGET (STRIDE-II 2021 + ACG 2025): "
        "Short-term target (3 months): clinical response — HBI <5 or CDAI <150, CRP normalization. "
        "Long-term target (12 months): endoscopic remission — SES-CD ≤2 (absence of ulcers). "
        "Adjunct targets: fecal calprotectin <150μg/g, transmural healing on MRI (emerging target). "
        "Assessment schedule: CRP + fecal calprotectin at 3 months; colonoscopy at 6–12 months to assess endoscopic response. "
        "If targets not met at 3 months: optimize therapy (TDM, dose escalation, or switch mechanism)."
    )

    # ─── Perianal Disease Plan ─────────────────────────────────────────────────
    perianaldisease_plan = "No perianal disease identified."
    if has_perianaldisease or has_fistula or has_abscess:
        perianaldisease_plan = (
            "Perianal Crohn's management: "
            "1) Drainage: abscess drainage (surgical or IR) BEFORE biologic initiation. "
            "2) Seton placement for complex fistulas — maintains drainage, prevents abscess recurrence. "
            "3) Anti-TNF (infliximab preferred) — ACCENT II trial: 46% fistula closure at 54 weeks. "
            "4) Combination: infliximab + seton + ciprofloxacin/metronidazole for complex perianal disease. "
            "5) Surgical options: advancement flap, LIFT procedure, fistula plug for select cases. "
            "6) MRI pelvis to characterize fistula anatomy before intervention."
        )
        next_steps.extend(
            [
                "MRI pelvis to characterize perianal fistula anatomy",
                "Colorectal surgery consultation for seton placement",
                "Drain abscess before starting biologic therapy",
            ]
        )

    # ─── Surgical Consideration ────────────────────────────────────────────────
    surgical_consideration = ""
    if has_abscess or pattern == "penetrating" or has_penetrating:
        surgical_consideration = (
            "Penetrating disease/abscess: surgical consultation required. "
            "Percutaneous drainage for accessible abscesses. "
            "Resection for non-drainable or recurrent abscesses. "
            "Optimize medical therapy post-operatively to prevent recurrence."
        )
        next_steps.extend(
            [
                "Surgical consultation",
                "Cross-sectional imaging (CT/MRI) to characterize penetrating disease",
            ]
        )
    elif has_stricture or pattern == "stricturing":
        surgical_consideration = (
            "Stricturing disease: distinguish inflammatory vs fibrotic stricture. "
            "Inflammatory stricture: may respond to biologic therapy. "
            "Fibrotic stricture: endoscopic balloon dilation (short, accessible strictures) or surgical resection. "
            "Strictureplasty for multiple short strictures to preserve bowel length."
        )
        next_steps.extend(
            [
                "MRI enterography to assess stricture — inflammatory vs fibrotic",
                "Endoscopy to assess stricture accessibility for dilation",
            ]
        )
    elif prior_therapy == "failed_multiple_biologics":
        surgical_consideration = (
            "Refractory disease: surgical resection may be preferable to continued biologic cycling. "
            "Ileocecal resection for localized ileocecal disease — low morbidity, high quality-of-life benefit. "
            "Multidisciplinary IBD team discussion recommended."
        )
    else:
        surgical_consideration = (
            "No immediate surgical indication. Monitor for complications (stricture, fistula, abscess)."
        )

    # ─── Monitoring Plan ──────────────────────────────────────────────────────
    monitoring_plan = (
        "Monitoring (ACG 2025): "
        "Labs every 3 months: CBC, CMP, CRP, fecal calprotectin. "
        "Therapeutic drug monitoring (TDM): trough levels + anti-drug antibodies at 14 weeks (anti-TNF), then annually or with loss of response. "
        "Colonoscopy at 6–12 months after therapy initiation to assess endoscopic response. "
        "Annual skin exam (melanoma risk with anti-TNF + thiopurines). "
        "Bone density (DEXA) if on steroids >3 months. "
        "Cervical cancer screening (HPV) annually in women on immunosuppression. "
        "CRC surveillance: colonoscopy every 1–3 years after 8 years of extensive colitis."
    )

    # ─── Next Steps ───────────────────────────────────────────────────────────
    if len(next_steps) == 0:
        next_steps.extend(
            [
                "Baseline labs: CBC, CMP, CRP, ESR, fecal calprotectin, albumin",
                "Colonoscopy + biopsies to confirm diagnosis and assess endoscopic activity",
                "Cross-sectional imaging (MRI enterography or CT enterography) to assess disease extent",
                "Infectious screening before biologic: TB (IGRA), hepatitis B/C, HIV, varicella",
                "Vaccination update before immunosuppression (pneumococcal, influenza, HPV, shingles)",
                "Gastroenterology/IBD specialist referral",
            ]
        )

    location_text = str(location).replace("_", " ")
    prior_therapy_text = str(prior_therapy).replace("_", " ")

    rationale = (
        f"CD location: {location_text}. "
        f"Pattern: {pattern}. "
        f"Severity: {severity}. "
        f"Prior therapy: {prior_therapy_text}. "
        f"Perianal disease: {'Yes' if has_perianaldisease else 'No'}. "
        f"High risk: {'Yes' if is_high_risk else 'No'} ({poor_prognosis_markers} poor prognosis markers). "
        f"CRP: {crp_status}. "
        f"Endoscopic activity: {endoscopic_activity}."
    )

    if is_high_risk or severity != "mild":
        primary_recommendation = (
            f"Moderate-severe or high-risk Crohn's disease: "
            f"{'early advanced therapy (top-down biologic) recommended' if prior_therapy == 'none' else 'escalate to next-line biologic/mechanism'}. "
            f"Treat-to-target with endoscopic remission goal."
        )
    else:
        primary_recommendation = (
            "Mild Crohn's disease: step-up approach with budesonide induction and immunomodulator maintenance. Reassess at 3 months."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "treatmentStrategy": treatment_strategy,
        "biologicSelection": biologic_selection,
        "maintenanceTherapy": maintenance_therapy,
        "treatToTargetPlan": treat_to_target_plan,
        "surgicalConsideration": surgical_consideration,
        "perianaldiseasePlan": perianaldisease_plan,
        "urgentFlags": urgent_flags,
        "recommendedAgents": recommended_agents,
        "agentsToAvoid": agents_to_avoid,
        "monitoringPlan": monitoring_plan,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": [dict(ref) for ref in _REFERENCES],
    }
