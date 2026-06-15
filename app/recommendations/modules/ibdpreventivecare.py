"""IBD Preventive Care Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/ibdPreventiveCareLogic.ts
(assessIBDPreventiveCare).

Based on: AGA Clinical Practice Update on Preventive Care in IBD (2023, 2025),
ACG Guidelines on Vaccination in IBD (2022), ECCO Consensus on Preventive
Medicine in IBD (2023).
"""

from __future__ import annotations

from datetime import datetime

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "ibdpreventivecare"


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    next_steps: list[str] = []

    immuno = data.get("currentImmunosuppression")
    high_or_combo = immuno == "high" or immuno == "combination"

    # ─── Urgent Flags ──────────────────────────────────────────────────
    if truthy(data.get("hasPortalVeinThrombosis")):
        urgent_flags.append(
            "PORTAL VEIN THROMBOSIS: anticoagulation required — LMWH or DOAC. "
            "IBD patients have 3x higher PVT risk. Hematology + hepatology referral."
        )
    if truthy(data.get("hasHepatitisB")) and high_or_combo:
        urgent_flags.append(
            "HEPATITIS B + BIOLOGIC: antiviral prophylaxis (entecavir or tenofovir) "
            "REQUIRED before starting biologic therapy — risk of HBV reactivation "
            "and fulminant hepatitis"
        )
    if truthy(data.get("hasHepatitisBCore")) and high_or_combo:
        urgent_flags.append(
            "Hepatitis B core antibody positive: monitor HBV DNA every 3 months "
            "during biologic therapy — consider prophylactic antiviral"
        )
    if truthy(data.get("hasLatentTB")) and high_or_combo:
        urgent_flags.append(
            "LATENT TB + BIOLOGIC: LTBI treatment required before starting anti-TNF "
            "(INH 9 months or rifampin 4 months). Vedolizumab/ustekinumab/IL-23 have "
            "lower TB reactivation risk."
        )
    if truthy(data.get("isHospitalized")) and truthy(data.get("hasActiveFlare")):
        urgent_flags.append(
            "Hospitalized IBD patient: DVT prophylaxis with LMWH required — IBD "
            "patients have 3x higher VTE risk during hospitalization"
        )
    if truthy(data.get("hasPriorDysplasia")):
        urgent_flags.append(
            "Prior dysplasia in IBD: annual colonoscopy with chromoendoscopy "
            "required — high CRC risk"
        )

    # ─── Vaccination Schedule ──────────────────────────────────────────
    vaccination_items: list[str] = []

    age_years = num(data.get("ageYears"), 0)

    if not truthy(data.get("hasHadInfluenzaThisYear")):
        vaccination_items.append(
            "Annual influenza vaccine (inactivated — SAFE in immunosuppressed; "
            "live intranasal NOT recommended)"
        )
        next_steps.append("Annual influenza vaccine (inactivated)")
    if not truthy(data.get("hasHadPneumococcalPCV15or20")):
        vaccination_items.append(
            "Pneumococcal PCV15 or PCV20 (conjugate) — recommended for all IBD "
            "patients on immunosuppression"
        )
        next_steps.append(
            "Pneumococcal PCV20 (or PCV15 followed by PPSV23 8 weeks later)"
        )
    if not truthy(data.get("hasHadHepatitisBVaccine")):
        vaccination_items.append(
            "Hepatitis B vaccine series (3-dose or 2-dose Heplisav-B) — check "
            "anti-HBs titer after series"
        )
        next_steps.append("Hepatitis B vaccine series")
    if not truthy(data.get("hasHadHPVVaccine")) and age_years <= 45:
        vaccination_items.append(
            "HPV vaccine (Gardasil 9) — recommended through age 45 for IBD patients "
            "on immunosuppression (higher cervical cancer risk)"
        )
        next_steps.append("HPV vaccine (Gardasil 9)")
    if not truthy(data.get("hasHadZosterVaccine")) and age_years >= 50:
        vaccination_items.append(
            "Shingrix (recombinant zoster vaccine) — SAFE in immunosuppressed; "
            "2-dose series. Recommended age ≥50 (or younger if on high-level "
            "immunosuppression)"
        )
        next_steps.append("Shingrix (recombinant zoster vaccine) — 2-dose series")
    if not truthy(data.get("hasHadVaricellaVaccine")) and immuno == "none":
        vaccination_items.append(
            "Varicella vaccine — LIVE vaccine: only give BEFORE starting "
            "immunosuppression (4 weeks before biologic initiation)"
        )
    if not truthy(data.get("hasHadMMRVaccine")) and immuno == "none":
        vaccination_items.append(
            "MMR vaccine — LIVE vaccine: only give BEFORE starting immunosuppression"
        )
    if not truthy(data.get("hasHadCOVID19Vaccine")):
        vaccination_items.append(
            "COVID-19 vaccine + booster (mRNA preferred — safe in immunosuppressed)"
        )
        next_steps.append("COVID-19 vaccine + booster")

    if len(vaccination_items) > 0:
        numbered = "\n".join(
            f"{i + 1}) {v}" for i, v in enumerate(vaccination_items)
        )
        vaccination_schedule = (
            "VACCINES DUE (AGA 2022 IBD Vaccination Guideline):\n"
            + numbered
            + "\n\nKEY RULE: Live vaccines (MMR, varicella, yellow fever, live "
            "influenza) are CONTRAINDICATED in patients on moderate-high "
            "immunosuppression. Give live vaccines ≥4 weeks before starting "
            "biologic therapy."
        )
    else:
        vaccination_schedule = (
            "Vaccination status appears up to date. Annual influenza vaccine "
            "reminder. Review at each visit."
        )

    # ─── Infection Risk Management ─────────────────────────────────────
    infection_risk_management = (
        "INFECTION RISK STRATIFICATION (AGA 2023): "
        + f"Current immunosuppression level: {immuno}. "
        + (
            "HIGHEST RISK: biologic + immunomodulator combination — monitor "
            "closely for opportunistic infections. "
            if immuno == "combination"
            else ""
        )
        + "Screening before biologic initiation: TB (IGRA), hepatitis B (HBsAg, "
        "anti-HBc, anti-HBs), hepatitis C, HIV, varicella IgG. "
        + "Annual TB screening during anti-TNF therapy. "
        + (
            "Histoplasmosis endemic area: Histoplasma urine antigen before "
            "anti-TNF initiation. "
            if truthy(data.get("hasHistoplasmosisRisk"))
            else ""
        )
        + (
            "Coccidioidomycosis endemic area: Coccidioides serology before "
            "anti-TNF initiation. "
            if truthy(data.get("hasCoccidioidomycosisRisk"))
            else ""
        )
        + "Avoid raw/undercooked foods and unpasteurized dairy. "
        + "Travel medicine consultation before international travel."
    )

    # ─── Cancer Surveillance ───────────────────────────────────────────
    cancer_surveillance_items: list[str] = []

    ibd_duration = num(data.get("ibdDurationYears"), 0)
    ibd_extent = data.get("ibdExtent")

    # CRC surveillance
    if ibd_duration >= 8 and (
        ibd_extent == "extensive"
        or ibd_extent == "pancolitis"
        or ibd_extent == "ileocolonic"
    ):
        interval = (
            "annual"
            if truthy(data.get("hasPSC")) or truthy(data.get("hasPriorDysplasia"))
            else "every 1–3 years"
        )
        cancer_surveillance_items.append(
            f"CRC surveillance colonoscopy {interval} with chromoendoscopy "
            "(IBD duration ≥8 years, extensive disease)"
        )
        last_year = data.get("ibdCRCSurveillanceLastYear")
        if not truthy(last_year) or (
            datetime.now().year - num(last_year, 0)
        ) > 1:
            next_steps.append(
                f"CRC surveillance colonoscopy with chromoendoscopy ({interval})"
            )

    # Cervical cancer
    if data.get("sex") == "female" and not truthy(
        data.get("hasHadCervicalCancerScreening")
    ):
        cancer_surveillance_items.append(
            "Annual cervical cancer screening (Pap + HPV co-test) — women on "
            "immunosuppression have higher cervical dysplasia risk"
        )
        next_steps.append("Annual cervical cancer screening (Pap + HPV)")

    # Skin cancer
    if not truthy(data.get("hasSkinExamLastYear")) and high_or_combo:
        cancer_surveillance_items.append(
            "Annual dermatology skin exam — anti-TNF + thiopurine combination "
            "increases non-melanoma skin cancer risk 4x"
        )
        next_steps.append(
            "Annual dermatology skin exam (melanoma + non-melanoma skin cancer "
            "surveillance)"
        )

    # Lymphoma risk
    current_medications = data.get("currentMedications") or []
    thiopurine_meds = {"azathioprine", "6-mp", "mercaptopurine"}
    if any(
        isinstance(m, str) and m.lower() in thiopurine_meds
        for m in current_medications
    ):
        cancer_surveillance_items.append(
            "Thiopurine use: hepatosplenic T-cell lymphoma risk (rare but fatal) "
            "— avoid thiopurine monotherapy in young males; prefer biologic "
            "monotherapy"
        )

    if len(cancer_surveillance_items) > 0:
        numbered = "\n".join(
            f"{i + 1}) {c}" for i, c in enumerate(cancer_surveillance_items)
        )
        cancer_surveillance = "CANCER SURVEILLANCE NEEDED:\n" + numbered
    else:
        cancer_surveillance = (
            "Cancer surveillance appears up to date. Continue scheduled "
            "surveillance per guidelines."
        )

    # ─── Bone Health ───────────────────────────────────────────────────
    cumulative_steroid_months = data.get("cumulativeSteroidMonths")
    needs_dexa = (
        (cumulative_steroid_months is not None and num(cumulative_steroid_months, 0) >= 3)
        or truthy(data.get("hasOsteoporosis"))
        or truthy(data.get("hasOsteopenia"))
        or not truthy(data.get("hasDEXALastYear"))
    )

    if needs_dexa:
        bone_health_plan = (
            "BONE HEALTH (AGA 2023): "
            + "DEXA scan recommended (cumulative steroid use ≥3 months or risk "
            "factors). "
            + "Calcium 1000–1200mg/day + Vitamin D 600–2000 IU/day "
            "supplementation. "
            + "Weight-bearing exercise. "
            + (
                "Osteoporosis confirmed: bisphosphonate therapy (alendronate 70mg "
                "weekly) — gastroenterology + endocrinology co-management. "
                if truthy(data.get("hasOsteoporosis"))
                else ""
            )
            + "Minimize steroid use — use budesonide (low systemic absorption) "
            "when possible."
        )
        if not truthy(data.get("isOnCalciumVitaminD")):
            next_steps.append(
                "Start calcium 1000mg/day + vitamin D 1000–2000 IU/day "
                "supplementation"
            )
        if not truthy(data.get("hasDEXALastYear")):
            next_steps.append("DEXA scan for bone density assessment")
    else:
        bone_health_plan = (
            "Bone health monitoring up to date. Continue calcium + vitamin D "
            "supplementation. DEXA every 2 years if on chronic steroids."
        )

    # ─── Thrombosis Risk ───────────────────────────────────────────────
    thrombosis_risk_management = (
        "THROMBOSIS RISK (IBD patients have 2–3x higher VTE risk): "
        + (
            "HOSPITALIZED: LMWH thromboprophylaxis required for all hospitalized "
            "IBD patients (AGA Strong Recommendation). "
            if truthy(data.get("isHospitalized"))
            else "Outpatient: assess VTE risk factors (active flare, immobility, "
            "prior VTE, surgery). "
        )
        + (
            "Prior VTE: anticoagulation discussion with hematology. "
            if truthy(data.get("hasVTEHistory"))
            else ""
        )
        + (
            "Portal vein thrombosis: anticoagulation required (LMWH or DOAC) — "
            "hepatology referral. "
            if truthy(data.get("hasPortalVeinThrombosis"))
            else ""
        )
        + "Avoid immobility during flares. "
        + "JAK inhibitors (tofacitinib, upadacitinib) have additional VTE risk — "
        "use with caution in patients with prior VTE or high CV risk."
    )

    # ─── Mental Health ─────────────────────────────────────────────────
    mental_health_screening = (
        "MENTAL HEALTH (AGA 2023 — depression/anxiety in 25–35% of IBD "
        "patients): "
        + (
            "PHQ-9 and GAD-7 screening recommended at each visit. "
            if not truthy(data.get("hasBeenScreenedForDepression"))
            else "Depression/anxiety screening performed. "
        )
        + (
            "Anxiety/depression identified: psychological support referral. CBT "
            "and IBD-specific psychotherapy have evidence for quality-of-life "
            "improvement. "
            if truthy(data.get("hasAnxietyDepression"))
            else ""
        )
        + "IBD nurse specialist or patient navigator improves outcomes. "
        + "IBD support groups (CCFA/Crohn's & Colitis Foundation) recommended."
    )

    if len(next_steps) == 0:
        next_steps.extend(
            [
                "Review vaccination status at each IBD visit",
                "Annual influenza vaccine",
                "Infection screening before biologic initiation (TB, HBV, HCV, "
                "HIV)",
                "CRC surveillance colonoscopy per IBD duration and extent",
                "Annual cervical cancer screening (women on immunosuppression)",
                "Annual dermatology skin exam (patients on anti-TNF + thiopurine)",
            ]
        )

    ibd_extent_display = (ibd_extent or "").replace("_", " ")
    rationale = (
        f"IBD type: {data.get('ibdType')}. "
        + f"Duration: {data.get('ibdDurationYears')} years. "
        + f"Extent: {ibd_extent_display}. "
        + f"Immunosuppression: {immuno}. "
        + f"PSC: {'Yes' if truthy(data.get('hasPSC')) else 'No'}. "
        + f"Prior dysplasia: {'Yes' if truthy(data.get('hasPriorDysplasia')) else 'No'}."
    )

    if len(urgent_flags) > 0:
        primary_recommendation = urgent_flags[0]
    elif len(vaccination_items) > 0:
        primary_recommendation = (
            f"{len(vaccination_items)} vaccination(s) due. Infection screening "
            "and cancer surveillance review recommended."
        )
    else:
        primary_recommendation = (
            "IBD preventive care review: vaccination, infection screening, "
            "cancer surveillance, and bone health appear up to date. Annual "
            "review recommended."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "vaccinationSchedule": vaccination_schedule,
        "infectionRiskManagement": infection_risk_management,
        "cancerSurveillance": cancer_surveillance,
        "boneHealthPlan": bone_health_plan,
        "thrombosisRiskManagement": thrombosis_risk_management,
        "mentalHealthScreening": mental_health_screening,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "B",
        "rationale": rationale,
        "references": [
            {
                "citation": "Farraye FA, et al. AGA Clinical Practice Guidelines "
                "on the Management of Moderate to Severe Ulcerative Colitis. "
                "Gastroenterology. 2020;158(5):1450-1461.",
                "pmid": "32068001",
                "url": "https://pubmed.ncbi.nlm.nih.gov/32068001/",
            },
            {
                "citation": "Rubin DT, et al. ACG Clinical Guideline: Ulcerative "
                "Colitis in Adults. Am J Gastroenterol. 2019;114(3):384-413.",
                "pmid": "30840605",
                "url": "https://pubmed.ncbi.nlm.nih.gov/30840605/",
            },
            {
                "citation": "Lichtenstein GR, et al. ACG Clinical Guideline: "
                "Vaccination in Patients with Inflammatory Bowel Disease. Am J "
                "Gastroenterol. 2022;117(3):409-426.",
                "pmid": "35167504",
                "url": "https://pubmed.ncbi.nlm.nih.gov/35167504/",
            },
            {
                "citation": "Lamb CA, et al. ECCO Consensus on Preventive Medicine "
                "in Inflammatory Bowel Disease. J Crohns Colitis. 2023;17(1):1-23.",
                "pmid": "35896083",
                "url": "https://pubmed.ncbi.nlm.nih.gov/35896083/",
            },
        ],
    }
