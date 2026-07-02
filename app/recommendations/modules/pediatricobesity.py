"""Pediatric Obesity Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/pediatricObesityLogic.ts
(assessPediatricObesity). AAP Clinical Practice Guideline 2023 (updated 2026) /
ASMBS 2023.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "pediatricobesity"

_REFERENCES = [
    {
        "citation": "Hampl SE et al. Clinical Practice Guideline for the Evaluation and Treatment of Children and Adolescents with Obesity. Pediatrics. 2023;151(2):e2022060640.",
        "url": "https://publications.aap.org/pediatrics/article/151/2/e2022060640",
    },
    {
        "citation": "Weghuber D et al. Once-Weekly Semaglutide in Adolescents with Obesity. NEJM. 2022;387(24):2245–2257. (STEP TEENS)",
        "url": "https://www.nejm.org/doi/10.1056/NEJMoa2208601",
    },
    {
        "citation": "Pratt JSA et al. ASMBS Pediatric Metabolic and Bariatric Surgery Guidelines 2018 (updated 2023). Surg Obes Relat Dis. 2018;14(7):882–901.",
        "url": "https://www.soard.org/article/S1550-7289(18)30174-5/fulltext",
    },
    {
        "citation": "Jastreboff AM et al. Tirzepatide Once Weekly for the Treatment of Obesity in Adolescents. NEJM. 2024. (SURMOUNT-TEEN)",
        "url": "https://www.nejm.org/doi/10.1056/NEJMoa2407701",
    },
]


def _js_str(v) -> str:
    """Render a value the way TS template literals do (true/false/null)."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    return str(v)


def _fmt_num(value: float) -> str:
    """Render a number the way a JS template literal would (drop trailing .0)."""
    if value == int(value):
        return str(int(value))
    return str(value)


def assess(data: dict) -> dict:
    # TS UI parses every numeric field with `parseFloat(value) || 0`, so the
    # engine receives numbers (0 for blanks). Reproduce that with num(...); this
    # also makes the strict `priorTreatmentAttempts === 0` and the numeric
    # template interpolations match TS for raw-string inputs.
    age_years = num(data.get("ageYears"), 0)
    obesity_category = data.get("obesityCategory")
    bmi_percentile = num(data.get("bmiPercentile"), 0)
    bmi_percent_of_p95 = num(data.get("bmiPercentOfP95"), 0)
    prior_treatment_attempts = num(data.get("priorTreatmentAttempts"), 0)

    urgent_flags: list[str] = []
    comorbidity_mgmt: list[str] = []
    recommended_agents: list[str] = []
    counseling_points: list[str] = []

    # ─── Urgent flags ─────────────────────────────────────────────────────────
    if truthy(data.get("hasIdiopathicIntracranialHypertension")):
        urgent_flags.append(
            "URGENT: Idiopathic intracranial hypertension (IIH) — refer to neurology + ophthalmology. Rapid weight loss intervention indicated. Acetazolamide may be needed."
        )
    if truthy(data.get("hasOrthopedicComplications")):
        urgent_flags.append(
            "URGENT: Orthopedic complication (SCFE or Blount disease) — refer to pediatric orthopedics. SCFE requires non-weight-bearing until surgical evaluation."
        )
    if truthy(data.get("hasType2Diabetes")):
        urgent_flags.append(
            "TYPE 2 DIABETES: Initiate metformin immediately. Consider GLP-1 RA (semaglutide ≥12 years) for dual benefit on weight and glycemia. HbA1c target <7%."
        )
        comorbidity_mgmt.append(
            "Type 2 Diabetes: Metformin 500mg BID → titrate to 1000mg BID (max 2000mg/day). Add semaglutide (Ozempic/Wegovy) for weight + glycemic benefit. Monitor HbA1c every 3 months."
        )
        recommended_agents.append("Metformin 500–2000mg/day (T2DM + obesity, ≥10 years)")
    if truthy(data.get("hasOSA")):
        urgent_flags.append(
            "OBSTRUCTIVE SLEEP APNEA: Refer to sleep medicine. Polysomnography if not done. CPAP if AHI ≥5. Weight loss is the primary treatment — may resolve OSA."
        )
        comorbidity_mgmt.append(
            "OSA: Polysomnography + CPAP if AHI ≥5. Adenotonsillectomy if adenotonsillar hypertrophy. Weight loss is primary treatment."
        )

    # ─── Treatment intensity (AAP 2023 4-stage model) ────────────────────────
    treatment_intensity: str
    lifestyle_intervention: str
    pharmacotherapy: str
    bariatric_consideration: str

    if obesity_category == "healthy_weight" or obesity_category == "overweight":
        treatment_intensity = "STAGE 1 — Prevention Plus: Counseling on healthy lifestyle behaviors. 5-2-1-0 framework (5 fruits/vegetables, ≤2 hours screen time, 1 hour activity, 0 sugary drinks). Monthly follow-up."
        lifestyle_intervention = "5-2-1-0 healthy lifestyle counseling. Family-based behavioral counseling. Motivational interviewing. Monthly follow-up visits."
        pharmacotherapy = "Not indicated for overweight. Pharmacotherapy reserved for obesity (BMI ≥95th %ile) with comorbidities or failed lifestyle intervention."
        bariatric_consideration = "Not indicated for overweight category."
    elif obesity_category == "class1_obesity":
        if prior_treatment_attempts == 0:
            treatment_intensity = "STAGE 2 — Structured Weight Management: Structured diet plan + increased physical activity + reduced sedentary time. Monthly provider visits. Refer to registered dietitian."
            lifestyle_intervention = "Structured diet: balanced macronutrients, portion control, elimination of sugar-sweetened beverages. 60 min/day MVPA. Screen time <2 hours/day. Monthly visits with provider + RD."
        else:
            treatment_intensity = "STAGE 3 — Comprehensive Multidisciplinary Intervention (CMDI): Refer to pediatric weight management program with multidisciplinary team (physician, RD, behavioral health, exercise specialist). Weekly visits for 12 weeks."
            lifestyle_intervention = "Intensive multidisciplinary program: behavioral modification, structured meal plan (1200–1500 kcal/day for children, 1500–1800 kcal/day for adolescents), 60 min/day MVPA, family therapy."
        if age_years >= 12:
            pharmacotherapy = "PHARMACOTHERAPY INDICATED (Class 1 obesity with comorbidities or failed lifestyle): Semaglutide (Wegovy) 0.25mg SC weekly → titrate to 2.4mg weekly over 16–20 weeks. FDA-approved ≥12 years. STEP TEENS trial: −16.1% BMI at 68 weeks."
        elif age_years >= 6:
            pharmacotherapy = "Orlistat (Xenical) 120mg TID with meals — FDA-approved ≥12 years. Off-label ≥6 years. Metformin for insulin resistance/prediabetes ≥10 years."
        else:
            pharmacotherapy = "Pharmacotherapy not approved <6 years. Lifestyle intervention only."
        bariatric_consideration = "Not indicated for Class 1 obesity without severe comorbidities."
    else:
        # Class 2 or 3 obesity
        _class = "2" if obesity_category == "class2_obesity" else "3"
        treatment_intensity = f"STAGE 3–4 — Comprehensive Multidisciplinary Intervention + Consider Pharmacotherapy/Surgery: Class {_class} obesity. Intensive intervention required. Refer to pediatric weight management program."
        lifestyle_intervention = "Intensive multidisciplinary program (CMDI). Very low calorie diet (VLCD) may be considered under medical supervision. Family-based behavioral therapy. 60 min/day MVPA."

        if age_years >= 12 and not truthy(data.get("hasContraindicationToGLP1")):
            pharmacotherapy = "PHARMACOTHERAPY STRONGLY INDICATED: Semaglutide (Wegovy) 0.25mg SC weekly → titrate to 2.4mg weekly. FDA-approved ≥12 years (BMI ≥95th %ile + weight-related comorbidity). STEP TEENS: −16.1% BMI. Monitor for nausea, pancreatitis, gallbladder disease. Contraindicated in MEN2, personal/family history of MTC."
            recommended_agents.append(
                "Semaglutide (Wegovy) 0.25mg SC weekly → 2.4mg/week (≥12 years, BMI ≥95th %ile)"
            )
            if truthy(data.get("priorGLP1Use")):
                pharmacotherapy += " Prior GLP-1 use: consider tirzepatide (Zepbound) — FDA-approved ≥12 years (2024). 5mg SC weekly → titrate to 15mg weekly. SURMOUNT-TEEN: −15.4% BMI."
                recommended_agents.append(
                    "Tirzepatide (Zepbound) 5mg SC weekly → 15mg/week (≥12 years, 2024 FDA approval)"
                )
        elif age_years >= 12 and truthy(data.get("hasContraindicationToGLP1")):
            pharmacotherapy = "GLP-1 RA CONTRAINDICATED: Consider orlistat 120mg TID (FDA-approved ≥12 years) or topiramate (off-label) for weight management. Metformin for insulin resistance."
            recommended_agents.append("Orlistat 120mg TID with meals (≥12 years)")
        else:
            pharmacotherapy = "Pharmacotherapy limited for age <12 years. Metformin for insulin resistance/prediabetes ≥10 years. Refer to pediatric endocrinology."

        # Bariatric surgery
        if age_years >= 13 and (
            bmi_percent_of_p95 >= 140
            or (
                bmi_percent_of_p95 >= 120
                and (
                    truthy(data.get("hasType2Diabetes"))
                    or truthy(data.get("hasOSA"))
                    or truthy(data.get("hasNASH"))
                    or truthy(data.get("hasHypertension"))
                )
            )
        ):
            bariatric_consideration = "BARIATRIC SURGERY CANDIDATE (ASMBS 2023 criteria): BMI ≥140% of 95th %ile OR BMI ≥120% of 95th %ile + severe comorbidity (T2DM, OSA, NASH, HTN). Refer to pediatric bariatric surgery center. Sleeve gastrectomy preferred in adolescents. Roux-en-Y gastric bypass for T2DM. Requires multidisciplinary evaluation (surgery, psychology, nutrition, endocrinology)."
            if not truthy(data.get("hasBariatricContraindication")):
                urgent_flags.append(
                    "BARIATRIC SURGERY CANDIDATE: Refer to pediatric bariatric surgery center per ASMBS 2023 criteria."
                )
        else:
            bariatric_consideration = (
                "Bariatric surgery: criteria not yet met. Continue pharmacotherapy + CMDI. Reassess if BMI ≥140% of 95th %ile or severe comorbidities develop."
                if age_years >= 13
                else "Bariatric surgery: minimum age 13 years (ASMBS 2023). Continue pharmacotherapy + CMDI."
            )

    # ─── Comorbidity management ───────────────────────────────────────────────
    if truthy(data.get("hasHypertension")):
        comorbidity_mgmt.append(
            "Hypertension: Weight loss is primary treatment. If BP persistently ≥95th %ile + 12 mmHg: initiate antihypertensive (ACE inhibitor or ARB). Refer to pediatric nephrology/cardiology."
        )
    if truthy(data.get("hasDyslipidemia")):
        comorbidity_mgmt.append(
            "Dyslipidemia: Dietary modification (reduce saturated fat, increase fiber). LDL ≥190 mg/dL: statin therapy (≥10 years). Refer to pediatric cardiology for severe dyslipidemia."
        )
        recommended_agents.append("Atorvastatin 10–20mg/day (LDL ≥190 mg/dL, ≥10 years)")
    if truthy(data.get("hasNASH")):
        comorbidity_mgmt.append(
            "MASH/NASH: Weight loss 7–10% reduces hepatic steatosis. Avoid hepatotoxic medications. Monitor ALT/AST every 3–6 months. Refer to pediatric gastroenterology for biopsy-proven NASH."
        )
    if truthy(data.get("hasPCOS")):
        comorbidity_mgmt.append(
            "PCOS: Metformin 500–2000mg/day for insulin resistance and menstrual regulation. Weight loss improves ovulatory function. Refer to pediatric endocrinology/gynecology."
        )
        recommended_agents.append("Metformin 500–2000mg/day (PCOS + insulin resistance)")
    if truthy(data.get("hasDepression")) or truthy(data.get("hasBingeEatingDisorder")):
        comorbidity_mgmt.append(
            "Mental health comorbidity: Refer to behavioral health for depression and/or binge eating disorder. Avoid weight-promoting antidepressants (e.g., mirtazapine, paroxetine). Consider CBT for binge eating."
        )
        urgent_flags.append(
            "MENTAL HEALTH COMORBIDITY: Refer to behavioral health. Screen for depression (PHQ-9) and binge eating disorder."
        )

    # ─── Family counseling ────────────────────────────────────────────────────
    counseling_points.extend(
        [
            "Obesity is a chronic disease — not a personal failure. Use non-stigmatizing, patient-first language ('child with obesity' not 'obese child').",
            "Family-based treatment is more effective than child-only interventions — engage all household members.",
            "5-2-1-0 framework: 5+ fruits/vegetables/day, ≤2 hours recreational screen time, 1+ hour MVPA, 0 sugar-sweetened beverages.",
            "Meal planning: structured meals, no skipping breakfast, family meals ≥5 times/week associated with healthier weight.",
            "Sleep: inadequate sleep (< 9 hours in children, < 8 hours in adolescents) is an independent risk factor for obesity.",
            "Weight stigma: protect child from weight-based bullying. Address with school if needed.",
        ]
    )

    if data.get("familyMotivation") == "low":
        counseling_points.append(
            "Low family motivation: Use motivational interviewing techniques. Identify family-specific barriers. Consider referral to family therapy or social work."
        )

    # ─── Monitoring ───────────────────────────────────────────────────────────
    _hba1c = "HbA1c every 3 months." if truthy(data.get("hasType2Diabetes")) else ""
    _sema = (
        "Semaglutide: monitor for nausea, vomiting, pancreatitis (amylase/lipase if symptoms). Gallbladder ultrasound if RUQ pain."
        if any("Semaglutide" in a for a in recommended_agents)
        else ""
    )
    monitoring_plan = f"Monthly weight/BMI monitoring during active treatment. Fasting glucose/HbA1c annually (or every 3 months if T2DM). Fasting lipid panel annually. ALT/AST annually (NASH risk). Blood pressure every visit. {_hba1c} {_sema}"

    if len(urgent_flags) > 0:
        primary_rec = urgent_flags[0]
    else:
        _category_label = _js_str(obesity_category).replace("_", " ").upper()
        primary_rec = (
            f"PEDIATRIC OBESITY — {_category_label} (BMI {_fmt_num(bmi_percentile)}th %ile, "
            f"{_fmt_num(bmi_percent_of_p95)}% of 95th %ile). {treatment_intensity.split(':')[0]}. "
            f"Evidence Level A (AAP CPG 2023)."
        )

    return {
        "primaryRecommendation": primary_rec,
        "treatmentIntensity": treatment_intensity,
        "lifestyleIntervention": lifestyle_intervention,
        "pharmacotherapy": pharmacotherapy,
        "bariatricConsideration": bariatric_consideration,
        "comorbidityManagement": comorbidity_mgmt,
        "urgentFlags": urgent_flags,
        "recommendedAgents": recommended_agents,
        "monitoringPlan": monitoring_plan,
        "familyCounselingPoints": counseling_points,
        "evidenceLevel": "A",
        "rationale": (
            f"Age {_fmt_num(age_years)} years. BMI {_fmt_num(bmi_percentile)}th %ile "
            f"({_fmt_num(bmi_percent_of_p95)}% of 95th %ile). Category: {_js_str(obesity_category)}. "
            f"Prior treatment attempts: {_fmt_num(prior_treatment_attempts)}. Comorbidities: "
            f"T2DM={_js_str(data.get('hasType2Diabetes'))}, HTN={_js_str(data.get('hasHypertension'))}, "
            f"OSA={_js_str(data.get('hasOSA'))}, NASH={_js_str(data.get('hasNASH'))}. "
            f"Recommendations per AAP CPG 2023 and ASMBS 2023."
        ),
        "references": _REFERENCES,
    }
