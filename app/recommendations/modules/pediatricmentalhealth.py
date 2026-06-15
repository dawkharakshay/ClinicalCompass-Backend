"""Pediatric Mental Health Screening Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/pediatricMentalHealthLogic.ts
(assessPediatricMentalHealth). AAP Mental Health Policy 2023/2025.
"""

from __future__ import annotations

from typing import Any

from app.recommendations.jslib import truthy

LOGIC_KEY = "pediatricmentalhealth"

_REFERENCES = [
    {
        "citation": "AAP. Addressing Mental Health Concerns in Pediatric Practice. Pediatrics. 2023.",
        "url": "https://publications.aap.org/pediatrics",
    },
    {
        "citation": "USPSTF. Screening for Anxiety in Children and Adolescents. JAMA. 2023;329(24):2163–2173.",
        "url": "https://jamanetwork.com/journals/jama/fullarticle/2806326",
    },
    {
        "citation": "USPSTF. Screening for Depression and Suicide Risk in Children and Adolescents. JAMA. 2022;328(15):1534–1542.",
        "url": "https://jamanetwork.com/journals/jama/fullarticle/2797177",
    },
    {
        "citation": "AAP. Suicide Prevention: Means Restriction Counseling. Pediatrics. 2024.",
        "url": "https://publications.aap.org/pediatrics",
    },
    {
        "citation": "AAP. ADHD Clinical Practice Guideline. Pediatrics. 2019 (updated 2023).",
        "url": "https://publications.aap.org/pediatrics/article/144/4/e20192528",
    },
]


def _num_or_none(x: Any) -> float | None:
    """Mirror a nullable JS ``number | null``.

    A missing field, ``None``, or an empty string maps to ``null`` (not
    obtained). Anything else is coerced to a float (preserving a literal 0).
    """
    if x is None:
        return None
    if isinstance(x, bool):
        return float(x)
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _fmt(x: float | None) -> str:
    """Reproduce JS ``${value}`` for a number that has passed a non-null check."""
    if x is not None and float(x).is_integer():
        return str(int(x))
    return str(x)


def _str_or_none(x: Any) -> str | None:
    """Nullable JS string field (e.g. ``vanderbiltScore``)."""
    if x is None:
        return None
    s = str(x).strip()
    return s if s != "" else None


def assess(data: dict) -> dict:
    phq2_score = _num_or_none(data.get("phq2Score"))
    phq9_score = _num_or_none(data.get("phq9Score"))
    phq9_item_nine_score = _num_or_none(data.get("phq9ItemNineScore"))
    gad7_score = _num_or_none(data.get("gad7Score"))
    mchat_score = _num_or_none(data.get("mchatScore"))
    crafft_score = _num_or_none(data.get("crafftScore"))
    vanderbilt_score = _str_or_none(data.get("vanderbiltScore"))

    age_group = str(data.get("ageGroup") or "")
    screen_time = data.get("screenTimeHoursPerDay")
    physical_activity = data.get("physicalActivityMinutesPerDay")

    has_active_si = truthy(data.get("hasActiveSuicidalIdeation"))
    has_suicide_plan = truthy(data.get("hasSuicidePlan"))
    has_suicide_attempt = truthy(data.get("hasSuicideAttemptHistory"))
    has_firearm = truthy(data.get("hasFirearmInHome"))
    has_meds_home = truthy(data.get("hasMedicationsInHome"))
    has_trauma = truthy(data.get("hasTraumaHistory"))
    has_lgbtq = truthy(data.get("hasLGBTQIdentity"))
    has_bullying = truthy(data.get("hasBullyingExposure"))
    has_sleep = truthy(data.get("hasSleepProblems"))

    urgent_flags: list[str] = []
    screening_results: list[dict] = []
    diagnoses: list[str] = []
    treatments: list[str] = []
    referrals: list[str] = []
    guidance: list[str] = []

    # URGENT: Suicidal ideation
    if has_active_si or (phq9_item_nine_score is not None and phq9_item_nine_score >= 1):
        urgent_flags.append(
            "ACTIVE SUICIDAL IDEATION: Conduct Columbia Suicide Severity Rating Scale "
            "(C-SSRS). Do NOT leave patient alone. Assess plan, intent, means access. "
            "If active plan or intent: EMERGENCY PSYCHIATRIC EVALUATION."
        )
        if has_suicide_plan:
            urgent_flags.append(
                "SUICIDE PLAN PRESENT: EMERGENCY — call 988 or 911. Psychiatric "
                "emergency evaluation. Do not discharge without safety plan and means "
                "restriction."
            )

    if has_suicide_attempt:
        urgent_flags.append(
            "PRIOR SUICIDE ATTEMPT: High-risk for future attempt. Refer to mental "
            "health. Means restriction counseling mandatory. Safety plan required."
        )
        referrals.append(
            "Mental health referral (priority) — prior suicide attempt is the "
            "strongest predictor of future attempt."
        )

    # Means restriction counseling
    if has_active_si or has_suicide_attempt or (phq9_score is not None and phq9_score >= 10):
        means_restriction = "MEANS RESTRICTION COUNSELING REQUIRED (AAP 2024): "
        if has_firearm:
            means_restriction += (
                "FIREARM IN HOME: Counsel on safe storage (trigger lock, gun safe, "
                "separate storage of ammunition). Ideally remove firearms from home "
                "during mental health crisis. Lethal means counseling reduces suicide "
                "risk. "
            )
            urgent_flags.append(
                "FIREARM IN HOME + MENTAL HEALTH RISK: Means restriction counseling "
                "mandatory. Recommend removing firearm from home during crisis."
            )
        if has_meds_home:
            means_restriction += (
                "MEDICATIONS IN HOME: Lock medications. Dispense in small quantities. "
                "Consider blister packs. Remove excess medications."
            )
    else:
        means_restriction = (
            "Universal means restriction counseling at all well-child visits (AAP "
            "2024): Ask about firearms in home. Counsel on safe storage regardless of "
            "mental health status."
        )
        if has_firearm:
            means_restriction += (
                " FIREARM PRESENT: Counsel on safe storage — trigger locks, gun "
                "safe, separate ammunition storage."
            )

    # Depression screening (PHQ-2/PHQ-9)
    if phq2_score is not None:
        phq2_interp = "POSITIVE — administer PHQ-9" if phq2_score >= 2 else "Negative"
        screening_results.append(
            {
                "tool": "PHQ-2",
                "score": _fmt(phq2_score),
                "interpretation": phq2_interp,
                "action": "Administer PHQ-9. Assess for suicidal ideation."
                if phq2_score >= 2
                else "Continue annual screening.",
            }
        )

    if phq9_score is not None:
        if phq9_score >= 20:
            phq9_interp = "SEVERE depression"
            phq9_action = (
                "URGENT psychiatric referral. Assess for hospitalization. Safety plan. "
                "Antidepressant + therapy."
            )
            urgent_flags.append(
                f"PHQ-9 SEVERE ({_fmt(phq9_score)}): Urgent psychiatric evaluation. "
                "Assess for hospitalization."
            )
            diagnoses.append("Major Depressive Disorder — severe")
            treatments.append(
                "SSRI (fluoxetine preferred, FDA-approved ≥8 years) + CBT. Urgent "
                "psychiatric referral."
            )
            referrals.append(
                "URGENT psychiatric evaluation for severe depression (PHQ-9 ≥20)."
            )
        elif phq9_score >= 15:
            phq9_interp = "Moderately severe depression"
            phq9_action = "Refer to mental health. Consider SSRI + CBT. Follow up in 2–4 weeks."
            diagnoses.append("Major Depressive Disorder — moderately severe")
            treatments.append(
                "SSRI (fluoxetine 10mg → 20mg, FDA-approved ≥8 years) + CBT. "
                "Refer to mental health."
            )
            referrals.append(
                "Mental health referral for moderately severe depression (PHQ-9 ≥15)."
            )
        elif phq9_score >= 10:
            phq9_interp = "Moderate depression"
            phq9_action = "Refer to mental health. Consider SSRI. Follow up in 4 weeks."
            diagnoses.append("Major Depressive Disorder — moderate")
            treatments.append(
                "CBT first-line. SSRI if CBT not available or insufficient response. "
                "Follow up 4 weeks."
            )
            referrals.append("Mental health referral for moderate depression (PHQ-9 ≥10).")
        elif phq9_score >= 5:
            phq9_interp = "Mild depression"
            phq9_action = (
                "Watchful waiting. Supportive counseling. Follow up in 4–6 weeks. "
                "Rescreen."
            )
            treatments.append(
                "Watchful waiting. Supportive counseling. Exercise, sleep hygiene, "
                "social support. Rescreen in 4–6 weeks."
            )
        else:
            phq9_interp = "Minimal/no depression"
            phq9_action = "Continue annual screening."
        screening_results.append(
            {
                "tool": "PHQ-9",
                "score": _fmt(phq9_score),
                "interpretation": phq9_interp,
                "action": phq9_action,
            }
        )

    # Anxiety screening (GAD-7 / SCARED)
    if gad7_score is not None:
        if gad7_score >= 15:
            gad7_interp = "Severe anxiety"
            gad7_action = "Refer to mental health. CBT + SSRI. Urgent if functional impairment severe."
            diagnoses.append("Generalized Anxiety Disorder — severe")
            treatments.append(
                "CBT (first-line) + SSRI (fluoxetine or sertraline). Refer to mental "
                "health."
            )
            referrals.append("Mental health referral for severe anxiety (GAD-7 ≥15).")
        elif gad7_score >= 10:
            gad7_interp = "Moderate anxiety"
            gad7_action = "CBT referral. Consider SSRI if CBT not available."
            diagnoses.append("Generalized Anxiety Disorder — moderate")
            treatments.append("CBT first-line. SSRI if CBT insufficient. Follow up 4–6 weeks.")
            referrals.append("Mental health referral for moderate anxiety (GAD-7 ≥10).")
        elif gad7_score >= 5:
            gad7_interp = "Mild anxiety"
            gad7_action = "Psychoeducation. Relaxation techniques. Follow up in 4–6 weeks."
        else:
            gad7_interp = "Minimal anxiety"
            gad7_action = "Continue annual screening."
        screening_results.append(
            {
                "tool": "GAD-7",
                "score": _fmt(gad7_score),
                "interpretation": gad7_interp,
                "action": gad7_action,
            }
        )

    # ADHD screening (Vanderbilt)
    if vanderbilt_score is not None and vanderbilt_score != "normal":
        adhd_action = (
            "ADHD confirmed: Behavior therapy (first-line ≤5 years). Medication "
            "≥6 years: methylphenidate or amphetamine salts. Refer to developmental "
            "pediatrics or child psychiatry if complex."
            if vanderbilt_score == "adhd"
            else "Possible ADHD: Obtain parent AND teacher Vanderbilt. Full evaluation "
            "per AAP 2023 ADHD CPG."
        )
        screening_results.append(
            {
                "tool": "Vanderbilt ADHD Rating Scale",
                "score": vanderbilt_score,
                "interpretation": "ADHD criteria met"
                if vanderbilt_score == "adhd"
                else "Possible ADHD — further evaluation needed",
                "action": adhd_action,
            }
        )
        if vanderbilt_score == "adhd":
            diagnoses.append("ADHD — confirmed by Vanderbilt")
            treatments.append(
                "ADHD: Behavior therapy (first-line ≤5 years). Stimulant medication "
                "≥6 years (methylphenidate or amphetamine). Classroom accommodations "
                "(504 plan or IEP). Recheck every 6 months."
            )

    # Autism screening (M-CHAT)
    if mchat_score is not None:
        mchat_risk = "high" if mchat_score >= 3 else "medium" if mchat_score >= 2 else "low"
        screening_results.append(
            {
                "tool": "M-CHAT-R/F",
                "score": _fmt(mchat_score),
                "interpretation": f"{mchat_risk.upper()} risk for autism",
                "action": "REFER to autism specialist + early intervention immediately"
                if mchat_risk == "high"
                else "Administer follow-up interview. Refer if still positive."
                if mchat_risk == "medium"
                else "Continue developmental surveillance.",
            }
        )
        if mchat_risk == "high":
            urgent_flags.append(
                f"M-CHAT HIGH RISK (score {_fmt(mchat_score)}): Refer for comprehensive "
                "autism evaluation + early intervention immediately. Do not wait for "
                "diagnosis."
            )
            referrals.append(
                "Autism evaluation: developmental pediatrics, child psychiatry, or "
                "neurology. Simultaneous early intervention referral."
            )

    # Substance use (CRAFFT)
    if crafft_score is not None and crafft_score >= 2:
        screening_results.append(
            {
                "tool": "CRAFFT",
                "score": _fmt(crafft_score),
                "interpretation": "POSITIVE — substance use concern",
                "action": "Brief intervention (BI). Refer to adolescent substance use "
                "treatment if CRAFFT ≥2.",
            }
        )
        urgent_flags.append(
            f"CRAFFT POSITIVE (score {_fmt(crafft_score)}): Brief intervention. Refer to "
            "adolescent substance use treatment."
        )
        referrals.append("Adolescent substance use treatment referral (CRAFFT ≥2).")

    # Risk factors
    if has_trauma:
        treatments.append(
            "Trauma history (ACEs): Trauma-focused CBT (TF-CBT). Refer to trauma-informed "
            "mental health provider. Screen for PTSD (Child PTSD Symptom Scale)."
        )
        referrals.append("Trauma-informed mental health referral for ACEs/trauma history.")
    if has_lgbtq:
        guidance.append(
            "LGBTQ+ youth: 4× higher risk of depression, anxiety, and suicide. "
            "Affirming care. Refer to LGBTQ+-affirming mental health provider. Discuss "
            "safe spaces and support resources (Trevor Project: 1-866-488-7386)."
        )
        if not any("mental health" in r for r in referrals):
            referrals.append("LGBTQ+-affirming mental health provider referral.")
    if has_bullying:
        guidance.append(
            "Bullying exposure (in-person or cyberbullying): Screen for depression and "
            "anxiety. Involve school counselor. Provide resources for reporting bullying."
        )
    if screen_time is not None and _num_or_none(screen_time) is not None and _num_or_none(screen_time) > 3:
        st = screen_time
        guidance.append(
            f"Excessive screen time ({st} hours/day): Limit recreational screen time to "
            "≤2 hours/day for school-age children. No screens 1 hour before bedtime. "
            "Discuss social media mental health effects."
        )
    if (
        physical_activity is not None
        and _num_or_none(physical_activity) is not None
        and _num_or_none(physical_activity) < 60
    ):
        pa = physical_activity
        guidance.append(
            f"Insufficient physical activity ({pa} min/day): Recommend 60 min/day MVPA. "
            "Physical activity reduces depression and anxiety symptoms."
        )
    if has_sleep:
        guidance.append(
            "Sleep problems: Sleep hygiene counseling (consistent bedtime, no screens 1 "
            "hour before bed, cool dark room). Adequate sleep: 9–12 hours (6–12 "
            "years), 8–10 hours (13–18 years). Melatonin 0.5–1mg for sleep "
            "onset if needed."
        )

    # Follow-up
    if len(urgent_flags) > 0:
        follow_up = (
            "URGENT follow-up within 1–2 weeks or sooner if safety concern. Provide "
            "crisis resources: 988 Suicide & Crisis Lifeline, Crisis Text Line (text HOME "
            "to 741741)."
        )
    elif len(diagnoses) > 0:
        follow_up = (
            "Follow up in 4–6 weeks to assess treatment response. Rescreen with "
            "validated tools at follow-up."
        )
    else:
        follow_up = "Annual mental health screening at well-child visits. Follow up as needed."

    if len(urgent_flags) > 0:
        primary_rec = urgent_flags[0]
    elif len(diagnoses) > 0:
        first_treatment = treatments[0] if len(treatments) > 0 else "Refer to mental health."
        primary_rec = (
            f"MENTAL HEALTH CONCERN IDENTIFIED: {', '.join(diagnoses)}. {first_treatment}"
        )
    else:
        primary_rec = (
            f"PEDIATRIC MENTAL HEALTH SCREENING — {age_group.replace('_', ' ')}. No "
            "acute concerns identified. Continue annual screening per AAP 2025 guidelines."
        )

    rationale = (
        f"Age group: {age_group}. "
        f"PHQ-9: {_fmt(phq9_score) if phq9_score is not None else 'not obtained'}. "
        f"GAD-7: {_fmt(gad7_score) if gad7_score is not None else 'not obtained'}. "
        f"Active SI: {str(has_active_si).lower()}. "
        f"Prior attempt: {str(has_suicide_attempt).lower()}. "
        f"Firearm in home: {str(has_firearm).lower()}. Per AAP 2023/2025 mental health "
        "policy."
    )

    return {
        "primaryRecommendation": primary_rec,
        "screeningResults": screening_results,
        "urgentFlags": urgent_flags,
        "diagnoses": diagnoses,
        "treatmentRecommendations": treatments,
        "referrals": referrals,
        "meansRestrictionCounseling": means_restriction,
        "anticipatoryGuidance": guidance,
        "followUpPlan": follow_up,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }
