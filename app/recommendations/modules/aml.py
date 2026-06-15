"""Acute Myeloid Leukemia (AML) Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/amlLogic.ts (assessAML and all
private helpers: assessFitness, classifyELNRisk, selectTherapy,
recommendTransplant, getTargetedAdditions, getWarnings, getPostRemissionPlan).

Based on ASH 2025 (PMID 39970951), ELN 2022 (PMID 34521987), ELN 2024
(PMID 38838239), VIALE-A (PMID 32558338), NCCN AML v2.2025.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "aml"


def _int_field(value: object) -> int:
    """Coerce a numeric enum (ecogPS, hctCI) to int, preserving 0.

    The TS treats these as numbers and compares with both ``===`` and ``>=``;
    parseFloat-style coercion is used so a literal 0 is kept (unlike
    jslib.intnum which maps 0 -> default).
    """
    v = parse_float(value)
    if math.isnan(v):
        return 0
    return int(v)


# ─── Fitness Assessment ───────────────────────────────────────────────────────


def assess_fitness(input: dict) -> str:
    ecog_ps = _int_field(input.get("ecogPS"))
    age = parse_float(input.get("age"))
    if math.isnan(age):
        age = 0.0
    hct_ci = _int_field(input.get("hctCI"))
    patient_preference = input.get("patientPreference")

    # Best supportive care only
    if ecog_ps == 4:
        return "bsc_only"
    if patient_preference == "minimal" or patient_preference == "bsc":
        return "bsc_only"

    # Unfit criteria (ASH 2025 / ELN 2022)
    unfit_factors: list[str] = []

    if age >= 75:
        unfit_factors.append("age_75plus")
    if ecog_ps >= 3:
        unfit_factors.append("ecog_3plus")
    if hct_ci >= 3:
        unfit_factors.append("hct_ci_3plus")
    if input.get("creatinine") == "elevated_2x_plus":
        unfit_factors.append("renal_severe")
    if input.get("bilirubin") == "elevated_2x_plus":
        unfit_factors.append("hepatic_severe")
    if input.get("ejectionFraction") == "severely_reduced":
        unfit_factors.append("ef_severe")

    # Moderate unfit factors
    moderate_unfit_factors: list[str] = []
    if age >= 65 and age < 75:
        moderate_unfit_factors.append("age_65_74")
    if ecog_ps == 2:
        moderate_unfit_factors.append("ecog_2")
    if hct_ci == 2:
        moderate_unfit_factors.append("hct_ci_2")
    if input.get("creatinine") == "elevated_1_5x":
        moderate_unfit_factors.append("renal_moderate")
    if input.get("bilirubin") == "elevated_1_5x":
        moderate_unfit_factors.append("hepatic_moderate")
    if input.get("ejectionFraction") == "reduced_35_44":
        moderate_unfit_factors.append("ef_reduced")

    if len(unfit_factors) >= 1:
        return "unfit"
    if len(moderate_unfit_factors) >= 2:
        return "unfit"
    return "fit"


# ─── ELN Risk Classification ──────────────────────────────────────────────────


def classify_eln_risk(input: dict) -> str:
    if truthy(input.get("isAPL")):
        return "apl"

    karyotype = input.get("karyotype")
    npm1 = truthy(input.get("npm1Mutation"))

    # Adverse risk (ELN 2022)
    if truthy(input.get("tp53Mutation")):
        return "adverse"
    if karyotype == "complex_3plus":
        return "adverse"
    if karyotype == "monosomal":
        return "adverse"
    if karyotype == "minus5_del5q":
        return "adverse"
    if karyotype == "minus7":
        return "adverse"
    if karyotype == "minus17_abn17p":
        return "adverse"
    if karyotype == "t6_9":
        return "adverse"
    if karyotype == "other_adverse":
        return "adverse"
    if truthy(input.get("runx1Mutation")) and not npm1:
        return "adverse"
    if truthy(input.get("asxl1Mutation")) and not npm1:
        return "adverse"
    if truthy(input.get("bcorMutation")) and not npm1:
        return "adverse"

    # Favorable risk (ELN 2022)
    if karyotype == "favorable_t8_21":
        return "favorable"
    if karyotype == "favorable_inv16":
        return "favorable"
    if truthy(input.get("cebpaDoubleMutation")):
        return "favorable"
    if npm1 and not truthy(input.get("flt3ITD")):
        return "favorable"

    # Intermediate risk
    return "intermediate"


# ─── Therapy Selection ────────────────────────────────────────────────────────


def select_therapy(fitness: str, eln_risk: str, input: dict) -> dict:
    if fitness == "bsc_only":
        return {
            "therapy": "bsc",
            "label": "Best Supportive Care",
            "rationale": (
                "Patient is not a candidate for active leukemia-directed therapy "
                "based on performance status or patient preference. Focus on quality "
                "of life, symptom management, and transfusion support."
            ),
        }

    # APL — special pathway
    if eln_risk == "apl":
        return {
            "therapy": "atra_ato",
            "label": "ATRA + ATO (All-trans retinoic acid + Arsenic trioxide)",
            "rationale": (
                "APL (t(15;17)/PML::RARA) is treated with ATRA + ATO, not standard "
                "7+3 chemotherapy. This is a highly effective regimen with cure rates "
                ">90% for low/intermediate-risk APL."
            ),
        }

    flt3 = truthy(input.get("flt3ITD")) or truthy(input.get("flt3TKD"))

    if fitness == "fit":
        # Fit patients — intensive chemotherapy
        if flt3:
            return {
                "therapy": "ic_7_3_midostaurin",
                "label": "7+3 Induction + Midostaurin (FLT3 inhibitor)",
                "rationale": (
                    "FLT3 mutation detected. ASH 2025 Rec 7 suggests adding an FLT3 "
                    "inhibitor to induction therapy. Midostaurin (RATIFY trial) is "
                    "standard with 7+3 for FLT3-mutated AML in fit patients."
                ),
            }
        if truthy(input.get("idh1Mutation")):
            return {
                "therapy": "ic_7_3_ivosidenib",
                "label": "7+3 Induction + Ivosidenib (IDH1 inhibitor)",
                "rationale": (
                    "IDH1 mutation detected. Ivosidenib in combination with induction "
                    "chemotherapy is an option for fit patients with IDH1-mutated AML "
                    "(IVY trial data)."
                ),
            }
        if truthy(input.get("idh2Mutation")):
            return {
                "therapy": "ic_7_3_enasidenib",
                "label": "7+3 Induction + Enasidenib (IDH2 inhibitor)",
                "rationale": (
                    "IDH2 mutation detected. Enasidenib may be added to induction for "
                    "IDH2-mutated AML in fit patients, though evidence is less robust "
                    "than for IDH1."
                ),
            }
        return {
            "therapy": "ic_7_3",
            "label": "Standard 7+3 Induction Chemotherapy (Cytarabine + Anthracycline)",
            "rationale": (
                "Fit patient without actionable mutations. Standard 7+3 (cytarabine "
                "100-200 mg/m²/day × 7 days + daunorubicin or idarubicin × 3 days) "
                "remains the standard induction regimen."
            ),
        }

    # Unfit patients — less-intensive therapy (ALT)
    if truthy(input.get("idh1Mutation")):
        return {
            "therapy": "alt_hma_ven_ivosidenib",
            "label": "HMA (Azacitidine) + Venetoclax + Ivosidenib",
            "rationale": (
                "IDH1 mutation in unfit patient. ASH 2025 Rec 5a suggests AZA + "
                "ivosidenib > AZA alone. HMA + venetoclax + ivosidenib is an emerging "
                "option with strong rationale (Rec 5b)."
            ),
        }
    if truthy(input.get("idh2Mutation")):
        return {
            "therapy": "alt_hma_ven_enasidenib",
            "label": "HMA (Azacitidine) + Venetoclax",
            "rationale": (
                "IDH2 mutation in unfit patient. ASH 2025 Rec 5d suggests HMA + "
                "venetoclax > HMA + enasidenib. Standard HMA + venetoclax is preferred "
                "for IDH2-mutated unfit AML."
            ),
        }
    if flt3:
        return {
            "therapy": "alt_hma_ven_flt3i",
            "label": "HMA (Azacitidine) + Venetoclax ± FLT3 Inhibitor",
            "rationale": (
                "FLT3 mutation in unfit patient. ASH 2025 Rec 7 conditionally suggests "
                "adding an FLT3 inhibitor to ALT. HMA + venetoclax is the backbone; "
                "FLT3 inhibitor addition is conditional (low certainty evidence)."
            ),
        }

    # Standard unfit: HMA + venetoclax (Rec 4c — strongest recommendation)
    return {
        "therapy": "alt_hma_ven",
        "label": "HMA (Azacitidine) + Venetoclax",
        "rationale": (
            "ASH 2025 Rec 4c (conditional recommendation, moderate certainty): HMA + "
            "venetoclax is preferred over HMA alone for unfit patients. VIALE-A trial "
            "demonstrated superior OS vs azacitidine monotherapy (14.7 vs 9.6 months "
            "median OS)."
        ),
    }


# ─── Transplant Recommendation ────────────────────────────────────────────────


def recommend_transplant(fitness: str, eln_risk: str, input: dict) -> dict:
    if fitness == "bsc_only" or truthy(input.get("priorHCT")):
        return {
            "recommendation": "not_candidate",
            "label": "Not a transplant candidate",
            "rationale": (
                "Prior HCT limits repeat transplant eligibility. Discuss with "
                "transplant center."
                if truthy(input.get("priorHCT"))
                else "Patient is not a candidate for active therapy; transplant is "
                "not appropriate."
            ),
        }

    if eln_risk == "apl":
        return {
            "recommendation": "not_recommended_cr1",
            "label": "Transplant not recommended in CR1 for APL",
            "rationale": (
                "APL treated with ATRA + ATO achieves >90% cure rates without "
                "transplant. Allo-HCT is reserved for relapsed/refractory APL."
            ),
        }

    if eln_risk == "favorable" and fitness == "fit":
        return {
            "recommendation": "not_recommended_cr1",
            "label": "Transplant not recommended in CR1 (Favorable Risk)",
            "rationale": (
                "ELN 2022: Favorable risk AML (t(8;21), inv(16), NPM1 mut without "
                "FLT3-ITD, biallelic CEBPA) does not benefit from allo-HCT in CR1. "
                "Consolidation with HiDAC is standard."
            ),
        }

    if eln_risk == "adverse" and fitness == "fit":
        donor_available = truthy(input.get("hasHLAMatchedSibling")) or truthy(
            input.get("hasMatchedUnrelatedDonor")
        )
        return {
            "recommendation": "strongly_recommended_cr1"
            if donor_available
            else "recommended_cr1",
            "label": "Allo-HCT strongly recommended in CR1 (Adverse Risk)"
            if donor_available
            else "Allo-HCT recommended in CR1 — Donor search urgently needed",
            "rationale": (
                "ELN 2022: Adverse risk AML has high relapse risk with chemotherapy "
                "alone. Allo-HCT in CR1 is strongly recommended. "
                + (
                    "Donor available — proceed with transplant planning."
                    if donor_available
                    else "No matched donor identified — initiate urgent unrelated "
                    "donor search (NMDP/DKMS)."
                )
            ),
        }

    if eln_risk == "intermediate" and fitness == "fit":
        return {
            "recommendation": "consider_cr1",
            "label": "Consider Allo-HCT in CR1 (Intermediate Risk)",
            "rationale": (
                "ELN 2022: Intermediate risk AML — transplant decision depends on MRD "
                "status after induction. MRD-positive after consolidation: transplant "
                "recommended. MRD-negative: transplant may be deferred. Discuss with "
                "transplant center."
            ),
        }

    if fitness == "unfit":
        return {
            "recommendation": "after_alt_response",
            "label": "Consider Allo-HCT after ALT response (if transplant-eligible)",
            "rationale": (
                "ASH 2025 Rec 8: For older adults who respond to ALT and have "
                "nonfavorable prognosis, allo-HCT is conditionally suggested over no "
                "transplant. Assess transplant eligibility after response."
            ),
        }

    return {
        "recommendation": "consider_cr1",
        "label": "Consider Allo-HCT based on MRD and clinical factors",
        "rationale": (
            "Transplant decision should be individualized based on MRD status, donor "
            "availability, and patient fitness."
        ),
    }


# ─── Targeted Additions ───────────────────────────────────────────────────────


def get_targeted_additions(input: dict, fitness: str) -> list[str]:
    additions: list[str] = []

    if truthy(input.get("flt3ITD")) or truthy(input.get("flt3TKD")):
        if fitness == "fit":
            additions.append(
                "Midostaurin 50 mg BID (days 8-21 of induction and consolidation) — "
                "RATIFY trial"
            )
        additions.append(
            "Consider sorafenib or gilteritinib as maintenance post-transplant (FLT3+)"
        )

    if truthy(input.get("idh1Mutation")):
        additions.append(
            "Ivosidenib (IDH1 inhibitor) — add to induction (fit) or HMA backbone "
            "(unfit)"
        )

    if truthy(input.get("idh2Mutation")):
        additions.append(
            "Enasidenib (IDH2 inhibitor) — less evidence for combination; HMA+VEN "
            "preferred (ASH 2025 Rec 5d)"
        )

    if truthy(input.get("tp53Mutation")):
        additions.append(
            "TP53 mutation: Consider decitabine-cedazuridine (oral decitabine) or "
            "clinical trial. Prognosis is poor with standard therapy."
        )

    if truthy(input.get("isSecondaryAML")):
        additions.append(
            "Secondary AML (prior MDS/MPN or therapy-related): Consider CPX-351 "
            "(liposomal daunorubicin/cytarabine) if fit — superior OS vs 7+3 in "
            "secondary AML (NEJM 2017)"
        )

    return additions


# ─── Warnings ─────────────────────────────────────────────────────────────────


def get_warnings(input: dict, eln_risk: str) -> list[str]:
    warnings: list[str] = []

    if truthy(input.get("isAPL")):
        warnings.append(
            "APL EMERGENCY: Initiate ATRA immediately upon morphologic suspicion — "
            "do not wait for molecular confirmation. Differentiation syndrome risk."
        )

    if truthy(input.get("tp53Mutation")):
        warnings.append(
            "TP53 mutation confers very poor prognosis. Median OS <6 months with "
            "standard therapy. Clinical trial enrollment strongly encouraged."
        )

    if input.get("karyotype") == "monosomal" or input.get("karyotype") == "complex_3plus":
        warnings.append(
            "Complex/monosomal karyotype: Adverse ELN risk. Transplant in CR1 is "
            "strongly recommended if patient is eligible."
        )

    if truthy(input.get("isRelapsedRefractory")):
        warnings.append(
            "Relapsed/Refractory AML: Standard salvage regimens (MEC, FLAG-IDA) have "
            "limited efficacy. Clinical trial enrollment is strongly encouraged. "
            "Gilteritinib for FLT3+ R/R AML (ADMIRAL trial)."
        )

    age = parse_float(input.get("age"))
    if math.isnan(age):
        age = 0.0
    if age >= 75 and truthy(input.get("flt3ITD")):
        warnings.append(
            "FLT3 inhibitor benefit in patients ≥75 receiving HMA+VEN is uncertain "
            "(ASH 2025 Rec 7 remark). Discuss risk/benefit carefully."
        )

    if truthy(input.get("priorHCT")):
        warnings.append(
            "Prior HCT: Standard salvage options are limited. Discuss with transplant "
            "center regarding second transplant eligibility."
        )

    return warnings


# ─── Post-Remission Plan ──────────────────────────────────────────────────────


def _get_post_remission_plan(fitness: str, eln_risk: str, input: dict) -> str:
    if fitness == "bsc_only":
        return "Focus on comfort measures and transfusion support per patient preference."

    if eln_risk == "apl":
        return (
            "APL: After CR with ATRA+ATO, consolidation with 2 cycles of ATO + ATRA. "
            "Maintenance: ATRA ± 6-MP/MTX × 2 years for high-risk APL. Monitor "
            "PML::RARA by PCR."
        )

    if fitness == "fit":
        if eln_risk == "favorable":
            return (
                "Consolidation: HiDAC (cytarabine 3 g/m² q12h, days 1/3/5) × 3-4 "
                "cycles. No transplant in CR1. Monitor MRD; transplant if MRD+ or "
                "relapse."
            )
        if eln_risk == "adverse":
            return (
                "Allo-HCT in CR1 strongly recommended. Proceed with donor search "
                "immediately. If no donor: HiDAC consolidation as bridge. Consider "
                "maintenance with targeted agents post-transplant."
            )
        return (
            "Intermediate risk: HiDAC consolidation × 1-2 cycles. Assess MRD after "
            "consolidation. MRD-positive → allo-HCT. MRD-negative → consider "
            "transplant vs additional consolidation based on risk factors."
        )

    # Unfit
    return (
        "Continue HMA + venetoclax indefinitely until progression or unacceptable "
        "toxicity (ASH 2025 Rec 6). Assess transplant eligibility if good response "
        "achieved. Monitor CBC every 2-4 weeks during induction."
    )


# ─── Main Assessment Function ─────────────────────────────────────────────────

_REFERENCES = [
    {
        "id": "ash2025",
        "text": "Sekeres MA et al. ASH 2025 Guidelines for Treating Newly Diagnosed AML in Older Adults. Blood Advances. 2025. PMID: 39970951",
    },
    {
        "id": "eln2022",
        "text": "Döhner H et al. Diagnosis and Management of AML in Adults: 2022 ELN Recommendations. Blood. 2022;140(12):1345–1377. PMID: 34521987",
    },
    {
        "id": "eln2024",
        "text": "Döhner H et al. ELN 2024 Risk Stratification Update for AML. Blood. 2024. PMID: 38838239",
    },
    {
        "id": "viale_a",
        "text": "DiNardo CD et al. Azacitidine and Venetoclax in Previously Untreated AML (VIALE-A). NEJM. 2020;383(7):617–629. PMID: 32558338",
    },
    {
        "id": "ratify",
        "text": "Stone RM et al. Midostaurin plus Chemotherapy for AML with FLT3 Mutation (RATIFY). NEJM. 2017;377(5):454–464. PMID: 28644114",
    },
]


def assess(data: dict) -> dict:
    fitness_category = assess_fitness(data)
    eln_risk = classify_eln_risk(data)
    therapy = select_therapy(fitness_category, eln_risk, data)
    transplant = recommend_transplant(fitness_category, eln_risk, data)
    targeted_additions = get_targeted_additions(data, fitness_category)
    key_warnings = get_warnings(data, eln_risk)
    post_remission_plan = _get_post_remission_plan(fitness_category, eln_risk, data)

    # Urgency
    urgency_flag = "routine"
    if truthy(data.get("isAPL")):
        urgency_flag = "emergent"
    elif truthy(data.get("isRelapsedRefractory")) or eln_risk == "adverse":
        urgency_flag = "urgent"

    return {
        "fitnessCategory": fitness_category,
        "elnRisk": eln_risk,
        "primaryTherapy": therapy["therapy"],
        "primaryTherapyLabel": therapy["label"],
        "primaryTherapyRationale": therapy["rationale"],
        "transplantRecommendation": transplant["recommendation"],
        "transplantLabel": transplant["label"],
        "transplantRationale": transplant["rationale"],
        "targetedAdditions": targeted_additions,
        "keyWarnings": key_warnings,
        "postRemissionPlan": post_remission_plan,
        "references": _REFERENCES,
        "urgencyFlag": urgency_flag,
    }
