"""Brain Metastases Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/brainMetastasesLogic.ts
(assessBrainMetastases).

Based on CNS 2025 / ASCO-SNO-ASTRO 2022 / NCCN brain metastases guidelines.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "brainmetastases"


def _get_brain_mets_references() -> list[dict]:
    return [
        {
            "citation": "Huntoon K et al. CNS Systematic Review and Evidence-Based Guidelines for Emerging Therapies for Adults with Metastatic Brain Tumors. Neurosurgery. 2025.",
            "pmid": "35417433",
        },
        {
            "citation": "Vogelbaum MA et al. Treatment for Brain Metastases: ASCO-SNO-ASTRO Guideline. J Clin Oncol. 2022;40(5):492-516.",
            "pmid": "34936423",
        },
        {
            "citation": "Ramos A et al. Brain Metastases: An Overview of Current Management. Neuro Oncol. 2022.",
            "pmid": "36523687",
        },
        {
            "citation": "Brown PD et al. Postoperative Stereotactic Radiosurgery Compared with Whole Brain Radiotherapy for Resected Metastatic Brain Disease (NCCTG N107C/CEC.3). Lancet Oncol. 2017;18(8):1049-1060.",
            "pmid": "28687387",
        },
        {
            "citation": "Soria JC et al. Osimertinib in Untreated EGFR-Mutated Advanced Non-Small-Cell Lung Cancer (FLAURA). N Engl J Med. 2018;378(2):113-125.",
            "pmid": "29151359",
        },
        {
            "citation": "Peters S et al. Alectinib versus Crizotinib in Untreated ALK-Positive Non-Small-Cell Lung Cancer (ALEX). N Engl J Med. 2017;377(9):829-838.",
            "pmid": "28586279",
        },
        {
            "citation": "Long GV et al. Dabrafenib plus Trametinib versus Dabrafenib Monotherapy in Patients with Metastatic BRAF V600E/K-Mutant Melanoma. Lancet Oncol. 2015;16(8):954-963.",
            "pmid": "26115796",
        },
    ]


def _build_systemic_plus_local_recommendation(
    data: dict,
    title: str,
    rationale: str,
    evidence_level: str,
    urgent_flags: list[str],
    warnings: list[str],
    local_therapy_options: list[str],
    systemic_therapy_options: list[str],
    surgical_considerations: list[str],
    monitoring_plan: list[str],
) -> dict:
    metastasis_count = data.get("metastasisCount")
    local_options = list(local_therapy_options)
    if metastasis_count == "single" or metastasis_count == "limited":
        local_options.append(
            "SRS to limited metastases: Consider in addition to systemic therapy for durable local control."
        )
    if truthy(data.get("symptomatic")) and truthy(data.get("massEffect")):
        local_options.append(
            "Urgent local therapy (SRS or surgery) for symptomatic lesions regardless of systemic therapy status."
        )

    return {
        "primaryRecommendation": "srs_plus_systemic",
        "recommendationTitle": title,
        "rationale": rationale,
        "evidenceLevel": evidence_level,
        "guidelineSource": "CNS 2025 Brain Metastases Guidelines (Huntoon K et al., Neurosurgery 2025; PMID 35417433)",
        "localTherapyOptions": local_options,
        "systemicTherapyOptions": systemic_therapy_options,
        "surgicalConsiderations": surgical_considerations,
        "monitoringPlan": [
            "MRI brain at 6–8 weeks after initiating systemic therapy",
            "MRI brain every 2–3 months",
            "Systemic staging CT every 3 months",
        ],
        "urgentFlags": urgent_flags,
        "warnings": [
            *warnings,
            "Immunotherapy + SRS: Combination may increase radiation necrosis risk — timing and sequencing require multidisciplinary coordination.",
        ],
        "nextSteps": [
            "Medical oncology consultation for systemic therapy initiation",
            "Radiation oncology consultation for SRS planning",
            "Molecular profiling confirmation",
            "MRI brain with gadolinium (thin-cut) for treatment planning",
            "Multidisciplinary tumor board review",
        ],
        "references": _get_brain_mets_references(),
    }


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    warnings: list[str] = []
    local_therapy_options: list[str] = []
    systemic_therapy_options: list[str] = []
    surgical_considerations: list[str] = []
    monitoring_plan: list[str] = []

    primary_histology = data.get("primaryHistology")
    metastasis_count = data.get("metastasisCount")
    largest_lesion_cm = num(data.get("largestLesionCm"), 0)

    # ── Urgent flags ──────────────────────────────────────────────────────────
    if truthy(data.get("leptomeningealDisease")):
        urgent_flags.append(
            "Leptomeningeal disease (LMD): Systemic and intrathecal therapy considerations. Prognosis significantly worse. Urgent multidisciplinary oncology review."
        )
    if truthy(data.get("massEffect")) and truthy(data.get("symptomatic")):
        urgent_flags.append(
            "Symptomatic mass effect: Consider urgent corticosteroids (dexamethasone 4–16 mg/day) and expedited neurosurgical evaluation."
        )
    if truthy(data.get("neurologicDeficit")) and truthy(data.get("massEffect")):
        urgent_flags.append(
            "Progressive neurologic deficit with mass effect: Urgent surgical evaluation for decompression."
        )

    # ── Poor performance status — best supportive care ────────────────────────
    if data.get("kpsScore") == "low":
        return {
            "primaryRecommendation": "best_supportive_care",
            "recommendationTitle": "Best Supportive Care / Palliative Approach",
            "rationale": "KPS <50 is associated with poor prognosis regardless of treatment. Aggressive local or systemic therapy is unlikely to provide meaningful benefit. Palliative care, symptom management, and goals-of-care discussion are recommended.",
            "evidenceLevel": "III",
            "guidelineSource": "CNS 2025 Brain Metastases Guidelines; ASCO 2022 Brain Metastases Guidelines",
            "localTherapyOptions": [
                "Corticosteroids for symptom management (dexamethasone 4–8 mg/day)",
                "WBRT may be considered for symptom palliation in selected patients",
            ],
            "systemicTherapyOptions": [
                "Continue targeted therapy if tolerated and previously effective",
                "Avoid aggressive cytotoxic chemotherapy",
            ],
            "surgicalConsiderations": [
                "Surgery generally not recommended with KPS <50 unless for emergency decompression",
            ],
            "monitoringPlan": [
                "Palliative care consultation",
                "Goals-of-care discussion",
                "Symptom-directed follow-up",
            ],
            "urgentFlags": urgent_flags,
            "warnings": [
                *warnings,
                "Prognosis: Median OS with KPS <50 is typically <2 months regardless of treatment.",
            ],
            "nextSteps": [
                "Palliative care consultation",
                "Goals-of-care discussion with patient and family",
                "Corticosteroids for symptom management",
                "Hospice evaluation if appropriate",
            ],
            "references": _get_brain_mets_references(),
        }

    # ── NSCLC with EGFR mutation ──────────────────────────────────────────────
    if primary_histology == "nsclc_egfr" and truthy(data.get("egfrMutation")):
        systemic_therapy_options.append(
            "Osimertinib (3rd-gen EGFR TKI): CNS penetration >60%, intracranial ORR ~70%. FLAURA2 trial: significant intracranial PFS benefit."
        )
        systemic_therapy_options.append(
            "EGFR TKIs + WBRT or SRS: Addition of EGFR TKIs to WBRT or SRS suggested to improve OS, PFS, and intracranial PFS (CNS 2025, Level III)."
        )
        if metastasis_count != "single" and metastasis_count != "limited":
            systemic_therapy_options.append(
                "Icotinib + WBRT: Recommended for NSCLC with EGFR mutation and ≥3 untreated brain metastases to improve intracranial PFS (CNS 2025, Level I)."
            )
        if metastasis_count == "single" or metastasis_count == "limited":
            local_therapy_options.append(
                "SRS + osimertinib: Preferred for limited brain metastases with EGFR mutation."
            )
        return _build_systemic_plus_local_recommendation(
            data,
            "NSCLC EGFR-Mutant: Targeted Therapy + Local Therapy",
            "NSCLC with EGFR mutation: Osimertinib has excellent CNS penetration and is the preferred systemic agent. For ≥3 untreated metastases, icotinib + WBRT improves intracranial PFS (Level I). EGFR TKIs + WBRT or SRS improves OS and PFS (Level III).",
            "I",
            urgent_flags,
            warnings,
            local_therapy_options,
            systemic_therapy_options,
            surgical_considerations,
            monitoring_plan,
        )

    # ── NSCLC with ALK mutation ───────────────────────────────────────────────
    if primary_histology == "nsclc_alk" and truthy(data.get("alkMutation")):
        systemic_therapy_options.append(
            "Alectinib: Recommended to delay intracranial tumor progression in ALK-mutant NSCLC with untreated brain metastases (CNS 2025, Level I)."
        )
        systemic_therapy_options.append(
            "Lorlatinib: Recommended to prolong intracranial tumor control and improve overall PFS (CNS 2025, Level II)."
        )
        systemic_therapy_options.append(
            "Brigatinib: Alternative ALK inhibitor with CNS activity."
        )
        return _build_systemic_plus_local_recommendation(
            data,
            "NSCLC ALK-Mutant: ALK Inhibitor Therapy",
            "ALK-mutant NSCLC with brain metastases: Alectinib is recommended to delay intracranial progression (Level I). Lorlatinib prolongs intracranial tumor control and improves overall PFS (Level II). These agents have excellent CNS penetration and may defer or eliminate need for local therapy.",
            "I",
            urgent_flags,
            warnings,
            local_therapy_options,
            systemic_therapy_options,
            surgical_considerations,
            monitoring_plan,
        )

    # ── Melanoma with BRAF V600E mutation ─────────────────────────────────────
    if primary_histology == "melanoma_braf" and truthy(data.get("brafV600E")):
        systemic_therapy_options.append(
            "Dabrafenib + trametinib: Recommended for BRAF V600E-mutant melanoma brain metastases for local tumor control (CNS 2025, Level I). Intracranial ORR ~60%."
        )
        systemic_therapy_options.append(
            "Ipilimumab + nivolumab: Recommended for active, untreated, asymptomatic parenchymal melanoma brain metastases to increase median OS (CNS 2025, Level I)."
        )
        return _build_systemic_plus_local_recommendation(
            data,
            "Melanoma BRAF V600E: Targeted Therapy + Immunotherapy",
            "BRAF V600E-mutant melanoma brain metastases: Dabrafenib + trametinib recommended for local tumor control (Level I). Ipilimumab + nivolumab recommended for active asymptomatic parenchymal metastases to improve OS (Level I). Combination of targeted therapy + immunotherapy may be considered in sequence.",
            "I",
            urgent_flags,
            warnings,
            local_therapy_options,
            systemic_therapy_options,
            surgical_considerations,
            monitoring_plan,
        )

    # ── Melanoma (non-BRAF or unknown) ────────────────────────────────────────
    if (
        primary_histology == "melanoma_other"
        or primary_histology == "melanoma_braf"
    ):
        systemic_therapy_options.append(
            "Ipilimumab + nivolumab: Recommended for active, untreated, asymptomatic parenchymal melanoma brain metastases (CNS 2025, Level I)."
        )
        systemic_therapy_options.append(
            "Pembrolizumab: Alternative checkpoint inhibitor with intracranial activity."
        )

    # ── Single/limited metastases — surgery or SRS ────────────────────────────
    if metastasis_count == "single" or metastasis_count == "limited":
        if largest_lesion_cm >= 3 or (
            truthy(data.get("symptomatic")) and truthy(data.get("massEffect"))
        ):
            surgical_considerations.append(
                "Large lesion (≥3 cm) or symptomatic mass effect: Surgical resection preferred for immediate decompression and tissue diagnosis."
            )
            surgical_considerations.append(
                "Post-resection SRS to cavity: Reduces local recurrence vs observation (Level I evidence from multiple RCTs)."
            )
            local_therapy_options.append(
                "Surgical resection + post-operative cavity SRS (preferred for large/symptomatic lesions)"
            )
            local_therapy_options.append(
                "SRS alone: Acceptable for lesions <3 cm without significant mass effect"
            )
            return {
                "primaryRecommendation": "surgery_plus_srs",
                "recommendationTitle": "Surgical Resection + Post-Operative Cavity SRS",
                "rationale": "Single or limited brain metastases with large lesion (≥3 cm) or symptomatic mass effect: Surgical resection provides immediate decompression, tissue diagnosis, and reduces tumor burden. Post-operative cavity SRS reduces local recurrence.",
                "evidenceLevel": "II",
                "guidelineSource": "CNS 2025 Brain Metastases Guidelines; ASCO 2022 Brain Metastases Guidelines (PMID 34936423)",
                "localTherapyOptions": local_therapy_options,
                "systemicTherapyOptions": systemic_therapy_options,
                "surgicalConsiderations": surgical_considerations,
                "monitoringPlan": [
                    "MRI brain at 6–8 weeks post-surgery/SRS",
                    "MRI brain every 2–3 months × 1 year, then every 3–4 months",
                    "Systemic staging CT every 3 months",
                ],
                "urgentFlags": urgent_flags,
                "warnings": [
                    *warnings,
                    "Post-resection SRS to cavity: Reduces local recurrence. WBRT should be avoided if SRS is feasible (neurocognitive toxicity).",
                ],
                "nextSteps": [
                    "Neurosurgery consultation for resection planning",
                    "Radiation oncology consultation for post-operative cavity SRS",
                    "Medical oncology for systemic therapy coordination",
                    "Tissue for molecular profiling if not previously obtained",
                    "MRI brain with gadolinium (thin-cut) for surgical planning",
                ],
                "references": _get_brain_mets_references(),
            }

        # Small single/limited — SRS alone
        local_therapy_options.append(
            "SRS (Gamma Knife, CyberKnife, or LINAC-based): Preferred for limited brain metastases <3 cm without significant mass effect."
        )
        local_therapy_options.append(
            "WBRT: Generally avoided in favor of SRS due to neurocognitive toxicity (QUARTZ trial, NCCTG N0574)."
        )
        return {
            "primaryRecommendation": "srs_alone",
            "recommendationTitle": "Stereotactic Radiosurgery (SRS) — Recommended",
            "rationale": "SRS is the preferred local therapy for limited brain metastases (<3 cm, no significant mass effect). Provides excellent local control (>80% at 1 year) with preservation of neurocognitive function. WBRT should be deferred due to neurocognitive toxicity.",
            "evidenceLevel": "I",
            "guidelineSource": "CNS 2025 Brain Metastases Guidelines; ASCO 2022 (PMID 34936423)",
            "localTherapyOptions": local_therapy_options,
            "systemicTherapyOptions": systemic_therapy_options,
            "surgicalConsiderations": surgical_considerations,
            "monitoringPlan": [
                "MRI brain at 6–8 weeks post-SRS",
                "MRI brain every 2–3 months × 1 year",
                "Systemic staging CT every 3 months",
            ],
            "urgentFlags": urgent_flags,
            "warnings": [
                *warnings,
                "Radiographic progression at 3–6 months may represent radiation necrosis vs true progression — MRI perfusion or PET may help differentiate.",
                "LITT (laser interstitial thermal therapy): Considered equivalent to craniotomy for recurrent brain metastases after SRS (CNS 2025, Level III).",
            ],
            "nextSteps": [
                "Radiation oncology consultation for SRS planning",
                "Medical oncology for systemic therapy coordination",
                "MRI brain with gadolinium (thin-cut) for SRS planning",
                "Molecular profiling of primary tumor if not done",
                "Neurocognitive baseline assessment",
            ],
            "references": _get_brain_mets_references(),
        }

    # ── Multiple/disseminated metastases ──────────────────────────────────────
    if metastasis_count == "multiple" or metastasis_count == "disseminated":
        # Actionable molecular target — systemic therapy first
        if (
            truthy(data.get("egfrMutation"))
            or truthy(data.get("alkMutation"))
            or truthy(data.get("brafV600E"))
            or truthy(data.get("her2Positive"))
        ):
            return _build_systemic_plus_local_recommendation(
                data,
                "Multiple Brain Metastases with Actionable Target: Systemic Therapy First",
                "Multiple brain metastases with actionable molecular target: CNS-penetrant targeted therapy is preferred first-line approach. Local therapy (SRS or WBRT) reserved for symptomatic lesions or progression on systemic therapy.",
                "II",
                urgent_flags,
                warnings,
                local_therapy_options,
                systemic_therapy_options,
                surgical_considerations,
                monitoring_plan,
            )

        # No actionable target — WBRT or SRS to multiple lesions
        local_therapy_options.append(
            "SRS to multiple lesions (up to 10–15): Preferred over WBRT if feasible to preserve neurocognitive function."
        )
        local_therapy_options.append(
            "WBRT: Consider for disseminated disease (>10 lesions) or leptomeningeal disease."
        )
        local_therapy_options.append(
            "Hippocampal-avoidance WBRT + memantine: If WBRT required, reduces neurocognitive toxicity."
        )
        warnings.append(
            "WBRT neurocognitive toxicity: Avoid if SRS to multiple lesions is feasible. Hippocampal-avoidance WBRT + memantine reduces cognitive decline."
        )

        return {
            "primaryRecommendation": "wbrt",
            "recommendationTitle": "Whole Brain Radiation Therapy (WBRT) or Multi-Lesion SRS",
            "rationale": "Multiple/disseminated brain metastases without actionable molecular target: WBRT or SRS to multiple lesions. Hippocampal-avoidance WBRT + memantine preferred if WBRT is required to reduce neurocognitive toxicity.",
            "evidenceLevel": "II",
            "guidelineSource": "CNS 2025 Brain Metastases Guidelines; ASCO 2022 (PMID 34936423)",
            "localTherapyOptions": local_therapy_options,
            "systemicTherapyOptions": systemic_therapy_options,
            "surgicalConsiderations": [
                "Surgery for single dominant symptomatic lesion causing mass effect",
            ],
            "monitoringPlan": [
                "MRI brain at 4–6 weeks post-WBRT",
                "MRI brain every 2–3 months",
                "Neurocognitive assessment at 3 and 6 months",
            ],
            "urgentFlags": urgent_flags,
            "warnings": warnings,
            "nextSteps": [
                "Radiation oncology consultation",
                "Medical oncology for systemic therapy coordination",
                "Molecular profiling if not done",
                "Neurocognitive baseline assessment",
                "Consider SRS to multiple lesions if ≤10 lesions and KPS ≥70",
            ],
            "references": _get_brain_mets_references(),
        }

    # ── Default: multidisciplinary evaluation ────────────────────────────────
    return {
        "primaryRecommendation": "multidisciplinary_evaluation",
        "recommendationTitle": "Multidisciplinary Tumor Board Evaluation",
        "rationale": "Complex brain metastases case requiring multidisciplinary tumor board review involving neurosurgery, radiation oncology, and medical oncology.",
        "evidenceLevel": "III",
        "guidelineSource": "CNS 2025 Brain Metastases Guidelines",
        "localTherapyOptions": local_therapy_options,
        "systemicTherapyOptions": systemic_therapy_options,
        "surgicalConsiderations": surgical_considerations,
        "monitoringPlan": ["MRI brain with gadolinium", "Systemic staging"],
        "urgentFlags": urgent_flags,
        "warnings": warnings,
        "nextSteps": [
            "Multidisciplinary tumor board presentation",
            "Neurosurgery, radiation oncology, and medical oncology consultation",
            "Molecular profiling of primary tumor",
        ],
        "references": _get_brain_mets_references(),
    }
