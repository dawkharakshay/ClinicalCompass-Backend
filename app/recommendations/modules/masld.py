"""MASLD / MASH Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/masldLogic.ts (assessMASLD).

Decisions reproduced faithfully: noninvasive fibrosis staging (FIB-4 / LSM),
cardiometabolic risk, pharmacotherapy (resmetirom, semaglutide, pioglitazone),
liver biopsy indication, transplant evaluation.
"""

from __future__ import annotations

import math
from typing import Any

from app.recommendations.jslib import parse_float

LOGIC_KEY = "masld"

_REFERENCES = [
    {
        "citation": "Loomba R, et al. Resmetirom for Nonalcoholic Steatohepatitis with Liver Fibrosis (MAESTRO-NASH). N Engl J Med. 2024;390(6):497-509.",
        "pmid": "38324483",
        "url": "https://pubmed.ncbi.nlm.nih.gov/38324483/",
    },
    {
        "citation": "AGA Clinical Practice Update on Nonalcoholic Fatty Liver Disease 2023. Gastroenterology. 2023;165(6):1392-1405.",
        "pmid": "37678709",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37678709/",
    },
    {
        "citation": "Rinella ME, et al. AASLD Practice Guidance on the Clinical Assessment and Management of Nonalcoholic Fatty Liver Disease. Hepatology. 2023;77(5):1797-1835.",
        "pmid": "36727674",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36727674/",
    },
    {
        "citation": "Sanyal AJ, et al. Pioglitazone, Vitamin E, or Placebo for Nonalcoholic Steatohepatitis (PIVENS). N Engl J Med. 2010;362(18):1675-1685.",
        "pmid": "20427778",
        "url": "https://pubmed.ncbi.nlm.nih.gov/20427778/",
    },
    {
        "citation": "Newsome PN, et al. A Placebo-Controlled Trial of Subcutaneous Semaglutide in Nonalcoholic Steatohepatitis. N Engl J Med. 2021;384(12):1113-1124.",
        "pmid": "33185364",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33185364/",
    },
]


def _to_fixed2(x: float) -> str:
    """JS Number.prototype.toFixed(2)."""
    return f"{float(x):.2f}"


def _present(x: Any) -> bool:
    """JS ``x !== undefined`` — present iff a valid number was supplied.

    Numeric fields arrive as raw strings (see coerce.py); ``parse_float``
    yields NaN for missing/blank/non-numeric values, which mirrors the TS
    ``number | undefined`` "undefined" case that skips the numeric branch."""
    return not math.isnan(parse_float(x))


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    recommended_agents: list[str] = []
    next_steps: list[str] = []

    has_hcc = data.get("hasHCC")
    has_ascites = data.get("hasAscites")
    has_hepatic_encephalopathy = data.get("hasHepaticEncephalopathy")
    has_cirrhosis = data.get("hasCirchosis")
    meld_score = data.get("meldScore")
    fib4_score = data.get("fib4Score")
    lsm_kpa = data.get("lsm_kPa")
    alcohol = data.get("alcoholUseGramsPerDay")
    # Numeric fields arrive as raw strings; parse for comparisons while the
    # raw values remain for template interpolation (matches TS number output).
    meld_num = parse_float(meld_score)
    fib4_num = parse_float(fib4_score)
    lsm_num = parse_float(lsm_kpa)
    alcohol_num = parse_float(alcohol)
    mash_status = data.get("mashStatus")
    estimated_stage = data.get("estimatedFibrosisStage")
    diabetes_status = data.get("diabetesStatus")

    # ─── Urgent Flags ────────────────────────────────────────────────────────
    if has_hcc:
        urgent_flags.append(
            "HEPATOCELLULAR CARCINOMA: multidisciplinary liver tumor board review required — staging and treatment planning"
        )
    if has_ascites or has_hepatic_encephalopathy:
        urgent_flags.append(
            "DECOMPENSATED CIRRHOSIS: hepatology referral urgently — liver transplant evaluation, SBP prophylaxis, lactulose/rifaximin"
        )
    if _present(meld_score) and meld_num >= 15:
        urgent_flags.append(
            f"MELD score {meld_score} ≥15: liver transplant evaluation recommended — refer to transplant center"
        )
    if data.get("hasEsophagealVarices"):
        urgent_flags.append(
            "Esophageal varices: non-selective beta-blocker (propranolol/carvedilol) for primary prophylaxis; EGD surveillance every 1–3 years"
        )
    if _present(alcohol) and alcohol_num > 20:
        urgent_flags.append(
            f"Significant alcohol use ({alcohol}g/day): diagnosis may be ALD or mixed ALD/MASLD — alcohol cessation counseling required before MASLD pharmacotherapy"
        )

    # ─── Fibrosis Assessment ─────────────────────────────────────────────────
    fibrosis_assessment = ""
    fibrosis_risk = "low"

    if _present(fib4_score):
        if fib4_num < 1.3:
            fibrosis_risk = "low"
            fibrosis_assessment = (
                f"FIB-4 {_to_fixed2(fib4_num)} (<1.3): LOW risk of advanced fibrosis. "
                "No further fibrosis testing needed in low-risk patients. Reassess FIB-4 every 1–2 years."
            )
        elif fib4_num <= 2.67:
            fibrosis_risk = "intermediate"
            fibrosis_assessment = (
                f"FIB-4 {_to_fixed2(fib4_num)} (1.3–2.67): INTERMEDIATE risk. "
                "Proceed to secondary noninvasive test — FibroScan (LSM) or ELF score. "
                "Consider liver biopsy if secondary test indeterminate."
            )
            next_steps.append(
                "FibroScan (vibration-controlled transient elastography) for liver stiffness measurement"
            )
            next_steps.append("Consider ELF (Enhanced Liver Fibrosis) score")
        else:
            fibrosis_risk = "high"
            fibrosis_assessment = (
                f"FIB-4 {_to_fixed2(fib4_num)} (>2.67): HIGH risk of advanced fibrosis (F3–F4). "
                "Hepatology referral + liver biopsy or advanced imaging (MR elastography) recommended."
            )
            next_steps.append("Hepatology referral")
            next_steps.append("Liver biopsy or MR elastography for fibrosis staging")
            next_steps.append("HCC surveillance if cirrhosis confirmed")
    elif _present(lsm_kpa):
        if lsm_num < 8:
            fibrosis_risk = "low"
            fibrosis_assessment = (
                f"FibroScan LSM {lsm_kpa}kPa (<8kPa): LOW risk of advanced fibrosis (F0–F1). "
                "Annual monitoring with FIB-4."
            )
        elif lsm_num < 12:
            fibrosis_risk = "intermediate"
            fibrosis_assessment = (
                f"FibroScan LSM {lsm_kpa}kPa (8–12kPa): INTERMEDIATE — may have F2–F3 fibrosis. "
                "Consider liver biopsy for definitive staging."
            )
        else:
            fibrosis_risk = "high"
            fibrosis_assessment = (
                f"FibroScan LSM {lsm_kpa}kPa (≥12kPa): HIGH risk — likely F3–F4 fibrosis or cirrhosis. "
                "Hepatology referral + HCC surveillance."
            )
            urgent_flags.append(
                "FibroScan LSM ≥12kPa: likely advanced fibrosis/cirrhosis — hepatology referral and HCC surveillance required"
            )
    else:
        fibrosis_assessment = (
            "Noninvasive fibrosis assessment not yet performed. "
            "RECOMMENDED PATHWAY (AGA 2024): "
            "Step 1: Calculate FIB-4 index (age × AST / [PLT × √ALT]). "
            "Step 2: If FIB-4 1.3–2.67 → FibroScan or ELF score. "
            "Step 3: If high risk on secondary test → hepatology referral ± liver biopsy."
        )
        next_steps.append("Calculate FIB-4 index (requires age, AST, ALT, platelet count)")
        next_steps.append("FibroScan if FIB-4 intermediate (1.3–2.67)")

    # ─── Pharmacotherapy ─────────────────────────────────────────────────────
    pharmacotherapy = ""
    is_pharmacotherapy_candidate = (
        mash_status == "biopsy_confirmed_mash"
        or (estimated_stage == "F2" or estimated_stage == "F3")
        or fibrosis_risk == "high"
    )

    if has_cirrhosis and data.get("childPughScore") == "C":
        pharmacotherapy = (
            "Decompensated cirrhosis (Child-Pugh C): pharmacotherapy for MASH is not the priority. "
            "Focus on liver transplant evaluation, management of complications (ascites, varices, HE). "
            "Avoid hepatotoxic medications."
        )
    elif is_pharmacotherapy_candidate or (
        mash_status == "suspected_mash" and fibrosis_risk != "low"
    ):
        pharmacotherapy = (
            "PHARMACOTHERAPY FOR MASH WITH SIGNIFICANT FIBROSIS (F2–F3): "
            "1) RESMETIROM (Rezdiffra) 80–100mg QD — FIRST FDA-APPROVED MASH DRUG (March 2024). "
            "   THRβ agonist. MAESTRO-NASH trial: 26% MASH resolution without fibrosis worsening at 52 weeks. "
            "   Indicated for MASH with moderate-to-advanced fibrosis (F2–F3) in adults. "
            "   Dose: 80mg/day (BMI <35) or 100mg/day (BMI ≥35). "
            "   Avoid with moderate-severe hepatic impairment (Child-Pugh B/C). "
            "2) SEMAGLUTIDE (Ozempic/Wegovy) — GLP-1 agonist: MASH resolution in 59% (NASH CRN phase 2). "
            "   Phase 3 ESSENCE trial (semaglutide 2.4mg) results expected 2025. "
            "   Also addresses cardiometabolic comorbidities (T2DM, obesity, CV risk). "
            "3) TIRZEPATIDE (Mounjaro/Zepbound) — GLP-1/GIP dual agonist: SYNERGY-NASH trial ongoing. "
            "   Significant weight loss (>20%) and metabolic benefit. "
            "4) PIOGLITAZONE (Actos) — TZD: PIVENS trial: MASH resolution in 47% (non-diabetic). "
            "   Effective for MASH ± T2DM. Caution: weight gain, fluid retention, bladder cancer risk. "
            "5) VITAMIN E 800 IU/day — PIVENS trial: MASH resolution in 43% (non-diabetic, non-cirrhotic). "
            "   Avoid in men (prostate cancer risk), diabetics, and cirrhosis."
        )
        recommended_agents.append(
            "Resmetirom 80–100mg QD (FDA-approved for MASH F2–F3 — MAESTRO-NASH)"
        )
        recommended_agents.append("Semaglutide 2.4mg SC weekly (GLP-1 — ESSENCE trial pending)")
        recommended_agents.append("Tirzepatide 15mg SC weekly (GLP-1/GIP — SYNERGY-NASH)")
        recommended_agents.append("Pioglitazone 30–45mg QD (TZD — PIVENS trial)")
        recommended_agents.append("Vitamin E 800 IU/day (non-diabetic, non-cirrhotic only)")
    elif estimated_stage == "F0" or estimated_stage == "F1":
        pharmacotherapy = (
            "MASLD without significant fibrosis (F0–F1): pharmacotherapy not routinely indicated. "
            "Lifestyle modification is the cornerstone of treatment. "
            "GLP-1 agonists (semaglutide, tirzepatide) are appropriate if T2DM or obesity present. "
            "Reassess fibrosis annually with FIB-4."
        )
        if diabetes_status == "type2_diabetes" or data.get("hasObesity"):
            recommended_agents.append(
                "Semaglutide (Ozempic 1mg SC weekly for T2DM; Wegovy 2.4mg SC weekly for obesity)"
            )
            recommended_agents.append("Tirzepatide (Mounjaro for T2DM; Zepbound for obesity)")
            recommended_agents.append(
                "Metformin (T2DM — neutral effect on MASH but addresses cardiometabolic risk)"
            )
    else:
        pharmacotherapy = (
            "Fibrosis stage not definitively established. "
            "Complete noninvasive fibrosis assessment before initiating MASH-specific pharmacotherapy."
        )

    # ─── Liver Biopsy Indication ─────────────────────────────────────────────
    liver_biopsy_indication = ""
    if fibrosis_risk == "high" or (_present(fib4_score) and fib4_num > 2.67):
        liver_biopsy_indication = (
            "Liver biopsy INDICATED (AGA 2024): "
            "High-risk noninvasive fibrosis assessment (FIB-4 >2.67 or LSM ≥12kPa). "
            "Biopsy provides definitive MASH diagnosis and fibrosis staging. "
            "Required before initiating resmetirom (FDA label requires MASH diagnosis). "
            "Consider MR elastography as alternative to biopsy for fibrosis staging."
        )
        next_steps.append(
            "Liver biopsy or MR elastography for definitive MASH diagnosis and fibrosis staging"
        )
    elif fibrosis_risk == "intermediate":
        liver_biopsy_indication = (
            "Liver biopsy CONSIDER (AGA 2024): "
            "Intermediate-risk noninvasive assessment. "
            "Biopsy indicated if secondary noninvasive test (FibroScan, ELF) also indeterminate. "
            "Biopsy required if pharmacotherapy (resmetirom) planned."
        )
    else:
        liver_biopsy_indication = (
            "Liver biopsy NOT routinely indicated for low-risk MASLD (FIB-4 <1.3). "
            "Reassess with FIB-4 every 1–2 years."
        )

    # ─── Cardiometabolic Management ──────────────────────────────────────────
    cardiometabolic_management = (
        "CARDIOMETABOLIC MANAGEMENT (AGA 2024 — cardiovascular disease is the leading cause of death in MASLD): "
        "1) Statin therapy: safe in MASLD/MASH — may reduce liver inflammation. Use for CV risk reduction per ACC/AHA guidelines. "
        "2) GLP-1 agonists: address T2DM, obesity, and MASH simultaneously — preferred in T2DM + MASLD. "
        "3) SGLT2 inhibitors (empagliflozin, dapagliflozin): CV benefit + potential MASH benefit (EMPA-LIVER trial). "
        "4) Blood pressure control: target <130/80 mmHg. "
        "5) Dyslipidemia: statin + ezetimibe if needed. "
        "6) Aspirin: per CV risk guidelines."
    )

    if not data.get("isOnStatin") and data.get("hasCardiovascularDisease"):
        recommended_agents.append(
            "High-intensity statin (atorvastatin 40–80mg or rosuvastatin 20–40mg) — safe in MASLD, CV benefit"
        )

    # ─── Lifestyle Interventions ─────────────────────────────────────────────
    lifestyle_interventions = (
        "LIFESTYLE INTERVENTIONS (cornerstone of MASLD management): "
        "1) Weight loss: ≥5% body weight → reduces steatosis; ≥7–10% → MASH resolution; ≥10% → fibrosis improvement. "
        "2) Mediterranean diet: most evidence for MASLD — reduces liver fat and inflammation. "
        "3) Physical activity: 150–300 min/week moderate aerobic + resistance training. "
        "4) Alcohol: complete abstinence recommended for MASH with fibrosis. "
        "5) Fructose/sugar-sweetened beverages: avoid — accelerates hepatic steatosis. "
        "6) Coffee: 2–3 cups/day associated with reduced fibrosis progression."
    )

    # ─── Surveillance Plan ───────────────────────────────────────────────────
    surveillance_plan = ""
    if has_cirrhosis or estimated_stage == "F4_cirrhosis":
        surveillance_plan = (
            "Cirrhosis surveillance: "
            "HCC surveillance: liver ultrasound ± AFP every 6 months. "
            "EGD every 1–3 years for varices. "
            "Labs every 3–6 months: CBC, CMP, INR, AFP. "
            "MELD score calculation every 3–6 months."
        )
        next_steps.append("HCC surveillance: liver ultrasound + AFP every 6 months")
        next_steps.append("EGD for variceal screening")
    elif fibrosis_risk == "high":
        surveillance_plan = (
            "Advanced fibrosis (F3) surveillance: "
            "FIB-4 + FibroScan every 12 months. "
            "Consider HCC surveillance if cirrhosis develops. "
            "Hepatology follow-up every 6 months."
        )
    else:
        surveillance_plan = (
            "Low-intermediate fibrosis: "
            "FIB-4 every 1–2 years. "
            "Liver ultrasound annually if metabolic risk factors present. "
            "Reassess pharmacotherapy candidacy if FIB-4 increases."
        )

    # ─── Transplant Consideration ────────────────────────────────────────────
    transplant_consideration = "No immediate transplant evaluation indicated."
    if _present(meld_score) and meld_num >= 15:
        transplant_consideration = (
            f"MELD {meld_score} ≥15: liver transplant evaluation recommended. "
            "MASLD/MASH is now the leading indication for liver transplant in the US. "
            "Transplant outcomes in MASLD are good — 5-year survival ~70%. "
            "Cardiometabolic optimization required before transplant listing."
        )
    elif has_cirrhosis and (has_ascites or has_hepatic_encephalopathy):
        transplant_consideration = (
            "Decompensated cirrhosis: hepatology referral for transplant evaluation. "
            "MELD score calculation to determine transplant priority."
        )

    mash_status_label = str(mash_status).replace("_", " ") if mash_status is not None else "None"
    diabetes_label = (
        str(diabetes_status).replace("_", " ") if diabetes_status is not None else "None"
    )
    fib4_label = _to_fixed2(fib4_num) if _present(fib4_score) else "not calculated"

    rationale = (
        f"MASLD/MASH status: {mash_status_label}. "
        f"Estimated fibrosis stage: {estimated_stage}. "
        f"FIB-4: {fib4_label}. "
        f"Fibrosis risk: {fibrosis_risk}. "
        f"Diabetes: {diabetes_label}. "
        f"Cirrhosis: {'Yes' if has_cirrhosis else 'No'}."
    )

    if has_hcc:
        primary_recommendation = (
            "Hepatocellular carcinoma detected — multidisciplinary liver tumor board review required."
        )
    elif has_ascites or has_hepatic_encephalopathy:
        primary_recommendation = (
            "Decompensated cirrhosis — urgent hepatology referral and transplant evaluation."
        )
    elif is_pharmacotherapy_candidate:
        primary_recommendation = (
            "MASH with significant fibrosis (F2–F3): resmetirom (FDA-approved 2024) + GLP-1 agonist + lifestyle modification."
        )
    else:
        primary_recommendation = (
            "MASLD without significant fibrosis: lifestyle modification, cardiometabolic optimization, annual FIB-4 monitoring."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "fibrosisAssessment": fibrosis_assessment,
        "pharmacotherapy": pharmacotherapy,
        "liverBiopsyIndication": liver_biopsy_indication,
        "cardiometabolicManagement": cardiometabolic_management,
        "lifestyleInterventions": lifestyle_interventions,
        "surveillancePlan": surveillance_plan,
        "transplantConsideration": transplant_consideration,
        "urgentFlags": urgent_flags,
        "recommendedAgents": recommended_agents,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }
