"""Hernia Repair Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/herniaLogic.ts
(calculateHerniaScore).
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "hernia"

_REFERENCES = [
    "HerniaSurge Group. International Guidelines for Groin Hernia Management. Hernia. 2018;22(1):1-165. PMID: 29330835 — Comprehensive evidence-based guidelines for inguinal hernia management",
    "Simons MP, et al. European Hernia Society Guidelines on the Treatment of Inguinal Hernia in Adult Patients. Hernia. 2009;13(4):343-403. PMID: 19636493",
    "Fitzgibbons RJ, et al. Watchful Waiting vs Repair of Inguinal Hernia in Minimally Symptomatic Men. JAMA. 2006;295(3):285-292. PMID: 16418463 — Watchful waiting safe for asymptomatic/minimally symptomatic inguinal hernias",
    "Bittner R, et al. EAES Guidelines for Laparoscopic Treatment of Ventral and Incisional Abdominal Wall Hernias. Surg Endosc. 2019;33(12):3933-3985. PMID: 31250199",
]


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0.0
    urgency = "Elective"

    strangulated = truthy(data.get("strangulated"))
    incarcerated = truthy(data.get("incarcerated"))
    symptomatic = truthy(data.get("symptomatic"))
    hernia_type = data.get("herniaType")
    sex = data.get("sex")
    pain_level = num(data.get("painLevel"), 0)
    defect_size = num(data.get("defectSize"), 0)
    duration_months = num(data.get("durationMonths"), 0)
    bmi = num(data.get("bmi"), 0)
    asa = num(data.get("asa"), 0)

    # Emergent — strangulation or incarceration
    if strangulated:
        score = 100.0
        urgency = "Emergent"
        warnings.append(
            "EMERGENT: Strangulated hernia — immediate surgical intervention required; bowel ischemia risk"
        )
        key_findings.append("Strangulated hernia — emergency surgery")
    elif incarcerated:
        score += 50
        urgency = "Semi-urgent"
        warnings.append(
            "Incarcerated hernia — urgent surgical evaluation; manual reduction may be attempted; if unsuccessful, urgent surgery required"
        )
        key_findings.append("Incarcerated hernia — semi-urgent repair")

    # Symptomatic hernia
    if symptomatic:
        score += 30
        key_findings.append(
            "Symptomatic hernia — surgery indicated per HerniaSurge Guidelines 2018"
        )

    # Pain level
    if pain_level >= 7:
        score += 15
        key_findings.append(f"Pain level {_fmt(pain_level)}/10 — significant symptom burden")
    elif pain_level >= 4:
        score += 8
    elif pain_level >= 1:
        score += 3

    # Hernia type specific
    if hernia_type == "femoral":
        score += 20
        key_findings.append(
            "Femoral hernia — high incarceration/strangulation risk; elective repair strongly recommended regardless of symptoms"
        )
    if hernia_type == "inguinal" and sex == "female":
        score += 10
        key_findings.append(
            "Inguinal hernia in female — higher proportion of femoral hernias; careful anatomic evaluation required"
        )

    # Defect size
    if defect_size >= 4:
        score += 10
        key_findings.append(
            f"Defect size {_fmt(defect_size)}cm — large hernia; mesh repair strongly recommended"
        )
    elif defect_size >= 2:
        score += 5

    # Worsening symptoms
    if truthy(data.get("worseningSymptoms")):
        score += 10
        key_findings.append("Worsening symptoms — progressive hernia; repair recommended")

    # Duration
    if duration_months >= 12:
        score += 5
        key_findings.append(
            f"{_fmt(duration_months)} months of symptomatic hernia — conservative management not effective"
        )

    # Recurrent hernia
    if truthy(data.get("recurrent")):
        score += 10
        key_findings.append(
            "Recurrent hernia — mesh repair required; consider laparoscopic approach (TEP/TAPP) or open preperitoneal repair"
        )
        warnings.append(
            "Recurrent hernia — higher complexity; experienced hernia surgeon recommended"
        )

    # Risk factors
    obesity = truthy(data.get("obesity"))
    if obesity and bmi >= 40:
        warnings.append(
            f"BMI {_fmt(bmi)} — morbid obesity significantly increases surgical risk and recurrence; consider weight loss pre-operatively"
        )
        score -= 10
    elif obesity:
        warnings.append(
            f"Obesity (BMI {_fmt(bmi)}) — increased surgical risk and recurrence rate; optimize weight pre-operatively"
        )

    if truthy(data.get("smoking")):
        warnings.append(
            "Active smoking — significantly increases wound complications and recurrence; smoking cessation ≥4 weeks pre-operatively recommended"
        )

    if truthy(data.get("diabetes")):
        warnings.append(
            "Diabetes — increased wound infection risk; optimize glycemic control pre-operatively (HbA1c <8%)"
        )

    if truthy(data.get("ascites")):
        warnings.append(
            "Ascites — hernia repair contraindicated until ascites controlled; high recurrence and wound complication risk"
        )
        score -= 20

    if asa >= 4:
        warnings.append(
            "ASA Class IV — very high surgical risk; risk-benefit discussion required; watchful waiting may be preferred"
        )
        score -= 20

    # Watchful waiting — asymptomatic inguinal hernia
    if not symptomatic and hernia_type == "inguinal" and pain_level == 0:
        key_findings.append(
            "Asymptomatic inguinal hernia — watchful waiting is safe per HerniaSurge Guidelines; 30% will develop symptoms requiring surgery within 5 years"
        )

    score = max(0, min(100, score))

    if strangulated or incarcerated:
        recommendation = "Strongly Indicated"
        approach = (
            "Emergency open or laparoscopic repair — bowel viability assessment required"
            if strangulated
            else "Urgent laparoscopic or open repair — TEP/TAPP or open inguinal repair"
        )
        mesh_recommendation = (
            "Mesh use in contaminated field — use biologic or biosynthetic mesh if bowel resection performed"
        )
    elif score >= 55:
        recommendation = "Strongly Indicated"
        if hernia_type == "inguinal":
            approach = "Laparoscopic repair (TEP or TAPP) preferred for bilateral or recurrent; open Lichtenstein acceptable for unilateral primary"
        elif hernia_type == "incisional" or hernia_type == "ventral":
            approach = "Laparoscopic IPOM or open component separation — mesh required for defects >2cm"
        else:
            approach = "Laparoscopic or open repair per anatomy and surgeon experience"
        mesh_recommendation = (
            "Mesh repair strongly recommended — reduces recurrence from 15–20% to <5%"
            if defect_size >= 2
            else "Mesh repair recommended; primary repair acceptable for small defects (<1cm) in low-risk patients"
        )
    elif score >= 30:
        recommendation = "Indicated"
        approach = "Elective laparoscopic or open repair; optimize modifiable risk factors pre-operatively"
        mesh_recommendation = "Mesh repair recommended per hernia size and type"
    elif score >= 10:
        recommendation = "Watchful Waiting Acceptable"
        approach = "Watchful waiting is safe for asymptomatic inguinal hernias; patient education on warning signs of incarceration"
        mesh_recommendation = "Mesh repair if surgery elected"
    else:
        recommendation = "Not Recommended"
        approach = "Conservative management; address contraindications; reassess in 3–6 months"
        mesh_recommendation = "N/A"

    return {
        "candidacyScore": _as_number(score),
        "recommendation": recommendation,
        "urgency": urgency,
        "approach": approach,
        "meshRecommendation": mesh_recommendation,
        "keyFindings": key_findings,
        "warnings": warnings,
        "references": list(_REFERENCES),
    }


def _as_number(x: float) -> float | int:
    """Mirror JS number semantics: integral values render without a decimal."""
    return int(x) if float(x).is_integer() else x


def _fmt(x: float) -> str:
    """Format a number the way JS string interpolation would (no trailing .0)."""
    return str(int(x)) if float(x).is_integer() else str(x)
