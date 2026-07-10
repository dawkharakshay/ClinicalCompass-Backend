"""Aplastic Anemia (AA) Clinical Compass pathway logic.

Ported 1:1 from old_static_code/client/src/lib/aplasticAnemiaLogic.ts
(assessAplasticAnemia + classifyAASeverity + label/color helpers).

Sources:
  ASH 2022 Guidelines for Aplastic Anemia (Bhatt VR et al., Blood Adv 2022, PMID 35255491)
  EBMT/EHA Severe Aplastic Anemia Guidelines 2024
  NCCN Guidelines: Aplastic Anemia v1.2025
  Eltrombopag + IST: Townsley DM et al., NEJM 2017, PMID 28564562
  Imetelstat in AA: Townsley et al., 2024
  Danazol in AA: Townsley DM et al., NEJM 2016, PMID 27959701
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "aplasticanemia"

# Static reference list surfaced as the card's "Supporting Guidelines & Evidence"
# section (auto-attached by app.recommendations.registry.get_evidence). Ported 1:1
# from the inline `const REFERENCES = [...]` array in
# old_static_code/client/src/pages/AplasticAnemiaCompass.tsx. URL-only entries fold
# the link into the description since _normalize_evidence keeps only
# title/source/description/pmid.
EVIDENCE = [
    {
        "title": "American Society of Hematology 2022 Guidelines for Aplastic Anemia",
        "source": "Bhatt VR et al.",
        "description": "Comprehensive ASH guidelines for diagnosis and management of aplastic anemia including transplant and IST recommendations.",
        "pmid": "35255491",
    },
    {
        "title": "Eltrombopag Added to Standard Immunosuppression for Aplastic Anemia",
        "source": "Townsley DM et al.",
        "description": "NEJM: hATG + CsA + eltrombopag achieved 94% overall response rate at 6 months in SAA.",
        "pmid": "28564562",
    },
    {
        "title": "Horse versus Rabbit Antithymocyte Globulin in Acquired Aplastic Anemia",
        "source": "Scheinberg P et al.",
        "description": "NEJM: hATG (horse ATG) superior to rATG (rabbit ATG) for first-line SAA treatment.",
        "pmid": "21345103",
    },
    {
        "title": "Danazol Treatment for Telomere Diseases",
        "source": "Townsley DM et al.",
        "description": "NEJM: Danazol improved telomere length and blood counts in telomere disease (dyskeratosis congenita).",
        "pmid": "27959701",
    },
    {
        "title": "EBMT/EHA Severe Aplastic Anemia Guidelines 2024",
        "source": "Risitano AM et al.",
        "description": "Updated EBMT/EHA guidelines for SAA management including haploidentical HCT recommendations. Available at: ebmt.org/education/guidelines.",
        "pmid": None,
    },
    {
        "title": "NCCN Clinical Practice Guidelines: Aplastic Anemia v1.2025",
        "source": "National Comprehensive Cancer Network",
        "description": "NCCN guidelines for aplastic anemia diagnosis, staging, and treatment.",
        "pmid": None,
    },
]


_SEVERITY_LABEL = {
    "non_severe": "Non-Severe AA",
    "severe": "Severe AA (SAA)",
    "very_severe": "Very Severe AA (vSAA)",
}

_SEVERITY_COLOR = {
    "non_severe": "bg-yellow-900/30 border-yellow-600/50 text-yellow-300",
    "severe": "bg-orange-900/30 border-orange-600/50 text-orange-300",
    "very_severe": "bg-red-900/30 border-red-600/50 text-red-300",
}


def classify_aa_severity(anc: float, reticulocytes: float, platelets: float) -> str:
    """Camitta criteria classification (classifyAASeverity)."""
    hypocellular_bm = True  # Assumed from clinical context
    if not hypocellular_bm:
        return "non_severe"

    severe_count = len(
        [
            c
            for c in [
                anc < 500,
                reticulocytes < 20000,
                platelets < 20,
            ]
            if c
        ]
    )

    if anc < 200:
        return "very_severe"  # vSAA: ANC <200
    if severe_count >= 2:
        return "severe"  # SAA: >=2 of 3 criteria
    return "non_severe"


def get_severity_label(severity: str) -> str:
    return _SEVERITY_LABEL[severity]


def get_severity_color(severity: str) -> str:
    return _SEVERITY_COLOR[severity]


def assess(data: dict) -> dict:
    # ── Inputs ────────────────────────────────────────────────────────────────
    age = num(data.get("age"), 0)
    ecog_ps = num(data.get("ecogPS"), 0)
    severity = data.get("severity")
    if severity is None:
        # Legacy form auto-classified severity from the CBC before assessment
        # (AplasticAnemiaCompass.tsx: classifyAASeverity({anc, reticulocytes,
        # platelets})); the seeded form submits the CBC but not severity.
        severity = classify_aa_severity(
            num(data.get("anc"), 0),
            num(data.get("reticulocytes"), 0),
            num(data.get("platelets"), 0),
        )
    etiology = data.get("etiology")
    inherited_type = data.get("inheritedType")

    has_pnh_clone = to_bool(data.get("hasPNHClone"))
    has_mds_features = to_bool(data.get("hasMDSFeatures"))
    has_clonal_cytogenetics = to_bool(data.get("hasClonalCytogenetics"))
    has_sf3b1_or_other_mds_mutation = to_bool(data.get("hasSF3B1OrOtherMDSMutation"))
    has_telomere_disease = to_bool(data.get("hasTelomereDisease"))

    prior_ist = to_bool(data.get("priorIST"))
    prior_hct = to_bool(data.get("priorHCT"))
    donor_availability = data.get("donorAvailability")
    patient_preference = data.get("patientPreference")
    prior_ist_response = data.get("priorISTResponse")

    key_warnings: list[str] = []
    monitoring_plan: list[str] = []
    second_line_options: list[str] = []  # noqa: F841 (parity with TS)

    # ── BSC ─────────────────────────────────────────────────────────────────
    if patient_preference == "bsc" or ecog_ps == 4:
        return {
            "primaryRecommendation": "bsc_only",
            "primaryLabel": "Best Supportive Care",
            "primaryRationale": "Transfusion support, infection prophylaxis, and growth factors as needed. Goals-of-care discussion documented.",
            "transplantRecommendation": "Not indicated",
            "transplantRationale": "BSC intent.",
            "secondLineOptions": [],
            "monitoringPlan": ["CBC with differential every 2–4 weeks", "Transfusion support as needed"],
            "keyWarnings": ["Ensure goals-of-care discussion is documented."],
            "urgencyFlag": "routine",
        }

    # ── Inherited AA — special considerations ─────────────────────────────────
    if inherited_type != "none" and etiology == "inherited":
        if inherited_type == "fanconi_anemia":
            key_warnings.append("Fanconi Anemia: Avoid standard conditioning regimens — use FA-specific reduced-intensity conditioning (fludarabine-based). Androgen therapy (danazol/oxymetholone) may provide temporary benefit. HCT is curative but requires FA-specific protocols.")
        if inherited_type == "dyskeratosis_congenita":
            key_warnings.append("Dyskeratosis Congenita / Telomeropathy: Danazol (androgen) can improve blood counts (Townsley DM et al., NEJM 2016). HCT has high risk of pulmonary/hepatic toxicity — use reduced-intensity conditioning. Screen family members for telomere disease.")
        if has_telomere_disease:
            key_warnings.append("Short telomeres detected: Consider danazol therapy. Standard IST (hATG+CsA) has lower response rates in telomeropathy. HCT conditioning must be modified.")

    # ── Clonal evolution warnings ─────────────────────────────────────────────
    if has_clonal_cytogenetics:
        key_warnings.append("Clonal cytogenetics (monosomy 7, del(5q), or complex): High risk of MDS/AML transformation. Allo-HCT is strongly recommended over IST.")
    if has_mds_features:
        key_warnings.append("MDS features on bone marrow biopsy: Reclassify as hypoplastic MDS. HCT is preferred over IST.")
    if has_sf3b1_or_other_mds_mutation:
        key_warnings.append("Somatic mutations (DNMT3A, ASXL1, SF3B1, etc.): Monitor for clonal evolution. Does not preclude IST but warrants closer surveillance.")

    # ── PNH clone ──────────────────────────────────────────────────────────────
    if has_pnh_clone:
        monitoring_plan.append("PNH clone detected: Monitor PNH clone size every 6 months. If clone >50% or thrombosis occurs, consider eculizumab.")

    # ── Non-severe AA ──────────────────────────────────────────────────────────
    if severity == "non_severe":
        if not prior_ist:
            return {
                "primaryRecommendation": "watch_wait",
                "primaryLabel": "Watch and Wait ± Supportive Care",
                "primaryRationale": "Non-severe AA without transfusion dependence: Observe with CBC monitoring every 4–8 weeks. Initiate treatment if progression to SAA/vSAA or transfusion dependence develops. Eltrombopag monotherapy is an option for transfusion-dependent non-severe AA.",
                "transplantRecommendation": "Not indicated for non-severe AA unless progression to SAA.",
                "transplantRationale": "Allo-HCT is reserved for SAA/vSAA or refractory disease.",
                "secondLineOptions": ["Eltrombopag monotherapy if transfusion-dependent", "IST (hATG + CsA) if progression to SAA"],
                "monitoringPlan": ["CBC with differential every 4–8 weeks", "Bone marrow biopsy if progression suspected", "PNH flow cytometry every 6–12 months", *monitoring_plan],
                "keyWarnings": key_warnings,
                "urgencyFlag": "routine",
            }

    # ── SAA/vSAA — First-line ──────────────────────────────────────────────────
    if not prior_ist and (severity == "severe" or severity == "very_severe"):
        # Young patient (<40) with MSD — HCT first-line
        if age < 40 and donor_availability == "hla_matched_sibling":
            return {
                "primaryRecommendation": "hct_msd_first_line",
                "primaryLabel": "Allo-HCT with HLA-Matched Sibling Donor (MSD) — First-Line",
                "primaryRationale": "ASH 2022 / EBMT 2024: For patients <40 years with SAA/vSAA and an available HLA-matched sibling donor, allo-HCT is the preferred first-line treatment. 5-year OS >90% with MSD-HCT in young patients. Cyclophosphamide + ATG conditioning is standard.",
                "transplantRecommendation": "Proceed to allo-HCT with MSD as soon as possible. Target <3 months from diagnosis to transplant.",
                "transplantRationale": "Delay in HCT increases transfusion burden and infection risk. Minimize transfusions before HCT to reduce alloimmunization.",
                "secondLineOptions": ["IST (hATG + CsA + eltrombopag) if HCT is delayed or patient declines", "MUD-HCT if MSD unavailable"],
                "monitoringPlan": ["Minimize blood product transfusions (use irradiated, leukoreduced products)", "Infection prophylaxis (antifungal, antibacterial, antiviral)", "HLA typing of patient and siblings", *monitoring_plan],
                "keyWarnings": [*key_warnings, "Minimize transfusions before HCT to reduce alloimmunization. Use leukoreduced, irradiated blood products.", "Avoid family member blood products (risk of alloimmunization to potential donor antigens)."],
                "urgencyFlag": "urgent",
            }

        # Age 40–60 with MSD — HCT vs IST discussion
        if age >= 40 and age < 60 and donor_availability == "hla_matched_sibling":
            return {
                "primaryRecommendation": "ist_hatg_csa_eltro",
                "primaryLabel": "hATG + CsA + Eltrombopag (First-Line IST) — MSD-HCT Alternative",
                "primaryRationale": "For patients 40–60 with MSD: Both IST and MSD-HCT are reasonable first-line options. EBMT 2024 recommends MSD-HCT up to age 50–60 in fit patients; ASH 2022 recommends IST for patients >40 with MSD. Discuss both options with patient. If IST chosen: hATG (horse ATG) + CsA + eltrombopag (NEJM 2017, PMID 28564562) — 94% response rate at 6 months.",
                "transplantRecommendation": "MSD-HCT is a viable first-line option for fit patients 40–60. If IST chosen, proceed to MSD-HCT if no response at 3–6 months.",
                "transplantRationale": "MSD-HCT outcomes are excellent even in patients 40–60. Discuss transplant vs IST based on patient preference, comorbidities, and institutional experience.",
                "secondLineOptions": ["MSD-HCT if IST fails (no response at 3–6 months)", "MUD-HCT if MSD-HCT not pursued and IST fails"],
                "monitoringPlan": ["CBC at 1, 2, 3, 6 months after IST", "CsA levels every 2 weeks initially", "Bone marrow biopsy at 3–6 months if no response", *monitoring_plan],
                "keyWarnings": [*key_warnings, "hATG (horse ATG, ATGAM) is preferred over rATG (rabbit ATG, Thymoglobulin) for first-line SAA (NEJM 2011, PMID 21345103).", "Eltrombopag must be started on Day 14 of hATG/CsA (not Day 1) to avoid early hepatotoxicity."],
                "urgencyFlag": "urgent",
            }

        # No MSD, age <40 — IST first, then MUD-HCT if IST fails
        if donor_availability != "hla_matched_sibling" and age < 40:
            return {
                "primaryRecommendation": "ist_hatg_csa_eltro",
                "primaryLabel": "hATG + CsA + Eltrombopag (First-Line IST)",
                "primaryRationale": "No MSD available: hATG + CsA + eltrombopag is first-line IST. NEJM 2017 (PMID 28564562): 94% overall response rate at 6 months with triple therapy. Initiate MUD search simultaneously — proceed to MUD-HCT if no response at 3–6 months.",
                "transplantRecommendation": "Initiate unrelated donor search immediately. Proceed to MUD-HCT (10/10 preferred) if no response to IST at 3–6 months.",
                "transplantRationale": "MUD-HCT outcomes in SAA have improved significantly with fludarabine-based conditioning. 5-year OS ~75–80% with MUD-HCT after IST failure.",
                "secondLineOptions": ["MUD-HCT (10/10) if IST fails", "Haploidentical HCT if MUD unavailable", "Eltrombopag continuation if partial response"],
                "monitoringPlan": ["CBC at 1, 2, 3, 6 months after IST", "CsA levels every 2 weeks", "Bone marrow biopsy at 3–6 months", "Unrelated donor search initiated at diagnosis", *monitoring_plan],
                "keyWarnings": [*key_warnings, "hATG preferred over rATG for first-line SAA.", "Start eltrombopag on Day 14 (not Day 1) of hATG/CsA."],
                "urgencyFlag": "urgent",
            }

        # Older adult (>=60) or unfit — IST preferred
        if age >= 60 or ecog_ps >= 2:
            return {
                "primaryRecommendation": "ist_hatg_csa_eltro",
                "primaryLabel": "hATG + CsA + Eltrombopag (First-Line IST)",
                "primaryRationale": "Older adults (≥60) or unfit patients: IST (hATG + CsA + eltrombopag) is preferred over HCT due to higher transplant-related mortality. Response rates remain high (~80–90%). Eltrombopag addition improves response rates and speed.",
                "transplantRecommendation": (
                    "Reduced-intensity conditioning (RIC) allo-HCT is an option for fit patients ≥60 with available donor after IST failure."
                    if donor_availability != "none"
                    else "Allo-HCT not recommended for patients ≥60 without available donor or with significant comorbidities."
                ),
                "transplantRationale": "RIC allo-HCT in selected patients ≥60 has improved outcomes with fludarabine-based conditioning.",
                "secondLineOptions": ["Eltrombopag monotherapy if IST contraindicated", "RIC allo-HCT if IST fails and patient is fit", "Danazol for telomeropathy"],
                "monitoringPlan": ["CBC monthly for 6 months, then every 2–3 months", "CsA levels every 2 weeks initially", "Bone marrow biopsy at 6 months", *monitoring_plan],
                "keyWarnings": [*key_warnings, "Monitor for cyclosporine nephrotoxicity and hypertension in older patients.", "Eltrombopag hepatotoxicity: Monitor LFTs monthly."],
                "urgencyFlag": "urgent",
            }

    # ── Refractory / Relapsed SAA ──────────────────────────────────────────────
    if prior_ist and (severity == "severe" or severity == "very_severe"):
        if prior_ist_response == "no_response" or prior_ist_response == "relapse":
            # Has donor — HCT
            if donor_availability != "none" and not prior_hct:
                rec = (
                    "hct_msd_first_line"
                    if donor_availability == "hla_matched_sibling"
                    else "hct_haplo"
                    if donor_availability == "haploidentical"
                    else "hct_mud"
                )

                return {
                    "primaryRecommendation": rec,
                    "primaryLabel": (
                        "Allo-HCT with MSD (Second-Line)"
                        if donor_availability == "hla_matched_sibling"
                        else "Haploidentical HCT (Post-IST Failure)"
                        if donor_availability == "haploidentical"
                        else "Allo-HCT with MUD (Second-Line)"
                    ),
                    "primaryRationale": "IST failure or relapse: Allo-HCT is the treatment of choice. Second-line IST (rATG or alemtuzumab) is an alternative if HCT is not feasible. EBMT 2024: Proceed to MUD-HCT without delay after IST failure.",
                    "transplantRecommendation": "Proceed to allo-HCT. Fludarabine-based conditioning (Flu/Cy/ATG) is preferred for MUD-HCT.",
                    "transplantRationale": "Second-line IST response rates are lower (~30–40%). HCT offers the best chance of long-term cure after IST failure.",
                    "secondLineOptions": ["Second-line IST (rATG + CsA ± eltrombopag) if HCT not feasible", "Eltrombopag monotherapy for partial responders"],
                    "monitoringPlan": ["Proceed to transplant evaluation immediately", "Infection prophylaxis and transfusion support", *monitoring_plan],
                    "keyWarnings": [*key_warnings, "Haploidentical HCT with post-transplant cyclophosphamide (PTCy) is increasingly used when MSD/MUD unavailable."],
                    "urgencyFlag": "urgent",
                }

            # No donor or prior HCT — second-line IST or eltrombopag
            return {
                "primaryRecommendation": "second_line_ist",
                "primaryLabel": "Second-Line IST (rATG + CsA ± Eltrombopag) or Eltrombopag Monotherapy",
                "primaryRationale": "No available donor or prior HCT: Second-line IST with rATG (rabbit ATG, Thymoglobulin) + CsA ± eltrombopag. Response rate ~30–40%. Eltrombopag monotherapy (Townsley DM et al., NEJM 2017) achieved trilineage response in 40% of refractory SAA patients.",
                "transplantRecommendation": "Haploidentical HCT should be explored if no prior HCT and response to second-line IST is inadequate.",
                "transplantRationale": "Haplo-HCT with PTCy has improved outcomes and is now a viable option when MSD/MUD unavailable.",
                "secondLineOptions": ["Eltrombopag monotherapy (150 mg/day)", "Haploidentical HCT with PTCy", "Clinical trial (imetelstat, luspatercept, novel agents)"],
                "monitoringPlan": ["CBC every 4 weeks", "Bone marrow biopsy at 3–6 months", "Monitor for clonal evolution (cytogenetics, NGS)", *monitoring_plan],
                "keyWarnings": [*key_warnings, "Monitor for clonal evolution (monosomy 7) with repeat bone marrow biopsy every 6–12 months.", "Eltrombopag: Monitor LFTs monthly. Discontinue if ALT >3× ULN."],
                "urgencyFlag": "urgent",
            }

        # Partial response — continue/optimize
        if prior_ist_response == "partial":
            return {
                "primaryRecommendation": "eltrombopag_mono",
                "primaryLabel": "Eltrombopag Optimization / Continuation",
                "primaryRationale": "Partial response to IST: Continue CsA and add/optimize eltrombopag (150 mg/day) if not already included. Reassess at 3–6 months. If no improvement, proceed to second-line IST or HCT.",
                "transplantRecommendation": (
                    "Consider allo-HCT if response is inadequate at 6 months."
                    if donor_availability != "none"
                    else "Optimize medical therapy; explore haploidentical HCT."
                ),
                "transplantRationale": "Partial response may be sufficient for some patients; full CR is the goal.",
                "secondLineOptions": ["Add eltrombopag if not already included", "Second-line IST (rATG) if no improvement", "HCT if donor available"],
                "monitoringPlan": ["CBC every 4–8 weeks", "CsA levels monthly", "Bone marrow biopsy at 6 months", *monitoring_plan],
                "keyWarnings": key_warnings,
                "urgencyFlag": "routine",
            }

    # Fallback
    return {
        "primaryRecommendation": "clinical_trial",
        "primaryLabel": "Clinical Trial / Specialist Consultation",
        "primaryRationale": "Consult hematology specialist for personalized recommendation.",
        "transplantRecommendation": "Assess after complete evaluation.",
        "transplantRationale": "Transplant decision requires complete risk stratification.",
        "secondLineOptions": [],
        "monitoringPlan": ["CBC with differential every 4 weeks", "Bone marrow biopsy as clinically indicated"],
        "keyWarnings": key_warnings,
        "urgencyFlag": "routine",
    }
