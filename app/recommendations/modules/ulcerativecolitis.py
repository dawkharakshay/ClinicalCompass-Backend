"""Ulcerative Colitis Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/ulcerativeColitisLogic.ts
(assessUlcerativeColitis).

Based on: ACG Clinical Guideline: Ulcerative Colitis in Adults (2019, 2025 Update),
AGA Living Clinical Practice Guideline on Moderate-to-Severe UC (2025),
ECCO Consensus on UC Management (2024).
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "ulcerativecolitis"


def assess(data: dict) -> dict:
    extent = data.get("extent")
    severity = data.get("severity")
    prior_therapy = data.get("priorTherapy")

    has_perforation = truthy(data.get("hasPerforation"))
    has_colon_dilation = truthy(data.get("hasColonDilation"))
    is_hospitalized = truthy(data.get("isHospitalized"))
    is_steroid_refractory = truthy(data.get("isSteroidRefractory"))
    is_steroid_dependent = truthy(data.get("isSteroidDependent"))
    has_active_tb = truthy(data.get("hasActiveTB"))
    has_chf = truthy(data.get("hasCongestiveHeartFailure"))
    has_demyelinating = truthy(data.get("hasDemyelinatingDisease"))
    has_jak_contra = truthy(data.get("hasJAKContraindication"))
    has_thromboembolism = truthy(data.get("hasThromboembolismHistory"))
    has_malignancy = truthy(data.get("hasMalignancyHistory"))

    urgent_flags: list[str] = []
    recommended_agents: list[str] = []
    agents_to_avoid: list[str] = []
    next_steps: list[str] = []

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if has_perforation:
        urgent_flags.append(
            "BOWEL PERFORATION: emergency surgical consultation — colectomy required urgently"
        )
    if has_colon_dilation:
        urgent_flags.append(
            "TOXIC MEGACOLON: urgent surgical consultation — NPO, IV fluids, IV steroids, "
            "consider emergency colectomy if no improvement in 24–48h"
        )
    if severity == "acute_severe" or (is_hospitalized and severity == "severe"):
        urgent_flags.append(
            "ACUTE SEVERE UC (Truelove-Witts criteria): admit to hospital, "
            "IV methylprednisolone 60mg/day or hydrocortisone 400mg/day, "
            "surgical consultation on admission"
        )
    if is_steroid_refractory and is_hospitalized:
        urgent_flags.append(
            "STEROID-REFRACTORY ACUTE SEVERE UC: rescue therapy required — "
            "infliximab 5mg/kg or cyclosporine 2–4mg/kg IV. Surgical consultation mandatory."
        )
    if has_active_tb:
        urgent_flags.append("ACTIVE TB: all biologic therapy contraindicated")
        agents_to_avoid.append(
            "All biologics and JAK inhibitors — contraindicated with active TB"
        )
    if has_chf:
        urgent_flags.append("CHF (EF <35%): anti-TNF agents contraindicated")
        agents_to_avoid.append(
            "Anti-TNF agents (infliximab, adalimumab, golimumab) — "
            "contraindicated in CHF with EF <35%"
        )
    if has_demyelinating:
        urgent_flags.append("Demyelinating disease: anti-TNF agents contraindicated")
        agents_to_avoid.append(
            "Anti-TNF agents — contraindicated with demyelinating disease"
        )
    if has_jak_contra or has_thromboembolism:
        agents_to_avoid.append(
            "JAK inhibitors (tofacitinib, upadacitinib, filgotinib) — "
            "contraindicated with DVT/PE history, high CV risk, or active malignancy "
            "(FDA Black Box Warning 2023)"
        )
    if has_malignancy:
        urgent_flags.append(
            "Prior malignancy: avoid JAK inhibitors; prefer vedolizumab or IL-23 inhibitors"
        )
        agents_to_avoid.append(
            "JAK inhibitors — relative contraindication with prior malignancy"
        )

    # ─── Acute Severe UC Plan ─────────────────────────────────────────────────
    acute_severe_uc_plan = "Not applicable — not acute severe UC."
    if severity == "acute_severe" or is_hospitalized:
        days_on_iv = data.get("daysOnIVSteroids")
        if is_steroid_refractory and days_on_iv is not None and num(days_on_iv, 0) >= 3:
            acute_severe_uc_plan = (
                "STEROID-REFRACTORY ACUTE SEVERE UC (day 3–5 assessment): "
                "Rescue therapy options (ACG 2025 Strong Recommendation): "
                "1) Infliximab 5mg/kg IV — Oxford criteria (albumin <30g/L, CRP >45mg/L, "
                ">8 stools/day at day 3) predicts steroid failure. "
                "   Accelerated dosing (5mg/kg at 0, 1, 2 weeks) may be used in severe cases. "
                "2) Cyclosporine 2mg/kg IV continuous infusion — bridge to azathioprine/6-MP. "
                "3) Tofacitinib 10mg TID x8 weeks (oral JAK inhibitor — rapid onset, 3–5 days) "
                "— emerging evidence for rescue. "
                "Colectomy: if no response to rescue therapy at 4–7 days, or at any time "
                "if clinical deterioration."
            )
            recommended_agents.append("Infliximab 5mg/kg IV (rescue — CONSTRUCT trial)")
            recommended_agents.append(
                "Cyclosporine 2mg/kg IV (rescue — bridge to thiopurine)"
            )
            recommended_agents.append(
                "Tofacitinib 10mg TID (oral rescue — emerging evidence)"
            )
            recommended_agents.append("Surgical consultation (colectomy if rescue fails)")
        else:
            acute_severe_uc_plan = (
                "ACUTE SEVERE UC — Initial management (Truelove-Witts protocol): "
                "IV methylprednisolone 60mg/day or hydrocortisone 100mg QID. "
                "NPO or clear liquids, IV fluids, DVT prophylaxis. "
                "Daily abdominal exam + plain X-ray (monitor for megacolon). "
                "Stool cultures + C. difficile PCR (exclude infectious trigger). "
                "Surgical consultation on admission. "
                "Assess response at day 3 (Oxford criteria) — plan rescue if no response."
            )
            recommended_agents.append(
                "IV methylprednisolone 60mg/day or hydrocortisone 400mg/day"
            )
            recommended_agents.append("DVT prophylaxis (LMWH)")
            recommended_agents.append("Stool cultures + C. difficile testing")

    # ─── Induction Therapy ────────────────────────────────────────────────────
    induction_therapy = ""
    biologic_selection = ""

    if prior_therapy == "none" or prior_therapy == "on_5asa":
        if severity == "mild" and (extent == "proctitis" or extent == "left_sided"):
            induction_therapy = (
                "Mild-moderate proctitis/left-sided UC: topical 5-ASA is FIRST-LINE "
                "(ACG 2025 Strong Recommendation). "
                "Mesalamine suppository 1g/day (proctitis) or enema 4g/day (left-sided). "
                "Combination oral + topical 5-ASA is superior to either alone (ASCEND trials). "
                "Oral mesalamine 2.4–4.8g/day for left-sided/extensive disease."
            )
            recommended_agents.append("Mesalamine suppository 1g/day (proctitis)")
            recommended_agents.append("Mesalamine enema 4g/day (left-sided)")
            recommended_agents.append(
                "Oral mesalamine 2.4–4.8g/day (MMX formulation preferred for once-daily dosing)"
            )
            recommended_agents.append(
                "Combination oral + topical 5-ASA (superior to monotherapy)"
            )
        elif (
            severity == "moderate"
            or severity == "severe"
            or extent == "extensive"
            or extent == "pancolitis"
        ):
            induction_therapy = (
                "Moderate-severe or extensive UC: biologic therapy recommended "
                "(AGA 2025 Strong Recommendation). "
                "Avoid prolonged steroid use — steroids are bridge therapy only. "
                "Early biologic initiation improves outcomes and reduces colectomy risk."
            )
            biologic_selection = (
                "Biologic selection for moderate-severe UC (AGA 2025 mechanism-based approach): "
                "1) Vedolizumab (gut-selective integrin inhibitor) — GEMINI trials: preferred "
                "for UC due to gut selectivity, favorable safety profile, lower infection risk. "
                "2) Infliximab (anti-TNF) — ULTRA/ACT trials: rapid onset, preferred when quick "
                "response needed or EIM present. "
                "3) Adalimumab (anti-TNF SC) — convenient SC dosing. "
                "4) Golimumab (anti-TNF SC) — PURSUIT trials: approved for UC. "
                "5) Ustekinumab (IL-12/23) — UNIFI trial: effective, favorable safety. "
                "6) Risankizumab (IL-23) — INSPIRE trial: 40% clinical remission at 52 weeks. "
                "7) Mirikizumab (IL-23) — LUCENT trials: FDA approved 2023. "
                "8) Tofacitinib (JAK) — OCTAVE trials: rapid onset (days), oral. "
                "9) Upadacitinib (JAK1) — U-ACHIEVE: superior to adalimumab in head-to-head "
                "(QUARTZ trial). "
                "10) Ozanimod/Etrasimod (S1P modulators) — TRUE NORTH/ELEVATE trials."
            )
            recommended_agents.append(
                "Vedolizumab 300mg IV (induction weeks 0, 2, 6, then Q8W) — preferred for UC"
            )
            recommended_agents.append(
                "Upadacitinib 45mg QD x8w then 30mg QD — oral JAK1 (superior to adalimumab in QUARTZ)"
            )
            recommended_agents.append(
                "Tofacitinib 10mg BID x8w then 5mg BID — oral JAK (rapid onset)"
            )
            recommended_agents.append(
                "Risankizumab 1200mg IV x3 then 360mg SC Q8W — IL-23 inhibitor"
            )
            recommended_agents.append(
                "Mirikizumab 300mg IV x3 then 200mg SC Q4W — IL-23 inhibitor (FDA 2023)"
            )
            recommended_agents.append(
                "Infliximab 5mg/kg IV Q8W — anti-TNF (rapid onset, EIM benefit)"
            )
            recommended_agents.append("Ozanimod 0.92mg QD — S1P modulator (oral)")
        else:
            induction_therapy = (
                "Mild-moderate extensive UC: oral 5-ASA + consider biologic if inadequate "
                "response at 4–8 weeks. "
                "Oral mesalamine 4.8g/day (MMX formulation) + topical mesalamine for "
                "combination benefit."
            )
            recommended_agents.append("Oral mesalamine 4.8g/day (MMX)")
            recommended_agents.append("Topical mesalamine enema 4g/day")
            recommended_agents.append(
                "Prednisone 40–60mg/day (bridge if needed — taper over 8–12 weeks)"
            )
    elif prior_therapy == "failed_5asa" or prior_therapy == "failed_immunomodulator":
        induction_therapy = (
            "5-ASA/immunomodulator failure: escalate to biologic therapy "
            "(AGA 2025 Strong Recommendation). "
            "Vedolizumab or anti-TNF as first biologic. "
            "Consider JAK inhibitor (upadacitinib) for rapid onset if needed."
        )
        biologic_selection = (
            "First biologic selection post-5-ASA/immunomodulator failure: "
            "Vedolizumab preferred (gut-selective, favorable safety, most UC-specific data). "
            "Anti-TNF (infliximab) if rapid response needed or EIM present. "
            "Upadacitinib if oral therapy preferred and no JAK contraindications."
        )
        recommended_agents.append("Vedolizumab 300mg IV Q8W (preferred — gut-selective)")
        recommended_agents.append("Infliximab 5mg/kg IV Q8W (rapid onset)")
        recommended_agents.append("Upadacitinib 45mg QD x8w then 30mg QD (oral)")
        recommended_agents.append("Tofacitinib 10mg BID x8w (oral — rapid onset)")
    elif prior_therapy == "failed_anti_tnf":
        induction_therapy = (
            "Anti-TNF failure: switch to non-anti-TNF mechanism. "
            "Assess reason for failure: primary non-response vs secondary loss of response "
            "(check drug levels/antibodies)."
        )
        biologic_selection = (
            "Post-anti-TNF options (AGA 2025): "
            "1) Vedolizumab — GEMINI: effective post-anti-TNF. "
            "2) Ustekinumab — UNIFI: effective post-anti-TNF. "
            "3) IL-23 inhibitors (risankizumab, mirikizumab) — effective post-anti-TNF. "
            "4) JAK inhibitors (upadacitinib, tofacitinib) — effective post-anti-TNF, rapid onset."
        )
        recommended_agents.append("Vedolizumab 300mg IV Q8W")
        recommended_agents.append("Upadacitinib 45mg QD x8w then 30mg QD")
        recommended_agents.append("Risankizumab 1200mg IV x3 then 360mg SC Q8W")
        recommended_agents.append("Mirikizumab 300mg IV x3 then 200mg SC Q4W")
        recommended_agents.append("Ustekinumab 260–520mg IV then 90mg SC Q8W")
    elif (
        prior_therapy == "failed_vedolizumab"
        or prior_therapy == "failed_multiple_biologics"
    ):
        induction_therapy = (
            "Multiple biologic failure: consider remaining mechanisms. "
            "JAK inhibitors (upadacitinib, tofacitinib) effective post-multiple biologic failure. "
            "S1P modulators (ozanimod, etrasimod) as additional options. "
            "Colectomy discussion if refractory to ≥2 biologics."
        )
        biologic_selection = (
            "Refractory UC options: "
            "1) Upadacitinib 45mg QD (JAK1 — effective post-multiple biologic failure). "
            "2) Tofacitinib 10mg BID (JAK — rapid onset). "
            "3) Ozanimod/Etrasimod (S1P modulators). "
            "4) Colectomy: curative option — total proctocolectomy with IPAA "
            "(ileal pouch-anal anastomosis)."
        )
        recommended_agents.append(
            "Upadacitinib 45mg QD x8w then 30mg QD (if no JAK contraindications)"
        )
        recommended_agents.append("Tofacitinib 10mg BID x8w (rapid onset)")
        recommended_agents.append("Ozanimod 0.92mg QD (S1P modulator)")
        recommended_agents.append("Etrasimod 2mg QD (S1P modulator)")
        recommended_agents.append("Surgical consultation for colectomy discussion")
        urgent_flags.append(
            "Multiple biologic failure: colectomy discussion recommended — curative option "
            "with good quality-of-life outcomes"
        )
    else:
        induction_therapy = "Optimize current therapy. Check drug levels and anti-drug antibodies."
        recommended_agents.append("Therapeutic drug monitoring (TDM)")

    # ─── Maintenance Therapy ──────────────────────────────────────────────────
    maintenance_therapy = (
        "Maintenance principles (ACG 2025): "
        "1) All patients who achieve remission should continue maintenance therapy indefinitely. "
        "2) 5-ASA maintenance for mild-moderate UC (mesalamine 2g/day minimum). "
        "3) Biologic maintenance for moderate-severe UC or steroid-dependent disease. "
        "4) Steroids are NOT maintenance — taper and discontinue. "
        "5) Treat-to-target: endoscopic remission (Mayo endoscopic subscore 0–1) + "
        "fecal calprotectin <150μg/g."
    )

    # ─── Colectomy Consideration ──────────────────────────────────────────────
    if has_perforation or has_colon_dilation:
        colectomy_consideration = (
            "EMERGENCY COLECTOMY: perforation or toxic megacolon — immediate surgical "
            "intervention required."
        )
    elif is_steroid_refractory and is_hospitalized:
        colectomy_consideration = (
            "Steroid-refractory acute severe UC: colectomy is curative and life-saving if "
            "rescue therapy fails. "
            "Total proctocolectomy with IPAA (ileal pouch-anal anastomosis) — excellent "
            "long-term outcomes. "
            "Discuss with patient before starting rescue therapy."
        )
    elif prior_therapy == "failed_multiple_biologics":
        colectomy_consideration = (
            "Refractory UC after multiple biologic failures: colectomy is a reasonable and "
            "curative option. "
            "Quality of life after IPAA is generally good — comparable to medically managed "
            "remission. "
            "Multidisciplinary IBD team discussion recommended."
        )
    else:
        colectomy_consideration = (
            "No immediate colectomy indication. Monitor disease activity and therapy response."
        )

    # ─── Monitoring Plan ──────────────────────────────────────────────────────
    monitoring_plan = (
        "Monitoring (ACG 2025): "
        "Labs every 3 months: CBC, CMP, CRP, fecal calprotectin. "
        "Therapeutic drug monitoring (TDM) for anti-TNF: trough levels at 14 weeks, then "
        "annually or with loss of response. "
        "Colonoscopy at 6–12 months to assess endoscopic response (target Mayo endoscopic "
        "subscore 0–1). "
        "CRC surveillance: colonoscopy every 1–3 years after 8 years of extensive colitis. "
        "Annual skin exam (melanoma risk with anti-TNF + thiopurines). "
        "Bone density (DEXA) if on steroids >3 months."
    )

    if len(next_steps) == 0:
        next_steps.append(
            "Colonoscopy to confirm diagnosis and assess endoscopic severity"
        )
        next_steps.append(
            "Baseline labs: CBC, CMP, CRP, ESR, fecal calprotectin, albumin"
        )
        next_steps.append("Stool cultures + C. difficile PCR (exclude infectious trigger)")
        next_steps.append(
            "Infectious screening before biologic: TB (IGRA), hepatitis B/C, HIV"
        )
        next_steps.append("Vaccination update before immunosuppression")
        next_steps.append("IBD specialist referral")

    extent_str = str(extent).replace("_", " ") if extent is not None else "None"
    severity_str = str(severity).replace("_", " ") if severity is not None else "None"
    prior_str = (
        str(prior_therapy).replace("_", " ") if prior_therapy is not None else "None"
    )

    rationale = (
        f"UC extent: {extent_str}. "
        f"Severity: {severity_str}. "
        f"Prior therapy: {prior_str}. "
        f"Steroid dependent: {'Yes' if is_steroid_dependent else 'No'}. "
        f"Steroid refractory: {'Yes' if is_steroid_refractory else 'No'}. "
        f"Hospitalized: {'Yes' if is_hospitalized else 'No'}."
    )

    if severity == "acute_severe" or is_hospitalized:
        primary_recommendation = (
            "ACUTE SEVERE UC: hospitalize, IV steroids, surgical consultation on admission. "
            "Rescue therapy if no response at day 3–5."
        )
    elif (
        severity == "mild"
        and (extent == "proctitis" or extent == "left_sided")
        and prior_therapy == "none"
    ):
        primary_recommendation = (
            "Mild proctitis/left-sided UC: topical + oral 5-ASA is first-line therapy."
        )
    elif prior_therapy == "failed_multiple_biologics":
        primary_recommendation = (
            "Refractory UC after multiple biologic failures: JAK inhibitor or S1P modulator; "
            "colectomy discussion recommended."
        )
    else:
        primary_recommendation = (
            "Moderate-severe UC: biologic therapy indicated. Select based on mechanism, "
            "comorbidities, and patient preference."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "inductionTherapy": induction_therapy,
        "maintenanceTherapy": maintenance_therapy,
        "biologicSelection": biologic_selection,
        "acuteSevereUCPlan": acute_severe_uc_plan,
        "colectomyConsideration": colectomy_consideration,
        "urgentFlags": urgent_flags,
        "recommendedAgents": recommended_agents,
        "agentsToAvoid": agents_to_avoid,
        "monitoringPlan": monitoring_plan,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": [
            {
                "citation": "Rubin DT, et al. ACG Clinical Guideline: Ulcerative Colitis in Adults. Am J Gastroenterol. 2019;114(3):384-413.",
                "pmid": "30840605",
                "url": "https://pubmed.ncbi.nlm.nih.gov/30840605/",
            },
            {
                "citation": "AGA Clinical Practice Guideline on the Management of Moderate to Severely Active Ulcerative Colitis. Gastroenterology. 2025. (Living guideline)",
                "url": "https://www.gastro.org/practice-guidance/practice-updates/aga-clinical-practice-guideline-uc",
            },
            {
                "citation": "Feagan BG, et al. Vedolizumab as Induction and Maintenance Therapy for Ulcerative Colitis (GEMINI I). N Engl J Med. 2013;369(8):699-710.",
                "pmid": "23964932",
                "url": "https://pubmed.ncbi.nlm.nih.gov/23964932/",
            },
            {
                "citation": "Danese S, et al. Upadacitinib as Induction and Maintenance Therapy for Moderately to Severely Active Ulcerative Colitis (U-ACHIEVE). Lancet. 2022;399(10341):2113-2128.",
                "pmid": "35644162",
                "url": "https://pubmed.ncbi.nlm.nih.gov/35644162/",
            },
            {
                "citation": "D'Haens G, et al. Risankizumab as Induction and Maintenance Therapy for Ulcerative Colitis (INSPIRE). Lancet. 2023;401(10380):905-918.",
                "pmid": "36870383",
                "url": "https://pubmed.ncbi.nlm.nih.gov/36870383/",
            },
            {
                "citation": "Sandborn WJ, et al. Tofacitinib as Induction and Maintenance Therapy for Ulcerative Colitis (OCTAVE). N Engl J Med. 2017;376(18):1723-1736.",
                "pmid": "28467869",
                "url": "https://pubmed.ncbi.nlm.nih.gov/28467869/",
            },
        ],
    }
