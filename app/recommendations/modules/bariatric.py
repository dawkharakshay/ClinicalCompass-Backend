"""Bariatric Surgery Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/bariatricLogic.ts
(calculateBariatricScore).

Based on the 2022 ASMBS/IFSO Guidelines for Bariatric and Metabolic Surgery
(Eisenberg D, et al. Surg Obes Relat Dis. 2022;18(12):1345-1356. PMID: 36280539),
the 2023 American Diabetes Association Standards of Care, and NICE Guideline
NG238 (2023).
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "bariatric"


def _fmt(value: float) -> str:
    """Render a numeric value the way JS string-interpolates it (no trailing .0)."""
    if value == int(value):
        return str(int(value))
    return repr(value)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0

    bmi = num(data.get("bmi"))
    bmi_str = _fmt(bmi)
    hba1c = num(data.get("hba1c"))
    hba1c_str = _fmt(hba1c)
    supervised = num(data.get("supervisedProgramDuration"))
    supervised_str = _fmt(supervised)

    type2_diabetes = truthy(data.get("type2Diabetes"))
    hypertension = truthy(data.get("hypertension"))
    sleep_apnea = truthy(data.get("sleepApnea"))
    nafld = truthy(data.get("nafld"))
    gerd = truthy(data.get("gerd"))
    osteoarthritis = truthy(data.get("osteoarthritis"))
    dyslipidemia = truthy(data.get("dyslipidemia"))
    heart_failure = truthy(data.get("heartFailure"))
    afib = truthy(data.get("afib"))
    pseudotumor_cerebri = truthy(data.get("pseudotumorCerebri"))
    psychological_clearance = truthy(data.get("psychologicalClearance"))
    nutrition_consult = truthy(data.get("nutritionConsultCompleted"))
    active_substance_abuse = truthy(data.get("activeSubstanceAbuse"))
    uncontrolled_psych = truthy(data.get("uncontrolledPsychiatricDisorder"))
    cirrhosis = truthy(data.get("cirrhosis"))
    prior_bariatric = truthy(data.get("priorBariatricSurgery"))
    esophageal_motility = truthy(data.get("esophagealMotilityDisorder"))
    procedure_type = data.get("procedureType")

    # BMI criteria — primary driver
    if bmi >= 40:
        bmi_category = "Class III Obesity (BMI ≥40)"
        score += 40
        key_findings.append(
            f"BMI {bmi_str} — Class III obesity; meets primary surgical criteria per ASMBS 2022 guidelines"
        )
    elif bmi >= 35:
        bmi_category = "Class II Obesity (BMI 35–39.9)"
        score += 30
        key_findings.append(
            f"BMI {bmi_str} — Class II obesity with comorbidities required for surgical candidacy"
        )
    elif bmi >= 30:
        bmi_category = "Class I Obesity (BMI 30–34.9)"
        score += 15
        key_findings.append(
            f"BMI {bmi_str} — Class I obesity; surgery appropriate if metabolic comorbidities present (2022 ASMBS guideline expansion)"
        )
    else:
        bmi_category = "BMI <30 — Below standard surgical threshold"
        warnings.append(
            f"BMI {bmi_str} — Below standard threshold for bariatric surgery; surgery not typically indicated"
        )
        score -= 20

    # Comorbidities — add to score for BMI 30–34.9; required for BMI 35–39.9
    comorbidity_count = sum(
        1
        for flag in [
            type2_diabetes,
            hypertension,
            sleep_apnea,
            nafld,
            dyslipidemia,
            heart_failure,
            afib,
            pseudotumor_cerebri,
            osteoarthritis,
        ]
        if flag
    )

    if comorbidity_count >= 2:
        score += 20
        key_findings.append(
            f"{comorbidity_count} obesity-related comorbidities — strong indication for metabolic surgery"
        )
    elif comorbidity_count == 1:
        score += 10
        key_findings.append(f"{comorbidity_count} obesity-related comorbidity present")
    elif bmi < 40:
        warnings.append(
            "No obesity-related comorbidities documented — required for BMI <40 per most payer criteria"
        )

    # Type 2 diabetes — metabolic surgery benefit
    if type2_diabetes:
        score += 15
        if hba1c >= 8:
            key_findings.append(
                f"T2DM with HbA1c {hba1c_str}% — poorly controlled; metabolic surgery achieves remission in 50–80% of patients"
            )
        else:
            key_findings.append(
                f"T2DM with HbA1c {hba1c_str}% — metabolic surgery recommended per ADA Standards of Care 2023"
            )

    # Sleep apnea
    if sleep_apnea:
        key_findings.append(
            "Obstructive sleep apnea — significant improvement/resolution expected post-surgery"
        )

    # GERD — affects procedure selection
    if gerd:
        key_findings.append(
            "GERD present — Roux-en-Y gastric bypass preferred over sleeve gastrectomy (sleeve may worsen GERD)"
        )
        if procedure_type == "sleeve":
            warnings.append(
                "Sleeve gastrectomy may worsen GERD — consider Roux-en-Y gastric bypass instead"
            )

    # Supervised program
    if supervised >= 6:
        score += 10
        key_findings.append(
            f"{supervised_str} months of supervised weight loss program completed — meets payer requirements"
        )
    elif supervised >= 3:
        score += 5
        warnings.append(
            f"Only {supervised_str} months of supervised program — most payers require 6 months"
        )
    else:
        warnings.append(
            "Supervised weight loss program not completed — required by most commercial payers (typically 6 months)"
        )
        score -= 10

    # Psychological clearance
    if psychological_clearance:
        score += 10
        key_findings.append("Psychological clearance obtained — required by all payers")
    else:
        warnings.append(
            "Psychological evaluation not completed — required by all payers before surgery"
        )
        score -= 10

    # Nutrition consultation
    if nutrition_consult:
        score += 5
        key_findings.append("Nutrition consultation completed")
    else:
        warnings.append("Nutrition consultation not documented — required by most payers")

    # Contraindications
    if active_substance_abuse:
        warnings.append(
            "CONTRAINDICATION: Active substance abuse — surgery contraindicated until sustained sobriety (typically ≥1 year)"
        )
        score -= 30
    if uncontrolled_psych:
        warnings.append(
            "CONTRAINDICATION: Uncontrolled psychiatric disorder — surgery contraindicated until stabilized"
        )
        score -= 20
    if cirrhosis:
        warnings.append(
            "Cirrhosis — significantly increased surgical risk; hepatology evaluation required; portal hypertension is relative contraindication"
        )
        score -= 15
    if prior_bariatric:
        key_findings.append(
            "Prior bariatric surgery — revision surgery; higher complexity and risk; specialized center required"
        )
    if esophageal_motility:
        warnings.append(
            "Esophageal motility disorder — sleeve gastrectomy and bypass may worsen symptoms; manometry required pre-operatively"
        )

    score = max(0, min(100, score))

    if score >= 65:
        recommendation = "Strongly Recommended"
        if gerd:
            preferred_procedure = (
                "Roux-en-Y Gastric Bypass (RYGB) — preferred given GERD; also superior for T2DM remission"
            )
        elif type2_diabetes and bmi >= 35:
            preferred_procedure = (
                "Roux-en-Y Gastric Bypass or Sleeve Gastrectomy — RYGB preferred for T2DM remission (80% vs 60%)"
            )
        else:
            preferred_procedure = (
                "Sleeve Gastrectomy (SG) or Roux-en-Y Gastric Bypass (RYGB) — discuss with patient based on anatomy, comorbidities, and preference"
            )
        metabolic_benefit = (
            "Expected: 25–35% total body weight loss; T2DM remission in 50–80%; HTN remission in 60–75%; OSA resolution in 80–85%"
        )
    elif score >= 45:
        recommendation = "Recommended"
        preferred_procedure = (
            "Sleeve Gastrectomy or RYGB — complete pre-operative workup including supervised program and psychological clearance"
        )
        metabolic_benefit = (
            "Expected: 20–30% total body weight loss; significant improvement in metabolic comorbidities"
        )
    elif score >= 25:
        recommendation = "May Be Appropriate"
        preferred_procedure = (
            "Complete remaining pre-operative requirements; bariatric surgery consultation recommended"
        )
        metabolic_benefit = "Metabolic benefit likely if BMI and comorbidity criteria met"
    else:
        recommendation = "Not Recommended"
        preferred_procedure = (
            "Address contraindications; optimize medical management; reassess in 6–12 months"
        )
        metabolic_benefit = "Insufficient criteria for surgical candidacy at this time"

    return {
        "candidacyScore": score,
        "recommendation": recommendation,
        "bmiCategory": bmi_category,
        "preferredProcedure": preferred_procedure,
        "keyFindings": key_findings,
        "warnings": warnings,
        "metabolicBenefit": metabolic_benefit,
        "references": [
            "Eisenberg D, et al. 2022 American Society for Metabolic and Bariatric Surgery (ASMBS) and International Federation for the Surgery of Obesity and Metabolic Disorders (IFSO) Indications for Metabolic and Bariatric Surgery. Surg Obes Relat Dis. 2022;18(12):1345-1356. PMID: 36280539",
            "American Diabetes Association. Standards of Medical Care in Diabetes—2023. Diabetes Care. 2023;46(Suppl 1):S1-S291. Section 8: Obesity and Weight Management — Metabolic surgery recommended for T2DM with BMI ≥30",
            "NICE Guideline NG238. Obesity: Identification, Assessment and Management. 2023 — Bariatric surgery for BMI ≥40 or ≥35 with comorbidity",
            "Schauer PR, et al. STAMPEDE Trial. Bariatric Surgery vs Intensive Medical Therapy for Diabetes. N Engl J Med. 2017;376(7):641-651. PMID: 28199805 — Surgery superior to medical therapy for T2DM control at 5 years",
            "Sjöström L, et al. Swedish Obese Subjects Study. Bariatric Surgery and Long-Term Cardiovascular Events. JAMA. 2012;307(1):56-65. PMID: 22215166 — Surgery reduces cardiovascular events and mortality",
        ],
    }
