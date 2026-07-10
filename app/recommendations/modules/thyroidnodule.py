"""Thyroid Nodule Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/thyroidNoduleLogic.ts
(assessThyroidNodule). Based on ATA 2023, ACR TI-RADS, AACE/ACE/AME 2023,
Bethesda System 2023.
"""

from __future__ import annotations

from app.recommendations.jslib import coalesce, parse_float, truthy

LOGIC_KEY = "thyroidnodule"

# Static reference list surfaced as the card's "Supporting Guidelines & Evidence"
# section (auto-attached by app.recommendations.registry.get_evidence). Ported 1:1
# from old_static_code/client/src/pages/ThyroidNoduleCompass.tsx `REFERENCES`.
EVIDENCE = [
    {
        "title": "ATA Management Guidelines for Thyroid Nodules 2023 Update",
        "source": "Haugen BR et al. Thyroid. 2023",
        "description": "Updated ATA guidelines for thyroid nodule evaluation, FNA indications, molecular testing, and management of differentiated thyroid cancer.",
        "pmid": "39325028",
    },
    {
        "title": "ACR TI-RADS Lexicon and Reporting System 2017",
        "source": "Tessler FN et al. J Am Coll Radiol. 2017",
        "description": "ACR TI-RADS: standardized ultrasound reporting system for thyroid nodules. TR1-TR5 categories with size-based FNA thresholds.",
        "pmid": "28372962",
    },
    {
        "title": "Bethesda System for Reporting Thyroid Cytopathology 3rd Edition 2023",
        "source": "Ali SZ, Cibas ES. Springer. 2023",
        "description": "Updated Bethesda categories I-VI with revised malignancy risk estimates: I (5-10%), II (0-3%), III (6-18%), IV (10-40%), V (45-75%), VI (94-96%).",
        "pmid": "37154917",
    },
    {
        "title": "AACE/ACE/AME Medical Guidelines for Thyroid Nodule Management 2023",
        "source": "Gharib H et al. Endocr Pract. 2023",
        "description": "AACE/ACE/AME guidelines on thyroid nodule evaluation, FNA, and management including molecular testing for indeterminate cytology.",
        "pmid": "37116862",
    },
    {
        "title": "Active Surveillance for Low-Risk Papillary Thyroid Microcarcinoma",
        "source": "Brito JP et al. Thyroid. 2021",
        "description": "Active surveillance is a safe alternative to immediate surgery for low-risk papillary thyroid microcarcinoma (≤1 cm, no high-risk features).",
        "pmid": "33076717",
    },
    {
        "title": "Molecular Testing for Thyroid Nodules: ThyroSeq v3 and Afirma GSC",
        "source": "Nikiforov YE et al. J Clin Endocrinol Metab. 2021",
        "description": "Molecular testing (Afirma GSC, ThyroSeq v3) for indeterminate thyroid nodules (Bethesda III/IV) reduces unnecessary surgery. NPV 95-96%.",
        "pmid": "33693718",
    },
]


# ─── TI-RADS Scoring ─────────────────────────────────────────────────────────

def calculate_tirads(data: dict) -> dict:
    score = 0

    composition = data.get("composition")
    echogenicity = data.get("echogenicity")
    shape = data.get("shape")
    margin = data.get("margin")
    echogenic_foci = data.get("echogenicFoci")

    # Composition
    if composition == "cystic":
        score += 0
    elif composition == "spongiform":
        score += 0
    elif composition == "mixed":
        score += 1
    elif composition == "solid" or composition == "predominantly_solid":
        score += 2

    # Echogenicity
    if echogenicity == "anechoic":
        score += 0
    elif echogenicity == "hyperechoic" or echogenicity == "isoechoic":
        score += 1
    elif echogenicity == "hypoechoic":
        score += 2
    elif echogenicity == "markedly_hypoechoic":
        score += 3

    # Shape
    if shape == "taller_than_wide":
        score += 3

    # Margin
    if margin == "smooth":
        score += 0
    elif margin == "ill_defined":
        score += 0
    elif margin == "lobulated" or margin == "irregular":
        score += 2
    elif margin == "extrathyroidal":
        score += 3

    # Echogenic foci
    if echogenic_foci == "none":
        score += 0
    elif echogenic_foci == "large_comet_tail":
        score += 0
    elif echogenic_foci == "macrocalcifications":
        score += 1
    elif echogenic_foci == "peripheral_calcifications":
        score += 2
    elif echogenic_foci == "punctate_echogenic_foci":
        score += 3

    # Determine category
    if score == 0:
        category = "TR1"
    elif score == 2:
        category = "TR2"
    elif score == 3:
        category = "TR3"
    elif 4 <= score <= 6:
        category = "TR4"
    else:
        category = "TR5"

    return {"category": category, "score": score}


def get_tirads_malignancy_risk(category: str) -> str:
    return {
        "TR1": "Benign (0%)",
        "TR2": "Not suspicious (<2%)",
        "TR3": "Mildly suspicious (5%)",
        "TR4": "Moderately suspicious (5-20%)",
        "TR5": "Highly suspicious (>20%)",
    }.get(category, "")


def get_biopsy_threshold(category: str) -> dict:
    return {
        "TR1": {"size": 0, "recommendation": "No biopsy — benign"},
        "TR2": {"size": 0, "recommendation": "No biopsy — not suspicious"},
        "TR3": {"size": 2.5, "recommendation": "FNA if ≥2.5 cm; follow if 1.5-2.5 cm"},
        "TR4": {"size": 1.5, "recommendation": "FNA if ≥1.5 cm; follow if 1.0-1.5 cm"},
        "TR5": {"size": 1.0, "recommendation": "FNA if ≥1.0 cm; follow if 0.5-1.0 cm"},
    }[category]


# ─── Bethesda-Based Recommendation ───────────────────────────────────────────

def get_bethesda_recommendation(data: dict) -> str:
    bethesda_category = data.get("bethesdaCategory")
    age = parse_float(data.get("age"))
    nodule_size = parse_float(data.get("noduleSize"))
    high_risk = (
        truthy(data.get("priorHeadNeckRT"))
        or truthy(data.get("familyHistoryThyroidCancer"))
        or age < 25
        or age > 65
    )

    if bethesda_category == "I":
        return (
            "Bethesda I (Non-diagnostic): Repeat FNA with ultrasound guidance — "
            "if repeatedly non-diagnostic and suspicious features, consider surgery"
        )
    if bethesda_category == "II":
        return (
            "Bethesda II (Benign): No surgery — clinical follow-up and repeat "
            "ultrasound in 12-24 months"
        )
    if bethesda_category == "III":
        return (
            "Bethesda III (AUS/FLUS): Malignancy risk 10-30%. Options: "
            "(1) Repeat FNA in 3-6 months, (2) Molecular testing (ThyroSeq v3, "
            "Afirma GSC), (3) Diagnostic lobectomy"
            + (" — HIGH RISK: molecular testing or lobectomy preferred" if high_risk else "")
        )
    if bethesda_category == "IV":
        return (
            "Bethesda IV (FN/SFN): Malignancy risk 25-40%. Molecular testing "
            "(ThyroSeq v3, Afirma GSC) recommended — if suspicious/malignant: "
            "thyroid lobectomy or total thyroidectomy"
            + (" — size >4 cm: total thyroidectomy preferred" if nodule_size > 4 else "")
        )
    if bethesda_category == "V":
        return (
            "Bethesda V (Suspicious for malignancy): Malignancy risk 60-75%. "
            "Thyroid lobectomy or total thyroidectomy recommended"
        )
    if bethesda_category == "VI":
        return (
            "Bethesda VI (Malignant): Malignancy risk 97-99%. Total thyroidectomy "
            "(or lobectomy for low-risk papillary microcarcinoma)"
        )
    if bethesda_category == "not_done":
        return (
            "FNA not performed — recommendation based on TI-RADS and clinical "
            "risk factors"
        )
    return ""


# ─── Main Assessment Function ─────────────────────────────────────────────────

def assess(data: dict) -> dict:
    nodule_size = parse_float(data.get("noduleSize"))
    raw_nodule_size = _js_interpolate(data.get("noduleSize"))
    tsh_level = parse_float(data.get("tshLevel"))
    bethesda_category = data.get("bethesdaCategory")

    if truthy(data.get("tiRadsCategory")):
        ti_rads = {
            "category": data.get("tiRadsCategory"),
            "score": coalesce(parse_float_or_none(data.get("tiRadsScore")), 0),
        }
    else:
        ti_rads = calculate_tirads(data)

    biopsy_threshold = get_biopsy_threshold(ti_rads["category"])
    malignancy_risk = get_tirads_malignancy_risk(ti_rads["category"])
    bethesda_rec = get_bethesda_recommendation(data)
    warnings: list[str] = []
    next_steps: list[str] = []

    # High-risk clinical features
    high_risk_clinical = (
        truthy(data.get("priorHeadNeckRT"))
        or truthy(data.get("familyHistoryMEN2"))
        or truthy(data.get("suspiciousLymphadenopathy"))
        or truthy(data.get("dysphonia"))
        or truthy(data.get("priorThyroidCancer"))
    )

    if truthy(data.get("familyHistoryMEN2")):
        warnings.append(
            "Family history of MEN2: RET proto-oncogene testing recommended — "
            "medullary thyroid cancer risk"
        )
    if truthy(data.get("suspiciousLymphadenopathy")):
        warnings.append(
            "Suspicious cervical lymphadenopathy: FNA of lymph node recommended "
            "regardless of nodule size"
        )
    if truthy(data.get("dysphonia")):
        warnings.append(
            "Dysphonia: evaluate for vocal cord paralysis — may indicate "
            "extrathyroidal extension"
        )
    if tsh_level < 0.4:
        warnings.append(
            "Suppressed TSH: consider thyroid scan (I-123) — hyperfunctioning "
            "nodule has very low malignancy risk, FNA may not be needed"
        )
    if tsh_level > 4.0:
        warnings.append(
            "Elevated TSH: associated with higher malignancy risk in thyroid "
            "nodules — lower threshold for FNA"
        )

    # ── Urgent: compressive symptoms or suspected malignancy ──
    if truthy(data.get("compressiveSymptoms")) or (
        bethesda_category == "VI" and high_risk_clinical
    ):
        surgical_extent = (
            "Total thyroidectomy ± central neck dissection (if lymph node involvement)"
            if bethesda_category == "VI"
            else "Thyroid lobectomy or total thyroidectomy (depending on pathology)"
        )
        return {
            "decision": "surgery_recommended",
            "decisionLabel": "Surgery Recommended",
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": malignancy_risk,
            "biopsyIndicated": bethesda_category == "not_done",
            "biopsyThreshold": biopsy_threshold["recommendation"],
            "surgicalExtent": surgical_extent,
            "surgicalRationale": (
                "Compressive symptoms (dysphagia, stridor, SVC syndrome): "
                "surgical decompression indicated"
                if truthy(data.get("compressiveSymptoms"))
                else "Bethesda VI with high-risk features: total thyroidectomy recommended"
            ),
            "bethesdaRecommendation": bethesda_rec,
            "surveillanceInterval": None,
            "keyWarnings": warnings,
            "nextSteps": [
                "Endocrinology or thyroid surgery consultation",
                "Laryngoscopy if dysphonia present",
                "CT neck/chest if compressive symptoms or substernal extension",
                "Pre-operative calcium and PTH levels",
                "Discuss extent of surgery: lobectomy vs total thyroidectomy",
            ],
            "rationale": (
                "Surgery indicated for compressive symptoms or confirmed/highly "
                "suspicious malignancy."
            ),
            "evidenceLevel": "Strong",
            "guidelineSource": "ATA 2023 (PMID: 39325028); AACE/ACE/AME 2023 (PMID: 37116862)",
        }

    # ── Bethesda VI: Malignant ──
    if bethesda_category == "VI":
        return {
            "decision": "surgery_recommended",
            "decisionLabel": "Surgery Recommended (Bethesda VI — Malignant)",
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": "97-99% (Bethesda VI)",
            "biopsyIndicated": False,
            "biopsyThreshold": "FNA already performed",
            "surgicalExtent": (
                "Thyroid lobectomy (for low-risk papillary microcarcinoma ≤1 cm) — "
                "active surveillance is an option"
                if nodule_size <= 1 and not high_risk_clinical
                else "Total thyroidectomy ± central neck dissection"
            ),
            "surgicalRationale": (
                "Bethesda VI: 97-99% malignancy risk. Total thyroidectomy for "
                "tumors >1 cm or high-risk features."
            ),
            "bethesdaRecommendation": bethesda_rec,
            "keyWarnings": [
                w
                for w in [
                    *warnings,
                    (
                        "Papillary microcarcinoma (≤1 cm): active surveillance is an "
                        "ATA 2023 option for low-risk patients — discuss with patient"
                        if nodule_size <= 1
                        else ""
                    ),
                ]
                if truthy(w)
            ],
            "nextSteps": [
                "Endocrine surgery consultation",
                "Neck ultrasound to evaluate lymph nodes",
                "Discuss extent of surgery: lobectomy vs total thyroidectomy",
                "RAI eligibility discussion if total thyroidectomy planned",
                "Pre-operative calcium and PTH",
            ],
            "rationale": (
                "Bethesda VI: surgery is recommended. For low-risk papillary "
                "microcarcinoma ≤1 cm, active surveillance is an option per ATA 2023."
            ),
            "evidenceLevel": "Strong",
            "guidelineSource": "ATA 2023 (PMID: 39325028)",
        }

    # ── Bethesda V: Suspicious for malignancy ──
    if bethesda_category == "V":
        return {
            "decision": "surgery_recommended",
            "decisionLabel": "Surgery Recommended (Bethesda V — Suspicious)",
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": "60-75% (Bethesda V)",
            "biopsyIndicated": False,
            "biopsyThreshold": "FNA already performed",
            "surgicalExtent": (
                "Thyroid lobectomy or total thyroidectomy — based on nodule size, "
                "contralateral disease, and patient preference"
            ),
            "surgicalRationale": (
                "Bethesda V: 60-75% malignancy risk. Surgical excision recommended."
            ),
            "bethesdaRecommendation": bethesda_rec,
            "keyWarnings": warnings,
            "nextSteps": [
                "Endocrine surgery consultation",
                "Molecular testing (ThyroSeq v3 or Afirma GSC) may help guide extent of surgery",
                "Neck ultrasound for lymph node evaluation",
                "Discuss lobectomy vs total thyroidectomy",
            ],
            "rationale": (
                "Bethesda V: surgery recommended. Molecular testing may help "
                "differentiate malignant subtypes and guide surgical extent."
            ),
            "evidenceLevel": "Strong",
            "guidelineSource": "ATA 2023 (PMID: 39325028); Bethesda System 2023 (PMID: 37154917)",
        }

    # ── Bethesda IV: Follicular neoplasm ──
    if bethesda_category == "IV":
        return {
            "decision": "molecular_testing",
            "decisionLabel": "Molecular Testing Recommended (Bethesda IV)",
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": "25-40% (Bethesda IV)",
            "biopsyIndicated": False,
            "biopsyThreshold": "FNA already performed",
            "surgicalExtent": (
                "Thyroid lobectomy (if molecular testing suspicious/malignant) or "
                "total thyroidectomy (if >4 cm or bilateral disease)"
            ),
            "bethesdaRecommendation": bethesda_rec,
            "keyWarnings": [
                *warnings,
                "Bethesda IV: FNA cannot distinguish follicular adenoma from "
                "follicular carcinoma — molecular testing or surgery required",
            ],
            "nextSteps": [
                "Molecular testing: ThyroSeq v3 or Afirma GSC — if benign result, "
                "follow with ultrasound; if suspicious/malignant, proceed to surgery",
                "If molecular testing not available: diagnostic thyroid lobectomy",
                "Endocrine surgery consultation",
                "Neck ultrasound for lymph node evaluation",
            ],
            "rationale": (
                "Bethesda IV: molecular testing (ThyroSeq v3 or Afirma GSC) is "
                "recommended to risk-stratify and guide surgical decision. If "
                "benign result: follow with ultrasound. If suspicious/malignant: "
                "lobectomy or total thyroidectomy."
            ),
            "evidenceLevel": "Strong",
            "guidelineSource": "ATA 2023 (PMID: 39325028); Bethesda System 2023 (PMID: 37154917)",
        }

    # ── Bethesda III: AUS/FLUS ──
    if bethesda_category == "III":
        return {
            "decision": "molecular_testing",
            "decisionLabel": "Molecular Testing or Repeat FNA (Bethesda III)",
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": "10-30% (Bethesda III)",
            "biopsyIndicated": False,
            "biopsyThreshold": "FNA already performed",
            "bethesdaRecommendation": bethesda_rec,
            "surveillanceInterval": "Repeat FNA in 3-6 months if molecular testing not available",
            "keyWarnings": warnings,
            "nextSteps": [
                "Molecular testing: ThyroSeq v3 or Afirma GSC (preferred over "
                "repeat FNA per ATA 2023)",
                "If molecular testing benign: follow with ultrasound in 12-24 months",
                "If molecular testing suspicious/malignant: proceed to surgery",
                "Endocrinology consultation",
            ],
            "rationale": (
                "Bethesda III: molecular testing is preferred over repeat FNA per "
                "ATA 2023. ThyroSeq v3 has 94% sensitivity and 82% specificity for "
                "malignancy."
            ),
            "evidenceLevel": "Moderate",
            "guidelineSource": "ATA 2023 (PMID: 39325028); Bethesda System 2023 (PMID: 37154917)",
        }

    # ── Bethesda II: Benign ──
    if bethesda_category == "II":
        return {
            "decision": "repeat_ultrasound",
            "decisionLabel": "Surveillance Ultrasound (Bethesda II — Benign)",
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": "0-3% (Bethesda II)",
            "biopsyIndicated": False,
            "biopsyThreshold": "FNA already performed — benign result",
            "bethesdaRecommendation": bethesda_rec,
            "surveillanceInterval": (
                "Repeat ultrasound in 12-24 months; if stable × 2 years, extend to 3-5 years"
            ),
            "keyWarnings": [
                *warnings,
                "Bethesda II false-negative rate: 0-3% — repeat FNA if nodule grows "
                ">20% or new suspicious features develop",
            ],
            "nextSteps": [
                "Repeat ultrasound in 12-24 months",
                "If nodule grows >20% in 2 dimensions: repeat FNA",
                "Endocrinology follow-up",
            ],
            "rationale": (
                "Bethesda II: benign cytology. Surveillance ultrasound recommended. "
                "False-negative rate 0-3%."
            ),
            "evidenceLevel": "Strong",
            "guidelineSource": "ATA 2023 (PMID: 39325028)",
        }

    # ── No FNA yet — TI-RADS based recommendation ──
    biopsy_needed = biopsy_threshold["size"] > 0 and nodule_size >= biopsy_threshold["size"]
    biopsy_optional = (
        biopsy_threshold["size"] > 0
        and nodule_size >= biopsy_threshold["size"] * 0.6
        and nodule_size < biopsy_threshold["size"]
    )

    if ti_rads["category"] == "TR1" or ti_rads["category"] == "TR2":
        return {
            "decision": "no_biopsy_observe",
            "decisionLabel": "No Biopsy — Observation Only",
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": malignancy_risk,
            "biopsyIndicated": False,
            "biopsyThreshold": biopsy_threshold["recommendation"],
            "bethesdaRecommendation": bethesda_rec,
            "surveillanceInterval": (
                "No follow-up needed"
                if ti_rads["category"] == "TR1"
                else "No follow-up needed unless clinical change"
            ),
            "keyWarnings": warnings,
            "nextSteps": [
                "No FNA required",
                (
                    "No routine follow-up ultrasound needed"
                    if ti_rads["category"] == "TR2"
                    else "No further workup needed"
                ),
                "Return if new symptoms develop (dysphagia, dysphonia, rapid growth)",
            ],
            "rationale": (
                f"TI-RADS {ti_rads['category']}: benign/not suspicious. FNA not "
                f"indicated. Malignancy risk {malignancy_risk}."
            ),
            "evidenceLevel": "Strong",
            "guidelineSource": "ACR TI-RADS (PMID: 28372962); ATA 2023 (PMID: 39325028)",
        }

    if biopsy_needed or high_risk_clinical:
        next_steps.append("Ultrasound-guided FNA biopsy")
        next_steps.append("Endocrinology consultation")
        if tsh_level < 0.4:
            next_steps.append(
                "Thyroid scan (I-123) before FNA — hyperfunctioning nodule has very "
                "low malignancy risk"
            )
        return {
            "decision": "biopsy_recommended",
            "decisionLabel": (
                f"FNA Biopsy Recommended (TI-RADS {ti_rads['category']}, size "
                f"{raw_nodule_size} cm)"
            ),
            "calculatedTIRADS": ti_rads["category"],
            "tiRadsScore": ti_rads["score"],
            "malignancyRisk": malignancy_risk,
            "biopsyIndicated": True,
            "biopsyThreshold": biopsy_threshold["recommendation"],
            "bethesdaRecommendation": bethesda_rec,
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": (
                f"TI-RADS {ti_rads['category']} nodule ≥{js_number(biopsy_threshold['size'])} cm: "
                f"FNA recommended per ACR TI-RADS and ATA 2023. Malignancy risk "
                f"{malignancy_risk}."
            ),
            "evidenceLevel": "Strong",
            "guidelineSource": "ACR TI-RADS (PMID: 28372962); ATA 2023 (PMID: 39325028)",
        }

    # Surveillance only
    if ti_rads["category"] == "TR3":
        follow_up_interval = "1-2 years"
    elif ti_rads["category"] == "TR4":
        follow_up_interval = "1 year"
    elif ti_rads["category"] == "TR5":
        follow_up_interval = "6-12 months"
    else:
        follow_up_interval = "1-2 years"

    return {
        "decision": "biopsy_optional" if biopsy_optional else "repeat_ultrasound",
        "decisionLabel": (
            f"FNA Optional (TI-RADS {ti_rads['category']}, size "
            f"{raw_nodule_size} cm — below threshold)"
            if biopsy_optional
            else f"Surveillance Ultrasound (TI-RADS {ti_rads['category']})"
        ),
        "calculatedTIRADS": ti_rads["category"],
        "tiRadsScore": ti_rads["score"],
        "malignancyRisk": malignancy_risk,
        "biopsyIndicated": biopsy_optional,
        "biopsyThreshold": biopsy_threshold["recommendation"],
        "bethesdaRecommendation": bethesda_rec,
        "surveillanceInterval": f"Repeat ultrasound in {follow_up_interval}",
        "keyWarnings": warnings,
        "nextSteps": [
            (
                "FNA may be considered — discuss with patient"
                if biopsy_optional
                else f"Repeat ultrasound in {follow_up_interval}"
            ),
            "If nodule grows >20% in 2 dimensions: FNA recommended",
            "Endocrinology consultation if TSH abnormal",
        ],
        "rationale": (
            f"TI-RADS {ti_rads['category']} nodule below FNA threshold "
            f"({biopsy_threshold['recommendation']}). Surveillance ultrasound recommended."
        ),
        "evidenceLevel": "Strong",
        "guidelineSource": "ACR TI-RADS (PMID: 28372962); ATA 2023 (PMID: 39325028)",
    }


def parse_float_or_none(x):
    """Return None when the value is None (so JS ``?? 0`` can apply), else the
    raw value. ``tiRadsScore ?? 0`` in TS only substitutes on null/undefined;
    a provided value (even string) is passed through (TS typed it ``number``)."""
    if x is None:
        return None
    return x


def js_number(value: float) -> str:
    """Render a numeric literal the way JS string interpolation would.

    ``biopsyThreshold.size`` is a genuine number literal in the TS (1.0, 1.5,
    2.5); JS prints integral values without a trailing ``.0`` (``1`` -> "1").
    """
    if value == int(value):
        return str(int(value))
    return repr(value)


def _js_interpolate(value) -> str:
    """Mirror JS ``${input.noduleSize}`` template interpolation.

    The form submits ``noduleSize`` as a string, so JS prints it verbatim.
    If a real number is supplied, use JS number formatting; ``None`` -> "".
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return js_number(float(value))
    return str(value)
