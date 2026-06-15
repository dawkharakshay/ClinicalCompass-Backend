"""OSA + Obesity Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/OSAObesityCompass.tsx
(the inline ``getRecommendation(answers)`` function). There is no separate
*Logic.ts file for this module; the decision logic lives inline in the Compass
page. Based on SURMOUNT-OSA Phase 3 trial data and FDA approval (Dec 20, 2024).
"""

from __future__ import annotations

LOGIC_KEY = "osaobesity"

# The seven wizard steps; the "incomplete" guard mirrors the TS
# ``Object.keys(answers).length < steps.length`` check.
_STEP_IDS = (
    "osa_severity",
    "obesity_status",
    "diabetes_status",
    "pap_status",
    "contraindications",
    "prior_weight_loss",
    "glp1_preference",
)


def assess(data: dict) -> dict:
    osa_severity = data.get("osa_severity")
    obesity_status = data.get("obesity_status")
    diabetes_status = data.get("diabetes_status")
    pap_status = data.get("pap_status")
    contraindications = data.get("contraindications")
    prior_weight_loss = data.get("prior_weight_loss")
    glp1_preference = data.get("glp1_preference")

    # Incomplete: not all steps answered.
    answered = sum(1 for k in _STEP_IDS if data.get(k) is not None)
    if answered < len(_STEP_IDS):
        return {
            "level": "incomplete",
            "title": "Assessment Incomplete",
            "summary": "Please complete all steps to receive a recommendation.",
            "details": [],
            "nextSteps": [],
            "warnings": [],
        }

    # Absolute contraindication.
    if contraindications == "mtc_men2":
        return {
            "level": "not_indicated",
            "title": "Tirzepatide Contraindicated — MTC/MEN2 History",
            "summary": "Zepbound (tirzepatide) is absolutely contraindicated in patients with a personal or family history of medullary thyroid carcinoma (MTC) or Multiple Endocrine Neoplasia type 2 (MEN2).",
            "details": [
                "Tirzepatide causes thyroid C-cell tumors in rats; human risk is unknown but MTC/MEN2 history is an absolute contraindication.",
                "Consider alternative weight management strategies: semaglutide (Wegovy) does not carry the same boxed warning for MTC/MEN2 but also has a thyroid C-cell tumor warning — consult endocrinology.",
                "Non-pharmacologic options: bariatric surgery (if BMI ≥35 with comorbidities), structured intensive behavioral therapy, positional therapy, oral appliance therapy.",
                "PAP therapy remains the standard of care for OSA regardless of weight management approach.",
            ],
            "nextSteps": [
                "Refer to endocrinology for thyroid risk stratification if GLP-1 therapy is still being considered.",
                "Optimize PAP therapy adherence.",
                "Consider bariatric surgery evaluation if BMI ≥35 with comorbidities.",
            ],
            "warnings": ["Absolute contraindication: Do NOT prescribe tirzepatide or semaglutide without endocrinology clearance in MTC/MEN2 patients."],
        }

    # OSA not confirmed.
    if osa_severity == "pending":
        return {
            "level": "conditional",
            "title": "OSA Diagnosis Must Be Confirmed First",
            "summary": "Zepbound for OSA requires confirmed moderate-to-severe OSA by PSG or HSAT before initiating therapy.",
            "details": [
                "Order PSG (CPT 95810) or home sleep apnea test (CPT 95800) to confirm OSA severity.",
                "AHI ≥15 events/hr (moderate-to-severe) is required for the Zepbound OSA indication.",
                "If obesity is present (BMI ≥30), Zepbound may be initiated for weight management while awaiting OSA workup — but the OSA-specific indication requires confirmed diagnosis.",
            ],
            "nextSteps": [
                "Order diagnostic sleep study (PSG preferred for suspected complex or central sleep apnea).",
                "Return to this module after OSA severity is confirmed.",
            ],
            "warnings": [],
        }

    # Mild OSA — not FDA-approved indication.
    if osa_severity == "mild":
        return {
            "level": "not_indicated",
            "title": "Mild OSA — Zepbound OSA Indication Not Met",
            "summary": "The FDA approval of Zepbound for OSA is limited to moderate-to-severe OSA (AHI ≥15 events/hr). Mild OSA does not meet the approved indication.",
            "details": [
                "SURMOUNT-OSA enrolled patients with AHI ≥15 events/hr; the FDA indication is for moderate-to-severe OSA.",
                "Weight loss (via any means including GLP-1 agents) can improve mild OSA, but this would be off-label use of the OSA-specific indication.",
                "If the patient has obesity (BMI ≥30) and other weight-related comorbidities, Zepbound may be appropriate under the weight management indication.",
                "For mild OSA: consider positional therapy, weight loss counseling, oral appliance therapy, or CPAP if symptomatic.",
            ],
            "nextSteps": [
                "If BMI ≥30 with weight-related comorbidities, evaluate Zepbound under the weight management indication (separate PA criteria).",
                "Refer to sleep medicine for mild OSA management.",
                "Repeat PSG after significant weight loss to reassess OSA severity.",
            ],
            "warnings": ["Mild OSA does not qualify for the Zepbound OSA-specific FDA indication. Document medical necessity carefully if prescribing off-label."],
        }

    # BMI too low for OSA indication.
    if obesity_status == "bmi_under_27":
        return {
            "level": "not_indicated",
            "title": "BMI Does Not Meet Threshold for Zepbound OSA Indication",
            "summary": "The Zepbound OSA indication requires obesity (BMI ≥30 kg/m²). Patients with BMI <27 do not qualify.",
            "details": [
                "The FDA approval is specifically for adults with obesity (BMI ≥30) and moderate-to-severe OSA.",
                "For OSA in non-obese patients, standard therapies apply: PAP therapy, oral appliance, positional therapy, upper airway surgery.",
                "Consider ENT/sleep surgery referral for anatomic evaluation.",
            ],
            "nextSteps": [
                "Optimize PAP therapy.",
                "Refer to ENT for surgical evaluation if PAP-intolerant.",
                "Re-evaluate if BMI increases to ≥30.",
            ],
            "warnings": [],
        }

    # T2DM — different pathway.
    if diabetes_status == "t2dm":
        return {
            "level": "conditional",
            "title": "T2DM Present — Use Mounjaro (Not Zepbound) for Tirzepatide; Consider Semaglutide",
            "summary": "Patients with T2DM were excluded from SURMOUNT-OSA. The Zepbound OSA indication is for patients WITHOUT T2DM. Tirzepatide for T2DM uses Mounjaro (different indication/PA pathway). Semaglutide (Ozempic for T2DM, Wegovy for weight) is an alternative.",
            "details": [
                "Tirzepatide (Mounjaro) is FDA-approved for T2DM and produces significant weight loss (15–22%) that can improve OSA.",
                "Semaglutide (Ozempic 1mg or 2mg for T2DM; Wegovy 2.4mg for weight management) is an alternative GLP-1 RA with 12–15% weight loss and likely OSA benefit.",
                "The SELECT trial demonstrated 20% CV risk reduction with semaglutide 2.4mg in obese patients with established CVD — relevant for OSA patients with cardiovascular comorbidities.",
                "Document OSA as a weight-related comorbidity to support PA for weight management indication.",
                "PAP therapy remains the standard of care for OSA regardless of pharmacologic weight management.",
            ],
            "nextSteps": [
                "For T2DM: prescribe Mounjaro (tirzepatide) or Ozempic (semaglutide) under T2DM indication.",
                "For weight management in T2DM with OSA: consider Wegovy (semaglutide 2.4mg) — document OSA as weight-related comorbidity.",
                "Optimize PAP therapy adherence.",
                "Repeat PSG after ≥10% weight loss to reassess OSA severity.",
            ],
            "warnings": ["Zepbound OSA indication is NOT for T2DM patients. Use Mounjaro for tirzepatide in T2DM."],
        }

    # Fully eligible for Zepbound OSA indication.
    is_eligible = (
        (osa_severity == "moderate" or osa_severity == "severe")
        and (
            obesity_status == "bmi_30_34"
            or obesity_status == "bmi_35_39"
            or obesity_status == "bmi_40plus"
        )
        and diabetes_status != "t2dm"
        and contraindications == "none"
    )

    if is_eligible:
        agent_note = (
            "Note: Semaglutide (Wegovy) is NOT FDA-approved for OSA. If semaglutide is preferred (e.g., tirzepatide intolerance), document off-label use and medical necessity."
            if glp1_preference == "semaglutide"
            else "Note: Other GLP-1 RAs (liraglutide, dulaglutide) have no OSA-specific trial data. Tirzepatide (Zepbound) is the only FDA-approved option for OSA."
            if glp1_preference == "other_glp1"
            else ""
        )

        pap_note = (
            "Patient is on PAP therapy — Zepbound is approved as adjunct to PAP (consistent with SURMOUNT-OSA Trial 2 population)."
            if pap_status == "pap_current"
            else "Patient is not using PAP — Zepbound is approved as standalone therapy for OSA in PAP-intolerant/unwilling patients (consistent with SURMOUNT-OSA Trial 1 population)."
        )

        prior_attempt_note = (
            "Prior weight loss attempt documentation is missing — most payers require ≥1 documented dietary attempt. Document this before submitting PA."
            if prior_weight_loss == "no_attempt"
            else ""
        )

        severity_word = "severe" if osa_severity == "severe" else "moderate"
        bmi_word = (
            "≥40"
            if obesity_status == "bmi_40plus"
            else "35–39.9"
            if obesity_status == "bmi_35_39"
            else "30–34.9"
        )

        details = [
            d
            for d in [
                pap_note,
                "SURMOUNT-OSA efficacy: AHI reduced by 47.7–56.2% vs placebo; OSA-specific hypoxia burden reduced by 61–70%; body weight reduced by 16–17% at 52 weeks (N Engl J Med 2024;391:1193-205).",
                "Dosing: Start tirzepatide 2.5 mg SC weekly; titrate by 2.5 mg every 4 weeks to maximum tolerated dose (10 or 15 mg weekly).",
                "Combination with reduced-calorie diet and increased physical activity is required per FDA labeling.",
                "Repeat PSG or HSAT at 12 months to document AHI response — critical for continued PA authorization.",
                agent_note,
                prior_attempt_note,
            ]
            if d
        ]

        if prior_weight_loss == "no_attempt":
            warnings = ["Document prior dietary/lifestyle weight loss attempt before PA submission — required by most payers."]
        elif contraindications == "pancreatitis":
            warnings = ["Prior pancreatitis history: use with caution; monitor amylase/lipase; consider GI consultation before initiating."]
        else:
            warnings = []

        return {
            "level": "approved",
            "title": "Zepbound (Tirzepatide) Indicated — OSA + Obesity",
            "summary": f"This patient meets criteria for Zepbound (tirzepatide) under the FDA-approved OSA indication: {severity_word} OSA confirmed by sleep study, obesity (BMI {bmi_word} kg/m²), no T2DM, and no absolute contraindications.",
            "details": details,
            "nextSteps": [
                "Submit prior authorization with: PSG/HSAT report (AHI ≥15), BMI documentation, T2DM exclusion, PAP therapy status, prior weight loss attempt documentation.",
                "Initiate Zepbound 2.5 mg SC weekly; titrate per protocol.",
                "Enroll patient in structured dietary counseling and physical activity program.",
                "Schedule follow-up at 4 weeks (tolerability), 12 weeks (weight/AHI response), 52 weeks (repeat sleep study).",
                "Monitor for: nausea/vomiting/diarrhea (most common), pancreatitis symptoms, gallbladder disease, kidney function.",
                "See OSA + Obesity Authorization Guide for CPT codes, ICD-10 codes, and payer-specific PA language.",
            ],
            "warnings": warnings,
        }

    # Overweight (BMI 27–29.9) — borderline.
    if obesity_status == "bmi_27_29":
        return {
            "level": "conditional",
            "title": "BMI 27–29.9 — Overweight, Not Obese: Borderline Eligibility",
            "summary": "The Zepbound OSA indication requires BMI ≥30 kg/m². BMI 27–29.9 does not meet the FDA-approved threshold for the OSA indication.",
            "details": [
                "SURMOUNT-OSA used BMI ≥30 (≥27 in Japan only) as inclusion criterion.",
                "Zepbound for weight management (not OSA-specific) requires BMI ≥30, or BMI ≥27 with ≥1 weight-related comorbidity (OSA qualifies as a weight-related comorbidity).",
                "Consider applying for PA under the weight management indication: BMI ≥27 + OSA as weight-related comorbidity.",
                "Document OSA as a weight-related comorbidity to support medical necessity.",
            ],
            "nextSteps": [
                "Apply for PA under weight management indication (BMI ≥27 + weight-related comorbidity).",
                "Document OSA as the qualifying weight-related comorbidity.",
                "Optimize PAP therapy while pursuing weight management.",
            ],
            "warnings": ["BMI 27–29.9 does not meet the OSA-specific Zepbound indication threshold. Use weight management indication pathway instead."],
        }

    return {
        "level": "conditional",
        "title": "Further Evaluation Needed",
        "summary": "Based on the information provided, additional clinical evaluation is needed before determining the appropriate treatment pathway.",
        "details": [
            "Confirm OSA severity with PSG (AHI ≥15 required for Zepbound OSA indication).",
            "Confirm BMI ≥30 for Zepbound OSA indication.",
            "Rule out T2DM (Zepbound OSA indication is for non-diabetic patients).",
            "Review contraindications: MTC/MEN2 history, pancreatitis history.",
        ],
        "nextSteps": [
            "Complete diagnostic workup and return to this assessment.",
            "Consult sleep medicine and/or endocrinology as appropriate.",
        ],
        "warnings": [],
    }
