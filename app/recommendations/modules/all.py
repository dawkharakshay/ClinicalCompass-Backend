"""Acute Lymphoblastic Leukemia & CAR-T Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/allLogic.ts (assessALL).

Sources (per the TS):
  NCCN ALL v2.2025, ESMO 2024, ASH 2021, ZUMA-3 (PMID 34097852),
  ELIANA (PMID 29385370), TOWER (PMID 28097305), ASCEND (PMID 33053285).
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float

LOGIC_KEY = "all"


# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_age_group(age: float) -> str:
    if age < 18:
        return "pediatric"
    if age < 40:
        return "aya"
    if age < 60:
        return "adult"
    return "older_adult"


def get_cart_label(eligibility: str) -> str:
    mapping = {
        "eligible_recommended": "CAR-T Recommended",
        "eligible_consider": "CAR-T — Consider",
        "not_eligible": "CAR-T — Not Eligible",
        "already_received": "Prior CAR-T Received",
    }
    return mapping[eligibility]


def get_cart_color(eligibility: str) -> str:
    mapping = {
        "eligible_recommended": "bg-green-900/30 border-green-600/50 text-green-300",
        "eligible_consider": "bg-blue-900/30 border-blue-600/50 text-blue-300",
        "not_eligible": "bg-slate-800/50 border-slate-600 text-slate-400",
        "already_received": "bg-amber-900/30 border-amber-600/50 text-amber-300",
    }
    return mapping[eligibility]


# ─── Core Logic ───────────────────────────────────────────────────────────────
def assess(data: dict) -> dict:
    # In TS, `age` and `ecogPS` are typed numbers and the booleans are real
    # booleans; the enums are string literals. We read them directly, mirroring
    # the JS reference equality / strict comparisons exactly.
    age = parse_float(data.get("age"))
    age_group = get_age_group(age)
    key_warnings: list[str] = []
    mrd_guided_actions: list[str] = []

    ecog_ps = data.get("ecogPS")
    lineage = data.get("lineage")
    phase = data.get("phase")
    ph_status = data.get("phStatus")
    cns_status = data.get("cnsStatus")
    fitness_status = data.get("fitnessStatus")
    mrd_status = data.get("mrdStatus")
    patient_preference = data.get("patientPreference")

    has_t315i = data.get("hasT315IMutation")
    has_kmt2a = data.get("hasKMT2ARearrangement")
    has_bcrabl1_like = data.get("hasBCRABL1Like")
    has_hypodiploidy = data.get("hasHypodiploidy")
    has_tp53 = data.get("hasTP53Mutation")
    prior_lines = parse_float(data.get("priorLines"))
    prior_blinatumomab = data.get("priorBlinatumomab")
    prior_cart_cell = data.get("priorCARTCell")
    prior_hct = data.get("priorHCT")
    has_hla_matched_donor = data.get("hasHLAMatchedDonor")

    # ── BSC ──────────────────────────────────────────────────────────────────
    if patient_preference == "bsc" or ecog_ps == 4:
        return {
            "primaryRecommendation": "bsc_only",
            "primaryLabel": "Best Supportive Care",
            "primaryRationale": "Patient preference or ECOG PS 4. Focus on symptom management, transfusion support, and palliative care.",
            "cartEligibility": "not_eligible",
            "cartLabel": "CAR-T — Not Eligible",
            "cartRationale": "BSC intent; CAR-T not appropriate.",
            "bridgeTherapy": None,
            "transplantRecommendation": "Not indicated",
            "transplantRationale": "BSC intent.",
            "mrdGuidedActions": [],
            "keyWarnings": ["Ensure goals-of-care discussion is documented."],
            "clinicalTrialNote": "Supportive care trials may be appropriate.",
            "urgencyFlag": "routine",
        }

    # ── CNS3 emergent ─────────────────────────────────────────────────────────
    if cns_status == "cns3":
        key_warnings.append(
            "CNS3 disease: Initiate intrathecal chemotherapy immediately. Cranial radiation may be required for refractory CNS disease."
        )

    # ── MRD-guided actions ────────────────────────────────────────────────────
    if mrd_status == "positive_high" and phase != "relapsed_refractory":
        mrd_guided_actions.append(
            "MRD-high after induction: Consider blinatumomab consolidation to achieve MRD negativity before transplant (BLAST trial evidence)."
        )
        mrd_guided_actions.append(
            "Expedite HLA typing and donor search if not already initiated."
        )
    if mrd_status == "positive_low" and phase != "relapsed_refractory":
        mrd_guided_actions.append(
            "MRD-low: Intensify consolidation or add blinatumomab cycle. Reassess MRD after next cycle."
        )
    if mrd_status == "negative":
        mrd_guided_actions.append(
            "MRD-negative: Continue planned consolidation/maintenance. Transplant decision based on risk stratification."
        )

    # ── Ph-like ALL warning ───────────────────────────────────────────────────
    if has_bcrabl1_like:
        key_warnings.append(
            "Ph-like ALL: Identify specific kinase driver (ABL-class → TKI; JAK-STAT → ruxolitinib; CRLF2 → targeted therapy). Outcomes similar to Ph+ ALL without TKI."
        )

    # ── Hypodiploidy warning ──────────────────────────────────────────────────
    if has_hypodiploidy:
        key_warnings.append(
            "Hypodiploidy (<44 chromosomes): Very high-risk. Allo-HCT in CR1 strongly recommended regardless of MRD status."
        )

    # ── TP53 warning ──────────────────────────────────────────────────────────
    if has_tp53:
        key_warnings.append(
            "TP53 mutation: Associated with very poor prognosis. Clinical trial enrollment strongly recommended."
        )

    # ─────────────────────────────────────────────────────────────────────────
    # NEWLY DIAGNOSED
    # ─────────────────────────────────────────────────────────────────────────
    if phase == "newly_diagnosed":
        # Ph+ ALL — ASCEND regimen or TKI + steroids
        if ph_status == "positive":
            primary_rec = (
                "dasatinib_blinatumomab"
                if age < 60 and fitness_status == "fit"
                else "ph_positive_tki"
            )

            primary_label = (
                "Dasatinib + Blinatumomab (ASCEND Regimen)"
                if primary_rec == "dasatinib_blinatumomab"
                else "TKI + Corticosteroids ± Low-Intensity Chemotherapy"
            )

            primary_rationale = (
                "ASCEND trial (Foà R et al., NEJM 2020, PMID 33053285): Dasatinib + blinatumomab achieved 97% CMR at 24 months with no intensive chemotherapy. Preferred for fit adults <60 with Ph+ ALL. Ponatinib + blinatumomab is an alternative (GIMEMA LAL2116)."
                if primary_rec == "dasatinib_blinatumomab"
                else "For older/unfit patients with Ph+ ALL: TKI (dasatinib or ponatinib) + corticosteroids achieves high remission rates with reduced toxicity. Add blinatumomab if tolerated."
            )

            transplant_rec = (
                "Allo-HCT in CR1 recommended for Ph+ ALL achieving MRD-negative CR, particularly if high-risk features present."
                if has_hla_matched_donor
                else "Initiate urgent HLA typing and unrelated donor search. Allo-HCT in CR1 is standard of care for Ph+ ALL."
            )

            if has_t315i:
                key_warnings.append(
                    "T315I mutation detected: Ponatinib is the preferred TKI (active against T315I). Dasatinib and nilotinib are ineffective."
                )

            return {
                "primaryRecommendation": primary_rec,
                "primaryLabel": primary_label,
                "primaryRationale": primary_rationale,
                "cartEligibility": "not_eligible",
                "cartLabel": "CAR-T — Not Indicated (Newly Diagnosed)",
                "cartRationale": "CAR-T is reserved for relapsed/refractory ALL. Proceed with TKI-based induction.",
                "bridgeTherapy": None,
                "transplantRecommendation": transplant_rec,
                "transplantRationale": "Allo-HCT in CR1 is standard for Ph+ ALL. MRD-negative status before transplant is the primary goal.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": key_warnings,
                "clinicalTrialNote": "Consider GIMEMA LAL2116 (ponatinib + blinatumomab) or other Ph+ ALL trials.",
                "urgencyFlag": "urgent",
            }

        # Pediatric B-ALL
        if age_group == "pediatric" and lineage == "b_all":
            return {
                "primaryRecommendation": "pediatric_protocol",
                "primaryLabel": "COG AALL1732 / BFM-Based Pediatric Protocol",
                "primaryRationale": "Standard pediatric ALL therapy: Induction (vincristine, dexamethasone, asparaginase, anthracycline ± rituximab for CD20+), followed by MRD-guided consolidation and maintenance. 5-year OS >90% for standard-risk pediatric B-ALL.",
                "cartEligibility": "not_eligible",
                "cartLabel": "CAR-T — Not Indicated (Newly Diagnosed)",
                "cartRationale": "CAR-T (tisagenlecleucel) is approved for pediatric/AYA B-ALL in 2nd+ relapse.",
                "bridgeTherapy": None,
                "transplantRecommendation": (
                    "Allo-HCT in CR1 recommended for very high-risk features (hypodiploidy, KMT2A rearrangement, MRD-high after consolidation)."
                    if has_hypodiploidy or has_kmt2a
                    else "Allo-HCT not routinely indicated in CR1 for standard/high-risk pediatric B-ALL. Reserve for very high-risk or MRD-persistent disease."
                ),
                "transplantRationale": "COG risk stratification guides transplant decisions. MRD after consolidation is the primary determinant.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": key_warnings,
                "clinicalTrialNote": "Enroll in COG AALL1732 or successor trial if eligible.",
                "urgencyFlag": "urgent",
            }

        # AYA B-ALL (18–39)
        if age_group == "aya" and lineage == "b_all":
            return {
                "primaryRecommendation": "aya_protocol",
                "primaryLabel": "Pediatric-Inspired Protocol (CALGB 10403 / GRAALL)",
                "primaryRationale": "AYA patients (18–39) have superior outcomes with pediatric-inspired regimens vs adult HYPER-CVAD (CALGB 10403: 3-yr OS 73% vs ~50% with adult regimens). Includes high-dose asparaginase, vincristine, dexamethasone, and CNS prophylaxis.",
                "cartEligibility": "not_eligible",
                "cartLabel": "CAR-T — Not Indicated (Newly Diagnosed)",
                "cartRationale": "CAR-T reserved for R/R ALL.",
                "bridgeTherapy": None,
                "transplantRecommendation": (
                    "Allo-HCT in CR1 recommended for very high-risk features."
                    if has_hypodiploidy or has_kmt2a or has_bcrabl1_like
                    else "Allo-HCT in CR1 for MRD-positive after consolidation; continue maintenance if MRD-negative."
                ),
                "transplantRationale": "MRD status after consolidation is the primary determinant of transplant decision in AYA ALL.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": key_warnings,
                "clinicalTrialNote": "Consider GRAALL-2014 or institutional AYA ALL trial.",
                "urgencyFlag": "urgent",
            }

        # Adult B-ALL (40–59) fit
        if age_group == "adult" and lineage == "b_all" and fitness_status == "fit":
            return {
                "primaryRecommendation": "adult_induction",
                "primaryLabel": "HYPER-CVAD / MRC UKALL12 / Linker Protocol",
                "primaryRationale": "Fit adults (40–59) with B-ALL: HYPER-CVAD (cyclophosphamide, vincristine, doxorubicin, dexamethasone alternating with MTX/AraC) or MRC UKALL12. CR rates 80–90%; 5-yr OS 40–50%. Add rituximab for CD20+ disease.",
                "cartEligibility": "not_eligible",
                "cartLabel": "CAR-T — Not Indicated (Newly Diagnosed)",
                "cartRationale": "CAR-T reserved for R/R ALL.",
                "bridgeTherapy": None,
                "transplantRecommendation": "Allo-HCT in CR1 recommended for high-risk features or MRD-positive after consolidation.",
                "transplantRationale": "MRD negativity before transplant is the primary goal. Initiate HLA typing at diagnosis.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": key_warnings,
                "clinicalTrialNote": "Consider ECOG-ACRIN E1910 or institutional adult ALL trial.",
                "urgencyFlag": "urgent",
            }

        # Older adult B-ALL (≥60) or unfit
        if (age_group == "older_adult" or fitness_status != "fit") and lineage == "b_all":
            return {
                "primaryRecommendation": "blinatumomab_chemo",
                "primaryLabel": "Reduced-Intensity Induction + Blinatumomab",
                "primaryRationale": "Older/unfit adults with B-ALL: Mini-HYPER-CVD + inotuzumab ozogamicin (Kantarjian HM et al., Lancet Oncol 2018) or blinatumomab-based induction. Avoid high-dose anthracyclines. Blinatumomab consolidation improves MRD negativity rates.",
                "cartEligibility": "eligible_consider",
                "cartLabel": "CAR-T — Consider if R/R",
                "cartRationale": "If relapse occurs, brexucabtagene autoleucel (KTE-X19) is approved for adults ≥18 with R/R B-ALL (ZUMA-3). Fitness assessment required.",
                "bridgeTherapy": None,
                "transplantRecommendation": "Reduced-intensity conditioning (RIC) allo-HCT in CR1 for fit older adults with available donor. Non-myeloablative conditioning may be considered.",
                "transplantRationale": "RIC allo-HCT is feasible in selected patients ≥60 with adequate organ function and available donor.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": key_warnings,
                "clinicalTrialNote": "Consider SWOG S1318 or institutional older adult ALL trial.",
                "urgencyFlag": "urgent",
            }

        # T-ALL (any age, fit)
        if lineage == "t_all" and fitness_status == "fit":
            return {
                "primaryRecommendation": "pediatric_protocol" if age_group == "pediatric" else "adult_induction",
                "primaryLabel": "COG AALL0434 (T-ALL Arm)" if age_group == "pediatric" else "HYPER-CVAD or BFM-Based T-ALL Protocol",
                "primaryRationale": "T-ALL: Nelarabine-containing regimens improve outcomes (COG AALL0434: nelarabine added to augmented BFM improved EFS in pediatric T-ALL). Adults: HYPER-CVAD or BFM-based with nelarabine consolidation.",
                "cartEligibility": "not_eligible",
                "cartLabel": "CAR-T — Investigational for T-ALL",
                "cartRationale": "No FDA-approved CAR-T for T-ALL. CD7-targeted CAR-T and other constructs are in clinical trials. Fratricide is a key challenge.",
                "bridgeTherapy": None,
                "transplantRecommendation": "Allo-HCT in CR1 for high-risk T-ALL (early T-cell precursor, MRD-positive after consolidation).",
                "transplantRationale": "Early T-cell precursor (ETP) ALL is very high-risk; allo-HCT in CR1 is recommended.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": [*key_warnings, "ETP-ALL (Early T-cell Precursor): Very high-risk subset. Confirm ETP immunophenotype and consider allo-HCT in CR1."],
                "clinicalTrialNote": "Consider CD7-targeted CAR-T trials for R/R T-ALL (NCT04033302 and others).",
                "urgencyFlag": "urgent",
            }

    # ─────────────────────────────────────────────────────────────────────────
    # MRD-POSITIVE (post-induction or consolidation)
    # ─────────────────────────────────────────────────────────────────────────
    if phase == "mrd_positive":
        if lineage == "b_all":
            return {
                "primaryRecommendation": "blinatumomab_mono",
                "primaryLabel": "Blinatumomab (MRD-Positive B-ALL)",
                "primaryRationale": "BLAST trial (Gökbuget N et al., Blood 2018, PMID 29540344): Blinatumomab achieved MRD response in 78% of MRD-positive B-ALL patients in CR. FDA-approved for MRD-positive B-ALL. Administer 1–2 cycles; reassess MRD.",
                "cartEligibility": "eligible_consider",
                "cartLabel": "CAR-T — Consider if MRD Persists",
                "cartRationale": "If MRD persists after blinatumomab, consider CAR-T cell therapy before transplant.",
                "bridgeTherapy": None,
                "transplantRecommendation": "Allo-HCT after achieving MRD negativity. Do not proceed to transplant with MRD-positive disease if avoidable.",
                "transplantRationale": "MRD negativity before allo-HCT is the strongest predictor of post-transplant outcome.",
                "mrdGuidedActions": [
                    "Administer blinatumomab cycle 1 (28-day continuous infusion). Reassess MRD at end of cycle.",
                    "If MRD-negative after blinatumomab: Proceed to allo-HCT.",
                    "If MRD-positive after 2 cycles: Consider CAR-T or clinical trial.",
                ],
                "keyWarnings": [*key_warnings, "Cytokine release syndrome (CRS) and neurotoxicity monitoring required during blinatumomab infusion."],
                "clinicalTrialNote": "Consider enrollment in MRD-directed trials.",
                "urgencyFlag": "urgent",
            }

    # ─────────────────────────────────────────────────────────────────────────
    # RELAPSED / REFRACTORY
    # ─────────────────────────────────────────────────────────────────────────
    if phase == "relapsed_refractory":
        # Already received CAR-T
        if prior_cart_cell:
            key_warnings.append(
                "Prior CAR-T therapy: CAR-T re-infusion is generally not recommended. Consider clinical trial, inotuzumab (if not prior), or blinatumomab (if not prior)."
            )
            return {
                "primaryRecommendation": "clinical_trial",
                "primaryLabel": "Clinical Trial (Post-CAR-T R/R ALL)",
                "primaryRationale": "Post-CAR-T relapse has very poor prognosis. Standard salvage options are limited. Clinical trial enrollment is strongly recommended. Options include: bispecific antibodies (mosunetuzumab), novel CAR constructs, or allo-HCT if not previously performed.",
                "cartEligibility": "already_received",
                "cartLabel": "Prior CAR-T Received",
                "cartRationale": "Re-infusion of same CAR-T product is not standard. Novel CAR constructs (investigational) may be considered.",
                "bridgeTherapy": None if prior_blinatumomab else "Blinatumomab bridge if not previously received",
                "transplantRecommendation": "Prior HCT: Second allo-HCT has high TRM; consider only in selected patients on clinical trial." if prior_hct else "Allo-HCT if CR2 achieved and donor available.",
                "transplantRationale": "Post-CAR-T allo-HCT may consolidate responses in selected patients.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": key_warnings,
                "clinicalTrialNote": "Strongly recommend enrollment in post-CAR-T salvage trials.",
                "urgencyFlag": "urgent",
            }

        # Ph+ R/R ALL
        if ph_status == "positive" and lineage == "b_all":
            rec = "ponatinib_blinatumomab" if has_t315i else "blinatumomab_chemo"
            return {
                "primaryRecommendation": rec,
                "primaryLabel": "Ponatinib + Blinatumomab" if has_t315i else "Blinatumomab + TKI (Dasatinib/Ponatinib)",
                "primaryRationale": (
                    "T315I mutation: Ponatinib is the only active TKI. Combine with blinatumomab for R/R Ph+ ALL. Asciminib (STAMP inhibitor) is an emerging option."
                    if has_t315i
                    else "R/R Ph+ ALL: Blinatumomab + dasatinib or ponatinib. ZUMA-3 included Ph+ patients; CAR-T is an option after TKI failure."
                ),
                "cartEligibility": "eligible_recommended" if prior_blinatumomab else "eligible_consider",
                "cartLabel": "CAR-T Recommended (Post-Blinatumomab)" if prior_blinatumomab else "CAR-T — Consider",
                "cartRationale": "Brexucabtagene autoleucel (KTE-X19) is FDA-approved for adults with R/R B-ALL (ZUMA-3, PMID 34097852). Ph+ patients were included in ZUMA-3.",
                "bridgeTherapy": "Blinatumomab or TKI as bridge to CAR-T manufacturing",
                "transplantRecommendation": "Allo-HCT after achieving CR2/MRD-negative remission, if not previously transplanted.",
                "transplantRationale": "Allo-HCT consolidates CAR-T or salvage responses in Ph+ ALL.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": key_warnings,
                "clinicalTrialNote": "Consider GIMEMA LAL2116 successor trials or asciminib-based trials for T315I.",
                "urgencyFlag": "urgent",
            }

        # R/R B-ALL — CAR-T eligible (adult)
        if lineage == "b_all" and (age_group == "adult" or age_group == "older_adult") and not prior_cart_cell:
            cart_elig = "eligible_recommended" if prior_lines >= 1 else "eligible_consider"
            return {
                "primaryRecommendation": "cart_brexu",
                "primaryLabel": "Brexucabtagene Autoleucel (KTE-X19) — ZUMA-3",
                "primaryRationale": "ZUMA-3 (Shah BD et al., Lancet 2021, PMID 34097852): KTE-X19 achieved 71% overall remission rate in adults with R/R B-ALL. Median OS 18.2 months. FDA-approved for adults ≥18 with R/R B-ALL. Leukapheresis should be initiated promptly.",
                "cartEligibility": cart_elig,
                "cartLabel": "CAR-T Recommended (KTE-X19)",
                "cartRationale": "KTE-X19 is the preferred CAR-T for adult R/R B-ALL. Requires ECOG PS ≤2, adequate organ function, and no active CNS disease. Manufacturing time ~4 weeks — initiate leukapheresis immediately.",
                "bridgeTherapy": (
                    "Inotuzumab ozogamicin bridge (if not prior) or low-intensity chemotherapy"
                    if prior_blinatumomab
                    else "Blinatumomab bridge to CAR-T manufacturing (if not previously received)"
                ),
                "transplantRecommendation": "Allo-HCT after CAR-T-induced CR is recommended for eligible patients, particularly those with high-risk features.",
                "transplantRationale": "Post-CAR-T allo-HCT consolidates durable remission. Discuss with transplant team before CAR-T infusion.",
                "mrdGuidedActions": [
                    "Initiate leukapheresis immediately for CAR-T manufacturing.",
                    "Administer bridge therapy to maintain disease control during manufacturing.",
                    "MRD assessment at Day 28 post-CAR-T infusion.",
                ],
                "keyWarnings": [*key_warnings, "CRS and ICANS monitoring required. Ensure access to tocilizumab and ICU-level care.", "Tumor burden reduction before CAR-T may reduce CRS severity."],
                "clinicalTrialNote": "Consider ZUMA-3 successor trials or novel CAR constructs.",
                "urgencyFlag": "urgent",
            }

        # R/R B-ALL — CAR-T eligible (pediatric/AYA)
        if lineage == "b_all" and (age_group == "pediatric" or age_group == "aya") and not prior_cart_cell:
            return {
                "primaryRecommendation": "cart_tisa",
                "primaryLabel": "Tisagenlecleucel (Kymriah) — ELIANA Trial",
                "primaryRationale": "ELIANA trial (Maude SL et al., NEJM 2018, PMID 29385370): Tisagenlecleucel achieved 81% remission rate in pediatric/AYA patients with R/R B-ALL (≤25 years). 12-month EFS 50%. FDA-approved for patients ≤25 years with R/R B-ALL.",
                "cartEligibility": "eligible_recommended",
                "cartLabel": "CAR-T Recommended (Tisagenlecleucel)",
                "cartRationale": "Tisagenlecleucel (tisa-cel) is FDA-approved for patients ≤25 years with R/R or refractory B-ALL. Requires ≥2 prior lines or relapse after allo-HCT.",
                "bridgeTherapy": (
                    "Inotuzumab or low-intensity chemotherapy bridge"
                    if prior_blinatumomab
                    else "Blinatumomab bridge to CAR-T manufacturing"
                ),
                "transplantRecommendation": "Allo-HCT after tisa-cel CR is considered for high-risk patients. Discuss benefit vs risk of transplant after CAR-T.",
                "transplantRationale": "Post-tisa-cel allo-HCT may improve durability in selected high-risk patients.",
                "mrdGuidedActions": [
                    "Initiate leukapheresis. Manufacturing time ~3–4 weeks.",
                    "Bridge therapy to control disease during manufacturing.",
                    "MRD and B-cell aplasia assessment at Day 28.",
                ],
                "keyWarnings": [*key_warnings, "CRS and neurotoxicity monitoring. Tocilizumab must be available.", "B-cell aplasia is expected and confirms CAR-T persistence."],
                "clinicalTrialNote": "Consider ELIANA successor trials or CD19/CD22 bispecific CAR-T trials.",
                "urgencyFlag": "urgent",
            }

        # R/R T-ALL
        if lineage == "t_all":
            return {
                "primaryRecommendation": "clinical_trial",
                "primaryLabel": "Nelarabine ± Clinical Trial (R/R T-ALL)",
                "primaryRationale": "R/R T-ALL: Nelarabine (Arranon) is FDA-approved for R/R T-ALL/T-LBL (ORR ~36%). Combine with cyclophosphamide and etoposide (NECTAR regimen) for higher response rates. No approved CAR-T for T-ALL — clinical trial enrollment is strongly recommended.",
                "cartEligibility": "not_eligible",
                "cartLabel": "CAR-T — Investigational Only",
                "cartRationale": "No FDA-approved CAR-T for T-ALL. CD7-targeted CAR-T (NCT04033302) and other constructs are in trials. Fratricide and T-cell aplasia are key challenges.",
                "bridgeTherapy": "Nelarabine-based salvage as bridge to transplant or trial",
                "transplantRecommendation": "Allo-HCT in CR2 for eligible patients. Haploidentical donor is acceptable if MSD/MUD unavailable.",
                "transplantRationale": "Allo-HCT is the only potentially curative option for R/R T-ALL outside of clinical trials.",
                "mrdGuidedActions": mrd_guided_actions,
                "keyWarnings": [*key_warnings, "Nelarabine neurotoxicity: Monitor for peripheral neuropathy and CNS toxicity. Avoid concurrent intrathecal MTX during nelarabine."],
                "clinicalTrialNote": "Strongly recommend CD7 CAR-T trial (NCT04033302) or other T-ALL-specific trials.",
                "urgencyFlag": "urgent",
            }

    # Fallback
    return {
        "primaryRecommendation": "clinical_trial",
        "primaryLabel": "Clinical Trial / Specialist Consultation",
        "primaryRationale": "Insufficient information to generate a specific recommendation. Consult hematology/oncology specialist and consider clinical trial enrollment.",
        "cartEligibility": "not_eligible",
        "cartLabel": "CAR-T — Assessment Required",
        "cartRationale": "Complete disease characterization required before CAR-T eligibility assessment.",
        "bridgeTherapy": None,
        "transplantRecommendation": "Assess after complete disease characterization.",
        "transplantRationale": "Transplant decision requires complete risk stratification.",
        "mrdGuidedActions": mrd_guided_actions,
        "keyWarnings": key_warnings,
        "clinicalTrialNote": "Consult hematology specialist for personalized recommendation.",
        "urgencyFlag": "routine",
    }
