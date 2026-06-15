"""Elective PCI Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/pciLogic.ts
(calculatePCIScore).

Based on the 2021 ACC/AHA/SCAI Guideline for Coronary Artery
Revascularization (Lawton JS, et al. J Am Coll Cardiol. 2022;79(2):e21-e129).
"""

from __future__ import annotations

from app.recommendations.jslib import intnum, parse_float, truthy

LOGIC_KEY = "pci"

_REFERENCES = [
    "Lawton JS, et al. 2021 ACC/AHA/SCAI Guideline for Coronary Artery Revascularization. J Am Coll Cardiol. 2022;79(2):e21-e129. PMID: 34895950",
    "Maron DJ, et al. ISCHEMIA Trial. Initial Invasive or Conservative Strategy for Stable Coronary Disease. N Engl J Med. 2020;382(15):1395-1407. PMID: 32227755",
    "Farooq V, et al. SYNTAX Score II. Lancet. 2013;381(9867):639-650. PMID: 23439103",
    "Neumann FJ, et al. 2018 ESC/EACTS Guidelines on Myocardial Revascularization. Eur Heart J. 2019;40(2):87-165. PMID: 30165437",
    "Pijls NH, et al. FAME Trial. Fractional Flow Reserve vs Angiography. N Engl J Med. 2009;360(3):213-224. PMID: 19144937",
]


def _fmt_num(x: float) -> str:
    """Render a number the way JS string interpolation would (no trailing
    ``.0`` for whole numbers)."""
    return str(int(x)) if x == int(x) else str(x)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0

    # Numeric coercions (TS treats these as numbers; form submits strings)
    syntax_score = parse_float(data.get("syntaxScore"))
    if syntax_score != syntax_score:  # NaN guard
        syntax_score = 0.0
    ccs_angina = intnum(data.get("ccsAngina"), 0)
    num_vessels = intnum(data.get("numVesselsDisease"), 0)
    lvef = parse_float(data.get("lvef"))
    if lvef != lvef:  # NaN guard
        lvef = 0.0
    omt_duration = parse_float(data.get("omtDuration"))
    if omt_duration != omt_duration:  # NaN guard
        omt_duration = 0.0
    bleeding_risk = data.get("bleedingRisk")
    ckd_stage = intnum(data.get("ckdStage"), 0)

    # SYNTAX score categorization
    if syntax_score <= 22:
        syntax_category = "Low"
    elif syntax_score <= 32:
        syntax_category = "Intermediate"
    else:
        syntax_category = "High"

    # Ischemia burden — primary driver of PCI benefit
    if truthy(data.get("stressTestHighRisk")):
        score += 30
        key_findings.append(
            "High-risk stress test findings (≥10% ischemic territory) "
            "— strong indication for revascularization"
        )
    elif truthy(data.get("stressTestPositive")):
        score += 15
        key_findings.append("Positive stress test with moderate ischemia")

    if truthy(data.get("ffrPositive")):
        score += 20
        key_findings.append(
            "Hemodynamically significant lesion confirmed by FFR ≤0.80 or iFR ≤0.89"
        )

    # Symptom burden
    if ccs_angina >= 3:
        score += 20
        key_findings.append(
            f"Severe angina (CCS Class {_fmt_num(ccs_angina)}) refractory to medical therapy"
        )
    elif ccs_angina >= 1:
        score += 10
        key_findings.append(f"Symptomatic angina (CCS Class {_fmt_num(ccs_angina)})")

    # OMT adequacy
    if not truthy(data.get("optimalMedicalTherapy")):
        score -= 15
        warnings.append(
            "Patient not on optimal medical therapy — OMT trial recommended "
            "before elective PCI per ISCHEMIA trial"
        )
    elif omt_duration >= 3:
        key_findings.append(
            f"Symptoms persist despite {_fmt_num(omt_duration)} months of optimal medical therapy"
        )

    # Anatomy considerations
    if truthy(data.get("leftMainDisease")):
        if syntax_category == "Low" or syntax_category == "Intermediate":
            score += 15
            key_findings.append(
                "Left main disease — PCI appropriate for low/intermediate "
                "SYNTAX score (Class IIa)"
            )
        else:
            warnings.append(
                "Left main disease with high SYNTAX score — CABG preferred (Class I)"
            )
            score -= 10

    if truthy(data.get("proximalLadDisease")):
        score += 10
        key_findings.append(
            "Proximal LAD disease — revascularization associated with mortality benefit"
        )

    if num_vessels == 3 and syntax_category == "High":
        warnings.append(
            "3-vessel disease with high SYNTAX score — CABG preferred over PCI (Class I)"
        )
        score -= 15
    elif num_vessels == 3 and syntax_category == "Intermediate":
        warnings.append(
            "3-vessel disease with intermediate SYNTAX score — Heart Team discussion recommended"
        )
        score -= 5

    if truthy(data.get("chronicTotalOcclusion")):
        key_findings.append(
            "Chronic total occlusion present — complex PCI; operator experience critical"
        )

    # LVEF
    if lvef < 35:
        warnings.append(
            "Severely reduced LVEF (<35%) — consider hemodynamic support and "
            "Heart Team evaluation"
        )
    elif lvef < 50:
        key_findings.append(
            f"Reduced LVEF ({_fmt_num(lvef)}%) — revascularization may improve "
            "function if viable myocardium present"
        )
        score += 5

    # DAPT tolerance — critical for PCI
    if not truthy(data.get("daptTolerance")):
        warnings.append(
            "Unable to tolerate DAPT — high stent thrombosis risk; consider "
            "CABG or medical therapy"
        )
        score -= 20

    # Bleeding risk
    if bleeding_risk == "high":
        warnings.append(
            "High bleeding risk — consider bare-metal stent or short DAPT duration strategy"
        )
        score -= 5

    # CKD
    if ckd_stage >= 4:
        warnings.append(
            "Advanced CKD (Stage ≥4) — contrast nephropathy risk; "
            "pre-hydration and iso-osmolar contrast required"
        )

    # Prior CABG
    if truthy(data.get("priorCABG")):
        key_findings.append(
            "Prior CABG — native vessel PCI or SVG intervention; higher risk of no-reflow"
        )

    # Clamp score
    score = max(0, min(100, score))

    # Determine recommendation
    if score >= 60:
        recommendation = "Appropriate"
        appropriateness_rating = (
            "Score 7–9: Elective PCI is appropriate based on clinical and "
            "anatomical criteria"
        )
        preferred_strategy = (
            "Single-vessel or low-complexity PCI with drug-eluting stent (DES)"
            if (num_vessels == 1 or syntax_category == "Low")
            else "Heart Team discussion; PCI feasible for low/intermediate SYNTAX anatomy"
        )
    elif score >= 35:
        recommendation = "May Be Appropriate"
        appropriateness_rating = (
            "Score 4–6: Elective PCI may be appropriate; individualized decision required"
        )
        preferred_strategy = (
            "Heart Team evaluation recommended; consider ISCHEMIA trial data for stable CAD"
        )
    else:
        recommendation = "Rarely Appropriate"
        appropriateness_rating = (
            "Score 1–3: Elective PCI is rarely appropriate in this clinical scenario"
        )
        preferred_strategy = (
            "Optimize medical therapy; reassess symptoms at 3–6 months; "
            "consider CABG if anatomy favors"
        )

    return {
        "candidacyScore": score,
        "recommendation": recommendation,
        "appropriatenessRating": appropriateness_rating,
        "syntaxCategory": syntax_category,
        "preferredStrategy": preferred_strategy,
        "keyFindings": key_findings,
        "warnings": warnings,
        "references": list(_REFERENCES),
    }
