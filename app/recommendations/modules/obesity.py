"""Obesity Treatment Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/obesityLogic.ts (assessObesity).

References:
- ASMBS/IFSO 2022 Indications for Metabolic and Bariatric Surgery (PMID: 35853783)
- AHA/ACC 2023 Obesity Guideline (PMID: 37228131)
- ASGE 2023 Endoscopic Bariatric and Metabolic Therapies Guideline (PMID: 37230994)
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "obesity"

# Static reference list surfaced as the card's "Supporting Guidelines & Evidence"
# section (auto-attached by app.recommendations.registry.get_evidence). Ported 1:1
# from old_static_code/client/src/pages/ObesityCompass.tsx `REFERENCES`.
EVIDENCE = [
    {
        "title": "ASMBS/IFSO 2022 Indications for Metabolic and Bariatric Surgery",
        "source": "Eisenberg D et al. Surg Obes Relat Dis. 2022",
        "description": "Updated indications for bariatric surgery: BMI ≥35 with any comorbidity, or BMI ≥30 with T2DM/metabolic syndrome. Removed requirement for failed conservative therapy.",
        "pmid": "35853783",
    },
    {
        "title": "AHA/ACC 2023 Guideline for the Management of Obesity",
        "source": "Grundy SM et al. Circulation. 2023",
        "description": "Comprehensive AHA/ACC guideline covering lifestyle modification, pharmacotherapy (GLP-1 agonists), and surgical/endoscopic interventions for obesity.",
        "pmid": "37228131",
    },
    {
        "title": "SURMOUNT-1: Tirzepatide for Obesity",
        "source": "Jastreboff AM et al. N Engl J Med. 2022",
        "description": "SURMOUNT-1: tirzepatide 15 mg achieved 22.5% mean body weight reduction vs 2.4% placebo at 72 weeks in adults without T2DM.",
        "pmid": "35658024",
    },
    {
        "title": "SELECT Trial: Semaglutide for Cardiovascular Risk Reduction",
        "source": "Lincoff AM et al. N Engl J Med. 2023",
        "description": "SELECT: semaglutide 2.4 mg reduced MACE by 20% (HR 0.80) in overweight/obese patients with established CVD but without T2DM.",
        "pmid": "37952131",
    },
    {
        "title": "ASGE 2023 Guideline: Endoscopic Bariatric and Metabolic Therapies",
        "source": "ASGE Standards of Practice Committee. Gastrointest Endosc. 2023",
        "description": "ASGE guideline on endoscopic sleeve gastroplasty (ESG) and other endoscopic bariatric procedures. ESG FDA-approved 2024 for BMI ≥30.",
        "pmid": "37230994",
    },
    {
        "title": "OASIS-1 Trial: Endoscopic Sleeve Gastroplasty",
        "source": "Abu Dayyeh BK et al. Lancet. 2022",
        "description": "OASIS-1: ESG achieved 13.6% total body weight loss vs 0.8% sham at 52 weeks. FDA approved ESG for BMI ≥30 in 2024.",
        "pmid": "36116424",
    },
]


def classify_bmi(bmi: float) -> str:
    if bmi < 30:
        return "overweight"
    if bmi < 35:
        return "obese_class1"
    if bmi < 40:
        return "obese_class2"
    return "obese_class3"


def count_comorbidities(data: dict) -> int:
    return sum(
        1
        for v in (
            truthy(data.get("t2dm")),
            truthy(data.get("hypertension")),
            truthy(data.get("osa")),
            truthy(data.get("nafld")),
            truthy(data.get("gerd")),
            truthy(data.get("dyslipidemia")),
            truthy(data.get("cardiovascularDisease")),
        )
        if v
    )


def is_surgical_candidate(data: dict) -> bool:
    bmi = parse_float(data.get("bmi"))
    if truthy(data.get("pregnant")):
        return False
    if data.get("surgicalRisk") == "prohibitive":
        return False
    if truthy(data.get("substanceAbuse")):
        return False
    # ASMBS 2022: BMI >=35 with comorbidities, or BMI >=40 regardless
    if bmi >= 40:
        return True
    if bmi >= 35 and count_comorbidities(data) >= 1:
        return True
    # ASMBS 2022 expanded: BMI 30-34.9 with T2DM or metabolic syndrome
    if bmi >= 30 and truthy(data.get("t2dm")):
        return True
    return False


def is_esg_candidate(data: dict) -> bool:
    bmi = parse_float(data.get("bmi"))
    if truthy(data.get("pregnant")):
        return False
    if truthy(data.get("cirrhosis")):
        return False
    if data.get("priorBariatricSurgery") != "none":
        return False
    # ASGE 2023: BMI 30-50, failed lifestyle +/- pharmacotherapy
    return bmi >= 30 and bmi <= 50 and truthy(data.get("lifestyleInterventionAttempted"))


def select_glp1_agent(data: dict) -> dict:
    t2dm = truthy(data.get("t2dm"))
    cvd = truthy(data.get("cardiovascularDisease"))
    # Tirzepatide (GIP/GLP-1): SURMOUNT-1 — 22.5% weight loss
    if t2dm and cvd:
        return {
            "agent": "Tirzepatide (Zepbound) 2.5 mg → 15 mg weekly — preferred for T2DM + CVD",
            "rationale": "SURMOUNT-1: 22.5% mean body weight reduction at 72 weeks. SURPASS-CVOT: superior CV outcomes vs dulaglutide in T2DM.",
        }
    if t2dm:
        return {
            "agent": "Tirzepatide (Zepbound) or Semaglutide (Ozempic 2 mg for T2DM) — both FDA-approved",
            "rationale": "SURMOUNT-2 (tirzepatide in T2DM): 15.7% weight loss. STEP-2 (semaglutide in T2DM): 9.6% weight loss.",
        }
    if cvd:
        return {
            "agent": "Semaglutide (Wegovy) 2.4 mg weekly — SELECT trial: 20% CV event reduction",
            "rationale": "SELECT trial: semaglutide 2.4 mg reduced MACE by 20% in overweight/obese patients with established CVD (no T2DM).",
        }
    # Default: tirzepatide preferred for weight loss efficacy
    return {
        "agent": "Tirzepatide (Zepbound) 2.5 mg → 15 mg weekly — highest weight loss efficacy",
        "rationale": "SURMOUNT-1: 22.5% mean weight loss vs 2.4% placebo at 72 weeks. Superior to semaglutide in head-to-head SURMOUNT-5 trial.",
    }


def assess(data: dict) -> dict:
    warnings: list[str] = []
    next_steps: list[str] = []
    contraindications: list[str] = []

    bmi = parse_float(data.get("bmi"))
    bmi_category = classify_bmi(bmi)
    comorbidity_count = count_comorbidities(data)
    surgical_candidate = is_surgical_candidate(data)
    esg_candidate = is_esg_candidate(data)
    glp1_agent = select_glp1_agent(data)

    t2dm = truthy(data.get("t2dm"))
    gerd = truthy(data.get("gerd"))
    glp1_attempted = truthy(data.get("glp1Attempted"))
    glp1_response = data.get("glp1Response")
    prior_bariatric = data.get("priorBariatricSurgery")
    surgical_risk = data.get("surgicalRisk")

    # Contraindications
    if truthy(data.get("pregnant")):
        contraindications.append(
            "Pregnancy: all pharmacotherapy and surgical/endoscopic interventions contraindicated"
        )
    if truthy(data.get("eatingDisorder")):
        contraindications.append(
            "Active eating disorder: requires psychiatric evaluation and treatment before any intervention"
        )
    if truthy(data.get("substanceAbuse")):
        contraindications.append(
            "Active substance abuse: contraindication to bariatric surgery until sustained sobriety achieved"
        )
    if truthy(data.get("cirrhosis")):
        contraindications.append(
            "Cirrhosis: ESG contraindicated; bariatric surgery requires hepatology evaluation"
        )

    # Warnings
    if gerd and prior_bariatric == "none":
        warnings.append(
            "GERD: sleeve gastrectomy may worsen GERD — RYGB preferred if GERD is significant"
        )
    if truthy(data.get("nafld")):
        warnings.append(
            "MASLD/NAFLD: bariatric surgery is most effective treatment — consider prioritizing surgical referral"
        )
    if truthy(data.get("heartFailure")):
        warnings.append(
            "Heart failure: GLP-1 agonists (semaglutide) have demonstrated benefit in HFpEF (STEP-HFpEF trial) — consider prioritizing pharmacotherapy"
        )
    if glp1_response == "inadequate" and glp1_attempted:
        warnings.append(
            "Inadequate GLP-1 response: escalate to maximum tolerated dose before switching — consider bariatric surgery if BMI criteria met"
        )
    if bmi >= 50:
        warnings.append(
            "BMI ≥50: BPD/DS may offer superior weight loss but higher complication risk — discuss with experienced bariatric center"
        )

    # ── Overweight / Class 1 without comorbidities ──
    if bmi < 30 or (bmi_category == "obese_class1" and comorbidity_count == 0 and not t2dm):
        next_steps.append(
            "Intensive behavioral therapy: ≥14 sessions in 6 months (AHA/ACC 2023 Class I)"
        )
        next_steps.append("Dietary counseling: caloric deficit 500-1000 kcal/day")
        next_steps.append(
            "Physical activity: ≥150 min/week moderate-intensity aerobic exercise"
        )
        return {
            "primaryApproach": "lifestyle_only",
            "primaryLabel": "Intensive Lifestyle Intervention",
            "alternativeApproaches": [],
            "alternativeLabels": [],
            "expectedWeightLoss": "5-10% body weight with sustained lifestyle modification",
            "contraindications": contraindications,
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": "BMI <30 or Class I obesity without comorbidities: lifestyle intervention is first-line per AHA/ACC 2023. Pharmacotherapy considered if BMI ≥30 or ≥27 with comorbidities.",
            "evidenceLevel": "Class I",
            "guidelineSource": "AHA/ACC 2023 Obesity Guideline (PMID: 37228131)",
        }

    # ── BMI ≥27 with comorbidities or BMI ≥30 — pharmacotherapy indicated ──
    if not glp1_attempted or glp1_response == "naive":
        next_steps.append(f"Initiate {glp1_agent['agent']}")
        next_steps.append("Titrate dose over 16-20 weeks to maximum tolerated dose")
        next_steps.append(
            "Reassess weight loss at 16 weeks: if <5%, consider switching agent or escalating to surgical/endoscopic therapy"
        )
        next_steps.append("Intensive lifestyle counseling concurrent with pharmacotherapy")
        if surgical_candidate and bmi >= 35:
            next_steps.append(
                "Discuss bariatric surgery as definitive option — refer to bariatric surgery center for evaluation"
            )
        return {
            "primaryApproach": "glp1_plus_lifestyle",
            "primaryLabel": "GLP-1/GIP Agonist + Intensive Lifestyle Intervention",
            "alternativeApproaches": (
                ["esg_endoscopic", "bariatric_surgery_sleeve"]
                if esg_candidate
                else ["bariatric_surgery_sleeve"]
            ),
            "alternativeLabels": (
                [
                    "Endoscopic Sleeve Gastroplasty (ESG) — if pharmacotherapy fails/intolerable",
                    "Sleeve Gastrectomy — if BMI criteria met",
                ]
                if esg_candidate
                else ["Sleeve Gastrectomy — if BMI criteria met"]
            ),
            "glp1Agent": glp1_agent["agent"],
            "glp1Rationale": glp1_agent["rationale"],
            "expectedWeightLoss": (
                "9-16% body weight (tirzepatide/semaglutide in T2DM)"
                if t2dm
                else "15-22% body weight (tirzepatide SURMOUNT-1)"
            ),
            "contraindications": contraindications,
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": f"GLP-1/GIP agonists are first-line pharmacotherapy for BMI ≥30 (or ≥27 with comorbidities) per AHA/ACC 2023. {glp1_agent['rationale']}",
            "evidenceLevel": "Class I",
            "guidelineSource": "AHA/ACC 2023 (PMID: 37228131); ASMBS/IFSO 2022 (PMID: 35853783)",
        }

    # ── GLP-1 intolerant or inadequate response ──
    if glp1_response == "intolerant" or glp1_response == "inadequate":
        # ESG option
        if esg_candidate and (bmi >= 30 and bmi < 40) and surgical_risk != "low":
            next_steps.append(
                "Endoscopic sleeve gastroplasty (ESG): outpatient procedure, 15-18% total body weight loss at 24 months"
            )
            next_steps.append(
                "Pre-procedure: upper endoscopy, nutritional counseling, anesthesia evaluation"
            )
            next_steps.append(
                "Post-procedure: liquid diet 2 weeks → soft diet 2 weeks → regular diet"
            )
            next_steps.append(
                "Concurrent lifestyle modification and nutritional supplementation"
            )
            return {
                "primaryApproach": "esg_endoscopic",
                "primaryLabel": "Endoscopic Sleeve Gastroplasty (ESG)",
                "alternativeApproaches": (
                    ["bariatric_surgery_sleeve", "bariatric_surgery_rygb"]
                    if surgical_candidate
                    else ["glp1_agonist"]
                ),
                "alternativeLabels": (
                    [
                        "Sleeve Gastrectomy (if BMI ≥35 with comorbidities)",
                        "RYGB (if GERD present or BMI ≥40)",
                    ]
                    if surgical_candidate
                    else [
                        "Alternative GLP-1 agent (tirzepatide if semaglutide failed, or vice versa)"
                    ]
                ),
                "esgCriteria": [
                    "BMI 30-50 kg/m²",
                    "Failed ≥6 months lifestyle intervention",
                    "No prior bariatric surgery",
                    "No cirrhosis or portal hypertension",
                    "Willing to comply with post-procedure diet",
                ],
                "expectedWeightLoss": "15-18% total body weight at 24 months (OASIS-1 trial)",
                "contraindications": contraindications,
                "keyWarnings": warnings,
                "nextSteps": next_steps,
                "rationale": "ESG is a minimally invasive endoscopic bariatric procedure. OASIS-1 trial: 13.6% total body weight loss vs 0.8% sham at 52 weeks. FDA approved 2024 for BMI ≥30.",
                "evidenceLevel": "Class IIa",
                "guidelineSource": "ASGE 2023 (PMID: 37230994); ASMBS/IFSO 2022 (PMID: 35853783)",
            }

        # Surgical options
        if surgical_candidate:
            prefer_rygb = gerd or bmi >= 50 or t2dm
            procedure = "bariatric_surgery_rygb" if prefer_rygb else "bariatric_surgery_sleeve"
            next_steps.append(
                "Bariatric surgery evaluation: multidisciplinary team (surgery, nutrition, psychology, medicine)"
            )
            next_steps.append(
                "Pre-operative workup: EGD, sleep study, cardiac evaluation if indicated"
            )
            next_steps.append(
                "Nutritional supplementation: multivitamin, calcium, vitamin D, B12 — lifelong"
            )
            next_steps.append(
                "RYGB: preferred for GERD, T2DM, or BMI ≥50 — superior glycemic control and GERD resolution"
                if prefer_rygb
                else "Sleeve gastrectomy: simpler procedure, lower complication rate — avoid if significant GERD"
            )
            return {
                "primaryApproach": procedure,
                "primaryLabel": (
                    "Roux-en-Y Gastric Bypass (RYGB) — preferred"
                    if prefer_rygb
                    else "Sleeve Gastrectomy — preferred"
                ),
                "alternativeApproaches": (
                    ["bariatric_surgery_sleeve", "esg_endoscopic"]
                    if prefer_rygb
                    else ["bariatric_surgery_rygb", "esg_endoscopic"]
                ),
                "alternativeLabels": (
                    ["Sleeve Gastrectomy (if GERD not severe)", "ESG (if surgical risk high)"]
                    if prefer_rygb
                    else ["RYGB (if GERD present or T2DM)", "ESG (if surgical risk high)"]
                ),
                "surgicalProcedure": (
                    "Roux-en-Y Gastric Bypass" if prefer_rygb else "Sleeve Gastrectomy"
                ),
                "surgicalRationale": (
                    "RYGB: 30-35% total body weight loss, superior T2DM remission (80%), and GERD resolution. Preferred for GERD, T2DM, BMI ≥50."
                    if prefer_rygb
                    else "Sleeve gastrectomy: 25-30% total body weight loss, simpler anatomy, lower malabsorption risk."
                ),
                "expectedWeightLoss": (
                    "30-35% total body weight at 2 years"
                    if prefer_rygb
                    else "25-30% total body weight at 2 years"
                ),
                "contraindications": contraindications,
                "keyWarnings": warnings,
                "nextSteps": next_steps,
                "rationale": (
                    "Bariatric surgery is the most effective long-term treatment for severe obesity. ASMBS/IFSO 2022 expanded indications: BMI ≥35 with any comorbidity, or BMI ≥30 with T2DM. "
                    + (
                        "RYGB preferred for GERD/T2DM."
                        if prefer_rygb
                        else "Sleeve gastrectomy for BMI 35-49 without significant GERD."
                    )
                ),
                "evidenceLevel": "Class I",
                "guidelineSource": "ASMBS/IFSO 2022 (PMID: 35853783); AHA/ACC 2023 (PMID: 37228131)",
            }

        # Not surgical candidate — try alternative GLP-1
        next_steps.append(
            "Consider alternative GLP-1 agent (tirzepatide if semaglutide failed, or vice versa)"
        )
        next_steps.append(
            "Orlistat 120 mg TID with meals — modest weight loss (2.9 kg vs placebo)"
        )
        next_steps.append("Naltrexone/bupropion (Contrave) — if GLP-1 not tolerated")
        next_steps.append("Intensive behavioral therapy: ≥14 sessions in 6 months")
        return {
            "primaryApproach": "glp1_agonist",
            "primaryLabel": "Alternative GLP-1 Agent or Combination Pharmacotherapy",
            "alternativeApproaches": ["lifestyle_only"],
            "alternativeLabels": ["Intensive Lifestyle Intervention + Behavioral Therapy"],
            "glp1Agent": "Alternative agent: Tirzepatide (if semaglutide failed) or Semaglutide (if tirzepatide failed)",
            "glp1Rationale": "Class switch may improve tolerability and efficacy. Consider lower starting dose and slower titration.",
            "expectedWeightLoss": "5-15% body weight depending on agent and tolerability",
            "contraindications": contraindications,
            "keyWarnings": [
                *warnings,
                "Surgical risk prohibitive: pharmacotherapy and lifestyle modification are primary options",
            ],
            "nextSteps": next_steps,
            "rationale": "For patients with inadequate GLP-1 response or intolerance who are not surgical candidates, consider alternative agents or combination pharmacotherapy.",
            "evidenceLevel": "Class IIa",
            "guidelineSource": "AHA/ACC 2023 (PMID: 37228131)",
        }

    # ── Revision surgery ──
    if prior_bariatric != "none":
        next_steps.append(
            "Evaluate cause of weight regain: dietary non-compliance, anatomic issue, or metabolic adaptation"
        )
        next_steps.append("Upper endoscopy to assess anatomy")
        next_steps.append(
            "Consider revision surgery: RYGB after failed sleeve, or band removal + conversion"
        )
        next_steps.append("GLP-1 agonist as adjunct to revision surgery or as alternative")
        return {
            "primaryApproach": "revision_surgery",
            "primaryLabel": "Revision Bariatric Surgery Evaluation",
            "alternativeApproaches": ["glp1_plus_lifestyle"],
            "alternativeLabels": [
                "GLP-1 Agonist + Lifestyle (as adjunct or alternative to revision)"
            ],
            "expectedWeightLoss": "Variable — depends on revision procedure and compliance",
            "contraindications": contraindications,
            "keyWarnings": [
                *warnings,
                "Revision surgery carries higher complication risk than primary bariatric surgery — ensure experienced center",
            ],
            "nextSteps": next_steps,
            "rationale": "Weight regain after bariatric surgery is common. Revision surgery or pharmacotherapy (GLP-1 agonists) are effective options. Multidisciplinary evaluation essential.",
            "evidenceLevel": "Class IIa",
            "guidelineSource": "ASMBS/IFSO 2022 (PMID: 35853783)",
        }

    # Default: multidisciplinary evaluation
    return {
        "primaryApproach": "multidisciplinary",
        "primaryLabel": "Multidisciplinary Obesity Management Program",
        "alternativeApproaches": ["glp1_plus_lifestyle", "bariatric_surgery_sleeve"],
        "alternativeLabels": [
            "GLP-1 Agonist + Lifestyle",
            "Bariatric Surgery (if criteria met)",
        ],
        "expectedWeightLoss": "10-20% body weight with comprehensive program",
        "contraindications": contraindications,
        "keyWarnings": warnings,
        "nextSteps": [
            "Comprehensive obesity evaluation: metabolic panel, thyroid, sleep study",
            "Multidisciplinary team: obesity medicine, nutrition, behavioral health, exercise physiology",
            "Individualize treatment based on comorbidities, preferences, and prior treatment history",
        ],
        "rationale": "Complex obesity management requires individualized multidisciplinary approach per AHA/ACC 2023.",
        "evidenceLevel": "Class I",
        "guidelineSource": "AHA/ACC 2023 (PMID: 37228131); ASMBS/IFSO 2022 (PMID: 35853783)",
    }
