"""Diffuse Low-Grade Glioma Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/lowGradeGliomaLogic.ts
(assessLowGradeGlioma).

Based on:
- SEOM-GEINO Clinical Guidelines for Grade 2 Gliomas (2024)
- WHO Classification of Tumors of the CNS 2021
- EORTC 22033-26033, RTOG 9802, INDIGO (Vorasidenib) trials
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "lowgradeglioma"


def _get_lgg_references() -> list[dict]:
    return [
        {
            "citation": (
                "Vaz-Salgado MA et al. SEOM-GEINO Clinical Guidelines for Grade 2 "
                "Gliomas (2023). Clin Transl Oncol. 2024;26(11):2856-2865."
            ),
            "pmid": "38662171",
        },
        {
            "citation": (
                "Louis DN et al. The 2021 WHO Classification of Tumors of the "
                "Central Nervous System. Acta Neuropathol. 2021;142(3):405-430."
            ),
            "pmid": "34185076",
        },
        {
            "citation": (
                "Buckner JC et al. Radiation plus Procarbazine, CCNU, and "
                "Vincristine in Low-Grade Glioma (RTOG 9802). N Engl J Med. "
                "2016;374(14):1344-1355."
            ),
            "pmid": "27050206",
        },
        {
            "citation": (
                "Mellinghoff IK et al. Vorasidenib in IDH1- or IDH2-Mutant "
                "Low-Grade Glioma (INDIGO Trial). N Engl J Med. 2023;389(8):710-721."
            ),
            "pmid": "37610921",
        },
        {
            "citation": (
                "Baumert BG et al. Temozolomide Chemotherapy versus Radiotherapy "
                "in High-Risk Low-Grade Glioma (EORTC 22033-26033). Lancet Oncol. "
                "2016;17(11):1521-1532."
            ),
            "pmid": "27686946",
        },
        {
            "citation": (
                "Shaw EG et al. Recurrence Following Neurosurgeon-Determined "
                "Gross-Total Resection of Adult Supratentorial Low-Grade Glioma. "
                "J Clin Oncol. 2012;30(31):3865-3870."
            ),
            "pmid": "23008392",
        },
        {
            "citation": (
                "Pignatti F et al. Prognostic Factors for Survival in Adult "
                "Patients with Cerebral Low-Grade Glioma. J Clin Oncol. "
                "2002;20(8):2076-2084."
            ),
            "pmid": "11956268",
        },
    ]


def assess(data: dict) -> dict:
    idh_status = data.get("idhStatus")
    tert_promoter_mutation = truthy(data.get("tertPromoterMutation"))
    egfr_amplification = truthy(data.get("egfrAmplification"))
    chromosome7_gain10_loss = truthy(data.get("chromosome7Gain10Loss"))
    tumor_size_cm = num(data.get("tumorSizeCm"), 0)
    tumor_crosses_midline = truthy(data.get("tumorCrossesMidline"))
    eloquent_cortex_involvement = truthy(data.get("eloquentCortexInvolvement"))
    age_years = num(data.get("ageYears"), 0)
    neurologic_deficit = truthy(data.get("neurologicDeficit"))
    extent_of_resection = data.get("extentOfResection")
    risk_category = data.get("riskCategory")

    urgent_flags: list[str] = []
    warnings: list[str] = []
    molecular_workup: list[str] = []
    adjuvant_therapy: list[str] = []
    monitoring_plan: list[str] = []

    # ── Molecular workup requirements ──
    molecular_workup.append(
        "IDH1/IDH2 mutation testing: IHC (IDH1 R132H) + sequencing if IHC negative"
    )
    molecular_workup.append("ATRX IHC: Loss suggests IDH-mutant astrocytoma")
    molecular_workup.append(
        "1p/19q co-deletion: FISH or sequencing (oligodendroglioma diagnosis "
        "requires IDH-mutant + 1p/19q co-deleted)"
    )
    molecular_workup.append("TERT promoter mutation sequencing")
    molecular_workup.append("EGFR amplification (if IDH-wildtype)")
    molecular_workup.append("+7/-10 chromosome copy number (if IDH-wildtype)")
    molecular_workup.append(
        "MGMT promoter methylation (guides chemotherapy response)"
    )

    # ── IDH-wildtype → likely GBM reclassification ──
    if idh_status == "idh_wildtype":
        if tert_promoter_mutation or egfr_amplification or chromosome7_gain10_loss:
            urgent_flags.append(
                "IDH-wildtype diffuse astrocytic tumor with TERT promoter "
                "mutation, EGFR amplification, or +7/-10: Meets criteria for "
                "IDH-wildtype Glioblastoma (WHO 2021). Reclassify and manage as GBM."
            )
            return {
                "primaryRecommendation": "reclassify_as_gbm",
                "recommendationTitle": (
                    "Reclassify as IDH-Wildtype Glioblastoma (WHO Grade 4)"
                ),
                "rationale": (
                    "IDH-wildtype diffuse astrocytic tumor with TERT promoter "
                    "mutation, EGFR amplification, or +7/-10 chromosome copy "
                    "number changes meets WHO 2021 criteria for IDH-wildtype "
                    "Glioblastoma regardless of histologic grade. Management "
                    "should follow GBM protocols (Stupp regimen)."
                ),
                "evidenceLevel": "IA",
                "guidelineSource": (
                    "WHO Classification of Tumors of the CNS 2021 (Louis DN et "
                    "al., Acta Neuropathol 2021; PMID 34185076)"
                ),
                "molecularDiagnosis": "IDH-wildtype Glioblastoma (WHO Grade 4)",
                "molecularWorkup": molecular_workup,
                "surgicalStrategy": (
                    "Maximal safe resection followed by concurrent temozolomide "
                    "+ RT (Stupp protocol), then adjuvant temozolomide."
                ),
                "adjuvantTherapy": [
                    "Concurrent temozolomide 75 mg/m²/day during RT",
                    "Adjuvant temozolomide 150–200 mg/m²/day × 5 days every "
                    "28 days × 6 cycles",
                    "MGMT methylation status guides benefit from temozolomide",
                    "Tumor treating fields (TTFields/Optune): Consider for newly "
                    "diagnosed GBM",
                ],
                "monitoringPlan": [
                    "MRI brain every 8–12 weeks",
                    "Pseudoprogression assessment at first post-RT MRI (6–8 weeks)",
                ],
                "urgentFlags": urgent_flags,
                "warnings": [
                    "This is NOT a low-grade glioma — reclassification to GBM "
                    "changes prognosis and treatment significantly.",
                    "Median OS for GBM: 14–16 months with Stupp regimen.",
                ],
                "nextSteps": [
                    "Neuro-oncology consultation for GBM management",
                    "MGMT methylation testing",
                    "Radiation oncology consultation for Stupp protocol",
                    "Multidisciplinary neuro-oncology tumor board",
                ],
                "references": _get_lgg_references(),
            }

    # ── Molecular diagnosis label ──
    molecular_diagnosis = "Pending molecular testing"
    if idh_status == "idh_mutant_1p19q_codeleted":
        molecular_diagnosis = (
            "Oligodendroglioma, IDH-mutant, 1p/19q-codeleted (WHO Grade 2)"
        )
    elif idh_status == "idh_mutant_atrx_mutant":
        molecular_diagnosis = "Astrocytoma, IDH-mutant (WHO Grade 2)"
    elif idh_status == "idh_wildtype":
        molecular_diagnosis = (
            "IDH-wildtype diffuse glioma — evaluate for GBM molecular markers"
        )
        warnings.append(
            "IDH-wildtype without GBM molecular markers: Rare. Consider repeat "
            "biopsy or expanded molecular panel."
        )

    # ── Unknown molecular status ──
    if idh_status == "unknown":
        return {
            "primaryRecommendation": "multidisciplinary_evaluation",
            "recommendationTitle": (
                "Molecular Testing Required — Defer Treatment Decision"
            ),
            "rationale": (
                "WHO 2021 classification requires molecular profiling (IDH, "
                "1p/19q, ATRX, TERT) before treatment planning. Treatment "
                "decisions for diffuse gliomas must be based on integrated "
                "histomolecular diagnosis."
            ),
            "evidenceLevel": "IA",
            "guidelineSource": (
                "WHO Classification of Tumors of the CNS 2021 (PMID 34185076); "
                "SEOM-GEINO 2024 (PMID 38662171)"
            ),
            "molecularDiagnosis": "Pending molecular testing",
            "molecularWorkup": molecular_workup,
            "surgicalStrategy": (
                "If not yet resected: Maximal safe resection to obtain adequate "
                "tissue for molecular profiling."
            ),
            "adjuvantTherapy": [
                "Defer adjuvant therapy pending molecular classification"
            ],
            "monitoringPlan": ["MRI brain with gadolinium after surgery"],
            "urgentFlags": urgent_flags,
            "warnings": [
                *warnings,
                "Do not initiate adjuvant therapy without molecular "
                "classification — treatment differs significantly between "
                "oligodendroglioma and astrocytoma.",
            ],
            "nextSteps": [
                "Ensure adequate tissue for molecular testing (IDH, 1p/19q, "
                "ATRX, TERT, EGFR, MGMT)",
                "Neuro-pathology review at specialized center",
                "Neuro-oncology multidisciplinary tumor board",
                "Defer adjuvant therapy pending molecular results",
            ],
            "references": _get_lgg_references(),
        }

    # ── Risk stratification ──
    is_high_risk = (
        risk_category == "high_risk"
        or age_years >= 40
        or extent_of_resection == "biopsy"
        or extent_of_resection == "subtotal"
        or tumor_size_cm >= 6
        or tumor_crosses_midline
        or neurologic_deficit
    )

    # ── Low-risk after GTR — observation ──
    if (
        not is_high_risk
        and extent_of_resection == "gross_total"
        and age_years < 40
        and not neurologic_deficit
    ):
        monitoring_plan.append(
            "MRI brain every 3–6 months × 2 years, then every 6–12 months"
        )
        monitoring_plan.append("Neurologic and neurocognitive assessment annually")

        return {
            "primaryRecommendation": "observation_after_gtr",
            "recommendationTitle": (
                "Observation After Gross Total Resection — Low-Risk LGG"
            ),
            "rationale": (
                "Low-risk LGG (age <40, GTR, no neurologic deficit): Observation "
                "after GTR is acceptable. EORTC 22033-26033 showed no OS benefit "
                "of immediate RT vs observation in low-risk patients. Early "
                "adjuvant therapy reserved for high-risk features."
            ),
            "evidenceLevel": "IIA",
            "guidelineSource": (
                "SEOM-GEINO 2024 (PMID 38662171); EORTC 22033-26033 (Baumert BG "
                "et al., Lancet Oncol 2016)"
            ),
            "molecularDiagnosis": molecular_diagnosis,
            "molecularWorkup": molecular_workup,
            "surgicalStrategy": (
                "GTR achieved. No immediate adjuvant therapy required for "
                "low-risk LGG."
            ),
            "adjuvantTherapy": [
                "Observation: Serial MRI every 3–6 months",
                "Vorasidenib (IDH inhibitor): Consider for IDH-mutant Grade 2 "
                "glioma after surgery (INDIGO trial, N Engl J Med 2023; "
                "PMID 37610921)",
                "Trigger for adjuvant therapy: Radiographic progression, new "
                "neurologic deficit, or transformation",
            ],
            "monitoringPlan": monitoring_plan,
            "urgentFlags": urgent_flags,
            "warnings": [
                w
                for w in [
                    *warnings,
                    "Vorasidenib (IDH inhibitor): INDIGO trial showed significant "
                    "improvement in PFS for IDH-mutant Grade 2 glioma after "
                    "surgery. Discuss with neuro-oncology.",
                    (
                        "IDH-mutant astrocytoma: Higher risk of transformation to "
                        "Grade 3/4 than oligodendroglioma. Closer surveillance "
                        "warranted."
                        if idh_status == "idh_mutant_atrx_mutant"
                        else ""
                    ),
                ]
                if truthy(w)
            ],
            "nextSteps": [
                "Neuro-oncology follow-up every 3–6 months",
                "MRI brain every 3–6 months × 2 years",
                "Discuss vorasidenib (IDH inhibitor) with neuro-oncology",
                "Seizure management if applicable (antiepileptic therapy)",
                "Neuropsychological assessment",
            ],
            "references": _get_lgg_references(),
        }

    # ── High-risk — RT + chemotherapy ──
    if is_high_risk:
        is_oligodendroglioma = idh_status == "idh_mutant_1p19q_codeleted"

        if is_oligodendroglioma:
            adjuvant_therapy.append(
                "RT (54 Gy in 30 fractions) followed by PCV chemotherapy "
                "(procarbazine + CCNU + vincristine) × 6 cycles — RTOG 9802 "
                "standard (Level I-A)"
            )
            adjuvant_therapy.append(
                "Alternative: RT + temozolomide (less evidence for "
                "oligodendroglioma vs PCV)"
            )
            adjuvant_therapy.append(
                "Vorasidenib: Consider for IDH-mutant Grade 2 glioma (INDIGO "
                "trial, Level I)"
            )
        else:
            adjuvant_therapy.append(
                "RT (54 Gy in 30 fractions) followed by PCV chemotherapy × 6 "
                "cycles — RTOG 9802 (Level I-A)"
            )
            adjuvant_therapy.append(
                "RT + temozolomide: Alternative regimen (less Level I evidence "
                "for LGG vs GBM)"
            )
            adjuvant_therapy.append(
                "Vorasidenib: Consider for IDH-mutant Grade 2 astrocytoma "
                "(INDIGO trial, Level I)"
            )

        monitoring_plan.append("MRI brain every 3 months during treatment")
        monitoring_plan.append(
            "MRI brain every 3–6 months post-treatment × 2 years"
        )
        monitoring_plan.append("Neurocognitive assessment at baseline and annually")

        return {
            "primaryRecommendation": "rt_plus_pvc_chemotherapy",
            "recommendationTitle": (
                "RT + "
                + ("PCV Chemotherapy" if is_oligodendroglioma else "PCV or Temozolomide")
                + " — High-Risk LGG"
            ),
            "rationale": (
                "High-risk LGG (age ≥40, STR/biopsy, neurologic deficit, large "
                "tumor, or midline crossing): RT + PCV chemotherapy is the "
                "standard of care per RTOG 9802 (Level I-A). RT alone is inferior "
                "to RT + PCV for high-risk LGG. Vorasidenib (IDH inhibitor) is an "
                "emerging option per INDIGO trial."
            ),
            "evidenceLevel": "IA",
            "guidelineSource": (
                "SEOM-GEINO 2024 (PMID 38662171); RTOG 9802 — Buckner JC et al., "
                "N Engl J Med 2016 (PMID 26598715); INDIGO Trial — Mellinghoff IK "
                "et al., N Engl J Med 2023 (PMID 37610921)"
            ),
            "molecularDiagnosis": molecular_diagnosis,
            "molecularWorkup": molecular_workup,
            "surgicalStrategy": (
                "Biopsy only: Consider re-resection for maximal safe resection "
                "before adjuvant therapy if feasible."
                if extent_of_resection == "biopsy"
                else "Maximal safe resection achieved. Proceed with adjuvant therapy."
            ),
            "adjuvantTherapy": adjuvant_therapy,
            "chemotherapyRegimen": (
                "PCV: Procarbazine 60 mg/m²/day days 8–21, CCNU 110 mg/m²/day "
                "day 1, Vincristine 1.4 mg/m² days 8 and 29; every 8 weeks × 6 "
                "cycles"
                if is_oligodendroglioma
                else "PCV (preferred per RTOG 9802) or Temozolomide 150–200 "
                "mg/m²/day × 5 days every 28 days × 12 cycles"
            ),
            "monitoringPlan": monitoring_plan,
            "urgentFlags": urgent_flags,
            "warnings": [
                w
                for w in [
                    *warnings,
                    "Radiation dose: 54 Gy in 30 fractions (standard). Higher "
                    "doses not shown to improve outcomes and increase "
                    "neurotoxicity.",
                    (
                        "Eloquent cortex involvement: Awake craniotomy with "
                        "cortical mapping may be required for maximal safe "
                        "resection."
                        if eloquent_cortex_involvement
                        else ""
                    ),
                    "Vorasidenib (IDH inhibitor): INDIGO trial showed 61% "
                    "reduction in risk of progression or death vs placebo for "
                    "IDH-mutant Grade 2 glioma after surgery. FDA approved 2024.",
                ]
                if truthy(w)
            ],
            "nextSteps": [
                s
                for s in [
                    "Radiation oncology consultation for RT planning "
                    "(54 Gy/30 fractions)",
                    "Neuro-oncology consultation for chemotherapy (PCV or "
                    "temozolomide)",
                    "Discuss vorasidenib eligibility (IDH-mutant, Grade 2, "
                    "post-surgery)",
                    "MGMT methylation testing",
                    "Neuropsychological baseline assessment",
                    "Seizure management optimization",
                    (
                        "Consider re-resection for maximal safe resection"
                        if extent_of_resection == "biopsy"
                        else ""
                    ),
                ]
                if truthy(s)
            ],
            "references": _get_lgg_references(),
        }

    # ── Default: surgery first ──
    return {
        "primaryRecommendation": "surgery_maximal_safe_resection",
        "recommendationTitle": "Maximal Safe Resection — Primary Treatment",
        "rationale": (
            "Maximal safe resection is the primary treatment for diffuse "
            "low-grade glioma. Greater extent of resection is associated with "
            "improved OS and PFS. Eloquent cortex involvement requires awake "
            "craniotomy with cortical mapping."
        ),
        "evidenceLevel": "IVB",
        "guidelineSource": "SEOM-GEINO 2024 (PMID 38662171); CNS 2025 LGG Guidelines",
        "molecularDiagnosis": molecular_diagnosis,
        "molecularWorkup": molecular_workup,
        "surgicalStrategy": (
            "Awake craniotomy with cortical mapping and intraoperative "
            "neurophysiological monitoring for eloquent cortex involvement."
            if eloquent_cortex_involvement
            else "Standard craniotomy for maximal safe resection. Intraoperative "
            "MRI or ultrasound to maximize EOR."
        ),
        "adjuvantTherapy": [
            "Adjuvant therapy decision based on risk stratification after surgery",
            "Low-risk (age <40, GTR): Observation acceptable",
            "High-risk (age ≥40, STR, neurologic deficit): RT + PCV chemotherapy",
        ],
        "monitoringPlan": [
            "MRI brain within 48–72 hours postoperatively (extent of resection "
            "assessment)",
            "MRI brain every 3–6 months postoperatively",
        ],
        "urgentFlags": urgent_flags,
        "warnings": [
            *warnings,
            "Molecular profiling: Ensure adequate tissue for IDH, 1p/19q, ATRX, "
            "TERT, MGMT testing.",
        ],
        "nextSteps": [
            "Neurosurgery consultation for resection planning",
            "Neuro-oncology multidisciplinary tumor board",
            "Functional MRI and DTI tractography for eloquent cortex mapping",
            "Ensure molecular profiling from surgical specimen",
            "Postoperative MRI within 48–72 hours",
        ],
        "references": _get_lgg_references(),
    }
