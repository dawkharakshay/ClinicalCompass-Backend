"""Bone Cancer Interventional Oncology Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/boneCancerLogic.ts
(assessBoneCancerCandidacy).

Based on NCCN 2026 Guidelines — Principles of Interventional Oncology (BONE-E)
and Society of Interventional Oncology (SIO) principles.

The legacy entry point takes four separate objects (PatientData, TumorData,
ProcedureConsiderations, ContraindicationScreening). The form submits the union
of those interface field names as a single flat object, so this port reads each
field directly from ``data``.
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num, truthy

LOGIC_KEY = "bonecancer"

# Static reference list surfaced as the card's "Supporting Guidelines & Evidence"
# section (auto-attached by app.recommendations.registry.get_evidence). Ported 1:1
# from the inline `references={[...]}` array in
# old_static_code/client/src/pages/BoneCancerCompass.tsx.
EVIDENCE = [
    {
        "title": "NCCN Clinical Practice Guidelines in Oncology: Bone Cancer (Version 2.2026)",
        "source": "National Comprehensive Cancer Network",
        "description": "NCCN Guidelines. Available at: nccn.org. Updated 2026.",
        "pmid": None,
    },
    {
        "title": "ESMO Clinical Practice Guidelines: Bone Sarcomas",
        "source": "Casali PG, Bielack S, Abecassis N, et al.",
        "description": "Ann Oncol. 2018;29(Suppl 4):iv79–iv95. PMID: 29771315",
        "pmid": "29771315",
    },
    {
        "title": "SIR Reporting Standards for the Treatment of Bone Tumors With Percutaneous Ablation",
        "source": "Tomasian A, Jennings JW",
        "description": "J Vasc Interv Radiol. 2021;32(8):1184–1193. PMID: 34175246",
        "pmid": "34175246",
    },
    {
        "title": "Percutaneous Ablation of Bone Tumors: Systematic Review and Meta-Analysis",
        "source": "Deschamps F, de Baere T, Hakime A, et al.",
        "description": "Cardiovasc Intervent Radiol. 2016;39(10):1385–1394. PMID: 27339483",
        "pmid": "27339483",
    },
]


def assess(data: dict) -> dict:
    score = 100
    key_considerations: list[str] = []
    contraindications_list: list[str] = []
    warnings: list[str] = []
    candidacy_label = "excellent"
    recommended_modalities: list[str] = []
    expected_technical_success = 95
    expected_local_control = 85
    expected_pain_relief = 75
    expected_complication = 5

    # Local mirror of the mutable ProcedureConsiderations fields the TS reassigns.
    proposed_ablation_modality = data.get("proposedAblationModality")
    proposed_embolization_type = data.get("proposedEmbolizationType")
    treatment_goal = data.get("treatmentGoal")
    thermal_protection_needed = truthy(data.get("thermalProtectionNeeded"))

    tumor_type = data.get("tumorType")
    resectability_status = data.get("resectabilityStatus")
    location = data.get("location")
    size_in_cm = num(data.get("sizeInCm"), 0)
    is_painful = truthy(data.get("isPainful"))
    pain_severity = data.get("painSeverity")
    has_vascular_involvement = truthy(data.get("hasVascularInvolvement"))
    prior_treatments = data.get("priorTreatments") or []

    performance_status = data.get("performanceStatus")
    has_coagulopathy = truthy(data.get("hasCoagulopathy"))
    coagulopathy_correctible = truthy(data.get("coagulopathyCorrectible"))
    active_infection = truthy(data.get("activeInfection"))

    combination_therapy = data.get("combinationTherapy") or []

    # ── ABSOLUTE CONTRAINDICATIONS ──────────────────────────────────────────
    if truthy(data.get("uncorrectableCoagulopathy")):
        contraindications_list.append(
            "Uncorrectable coagulopathy (absolute contraindication)"
        )
        score = 0
        candidacy_label = "contraindicated"

    if truthy(data.get("activeInfectionInArea")):
        contraindications_list.append(
            "Active infection in planned treatment area (absolute contraindication)"
        )
        score = 0
        candidacy_label = "contraindicated"

    if truthy(data.get("unprotectableCriticalStructures")):
        contraindications_list.append(
            "Inability to displace or protect adjacent critical structures (relative contraindication)"
        )
        score -= 25
        warnings.append(
            "Requires detailed risk-benefit discussion and advanced thermal protection strategies"
        )

    # ── TUMOR CHARACTERISTICS ASSESSMENT ────────────────────────────────────
    if tumor_type == "osteosarcoma":
        key_considerations.append(
            "Osteosarcoma: RFA is standard for relapsed/refractory disease; cryoablation is safe alternative"
        )
        recommended_modalities.extend(["rfa", "cryoablation"])
        expected_local_control = 85
    elif tumor_type == "chondrosarcoma":
        key_considerations.append(
            "Chondrosarcoma: Ablation is treatment option for recurrent disease"
        )
        recommended_modalities.extend(["rfa", "cryoablation"])
        expected_local_control = 80
    elif tumor_type == "gctb":
        key_considerations.append(
            "Giant Cell Tumor of Bone (GCTB): Cryoablation has excellent local control (recurrence 2.3%); consider serial embolization with denosumab for large/sacropelvic lesions"
        )
        recommended_modalities.append("cryoablation")
        if proposed_embolization_type == "serial":
            recommended_modalities.append("rfa")
        expected_local_control = 97.7  # 2.3% recurrence rate
    elif tumor_type == "abc":
        key_considerations.append(
            "Aneurysmal Bone Cyst (ABC): Serial arterial embolization is effective primary treatment, especially for surgically inaccessible locations (spine, pelvis); healing rates 58-83%"
        )
        recommended_modalities.append("rfa")
        proposed_embolization_type = "serial"
        expected_local_control = 70
    elif tumor_type == "bone-metastases":
        key_considerations.append(
            "Bone Metastases: RFA is standard treatment (SPARTA study: 100% technical success); excellent for pain palliation (60-80% pain control)"
        )
        recommended_modalities.extend(["rfa", "mwa"])
        if is_painful:
            expected_pain_relief = 75
        expected_local_control = 85
    elif tumor_type == "chordoma":
        key_considerations.append(
            "Chordoma: Ablation is treatment option for recurrent disease"
        )
        recommended_modalities.extend(["rfa", "cryoablation"])
        expected_local_control = 80
    else:
        recommended_modalities.extend(["rfa", "mwa", "cryoablation"])

    # Resectability assessment
    if resectability_status == "unresectable":
        key_considerations.append(
            "Unresectable tumor: Image-guided ablation is appropriate treatment option"
        )
        score += 15
    elif resectability_status == "relapsed-refractory":
        key_considerations.append(
            "Relapsed/refractory disease: Ablation is indicated when excision is not possible"
        )
        score += 10
    elif resectability_status == "resectable":
        if treatment_goal == "preoperative":
            key_considerations.append(
                "Preoperative embolization: Reduces intraoperative blood loss and facilitates tumor resection (perform 24-48 hours prior to surgery)"
            )
            proposed_embolization_type = "preoperative"

    # Tumor location considerations
    if location == "spine" or location == "pelvis":
        key_considerations.append(
            "Spine/Pelvis location: Anatomically challenging; embolization particularly beneficial to reduce blood loss; thermal protection critical"
        )
        thermal_protection_needed = True
        score += 5

    # Size assessment
    if size_in_cm > 5:
        warnings.append(
            "Large tumor (>5 cm): May require staged ablation or combination approach"
        )
        score -= 10

    # Pain assessment
    if is_painful and truthy(pain_severity) and num(pain_severity, 0) >= 7:
        key_considerations.append(
            "Severe pain: Palliative ablation can achieve pain control in 60-80% of patients with rapid response (median 1-2 days)"
        )
        treatment_goal = "palliative"
        score += 10

    # Vascular involvement
    if has_vascular_involvement:
        key_considerations.append(
            "Hypervascular tumor: Preoperative embolization reduces blood loss"
        )
        proposed_embolization_type = "preoperative"
        score += 5

    # Prior treatments
    if includes(prior_treatments, "chemotherapy") and includes(
        prior_treatments, "radiation"
    ):
        key_considerations.append(
            "Disease progression despite conventional therapies: Candidate for interventional oncology approach"
        )
        score += 5

    # ── PATIENT FACTORS ASSESSMENT ──────────────────────────────────────────
    if performance_status == "3" or performance_status == "4":
        warnings.append(
            "Poor performance status: Multidisciplinary team discussion strongly recommended"
        )
        score -= 15

    if has_coagulopathy and not coagulopathy_correctible:
        contraindications_list.append("Uncorrectable coagulopathy")
        score = 0
        candidacy_label = "contraindicated"

    if active_infection:
        contraindications_list.append("Active infection")
        score = 0
        candidacy_label = "contraindicated"

    # ── PROCEDURE-SPECIFIC CONSIDERATIONS ───────────────────────────────────
    if includes(combination_therapy, "augmentation"):
        key_considerations.append(
            "Combination ablation + cement augmentation/osteoplasty: Recommended for osseous destruction or increased fracture risk, especially weight-bearing bones"
        )

    if includes(combination_therapy, "radiation"):
        key_considerations.append(
            "Ablation + radiation therapy: May produce faster and longer-lasting pain relief than radiation alone"
        )

    if thermal_protection_needed:
        key_considerations.append(
            "Thermal protection strategies required: Hydrodissection, pneumodissection, temperature monitoring to minimize risk of thermal injury to adjacent structures"
        )

    # ── MODALITY-SPECIFIC OUTCOMES ──────────────────────────────────────────
    if proposed_ablation_modality == "cryoablation":
        expected_complication = 2.5
        key_considerations.append(
            "Cryoablation complication rate: ~2.5% (secondary fracture most common)"
        )

    if proposed_ablation_modality == "rfa":
        key_considerations.append(
            "RFA: Standard treatment for osteoid osteoma and bone metastases; higher technical success and lower morbidity compared to open surgery"
        )

    if proposed_embolization_type == "serial":
        expected_local_control = 75
        key_considerations.append(
            "Serial embolization: Preferred approach for GCTB, especially when combined with denosumab for synergistic sclerosis and pain reduction"
        )

    if proposed_embolization_type == "preoperative":
        key_considerations.append(
            "Preoperative embolization: Ideally performed 24-48 hours prior to surgery; reduces intraoperative blood loss and facilitates tumor resection"
        )

    if proposed_embolization_type == "palliative":
        expected_pain_relief = 70
        key_considerations.append(
            "Palliative embolization: Achieves pain control in 60-80% of patients with painful bone metastases; median response time 1-2 days"
        )

    # ── FINAL SCORE NORMALIZATION & LABEL ASSIGNMENT ────────────────────────
    score = max(0, min(100, score))

    if candidacy_label != "contraindicated":
        if score >= 85:
            candidacy_label = "excellent"
        elif score >= 70:
            candidacy_label = "good"
        elif score >= 50:
            candidacy_label = "fair"
        else:
            candidacy_label = "poor"

    return {
        "candidacyScore": score,
        "candidacyLabel": candidacy_label,
        "recommendedModalities": recommended_modalities
        if len(recommended_modalities) > 0
        else ["rfa"],
        "recommendedApproach": proposed_embolization_type,
        "expectedOutcomes": {
            "technicalSuccessRate": expected_technical_success,
            "localControlRate": expected_local_control,
            "painReliefRate": expected_pain_relief if is_painful else None,
            "complicationRate": expected_complication,
        },
        "keyConsiderations": key_considerations,
        "contraindications": contraindications_list,
        "warnings": warnings,
    }
