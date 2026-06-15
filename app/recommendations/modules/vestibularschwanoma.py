"""Vestibular Schwannoma Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/vestibularSchwaноmaLogic.ts
(assessVestibularSchwanoma). The legacy filename/type names carried Cyrillic
homoglyphs ("но"); the module uses the ASCII LOGIC_KEY "vestibularschwannoma"
(the registry normalises the incoming Cyrillic key to match).

Based on CNS 2025 Evidence-Based Clinical Practice Guidelines for Vestibular
Schwannoma; AAO-HNS Acoustic Neuroma Guidelines; NOMS Framework.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "vestibularschwanoma"


def _get_vs_references() -> list[dict]:
    return [
        {
            "citation": "Olson JJ. CNS Evidence-Based Clinical Practice Guidelines for the Treatment of Adults with Vestibular Schwannoma: Introduction and Methods Update. Neurosurgery. 2025.",
        },
        {
            "citation": "Germano IM et al. CNS Systematic Review and Evidence-Based Guideline on the Role of Radiosurgery (SRS) and Radiation Therapy in the Management of Patients with Vestibular Schwannomas: Updates. Neurosurgery. 2025.",
        },
        {
            "citation": "Van Gompel JJ et al. Surgical Resection For The Treatment Of Patients With Vestibular Schwannomas: Update. Neurosurgery. 2025.",
        },
        {
            "citation": "Daher GS et al. CNS Systematic Review and Evidence-Based Guideline on Hearing Preservation Outcomes in Patients with Sporadic Vestibular Schwannoma: Update. Neurosurgery. 2025.",
        },
        {
            "citation": "Graffeo CS et al. The Role Of Imaging In The Management Of Patients With Vestibular Schwannomas: Update. Neurosurgery. 2025.",
        },
        {
            "citation": "Strickland BA et al. CNS Systematic Review and Evidence-Based Guidelines Update for the Role of Audiologic Screening in the Diagnosis and Management of Patients with Vestibular Schwannomas. Neurosurgery. 2025.",
        },
        {
            "citation": "Patel NS et al. CNS Systematic Review and Evidence-Based Guidelines Update for the Role of Intraoperative Cranial Nerve Monitoring in the Management of Patients with Vestibular Schwannomas. Neurosurgery. 2025.",
        },
    ]


def _build_observation_recommendation(
    data: dict,
    urgent_flags: list[str],
    warnings: list[str],
    surgical_notes: list[str],
    srs_notes: list[str],
    observation_notes: list[str],
    monitoring_plan: list[str],
    hearing_preservation_counseling: list[str],
) -> dict:
    return {
        "primaryRecommendation": "observation_active_surveillance",
        "recommendationTitle": "Active Surveillance — Observation with Serial MRI",
        "rationale": (
            "Active surveillance is appropriate for small/intracanalicular vestibular schwannomas, "
            "especially in older patients or those with serviceable hearing where treatment risks may "
            "outweigh benefits. CNS 2025 notes that SRS is NOT superior to observation for hearing "
            "preservation in sporadic intracanalicular or <2 cm VS."
        ),
        "evidenceLevel": "III",
        "guidelineSource": "CNS 2025 Vestibular Schwannoma Guidelines (Olson JJ et al., Neurosurgery 2025)",
        "hearingPreservationCounseling": hearing_preservation_counseling,
        "surgicalNotes": surgical_notes,
        "srsNotes": srs_notes,
        "observationNotes": [
            *observation_notes,
            "Serial MRI: Every 6 months × 2 years, then annually × 3 years, then every 2 years if stable.",
            "Annual audiogram to monitor hearing.",
            "Trigger for treatment: growth ≥2 mm in any dimension, hearing deterioration, new symptoms.",
        ],
        "monitoringPlan": [
            "MRI with gadolinium at 6 months, 12 months, then annually",
            "Annual audiogram",
            "Vestibular function testing if balance issues develop",
        ],
        "urgentFlags": urgent_flags,
        "warnings": [
            x
            for x in [
                *warnings,
                "Cystic VS: Associated with rapid growth — shorter observation intervals recommended."
                if truthy(data.get("cysticComponent"))
                else "",
            ]
            if truthy(x)
        ],
        "nextSteps": [
            "MRI with gadolinium in 6 months",
            "Annual audiogram",
            "Counsel patient on observation vs treatment trade-offs",
            "Discuss triggers for treatment: growth, hearing loss, new symptoms",
            "Refer to skull base multidisciplinary team for shared decision-making",
        ],
        "references": _get_vs_references(),
    }


def _build_srs_recommendation(
    data: dict,
    urgent_flags: list[str],
    warnings: list[str],
    surgical_notes: list[str],
    srs_notes: list[str],
    observation_notes: list[str],
    monitoring_plan: list[str],
    hearing_preservation_counseling: list[str],
) -> dict:
    return {
        "primaryRecommendation": "srs_gamma_knife",
        "recommendationTitle": "Stereotactic Radiosurgery (SRS / Gamma Knife) — Recommended",
        "rationale": (
            "SRS provides excellent local tumor control (>90% at 5 years) for small-to-medium "
            "vestibular schwannomas with lower procedural risk than microsurgery. CNS 2025 recommends "
            "single fraction SRS over hypofractionated SRS for decreased cranial nerve dysfunction."
        ),
        "evidenceLevel": "III",
        "guidelineSource": "CNS 2025 Vestibular Schwannoma Guidelines — Radiosurgery (Germano IM et al., Neurosurgery 2025)",
        "hearingPreservationCounseling": [
            *hearing_preservation_counseling,
            "SRS hearing preservation: >50% at 2–5 years with cochlear dose ≤4 Gy and marginal dose ≤13 Gy.",
            "Cochlear dose >4.2 Gy in single fraction associated with higher hearing loss risk.",
        ],
        "surgicalNotes": surgical_notes,
        "srsNotes": [
            *srs_notes,
            "Marginal dose: 12–13 Gy (single fraction) recommended for tumor control.",
            "Cochlear dose constraint: <4 Gy single fraction, <35 Gy fractionated.",
            "Single fraction SRS preferred over hypofractionated SRS (CNS 2025, Level III).",
            "Tumor control rate: >90% at 5 years, >85% at 10 years.",
            "Facial nerve preservation: >95% at experienced centers.",
        ],
        "observationNotes": observation_notes,
        "monitoringPlan": [
            "MRI at 6 months post-SRS, then annually × 5 years",
            "Annual audiogram",
            "Facial nerve function assessment at each visit",
            "Trigeminal function assessment",
        ],
        "urgentFlags": urgent_flags,
        "warnings": [
            x
            for x in [
                *warnings,
                "SRS does not remove the tumor — radiographic 'expansion' in first 6–12 months is common and does not indicate treatment failure.",
                "Tumor >2.5 cm: SRS may have higher risk of brainstem edema. Consider fractionated SRT."
                if num(data.get("tumorSizeCm"), 0) > 2.5
                else "",
            ]
            if truthy(x)
        ],
        "nextSteps": [
            "Radiation oncology consultation for SRS planning",
            "Skull base multidisciplinary team review",
            "Audiogram before treatment",
            "Ophthalmology evaluation if trigeminal symptoms",
            "Counsel on 6–12 month radiographic expansion (pseudoprogression)",
            "MRI at 6 months post-SRS",
        ],
        "references": _get_vs_references(),
    }


def _build_surgery_recommendation(
    data: dict,
    urgent_flags: list[str],
    warnings: list[str],
    surgical_notes: list[str],
    srs_notes: list[str],
    observation_notes: list[str],
    monitoring_plan: list[str],
    hearing_preservation_counseling: list[str],
) -> dict:
    approach = (
        "Middle fossa or retrosigmoid approach (hearing preservation intent)"
        if truthy(data.get("serviceableHearing")) and truthy(data.get("hearingPreservationPriority"))
        else "Translabyrinthine approach (if hearing non-serviceable — best facial nerve exposure)"
    )

    return {
        "primaryRecommendation": "microsurgery_resection",
        "recommendationTitle": "Microsurgical Resection — Recommended",
        "rationale": (
            "Microsurgical resection is indicated for large tumors (>3 cm), tumors causing brainstem "
            "compression, or when trigeminal neuralgia symptoms are present. Intraoperative cranial "
            "nerve monitoring is standard of care."
        ),
        "evidenceLevel": "III",
        "guidelineSource": "CNS 2025 Vestibular Schwannoma Guidelines — Surgery (Van Gompel JJ et al., Neurosurgery 2025)",
        "hearingPreservationCounseling": [
            *hearing_preservation_counseling,
            "Microsurgery hearing preservation: >25% at 2, 5, 10 years. Better with Class A/GR I, smaller tumor, fundal CSF cap present."
            if truthy(data.get("serviceableHearing"))
            else "Hearing non-serviceable: Translabyrinthine approach provides best facial nerve exposure.",
            "Fundal CSF cap present: Associated with better hearing preservation outcomes."
            if truthy(data.get("fundalCSFCap"))
            else "Fundal CSF cap absent (lateral IAC involvement): Reduced hearing preservation likelihood.",
        ],
        "surgicalNotes": [
            x
            for x in [
                *surgical_notes,
                approach,
                "Intraoperative facial nerve monitoring: Standard of care (CNS 2025).",
                "Intraoperative auditory monitoring (ABR or CNAP) if hearing preservation intent.",
                "Cystic VS: Lower complete resection rates and inferior immediate postoperative facial nerve outcomes — counsel patient."
                if truthy(data.get("cysticComponent"))
                else "",
                "Prior SRS: Increased likelihood of STR and decreased facial nerve function (CNS 2025, Level III)."
                if truthy(data.get("priorSRS"))
                else "",
                "STR + adjuvant SRS: Acceptable alternative to GTR for large tumors to preserve facial nerve.",
            ]
            if truthy(x)
        ],
        "srsNotes": srs_notes,
        "observationNotes": observation_notes,
        "monitoringPlan": [
            "MRI at 3 months postoperatively",
            "Annual MRI × 5 years",
            "Audiogram at 3 months postoperatively",
            "Facial nerve function assessment (House-Brackmann) at each visit",
            "Vestibular rehabilitation if balance issues persist",
        ],
        "urgentFlags": urgent_flags,
        "warnings": [
            x
            for x in [
                *warnings,
                "Facial nerve injury risk: Varies by tumor size and adherence. Experienced skull base surgeon essential.",
                "Large tumor: Consider STR + SRS strategy to optimize facial nerve preservation."
                if num(data.get("tumorSizeCm"), 0) > 3
                else "",
            ]
            if truthy(x)
        ],
        "nextSteps": [
            "Refer to high-volume skull base neurosurgery center",
            "Multidisciplinary skull base team review (neurosurgery + otolaryngology)",
            "Preoperative audiogram",
            "Preoperative MRI with thin-cut IAC protocol",
            "Discuss STR vs GTR trade-offs (facial nerve preservation vs recurrence risk)",
            "Vestibular rehabilitation referral postoperatively",
        ],
        "references": _get_vs_references(),
    }


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    warnings: list[str] = []
    hearing_preservation_counseling: list[str] = []
    surgical_notes: list[str] = []
    srs_notes: list[str] = []
    observation_notes: list[str] = []
    monitoring_plan: list[str] = []

    # ── Diagnostic flags ──────────────────────────────────────────────────
    if truthy(data.get("suddenSNHL")):
        urgent_flags.append(
            "Sudden SNHL: MRI with gadolinium is suggested to evaluate for vestibular schwannoma (CNS 2025, Level III)."
        )
    if truthy(data.get("asymmetricSNHL")) or truthy(data.get("asymmetricTinnitus")):
        urgent_flags.append(
            "Asymmetric SNHL or tinnitus: MRI screening is suggested (CNS 2025, Level III)."
        )

    # ── NF2 pathway ───────────────────────────────────────────────────────
    if truthy(data.get("nf2Status")):
        warnings.append(
            "NF2 (Neurofibromatosis Type 2): Bilateral vestibular schwannomas. Bevacizumab may be considered for hearing preservation. SRS is an option for enlarging or hearing-loss-causing tumors. Surgical planning must consider contralateral hearing."
        )
        if truthy(data.get("contralateralHearingLoss")):
            urgent_flags.append(
                "NF2 with contralateral hearing loss: Only-hearing ear situation. Hearing preservation is paramount — auditory brainstem implant (ABI) planning may be required."
            )
        return {
            "primaryRecommendation": "multidisciplinary_nf2",
            "recommendationTitle": "Multidisciplinary NF2 Management",
            "rationale": (
                "NF2-associated vestibular schwannomas require specialized multidisciplinary management. "
                "Bevacizumab may improve hearing and reduce tumor growth. SRS is a treatment option for "
                "enlarging tumors or those causing hearing loss (CNS 2025, Level III)."
            ),
            "evidenceLevel": "III",
            "guidelineSource": "CNS 2025 Vestibular Schwannoma Guidelines (Olson JJ et al., Neurosurgery 2025)",
            "hearingPreservationCounseling": [
                "NF2: Hearing preservation is the primary goal of management.",
                "Bevacizumab (anti-VEGF): Evidence for hearing improvement and tumor stabilization in NF2.",
                "SRS: Option for enlarging tumors — counsel on hearing preservation rates (moderately high at 2–5 years).",
                "Auditory brainstem implant (ABI) planning if hearing loss is anticipated.",
            ],
            "surgicalNotes": [
                "Surgery in NF2: Subtotal resection (STR) followed by SRS may preserve facial nerve function.",
                "Microsurgical resection after prior SRS: Increased likelihood of STR and decreased facial nerve function.",
            ],
            "srsNotes": [
                "SRS cochlear dose constraint: <4 Gy single fraction, <35 Gy fractionated.",
                "Single fraction SRS preferred over hypofractionated SRS for decreased cranial nerve dysfunction (CNS 2025).",
            ],
            "observationNotes": [
                "Annual MRI surveillance for NF2 tumors not requiring immediate intervention.",
            ],
            "monitoringPlan": [
                "Annual MRI with gadolinium",
                "Annual audiogram",
                "Multidisciplinary NF2 clinic follow-up",
                "Genetic counseling for family members",
            ],
            "urgentFlags": urgent_flags,
            "warnings": warnings,
            "nextSteps": [
                "Refer to NF2 multidisciplinary center",
                "Neurology, neurosurgery, otolaryngology, and audiology co-management",
                "Genetic counseling",
                "Consider bevacizumab trial if hearing deterioration",
                "ABI planning consultation if bilateral hearing loss anticipated",
            ],
            "references": _get_vs_references(),
        }

    # ── Large tumor (>3 cm) — surgery preferred ───────────────────────────
    if data.get("tumorSizeClass") == "large" or num(data.get("tumorSizeCm"), 0) > 3:
        urgent_flags.append(
            "Large tumor (>3 cm): Brainstem compression risk. Surgical resection is typically indicated."
        )
        if num(data.get("facialNerveFunctionHB"), 0) > 2:
            warnings.append(
                "Facial nerve function already compromised (HB >2): Intraoperative cranial nerve monitoring essential."
            )
        surgical_notes.append(
            "Large VS: Subtotal resection (STR) + adjuvant SRS may be considered to preserve facial nerve function."
        )
        surgical_notes.append(
            "Intraoperative facial nerve monitoring is standard of care."
        )
        surgical_notes.append(
            "Cystic VS: Lower complete resection rates and inferior immediate postoperative facial nerve outcomes (CNS 2025)."
        )
        if truthy(data.get("cysticComponent")):
            warnings.append(
                "Cystic VS: Associated with rapid growth, lower complete resection rates, and inferior immediate postoperative facial nerve outcomes."
            )

        return _build_surgery_recommendation(
            data,
            urgent_flags,
            warnings,
            surgical_notes,
            srs_notes,
            observation_notes,
            monitoring_plan,
            hearing_preservation_counseling,
        )

    # ── Intracanalicular or small (<1.5 cm) — observation vs SRS ─────────
    if data.get("tumorSizeClass") in ("intracanalicular", "small"):
        # Hearing preservation counseling for serviceable hearing
        if truthy(data.get("serviceableHearing")):
            hearing_preservation_counseling.append(
                "Serviceable hearing + observation: HP rate >75% at 2 years, >50% at 5 years, >25% at 10 years (CNS 2025, Level III)."
            )
            hearing_preservation_counseling.append(
                "Serviceable hearing + SRS (single fraction): HP rate >50% at 2 and 5 years, >25% at 10 years. Better outcomes with cochlear dose ≤4 Gy, marginal dose ≤13 Gy, and Class A/GR I status (CNS 2025, Level III)."
            )
            hearing_preservation_counseling.append(
                "Serviceable hearing + microsurgery: HP rate >25% immediately and at 2, 5, 10 years. Better outcomes with Class A/GR I status, smaller tumor, and fundal CSF cap present (CNS 2025, Level III)."
            )
            hearing_preservation_counseling.append(
                "IMPORTANT: For sporadic intracanalicular or <2 cm VS with hearing preservation goal — SRS is NOT superior to observation for hearing preservation (CNS 2025, Level III)."
            )

        # No growth on observation — continue observation
        if truthy(data.get("priorObservation")) and not truthy(data.get("tumorGrowthOnObservation")):
            observation_notes.append(
                "No tumor growth on observation: Continue active surveillance."
            )
            observation_notes.append(
                "MRI every 12 months × 3 years, then every 2 years if stable."
            )
            return _build_observation_recommendation(
                data,
                urgent_flags,
                warnings,
                surgical_notes,
                srs_notes,
                observation_notes,
                monitoring_plan,
                hearing_preservation_counseling,
            )

        # Growth documented — offer treatment
        if truthy(data.get("tumorGrowthOnObservation")):
            warnings.append(
                "Tumor growth documented on observation: Treatment should be discussed. SRS or microsurgery depending on patient factors."
            )

        # Default for small/intracanalicular: observation or SRS
        if not truthy(data.get("tumorGrowthOnObservation")) and not truthy(data.get("priorObservation")):
            return _build_observation_recommendation(
                data,
                urgent_flags,
                warnings,
                surgical_notes,
                srs_notes,
                observation_notes,
                monitoring_plan,
                hearing_preservation_counseling,
            )

    # ── Medium tumor (1.5–3 cm) — shared decision-making ─────────────────
    if data.get("tumorSizeClass") == "medium":
        if truthy(data.get("serviceableHearing")) and truthy(data.get("hearingPreservationPriority")):
            srs_notes.append(
                "Medium VS with serviceable hearing: SRS may offer hearing preservation rates comparable to observation at 2–5 years."
            )
            srs_notes.append(
                "Cochlear dose constraint: Single fraction <4 Gy, fractionated <35 Gy (CNS 2025)."
            )
            srs_notes.append(
                "Single fraction SRS preferred over hypofractionated SRS for decreased cranial nerve dysfunction."
            )
            return _build_srs_recommendation(
                data,
                urgent_flags,
                warnings,
                surgical_notes,
                srs_notes,
                observation_notes,
                monitoring_plan,
                hearing_preservation_counseling,
            )

        if truthy(data.get("trigeminalNeuralgiaSymptoms")):
            surgical_notes.append(
                "Trigeminal neuralgia symptoms: Surgical resection may better relieve symptoms compared to SRS (CNS 2025, Level III)."
            )
            return _build_surgery_recommendation(
                data,
                urgent_flags,
                warnings,
                surgical_notes,
                srs_notes,
                observation_notes,
                monitoring_plan,
                hearing_preservation_counseling,
            )

    # ── Prior SRS — retreatment considerations ────────────────────────────
    if truthy(data.get("priorSRS")):
        warnings.append(
            "Prior SRS: Microsurgical resection after SRS carries increased likelihood of subtotal resection (STR) and decreased facial nerve function (CNS 2025, Level III)."
        )
        surgical_notes.append(
            "Post-SRS surgery: STR + facial nerve preservation is the primary goal. Complete resection may not be achievable."
        )

    # ── Default: SRS for medium tumors or growing small tumors ───────────
    return _build_srs_recommendation(
        data,
        urgent_flags,
        warnings,
        surgical_notes,
        srs_notes,
        observation_notes,
        monitoring_plan,
        hearing_preservation_counseling,
    )
