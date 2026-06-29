"""Pelvic Venous Disease Clinical Compass: Pelvic Venous Disorder (PeVD) scoring.

Ported 1:1 from old_static_code/client/src/lib/womensHealthLogic.ts. The module
combines two layers:

1. **Congestion score** (``assess`` core) — the original PeVD likelihood score
   synthesising ACOG / SIR / AVFS symptom, hemodynamic, and anatomic criteria.
2. **SVP classification** (Symptoms-Varices-Pathophysiology) — the modern
   instrument that clarifies pelvic venous disorder classification by defining
   homogenous patient populations. It encompasses three domains:
       S — Symptoms
       V — Varices
       P — Pathophysiology (subdomains: Anatomic [A], Hemodynamic [H], Etiologic [E])
   An individual patient's classification is designated ``SVP(A, H, E)``. For
   patients with pelvic-origin lower-extremity signs (V3) the SVP instrument is
   complementary to CEAP and the two are reported side by side.

The TypeScript oracle takes a nested ``AssessmentData`` (symptoms / hemodynamics
/ anatomy); the submitted form delivers the interface leaf fields flat, so we
read the leaf field names directly. The scoring is identical.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import intnum, js_round, parse_float, truthy

LOGIC_KEY = "womenshealth"


# ─── SVP Classification ───────────────────────────────────────────────────────


def compute_svp_classification(data: dict) -> dict:
    """Compute the Symptoms-Varices-Pathophysiology classification.

    Ported from ``computeSVPClassification``. Reflux durations are read in
    seconds (pathological reflux > 1 s on Valsalva), matching the form's
    "(sec)" inputs and the SVP oracle.
    """
    # ── S (Symptoms) Grade ────────────────────────────────────────────────────
    has_chronic_pain = truthy(data.get("chronicPelvicPain"))
    has_positional_pain = truthy(data.get("exacerbatedByStanding"))
    has_postcoital_pain = truthy(data.get("postcoitalPain"))
    has_premenstrual = truthy(data.get("premenstrualWorsening"))
    symptom_count = sum(
        1 for x in (has_chronic_pain, has_positional_pain, has_postcoital_pain, has_premenstrual) if x
    )

    if has_chronic_pain and symptom_count >= 3:
        symptoms_grade = 3
        symptoms_description = "Severe — debilitating pelvic pain with multiple aggravating factors"
    elif has_chronic_pain and symptom_count >= 2:
        symptoms_grade = 2
        symptoms_description = "Moderate — daily symptoms affecting quality of life"
    elif has_chronic_pain or has_positional_pain or has_postcoital_pain:
        symptoms_grade = 1
        symptoms_description = "Mild — intermittent pelvic discomfort, no significant functional impairment"
    else:
        symptoms_grade = 0
        symptoms_description = "Asymptomatic — no pelvic venous symptoms reported"

    # ── V (Varices) Grade ─────────────────────────────────────────────────────
    has_vulvar = truthy(data.get("vulvarVaricosities"))
    has_pelvic_varicosities = truthy(data.get("pelvicVaricosities"))
    has_uterine = truthy(data.get("uterineVeinDilation"))
    arcuate = data.get("dilatedArcuateVeins")
    has_dilated_arcuate = arcuate in ("mild", "pronounced")
    cross_pelvic = data.get("crossPelvicFlow")

    if (has_pelvic_varicosities or has_uterine) and has_vulvar and cross_pelvic == "present":
        varices_grade = 3
        varices_description = (
            "Pelvic varices with extension to lower extremities (pelvic-origin venous insufficiency)"
        )
    elif (has_pelvic_varicosities or has_uterine) and has_vulvar:
        varices_grade = 2
        varices_description = "Pelvic varices with perineal/vulvar extension"
    elif has_pelvic_varicosities or has_uterine or has_dilated_arcuate:
        varices_grade = 1
        varices_description = "Pelvic varices only (internal, detected on imaging)"
    else:
        varices_grade = 0
        varices_description = "No visible or detectable varices"

    # ── P: A (Anatomic) Grade ─────────────────────────────────────────────────
    lov_diam = parse_float(data.get("lovDiameter"))
    rov_diam = parse_float(data.get("rovDiameter"))
    has_gonadal = (not math.isnan(lov_diam) and lov_diam >= 5) or (
        not math.isnan(rov_diam) and rov_diam >= 5
    )
    has_may_thurner = truthy(data.get("mayThurner"))
    nut_angle = parse_float(data.get("nutcrackerAngle"))
    has_nutcracker = not math.isnan(nut_angle) and nut_angle < 25
    has_compression = has_may_thurner or has_nutcracker

    if has_compression:
        anatomic_grade = 4
        compression_types: list[str] = []
        if has_nutcracker:
            compression_types.append("Nutcracker (renal vein compression)")
        if has_may_thurner:
            compression_types.append("May-Thurner (iliac vein compression)")
        anatomic_description = "Venous compression syndrome: " + "; ".join(compression_types)
    elif has_gonadal and (has_uterine or has_dilated_arcuate):
        anatomic_grade = 3
        anatomic_description = "Combined gonadal vein + internal iliac tributaries involvement"
    elif has_uterine or has_dilated_arcuate:
        anatomic_grade = 2
        anatomic_description = "Internal iliac vein tributaries involvement"
    elif has_gonadal:
        anatomic_grade = 1
        anatomic_description = "Gonadal (ovarian) vein involvement"
    else:
        anatomic_grade = 0
        anatomic_description = "No anatomic abnormality identified"

    # ── P: H (Hemodynamic) Grade ──────────────────────────────────────────────
    lov_reflux = parse_float(data.get("lovRefluxDuration"))
    rov_reflux = parse_float(data.get("rovRefluxDuration"))
    has_reflux = (not math.isnan(lov_reflux) and lov_reflux > 1) or (
        not math.isnan(rov_reflux) and rov_reflux > 1
    )
    has_obstruction = has_compression  # Compression syndromes imply obstruction

    if has_reflux and has_obstruction:
        hemodynamic_grade = 3
        hemodynamic_description = "Combined reflux + obstruction"
    elif has_obstruction:
        hemodynamic_grade = 2
        hemodynamic_description = "Obstruction only (compression or thrombosis)"
    elif has_reflux:
        hemodynamic_grade = 1
        hemodynamic_description = "Reflux only (incompetent valves, retrograde flow)"
    else:
        hemodynamic_grade = 0
        hemodynamic_description = "No reflux or obstruction detected"

    # ── P: E (Etiologic) Class ────────────────────────────────────────────────
    if has_compression:
        etiologic_class = "Es"
        etiologic_description = (
            "Secondary — compression syndrome (post-thrombotic or extrinsic compression)"
        )
    elif has_reflux and has_gonadal:
        etiologic_class = "Ep"
        etiologic_description = "Primary — idiopathic degenerative valve incompetence"
    elif has_gonadal or has_pelvic_varicosities:
        etiologic_class = "Ep"
        etiologic_description = "Primary — presumed degenerative valve incompetence"
    else:
        etiologic_class = "En"
        etiologic_description = "No identifiable etiology determined from available data"

    designation = (
        f"S{symptoms_grade} V{varices_grade} "
        f"P(A{anatomic_grade}, H{hemodynamic_grade}, {etiologic_class})"
    )

    if symptoms_grade >= 2 and varices_grade >= 1 and hemodynamic_grade >= 1:
        interpretation = (
            "Symptomatic pelvic venous disease with confirmed varices and hemodynamic derangement. "
            "Intervention is likely indicated based on SVP classification. "
            "For patients with pelvic-origin lower extremity signs or symptoms, SVP should be used "
            "in conjunction with CEAP."
        )
    elif symptoms_grade >= 1 and (varices_grade >= 1 or hemodynamic_grade >= 1):
        interpretation = (
            "Symptomatic patient with imaging or hemodynamic evidence of pelvic venous disease. "
            "Further diagnostic workup recommended to fully characterize pathophysiology before "
            "treatment decisions."
        )
    elif varices_grade >= 1 or hemodynamic_grade >= 1:
        interpretation = (
            "Imaging evidence of pelvic venous abnormality in an asymptomatic or minimally "
            "symptomatic patient. Conservative management with surveillance recommended unless "
            "symptoms develop."
        )
    else:
        interpretation = (
            "No significant pelvic venous disease identified by SVP criteria. "
            "Consider alternative diagnoses if clinical suspicion persists."
        )

    return {
        "symptoms": symptoms_grade,
        "symptomsDescription": symptoms_description,
        "varices": varices_grade,
        "varicesDescription": varices_description,
        "anatomic": anatomic_grade,
        "anatomicDescription": anatomic_description,
        "hemodynamic": hemodynamic_grade,
        "hemodynamicDescription": hemodynamic_description,
        "etiologic": etiologic_class,
        "etiologicDescription": etiologic_description,
        "designation": designation,
        "interpretation": interpretation,
    }


# ─── CEAP Classification (for V3 patients with lower-extremity involvement) ────

_CEAP_CLINICAL_DESCRIPTIONS = {
    0: "C0 — No visible or palpable signs of venous disease",
    1: "C1 — Telangiectasias or reticular veins",
    2: "C2 — Varicose veins (≥3mm diameter)",
    3: "C3 — Edema without skin changes",
    4: "C4 — Skin changes (pigmentation, eczema, lipodermatosclerosis)",
    5: "C5 — Healed venous ulcer",
    6: "C6 — Active venous ulcer",
}

_CEAP_ETIOLOGY_DESCRIPTIONS = {
    "Ec": "Congenital",
    "Ep": "Primary (undetermined cause)",
    "Es": "Secondary (post-thrombotic, post-traumatic)",
    "En": "No identifiable cause",
}

_CEAP_ANATOMY_DESCRIPTIONS = {
    "As": "Superficial veins",
    "Ap": "Perforator veins",
    "Ad": "Deep veins",
    "An": "No venous location identified",
}

_CEAP_PATHOPHYSIOLOGY_DESCRIPTIONS = {
    "Pr": "Reflux",
    "Po": "Obstruction",
    "Pr,o": "Reflux and obstruction",
    "Pn": "No venous pathophysiology identifiable",
}


def compute_ceap_classification(ceap_input: dict) -> dict:
    """Compute the CEAP classification, ported from ``computeCEAPClassification``.

    ``ceap_input`` keys: ``clinicalClass`` (int 0–6), ``etiology`` (Ec/Ep/Es/En),
    ``anatomy`` (As/Ap/Ad/An), ``pathophysiology`` (Pr/Po/Pr,o/Pn).
    """
    clinical_class = ceap_input.get("clinicalClass", 0)
    if clinical_class not in _CEAP_CLINICAL_DESCRIPTIONS:
        clinical_class = 0
    etiology = ceap_input.get("etiology") or "Ep"
    anatomy = ceap_input.get("anatomy") or "As"
    pathophysiology = ceap_input.get("pathophysiology") or "Pr"

    designation = f"C{clinical_class},{etiology},{anatomy},{pathophysiology}"

    if clinical_class >= 4:
        combined_interpretation = (
            "Advanced chronic venous disease with skin changes or ulceration. "
            "When combined with SVP V3 (pelvic-origin), treatment should address both pelvic and "
            "lower extremity sources. Pelvic vein embolization should precede or accompany lower "
            "extremity intervention to prevent recurrence."
        )
    elif clinical_class >= 2:
        combined_interpretation = (
            "Visible varicose veins with pelvic venous origin (SVP V3). "
            "Standard lower extremity treatment alone may be insufficient — pelvic source must be "
            "addressed. Consider combined approach: pelvic vein embolization + foam "
            "sclerotherapy/ablation of lower extremity varices."
        )
    else:
        combined_interpretation = (
            "Early-stage lower extremity venous changes with pelvic origin. "
            "Monitor for progression. Addressing pelvic venous reflux may prevent lower extremity "
            "disease advancement."
        )

    return {
        "designation": designation,
        "clinicalClass": clinical_class,
        "clinicalDescription": _CEAP_CLINICAL_DESCRIPTIONS.get(clinical_class, ""),
        "etiology": etiology,
        "etiologyDescription": _CEAP_ETIOLOGY_DESCRIPTIONS.get(etiology, ""),
        "anatomy": anatomy,
        "anatomyDescription": _CEAP_ANATOMY_DESCRIPTIONS.get(anatomy, ""),
        "pathophysiology": pathophysiology,
        "pathophysiologyDescription": _CEAP_PATHOPHYSIOLOGY_DESCRIPTIONS.get(pathophysiology, ""),
        "combinedInterpretation": combined_interpretation,
    }


def _has_ceap_input(data: dict) -> bool:
    """True when the submission carries CEAP inputs (any CEAP field present)."""
    return any(
        data.get(k) not in (None, "")
        for k in ("ceapClinicalClass", "ceapEtiology", "ceapAnatomy", "ceapPathophysiology")
    )


# ─── SVP Treatment Algorithm ──────────────────────────────────────────────────


def compute_svp_treatment(svp: dict, ceap: dict | None = None) -> dict:
    """Map SVP grade combinations to evidence-based treatment recommendations.

    Ported from ``computeSVPTreatment``. Tiers: definitive intervention,
    diagnostic workup, conservative management, surveillance.
    """
    symptoms = svp["symptoms"]
    varices = svp["varices"]
    anatomic = svp["anatomic"]
    hemodynamic = svp["hemodynamic"]
    etiologic = svp["etiologic"]

    # ── Tier 1: Definitive Intervention ───────────────────────────────────────
    # S≥2 + V≥1 + H≥1 = symptomatic disease with confirmed varices + hemodynamic derangement.
    if symptoms >= 2 and varices >= 1 and hemodynamic >= 1:
        procedures: list[dict] = []
        special_considerations: list[str] = []
        adjunctive_therapies: list[str] = []

        if hemodynamic == 1 or hemodynamic == 3:
            procedures.append({
                "name": "Gonadal vein embolization (coils ± sclerosant)",
                "indication": (
                    f"Reflux confirmed (H{hemodynamic}); "
                    + (f"anatomic involvement A{anatomic}" if anatomic >= 1 else "gonadal vein incompetence")
                ),
                "evidenceLevel": "B",
            })

        if hemodynamic >= 2 and anatomic == 4:
            procedures.append({
                "name": "Iliac/renal vein stenting",
                "indication": (
                    f"Obstruction detected (H{hemodynamic}) with compression syndrome "
                    f"(A4: {svp['anatomicDescription']})"
                ),
                "evidenceLevel": "B",
            })

        if varices >= 2:
            procedures.append({
                "name": "Pelvic variceal sclerotherapy (foam or liquid)",
                "indication": (
                    f"Extensive varices (V{varices}) with perineal/vulvar or lower extremity extension"
                ),
                "evidenceLevel": "C",
            })

        if varices == 3 and ceap:
            procedures.append({
                "name": "Lower extremity varicose vein ablation (thermal/non-thermal)",
                "indication": (
                    f"Pelvic-origin lower extremity varices (V3 + CEAP {ceap['designation']}); "
                    "address after pelvic source"
                ),
                "evidenceLevel": "B",
            })
            special_considerations.append(
                "Pelvic vein embolization should be performed BEFORE or concurrent with lower "
                "extremity treatment to prevent recurrence."
            )
            special_considerations.append(
                f"CEAP {ceap['designation']}: {ceap['combinedInterpretation']}"
            )

        if anatomic == 4 and "Nutcracker" in svp["anatomicDescription"]:
            special_considerations.append(
                "Nutcracker syndrome confirmed: consider left renal vein transposition or stenting "
                "if hematuria/flank pain present."
            )

        if anatomic == 4 and "May-Thurner" in svp["anatomicDescription"]:
            special_considerations.append(
                "May-Thurner syndrome: iliac vein stenting indicated. Assess for DVT history and "
                "consider anticoagulation."
            )

        adjunctive_therapies.append("Graduated compression stockings (20–30 mmHg)")
        if symptoms >= 3:
            adjunctive_therapies.append("Multimodal pain management (NSAIDs, neuromodulators)")
        if etiologic == "Ep":
            adjunctive_therapies.append(
                "Hormonal therapy consideration (MPA, GnRH agonists) if pre-menopausal"
            )

        return {
            "tier": "definitive",
            "tierLabel": "Definitive Intervention Indicated",
            "primaryRecommendation": (
                f"Symptomatic PeVD confirmed ({svp['designation']}). Endovascular intervention is "
                "clinically indicated based on SVP grade combination."
            ),
            "procedures": procedures,
            "adjunctiveTherapies": adjunctive_therapies,
            "followUpInterval": "1 month post-procedure, then 3, 6, 12 months with duplex ultrasound",
            "specialConsiderations": special_considerations,
        }

    # ── Tier 2: Diagnostic Workup ─────────────────────────────────────────────
    # S≥1 + (V≥1 OR H≥1) = symptomatic with some evidence, needs confirmation.
    if symptoms >= 1 and (varices >= 1 or hemodynamic >= 1):
        procedures = []
        special_considerations = []

        procedures.append({
            "name": "Diagnostic pelvic venography with provocation",
            "indication": (
                f"Symptomatic (S{symptoms}) with "
                + (f"varices V{varices}" if varices >= 1 else f"hemodynamic findings H{hemodynamic}")
                + "; definitive characterization needed"
            ),
            "evidenceLevel": "B",
        })

        if anatomic == 0 or hemodynamic == 0:
            procedures.append({
                "name": "MR venography or CT venography",
                "indication": (
                    "Non-invasive cross-sectional imaging to map venous anatomy and identify compression"
                ),
                "evidenceLevel": "B",
            })

        if varices >= 1 and hemodynamic == 0:
            procedures.append({
                "name": "Transvaginal duplex ultrasound with Valsalva",
                "indication": "Confirm reflux in identified varices; establish hemodynamic significance",
                "evidenceLevel": "B",
            })

        special_considerations.append(
            "If diagnostic workup confirms H≥1, escalate to Tier 1 (definitive intervention)."
        )
        special_considerations.append(
            "Consider trial of conservative therapy (3–6 months) while awaiting definitive imaging."
        )

        return {
            "tier": "diagnostic",
            "tierLabel": "Diagnostic Workup Recommended",
            "primaryRecommendation": (
                f"Symptomatic patient with partial SVP criteria met ({svp['designation']}). "
                "Advanced diagnostic imaging recommended to fully characterize pathophysiology before "
                "treatment decisions."
            ),
            "procedures": procedures,
            "adjunctiveTherapies": [
                "Graduated compression stockings (15–20 mmHg)",
                "NSAIDs for symptom control",
                "Activity modification (avoid prolonged standing)",
            ],
            "followUpInterval": "3 months after diagnostic workup completion",
            "specialConsiderations": special_considerations,
        }

    # ── Tier 3: Conservative Management ───────────────────────────────────────
    # S≥1 but V0 and H0 = symptomatic without objective evidence.
    if symptoms >= 1:
        return {
            "tier": "conservative",
            "tierLabel": "Conservative Management",
            "primaryRecommendation": (
                f"Symptomatic presentation (S{symptoms}) without confirmed varices or hemodynamic "
                "derangement. Conservative management with targeted follow-up recommended."
            ),
            "procedures": [{
                "name": "Pelvic ultrasound with Doppler",
                "indication": "Baseline imaging to screen for occult varices or reflux",
                "evidenceLevel": "C",
            }],
            "adjunctiveTherapies": [
                "Graduated compression stockings (15–20 mmHg)",
                "NSAIDs or acetaminophen for pain management",
                "Pelvic floor physiotherapy",
                "Hormonal therapy consideration (if cyclic symptoms)",
                "Activity modification and weight management",
            ],
            "followUpInterval": "6 months; repeat imaging if symptoms worsen",
            "specialConsiderations": [
                "Rule out alternative diagnoses: endometriosis, adenomyosis, musculoskeletal pain.",
                "If symptoms persist >6 months despite conservative therapy, escalate to diagnostic "
                "venography.",
            ],
        }

    # ── Tier 4: Surveillance ──────────────────────────────────────────────────
    # Asymptomatic with incidental findings OR no findings.
    has_findings = varices >= 1 or hemodynamic >= 1
    return {
        "tier": "surveillance",
        "tierLabel": "Surveillance / No Intervention",
        "primaryRecommendation": (
            f"Incidental pelvic venous findings ({svp['designation']}) in an asymptomatic patient. "
            "No intervention indicated; surveillance recommended."
            if has_findings
            else f"No significant pelvic venous disease identified ({svp['designation']}). "
            "No further workup needed unless clinical suspicion changes."
        ),
        "procedures": [],
        "adjunctiveTherapies": (
            ["Lifestyle counseling (avoid prolonged standing, maintain healthy weight)",
             "Annual symptom reassessment"]
            if varices >= 1 else []
        ),
        "followUpInterval": "12 months with symptom reassessment" if varices >= 1 else "As clinically indicated",
        "specialConsiderations": (
            ["Incidental varices may become symptomatic; educate patient on warning signs."]
            if varices >= 1 else []
        ),
    }


def assess(data: dict) -> dict:
    score: float = 0.0
    max_score = 10
    criteria_met_count = 0
    criteria_total_count = 10

    # ── Symptom scoring ──────────────────────────────────────────────
    # Chronic pelvic pain >6 months is the hallmark presentation
    if truthy(data.get("chronicPelvicPain")):
        score += 1
        criteria_met_count += 1

    # Orthostatic exacerbation is characteristic of venous etiology
    if truthy(data.get("exacerbatedByStanding")):
        score += 1
        criteria_met_count += 1

    # Postcoital pain/dyspareunia strongly associated with PCS
    if truthy(data.get("postcoitalPain")):
        score += 1
        criteria_met_count += 1

    # Vulvar varicosities are a specific exam finding
    if truthy(data.get("vulvarVaricosities")):
        score += 0.5

    # Premenstrual worsening reflects hormonal influence on venous tone
    if truthy(data.get("premenstrualWorsening")):
        score += 0.5

    # Multiparity (>=2) is a significant risk factor
    if intnum(data.get("gravidity")) >= 2:
        score += 0.5
        criteria_met_count += 1

    # ── Hemodynamic scoring ──────────────────────────────────────────
    # Ovarian vein diameter thresholds:
    #   >=5mm = suggestive, >=6mm = diagnostic threshold, >=8mm = severe
    lov_diam = parse_float(data.get("lovDiameter"))
    if not math.isnan(lov_diam):
        if lov_diam >= 8:
            score += 2
            criteria_met_count += 1
        elif lov_diam >= 6:
            score += 1.5
            criteria_met_count += 1
        elif lov_diam >= 5:
            score += 0.5

    # Reflux duration >1 second on Valsalva = pathological
    lov_reflux = parse_float(data.get("lovRefluxDuration"))
    if not math.isnan(lov_reflux) and lov_reflux > 1000:
        score += 1
        criteria_met_count += 1

    # Cross-pelvic collateral flow indicates advanced incompetence
    if data.get("crossPelvicFlow") == "present":
        score += 1
        criteria_met_count += 1

    # ── Anatomy scoring ──────────────────────────────────────────────
    # Pelvic varicosities confirmed on imaging
    if truthy(data.get("pelvicVaricosities")):
        score += 1
        criteria_met_count += 1

    # Dilated arcuate veins traversing myometrium
    if data.get("dilatedArcuateVeins") == "pronounced":
        score += 0.5
        criteria_met_count += 1
    elif data.get("dilatedArcuateVeins") == "mild":
        score += 0.25

    normalized = min(score / max_score, 1)

    # ── LOV incompetence assessment ──────────────────────────────────
    # Combined diameter + reflux criteria. NB: NaN comparisons are False in
    # both JS and Python, so the missing-value behaviour matches.
    if lov_diam >= 6 and lov_reflux > 1000:
        lov_incompetence = "detected"
    elif lov_diam >= 5 or lov_reflux > 500:
        lov_incompetence = "inconclusive"
    else:
        lov_incompetence = "absent"

    # ── Nutcracker assessment ────────────────────────────────────────
    # Aortomesenteric angle <25 deg strongly suggests Nutcracker
    # Angle 25-35 deg is borderline
    nut_angle = parse_float(data.get("nutcrackerAngle"))
    if not math.isnan(nut_angle) and nut_angle < 25:
        nutcracker_risk = "detected"
    elif not math.isnan(nut_angle) and nut_angle < 35:
        nutcracker_risk = "inconclusive"
    else:
        nutcracker_risk = "absent"

    arcuate = data.get("dilatedArcuateVeins")
    if truthy(data.get("pelvicVaricosities")):
        pelvic_varicosities = "confirmed"
    elif arcuate != "none" and arcuate != "":
        pelvic_varicosities = "suspected"
    else:
        pelvic_varicosities = "absent"

    if normalized >= 0.7:
        confidence = "high"
    elif normalized >= 0.4:
        confidence = "moderate"
    else:
        confidence = "low"

    recommendation = ""
    treatment_options: list[str] = []
    label = ""
    color = "destructive"

    if normalized >= 0.7:
        label = "Criteria Met for PeVD"
        color = "primary"
        if lov_incompetence == "detected":
            tail = (
                "Left Ovarian Vein embolization is clinically indicated based on "
                "current hemodynamic profile."
            )
        else:
            tail = "Further venographic confirmation recommended before intervention."
        recommendation = (
            "Criteria met for Pelvic Venous Disorder (PeVD; formerly termed Pelvic "
            f"Congestion Syndrome). {tail}"
        )
        treatment_options.append("Ovarian vein embolization")
        treatment_options.append("Sclerotherapy")
        if nutcracker_risk == "detected":
            treatment_options.append("Renal vein stenting (Nutcracker)")
    elif normalized >= 0.4:
        label = "Moderate Suspicion for PeVD"
        color = "warning"
        recommendation = (
            "Moderate suspicion for Pelvic Venous Disorder (PeVD). Consider "
            "diagnostic venography with provocation maneuvers for definitive "
            "assessment."
        )
        treatment_options.append("Diagnostic venography")
        treatment_options.append("MR venography")
        treatment_options.append("Conservative management trial")
    else:
        label = "Low Probability for PeVD"
        color = "destructive"
        recommendation = (
            "Low probability for Pelvic Venous Disorder (PeVD) based on current "
            "data. Consider alternative differential diagnoses including "
            "endometriosis, adenomyosis, or musculoskeletal etiologies."
        )
        treatment_options.append("Expanded differential workup")
        treatment_options.append("Pelvic MRI")

    # ── SVP classification, CEAP (V3 / when provided), and treatment algorithm ──
    svp_classification = compute_svp_classification(data)
    ceap_classification = None
    if _has_ceap_input(data):
        ceap_classification = compute_ceap_classification({
            "clinicalClass": intnum(data.get("ceapClinicalClass"), 0),
            "etiology": data.get("ceapEtiology") or "Ep",
            "anatomy": data.get("ceapAnatomy") or "As",
            "pathophysiology": data.get("ceapPathophysiology") or "Pr",
        })
    svp_treatment = compute_svp_treatment(svp_classification, ceap_classification)

    result = {
        "congestionScore": normalized,
        "confidence": confidence,
        "lovIncompetence": lov_incompetence,
        "nutcrackerRisk": nutcracker_risk,
        "pelvicVaricosities": pelvic_varicosities,
        "recommendation": recommendation,
        "treatmentOptions": treatment_options,
        "label": label,
        "summary": recommendation,
        "color": color,
        "score": js_round(normalized * 100),
        "criteriaMetCount": criteria_met_count,
        "criteriaTotalCount": criteria_total_count,
        "svpClassification": svp_classification,
        "svpTreatment": svp_treatment,
    }
    if ceap_classification is not None:
        result["ceapClassification"] = ceap_classification
    return result


def present(native: dict) -> dict:
    """Fold the engine output into the uniform card, with explicit SVP/CEAP
    sections so the full SVP designation, S/V/P(A,H,E) domain breakdown, the
    treatment algorithm, and (for V3) the CEAP classification all appear in the
    downloadable clinical report / PDF export."""
    from app.recommendations.card import build_card

    native = dict(native or {})
    svp = native.pop("svpClassification", None)
    tx = native.pop("svpTreatment", None)
    ceap = native.pop("ceapClassification", None)

    card = build_card(native, logic_key=LOGIC_KEY)

    svp_sections: list[dict] = []
    if svp:
        svp_sections.append({
            "id": "svp_classification",
            "label": f"SVP Classification — {svp['designation']}",
            "type": "keyvalue",
            "items": [
                {"key": "Designation", "value": svp["designation"]},
                {"key": "S (Symptoms)", "value": f"S{svp['symptoms']} — {svp['symptomsDescription']}"},
                {"key": "V (Varices)", "value": f"V{svp['varices']} — {svp['varicesDescription']}"},
                {"key": "A (Anatomic)", "value": f"A{svp['anatomic']} — {svp['anatomicDescription']}"},
                {"key": "H (Hemodynamic)", "value": f"H{svp['hemodynamic']} — {svp['hemodynamicDescription']}"},
                {"key": "E (Etiologic)", "value": f"{svp['etiologic']} — {svp['etiologicDescription']}"},
            ],
        })
        svp_sections.append({
            "id": "svp_interpretation",
            "label": "SVP Interpretation",
            "type": "text",
            "content": svp["interpretation"],
        })
    if tx:
        svp_sections.append({
            "id": "svp_treatment",
            "label": f"SVP Treatment Algorithm — {tx['tierLabel']}",
            "type": "keyvalue",
            "items": [
                {"key": "Tier", "value": tx["tierLabel"]},
                {"key": "Primary Recommendation", "value": tx["primaryRecommendation"]},
                {"key": "Follow-up", "value": tx["followUpInterval"]},
            ],
        })
        if tx.get("procedures"):
            svp_sections.append({
                "id": "svp_procedures",
                "label": "Recommended Procedures",
                "type": "list",
                "items": [
                    f"{p['name']} — {p['indication']} (Evidence {p['evidenceLevel']})"
                    for p in tx["procedures"]
                ],
            })
        if tx.get("adjunctiveTherapies"):
            svp_sections.append({
                "id": "svp_adjunctive",
                "label": "Adjunctive Therapies",
                "type": "list",
                "items": list(tx["adjunctiveTherapies"]),
            })
        if tx.get("specialConsiderations"):
            svp_sections.append({
                "id": "svp_special_considerations",
                "label": "Special Considerations",
                "type": "list",
                "items": list(tx["specialConsiderations"]),
            })
    if ceap:
        svp_sections.append({
            "id": "ceap_classification",
            "label": f"CEAP Classification (complementary to SVP for V3) — {ceap['designation']}",
            "type": "keyvalue",
            "items": [
                {"key": "Designation", "value": ceap["designation"]},
                {"key": "Clinical", "value": ceap["clinicalDescription"]},
                {"key": "Etiology", "value": ceap["etiologyDescription"]},
                {"key": "Anatomy", "value": ceap["anatomyDescription"]},
                {"key": "Pathophysiology", "value": ceap["pathophysiologyDescription"]},
                {"key": "Combined Interpretation", "value": ceap["combinedInterpretation"]},
            ],
        })

    # SVP is the headline output for this module — show its sections first.
    card["sections"] = svp_sections + card.get("sections", [])
    return card
