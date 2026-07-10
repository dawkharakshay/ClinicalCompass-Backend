"""Liver Tumor Clinical Compass — HCC / BCLC decision support.

Ported 1:1 from old_static_code/client/src/lib/liverTumorLogic.ts
(assessLiverTumor and its helpers classifyBCLC, isWithinMilan,
isResectionCandidate, isAblationCandidate, isTACECandidate).

Based on:
- EASL Clinical Practice Guidelines on HCC. J Hepatol. 2025;82(2):315-374 (PMID: 39690085)
- AASLD Practice Guidance on HCC. Hepatology 2025 (PMID: 39992051)
- ESMO Clinical Practice Guideline HCC 2025 (PMID: 39986353)
- BCLC 2022 staging system
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, to_bool

LOGIC_KEY = "livertumor"

# Static reference list surfaced as the card's "Supporting Guidelines & Evidence"
# section (auto-attached by app.recommendations.registry.get_evidence). Ported 1:1
# from old_static_code/client/src/pages/LiverTumorCompass.tsx `REFERENCES`.
EVIDENCE = [
    {
        "title": "EASL Clinical Practice Guidelines on HCC 2025",
        "source": "European Association for the Study of the Liver, 2025",
        "description": "Comprehensive guidelines on HCC surveillance, diagnosis, staging (BCLC), and treatment including resection, ablation, TACE, TARE, systemic therapy, and transplantation.",
        "pmid": "39690085",
    },
    {
        "title": "AASLD Practice Guidance on HCC 2025",
        "source": "American Association for the Study of Liver Diseases, 2025",
        "description": "Updated AASLD guidance covering BCLC staging, treatment allocation, and systemic therapy options for HCC.",
        "pmid": "39992051",
    },
    {
        "title": "ESMO Clinical Practice Guideline: HCC 2025",
        "source": "European Society for Medical Oncology, 2025",
        "description": "ESMO guideline covering systemic therapy, immunotherapy combinations, and treatment sequencing for advanced HCC.",
        "pmid": "39986353",
    },
    {
        "title": "IMbrave150 Trial: Atezolizumab + Bevacizumab for Advanced HCC",
        "source": "Finn RS et al. N Engl J Med. 2020",
        "description": "IMbrave150: atezolizumab + bevacizumab improved OS (HR 0.66) and PFS (HR 0.59) vs sorafenib as first-line therapy for advanced HCC.",
        "pmid": "31912578",
    },
    {
        "title": "HIMALAYA Trial: Durvalumab + Tremelimumab for Advanced HCC",
        "source": "Abou-Alfa GK et al. Nat Med. 2022",
        "description": "HIMALAYA: STRIDE regimen (durvalumab + tremelimumab) improved OS vs sorafenib (HR 0.78) as first-line therapy for advanced HCC.",
        "pmid": "35145305",
    },
    {
        "title": "KEYNOTE-177: Pembrolizumab for MSI-H/dMMR Metastatic Colorectal Cancer",
        "source": "André T et al. N Engl J Med. 2020",
        "description": "KEYNOTE-177: pembrolizumab superior to chemotherapy as first-line for MSI-H/dMMR mCRC (PFS HR 0.60).",
        "pmid": "32396838",
    },
]


def _num(x) -> float:
    """Numeric coercion preserving 0 (JS treats typed numbers literally).

    Form values arrive as strings; a missing/blank value becomes NaN, which in
    JS makes every numeric comparison false — replicate that with NaN.
    """
    v = parse_float(x)
    return v  # may be NaN; comparisons against NaN are False in Python too


def _str(x, default: str = "") -> str:
    return default if x is None else str(x)


# ─── BCLC Staging ────────────────────────────────────────────────────────────


def classify_bclc(input: dict) -> str:
    ecog_ps = _num(input.get("ecogPS"))
    child_pugh = _str(input.get("childPugh"))
    tumor_count = _num(input.get("tumorCount"))
    max_tumor_size = _num(input.get("maxTumorSize"))
    vascular_invasion = _str(input.get("vascularInvasion"))
    extrahepatic = to_bool(input.get("extrahepatic"))

    # Stage D: End-stage
    if child_pugh.startswith("C") or ecog_ps >= 3:
        return "D"

    # Stage C: Advanced
    if (
        vascular_invasion == "macro_main"
        or vascular_invasion == "macro_branch"
        or extrahepatic
        or ecog_ps >= 2
    ):
        return "C"

    # Stage 0: Very early
    if (
        tumor_count == 1
        and max_tumor_size <= 2
        and ecog_ps == 0
        and (child_pugh == "A5" or child_pugh == "A6")
    ):
        return "0"

    # Stage A: Early (single or up to 3 nodules ≤3 cm)
    if (tumor_count == 1 and max_tumor_size <= 5) or (
        tumor_count <= 3 and max_tumor_size <= 3
    ):
        if ecog_ps <= 1 and not child_pugh.startswith("C"):
            return "A"

    # Stage B: Intermediate (multinodular, preserved liver function)
    if tumor_count > 1 or (tumor_count == 1 and max_tumor_size > 5):
        if (
            ecog_ps <= 1
            and not child_pugh.startswith("C")
            and not vascular_invasion.startswith("macro")
            and not extrahepatic
        ):
            return "B"

    return "C"


def get_bclc_label(stage: str) -> str:
    return {
        "0": "BCLC 0 — Very Early HCC",
        "A": "BCLC A — Early HCC",
        "B": "BCLC B — Intermediate HCC",
        "C": "BCLC C — Advanced HCC",
        "D": "BCLC D — End-Stage HCC",
    }.get(stage, "")


def is_within_milan(input: dict) -> bool:
    tumor_count = _num(input.get("tumorCount"))
    max_tumor_size = _num(input.get("maxTumorSize"))
    return (tumor_count == 1 and max_tumor_size <= 5) or (
        tumor_count <= 3 and max_tumor_size <= 3
    )


def is_resection_candidate(input: dict) -> bool:
    child_pugh = _str(input.get("childPugh"))
    portal_htn = _str(input.get("portalHTN"))
    ecog_ps = _num(input.get("ecogPS"))
    vascular_invasion = _str(input.get("vascularInvasion"))
    extrahepatic = to_bool(input.get("extrahepatic"))
    future_liver_remnant = _num(input.get("futureLiverRemnant"))

    if extrahepatic:
        return False
    if vascular_invasion == "macro_main":
        return False
    if ecog_ps >= 2:
        return False
    if child_pugh.startswith("C"):
        return False
    # Major resection contraindicated with significant portal HTN + Child-Pugh B
    if portal_htn == "severe" and child_pugh.startswith("B"):
        return False
    # FLR <30% is a contraindication for major resection
    if future_liver_remnant > 0 and future_liver_remnant < 30:
        return False
    return True


def is_ablation_candidate(input: dict) -> bool:
    tumor_count = _num(input.get("tumorCount"))
    max_tumor_size = _num(input.get("maxTumorSize"))
    child_pugh = _str(input.get("childPugh"))
    ecog_ps = _num(input.get("ecogPS"))

    if ecog_ps >= 2:
        return False
    if child_pugh.startswith("C"):
        return False
    # Standard ablation criteria: ≤3 cm (optimal), up to 5 cm with MWA
    if max_tumor_size > 5:
        return False
    if tumor_count > 3:
        return False
    return True


def is_tace_candidate(input: dict) -> bool:
    child_pugh = _str(input.get("childPugh"))
    ecog_ps = _num(input.get("ecogPS"))
    vascular_invasion = _str(input.get("vascularInvasion"))
    tace_suitability = _str(input.get("taceSuitability"))
    extrahepatic = to_bool(input.get("extrahepatic"))

    if extrahepatic:
        return False
    if child_pugh.startswith("C"):
        return False
    if ecog_ps >= 2:
        return False
    if vascular_invasion == "macro_main":
        return False
    if tace_suitability != "suitable":
        return False
    return True


# ─── Main Assessment Function ────────────────────────────────────────────────


def assess(data: dict) -> dict:
    bclc_stage = classify_bclc(data)
    bclc_label = get_bclc_label(bclc_stage)
    warnings: list[str] = []
    next_steps: list[str] = []

    afp_level = _num(data.get("afpLevel"))
    vascular_invasion = _str(data.get("vascularInvasion"))
    adjacent_vessel = to_bool(data.get("adjacentVessel"))
    peri_hilar = to_bool(data.get("periHilar"))
    child_pugh = _str(data.get("childPugh"))
    portal_htn = _str(data.get("portalHTN"))
    tumor_count = _num(data.get("tumorCount"))
    max_tumor_size = _num(data.get("maxTumorSize"))
    transplant_eligible = to_bool(data.get("transplantEligible"))
    milan_criteria = to_bool(data.get("milanCriteria"))
    tace_suitability = _str(data.get("taceSuitability"))

    # AFP warning
    if afp_level > 1000:
        warnings.append(
            "AFP >1,000 ng/mL: absolute contraindication to liver transplantation per EASL 2025 (unless AFP drops to <1,000 for ≥3 months after downstaging)"
        )
    if afp_level > 400:
        warnings.append(
            "AFP >400 ng/mL: associated with high risk of recurrence after resection — consider adjuvant therapy discussion"
        )
    if vascular_invasion != "none":
        warnings.append(
            f"Vascular invasion ({vascular_invasion}): significantly impacts prognosis and treatment selection"
        )
    if adjacent_vessel:
        warnings.append(
            "Tumor adjacent to major vessel: ablation has higher risk of incomplete treatment (heat-sink effect) — consider resection or SBRT"
        )
    if peri_hilar:
        warnings.append(
            "Perihilar location: ablation carries risk of biliary injury — consider SBRT or resection"
        )

    # ── BCLC D: End-stage ──
    if bclc_stage == "D":
        return {
            "bclcStage": bclc_stage,
            "bclcLabel": bclc_label,
            "primaryModality": "best_supportive_care",
            "primaryModalityLabel": "Best Supportive Care / Palliative",
            "alternativeModalities": [],
            "alternativeModalityLabels": [],
            "keyWarnings": [
                *warnings,
                "Child-Pugh C or ECOG ≥3: curative/palliative liver-directed therapy not recommended",
            ],
            "nextSteps": [
                "Palliative care referral",
                "Liver transplant evaluation if Child-Pugh C due to cirrhosis (not tumor burden)",
                "Symptom management",
                "Nutritional support",
            ],
            "rationale": "BCLC D (end-stage): median survival <3 months. Active treatment does not improve survival. Best supportive care is recommended per EASL 2025.",
            "evidenceLevel": "1A",
            "guidelineSource": "EASL 2025 (PMID: 39690085); AASLD 2025 (PMID: 39992051)",
        }

    # ── BCLC C: Advanced ──
    if bclc_stage == "C":
        systemic_regimen = (
            "Atezolizumab + Bevacizumab (IMbrave150) or Durvalumab + Tremelimumab (HIMALAYA) — first-line"
            if vascular_invasion == "macro_branch" or vascular_invasion == "macro_main"
            else "Atezolizumab + Bevacizumab (IMbrave150) — first-line; Lenvatinib or Sorafenib if IO contraindicated"
        )
        return {
            "bclcStage": bclc_stage,
            "bclcLabel": bclc_label,
            "primaryModality": "systemic_first_line",
            "primaryModalityLabel": "Systemic Therapy (Immunotherapy-Based)",
            "alternativeModalities": ["sbrt"]
            if vascular_invasion == "macro_branch"
            else [],
            "alternativeModalityLabels": [
                "SBRT (for segmental/lobar PVI without extrahepatic disease)"
            ]
            if vascular_invasion == "macro_branch"
            else [],
            "systemicRegimen": systemic_regimen,
            "keyWarnings": [
                w
                for w in [
                    *warnings,
                    "Advanced HCC: TACE not recommended as standard — systemic therapy preferred per EASL 2025",
                    "Segmental/lobar portal vein invasion: SBRT may be considered but cannot be recommended over systemic IO-based therapy"
                    if vascular_invasion == "macro_branch"
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "PD-L1 testing and hepatitis B/C viral load",
                "Atezolizumab + Bevacizumab: screen for esophageal varices before starting (endoscopy if not done in past 6 months)",
                "Baseline CT chest/abdomen/pelvis for staging",
                "Multidisciplinary tumor board discussion",
                "Consider SBRT for portal vein involvement if systemic therapy contraindicated",
            ],
            "rationale": "BCLC C: systemic therapy with atezolizumab+bevacizumab is first-line (IMbrave150: OS HR 0.66, PFS HR 0.59 vs sorafenib). HIMALAYA (durvalumab+tremelimumab) is an alternative.",
            "evidenceLevel": "1A",
            "guidelineSource": "EASL 2025 (PMID: 39690085); ESMO 2025 (PMID: 39986353)",
        }

    # ── BCLC B: Intermediate ──
    if bclc_stage == "B":
        tace_candidate = is_tace_candidate(data)
        primary_modality = "tace" if tace_candidate else "tare_y90"
        alternatives = (
            ["tare_y90", "sbrt"]
            if tace_candidate
            else ["sbrt", "systemic_first_line"]
        )
        result = {
            "bclcStage": bclc_stage,
            "bclcLabel": bclc_label,
            "primaryModality": primary_modality,
            "primaryModalityLabel": "TACE (cTACE or DEB-TACE) — preferred for liver-confined intermediate HCC"
            if tace_candidate
            else "TARE/Y-90 (SIRT) — alternative when TACE unsuitable",
            "alternativeModalities": alternatives,
            "alternativeModalityLabels": [
                "TARE/Y-90 (SIRT) — alternative to TACE",
                "SBRT — for selected patients unsuitable for TACE/TARE",
            ]
            if tace_candidate
            else ["SBRT", "Systemic therapy (if lobar TARE not feasible)"],
            "keyWarnings": [
                w
                for w in [
                    *warnings,
                    f"TACE unsuitable: {tace_suitability.replace('_', ' ')} — consider TARE/Y-90 or systemic therapy"
                    if not tace_candidate
                    else "",
                    "Child-Pugh B: increased risk of hepatic decompensation after TACE — consider TARE or systemic therapy"
                    if child_pugh.startswith("B")
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "Multidisciplinary tumor board discussion (hepatology, IR, oncology, surgery)",
                "Plan TACE: selective approach preferred (cTACE or DEB-TACE — equivalent per EASL 2025)"
                if tace_candidate
                else "Plan TARE/Y-90: lobar approach if feasible",
                "Liver function assessment: Child-Pugh, ALBI, bilirubin",
                "Assess for transplant eligibility if within Milan criteria",
                "Response assessment: mRECIST at 4-6 weeks post-TACE",
            ],
            "rationale": "BCLC B: TACE is preferred for liver-confined intermediate HCC with preserved portal flow. TARE/Y-90 is an alternative when TACE is unsuitable. Per EASL 2025: TACE should be preferred to systemic therapy for liver-confined disease when selective approach is possible.",
            "evidenceLevel": "1A",
            "guidelineSource": "EASL 2025 (PMID: 39690085); AASLD 2025 (PMID: 39992051)",
        }
        if transplant_eligible and milan_criteria:
            result["transplantBridge"] = (
                "TACE or TARE as bridge to transplant — maintain within Milan criteria"
            )
        return result

    # ── BCLC A: Early ──
    resection_candidate = is_resection_candidate(data)
    ablation_candidate = is_ablation_candidate(data)

    # Very early (BCLC 0) or solitary ≤2 cm
    if bclc_stage == "0" or (tumor_count == 1 and max_tumor_size <= 2):
        prefer_resection = (
            resection_candidate and not adjacent_vessel and portal_htn == "none"
        )
        primary = (
            "resection"
            if prefer_resection
            else "ablation_rfa"
            if ablation_candidate
            else "transplant"
        )
        result = {
            "bclcStage": bclc_stage,
            "bclcLabel": bclc_label,
            "primaryModality": primary,
            "primaryModalityLabel": "Liver Resection (preferred for non-cirrhotic or well-compensated cirrhosis)"
            if primary == "resection"
            else "Thermal Ablation (RFA or MWA) — equivalent to resection for ≤2 cm"
            if primary == "ablation_rfa"
            else "Liver Transplantation",
            "alternativeModalities": ["ablation_rfa", "transplant"]
            if prefer_resection
            else ["resection", "transplant"]
            if resection_candidate
            else ["ablation_rfa"],
            "alternativeModalityLabels": [
                "Thermal Ablation (RFA/MWA) — equivalent to resection for ≤2 cm per EASL 2025",
                "Liver Transplantation (if not candidate for resection/ablation)",
            ]
            if prefer_resection
            else ["Resection (if portal HTN resolves)", "Liver Transplantation"],
            "keyWarnings": [
                w
                for w in [
                    *warnings,
                    "Tumor adjacent to vessel: heat-sink effect reduces ablation efficacy — consider resection or SBRT"
                    if adjacent_vessel
                    else "",
                    "Clinically significant portal HTN: limit resection to minor hepatectomy (≤2 segments) — avoid major resection per EASL 2025"
                    if portal_htn == "severe" and resection_candidate
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "Liver volumetry (CT/MRI) if resection planned — ensure FLR ≥30%",
                "Minimally invasive resection (laparoscopic/robotic) preferred if technically feasible"
                if prefer_resection
                else "Thermal ablation: RFA for ≤3 cm, MWA for 3-5 cm or near vessels",
                "Transplant evaluation if not candidate for resection or ablation",
                "Surveillance: CT/MRI Q3 months × 2 years after treatment",
            ],
            "rationale": "BCLC 0/A: resection and ablation are recommended without preference for solitary HCC ≤2 cm per EASL 2025. For non-cirrhotic liver, resection is preferred. Transplant for patients not eligible for resection/ablation within Milan criteria.",
            "evidenceLevel": "1A",
            "guidelineSource": "EASL 2025 (PMID: 39690085); AASLD 2025 (PMID: 39992051)",
        }
        if transplant_eligible:
            result["transplantBridge"] = (
                "Ablation as bridge to transplant — maintain within Milan criteria"
            )
        return result

    # BCLC A: single >2 cm or up to 3 nodules ≤3 cm
    prefer_resection = resection_candidate and tumor_count == 1
    primary = (
        "resection"
        if prefer_resection
        else "ablation_rfa"
        if (ablation_candidate and max_tumor_size <= 3)
        else "transplant"
        if (transplant_eligible and milan_criteria)
        else "tace"
    )

    next_steps.append("Multidisciplinary tumor board discussion")
    next_steps.append("Liver volumetry if resection planned (FLR ≥30% required)")
    if prefer_resection:
        next_steps.append(
            "Minimally invasive resection — laparoscopic/robotic preferred"
        )
        next_steps.append(
            "Adjuvant therapy discussion: IMbrave050 did not show sustained benefit — active surveillance preferred"
        )
    if ablation_candidate and max_tumor_size <= 3:
        next_steps.append(
            "Thermal ablation: RFA (≤3 cm) or MWA (3-5 cm) — plan under imaging guidance"
        )
    if transplant_eligible and milan_criteria:
        next_steps.append(
            "List for liver transplantation — bridge therapy (TACE/ablation) to maintain within Milan criteria"
        )

    result = {
        "bclcStage": bclc_stage,
        "bclcLabel": bclc_label,
        "primaryModality": primary,
        "primaryModalityLabel": "Liver Resection (preferred for single HCC >2 cm with preserved liver function)"
        if primary == "resection"
        else "Thermal Ablation (RFA/MWA) — for ≤3 cm or when resection not feasible"
        if primary == "ablation_rfa"
        else "Liver Transplantation (within Milan criteria)"
        if primary == "transplant"
        else "TACE (bridge to transplant or for multinodular disease)",
        "alternativeModalities": ["ablation_rfa", "transplant", "sbrt"]
        if prefer_resection
        else ["resection", "transplant", "sbrt"],
        "alternativeModalityLabels": [
            "Thermal Ablation (RFA/MWA)",
            "Liver Transplantation (if within Milan criteria)",
            "SBRT (if ablation not feasible)",
        ]
        if prefer_resection
        else ["Resection (if liver function improves)", "Liver Transplantation", "SBRT"],
        "keyWarnings": [
            w
            for w in [
                *warnings,
                "Clinically significant portal HTN: major resection contraindicated — consider ablation or transplant"
                if portal_htn == "severe" and prefer_resection
                else "",
                "Tumor >3 cm: ablation has higher local recurrence risk — MWA preferred over RFA, or consider resection/SBRT"
                if max_tumor_size > 3 and ablation_candidate
                else "",
            ]
            if w
        ],
        "nextSteps": next_steps,
        "rationale": "BCLC A: resection is preferred for single HCC >2 cm with preserved liver function. Ablation is equivalent to resection for ≤2 cm. Transplant for patients within Milan criteria not eligible for resection/ablation.",
        "evidenceLevel": "1A",
        "guidelineSource": "EASL 2025 (PMID: 39690085); AASLD 2025 (PMID: 39992051); ESMO 2025 (PMID: 39986353)",
    }
    if transplant_eligible and milan_criteria:
        result["transplantBridge"] = "TACE or ablation as bridge to transplant"
    return result
