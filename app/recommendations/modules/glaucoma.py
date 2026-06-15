"""Glaucoma clinical recommendation engine.

Ported 1:1 from old_static_code/client/src/lib/glaucomaLogic.ts (assessGlaucoma).

Based on AAO 2026 Comprehensive Adult Eye Evaluation PPP, AAO Glaucoma PPP 2020
(updated 2024), EGS 2024, and the OHTS/EMGT/CIGTS/CNTGS/AGIS trials.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "glaucoma"


def _display_num(x):
    """Return the value as JS would interpolate it into a template string.

    Form data arrives as strings; the TS interpolates the raw `number`. We mirror
    the numeric appearance (e.g. "0.7", "24", "550") rather than a quoted string.
    """
    v = parse_float(x)
    if v != v:  # NaN
        return str(x)
    if v == int(v):
        return str(int(v))
    return repr(v)


def assess(data: dict) -> dict:
    glaucoma_type = data.get("glaucomaType")
    visual_field_status = data.get("visualFieldStatus")
    current_therapy = data.get("currentTherapy")

    iop = parse_float(data.get("iop"))
    cct = parse_float(data.get("cct"))
    cd_ratio = parse_float(data.get("cdRatio"))

    has_progression = truthy(data.get("hasProgressionOnCurrentTherapy"))
    has_high_myopia = truthy(data.get("hasHighMyopia"))
    has_diabetes = truthy(data.get("hasDiabetes"))
    has_low_corneal_hysteresis = truthy(data.get("hasLowCornealHysteresis"))
    has_low_opp = truthy(data.get("hasLowOcularPerfusionPressure"))
    is_african_american = truthy(data.get("isAfricanAmerican"))
    is_surgical_candidate = truthy(data.get("isSurgicalCandidate"))  # noqa: F841 - parity with TS input
    contralateral_eye_lost = truthy(data.get("contralateralEyeLost"))

    urgent_flags: list[str] = []
    next_steps: list[str] = []

    # ── Urgent flags ──────────────────────────────────────────────────────────
    if iop > 40:
        urgent_flags.append(
            "IOP >40 mmHg — urgent ophthalmology evaluation; consider IV acetazolamide and topical therapy immediately."
        )
    if glaucoma_type == "pacg" and iop > 30:
        urgent_flags.append(
            "Acute angle closure suspected — urgent laser peripheral iridotomy (LPI) required; refer to ophthalmology emergently."
        )
    if visual_field_status == "split_fixation":
        urgent_flags.append(
            "Visual field defect threatening fixation — urgent IOP reduction to prevent further central vision loss."
        )
    if contralateral_eye_lost:
        urgent_flags.append(
            "Monocular patient — aggressive IOP control and lower target IOP warranted; consider earlier surgical intervention."
        )
    if glaucoma_type == "poag_severe" and has_progression:
        urgent_flags.append(
            "Severe POAG with documented progression — surgical intervention (trabeculectomy/tube shunt) should be strongly considered."
        )

    # ── Diagnosis confirmation ─────────────────────────────────────────────────
    diagnosis_confirmation = ""
    if glaucoma_type == "ocular_hypertension":
        diagnosis_confirmation = "Ocular hypertension (OHT): IOP >21 mmHg with normal optic nerve and visual fields. OHTS risk calculator recommended to guide treatment decision."
    elif glaucoma_type == "glaucoma_suspect":
        diagnosis_confirmation = "Glaucoma suspect: Suspicious optic disc (C/D ≥0.7, asymmetry ≥0.2, disc hemorrhage) or borderline VF. Repeat VF and OCT RNFL to confirm or exclude."
    elif glaucoma_type == "poag_mild":
        diagnosis_confirmation = "Primary open-angle glaucoma (POAG), mild stage (MD > -6 dB). Open angle confirmed on gonioscopy."
    elif glaucoma_type == "poag_moderate":
        diagnosis_confirmation = "POAG, moderate stage (MD -6 to -12 dB). Structural-functional correlation should be confirmed with OCT RNFL."
    elif glaucoma_type == "poag_severe":
        diagnosis_confirmation = "POAG, severe stage (MD < -12 dB). Fixation-threatening risk requires aggressive IOP reduction."
    elif glaucoma_type == "ntg":
        diagnosis_confirmation = "Normal-tension glaucoma (NTG): IOP ≤21 mmHg with glaucomatous optic neuropathy. Systemic vascular risk factors and nocturnal hypotension should be evaluated."
    elif glaucoma_type == "angle_closure_suspect":
        diagnosis_confirmation = "Angle closure suspect: Narrow angles on gonioscopy (Shaffer grade ≤2). Prophylactic LPI should be considered."
    elif glaucoma_type == "pacg":
        diagnosis_confirmation = "Primary angle-closure glaucoma (PACG): Confirmed on gonioscopy with optic nerve damage. LPI is first-line; lens extraction may be indicated."
    elif glaucoma_type == "secondary_glaucoma":
        diagnosis_confirmation = "Secondary glaucoma: Treat underlying cause (neovascular: anti-VEGF + IOP control; uveitic: inflammation control; exfoliative/pigmentary: SLT often effective)."

    # ── Target IOP ────────────────────────────────────────────────────────────
    if glaucoma_type in ("ocular_hypertension", "glaucoma_suspect"):
        target_iop_range = "Target IOP: ≤21 mmHg or ≥20% reduction from baseline if treatment initiated."
    elif glaucoma_type == "poag_mild":
        target_iop_range = "Target IOP: ≤18 mmHg (≥25–30% reduction from baseline). Individualize based on CCT, age, and progression risk."
    elif glaucoma_type == "poag_moderate":
        target_iop_range = "Target IOP: ≤15–18 mmHg (≥30% reduction). Reassess target if progression documented on current therapy."
    elif glaucoma_type == "poag_severe" or visual_field_status == "split_fixation":
        target_iop_range = "Target IOP: ≤12–15 mmHg (≥30–40% reduction). Surgical intervention often required to achieve this target."
    elif glaucoma_type == "ntg":
        target_iop_range = "Target IOP: ≤12 mmHg or ≥30% reduction from baseline (CNTGS). Address systemic vascular risk factors."
    elif glaucoma_type == "pacg":
        target_iop_range = "Target IOP: ≤18 mmHg post-LPI. Lens extraction may provide additional IOP reduction."
    else:
        target_iop_range = "Target IOP: Individualize based on stage, rate of progression, and life expectancy."

    # ── Treatment strategy ────────────────────────────────────────────────────
    treatment_strategy = ""
    first_line_agent = None
    laser_option = None
    surgical_option = None

    if glaucoma_type == "ocular_hypertension":
        ohts_risk = (
            (1 if iop > 26 else 0)
            + (1 if cct < 555 else 0)
            + (1 if cd_ratio > 0.5 else 0)
            + (1 if is_african_american else 0)
            + (1 if has_diabetes else 0)
        )
        if ohts_risk >= 3:
            treatment_strategy = "High-risk OHT (OHTS score ≥3 risk factors): Treatment recommended. Prostaglandin analogue first-line."
            first_line_agent = "Prostaglandin analogue (latanoprost, bimatoprost, travoprost) — once nightly. Reduces IOP 25–35%."
        else:
            treatment_strategy = "Low-to-moderate risk OHT: Observation with monitoring every 6–12 months is acceptable. Discuss treatment vs. watchful waiting using OHTS risk calculator."
    elif glaucoma_type == "glaucoma_suspect":
        treatment_strategy = "Glaucoma suspect: Confirm diagnosis with repeat VF (24-2 SITA-Standard) and OCT RNFL. If high-risk features (thin CCT, large C/D, family history), initiate treatment as for early POAG."
    elif glaucoma_type == "angle_closure_suspect":
        treatment_strategy = "Angle closure suspect: Laser peripheral iridotomy (LPI) recommended in most cases to prevent acute closure. Gonioscopy-guided decision."
        laser_option = "Laser peripheral iridotomy (LPI) — Nd:YAG laser. Prophylactic in narrow angles (Shaffer ≤2)."
    elif glaucoma_type == "pacg":
        treatment_strategy = "PACG: LPI first-line to relieve pupillary block. If IOP remains elevated post-LPI, add topical medications. Lens extraction (phacoemulsification) increasingly preferred for PACG with visually significant cataract."
        laser_option = "LPI (Nd:YAG) — first-line for pupillary block. Consider lens extraction if cataract present."
        first_line_agent = "Prostaglandin analogue or beta-blocker post-LPI if IOP target not achieved."
    elif current_therapy == "none":
        # Treatment-naive POAG/NTG
        if glaucoma_type == "ntg":
            treatment_strategy = "NTG: Prostaglandin analogue first-line for IOP reduction. Address systemic vascular risk (nocturnal hypotension, vasospasm). Consider calcium channel blockers if vasospasm present."
            first_line_agent = "Prostaglandin analogue (latanoprost/bimatoprost) — most effective IOP reduction. Avoid beta-blockers if vasospasm or nocturnal hypotension suspected."
        else:
            treatment_strategy = "Treatment-naive POAG: Prostaglandin analogue first-line (EMGT, AGIS evidence). SLT is an equally valid first-line alternative (LiGHT trial — SLT non-inferior to drops, better adherence)."
            first_line_agent = "Prostaglandin analogue (latanoprost 0.005% once nightly) — first-line per AAO PPP. Reduces IOP 25–35%."
            laser_option = "Selective laser trabeculoplasty (SLT) — first-line alternative (LiGHT trial). 180° or 360°. Repeatable. Preferred if adherence concerns."
    elif current_therapy == "one_medication" and has_progression:
        treatment_strategy = "Progression on monotherapy: Add second agent (beta-blocker, carbonic anhydrase inhibitor, or alpha-agonist) or switch to fixed-combination drop. Consider SLT if not yet performed."
        first_line_agent = "Add timolol 0.5% twice daily OR dorzolamide/timolol fixed combination (Cosopt) OR brimonidine 0.1% twice daily."
        laser_option = "SLT if not previously performed — can reduce medication burden."
    elif current_therapy == "two_medications" and has_progression:
        treatment_strategy = "Progression on two medications: Add third agent or consider surgical intervention. Trabeculectomy or MIGS (if mild-moderate) should be discussed."
        surgical_option = "MIGS (iStent, Hydrus, GATT) for mild-moderate POAG. Trabeculectomy for moderate-severe or when lower IOP target required."
    elif current_therapy == "three_plus_medications" or (has_progression and glaucoma_type == "poag_severe"):
        treatment_strategy = "Maximal medical therapy with progression: Surgical intervention indicated. Trabeculectomy with MMC remains gold standard for achieving low IOP targets. Tube shunt (Ahmed/Baerveldt) for refractory cases."
        surgical_option = "Trabeculectomy with mitomycin C (MMC) — gold standard. Target IOP <12–15 mmHg. Tube shunt (Ahmed valve) for refractory/failed trabeculectomy."
    else:
        treatment_strategy = "Continue current therapy. Reassess IOP target and progression rate at next visit. Ensure adherence to current regimen."

    # ── Monitoring plan ───────────────────────────────────────────────────────
    if glaucoma_type in ("ocular_hypertension", "glaucoma_suspect"):
        monitoring_plan = "Monitor every 6–12 months: IOP, optic disc photos, OCT RNFL, VF (24-2). Repeat gonioscopy annually."
    elif glaucoma_type in ("poag_mild", "ntg"):
        monitoring_plan = "Monitor every 3–6 months initially, then every 6 months if stable: IOP, OCT RNFL, VF (24-2 SITA-Standard). Assess progression with trend analysis (VF MD slope, RNFL thickness)."
    elif glaucoma_type == "poag_moderate":
        monitoring_plan = "Monitor every 3–4 months: IOP, OCT RNFL, VF. Minimum 2 VF tests per year to detect progression. Disc photos annually."
    elif glaucoma_type == "poag_severe":
        monitoring_plan = "Monitor every 2–3 months: IOP, VF (10-2 if central field threatened), OCT RNFL. Post-surgical monitoring per procedure protocol."
    else:
        monitoring_plan = "Individualize monitoring frequency based on disease stage and rate of progression. Minimum annual comprehensive eye exam."

    # ── Next steps ────────────────────────────────────────────────────────────
    next_steps.append(
        "Confirm diagnosis with gonioscopy, optic disc photography, OCT RNFL, and 24-2 VF (SITA-Standard)."
    )
    if (not truthy(current_therapy)) or current_therapy == "none":
        next_steps.append(
            "Initiate first-line treatment: prostaglandin analogue or SLT (patient preference and adherence-guided)."
        )
    if has_progression:
        next_steps.append(
            "Document progression with VF trend analysis (MD slope ≥ -1 dB/year = significant) and OCT RNFL thinning."
        )
        next_steps.append(
            "Escalate treatment: add second agent, perform SLT, or refer for surgical evaluation."
        )
    if glaucoma_type == "ntg":
        next_steps.append(
            "Order 24-hour IOP curve and nocturnal BP monitoring to evaluate vascular risk contribution."
        )
        next_steps.append(
            "Refer to internist/cardiologist if nocturnal hypotension or systemic vascular disease suspected."
        )
    if glaucoma_type in ("pacg", "angle_closure_suspect"):
        next_steps.append(
            "Refer to ophthalmology for LPI. Screen fellow eye — bilateral LPI recommended if narrow angles bilateral."
        )
    if has_diabetes or has_high_myopia:
        next_steps.append(
            "Annual dilated fundus exam per AAO 2026 PPP — diabetes and high myopia are independent glaucoma risk factors."
        )
    next_steps.append(
        "Counsel on medication adherence, instillation technique, and side effects. Consider once-daily fixed-combination drops to improve compliance."
    )
    next_steps.append(
        f"Establish monitoring schedule: {monitoring_plan.split('.')[0]}."
    )

    # ── Rationale ─────────────────────────────────────────────────────────────
    gt_display = glaucoma_type.replace("_", " ") if isinstance(glaucoma_type, str) else str(glaucoma_type)
    vf_display = visual_field_status.replace("_", " ") if isinstance(visual_field_status, str) else str(visual_field_status)
    cct_descriptor = "thin — increases OHTS risk" if cct < 555 else ("thick — reduces OHTS risk" if cct > 585 else "average")
    rationale = (
        "Assessment based on AAO 2026 Comprehensive Adult Eye Evaluation PPP and AAO Glaucoma PPP. "
        f"Glaucoma type: {gt_display}. IOP: {_display_num(data.get('iop'))} mmHg. "
        f"CCT: {_display_num(data.get('cct'))} μm ({cct_descriptor}). "
        f"C/D ratio: {_display_num(data.get('cdRatio'))}. VF status: {vf_display}. "
        + ("African American race — 4–5× higher POAG risk (OHTS). " if is_african_american else "")
        + ("Low corneal hysteresis (<9 mmHg) — independent progression risk factor. " if has_low_corneal_hysteresis else "")
        + ("Low ocular perfusion pressure — vascular risk for NTG progression. " if has_low_opp else "")
    )

    # ── Evidence level ────────────────────────────────────────────────────────
    evidence_level = "I"
    if glaucoma_type in ("ntg", "secondary_glaucoma"):
        evidence_level = "II"

    return {
        "primaryRecommendation": treatment_strategy.split(".")[0] + ".",
        "diagnosisConfirmation": diagnosis_confirmation,
        "targetIOPRange": target_iop_range,
        "treatmentStrategy": treatment_strategy,
        "firstLineAgent": first_line_agent,
        "laserOption": laser_option,
        "surgicalOption": surgical_option,
        "monitoringPlan": monitoring_plan,
        "rationale": rationale,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": evidence_level,
        "references": [
            {"citation": "AAO Preferred Practice Pattern: Comprehensive Adult Medical Eye Evaluation. 2026.", "pmid": None},
            {"citation": "AAO Preferred Practice Pattern: Primary Open-Angle Glaucoma. 2020 (updated 2024).", "pmid": None},
            {"citation": "Kass MA et al. The Ocular Hypertension Treatment Study (OHTS). Arch Ophthalmol. 2002;120(6):701–713.", "pmid": "12049574"},
            {"citation": "Heijl A et al. Early Manifest Glaucoma Trial (EMGT). Arch Ophthalmol. 2002;120(10):1268–1279.", "pmid": "12365904"},
            {"citation": "Gazzard G et al. Selective laser trabeculoplasty vs drops for glaucoma (LiGHT trial). Lancet. 2019;393(10180):1505–1516.", "pmid": "30862377"},
            {"citation": "Collaborative Normal-Tension Glaucoma Study Group (CNTGS). Am J Ophthalmol. 1998;126(4):487–497.", "pmid": "9780094"},
            {"citation": "European Glaucoma Society (EGS) Terminology and Guidelines for Glaucoma. 4th ed. 2024.", "pmid": None},
            {"citation": "Weinreb RN et al. The pathophysiology and treatment of glaucoma. JAMA. 2014;311(18):1901–1911.", "pmid": "24825645"},
        ],
    }
