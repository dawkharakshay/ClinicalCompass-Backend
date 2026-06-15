"""Bright Futures Well-Child Care Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/brightFuturesLogic.ts
(assessBrightFutures). AAP Bright Futures 4th Edition (2025 update).

Nullable numeric inputs (bmiPercentile, m_chatScore, phq2Score, phq9Score,
weightForLengthPercentile) follow the TS ``!== null`` semantics: a value of 0
is a real measurement and is NOT treated as missing. Only None is "not
provided", so we compare against None directly rather than using num()/||.
"""

from __future__ import annotations

LOGIC_KEY = "brightfutures"

_VISIT_AGE_YEARS = {
    "3_5_days": 0,
    "1_month": 0.08,
    "2_months": 0.17,
    "4_months": 0.33,
    "6_months": 0.5,
    "9_months": 0.75,
    "12_months": 1,
    "15_months": 1.25,
    "18_months": 1.5,
    "24_months": 2,
    "30_months": 2.5,
    "3_years": 3,
    "4_years": 4,
    "5_years": 5,
    "6_years": 6,
    "7_years": 7,
    "8_years": 8,
    "9_years": 9,
    "10_years": 10,
    "11_years": 11,
    "12_years": 12,
    "13_years": 13,
    "14_years": 14,
    "15_years": 15,
    "16_years": 16,
    "17_years": 17,
    "18_years": 18,
    "19_21_years": 19,
}

_NEXT_VISIT_MAP = {
    "3_5_days": "Return at 1 month",
    "1_month": "Return at 2 months",
    "2_months": "Return at 4 months",
    "4_months": "Return at 6 months",
    "6_months": "Return at 9 months",
    "9_months": "Return at 12 months",
    "12_months": "Return at 15 months",
    "15_months": "Return at 18 months",
    "18_months": "Return at 24 months",
    "24_months": "Return at 30 months",
    "30_months": "Return at 3 years",
    "3_years": "Return at 4 years",
    "4_years": "Return at 5 years",
    "5_years": "Return at 6 years",
    "6_years": "Return at 7 years",
    "7_years": "Return at 8 years",
    "8_years": "Return at 9 years",
    "9_years": "Return at 10 years",
    "10_years": "Return at 11 years",
    "11_years": "Return at 12 years",
    "12_years": "Return at 13 years",
    "13_years": "Return at 14 years",
    "14_years": "Return at 15 years",
    "15_years": "Return at 16 years",
    "16_years": "Return at 17 years",
    "17_years": "Return at 18 years",
    "18_years": "Return at 19–21 years",
    "19_21_years": "Transition to adult care. Provide warm handoff to adult primary care provider.",
}

_REFERENCES = [
    {
        "citation": "Hagan JF, Shaw JS, Duncan PM (eds). Bright Futures: Guidelines for Health Supervision of Infants, Children, and Adolescents, 4th Edition. AAP. 2017 (2025 update).",
        "url": "https://brightfutures.aap.org",
    },
    {
        "citation": "AAP Bright Futures Periodicity Schedule 2025. American Academy of Pediatrics.",
        "url": "https://www.aap.org/en/practice-management/bright-futures/bright-futures-periodicity-schedule/",
    },
    {
        "citation": "USPSTF. Screening for Depression and Suicide Risk in Children and Adolescents. JAMA. 2022;328(15):1534–1542.",
        "url": "https://jamanetwork.com/journals/jama/fullarticle/2797177",
    },
    {
        "citation": "AAP Council on Community Pediatrics. Poverty and Child Health in the United States. Pediatrics. 2016;137(4):e20160339.",
        "url": "https://publications.aap.org/pediatrics/article/137/4/e20160339",
    },
]


def _parse_visit_age_to_years(age) -> float:
    return _VISIT_AGE_YEARS.get(age, 0)


def assess(data: dict) -> dict:
    screenings: list[dict] = []
    guidance: list[str] = []
    urgent_flags: list[str] = []
    referrals: list[str] = []

    visit_age = data.get("visitAge")
    sex = data.get("sex")
    bmi_percentile = data.get("bmiPercentile")
    weight_for_length_percentile = data.get("weightForLengthPercentile")
    developmental_concerns = data.get("developmentalConcerns")
    m_chat_score = data.get("m_chatScore")
    phq2_score = data.get("phq2Score")
    phq9_score = data.get("phq9Score")
    asq_score = data.get("asqScore")
    has_vision_concerns = data.get("hasVisionConcerns")
    has_hearing_concerns = data.get("hasHearingConcerns")
    lead_risk_factors = data.get("leadRiskFactors")
    iron_deficiency_risk = data.get("ironDeficiencyRisk")
    tb_exposure_risk = data.get("tbExposureRisk")
    dyslipidemi_risk = data.get("dyslipidemiRisk")
    sexually_active = data.get("sexuallyActive")
    substance_use_screen_positive = data.get("substanceUseScreenPositive")
    tobacco_exposure = data.get("tobaccoExposure")
    family_social_risks = data.get("familySocialRisks")

    age_years = _parse_visit_age_to_years(visit_age)

    # Universal screenings at every visit
    if bmi_percentile is not None:
        growth_result = f"BMI %ile: {bmi_percentile}"
    elif weight_for_length_percentile is not None:
        growth_result = f"Wt/Length %ile: {weight_for_length_percentile}"
    else:
        growth_result = "Not yet applicable"

    screenings.append(
        {
            "screening": "Height/Weight/BMI",
            "method": "Measured and plotted on CDC growth chart",
            "result": growth_result,
            "action": "Plot on growth chart; assess trend",
            "frequency": "Every visit",
        }
    )
    screenings.append(
        {
            "screening": "Blood Pressure",
            "method": "Auscultatory or oscillometric",
            "result": "Measure from age 3 years; earlier if risk factors",
            "action": "Compare to age/sex/height normative tables (AAP 2017 CPG)",
            "frequency": "Annually ≥3 years",
        }
    )

    # Obesity / BMI screening
    if bmi_percentile is not None:
        if bmi_percentile >= 95:
            urgent_flags.append(
                "BMI ≥95th percentile: OBESITY — initiate AAP 2023 intensive health behavior and lifestyle treatment (IHBLT). Consider pharmacotherapy (≥12 years) or bariatric surgery (≥13 years) per AAP CPG 2023."
            )
            screenings.append(
                {
                    "screening": "Obesity workup",
                    "method": "Fasting lipids, HbA1c, ALT/AST, TSH",
                    "result": f"BMI {bmi_percentile}th percentile",
                    "action": "Initiate IHBLT. Refer to obesity medicine or pediatric weight management program",
                    "frequency": "At diagnosis and follow-up",
                }
            )
        elif bmi_percentile >= 85:
            urgent_flags.append(
                "BMI 85–94th percentile: OVERWEIGHT — counsel on healthy lifestyle. Assess for comorbidities. Refer to weight management if lifestyle counseling insufficient."
            )

    # Developmental surveillance & screening
    dev_assessment = "Developmental surveillance at every visit using structured observation and parent-reported concerns."

    if age_years <= 3:
        if asq_score:
            asq_result = f"ASQ: {asq_score}"
        else:
            asq_result = "Administer at 9, 18, 30 months"
        if asq_score == "refer":
            asq_action = "REFER to early intervention (EI) — do not delay"
        elif asq_score == "monitor":
            asq_action = "Rescreen in 1–2 months"
        else:
            asq_action = "Continue surveillance"
        screenings.append(
            {
                "screening": "Developmental Screening (ASQ-3)",
                "method": "Ages & Stages Questionnaire, 3rd edition",
                "result": asq_result,
                "action": asq_action,
                "frequency": "9, 18, 30 months (AAP 2020)",
            }
        )
        if asq_score == "refer":
            urgent_flags.append(
                "DEVELOPMENTAL SCREEN POSITIVE: Refer to early intervention (Part C, IDEA) immediately. Do not wait for diagnosis to refer."
            )
            referrals.append(
                "Early Intervention (EI) referral — Part C IDEA. Simultaneous referral to developmental pediatrician or neurodevelopmental specialist."
            )

    # Autism screening (M-CHAT-R/F)
    if (visit_age == "18_months" or visit_age == "24_months") and m_chat_score is not None:
        if m_chat_score >= 3:
            m_chat_risk = "high"
        elif m_chat_score >= 2:
            m_chat_risk = "medium"
        else:
            m_chat_risk = "low"
        if m_chat_risk == "high":
            m_chat_action = "Refer to autism specialist + EI immediately"
        elif m_chat_risk == "medium":
            m_chat_action = "Administer follow-up interview; refer if still positive"
        else:
            m_chat_action = "Continue surveillance"
        screenings.append(
            {
                "screening": "Autism Screening (M-CHAT-R/F)",
                "method": "Modified Checklist for Autism in Toddlers, Revised with Follow-Up",
                "result": f"Score: {m_chat_score} ({m_chat_risk} risk)",
                "action": m_chat_action,
                "frequency": "18 and 24 months",
            }
        )
        if m_chat_risk == "high":
            urgent_flags.append(
                f"M-CHAT-R/F HIGH RISK (score {m_chat_score}): Refer for comprehensive autism evaluation and early intervention immediately. Do not wait for diagnosis."
            )
            referrals.append(
                "Autism evaluation: developmental pediatrics, child psychiatry, or neurology. Simultaneous EI referral for ABA/speech/OT."
            )

    # Vision screening
    if age_years >= 3:
        screenings.append(
            {
                "screening": "Vision Screening",
                "method": "Instrument-based (photoscreening) preferred ≥1 year; visual acuity chart ≥3 years",
                "result": "Concerns reported" if has_vision_concerns else "No concerns",
                "action": "Refer to pediatric ophthalmology" if has_vision_concerns else "Continue annual screening",
                "frequency": "Annually ≥3 years; instrument-based at 12 and 24 months",
            }
        )
        if has_vision_concerns:
            referrals.append("Pediatric ophthalmology referral for vision concerns.")

    # Hearing screening
    if visit_age == "3_5_days":
        screenings.append(
            {
                "screening": "Newborn Hearing Screening (UNHS)",
                "method": "OAE or ABR before hospital discharge",
                "result": "Universal newborn hearing screening — mandatory in all 50 states",
                "action": "Refer to audiologist if fail. Diagnosis by 3 months, intervention by 6 months (EHDI 1-3-6 goals)",
                "frequency": "Birth",
            }
        )
    elif age_years >= 4 and age_years <= 10:
        screenings.append(
            {
                "screening": "Hearing Screening",
                "method": "Pure-tone audiometry",
                "result": "Concerns present" if has_hearing_concerns else "No concerns",
                "action": "Refer to audiology" if has_hearing_concerns else "Continue periodic screening",
                "frequency": "Ages 4, 5, 6, 8, 10 years",
            }
        )

    # Lead screening
    if age_years >= 1 and age_years <= 2:
        screenings.append(
            {
                "screening": "Lead Screening",
                "method": "Blood lead level (BLL)",
                "result": "Risk factors present" if lead_risk_factors else "Universal at 12 and 24 months in high-risk communities",
                "action": "BLL ≥3.5 μg/dL: case management, environmental investigation. BLL ≥45 μg/dL: chelation therapy",
                "frequency": "12 and 24 months; risk-based thereafter",
            }
        )
        if lead_risk_factors:
            urgent_flags.append(
                "LEAD RISK FACTORS: Obtain blood lead level. BLL ≥3.5 μg/dL requires case management and environmental investigation."
            )

    # Iron deficiency screening
    if age_years >= 1 and age_years <= 3 and iron_deficiency_risk:
        screenings.append(
            {
                "screening": "Iron Deficiency Screening",
                "method": "Hemoglobin or hematocrit",
                "result": "Risk factors present",
                "action": "Hgb <11 g/dL: trial of iron supplementation. No response → further evaluation",
                "frequency": "12 months universal; risk-based 1–5 years",
            }
        )

    # TB screening
    if tb_exposure_risk:
        screenings.append(
            {
                "screening": "TB Screening",
                "method": "TST or IGRA (IGRA preferred ≥2 years)",
                "result": "Risk factors present",
                "action": "Positive screen: chest X-ray, infectious disease referral",
                "frequency": "Risk-based",
            }
        )
        referrals.append("Infectious disease referral for TB exposure risk assessment.")

    # Dyslipidemia screening
    if (age_years >= 9 and age_years <= 11) or (age_years >= 17 and age_years <= 21) or dyslipidemi_risk:
        screenings.append(
            {
                "screening": "Dyslipidemia Screening (Fasting Lipid Panel)",
                "method": "Fasting lipid panel",
                "result": "Risk factors present (family history or obesity)" if dyslipidemi_risk else "Universal at 9–11 and 17–21 years",
                "action": "LDL ≥130 mg/dL: dietary counseling. LDL ≥190 mg/dL: consider statin (≥10 years)",
                "frequency": "Universal at 9–11 years and 17–21 years; risk-based at other ages",
            }
        )

    # Depression screening
    if age_years >= 12:
        phq2_result = f"PHQ-2 score: {phq2_score}" if phq2_score is not None else "Administer PHQ-2"
        if phq2_score is not None and phq2_score >= 2:
            phq2_action = "PHQ-2 POSITIVE: Administer PHQ-9. Score ≥10: refer to mental health. Score ≥20 or SI: urgent psychiatric evaluation"
        else:
            phq2_action = "PHQ-2 negative: continue annual screening"
        screenings.append(
            {
                "screening": "Depression Screening (PHQ-2/PHQ-9)",
                "method": "Patient Health Questionnaire-2 (PHQ-2), then PHQ-9 if positive",
                "result": phq2_result,
                "action": phq2_action,
                "frequency": "Annually ≥12 years (AAP/USPSTF)",
            }
        )
        if phq2_score is not None and phq2_score >= 2:
            urgent_flags.append(
                f"PHQ-2 POSITIVE (score {phq2_score}): Administer PHQ-9. Assess for suicidal ideation. Refer to mental health services."
            )
            if phq9_score is not None and phq9_score >= 20:
                urgent_flags.append(
                    f"PHQ-9 SEVERE (score {phq9_score}): URGENT psychiatric evaluation. Assess for active suicidal ideation and safety plan."
                )
                referrals.append("URGENT: Psychiatric evaluation for severe depression (PHQ-9 ≥20).")
            elif phq9_score is not None and phq9_score >= 10:
                referrals.append("Mental health referral for moderate-severe depression (PHQ-9 ≥10).")

    # Substance use screening
    if age_years >= 11:
        screenings.append(
            {
                "screening": "Substance Use Screening (CRAFFT)",
                "method": "CRAFFT 2.1 (Car, Relax, Alone, Forget, Friends, Trouble)",
                "result": "CRAFFT positive" if substance_use_screen_positive else "CRAFFT negative",
                "action": "Brief intervention (BI). Refer to substance use treatment if moderate-severe use" if substance_use_screen_positive else "Anticipatory guidance on substance avoidance",
                "frequency": "Annually ≥11 years",
            }
        )
        if substance_use_screen_positive:
            urgent_flags.append(
                "SUBSTANCE USE SCREEN POSITIVE: Conduct brief intervention (BI). Refer to adolescent substance use treatment if CRAFFT ≥2."
            )
            referrals.append("Adolescent substance use treatment referral (CRAFFT ≥2).")

    # STI/sexual health screening
    if sexually_active and age_years >= 13:
        screenings.append(
            {
                "screening": "Chlamydia/Gonorrhea Screening",
                "method": "NAAT (urine or vaginal swab)",
                "result": "Sexually active",
                "action": "Annual screening for all sexually active adolescents. Treat per CDC STI guidelines 2021",
                "frequency": "Annually if sexually active",
            }
        )
        screenings.append(
            {
                "screening": "HIV Screening",
                "method": "4th-generation HIV Ag/Ab combo test",
                "result": "Sexually active",
                "action": "Opt-out HIV screening. Confirm positive with Western blot or NAAT",
                "frequency": "At least once; annually if high risk",
            }
        )
        if sex == "female":
            screenings.append(
                {
                    "screening": "Pregnancy Prevention Counseling",
                    "method": "Counseling + contraception discussion",
                    "result": "Sexually active female",
                    "action": "Discuss contraceptive options including LARC. Offer HPV vaccination if not complete",
                    "frequency": "Every visit if sexually active",
                }
            )

    # Anticipatory guidance
    if age_years < 1:
        guidance.extend(
            [
                "Safe sleep: Back to sleep, firm flat surface, no soft bedding, no bed-sharing (AAP SIDS prevention 2022).",
                "Breastfeeding: Exclusive breastfeeding for 6 months, continue with complementary foods to 12 months or beyond.",
                "Vitamin D supplementation: 400 IU/day starting in first few days of life for breastfed infants.",
                "Car seat: Rear-facing until maximum weight/height limit of seat.",
                "Tummy time: Supervised tummy time when awake to prevent positional plagiocephaly.",
            ]
        )
    elif age_years < 2:
        guidance.extend(
            [
                "No screen time except video chatting for children <18–24 months (AAP 2016 media policy).",
                "Introduce allergenic foods (peanuts, eggs, tree nuts) early — LEAP trial evidence supports early introduction.",
                "Iron-rich foods: Introduce iron-fortified cereals and pureed meats at 6 months.",
                "Dental care: First dental visit by age 1. Fluoride varnish application at well-child visits.",
                "Water fluoridation: If community water not fluoridated, prescribe fluoride drops.",
            ]
        )
    elif age_years < 6:
        guidance.extend(
            [
                "Screen time: Limit to 1 hour/day of high-quality programming for ages 2–5 (AAP 2016).",
                "Reading aloud: Daily reading promotes language development and school readiness.",
                "Physical activity: 3 hours/day of active play for preschoolers.",
                "Dental hygiene: Brush twice daily with fluoride toothpaste (pea-sized amount ≥3 years).",
                "Helmet use: Bicycle helmets required for all riding activities.",
            ]
        )
    elif age_years < 12:
        guidance.extend(
            [
                "Screen time: Consistent limits; avoid screens during meals and 1 hour before bedtime.",
                "Physical activity: 60 minutes of moderate-vigorous activity daily (MVPA).",
                "Sleep: 9–12 hours/night for ages 6–12 years.",
                "Bullying prevention: Discuss cyberbullying, peer relationships, and school safety.",
                "Sun protection: SPF ≥30 sunscreen, protective clothing, limit peak sun exposure.",
            ]
        )
    else:
        guidance.extend(
            [
                "Sleep: 8–10 hours/night for adolescents. Discuss sleep hygiene and screen use at bedtime.",
                "Physical activity: 60 minutes of MVPA daily. Limit sedentary screen time.",
                "Driving safety: Graduated driver licensing laws. No phone use while driving.",
                "Substance use prevention: Discuss risks of alcohol, marijuana, vaping, and opioids.",
                "Mental health: Normalize help-seeking. Provide crisis resources (988 Suicide & Crisis Lifeline).",
                "Social media: Discuss digital footprint, online safety, and mental health effects of social media.",
            ]
        )

    if tobacco_exposure:
        guidance.append(
            "Secondhand smoke exposure: Counsel family on smoking cessation. Refer to quitline (1-800-QUIT-NOW). Tobacco smoke increases risk of SIDS, asthma, otitis media, and respiratory infections."
        )
        referrals.append(
            "Smoking cessation referral for household members (1-800-QUIT-NOW or AAP Tobacco Cessation resources)."
        )

    if family_social_risks:
        guidance.append(
            "Social determinants of health (SDOH): Screen for food insecurity (Hunger Vital Sign), housing instability, and domestic violence. Connect to community resources (WIC, SNAP, housing assistance)."
        )
        screenings.append(
            {
                "screening": "Social Determinants of Health (SDOH)",
                "method": "Hunger Vital Sign, PRAPARE, or WE CARE tool",
                "result": "Risk factors identified",
                "action": "Connect to WIC, SNAP, housing assistance, legal aid, domestic violence resources",
                "frequency": "Every visit",
            }
        )

    # Immunizations note
    visit_age_label = str(visit_age).replace("_", " ")
    immunizations_note = (
        f"Review and update immunizations per AAP 2026 Immunization Schedule at this "
        f"{visit_age_label} visit. Administer all due vaccines. Provide VIS for each vaccine administered."
    )

    # Primary recommendation
    if len(urgent_flags) > 0:
        primary_rec = urgent_flags[0]
    else:
        referral_phrase = f"{len(referrals)} referral(s) needed." if len(referrals) > 0 else "No urgent referrals."
        primary_rec = (
            f"WELL-CHILD VISIT — {visit_age_label}. {len(screenings)} screening(s) indicated. "
            f"{referral_phrase} Evidence Level A (Bright Futures 2025)."
        )

    bmi_display = bmi_percentile if bmi_percentile is not None else "N/A"
    rationale = (
        f"Visit age: {visit_age}. BMI %ile: {bmi_display}. "
        f"Developmental concerns: {_js_bool_str(developmental_concerns)}. "
        f"Recommendations per AAP Bright Futures 4th Edition (2025 update) and USPSTF 2025 pediatric preventive services."
    )

    return {
        "primaryRecommendation": primary_rec,
        "screeningsRequired": screenings,
        "anticipatoryGuidance": guidance,
        "immunizationsNote": immunizations_note,
        "developmentalAssessment": dev_assessment,
        "urgentFlags": urgent_flags,
        "referrals": referrals,
        "nextVisit": _NEXT_VISIT_MAP.get(visit_age, "Follow Bright Futures periodicity schedule"),
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }


def _js_bool_str(value) -> str:
    """JS string interpolation of a boolean: ``${true}`` -> "true"."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "undefined"
    return str(value)
