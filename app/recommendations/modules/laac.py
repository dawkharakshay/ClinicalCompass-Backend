"""Left Atrial Appendage Closure (LAAC) — Watchman/Amulet appropriateness.

Ported 1:1 from old_static_code/client/src/lib/laacLogic.ts (calculateLAACScore).
"""

from __future__ import annotations

import math

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "laac"

_REFERENCES = [
    "Joglar JA, et al. 2023 ACC/AHA/ACCP/HRS Guideline for AF. J Am Coll Cardiol. 2024;83(1):109-279. PMID: 38033089",
    "Holmes DR, et al. PROTECT AF Trial. Percutaneous Closure of LAA vs Warfarin. Lancet. 2009;374(9689):534-542. PMID: 19683639",
    "Holmes DR, et al. PREVAIL Trial. Prospective Randomized Evaluation of the Watchman LAA Closure Device. J Am Coll Cardiol. 2014;64(1):1-12. PMID: 24998121",
    "Osmancik P, et al. PRAGUE-17 Trial. Left Atrial Appendage Closure vs Novel Anticoagulants. J Am Coll Cardiol. 2020;75(25):3122-3135. PMID: 32586591",
    "Lakkireddy D, et al. Amulet IDE Trial. Amulet vs Watchman for LAAC. JAMA. 2021;327(23):2295-2305. PMID: 34928388",
]


def _calc_cha2ds2vasc(data: dict) -> int:
    score = 0
    if truthy(data.get("chf")):
        score += 1
    if truthy(data.get("hypertension")):
        score += 1
    if truthy(data.get("age75orOlder")):
        score += 2
    if truthy(data.get("diabetes")):
        score += 1
    if truthy(data.get("stroke")):
        score += 2
    if truthy(data.get("vascularDisease")):
        score += 1
    if truthy(data.get("age65to74")):
        score += 1
    if data.get("sex") == "female":
        score += 1
    return score


def _calc_hasbled(data: dict) -> int:
    score = 0
    if truthy(data.get("uncontrolledHypertension")):
        score += 1
    if truthy(data.get("renalDisease")):
        score += 1
    if truthy(data.get("liverDisease")):
        score += 1
    if truthy(data.get("priorStrokeHistory")):
        score += 1
    if truthy(data.get("priorMajorBleeding")):
        score += 1
    if truthy(data.get("labileINR")):
        score += 1
    if truthy(data.get("elderlyAge65")):
        score += 1
    if truthy(data.get("drugsAlcohol")):
        score += 1
    return min(score, 9)


def _fmt(x: float) -> str:
    """Render a JS number the way template-literal interpolation would."""
    if x == int(x) and not math.isinf(x):
        return str(int(x))
    return repr(x)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0

    cha2ds2vasc_score = _calc_cha2ds2vasc(data)
    hasbled_score = _calc_hasbled(data)

    laa_size_ostium = parse_float(data.get("laaSizeOstium"))
    if math.isnan(laa_size_ostium):
        laa_size_ostium = 0.0

    # Absolute contraindication
    if truthy(data.get("laaThrombus")):
        warnings.append(
            "CONTRAINDICATION: LAA thrombus present — LAAC contraindicated; anticoagulate and reassess in 6 weeks"
        )
        return {
            "candidacyScore": 0,
            "cha2ds2vascScore": cha2ds2vasc_score,
            "hasbledScore": hasbled_score,
            "recommendation": "Not Recommended",
            "guidelineClass": "Class III: Harm",
            "deviceConsideration": "Defer until thrombus resolves",
            "keyFindings": key_findings,
            "warnings": warnings,
            "references": [],
        }

    if truthy(data.get("pericardialDisease")):
        warnings.append(
            "Pericardial disease — increased pericardial effusion/tamponade risk; evaluate carefully"
        )

    # Stroke risk — must be high enough to justify procedure
    if cha2ds2vasc_score >= 4:
        score += 30
        key_findings.append(
            f"High stroke risk: CHA₂DS₂-VASc {cha2ds2vasc_score} — strong indication for stroke prevention"
        )
    elif cha2ds2vasc_score >= 2:
        score += 20
        key_findings.append(
            f"Moderate stroke risk: CHA₂DS₂-VASc {cha2ds2vasc_score} — anticoagulation or LAAC indicated"
        )
    else:
        warnings.append(
            f"Low stroke risk: CHA₂DS₂-VASc {cha2ds2vasc_score} — LAAC benefit may not outweigh procedural risk"
        )
        score -= 10

    # OAC contraindication/intolerance — primary indication for LAAC
    if truthy(data.get("acContradicated")):
        score += 30
        key_findings.append(
            "Absolute contraindication to oral anticoagulation — LAAC is primary stroke prevention strategy"
        )
    elif truthy(data.get("intracranialHemorrhage")):
        score += 25
        key_findings.append(
            "Prior intracranial hemorrhage — LAAC preferred over OAC for stroke prevention (Class IIa)"
        )
    elif truthy(data.get("acFailed")):
        score += 20
        key_findings.append(
            "Stroke/TIA on therapeutic anticoagulation — LAAC reasonable as adjunct or alternative"
        )
    elif truthy(data.get("acIntolerant")) or truthy(data.get("acHighRisk")):
        score += 15
        key_findings.append(
            "OAC intolerance or high bleeding risk — LAAC is reasonable alternative (Class IIa)"
        )
    else:
        key_findings.append(
            "No OAC contraindication identified — LAAC vs OAC decision requires shared decision-making"
        )
        score += 5

    # Bleeding risk
    if hasbled_score >= 3:
        score += 10
        key_findings.append(
            f"High bleeding risk: HAS-BLED {hasbled_score} — LAAC may reduce long-term bleeding vs OAC"
        )

    if truthy(data.get("gi_bleeding")):
        score += 10
        key_findings.append(
            "Prior GI bleeding — LAAC reduces need for long-term anticoagulation"
        )

    if truthy(data.get("fallRisk")):
        score += 5
        key_findings.append(
            "High fall risk — LAAC reduces intracranial hemorrhage risk vs OAC"
        )

    # LAA anatomy
    if laa_size_ostium >= 17 and laa_size_ostium <= 31:
        key_findings.append(
            f"LAA ostium {_fmt(laa_size_ostium)} mm — within Watchman FLX sizing range (17–31 mm)"
        )
        score += 10
    elif laa_size_ostium > 31:
        warnings.append(
            f"LAA ostium {_fmt(laa_size_ostium)} mm — exceeds Watchman FLX range; consider Amulet (up to 34 mm) or surgical ligation"
        )
        score -= 5
    elif laa_size_ostium < 17 and laa_size_ostium > 0:
        warnings.append(
            f"LAA ostium {_fmt(laa_size_ostium)} mm — below minimum device size; verify with 3D TEE"
        )
        score -= 5

    if data.get("laaMorphology") == "cauliflower":
        warnings.append(
            "Cauliflower LAA morphology — higher thrombus risk and more complex implantation; experienced operator recommended"
        )
    elif data.get("laaMorphology") == "chicken-wing":
        key_findings.append(
            "Chicken-wing LAA morphology — may require specific device positioning; pre-procedure CT planning recommended"
        )

    # ESRD
    if truthy(data.get("esrd")):
        warnings.append(
            "ESRD on dialysis — contrast use limited; TEE guidance preferred; higher procedural risk"
        )
        score -= 5

    # CKD
    if parse_float(data.get("ckdStage")) >= 4:
        warnings.append(
            "Advanced CKD — contrast nephropathy risk; consider TEE-only guidance"
        )

    score = max(0, min(100, score))

    if score >= 60:
        recommendation = "Appropriate"
        guideline_class = "Class IIa: LAAC is reasonable for patients with AF and high stroke risk who have contraindications to long-term OAC"
        device_consideration = "Watchman FLX (17–31 mm) or Amulet device; pre-procedure CT angiography and TEE sizing required; 45-day TEE follow-up to confirm seal"
    elif score >= 40:
        recommendation = "Reasonable"
        guideline_class = "Class IIb: LAAC may be considered after thorough risk-benefit discussion"
        device_consideration = "Multidisciplinary discussion with electrophysiology and structural heart team; confirm OAC alternatives exhausted"
    elif score >= 20:
        recommendation = "Consider with Caution"
        guideline_class = "Individualized decision — limited evidence in this clinical scenario"
        device_consideration = "Optimize modifiable risk factors; reassess OAC candidacy; consider EP consultation"
    else:
        recommendation = "Not Recommended"
        guideline_class = "Class III: LAAC not recommended — insufficient stroke risk or OAC is safe and effective"
        device_consideration = "Continue optimal anticoagulation therapy; reassess annually"

    return {
        "candidacyScore": score,
        "cha2ds2vascScore": cha2ds2vasc_score,
        "hasbledScore": hasbled_score,
        "recommendation": recommendation,
        "guidelineClass": guideline_class,
        "deviceConsideration": device_consideration,
        "keyFindings": key_findings,
        "warnings": warnings,
        "references": _REFERENCES,
    }
