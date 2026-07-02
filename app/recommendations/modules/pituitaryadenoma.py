"""Pituitary Adenoma Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/pituitaryAdenomaLogic.ts
(assessPituitaryAdenoma).

Based on CNS 2025 Systematic Review and Evidence-Based Guidelines for
Functioning Pituitary Adenomas and Endocrine Society guidelines.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import num, parse_float, truthy

LOGIC_KEY = "pituitaryadenoma"


def _get_pituitary_references() -> list[dict]:
    return [
        {
            "citation": "Turin CG et al. CNS Systematic Review and Evidence-Based Guidelines for Medical Perioperative Management for Functioning Pituitary Adenomas. Neurosurgery. 2025;97(3S):S1-S14.",
            "pmid": "40815128",
        },
        {
            "citation": "Lillehei KO et al. CNS Systematic Review and Evidence-Based Guidelines for the Role of Surgery for Functioning Pituitary Adenomas. Neurosurgery. 2025;97(3S):24-35.",
            "pmid": "40815132",
        },
        {
            "citation": "Green S et al. CNS Systematic Review and Evidence-Based Guidelines for the Role of Radiosurgery for Functioning Pituitary Adenomas. Neurosurgery. 2025;97(3S):S36-S43.",
            "pmid": "40815129",
        },
        {
            "citation": "Junn JC et al. CNS Systematic Review and Evidence-Based Guidelines for the Role of Imaging for Functioning Pituitary Adenomas. Neurosurgery. 2025;97(3S):S15-S23.",
            "pmid": "40815142",
        },
        {
            "citation": "Katznelson L et al. Acromegaly: An Endocrine Society Clinical Practice Guideline. J Clin Endocrinol Metab. 2014;99(11):3933-3951.",
            "pmid": "25356808",
        },
        {
            "citation": "Nieman LK et al. Treatment of Cushing's Syndrome: An Endocrine Society Clinical Practice Guideline. J Clin Endocrinol Metab. 2015;100(8):2807-2831.",
            "pmid": "26222757",
        },
        {
            "citation": "Melmed S et al. Diagnosis and Treatment of Hyperprolactinemia: An Endocrine Society Clinical Practice Guideline. J Clin Endocrinol Metab. 2011;96(2):273-288.",
            "pmid": "21296991",
        },
    ]


def assess(data: dict) -> dict:
    tumor_type = data.get("tumorType")
    tumor_size = data.get("tumorSize")
    cavernous = data.get("cavernousSinusInvasion")

    urgent_flags: list[str] = []
    warnings: list[str] = []
    perioperative_notes: list[str] = []
    postop_monitoring: list[str] = []

    # ── Urgent flags ──────────────────────────────────────────────────────
    if truthy(data.get("pituitaryApoplexy")):
        urgent_flags.append(
            "PITUITARY APOPLEXY: Urgent neurosurgical evaluation required. Consider emergent decompression if visual compromise or altered consciousness."
        )
    if truthy(data.get("visualFieldDefect")) and not truthy(data.get("pituitaryApoplexy")):
        urgent_flags.append(
            "Visual field defect detected: Expedited surgical evaluation recommended to prevent permanent vision loss (chiasmal compression)."
        )
    if truthy(data.get("cranialNervePalsy")):
        urgent_flags.append(
            "Cranial nerve palsy present: Indicates cavernous sinus involvement. Urgent multidisciplinary evaluation."
        )

    # ── Prolactinoma pathway ──────────────────────────────────────────────
    if tumor_type == "prolactinoma":
        prolactin = num(data.get("prolactinLevelNgMl"), 0)

        # Pregnancy considerations
        if truthy(data.get("pregnancyDesired")) and tumor_size == "macroadenoma":
            warnings.append(
                "Pregnancy desired with macroprolactinoma: Dopamine agonist (cabergoline preferred) should achieve tumor control before conception. Monitor closely during pregnancy."
            )

        # Medical therapy is first-line for prolactinomas
        if not truthy(data.get("visualFieldDefect")) and not truthy(data.get("pituitaryApoplexy")):
            next_steps_rec = [
                "Initiate cabergoline at low dose (0.25 mg twice weekly), titrate to normoprolactinemia",
                "Check prolactin level at 4–6 weeks",
                "Obtain baseline MRI pituitary with gadolinium if not already done",
                "Refer to endocrinology for ongoing management",
                "Discuss fertility implications if relevant",
                "Prolactin >500 ng/mL: strongly suggests macroprolactinoma — ensure MRI confirms diagnosis"
                if prolactin > 500
                else "",
            ]
            return {
                "primaryRecommendation": "medical_therapy_first",
                "recommendationTitle": "Dopamine Agonist Therapy — First-Line",
                "rationale": "CNS 2025 guidelines recommend medical management (dopamine agonist) over surgery as primary treatment for prolactin-secreting microadenomas and most macroadenomas. Cabergoline achieves normoprolactinemia in >80% of patients and tumor shrinkage in 70–80% of macroadenomas.",
                "evidenceLevel": "C",
                "guidelineSource": "CNS 2025 Functioning Pituitary Adenoma Guidelines (Neurosurgery 97(3S), 2025; PMID 40815128)",
                "medicalOptions": [
                    "Cabergoline 0.25–3.5 mg twice weekly (preferred — higher efficacy, better tolerability than bromocriptine)",
                    "Bromocriptine 2.5–15 mg/day (alternative, especially in pregnancy — more safety data)",
                    "Target: normoprolactinemia + tumor size reduction",
                    "Reassess at 3 months; MRI at 6 months if macroadenoma",
                ],
                "perioperativeNotes": [
                    "Fluid restriction after trans-sphenoidal surgery is suggested to prevent delayed hyponatremia (CNS 2025, Class III).",
                    "Postoperative serum sodium monitoring for 7–10 days recommended.",
                ],
                "postopMonitoring": [
                    "Prolactin level at 6 weeks post-treatment initiation",
                    "MRI at 6 months if macroadenoma to assess tumor response",
                    "Annual MRI if stable; every 2 years if in remission",
                ],
                "imagingFollowUp": [
                    "MRI pituitary with gadolinium: baseline, then 6 months after treatment initiation",
                    "Annual MRI for macroadenomas until stable × 2 years, then every 2 years",
                    "Microadenoma on stable DA therapy: MRI every 2 years",
                ],
                "urgentFlags": urgent_flags,
                "warnings": warnings,
                "nextSteps": [s for s in next_steps_rec if truthy(s)],
                "references": _get_pituitary_references(),
            }

    # ── Acromegaly (GH-secreting) pathway ────────────────────────────────
    if tumor_type == "acromegaly_gh":
        # Surgery is first-line for GH microadenomas
        if tumor_size == "microadenoma":
            perioperative_notes.append(
                "Preoperative somatostatin analogs are NOT routinely recommended for GH-secreting microadenomas (CNS 2025, Class III)."
            )
            perioperative_notes.append(
                "Fluid restriction post-surgery suggested to prevent delayed hyponatremia."
            )
            postop_monitoring.append(
                "IGF-1 at 12 weeks postoperatively to assess biochemical remission"
            )
            postop_monitoring.append(
                "Oral glucose tolerance test (OGTT) with GH at 3 months"
            )
            postop_monitoring.append(
                "MRI at 3 months postoperatively to assess extent of resection"
            )

            macro_warnings = list(warnings)
            if cavernous != "none":
                macro_warnings.append(
                    f"Cavernous sinus invasion ({cavernous}): Reduces surgical cure rate significantly. Adjuvant medical therapy or radiosurgery likely required."
                )
            micro_next_steps = [
                "Refer to experienced pituitary neurosurgeon (center with >50 pituitary cases/year)",
                "Preoperative endocrine evaluation: IGF-1, GH, cortisol, thyroid, gonadal axes",
                "Ophthalmology evaluation if suprasellar extension",
                "Cardiology evaluation (acromegaly-related cardiomyopathy)",
                "Postoperative: IGF-1 and OGTT-GH at 12 weeks",
                "Plan for adjuvant somatostatin analog (octreotide LAR or lanreotide) if residual disease"
                if cavernous != "none"
                else "",
            ]
            return {
                "primaryRecommendation": "surgery_first",
                "recommendationTitle": "Endoscopic Trans-Sphenoidal Surgery — First-Line for GH Microadenoma",
                "rationale": "CNS 2025 guidelines recommend surgery over medical management for GH-secreting microadenomas. Cure rates of 70–90% for microadenomas with experienced pituitary surgeons. Endoscopic technique may offer superior outcomes for macroadenomas without cavernous sinus invasion.",
                "evidenceLevel": "C",
                "guidelineSource": "CNS 2025 Functioning Pituitary Adenoma Guidelines (PMID 40815132)",
                "surgicalApproach": "Endoscopic endonasal trans-sphenoidal surgery (EETS) preferred. Microscopic approach acceptable alternative. Endoscopic technique may be superior for macroadenomas without cavernous sinus invasion (shorter operative time, higher EOR, better hormone remission rates).",
                "perioperativeNotes": perioperative_notes,
                "postopMonitoring": postop_monitoring,
                "imagingFollowUp": [
                    "MRI pituitary at 3 months postoperatively",
                    "Annual MRI × 3 years, then every 2 years if stable",
                    "MRI grading systems (Knosp grade) to predict postoperative biochemical control",
                ],
                "urgentFlags": urgent_flags,
                "warnings": [w for w in macro_warnings if truthy(w)],
                "nextSteps": [s for s in micro_next_steps if truthy(s)],
                "references": _get_pituitary_references(),
            }

        # GH macroadenoma
        perioperative_notes.append(
            "Preoperative somatostatin analogs may be considered for large macroadenomas to reduce tumor vascularity and improve surgical conditions (not routinely recommended per CNS 2025)."
        )
        if cavernous == "bilateral":
            warnings.append(
                "Bilateral cavernous sinus invasion: Surgical cure unlikely (<20%). Plan for multimodal therapy: surgery for debulking + somatostatin analog + radiosurgery."
            )

    # ── Cushing's disease (ACTH-secreting) pathway ───────────────────────
    if tumor_type == "cushings_acth":
        # Postoperative cortisol assessment
        postop_cortisol = parse_float(data.get("postopCortisolUgDl"))
        hours_post = parse_float(data.get("hoursPostSurgery"))
        if not math.isnan(postop_cortisol) and not math.isnan(hours_post):
            if postop_cortisol < 2 and hours_post <= 72:
                cushings_warnings = list(warnings)
                cushings_warnings.append(
                    "Adrenal insufficiency risk: Patient requires glucocorticoid replacement and stress-dosing education."
                )
                return {
                    "primaryRecommendation": "surgery_first",
                    "recommendationTitle": "Biochemical Remission Confirmed — Glucocorticoid Replacement Required",
                    "rationale": "Postoperative serum cortisol <2 μg/dL within 72 hours is a strong predictor of remission (CNS 2025, Class III). Glucocorticoid replacement is required to prevent adrenal insufficiency.",
                    "evidenceLevel": "C",
                    "guidelineSource": "CNS 2025 Functioning Pituitary Adenoma Guidelines (PMID 40815128)",
                    "perioperativeNotes": [
                        "Serum cortisol <2 μg/dL within ≤72 hours post-surgery = predictor of remission (CNS 2025).",
                        "Initiate glucocorticoid replacement immediately (hydrocortisone 10–15 mg/m²/day in divided doses).",
                        "Fluid restriction post-surgery to prevent delayed hyponatremia.",
                    ],
                    "postopMonitoring": [
                        "Morning cortisol at 6 weeks (off replacement) to confirm remission",
                        "24-hour urinary free cortisol at 3 months",
                        "Late-night salivary cortisol at 3 months",
                        "MRI at 3 months",
                        "Annual MRI × 5 years (high recurrence risk)",
                    ],
                    "imagingFollowUp": [
                        "MRI pituitary at 3 months postoperatively",
                        "Annual MRI × 5 years (Cushing's recurrence rate 10–25% at 5 years)",
                    ],
                    "urgentFlags": urgent_flags,
                    "warnings": cushings_warnings,
                    "nextSteps": [
                        "Initiate hydrocortisone replacement (10–15 mg/m²/day)",
                        "Educate patient on sick-day dosing and adrenal crisis prevention",
                        "Endocrinology follow-up at 6 weeks",
                        "Morning cortisol off replacement at 6 weeks to confirm sustained remission",
                    ],
                    "references": _get_pituitary_references(),
                }

        # Preoperative Cushing's
        perioperative_notes.append(
            "BIPSS (bilateral inferior petrosal sinus sampling) is recommended if MRI is negative or equivocal to confirm pituitary source (CNS 2025, Class III)."
        )
        perioperative_notes.append(
            "If ectopic ACTH syndrome suspected → CT abdomen/pelvis preferred over pituitary MRI (CNS 2025, Class III)."
        )
        if tumor_size == "microadenoma":
            warnings.append(
                "ACTH-secreting microadenoma: Insufficient evidence to favor surgery over medical management per CNS 2025. Surgery remains standard of care at experienced centers."
            )

    # ── TSHoma pathway ────────────────────────────────────────────────────
    if tumor_type == "tshoma":
        warnings.append(
            "TSH-secreting adenoma: Insufficient evidence to favor surgery over medical management per CNS 2025. Surgery is standard first-line at experienced centers."
        )
        perioperative_notes.append(
            "Preoperative thyroid function normalization with somatostatin analogs or antithyroid drugs recommended to reduce surgical risk."
        )

    # ── Recurrent/persistent disease → radiosurgery ──────────────────────
    medical_response = data.get("medicalTherapyResponse")
    if truthy(data.get("priorSurgery")) and (
        medical_response == "none" or medical_response == "partial"
    ):
        radiosurgery_warnings = list(warnings)
        radiosurgery_warnings.append(
            "Radiosurgery hormonal remission rates: 50–60% for Cushing's, 40–60% for acromegaly, 25–40% for prolactinoma at 5 years."
        )
        radiosurgery_warnings.append(
            "Hypopituitarism risk post-SRS: 20–30% at 5 years."
        )
        return {
            "primaryRecommendation": "radiosurgery_adjuvant",
            "recommendationTitle": "Stereotactic Radiosurgery — Adjuvant for Recurrent/Persistent Disease",
            "rationale": "CNS 2025 guidelines suggest SRS, hypofractionated SRS, fractionated RT, and conventional RT for progressive/recurrent functioning pituitary adenomas with improved radiographic control and variable hormonal reduction (Class III). Endocrine-suppressive medical therapy may be continued before SRS.",
            "evidenceLevel": "C",
            "guidelineSource": "CNS 2025 Functioning Pituitary Adenoma Guidelines — Radiosurgery (PMID 40815129)",
            "radiosurgeryIndication": "Recurrent or persistent functioning pituitary adenoma after surgery with inadequate response to medical therapy.",
            "perioperativeNotes": [
                "Endocrine-suppressive medical therapy may be continued before SRS (CNS 2025, Class III).",
                "Coordinate with radiation oncology for treatment planning.",
                "Minimum 3–6 month interval from surgery to SRS recommended.",
            ],
            "postopMonitoring": [
                "Hormone levels at 3, 6, 12 months post-SRS",
                "MRI at 6 months post-SRS, then annually",
                "Hypopituitarism screening annually (GH, ACTH, TSH, LH/FSH axes)",
            ],
            "imagingFollowUp": [
                "MRI at 6 months post-SRS",
                "Annual MRI × 5 years",
                "Long-term annual MRI (radiosurgery effect can take 2–5 years)",
            ],
            "urgentFlags": urgent_flags,
            "warnings": radiosurgery_warnings,
            "nextSteps": [
                "Multidisciplinary tumor board review (neurosurgery, endocrinology, radiation oncology)",
                "Radiation oncology consultation for SRS planning",
                "Continue medical therapy (somatostatin analog, dopamine agonist, or steroidogenesis inhibitor) until SRS effect achieved",
                "Annual pituitary hormone panel",
            ],
            "references": _get_pituitary_references(),
        }

    # ── Default: surgery first for most functioning adenomas ─────────────
    is_macro = tumor_size == "macroadenoma" or tumor_size == "giant"
    endoscopic_superior = is_macro and cavernous == "none"

    perioperative_notes.append(
        "Fluid restriction after trans-sphenoidal surgery is suggested to prevent delayed hyponatremia (CNS 2025, Class III)."
    )
    perioperative_notes.append(
        "Postoperative serum cortisol <2 μg/dL within ≤72 hours predicts remission in Cushing's disease."
    )
    if truthy(data.get("hypopituitarism")):
        perioperative_notes.append(
            "Preoperative hypopituitarism: Ensure cortisol replacement before surgery. Stress-dose steroids perioperatively."
        )

    default_warnings = list(warnings)
    if cavernous != "none":
        default_warnings.append(
            f"Cavernous sinus invasion ({cavernous}): Surgical cure rate reduced. Plan for adjuvant medical therapy or radiosurgery."
        )
    if is_macro:
        default_warnings.append(
            "Macroadenoma: Ophthalmology evaluation required preoperatively for visual field assessment."
        )

    rationale_suffix = (
        "Endoscopic technique may be superior to microscopic for macroadenomas without cavernous sinus invasion (shorter operative time, higher EOR, better hormone remission rates — CNS 2025, Class III)."
        if endoscopic_superior
        else ""
    )

    return {
        "primaryRecommendation": "surgery_first",
        "recommendationTitle": "Endoscopic Trans-Sphenoidal Surgery — Primary Treatment",
        "rationale": f"Trans-sphenoidal surgery is the primary treatment for most functioning pituitary adenomas (except prolactinomas). {rationale_suffix}",
        "evidenceLevel": "C",
        "guidelineSource": "CNS 2025 Functioning Pituitary Adenoma Guidelines — Surgery (PMID 40815132)",
        "surgicalApproach": "Endoscopic endonasal trans-sphenoidal surgery (EETS) preferred for macroadenomas without cavernous sinus invasion."
        if endoscopic_superior
        else "Endoscopic or microscopic trans-sphenoidal approach based on surgeon expertise and anatomy.",
        "perioperativeNotes": perioperative_notes,
        "postopMonitoring": [
            "Serum cortisol within 72 hours postoperatively (Cushing's disease)",
            "IGF-1 at 12 weeks (acromegaly)",
            "Prolactin at 6 weeks (prolactinoma)",
            "Full pituitary hormone panel at 6 weeks",
            "MRI at 3 months postoperatively",
        ],
        "imagingFollowUp": [
            "MRI pituitary with gadolinium: baseline (if not done), then 3 months postoperatively",
            "Annual MRI × 3 years, then every 2 years if stable",
            "MRI grading systems (Knosp grade) recommended to predict postoperative biochemical control (CNS 2025, Class III)",
        ],
        "urgentFlags": urgent_flags,
        "warnings": [w for w in default_warnings if truthy(w)],
        "nextSteps": [
            "Refer to experienced pituitary neurosurgeon (high-volume center)",
            "Preoperative endocrine evaluation: full pituitary hormone panel",
            "Ophthalmology evaluation with formal visual fields if suprasellar extension",
            "Anesthesia evaluation (acromegaly: difficult airway; Cushing's: metabolic optimization)",
            "Postoperative endocrinology follow-up at 6 weeks",
        ],
        "references": _get_pituitary_references(),
    }
