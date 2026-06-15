"""Varicocele Embolization Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/varicoceleLogic.ts
(assessVaricocele + buildFertilityContext helper).

Guidelines: AUA/ASRM 2022, EAU 2024, CIRSE 2023, SIR QI 2021.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, to_bool

LOGIC_KEY = "varicocele"


def _build_fertility_context(data: dict) -> str:
    infertility_duration = parse_float(data.get("infertilityDuration"))
    partner_age = parse_float(data.get("partnerAge"))
    pain = data.get("pain")

    if infertility_duration == 0:
        if pain != "none":
            return "Pain is the primary indication. No active fertility concern reported."
        return "No active fertility concern. Treatment indicated for symptom relief or atrophy prevention."

    parts: list[str] = []
    # JS interpolates the raw input value; mirror with the original submitted value.
    parts.append(f"Infertility duration: {data.get('infertilityDuration')} months.")
    if partner_age > 0:
        parts.append(f"Female partner age: {data.get('partnerAge')} years.")
    if data.get("partnerFertilityStatus") != "not_applicable":
        status_map = {
            "normal": "Female partner fertility: normal.",
            "reduced": "Female partner fertility: reduced — ART may be needed regardless of varicocele repair.",
            "unknown": "Female partner fertility: not yet evaluated — complete female workup recommended.",
        }
        # JS: statusMap[status] ?? "" — undefined key -> "".
        parts.append(status_map.get(data.get("partnerFertilityStatus"), ""))
    if to_bool(data.get("sdfElevated")):
        parts.append("Elevated SDF: varicocele repair may reduce SDF by 6–7% (EAU 2024 Weak Recommendation).")
    if to_bool(data.get("priorArtFailure")):
        parts.append("Prior ART failure: varicocele repair before repeat ART may improve outcomes.")
    return " ".join(parts)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    urgent_flags: list[str] = []
    embolization_notes: list[str] = []
    surgery_notes: list[str] = []
    next_steps: list[str] = []
    embolization_tech_notes: list[str] = []

    grade = data.get("grade")
    pain = data.get("pain")
    laterality = data.get("laterality")
    semen_quality = data.get("semenQuality")
    prior_treatment = data.get("priorTreatment")

    is_adolescent = to_bool(data.get("isAdolescent"))
    testicular_atrophy = to_bool(data.get("testicularAtrophy"))
    sdf_elevated = to_bool(data.get("sdfElevated"))
    prior_art_failure = to_bool(data.get("priorArtFailure"))
    noa = to_bool(data.get("nonObstructiveAzoospermia"))
    prefer_minimally_invasive = to_bool(data.get("preferMinimallyInvasive"))
    general_anesthesia_risk = to_bool(data.get("generalAnesthesiaRisk"))
    anatomic_access_concern = to_bool(data.get("anatomicAccessConcern"))
    isolated_right_sided = to_bool(data.get("isolatedRightSided"))

    infertility_duration = parse_float(data.get("infertilityDuration"))
    partner_age = parse_float(data.get("partnerAge"))
    atrophy_percent = parse_float(data.get("atrophyPercent"))

    # ── Step 1: Isolated right-sided varicocele flag ──
    if isolated_right_sided:
        urgent_flags.append(
            "Isolated right-sided varicocele: consider abdominal imaging to exclude retroperitoneal pathology "
            "(malignancy, IVC obstruction) before proceeding with embolization."
        )

    # ── Step 2: Subclinical varicocele — no treatment ──
    if grade == "subclinical":
        return {
            "primaryRecommendation": "no_treatment_subclinical",
            "recommendationLabel": "Observation — No Treatment Indicated",
            "rationale": (
                "AUA/ASRM (Strong, Grade C) and EAU 2024 guidelines do not recommend treatment for subclinical "
                "varicoceles detected only on ultrasound. There is no solid evidence that repair improves semen "
                "parameters or pregnancy rates in subclinical disease."
            ),
            "embolizationCandidate": False,
            "embolizationNotes": ["Not indicated for subclinical varicocele."],
            "surgeryCandidate": False,
            "surgeryNotes": ["Not indicated for subclinical varicocele."],
            "treatmentIndicated": False,
            "indicationReason": "Subclinical varicocele — no clinical indication for repair.",
            "warnings": [
                "Routine scrotal ultrasound to identify non-palpable varicoceles is not recommended by AUA/ASRM or EAU.",
            ],
            "urgentFlags": urgent_flags,
            "fertilityContext": (
                "If infertility is the concern, evaluation should focus on other correctable causes. Subclinical "
                "varicocele repair has not demonstrated benefit."
            ),
            "nextSteps": [
                "Semen analysis if infertility is a concern",
                "Reassess if varicocele becomes clinically palpable",
                "Urology/andrology referral if infertility persists",
            ],
            "evidenceLevel": "C",
            "guidelineSource": "AUA/ASRM 2022 (Strong Rec, Grade C); EAU 2024",
            "embolizationTechNotes": [],
        }

    # ── Step 3: Determine treatment indication ──
    treatment_indicated = False
    indication_reason = ""

    has_pain_indication = pain == "persistent_moderate" or pain == "severe_limiting"
    has_fertility_indication = (
        infertility_duration > 0 and semen_quality != "normal" and not noa
    )
    has_atrophy_indication = is_adolescent and testicular_atrophy and atrophy_percent >= 20
    has_sdf_indication = sdf_elevated and prior_art_failure and infertility_duration > 0

    if has_pain_indication:
        treatment_indicated = True
        indication_reason = "Persistent scrotal pain refractory to conservative measures"
        next_steps.append("Varicocele repair for pain: ~80% response rate (SIR/CIRSE 2023)")
    if has_fertility_indication:
        treatment_indicated = True
        indication_reason = (
            indication_reason + "; infertility with abnormal semen parameters"
            if indication_reason
            else "Infertility with palpable varicocele and abnormal semen parameters"
        )
    if has_atrophy_indication:
        treatment_indicated = True
        indication_reason = (
            indication_reason + f"; testicular atrophy ({data.get('atrophyPercent')}% discrepancy)"
            if indication_reason
            else f"Adolescent testicular atrophy ({data.get('atrophyPercent')}% volume discrepancy > 20% threshold)"
        )
        warnings.append(
            "Adolescent varicocele: monitor for 6–12 months for spontaneous catch-up growth before intervention "
            "unless atrophy is progressive."
        )
    if has_sdf_indication:
        treatment_indicated = True
        indication_reason = (
            indication_reason + "; elevated SDF with ART failure"
            if indication_reason
            else "Elevated sperm DNA fragmentation with prior ART failure"
        )
        warnings.append(
            "EAU 2024 (Weak Recommendation): varicocelectomy may be considered for elevated SDF with unexplained "
            "infertility or failed ART. Evidence for improved live birth rates remains limited."
        )

    # ── Step 4: NOA pathway ──
    if noa:
        warnings.append(
            "Non-obstructive azoospermia (NOA): AUA/ASRM states there is no definitive evidence supporting "
            "varicocele repair prior to ART. Varicocele repair may increase sperm retrieval rate at micro-TESE "
            "(OR 2.65; PMID 40034026) but should be individualized."
        )
        return {
            "primaryRecommendation": "multidisciplinary_noa",
            "recommendationLabel": "Multidisciplinary Evaluation — NOA",
            "rationale": (
                "AUA/ASRM Expert Opinion: inform couples with clinical varicocele and NOA of the absence of "
                "definitive evidence supporting varicocele repair prior to ART. A recent meta-analysis "
                "(PMID 40034026) showed higher sperm retrieval rates at micro-TESE after varicocele repair "
                "(OR 2.65), but this has not translated to confirmed live birth rate improvements."
            ),
            "embolizationCandidate": False,
            "embolizationNotes": [
                "Embolization is not first-line for NOA; microsurgical varicocelectomy is preferred if repair is pursued.",
            ],
            "surgeryCandidate": True,
            "surgeryNotes": [
                "Microscopic subinguinal varicocelectomy if repair is pursued before micro-TESE.",
            ],
            "treatmentIndicated": False,
            "indicationReason": "NOA — individualized decision with reproductive endocrinology and urology",
            "warnings": warnings,
            "urgentFlags": urgent_flags,
            "fertilityContext": (
                "Discuss micro-TESE with IVF/ICSI as primary pathway. Varicocele repair may be considered to "
                "improve micro-TESE sperm retrieval rates but should not delay ART in couples with advanced "
                "female partner age."
            ),
            "nextSteps": [
                "Reproductive endocrinology/urology multidisciplinary consultation",
                "Karyotype and Y-chromosome microdeletion testing",
                "Hormone panel: FSH, LH, testosterone, inhibin B",
                "Discuss micro-TESE + IVF/ICSI as primary pathway",
            ],
            "evidenceLevel": "Expert",
            "guidelineSource": "AUA/ASRM 2022 (Expert Opinion); PMID 40034026",
            "embolizationTechNotes": [],
        }

    # ── Step 5: Partner age / ART timing consideration ──
    if partner_age >= 37 and infertility_duration > 0:
        warnings.append(
            "Female partner age ≥37: consider simultaneous varicocele repair + ART rather than sequential approach "
            "to avoid delaying ART. Semen improvement takes 3–6 months post-repair."
        )

    # ── Step 6: No treatment indication ──
    if not treatment_indicated:
        return {
            "primaryRecommendation": "observe_monitor",
            "recommendationLabel": "Observation and Monitoring",
            "rationale": (
                "Current clinical picture does not meet AUA/ASRM or EAU treatment thresholds. Treatment is indicated "
                "for: (1) persistent pain refractory to conservative measures, (2) infertility with palpable "
                "varicocele and abnormal semen parameters, or (3) adolescent testicular atrophy >20%."
            ),
            "embolizationCandidate": False,
            "embolizationNotes": [],
            "surgeryCandidate": False,
            "surgeryNotes": [],
            "treatmentIndicated": False,
            "indicationReason": "No current treatment indication met",
            "warnings": warnings,
            "urgentFlags": urgent_flags,
            "fertilityContext": (
                "Infertility evaluation ongoing — if semen parameters worsen or remain abnormal at follow-up, "
                "reassess treatment indication."
                if infertility_duration > 0
                else "No active fertility concern. Annual follow-up with semen analysis if planning future conception."
            ),
            "nextSteps": [
                "Semen analysis in 6–12 months if fertility is a future concern",
                "Reassess pain management with NSAIDs and scrotal support",
                "Urology follow-up if symptoms progress",
            ],
            "evidenceLevel": "B",
            "guidelineSource": "AUA/ASRM 2022; EAU 2024",
            "embolizationTechNotes": [],
        }

    # ── Step 7: Recurrent varicocele after prior surgery → embolization preferred ──
    if prior_treatment == "prior_surgery_recurrent":
        embolization_notes.append(
            "Percutaneous embolization is the preferred approach for recurrent varicocele after surgical repair "
            "(AUA/ASRM; CIRSE 2023). Avoids re-operative field and associated adhesion risk."
        )
        embolization_notes.append(
            "Technical success rate: 85–95% for experienced operators (SIR QI Guidelines 2021)."
        )
        embolization_tech_notes.append(
            "Retrograde approach via right femoral or right internal jugular vein; coil ± sclerosant (sodium "
            "tetradecyl sulfate or polidocanol foam) embolization of internal spermatic vein."
        )
        embolization_tech_notes.append(
            "Failure to access the spermatic vein occurs in 8–30% of cases; have surgical backup plan."
        )
        next_steps.append("IR consultation for percutaneous varicocele embolization")
        next_steps.append("Pre-procedure Doppler ultrasound to map venous anatomy")
        next_steps.append("Post-procedure semen analysis at 3 and 6 months")

        return {
            "primaryRecommendation": "embolization_for_recurrence",
            "recommendationLabel": "Percutaneous Embolization — Preferred for Recurrence",
            "rationale": (
                "AUA/ASRM and CIRSE 2023 guidelines recommend percutaneous embolization as the preferred treatment "
                "for recurrent varicocele after surgical repair. It avoids the re-operative field, has a lower "
                "hydrocele risk than repeat surgery, and achieves comparable semen parameter improvement."
            ),
            "embolizationCandidate": True,
            "embolizationNotes": embolization_notes,
            "surgeryCandidate": True,
            "surgeryNotes": [
                "Inguinal microsurgical varicocelectomy is an alternative if embolization access fails.",
                "Avoid subinguinal approach if prior subinguinal surgery was performed.",
            ],
            "treatmentIndicated": True,
            "indicationReason": indication_reason,
            "warnings": warnings,
            "urgentFlags": urgent_flags,
            "fertilityContext": _build_fertility_context(data),
            "nextSteps": next_steps,
            "evidenceLevel": "B",
            "guidelineSource": "AUA/ASRM 2022; CIRSE Standards of Practice 2023; SIR QI Guidelines 2021",
            "embolizationTechNotes": embolization_tech_notes,
        }

    # ── Step 8: Primary treatment — embolization vs surgery ──
    embolization_favored = prefer_minimally_invasive or general_anesthesia_risk
    surgery_favored = not prefer_minimally_invasive and not general_anesthesia_risk

    embolization_notes.append(
        "Percutaneous embolization: minimally invasive, outpatient, local anesthesia/IV sedation, no incision."
    )
    embolization_notes.append(
        "Technical success: 85–95%; recurrence rate 10–15% (higher than microsurgery). Chen et al. 2025 "
        "meta-analysis: lower overall complication rate vs surgical ligation (OR 0.65; PMID 41137990)."
    )
    embolization_notes.append(
        "Hydrocele risk: <1% (significantly lower than surgical repair at 3–10%)."
    )
    if anatomic_access_concern:
        warnings.append(
            "Anatomic access concern noted: catheter navigation to the internal spermatic vein may be technically "
            "challenging. Failure to access occurs in 8–30% of cases (PMID 26658060)."
        )

    surgery_notes.append(
        "Microscopic subinguinal or inguinal varicocelectomy: AUA/ASRM and EAU gold standard. Highest success "
        "rate, lowest recurrence (2–5%), lowest hydrocele risk among surgical approaches."
    )
    surgery_notes.append(
        "Semen parameter improvement: 60–80%; spontaneous pregnancy rate improvement: 26–37% (PMID 40034026)."
    )
    surgery_notes.append(
        "Laparoscopic approach: acceptable alternative but higher recurrence and hydrocele rates than microsurgery."
    )

    embolization_tech_notes.append(
        "Access: right common femoral vein or right internal jugular vein approach."
    )
    embolization_tech_notes.append(
        "Target: left internal spermatic vein (gonadal vein) — enters left renal vein at ~90°. Right gonadal vein "
        "enters IVC directly."
    )
    embolization_tech_notes.append(
        "Embolic agents: coils (0.035\" or 0.018\" micro-coils) ± liquid sclerosant (sodium tetradecyl sulfate 3%, "
        "polidocanol foam). Coil-only or combination approach per operator preference."
    )
    embolization_tech_notes.append(
        "Embolize from distal to proximal to prevent collateral recanalization. Treat all collateral channels "
        "identified on venography."
    )
    embolization_tech_notes.append(
        "Post-procedure: same-day discharge, scrotal support, avoid strenuous activity × 48 hours."
    )
    if laterality == "bilateral":
        embolization_tech_notes.append(
            "Bilateral varicocele: both gonadal veins can be treated in a single session via the same venous access."
        )

    next_steps.append("Urology/andrology consultation to confirm treatment indication")
    next_steps.append("Scrotal Doppler ultrasound to map venous anatomy pre-procedure")
    if embolization_favored:
        next_steps.append("IR consultation for percutaneous varicocele embolization")
    else:
        next_steps.append("Urology referral for microscopic varicocelectomy")
    if infertility_duration > 0:
        next_steps.append("Semen analysis at 3 and 6 months post-treatment")
        next_steps.append("Female partner fertility evaluation (ovarian reserve, tubal patency)")
    if pain != "none":
        next_steps.append("NSAIDs and scrotal support as bridge to definitive repair")

    if embolization_favored and not surgery_favored:
        primary_recommendation = "embolization_preferred"
        recommendation_label = "Percutaneous Embolization — Preferred"
        rationale = (
            "Patient profile favors percutaneous embolization: minimally invasive preference, high surgical risk, "
            "or recurrent disease. CIRSE 2023 and SIR guidelines support embolization as an effective, "
            "guideline-endorsed alternative to surgery with lower complication rates (Chen et al. 2025, OR 0.65 "
            "for complications vs surgical ligation; PMID 41137990). Recurrence rate is higher than microsurgery "
            "(10–15% vs 2–5%) but acceptable given lower procedural risk."
        )
        evidence_level = "B"
    elif surgery_favored and not embolization_favored:
        primary_recommendation = "surgery_preferred"
        recommendation_label = "Microscopic Varicocelectomy — Preferred"
        rationale = (
            "AUA/ASRM (Moderate Recommendation, Grade B) and EAU 2024 guidelines recommend microscopic "
            "varicocelectomy as the gold standard for primary treatment. It achieves the highest success rate, "
            "lowest recurrence (2–5%), and lowest hydrocele rate among surgical approaches. Semen parameter "
            "improvement in 60–80% of patients; spontaneous pregnancy rate improvement 26–37%."
        )
        evidence_level = "B"
    else:
        primary_recommendation = "embolization_or_surgery"
        recommendation_label = "Embolization or Microsurgery — Shared Decision"
        rationale = (
            "Both percutaneous embolization and microscopic varicocelectomy are guideline-endorsed options. Surgery "
            "(microscopic varicocelectomy) has the highest success and lowest recurrence rate per AUA/ASRM and "
            "EAU 2024. Embolization offers a minimally invasive alternative with lower complication rates "
            "(PMID 41137990) but higher recurrence (10–15%). Decision should be individualized based on patient "
            "preference, anatomy, and operator expertise."
        )
        evidence_level = "B"

    return {
        "primaryRecommendation": primary_recommendation,
        "recommendationLabel": recommendation_label,
        "rationale": rationale,
        "embolizationCandidate": True,
        "embolizationNotes": embolization_notes,
        "surgeryCandidate": True,
        "surgeryNotes": surgery_notes,
        "treatmentIndicated": True,
        "indicationReason": indication_reason,
        "warnings": warnings,
        "urgentFlags": urgent_flags,
        "fertilityContext": _build_fertility_context(data),
        "nextSteps": next_steps,
        "evidenceLevel": evidence_level,
        "guidelineSource": (
            "AUA/ASRM 2022 (Moderate Rec, Grade B); EAU Male Infertility 2024; CIRSE Standards of Practice 2023; "
            "SIR QI Guidelines 2021 (PMID 33610449); Chen et al. 2025 (PMID 41137990)"
        ),
        "embolizationTechNotes": embolization_tech_notes,
    }
