"""Amyloidosis Diagnostic Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/amyloidosisLogic.ts
(assessAmyloidosis, detectRedFlags, getALStage, getALStageLabel).

Sources (per TS header):
  Gertz MA et al. ASH 2020; Gillmore JD et al. Lancet 2022 (PMID 35240070);
  Garcia-Pavia P et al. Eur Heart J 2021 (PMID 33789347);
  Maurer MS et al. NEJM 2018 (PMID 30145929); Benson MD et al. NEJM 2019;
  Kastritis E et al. NEJM 2021 (PMID 33951374); Palladini G / Mayo 2012.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "amyloidosis"


_AL_STAGE_LABEL = {
    "stage1": "Stage I (Median OS >5 years)",
    "stage2": "Stage II (Median OS ~40 months)",
    "stage3": "Stage III (Median OS ~14 months)",
    "stage3b": "Stage IIIb (Median OS ~6 months) — Very High Risk",
}


def _get_al_stage(ntpro_bnp: float, troponin_t: float, egfr: float) -> str:
    # Mayo 2012 staging (Dispenzieri A et al.)
    high_nt = ntpro_bnp >= 1800
    high_tn = troponin_t >= 25
    low_egfr = egfr < 50

    score = sum(1 for x in (high_nt, high_tn, low_egfr) if x)
    if score == 0:
        return "stage1"
    if score == 1:
        return "stage2"
    if score == 2:
        return "stage3"
    return "stage3b"  # All 3 — very high risk


def _get_al_stage_label(stage: str) -> str:
    return _AL_STAGE_LABEL[stage]


def _detect_red_flags(data: dict) -> list[str]:
    symptoms = data.get("symptoms") or {}
    age = num(data.get("age"), 0)
    flags: list[str] = []

    if truthy(symptoms.get("unexplainedHypertrophicCM")) and truthy(symptoms.get("lowVoltageECG")):
        flags.append(
            "CRITICAL: Hypertrophic cardiomyopathy + low-voltage ECG — classic ATTR-CM pattern. "
            "Urgent cardiac amyloidosis workup required."
        )
    if truthy(symptoms.get("bilateralCarpalTunnel")) and age > 60:
        flags.append(
            "Bilateral carpal tunnel syndrome in older adult: Soft tissue amyloid deposition — screen for ATTR."
        )
    if truthy(symptoms.get("spinalStenosis")) and truthy(symptoms.get("bilateralCarpalTunnel")):
        flags.append(
            "Carpal tunnel + spinal stenosis: High specificity for ATTR amyloidosis. "
            "Proceed with cardiac imaging and bone scan."
        )
    if truthy(symptoms.get("macroglossia")):
        flags.append(
            "Macroglossia: Highly specific for AL amyloidosis. Urgent SPEP/SFLC and bone marrow biopsy."
        )
    if truthy(symptoms.get("periorbitalPurpura")):
        flags.append(
            "Periorbital purpura ('raccoon eyes'): Pathognomonic for AL amyloidosis. Urgent AL workup."
        )
    if num(data.get("echoLVWallThickness"), 0) >= 15 and truthy(symptoms.get("heartFailure")):
        flags.append(
            "LV wall thickness ≥15 mm with heart failure: High suspicion for cardiac amyloidosis."
        )
    if truthy(symptoms.get("peripheralNeuropathy")) and truthy(symptoms.get("autonomicDysfunction")):
        flags.append(
            "Peripheral + autonomic neuropathy: Characteristic of hereditary ATTR (hATTR) or AL "
            "amyloidosis. Genetic testing and nerve biopsy recommended."
        )
    if truthy(symptoms.get("nephrotic")) and truthy(data.get("hasMGUS")):
        flags.append(
            "Nephrotic syndrome + MGUS: High suspicion for AL amyloidosis with renal involvement. "
            "Kidney biopsy recommended."
        )
    if data.get("ethnicity") == "african_american" and age >= 60 and truthy(symptoms.get("heartFailure")):
        flags.append(
            "African American patient ≥60 with heart failure: V122I TTR mutation prevalence ~3–4%. "
            "Genetic testing for TTR V122I strongly recommended."
        )

    return flags


def assess(data: dict) -> dict:
    symptoms = data.get("symptoms") or {}
    red_flags = _detect_red_flags(data)
    key_warnings: list[str] = []
    next_diagnostic_steps: list[str] = []

    amyloid_type = data.get("amyloidType")
    biopsy_result = data.get("biopsyResult")
    ntpro_bnp = num(data.get("ntproBNP"), 0)
    troponin_t = num(data.get("troponinT"), 0)
    egfr = num(data.get("egfr"), 0)
    ecog_ps = num(data.get("ecogPS"), 0)
    nyha_class = num(data.get("nyhaClass"), 0)
    lv_wall = num(data.get("echoLVWallThickness"), 0)

    # ── BSC ──────────────────────────────────────────────────────────────────
    if data.get("patientPreference") == "bsc" or ecog_ps == 4:
        return {
            "diagnosticConfidence": "suspected",
            "suspectedType": amyloid_type,
            "diagnosticLabel": "Best Supportive Care",
            "diagnosticRationale": "Patient preference or ECOG PS 4.",
            "nextDiagnosticSteps": [],
            "treatmentRecommendation": "Supportive care: Diuretics for heart failure, pain management, nutritional support.",
            "treatmentRationale": "Goals-of-care focused management.",
            "stagingInfo": "",
            "keyWarnings": ["Ensure goals-of-care discussion is documented."],
            "redFlags": red_flags,
            "urgencyFlag": "routine",
        }

    # ── Confirmed AL Amyloidosis ──────────────────────────────────────────────
    if amyloid_type == "al_amyloidosis" or biopsy_result == "positive_al":
        al_stage = _get_al_stage(ntpro_bnp, troponin_t, egfr)
        al_stage_label = _get_al_stage_label(al_stage)

        is_transplant_eligible = (
            ecog_ps <= 2
            and nyha_class <= 2
            and ntpro_bnp < 8500
            and troponin_t < 60
            and egfr >= 30
        )

        if al_stage == "stage3b":
            treatment_rec = (
                "Daratumumab + VCd (Dara-VCd) — ANDROMEDA Trial. Stage IIIb: Avoid ASCT. "
                "Dara-VCd is standard of care (Kastritis E et al., NEJM 2021, PMID 33951374). "
                "ORR 91.3%, hematologic CR 53%."
            )
        elif is_transplant_eligible:
            treatment_rec = (
                "Daratumumab + VCd (Dara-VCd) induction → Autologous Stem Cell Transplant (ASCT) "
                "for eligible patients. ASCT achieves highest rates of hematologic CR and organ response."
            )
        else:
            treatment_rec = (
                "Daratumumab + VCd (Dara-VCd) — ANDROMEDA regimen. Standard of care for "
                "transplant-ineligible AL amyloidosis. Dara-VCd superior to VCd alone (ANDROMEDA trial)."
            )

        if al_stage == "stage3b":
            key_warnings.append(
                "Stage IIIb AL Amyloidosis: Very poor prognosis (median OS ~6 months). Avoid "
                "cardiotoxic agents. Dara-VCd is preferred. Avoid ASCT."
            )
        if truthy(symptoms.get("heartFailure")) and nyha_class >= 3:
            key_warnings.append(
                "Advanced cardiac involvement (NYHA III-IV): Avoid ACE inhibitors, ARBs, beta-blockers, "
                "and calcium channel blockers — may cause severe hypotension. Use diuretics cautiously."
            )

        return {
            "diagnosticConfidence": "confirmed",
            "suspectedType": "al_amyloidosis",
            "diagnosticLabel": "AL Amyloidosis (Light Chain Amyloidosis)",
            "diagnosticRationale": (
                "Biopsy-proven AL amyloidosis or confirmed plasma cell dyscrasia with amyloid deposits. "
                "Congo red staining with apple-green birefringence + immunofluorescence/immunohistochemistry "
                "for light chain typing."
            ),
            "nextDiagnosticSteps": [
                "Bone marrow biopsy with plasma cell quantification and light chain restriction",
                "Echocardiogram with strain imaging (GLS, apical sparing)",
                "24-hour urine protein electrophoresis",
                "Mayo 2012 staging: NT-proBNP, hsTnT, eGFR",
                "Cardiac MRI with gadolinium (if eGFR permits)",
                "Assess ASCT eligibility: ECOG PS, NYHA class, NT-proBNP, hsTnT, eGFR",
            ],
            "treatmentRecommendation": treatment_rec,
            "treatmentRationale": (
                "ANDROMEDA trial (Kastritis E et al., NEJM 2021): Daratumumab + VCd vs VCd alone — "
                "91.3% vs 76.9% hematologic response; 53% vs 18% hematologic CR. Dara-VCd is now "
                "standard of care for newly diagnosed AL amyloidosis."
            ),
            "stagingInfo": f"Mayo 2012 Stage: {al_stage_label}",
            "keyWarnings": key_warnings,
            "redFlags": red_flags,
            "urgencyFlag": "emergent" if al_stage == "stage3b" else "urgent",
        }

    # ── Confirmed ATTR Amyloidosis ────────────────────────────────────────────
    if (
        amyloid_type == "attr_wt"
        or amyloid_type == "attr_hereditary"
        or biopsy_result == "positive_attr"
    ):
        is_hereditary = (
            amyloid_type == "attr_hereditary"
            or data.get("ttrGeneticTest") == "positive_pathogenic"
        )
        has_neuropathy = truthy(symptoms.get("peripheralNeuropathy")) or truthy(
            symptoms.get("autonomicDysfunction")
        )
        has_cardiomyopathy = truthy(symptoms.get("heartFailure")) or lv_wall >= 12

        # Non-biopsy diagnosis criteria (Gillmore 2022)
        bone_scan = data.get("boneScanResult")
        non_biopsy_diagnosis = bone_scan == "grade2" or bone_scan == "grade3"
        mgus_excluded = (not truthy(data.get("hasMGUS"))) and data.get("sflcRatio") == "normal"
        non_biopsy_attr = non_biopsy_diagnosis and mgus_excluded

        if biopsy_result == "positive_attr":
            diagnostic_confidence = "confirmed"
        elif non_biopsy_attr:
            diagnostic_confidence = "highly_likely"
        else:
            diagnostic_confidence = "suspected"

        if is_hereditary and has_neuropathy:
            treatment_rec = (
                "Patisiran (Onpattro) or Vutrisiran (Amvuttra) — siRNA gene silencing. First-line "
                "for hATTR polyneuropathy. Inotersen (Tegsedi) is an alternative (antisense oligonucleotide)."
            )
            treatment_rationale = (
                "APOLLO trial (Benson MD et al., NEJM 2019, PMID 29972757): Patisiran reduced "
                "neuropathy progression vs placebo. Vutrisiran (HELIOS-A, PMID 34126015): Non-inferior "
                "to patisiran with quarterly SC dosing. Both are FDA-approved for hATTR polyneuropathy."
            )
        elif has_cardiomyopathy:
            treatment_rec = (
                "Tafamidis (Vyndaqel/Vyndamax) — TTR stabilizer. Standard of care for ATTR-CM (both wt "
                "and hereditary). Acoramidis (Attruby) is an alternative TTR stabilizer approved 2024."
            )
            treatment_rationale = (
                "ATTR-ACT trial (Maurer MS et al., NEJM 2018, PMID 30145929): Tafamidis reduced "
                "all-cause mortality (29.5% vs 42.9%) and CV hospitalizations vs placebo in ATTR-CM. "
                "FDA-approved for ATTR-CM (wt and hereditary). Acoramidis (ATTRibute-CM, PMID 38739481) "
                "approved 2024."
            )
        elif is_hereditary:
            treatment_rec = (
                "Tafamidis (Vyndaqel/Vyndamax) for cardiac involvement. Patisiran or vutrisiran for "
                "neuropathy. Initiate based on predominant organ involvement."
            )
            treatment_rationale = (
                "hATTR with mixed phenotype: Treat predominant organ involvement. Both TTR stabilizers "
                "and gene silencing agents are approved."
            )
        else:
            treatment_rec = (
                "Tafamidis (Vyndaqel/Vyndamax) — Standard of care for wt-ATTR cardiomyopathy."
            )
            treatment_rationale = (
                "Wild-type ATTR-CM: Tafamidis is the only FDA-approved therapy. Early initiation "
                "improves outcomes."
            )

        ttr_mutation = data.get("ttrMutation")
        if ttr_mutation == "val122ile":
            key_warnings.append(
                "V122I TTR mutation (Val122Ile): Most common hereditary ATTR in African Americans "
                "(~3–4% prevalence). Predominantly cardiac phenotype. Tafamidis is the preferred treatment."
            )
        if ttr_mutation == "val30met":
            key_warnings.append(
                "V30M TTR mutation (Val30Met): Most common hereditary ATTR worldwide. Predominantly "
                "neuropathic phenotype. Patisiran or vutrisiran preferred for neuropathy; tafamidis for "
                "cardiac involvement."
            )

        next_steps: list[str] = []
        if data.get("ttrGeneticTest") == "not_done":
            next_steps.append(
                "TTR genetic testing (all ATTR patients) — identifies hereditary vs wt-ATTR and guides "
                "therapy selection"
            )
        if bone_scan == "not_done":
            next_steps.append(
                "Tc-99m PYP/DPD bone scan (Perugini score) — non-biopsy ATTR-CM diagnosis if grade 2–3 "
                "+ MGUS excluded"
            )
        next_steps.append("Echocardiogram with strain imaging (GLS, apical sparing pattern)")
        next_steps.append("Cardiac MRI with gadolinium (late gadolinium enhancement pattern)")
        next_steps.append("NT-proBNP and hsTnT for staging and monitoring")
        if is_hereditary:
            next_steps.append("Family screening with TTR genetic testing (autosomal dominant)")
        if has_neuropathy:
            next_steps.append("Nerve conduction studies / EMG")
            next_steps.append("Autonomic testing")

        return {
            "diagnosticConfidence": diagnostic_confidence,
            "suspectedType": "attr_hereditary" if is_hereditary else "attr_wt",
            "diagnosticLabel": (
                "Hereditary ATTR Amyloidosis (hATTR)"
                if is_hereditary
                else "Wild-Type ATTR Amyloidosis (wt-ATTR / Senile Cardiac Amyloidosis)"
            ),
            "diagnosticRationale": (
                "Non-biopsy diagnosis criteria met (Gillmore JD et al., Lancet 2022): Bone scan grade 2–3 "
                "+ no MGUS/abnormal SFLC ratio. Biopsy not required for ATTR-CM diagnosis."
                if non_biopsy_attr
                else "Biopsy-proven ATTR amyloidosis with Congo red staining and mass spectrometry typing."
            ),
            "nextDiagnosticSteps": next_steps,
            "treatmentRecommendation": treatment_rec,
            "treatmentRationale": treatment_rationale,
            "stagingInfo": (
                f"NYHA Class: {data.get('nyhaClass')} | LV Wall Thickness: "
                f"{data.get('echoLVWallThickness')} mm | NT-proBNP: {data.get('ntproBNP')} pg/mL"
            ),
            "keyWarnings": key_warnings,
            "redFlags": red_flags,
            "urgencyFlag": "urgent" if nyha_class >= 3 else "routine",
        }

    # ── Unknown / Suspected — Diagnostic Workup ───────────────────────────────
    red_flag_count = len(red_flags)
    diagnostic_confidence = "suspected" if red_flag_count >= 3 else "low_suspicion"

    # Build diagnostic pathway
    if truthy(data.get("hasMGUS")) or data.get("sflcRatio") == "abnormal":
        next_diagnostic_steps.append(
            "MGUS/abnormal SFLC: Prioritize AL amyloidosis workup — bone marrow biopsy, fat pad biopsy, "
            "24-hour urine protein electrophoresis."
        )
    if truthy(symptoms.get("heartFailure")) or lv_wall >= 12:
        next_diagnostic_steps.append(
            "Cardiac involvement suspected: Tc-99m PYP/DPD bone scan + SPEP/SFLC to differentiate ATTR vs AL."
        )
        next_diagnostic_steps.append(
            "Echocardiogram with strain imaging (apical sparing = ATTR pattern)."
        )
        next_diagnostic_steps.append("Cardiac MRI with gadolinium if eGFR permits.")
    if truthy(symptoms.get("peripheralNeuropathy")) or truthy(symptoms.get("autonomicDysfunction")):
        next_diagnostic_steps.append(
            "Neuropathy workup: TTR genetic testing, nerve conduction studies, autonomic testing. "
            "Consider nerve biopsy if diagnosis unclear."
        )
    if len(next_diagnostic_steps) == 0:
        next_diagnostic_steps.append(
            "Complete amyloidosis screening: SPEP, SFLC ratio, 24-hour urine protein electrophoresis."
        )
        next_diagnostic_steps.append("Echocardiogram with strain imaging.")
        next_diagnostic_steps.append("TTR genetic testing if age >60 or African American.")
        next_diagnostic_steps.append(
            "Consider fat pad biopsy (sensitivity ~80% for AL, ~45% for ATTR)."
        )

    return {
        "diagnosticConfidence": diagnostic_confidence,
        "suspectedType": "unknown",
        "diagnosticLabel": (
            "Amyloidosis Suspected — Urgent Workup Required"
            if red_flag_count >= 3
            else "Low Suspicion — Screening Recommended"
        ),
        "diagnosticRationale": (
            f"{red_flag_count} red flag(s) identified. Systematic amyloidosis workup is recommended to "
            "confirm or exclude diagnosis."
            if red_flag_count >= 3
            else "Insufficient features to confirm amyloidosis. Consider screening if clinical suspicion remains."
        ),
        "nextDiagnosticSteps": next_diagnostic_steps,
        "treatmentRecommendation": (
            "Complete diagnostic workup before initiating therapy. Treatment depends on amyloid type "
            "(AL vs ATTR)."
        ),
        "treatmentRationale": (
            "Mistyping amyloid subtype leads to incorrect treatment — AL therapy (chemotherapy) is "
            "harmful in ATTR and vice versa."
        ),
        "stagingInfo": "",
        "keyWarnings": [
            *key_warnings,
            "CRITICAL: Always type the amyloid before treating. Congo red + mass spectrometry (or "
            "immunofluorescence) is required. Treating AL as ATTR (or vice versa) can be fatal.",
        ],
        "redFlags": red_flags,
        "urgencyFlag": "urgent" if red_flag_count >= 3 else "routine",
    }
