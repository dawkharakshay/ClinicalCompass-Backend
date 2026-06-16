"""Rectal Cancer Clinical Compass — TNT vs Surgery vs Watch-and-Wait.

Ported 1:1 from old_static_code/client/src/lib/rectalCancerLogic.ts
(assessRectalCancer and all helpers).

Based on:
- NCCN Guidelines Rectal Cancer v3.2024 (PMID: 39151454)
- ESMO Living Guideline: Localised Rectal Cancer v1.0 2025 (PMID: 40412553)
- ASCO Guideline Clinical Insights 2025 (PMID: 39236282)
Key trials: RAPIDO, PRODIGE 23, OPRA, PROSPECT, TRIGGER
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "rectalcancer"


# ─── Evidence (static reference list) ─────────────────────────────────────────
# Ported 1:1 from old_static_code/client/src/pages/RectalCancerCompass.tsx
# (the page-level REFERENCES array). Static per module — attached to every
# recommendation so the frontend renders without holding its own copy.

EVIDENCE = [
    {
        "title": "NCCN Clinical Practice Guidelines in Oncology: Rectal Cancer v3.2024",
        "source": "National Comprehensive Cancer Network",
        "description": "Comprehensive guidelines for rectal cancer staging, neoadjuvant therapy, surgical approach, and watch-and-wait protocols.",
        "pmid": "39151454",
    },
    {
        "title": "ESMO Living Guideline: Localised Rectal Cancer v1.0 2025",
        "source": "Glynne-Jones R et al.",
        "description": "European Society for Medical Oncology living guideline covering TNT regimens, organ preservation, and watch-and-wait strategies.",
        "pmid": "40412553",
    },
    {
        "title": "RAPIDO Trial: Short-course RT + consolidation chemotherapy vs standard CRT",
        "source": "Bahadoer RR et al. Lancet Oncol. 2021",
        "description": "RAPIDO: Short-course RT (5×5 Gy) followed by CAPOX chemotherapy improved pCR (28% vs 14%) and 3-year DFS for high-risk locally advanced rectal cancer.",
        "pmid": "33301740",
    },
    {
        "title": "PRODIGE 23 Trial: Induction FOLFIRINOX before CRT",
        "source": "Conroy T et al. J Clin Oncol. 2021",
        "description": "PRODIGE 23: mFOLFIRINOX induction before CRT improved 3-year DFS (75.7% vs 68.5%) and pCR rate (27.5% vs 11.7%).",
        "pmid": "33577352",
    },
    {
        "title": "OPRA Trial: Organ Preservation in Rectal Cancer",
        "source": "Garcia-Aguilar J et al. J Clin Oncol. 2022",
        "description": "OPRA: consolidation chemotherapy after CRT increased organ preservation rates (58% W&W at 3 years for cCR patients).",
        "pmid": "35436152",
    },
    {
        "title": "Watch-and-Wait in Rectal Cancer: International Registry",
        "source": "Fernandez LM et al. Lancet Oncol. 2021",
        "description": "International Watch & Wait Database: 2-year organ preservation rate 88% for cCR patients. 5-year OS comparable to surgery.",
        "pmid": "33765415",
    },
]


# ─── Input normalisation ──────────────────────────────────────────────────────


def _inp(data: dict) -> dict:
    """Coerce submitted form fields to the shapes the TS logic expects.

    String enums compared with ``===`` in TS are kept as raw strings; boolean
    flags (truthiness checks ``if (input.x)``) go through ``to_bool``.
    """
    return {
        "tStage": data.get("tStage"),
        "nStage": data.get("nStage"),
        "mStage": data.get("mStage"),
        "tumorLocation": data.get("tumorLocation"),
        "mrfStatus": data.get("mrfStatus"),
        "emviStatus": data.get("emviStatus"),
        "tumorSize": num(data.get("tumorSize"), 0),
        "age": num(data.get("age"), 0),
        "ecogPS": data.get("ecogPS"),
        "surgicalFitness": data.get("surgicalFitness"),
        "priorPelvicRT": to_bool(data.get("priorPelvicRT")),
        "priorChemo": to_bool(data.get("priorChemo")),
        "responseAssessment": data.get("responseAssessment"),
        "patientPreference": data.get("patientPreference"),
        "ibd": to_bool(data.get("ibd")),
        "msi_mmr": data.get("msi_mmr"),
    }


# ─── Helper Functions ─────────────────────────────────────────────────────────


def classify_disease(i: dict) -> str:
    t_stage = i["tStage"]
    n_stage = i["nStage"]
    m_stage = i["mStage"]
    if m_stage == "M1":
        return "metastatic"
    if t_stage == "T1" and n_stage == "N0":
        return "early"
    if t_stage == "T2" and n_stage == "N0":
        return "early_t2"
    if (t_stage == "T3" or t_stage == "T4a") and n_stage == "N0":
        return "locally_advanced_low_risk"
    if n_stage != "N0" or t_stage == "T4b" or i["mrfStatus"] != "clear":
        return "locally_advanced_high_risk"
    return "locally_advanced_intermediate"


def is_tnt_candidate(i: dict) -> bool:
    t_stage = i["tStage"]
    n_stage = i["nStage"]
    mrf_status = i["mrfStatus"]
    emvi_status = i["emviStatus"]
    tumor_location = i["tumorLocation"]
    m_stage = i["mStage"]
    if m_stage == "M1":
        return False
    if i["priorPelvicRT"]:
        return False
    # High-risk features per RAPIDO/PRODIGE 23 criteria
    high_risk_features = [
        t_stage == "T4a" or t_stage == "T4b",
        n_stage == "N2",
        mrf_status == "threatened" or mrf_status == "involved",
        emvi_status == "positive",
        tumor_location == "lower" and n_stage != "N0",
    ].count(True)
    # T3N0 with clear MRF — TNT is an option but not required
    if t_stage == "T3" and n_stage == "N0" and mrf_status == "clear":
        return True
    return high_risk_features >= 1


def is_watch_and_wait_eligible(i: dict) -> bool:
    response_assessment = i["responseAssessment"]
    m_stage = i["mStage"]
    surgical_fitness = i["surgicalFitness"]
    prior_pelvic_rt = i["priorPelvicRT"]
    if m_stage == "M1":
        return False
    if prior_pelvic_rt:
        return False
    return (
        response_assessment == "cCR"
        or (response_assessment == "near_cCR" and surgical_fitness == "unfit")
        or (
            response_assessment == "near_cCR"
            and i["patientPreference"] == "organ_preservation"
        )
    )


def select_tnt_regimen(i: dict) -> dict:
    mrf_status = i["mrfStatus"]
    t_stage = i["tStage"]
    emvi_status = i["emviStatus"]
    # RAPIDO regimen: short-course RT → consolidation chemo (preferred for high-risk)
    if mrf_status == "involved" or t_stage == "T4b" or emvi_status == "positive":
        return {
            "regimen": "short_course_rt_chemo",
            "label": "Short-course RT (5×5 Gy) → CAPOX/FOLFOX × 6 cycles → TME (RAPIDO regimen)",
            "rationale": "RAPIDO trial: superior pCR (28% vs 14%) and 3-year disease-free survival (30.4% vs 27.7%) vs standard CRT for high-risk locally advanced rectal cancer.",
        }
    # PRODIGE 23 regimen: induction FOLFIRINOX → CRT → surgery
    if t_stage == "T3" or t_stage == "T4a":
        return {
            "regimen": "induction_chemo_crt",
            "label": "Induction mFOLFIRINOX × 6 cycles → CRT → TME (PRODIGE 23 regimen)",
            "rationale": "PRODIGE 23 trial: improved 3-year DFS (75.7% vs 68.5%) and pCR rate (27.5% vs 11.7%) with induction FOLFIRINOX before CRT.",
        }
    # Standard long-course CRT + consolidation
    return {
        "regimen": "long_course_crt_chemo",
        "label": "Long-course CRT (45-50.4 Gy + capecitabine) → consolidation CAPOX × 2-3 cycles → TME",
        "rationale": "OPRA trial: consolidation chemotherapy after CRT increases organ preservation rates (58% W&W at 3 years for cCR patients).",
    }


def calculate_organ_preservation_score(i: dict) -> int:
    score = 50  # baseline
    # Favorable factors
    if i["tumorLocation"] == "lower":
        score += 15  # lower tumors → APR avoided
    if i["patientPreference"] == "organ_preservation":
        score += 10
    if i["responseAssessment"] == "cCR":
        score += 25
    if i["responseAssessment"] == "near_cCR":
        score += 15
    if i["tStage"] == "T1" or i["tStage"] == "T2":
        score += 10
    if i["nStage"] == "N0":
        score += 5
    # Unfavorable factors
    if i["tStage"] == "T4b":
        score -= 20
    if i["mrfStatus"] == "involved":
        score -= 15
    if i["nStage"] == "N2":
        score -= 10
    if i["responseAssessment"] == "no_response":
        score -= 30
    if i["priorPelvicRT"]:
        score -= 20
    if i["ibd"]:
        score -= 10
    return max(0, min(100, score))


# ─── Main Assessment Function ─────────────────────────────────────────────────


def assess(data: dict) -> dict:
    i = _inp(data)
    warnings: list[str] = []
    next_steps: list[str] = []
    classify_disease(i)  # diseaseClass (computed, unused downstream — kept for parity)
    organ_score = calculate_organ_preservation_score(i)

    # ── Metastatic disease ──
    if i["mStage"] == "M1":
        # MSI-H/dMMR: immunotherapy first
        if i["msi_mmr"] == "MSI-H":
            return {
                "strategy": "immunotherapy_first",
                "strategyLabel": "Immunotherapy-First (Pembrolizumab)",
                "urgency": "routine",
                "wwEligible": False,
                "organPreservationScore": organ_score,
                "organPreservationLabel": "Not applicable (metastatic disease)",
                "keyWarnings": [
                    "MSI-H/dMMR metastatic rectal cancer — pembrolizumab first-line per KEYNOTE-177"
                ],
                "nextSteps": [
                    "Pembrolizumab 200 mg Q3W (KEYNOTE-177 regimen)",
                    "Multidisciplinary tumor board discussion",
                    "Consider conversion resection if response achieved",
                ],
                "rationale": "KEYNOTE-177: pembrolizumab superior to chemotherapy as first-line for MSI-H/dMMR mCRC (PFS HR 0.60, OS HR 0.74).",
                "evidenceLevel": "Category 1",
                "guidelineSource": "NCCN Rectal Cancer v3.2024; ESMO 2025",
            }
        return {
            "strategy": "palliative",
            "strategyLabel": "Systemic Therapy (Palliative Intent)",
            "urgency": "routine",
            "wwEligible": False,
            "organPreservationScore": 0,
            "organPreservationLabel": "Not applicable (metastatic disease)",
            "keyWarnings": [
                "Metastatic disease — curative resection not indicated unless oligometastatic with resectable disease"
            ],
            "nextSteps": [
                "FOLFOX/FOLFIRI + bevacizumab or cetuximab (RAS/BRAF status)",
                "Consider resection of primary if symptomatic obstruction/bleeding",
                "Multidisciplinary tumor board discussion",
                "Assess for oligometastatic resection candidacy",
            ],
            "rationale": "Systemic therapy is standard for metastatic rectal cancer. Oligometastatic disease may be considered for curative resection after MDT discussion.",
            "evidenceLevel": "Category 1",
            "guidelineSource": "NCCN Rectal Cancer v3.2024",
        }

    # ── Early stage (T1N0) — local excision ──
    if i["tStage"] == "T1" and i["nStage"] == "N0":
        ww_eligible = i["responseAssessment"] == "cCR"
        return {
            "strategy": "upfront_surgery",
            "strategyLabel": "Local Excision (TEM/TAMIS) or Low Anterior Resection",
            "urgency": "routine",
            "surgicalApproach": "local_excision",
            "surgicalApproachLabel": "Transanal Endoscopic Microsurgery (TEM) or TAMIS for T1N0 <3 cm, favorable histology",
            "wwEligible": ww_eligible,
            "wwCriteria": ["cCR after neoadjuvant therapy"] if ww_eligible else None,
            "organPreservationScore": organ_score,
            "organPreservationLabel": "High — organ preservation likely achievable"
            if organ_score >= 70
            else "Moderate",
            "keyWarnings": [
                w
                for w in [
                    "Ensure no high-risk features: sm3 invasion, LVI, poor differentiation — if present, proceed to TME",
                    "Lower rectal T1N0: TEM/TAMIS preferred to avoid permanent colostomy"
                    if i["tumorLocation"] == "lower"
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "Endorectal ultrasound or MRI for precise T-staging",
                "TEM/TAMIS for T1N0 <3 cm with favorable histology",
                "If high-risk features on pathology: completion TME",
                "Surveillance: MRI + endoscopy Q3-6 months × 2 years",
            ],
            "rationale": "T1N0 rectal cancer: local excision (TEM/TAMIS) is appropriate for lesions <3 cm without high-risk features. TME required for sm3, LVI, or poor differentiation.",
            "evidenceLevel": "Category 2A",
            "guidelineSource": "NCCN Rectal Cancer v3.2024; ESMO 2025",
        }

    # ── T2N0 — surgery vs short-course RT + surgery ──
    if i["tStage"] == "T2" and i["nStage"] == "N0" and i["mrfStatus"] == "clear":
        ww_eligible = is_watch_and_wait_eligible(i)
        tnt_candidate = (
            i["tumorLocation"] == "lower"
            and i["patientPreference"] == "organ_preservation"
        )
        return {
            "strategy": "tnt_alternative" if tnt_candidate else "upfront_surgery",
            "strategyLabel": "Neoadjuvant CRT → Assess Response → Surgery or W&W"
            if tnt_candidate
            else "Total Mesorectal Excision (TME)",
            "urgency": "routine",
            "surgicalApproach": "apr" if i["tumorLocation"] == "lower" else "lar",
            "surgicalApproachLabel": "Abdominoperineal Resection (APR) — unless organ preservation achieved"
            if i["tumorLocation"] == "lower"
            else "Low Anterior Resection (LAR) with TME",
            "wwEligible": ww_eligible,
            "wwCriteria": [
                "cCR after neoadjuvant therapy",
                "Patient preference for organ preservation",
                "Strict surveillance protocol",
            ]
            if ww_eligible
            else None,
            "organPreservationScore": organ_score,
            "organPreservationLabel": "Moderate-High — consider neoadjuvant if organ preservation desired"
            if organ_score >= 60
            else "Moderate",
            "keyWarnings": [
                w
                for w in [
                    "Lower T2N0: discuss organ preservation options — neoadjuvant CRT may allow W&W if cCR achieved"
                    if i["tumorLocation"] == "lower"
                    else "",
                    "Ensure accurate MRI staging before treatment decision",
                ]
                if w
            ],
            "nextSteps": [
                "High-resolution MRI pelvis for precise staging",
                "Neoadjuvant CRT (50.4 Gy + capecitabine) → response assessment MRI at 8-12 weeks"
                if tnt_candidate
                else "Upfront TME with nerve-sparing technique",
                "Multidisciplinary tumor board discussion",
                "Discuss sphincter preservation vs permanent colostomy with patient",
            ],
            "rationale": "T2N0 rectal cancer: upfront TME is standard. For lower rectal T2N0 with patient preference for organ preservation, neoadjuvant CRT with W&W after cCR is an option per OPRA trial.",
            "evidenceLevel": "Category 2A",
            "guidelineSource": "NCCN Rectal Cancer v3.2024; ESMO 2025",
        }

    # ── Locally advanced — TNT vs standard CRT ──
    tnt_candidate = is_tnt_candidate(i)
    ww_eligible = is_watch_and_wait_eligible(i)
    tnt_regimen = select_tnt_regimen(i)

    if i["priorPelvicRT"]:
        warnings.append(
            "Prior pelvic RT: re-irradiation carries significant toxicity risk — limit dose and discuss with radiation oncology"
        )
    if i["ibd"]:
        warnings.append(
            "IBD: increased radiation toxicity risk — consider surgery-first approach"
        )
    if i["msi_mmr"] == "MSI-H":
        warnings.append(
            "MSI-H/dMMR: consider immunotherapy (pembrolizumab) as neoadjuvant — NICHE-2 trial shows high pCR rates"
        )
    if i["tStage"] == "T4b":
        warnings.append(
            "T4b disease: multivisceral resection likely required — ensure surgical team experienced in en-bloc resection"
        )
    if i["surgicalFitness"] == "unfit":
        warnings.append(
            "Patient unfit for surgery: consider definitive CRT or watch-and-wait after TNT if cCR achieved"
        )
    if i["mrfStatus"] == "involved":
        warnings.append(
            "MRF involvement: R0 resection may require extended surgery — TNT to downstage is strongly recommended"
        )

    next_steps.append(
        "High-resolution MRI pelvis (3T preferred) for baseline staging"
    )
    next_steps.append(
        "Multidisciplinary tumor board discussion (surgery, radiation, medical oncology, radiology)"
    )
    if tnt_candidate:
        next_steps.append(f"Initiate TNT: {tnt_regimen['label']}")
        next_steps.append(
            "Response assessment MRI at 8-12 weeks after completion of TNT"
        )
        if ww_eligible:
            next_steps.append(
                "If cCR confirmed: discuss watch-and-wait with patient — strict surveillance protocol required"
            )
        else:
            next_steps.append("Plan TME surgery 6-12 weeks after completion of TNT")
    else:
        next_steps.append("Standard long-course CRT (45-50.4 Gy + capecitabine)")
        next_steps.append("Surgery (TME) 6-8 weeks after CRT completion")
    next_steps.append("Adjuvant chemotherapy discussion based on pathologic response")

    if organ_score >= 70:
        organ_label = "High — organ preservation likely achievable with cCR"
    elif organ_score >= 50:
        organ_label = "Moderate — organ preservation possible, depends on response"
    elif organ_score >= 30:
        organ_label = "Low-Moderate — surgery likely required"
    else:
        organ_label = "Low — surgery strongly recommended"

    return {
        "strategy": "tnt_preferred" if tnt_candidate else "tnt_alternative",
        "strategyLabel": "Total Neoadjuvant Therapy (TNT) — Preferred"
        if tnt_candidate
        else "Standard Neoadjuvant CRT → TME",
        "urgency": "urgent"
        if i["tStage"] == "T4b" and i["mrfStatus"] == "involved"
        else "routine",
        "tntRegimen": tnt_regimen["regimen"] if tnt_candidate else None,
        "tntRegimenLabel": tnt_regimen["label"] if tnt_candidate else None,
        "surgicalApproach": "apr" if i["tumorLocation"] == "lower" else "lar",
        "surgicalApproachLabel": "Abdominoperineal Resection (APR) or intersphincteric resection"
        if i["tumorLocation"] == "lower"
        else "Low Anterior Resection (LAR) with TME",
        "wwEligible": ww_eligible,
        "wwCriteria": [
            "Clinical complete response (cCR) confirmed on MRI + endoscopy",
            "No residual tumor on DRE",
            "Patient willing and able to comply with strict surveillance",
            "Surveillance: MRI + endoscopy Q3 months × 2 years, then Q6 months × 3 years",
        ]
        if ww_eligible
        else None,
        "organPreservationScore": organ_score,
        "organPreservationLabel": organ_label,
        "keyWarnings": warnings,
        "nextSteps": next_steps,
        "rationale": f"TNT preferred for high-risk locally advanced rectal cancer. {tnt_regimen['rationale']}"
        if tnt_candidate
        else "Standard neoadjuvant CRT followed by TME for intermediate-risk locally advanced rectal cancer.",
        "evidenceLevel": "Category 1" if tnt_candidate else "Category 2A",
        "guidelineSource": "NCCN Rectal Cancer v3.2024 (PMID: 39151454); ESMO Living Guideline 2025 (PMID: 40412553); ASCO 2025 (PMID: 39236282)",
    }


# ─── Presentation ─────────────────────────────────────────────────────────────
# No module-specific ``present()``: the generic mapper
# (app.recommendations.card.build_card) folds this engine's native output into
# the uniform RecommendationCard. ``organPreservationScore`` is recognised as a
# score (see card.SCORE_CONFIG), and the module ``EVIDENCE`` above is attached as
# the card's references.
