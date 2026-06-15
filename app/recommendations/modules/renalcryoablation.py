"""Renal Cryoablation Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/renalCryoablationLogic.ts
(evaluateRenalCryoablation).

Guidelines: AUA 2021 Renal Mass Guidelines, SRU/SIR 2021 Ablation Guidelines,
NCCN Kidney Cancer 2024, ACR Appropriateness Criteria 2022.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "renalcryoablation"

_REFERENCES = [
    "Campbell S, et al. Renal Mass and Localized Renal Cancer: AUA Guideline. J Urol. 2021;206(2):199-217.",
    "Psutka SP, et al. Long-Term Oncologic Outcomes After Radiofrequency Ablation for T1 Renal Cell Carcinoma. J Urol. 2013;189(2):429-435.",
    "Schmit GD, et al. Percutaneous Cryoablation of Renal Masses >3 cm: Technical Considerations, Outcomes, and Tumor Size as a Predictor of Outcomes. AJR Am J Roentgenol. 2010;195(2):W181-W186.",
    "Atwell TD, et al. Percutaneous Renal Cryoablation: Experience Treating 115 Tumors. AJR Am J Roentgenol. 2008;191(6):1737-1742.",
    "NCCN Clinical Practice Guidelines in Oncology: Kidney Cancer. Version 3.2024. National Comprehensive Cancer Network.",
    "ACR Appropriateness Criteria: Local Treatment of Renal Cell Carcinoma. American College of Radiology. 2022.",
    "Ljungberg B, et al. EAU Guidelines on Renal Cell Carcinoma. Eur Urol. 2022;82(4):399-410.",
    "Georgiades CS, et al. Safety and Efficacy of Percutaneous Cryoablation for Stage 1a/b Renal Cell Carcinoma: Results of a Prospective, Single-Arm, 5-Year Study. Cardiovasc Intervent Radiol. 2014;37(6):1494-1499.",
]


def _fmt_num(x: float) -> str:
    """Render a number the way JS template literals do (no trailing .0 for ints)."""
    return str(int(x)) if float(x).is_integer() else str(x)


def _get_tumor_stage(size_cm: float) -> str:
    if size_cm <= 4:
        return "T1a"
    if size_cm <= 7:
        return "T1b"
    return "T2"


def _get_renal_score_category(score: float) -> str:
    if score <= 6:
        return "low"
    if score <= 9:
        return "intermediate"
    return "high"


def assess(data: dict) -> dict:
    tumor_size_cm = num(data.get("tumorSizeCm"), 0)
    renal_score = num(data.get("renalNephrometryScore"), 0)
    tumor_location = data.get("tumorLocation")
    contralateral = data.get("contralateralKidneyFunction")
    patient_age = num(data.get("patientAge"), 0)
    prior_nephrectomy = truthy(data.get("priorNephrectomy"))
    hereditary_syndrome = truthy(data.get("hereditarySyndrome"))
    multiple_ipsilateral = truthy(data.get("multipleIpsilateralTumors"))
    biopsy_performed = truthy(data.get("biopsyPerformed"))
    biopsy_result = data.get("biopsyResult")
    prior_ablation = truthy(data.get("priorAblation"))
    imaging_modality = data.get("imagingModality")

    comorbidities = data.get("comorbidities") or {}
    ckd = truthy(comorbidities.get("ckd"))
    diabetes = truthy(comorbidities.get("diabetes"))
    cardiopulmonary = truthy(comorbidities.get("cardiopulmonaryDisease"))
    anticoagulation = truthy(comorbidities.get("anticoagulation"))

    stage = _get_tumor_stage(tumor_size_cm)
    renal_category = _get_renal_score_category(renal_score)
    rationale: list[str] = []
    warnings: list[str] = []
    technical_considerations: list[str] = []

    # --- Primary indication assessment ---
    recommendation = "not_indicated"
    cor = "III"
    loe = "C"

    # T1a tumors — strongest indication
    if stage == "T1a":
        if renal_category in ("low", "intermediate"):
            recommendation = "indicated"
            cor = "I"
            loe = "B"
            rationale.append(
                "T1a renal mass (≤4 cm) with low-to-intermediate R.E.N.A.L. nephrometry score: thermal ablation is a guideline-endorsed alternative to partial nephrectomy (AUA 2021, Grade B)."
            )
            rationale.append(
                "Cryoablation achieves 5-year local recurrence-free survival of 90–95% for T1a tumors, comparable to surgical outcomes in appropriately selected patients (Psutka SP, et al. J Urol 2013)."
            )
        else:
            recommendation = "consider"
            cor = "IIa"
            loe = "B"
            rationale.append(
                "T1a renal mass with high R.E.N.A.L. score (≥10): cryoablation may be considered but carries higher local recurrence risk due to complex anatomy. Partial nephrectomy preferred if surgically feasible."
            )

    # T1b tumors — conditional indication
    if stage == "T1b":
        if (
            patient_age >= 70
            or cardiopulmonary
            or contralateral != "normal"
            or prior_nephrectomy
        ):
            recommendation = "consider"
            cor = "IIa"
            loe = "B-NR"
            rationale.append(
                "T1b renal mass (4–7 cm): cryoablation may be considered in patients with high surgical risk (age ≥70, significant comorbidities, reduced contralateral function, or prior nephrectomy) where partial nephrectomy carries prohibitive risk."
            )
            rationale.append(
                "AUA 2021 guidelines support ablation for T1b tumors in patients who are poor surgical candidates, acknowledging higher local recurrence rates compared to T1a (approximately 10–15% at 5 years)."
            )
        else:
            recommendation = "consider"
            cor = "IIb"
            loe = "B-NR"
            rationale.append(
                "T1b renal mass in a surgically fit patient: partial nephrectomy is preferred per AUA 2021 guidelines. Cryoablation may be considered as an alternative if the patient declines surgery after informed discussion of comparative outcomes."
            )
            warnings.append(
                "Partial nephrectomy is the preferred treatment for T1b tumors in surgically fit patients. Local recurrence rates after ablation are higher for tumors >4 cm."
            )

    # T2 tumors — generally not indicated
    if stage == "T2":
        recommendation = "not_indicated"
        cor = "III"
        loe = "B-NR"
        rationale.append(
            "T2 renal mass (>7 cm): thermal ablation is generally not recommended as primary treatment due to high local recurrence rates and inability to achieve adequate ablation margins. Radical or partial nephrectomy is preferred."
        )
        warnings.append(
            "Tumor size >7 cm is outside standard ablation criteria. Cryoablation may be considered only in exceptional circumstances (e.g., solitary kidney, severe comorbidities precluding surgery) with multidisciplinary team input."
        )

    # Hereditary syndrome — upgrade indication
    if hereditary_syndrome and stage != "T2":
        if recommendation == "consider":
            recommendation = "indicated"
        rationale.append(
            "Hereditary renal cell carcinoma syndrome (VHL, HLRCC, BHD, or other): ablation is preferred over nephrectomy to preserve nephrons given the high likelihood of future ipsilateral or contralateral tumors (AUA 2021, Grade A)."
        )

    # Multiple ipsilateral tumors
    if multiple_ipsilateral and stage != "T2":
        rationale.append(
            "Multiple ipsilateral renal tumors: nephron-sparing approach (ablation or partial nephrectomy) is strongly preferred to minimize risk of renal functional loss requiring dialysis."
        )

    # Solitary kidney / CKD
    if contralateral == "solitary" or ckd:
        if recommendation == "not_indicated" and stage == "T1b":
            recommendation = "consider"
            cor = "IIa"
        rationale.append(
            "Solitary kidney or CKD stage 3+: nephron-sparing ablation is preferred over radical nephrectomy to preserve renal function and reduce risk of dialysis dependence (AUA 2021, Grade A)."
        )
        warnings.append(
            "Post-procedure renal function monitoring is essential. Baseline and 3-month eGFR should be documented. Contrast nephropathy risk should be mitigated with pre-procedure hydration and minimization of contrast volume."
        )

    # Anticoagulation
    if anticoagulation:
        warnings.append(
            "Patient is on anticoagulation therapy. Bridging protocol or temporary discontinuation should be coordinated with prescribing physician prior to procedure. Cryoablation carries lower bleeding risk than radiofrequency ablation due to the cryogenic hemostatic effect."
        )

    # Biopsy
    if not biopsy_performed:
        warnings.append(
            "Pre-ablation biopsy has not been performed. AUA 2021 and NCCN 2024 guidelines recommend percutaneous renal mass biopsy prior to ablation to confirm malignancy and guide treatment planning. Oncocytoma and angiomyolipoma are benign and may not require treatment."
        )
    elif biopsy_result in ("oncocytoma", "angiomyolipoma"):
        recommendation = "consider"
        cor = "IIb"
        warnings.append(
            f"Biopsy result: {biopsy_result}. This is a benign lesion. Active surveillance is an appropriate alternative to ablation. Ablation may be considered for symptomatic, enlarging, or high-risk lesions (e.g., AML >4 cm with hemorrhage risk)."
        )
    elif biopsy_result == "indeterminate":
        warnings.append(
            "Indeterminate biopsy result: repeat biopsy or multidisciplinary tumor board review is recommended before proceeding with ablation."
        )

    # Prior ablation (re-ablation)
    if prior_ablation:
        rationale.append(
            "Prior ablation with local recurrence or incomplete treatment: re-ablation is a reasonable option for small residual or recurrent tumors, with success rates of 80–90% for lesions ≤3 cm (Psutka SP, et al. J Urol 2013)."
        )

    # Technical considerations
    if tumor_location == "hilar":
        technical_considerations.append(
            "Hilar tumor location: proximity to renal pelvis and collecting system requires careful probe placement and temperature monitoring to avoid urothelial injury. Consider hydrodissection or retrograde ureteral cooling."
        )
    if tumor_location == "endophytic":
        technical_considerations.append(
            "Endophytic tumor: MRI guidance preferred over CT for real-time ice ball monitoring. Ensure adequate ablation margin (≥5 mm) beyond tumor boundary."
        )
    if renal_score >= 10:
        technical_considerations.append(
            "High R.E.N.A.L. nephrometry score (≥10): complex anatomy increases technical difficulty. Consider MRI-guided cryoablation for superior soft tissue contrast. Multidisciplinary planning with urology is recommended."
        )
    if imaging_modality == "ultrasound":
        technical_considerations.append(
            "Ultrasound guidance: adequate for exophytic tumors but limited for endophytic or hilar lesions. CT or MRI guidance preferred for complex anatomy."
        )
    if diabetes:
        technical_considerations.append(
            "Diabetes mellitus: increased risk of post-procedure infection. Perioperative glucose management and prophylactic antibiotics per institutional protocol are recommended."
        )

    # Build summary
    size_str = _fmt_num(tumor_size_cm)
    score_str = _fmt_num(renal_score)
    if recommendation == "indicated":
        summary = (
            f"Renal cryoablation is INDICATED for this {size_str} cm {stage} renal mass "
            f"(R.E.N.A.L. score {score_str}, {renal_category} complexity). Supported by AUA "
            f"2021 guidelines with Class {cor} / Level {loe} evidence."
        )
    elif recommendation == "consider":
        summary = (
            f"Renal cryoablation MAY BE CONSIDERED for this {size_str} cm {stage} renal mass "
            f"(R.E.N.A.L. score {score_str}, {renal_category} complexity) based on patient-specific "
            f"factors. Class {cor} / Level {loe}."
        )
    else:
        summary = (
            f"Renal cryoablation is NOT RECOMMENDED as primary treatment for this {size_str} cm "
            f"{stage} renal mass. Surgical resection (partial or radical nephrectomy) is preferred."
        )

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": loe,
        "summary": summary,
        "rationale": rationale,
        "warnings": warnings,
        "technicalConsiderations": technical_considerations,
        "references": list(_REFERENCES),
    }
