"""Cholecystectomy Clinical Compass — candidacy scoring.

Ported 1:1 from old_static_code/client/src/lib/cholecystectomyLogic.ts
(calculateCholecystectomyScore).

Based on: SAGES Clinical Spotlight Review — Cholecystectomy (2022);
2020 WSES Tokyo Guidelines; ACS NSQIP Best Practices.
"""

from __future__ import annotations

from app.recommendations.jslib import intnum, parse_float, truthy

LOGIC_KEY = "cholecystectomy"

_REFERENCES = [
    "Yokoe M, et al. Tokyo Guidelines 2018: Diagnostic Criteria and Severity Grading of Acute Cholecystitis. J Hepatobiliary Pancreat Sci. 2018;25(1):41-54. PMID: 29032636",
    "SAGES Clinical Spotlight Review: Cholecystectomy. 2022 — Laparoscopic cholecystectomy is the gold standard for symptomatic cholelithiasis and acute cholecystitis",
    "Gurusamy KS, et al. Early vs Delayed Laparoscopic Cholecystectomy for Acute Cholecystitis. Cochrane Database Syst Rev. 2013;6:CD005440. PMID: 23813477 — Early surgery reduces complications and hospital stay",
    "Stinton LM, Shaffer EA. Epidemiology of Gallbladder Disease: Cholelithiasis and Cancer. Gut Liver. 2012;6(2):172-187. PMID: 22570746",
]


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0
    urgency = "Elective"

    indication = data.get("indication")
    frequency = data.get("frequency")
    pain_duration = parse_float(data.get("painDuration"))
    ejection_fraction = parse_float(data.get("ejectionFraction"))
    polyp_size = parse_float(data.get("polypSize"))
    asa = intnum(data.get("asa"), 0)
    pregnancy_trimester = intnum(data.get("pregnancyTrimester"), 0)

    # Acute cholecystitis — urgent/semi-urgent
    if truthy(data.get("acuteCholecystitis")):
        score += 40
        urgency = "Semi-urgent (within 6 weeks)"
        key_findings.append(
            "Acute cholecystitis — early laparoscopic cholecystectomy within 72 hours is preferred per Tokyo Guidelines 2020"
        )
        if truthy(data.get("cholangitis")):
            urgency = "Urgent (within 72 hours)"
            warnings.append(
                "Acute cholangitis — biliary drainage required urgently; cholecystectomy after stabilization"
            )

    # Gallstone pancreatitis — urgent
    if truthy(data.get("gallstonePancreatitis")):
        score += 40
        urgency = "Semi-urgent (within 6 weeks)"
        key_findings.append(
            "Gallstone pancreatitis — cholecystectomy during same admission (mild pancreatitis) or after resolution (severe) per SAGES guidelines"
        )

    # Symptomatic cholelithiasis
    if truthy(data.get("biliaryColic")) and truthy(data.get("gallstonesPresent")):
        score += 30
        key_findings.append(
            "Symptomatic cholelithiasis with confirmed gallstones — standard indication for elective cholecystectomy"
        )

    # Symptom frequency
    if frequency == "daily":
        score += 15
        key_findings.append("Daily biliary colic — high symptom burden")
    elif frequency == "weekly":
        score += 10
    elif frequency == "monthly":
        score += 5

    # Duration
    if pain_duration >= 3:
        score += 10
        key_findings.append(
            f"{_fmt(pain_duration)} months of symptomatic cholelithiasis — conservative treatment not effective"
        )

    # Biliary dyskinesia
    if indication == "biliary-dyskinesia" and ejection_fraction < 35:
        score += 25
        key_findings.append(
            f"HIDA scan ejection fraction {_fmt(ejection_fraction)}% — biliary dyskinesia; cholecystectomy indicated per SAGES guidelines"
        )

    # Gallbladder polyp
    if indication == "polyp":
        if polyp_size >= 10:
            score += 35
            key_findings.append(
                "Gallbladder polyp ≥10mm — cholecystectomy indicated due to malignancy risk"
            )
        elif polyp_size >= 6:
            score += 15
            key_findings.append(
                f"Gallbladder polyp {_fmt(polyp_size)}mm — surveillance vs cholecystectomy; consider surgery if symptomatic or risk factors"
            )

    # Choledocholithiasis
    if truthy(data.get("choledocholithiasis")):
        score += 20
        key_findings.append(
            "Choledocholithiasis — ERCP + cholecystectomy; laparoscopic common bile duct exploration if ERCP unavailable"
        )

    # Imaging findings
    if truthy(data.get("wallThickening")):
        score += 10
        key_findings.append(
            "Gallbladder wall thickening — increased urgency; consider malignancy workup"
        )

    # Conservative treatment
    if truthy(data.get("triedDietModification")):
        score += 5

    # Surgical risk
    if asa >= 4:
        warnings.append(
            "ASA Class IV — high surgical risk; multidisciplinary risk assessment required; percutaneous cholecystostomy may be preferred for acute cholecystitis"
        )
        score -= 15
    elif asa == 3:
        warnings.append(
            "ASA Class III — moderate surgical risk; optimize medical comorbidities pre-operatively"
        )

    if truthy(data.get("cirrhosis")):
        warnings.append(
            "Cirrhosis — significantly increased surgical risk; hepatology consultation required; Child-Pugh score should guide decision"
        )
        score -= 10

    if truthy(data.get("pregnancy")):
        if pregnancy_trimester == 2:
            key_findings.append(
                "Pregnancy (2nd trimester) — laparoscopic cholecystectomy safest in 2nd trimester if surgery required"
            )
        elif pregnancy_trimester == 3:
            warnings.append(
                "3rd trimester pregnancy — increased surgical risk; conservative management preferred unless emergent"
            )

    if truthy(data.get("mirizzySyndrome")):
        warnings.append(
            "Mirizzi syndrome — complex anatomy; experienced hepatobiliary surgeon recommended; open conversion may be required"
        )

    score = max(0, min(100, score))

    if score >= 60:
        recommendation = "Strongly Indicated"
        if truthy(data.get("cirrhosis")) or truthy(data.get("mirizzySyndrome")):
            approach = "Laparoscopic cholecystectomy — experienced hepatobiliary surgeon; open conversion may be required"
        else:
            approach = "Laparoscopic cholecystectomy — standard approach; single-incision laparoscopic (SILC) or robotic if available"
    elif score >= 35:
        recommendation = "Indicated"
        approach = "Laparoscopic cholecystectomy — elective; optimize medical comorbidities pre-operatively"
    elif score >= 15:
        recommendation = "Consider"
        approach = "Surgical consultation; complete workup; consider conservative management vs elective cholecystectomy"
    else:
        recommendation = "Not Indicated"
        approach = "Conservative management; dietary modification; reassess in 3–6 months"

    return {
        "candidacyScore": score,
        "recommendation": recommendation,
        "urgency": urgency,
        "approach": approach,
        "keyFindings": key_findings,
        "warnings": warnings,
        "references": list(_REFERENCES),
    }


def _fmt(x: float) -> str:
    """Render a number the way JS string interpolation would (no trailing .0)."""
    if x == int(x):
        return str(int(x))
    return repr(x)
