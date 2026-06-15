"""Y-90 Radioembolization Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/y90Logic.ts (assessY90Candidacy).
Based on EASL 2024, AASLD 2023, SIR Guidelines 2024.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "y90"

_FOLLOW_UP_SCHEDULE = [
    "4-6 weeks post-Y90: Clinical assessment, labs (bilirubin, albumin, INR)",
    "8-12 weeks: Imaging (CT/MRI) to assess treatment response",
    "3-6 months: Repeat imaging and tumor markers",
    "Every 3 months: Ongoing surveillance per AASLD/EASL guidelines",
]

_REFERENCES = [
    "EASL Clinical Practice Guidelines: HCC (2024 Update)",
    "AASLD Guidance: HCC (2023)",
    "LEGACY Trial (Lewandowski et al., 2023)",
    "YES-P Trial (Salem et al., 2024)",
    "SIR Guidelines for Y90 Radioembolization (2024)",
    "DOSISPHERE-01 Trial (Garin et al., 2021)",
    "2025 TheraSphere Global Steering Committee Recommendations",
]


def assess(data: dict) -> dict:
    contraindications: list[str] = []
    recommendations: list[str] = []
    candidacy = "caution"
    dosimetry_notes = ""
    summary = ""

    diagnosis = data.get("diagnosis")
    bclc_stage = data.get("bclcStage")
    tace_feasibility = data.get("taceFeasibility")
    portal_vein = data.get("portalVeinInvolvement")
    icca_line = data.get("iccaTreatmentLine")

    # tumorSize / tumorCount: JS treats them as numbers with `&&` truthiness.
    tumor_size = parse_float(data.get("tumorSize"))  # NaN when absent
    tumor_count = parse_float(data.get("tumorCount"))

    # HCC assessment pathway
    if diagnosis == "hcc":
        # BCLC-D: Not eligible
        if bclc_stage == "d":
            candidacy = "not-eligible"
            summary = (
                "Y90 is not indicated in BCLC-D (Child-Pugh C, ECOG PS >2). "
                "Best supportive care recommended."
            )
            contraindications.append("BCLC-D stage with terminal liver disease")
            contraindications.append("Child-Pugh C cirrhosis")
            contraindications.append("ECOG performance status >2")
        # BCLC 0/A: Early stage
        elif bclc_stage == "0" or bclc_stage == "a":
            if truthy(tumor_size) and tumor_size <= 5 and tumor_count == 1:
                candidacy = "eligible"
                summary = (
                    "Y90 radiation segmentectomy is indicated for solitary HCC "
                    "≤5 cm in non-surgical candidates (LEGACY Trial)."
                )
                dosimetry_notes = (
                    "Target dose ≥400 Gy (glass) or ≥150 Gy (resin) to "
                    "treated segment. Complete pathologic necrosis rates ~50-60%."
                )
                recommendations.append("Superselective catheterization technique")
                recommendations.append("Personalized dosimetry planning")
                recommendations.append("Consider bridge-to-transplant strategy")
            elif truthy(tumor_size) and tumor_size > 5:
                candidacy = "caution"
                summary = (
                    "Tumor >5 cm may require radiation lobectomy. Requires "
                    "adequate future liver remnant (FLR)."
                )
                contraindications.append("Inadequate future liver remnant (<25%)")
                recommendations.append("Volumetric assessment for lobectomy")
                recommendations.append("Contralateral hypertrophy monitoring (6-8 weeks)")
        # BCLC B: Intermediate stage
        elif bclc_stage == "b":
            if tace_feasibility == "eligible":
                candidacy = "caution"
                summary = (
                    "TACE remains standard first-line for BCLC-B. Y90 is alternative "
                    "for large (>5 cm) or bilobar disease per EASL 2024."
                )
                recommendations.append("Consider Y90 for large or bilobar tumors")
                recommendations.append("Discuss TACE vs. Y90 in multidisciplinary setting")
            elif tace_feasibility == "refractory":
                candidacy = "eligible"
                summary = (
                    "Y90 is indicated as alternative locoregional therapy for "
                    "TACE-refractory intermediate HCC. Per EASL 2024, Y90 recommended "
                    "alternative to TACE."
                )
                dosimetry_notes = (
                    "Personalized dosimetry recommended (≥205 Gy target dose, "
                    "glass microspheres)."
                )
                recommendations.append(
                    "Y90 radiation segmentectomy or lobectomy based on tumor extent"
                )
                recommendations.append(
                    "Comparable OS to TACE with potentially better quality of life"
                )
            elif tace_feasibility == "diffuse":
                candidacy = "caution"
                summary = (
                    "Diffuse/infiltrative HCC pattern may limit TACE efficacy. Y90 may "
                    "be considered for liver-dominant disease."
                )
                recommendations.append("Consider Y90 for diffuse HCC patterns")
                recommendations.append("Multidisciplinary evaluation recommended")
            else:
                candidacy = "caution"
                summary = (
                    "TACE remains standard first-line for BCLC-B. Y90 may be preferred "
                    "for large or bilobar disease."
                )
                recommendations.append("Discuss TACE vs. Y90 in multidisciplinary setting")
        # BCLC C: Advanced stage
        elif bclc_stage == "c":
            if portal_vein == "branch":
                candidacy = "eligible"
                summary = (
                    "Y90 is indicated and safe in branch portal vein thrombosis "
                    "(Vp1-Vp3). Median OS 14-17 months with optimized dosing."
                )
                dosimetry_notes = "Lobar Y90 with personalized dosimetry recommended."
                recommendations.append("YES-P Trial evidence supports safety in PVT")
                recommendations.append("Hepatopetal flow assessment essential")
            elif portal_vein == "main":
                candidacy = "caution"
                summary = (
                    "Y90 may be considered in selected cases with main portal vein "
                    "involvement if hepatopetal flow preserved. Higher risk."
                )
                contraindications.append("Hepatofugal portal vein flow")
                recommendations.append("Expert center evaluation required")
                recommendations.append(
                    "Systemic therapy (atezolizumab + bevacizumab) is standard"
                )
            else:
                candidacy = "caution"
                summary = (
                    "For BCLC-C without PVT, systemic therapy is first-line. Y90 may be "
                    "considered in liver-dominant disease."
                )
                recommendations.append("Consider combination with systemic therapy")
    # iCCA assessment pathway
    elif diagnosis == "icca":
        if icca_line == "first-line":
            candidacy = "eligible"
            summary = (
                "Y90 can be combined with gemcitabine/cisplatin ± durvalumab for "
                "unresectable iCCA. Median OS 18-22 months."
            )
            dosimetry_notes = "Personalized dosimetry recommended (≥150 Gy target)."
            recommendations.append("Combination with systemic chemotherapy")
            recommendations.append("Consider durvalumab addition per TOPAZ-1")
        elif icca_line == "second-line":
            candidacy = "eligible"
            summary = (
                "Y90 is indicated for liver-dominant iCCA progressing on systemic "
                "therapy. Objective response rates 20-35%."
            )
            recommendations.append("Adequate liver function required (Child-Pugh A)")
            recommendations.append("Consider if liver-dominant disease")
        elif icca_line == "neoadjuvant":
            candidacy = "caution"
            summary = (
                "Limited data for Y90 as downstaging in iCCA. May be considered in "
                "borderline resectable cases."
            )
            recommendations.append("Multidisciplinary evaluation essential")
            recommendations.append("Expert center experience recommended")
    # Other primary liver malignancies
    else:
        candidacy = "caution"
        summary = (
            "Y90 data is limited for other primary liver tumors. Case-by-case "
            "evaluation recommended."
        )
        recommendations.append("Multidisciplinary tumor board discussion")
        recommendations.append("Limited evidence base for non-HCC/iCCA tumors")

    # General contraindications
    if data.get("childPughScore") == "c":
        contraindications.append("Child-Pugh C cirrhosis")
    ecog = parse_float(data.get("ecogPerformanceStatus"))
    if truthy(ecog) and ecog > 2:
        contraindications.append("ECOG performance status >2")

    return {
        "candidacy": candidacy,
        "summary": summary,
        "recommendations": recommendations,
        "contraindications": contraindications,
        "dosimetryNotes": dosimetry_notes,
        "followUpSchedule": list(_FOLLOW_UP_SCHEDULE),
        "references": list(_REFERENCES),
    }
