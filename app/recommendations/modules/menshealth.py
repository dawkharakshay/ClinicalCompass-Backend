"""Men's Health: Prostatic Artery Embolization (PAE) candidacy.

Ported 1:1 from old_static_code/client/src/lib/mensHealthLogic.ts
(computePAEScore). Based on SIR guidelines and peer-reviewed literature.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "menshealth"


def assess(data: dict) -> dict:
    ipss_score = num(data.get("ipssScore"), 0)
    ipss_qol = num(data.get("ipssQol"), 0)

    failed_medical_therapy = truthy(data.get("failedMedicalTherapy"))
    symptom_duration_over6 = truthy(data.get("symptomDurationOver6Months"))
    no_prostate_cancer = truthy(data.get("noProstateCancer"))
    prostate_volume_over40 = truthy(data.get("prostateVolumeOver40"))
    urinary_retention_history = truthy(data.get("urinaryRetentionHistory"))
    mri_performed = truthy(data.get("mriPerformed"))
    cta_performed = truthy(data.get("ctaPerformed"))
    no_active_uti = truthy(data.get("noActiveUTI"))
    no_coagulopathy = truthy(data.get("noCoagulopathy"))

    score = 0
    criteria_met: list[bool] = []

    # IPSS scoring (max 20)
    if ipss_score >= 20:
        score += 20
        criteria_met.append(True)
    elif ipss_score >= 13:
        score += 15
        criteria_met.append(True)
    elif ipss_score >= 8:
        score += 8
        criteria_met.append(True)
    else:
        score += 3
        criteria_met.append(False)

    # IPSS QoL (max 10)
    if ipss_qol >= 4:
        score += 10
        criteria_met.append(True)
    elif ipss_qol >= 3:
        score += 6
        criteria_met.append(True)
    else:
        score += 2
        criteria_met.append(False)

    # Prostate volume (max 15)
    if prostate_volume_over40:
        score += 15
        criteria_met.append(True)
    else:
        criteria_met.append(False)

    # Mandatory criteria (10 pts each = 30 total)
    mandatory_criteria = [
        failed_medical_therapy,
        symptom_duration_over6,
        no_prostate_cancer,
    ]
    for met in mandatory_criteria:
        if met:
            score += 10
        criteria_met.append(met)

    # Bonus criteria (5 pts each, max 15)
    if urinary_retention_history:
        score += 5
    if mri_performed or cta_performed:
        score += 5
    if no_active_uti and no_coagulopathy:
        score += 5

    criteria_met_count = sum(1 for m in criteria_met if m)
    criteria_total_count = len(criteria_met)

    # Hard disqualifiers
    if not no_prostate_cancer:
        return {
            "score": min(score, 20),
            "label": "Not Indicated",
            "color": "destructive",
            "summary": (
                "Active prostate malignancy is an absolute contraindication. "
                "PAE is not indicated until malignancy is ruled out or treated."
            ),
            "criteriaMetCount": criteria_met_count,
            "criteriaTotalCount": criteria_total_count,
        }

    if not no_active_uti:
        return {
            "score": min(score, 25),
            "label": "Not Indicated",
            "color": "destructive",
            "summary": (
                "Active urinary tract infection must be treated before PAE can be considered."
            ),
            "criteriaMetCount": criteria_met_count,
            "criteriaTotalCount": criteria_total_count,
        }

    if score >= 75:
        return {
            "score": min(score, 100),
            "label": "Strong Candidate",
            "color": "primary",
            "summary": (
                "Patient demonstrates significant LUTS with adequate prostate volume "
                "and failed medical therapy. Optimal profile for prostatic artery embolization."
            ),
            "criteriaMetCount": criteria_met_count,
            "criteriaTotalCount": criteria_total_count,
        }

    if score >= 50:
        return {
            "score": score,
            "label": "Moderate Candidate",
            "color": "warning",
            "summary": (
                "Patient may benefit from PAE but incomplete criteria met. "
                "Consider multidisciplinary review with urology before proceeding."
            ),
            "criteriaMetCount": criteria_met_count,
            "criteriaTotalCount": criteria_total_count,
        }

    return {
        "score": score,
        "label": "Weak Candidate",
        "color": "destructive",
        "summary": (
            "Insufficient evidence to support PAE candidacy. "
            "Consider further medical optimization or alternative interventions."
        ),
        "criteriaMetCount": criteria_met_count,
        "criteriaTotalCount": criteria_total_count,
    }
