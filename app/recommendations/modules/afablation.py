"""Atrial Fibrillation Catheter Ablation appropriateness.

Ported 1:1 from old_static_code/client/src/lib/afAblationLogic.ts
(calculateAFAblationScore).

Based on the 2023 ACC/AHA/ACCP/HRS Guideline for Diagnosis and Management of
Atrial Fibrillation.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "afablation"

_REFERENCES = [
    "Joglar JA, et al. 2023 ACC/AHA/ACCP/HRS Guideline for Diagnosis and Management of Atrial Fibrillation. J Am Coll Cardiol. 2024;83(1):109-279. PMID: 38033089",
    "Calkins H, et al. 2017 HRS/EHRA/ECAS/APHRS/SOLAECE Expert Consensus Statement on Catheter Ablation of AF. Heart Rhythm. 2017;14(10):e275-e444. PMID: 28506916",
    "Marrouche NF, et al. CASTLE-AF Trial. Catheter Ablation for AF with Heart Failure. N Engl J Med. 2018;378(5):417-427. PMID: 29385358",
    "Packer DL, et al. CABANA Trial. Catheter Ablation vs Medical Therapy for AF. JAMA. 2019;321(13):1261-1274. PMID: 30874766",
    "Pathak RK, et al. LEGACY Trial. Long-Term Effect of Goal-Directed Weight Management on AF. J Am Coll Cardiol. 2015;65(20):2159-2169. PMID: 25997708",
]


def _fmt_num(x: float) -> str:
    """Reproduce JS number-to-string in template literals (no trailing .0)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def _num(x: object) -> float:
    v = parse_float(x)
    return 0.0 if math.isnan(v) else v


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


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0

    cha2ds2vasc_score = _calc_cha2ds2vasc(data)

    af_type = data.get("afType")
    symptom_burden = data.get("symptomBurden")
    la_size = _num(data.get("laSize"))
    lvef = _num(data.get("lvef"))
    bmi = _num(data.get("bmi"))
    aad_trialed = data.get("aadTrialed") or []

    # Absolute contraindications
    if truthy(data.get("recentThrombus")):
        warnings.append(
            "CONTRAINDICATION: LAA thrombus on TEE — ablation contraindicated until thrombus resolves with anticoagulation"
        )
        return {
            "candidacyScore": 0,
            "cha2ds2vascScore": cha2ds2vasc_score,
            "recommendation": "Not Recommended",
            "guidelineClass": "Class III: Harm",
            "preferredApproach": "Anticoagulate for ≥3 weeks and repeat TEE before reconsidering ablation",
            "keyFindings": key_findings,
            "warnings": warnings,
            "anticoagulationNote": "Anticoagulation required; repeat TEE in 3–6 weeks",
            "references": [],
        }

    if truthy(data.get("activeInfection")):
        warnings.append("CONTRAINDICATION: Active infection — defer ablation until resolved")

    # AF type and symptom burden — primary drivers
    if af_type == "paroxysmal":
        score += 25
        key_findings.append("Paroxysmal AF — highest success rates with pulmonary vein isolation (PVI)")
    elif af_type == "persistent":
        score += 20
        key_findings.append("Persistent AF — PVI with possible additional substrate modification; success rates 60–80%")
    elif af_type == "longstanding-persistent":
        score += 10
        key_findings.append("Long-standing persistent AF — lower success rates; may require staged procedures")
        warnings.append(
            "Long-standing persistent AF — discuss realistic success rates (50–60%) and possible need for repeat procedures"
        )
    else:
        warnings.append(
            "Permanent AF — ablation generally not indicated unless rhythm control strategy is being re-initiated"
        )
        score -= 20

    if symptom_burden == "severe":
        score += 25
        key_findings.append("Severe symptom burden — ablation strongly supported for quality-of-life improvement")
    elif symptom_burden == "moderate":
        score += 15
        key_findings.append("Moderate symptoms — ablation appropriate after AAD failure or as first-line option")
    elif symptom_burden == "mild":
        score += 5
    else:
        warnings.append(
            "Asymptomatic AF — ablation benefit primarily for rhythm control; discuss risks vs benefits"
        )
        score -= 10

    # AAD history
    if truthy(data.get("aadFailed")):
        score += 20
        key_findings.append(
            f"Failed AAD therapy ({', '.join(str(a) for a in aad_trialed)}) — ablation is Class I indication"
        )
    elif truthy(data.get("aadIntolerant")):
        score += 15
        key_findings.append("AAD intolerance — ablation reasonable as alternative rhythm control strategy")
    else:
        key_findings.append(
            "No prior AAD trial — ablation may be considered as first-line per 2023 ACC/AHA guidelines (Class IIa for paroxysmal AF)"
        )
        score += 5

    # LA size
    if la_size > 55:
        warnings.append(
            f"Markedly enlarged LA ({_fmt_num(la_size)} mm) — significantly reduced ablation success; consider rate control"
        )
        score -= 15
    elif la_size > 45:
        warnings.append(f"Enlarged LA ({_fmt_num(la_size)} mm) — reduced success rates; discuss expectations")
        score -= 5
    else:
        key_findings.append(f"LA size {_fmt_num(la_size)} mm — favorable anatomy for ablation")
        score += 5

    # LVEF
    if lvef < 35:
        key_findings.append(
            f"Reduced LVEF ({_fmt_num(lvef)}%) — tachycardia-mediated cardiomyopathy possible; ablation may improve EF (CASTLE-AF)"
        )
        score += 10

    # HCM
    if truthy(data.get("hcm")):
        key_findings.append("HCM with AF — ablation reasonable; higher recurrence rates; specialized center recommended")

    # Modifiable risk factors
    if truthy(data.get("sleepApnea")) and not truthy(data.get("sleepApneaTreated")):
        warnings.append("Untreated obstructive sleep apnea — treat OSA before ablation to reduce recurrence risk")
        score -= 5
    if truthy(data.get("obesity")) and bmi >= 35:
        warnings.append(
            f"BMI {_fmt_num(bmi)} — weight loss to BMI <30 significantly improves ablation outcomes (LEGACY trial)"
        )
        score -= 5
    if truthy(data.get("thyroidDisease")) and not truthy(data.get("thyroidTreated")):
        warnings.append("Untreated thyroid disease — correct thyroid function before ablation")
        score -= 10

    # Anticoagulation
    if not truthy(data.get("onAnticoagulation")) and cha2ds2vasc_score >= 2:
        warnings.append(
            f"CHA₂DS₂-VASc score {cha2ds2vasc_score} — anticoagulation required; start before ablation"
        )

    score = max(0, min(100, score))

    if score >= 65:
        recommendation = "Strongly Recommended"
        guideline_class = "Class I: Catheter ablation is recommended"
        preferred_approach = (
            "Pulmonary vein isolation (PVI) — radiofrequency or cryoablation; continue anticoagulation peri-procedurally"
        )
    elif score >= 45:
        recommendation = "Recommended"
        guideline_class = "Class IIa: Catheter ablation is reasonable"
        preferred_approach = "PVI with electrophysiology consultation; optimize modifiable risk factors pre-procedure"
    elif score >= 25:
        recommendation = "Reasonable"
        guideline_class = "Class IIb: Catheter ablation may be considered"
        preferred_approach = (
            "Shared decision-making; address modifiable risk factors; consider rate control if ablation risks outweigh benefits"
        )
    else:
        recommendation = "Not Recommended"
        guideline_class = "Class III: Ablation not recommended in current clinical context"
        preferred_approach = "Rate control strategy; optimize anticoagulation; reassess in 6–12 months"

    if cha2ds2vasc_score >= 2:
        anticoagulation_note = (
            f"CHA₂DS₂-VASc {cha2ds2vasc_score} — long-term anticoagulation recommended regardless of ablation outcome (Class I)"
        )
    elif cha2ds2vasc_score == 1 and data.get("sex") != "female":
        anticoagulation_note = (
            f"CHA₂DS₂-VASc {cha2ds2vasc_score} — anticoagulation may be considered (Class IIb)"
        )
    else:
        anticoagulation_note = (
            f"CHA₂DS₂-VASc {cha2ds2vasc_score} — anticoagulation not routinely recommended; reassess annually"
        )

    return {
        "candidacyScore": score,
        "cha2ds2vascScore": cha2ds2vasc_score,
        "recommendation": recommendation,
        "guidelineClass": guideline_class,
        "preferredApproach": preferred_approach,
        "keyFindings": key_findings,
        "warnings": warnings,
        "anticoagulationNote": anticoagulation_note,
        "references": list(_REFERENCES),
    }
