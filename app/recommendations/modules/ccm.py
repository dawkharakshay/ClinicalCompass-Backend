"""Cerebral Cavernous Malformation (CCM) Compass.

Ported 1:1 from old_static_code/client/src/lib/ccmLogic.ts (assessCCM).

Based on:
- Angioma Alliance / CNS 2025 Updated Consensus Recommendations for CCM Management
- Akers A et al. Synopsis of Guidelines for CCM (Neurosurgery 2017)
- AHA/ASA 2021 Stroke Prevention Guidelines
- Al-Shahi Salman R et al. Lancet Neurol 2012 (natural history)
- Horne MA et al. Lancet Neurol 2016 (meta-analysis)
- Josephson CB et al. Neurology 2011 (seizure risk)

PMIDs: 28282516, 34025742, 22265208, 26708940, 21536040
"""

from __future__ import annotations

from app.recommendations.jslib import truthy

LOGIC_KEY = "ccm"


def _get_ccm_references() -> list[dict]:
    return [
        {
            "citation": (
                "Akers A et al. Synopsis of Guidelines for the Clinical Management of "
                "Cerebral Cavernous Malformations: Consensus Recommendations Based on "
                "Systematic Literature Review by the Angioma Alliance Scientific Advisory "
                "Board Clinical Experts Panel. Neurosurgery. 2017;80(5):665-680."
            ),
            "pmid": "28282516",
        },
        {
            "citation": (
                "Al-Shahi Salman R et al. Untreated Clinical Course of Cerebral Cavernous "
                "Malformations: A Prospective, Population-Based Cohort Study. Lancet Neurol. "
                "2012;11(3):217-224."
            ),
            "pmid": "22265208",
        },
        {
            "citation": (
                "Horne MA et al. Clinical Course of Untreated Cerebral Cavernous "
                "Malformations: A Meta-Analysis of Individual Patient Data. Lancet Neurol. "
                "2016;15(2):166-173."
            ),
            "pmid": "26708940",
        },
        {
            "citation": (
                "Josephson CB et al. Seizure Risk from Cavernous or Arteriovenous "
                "Malformations: Prospective Population-Based Study. Neurology. "
                "2011;76(18):1548-1554."
            ),
            "pmid": "21536040",
        },
        {
            "citation": (
                "Kleindorfer DO et al. 2021 Guideline for the Prevention of Stroke in "
                "Patients with Stroke and TIA: AHA/ASA Guideline. Stroke. "
                "2021;52(7):e364-e467."
            ),
            "pmid": "34025742",
        },
        {
            "citation": (
                "Lunsford LD et al. Stereotactic Radiosurgery for Cerebral Cavernous "
                "Malformations: A Systematic Review and Meta-Analysis. J Neurosurg. "
                "2017;126(4):1088-1099."
            ),
        },
        {
            "citation": (
                "Dammann P et al. Outcome After Conservative Management or Surgical "
                "Treatment for New-Onset Epilepsy in Cerebral Cavernous Malformation. "
                "J Neurosurg. 2017;126(4):1303-1311."
            ),
        },
    ]


def assess(data: dict) -> dict:
    location = data.get("location")
    ccm_type = data.get("ccmType")
    hemorrhage_status = data.get("hemorrhageStatus")
    seizure_status = data.get("seizureStatus")
    known_variant = data.get("knownCCMGeneVariant")
    surgical_risk = data.get("surgicalRisk")

    urgent_flags: list[str] = []
    warnings: list[str] = []
    surgical_considerations: list[str] = []
    radiosurgery_considerations: list[str] = []
    medical_management: list[str] = []
    genetic_counseling: list[str] = []
    monitoring_plan: list[str] = []

    # ── Urgent flags ──────────────────────────────────────────────────────────
    if truthy(data.get("spinalCM")) and truthy(data.get("acuteNeurologicImpairment")):
        urgent_flags.append(
            "Acute spinal CM hemorrhage with rapid neurological deterioration: Urgent "
            "surgical resection may be considered (subject to patient comorbidities and "
            "preferences)."
        )
    if truthy(data.get("neurologicDeficit")) and hemorrhage_status == "recurrent_hemorrhage":
        urgent_flags.append(
            "Recurrent hemorrhage with neurologic deficit: Surgical evaluation urgently "
            "recommended."
        )
    if known_variant == "ccm3":
        warnings.append(
            "CCM3 mutation: Associated with higher hemorrhage rate and more aggressive "
            "clinical course. Closer surveillance warranted."
        )

    # ── Genetic counseling ────────────────────────────────────────────────────
    if ccm_type == "familial" or truthy(data.get("familyHistory")):
        genetic_counseling.append(
            "Familial CCM: Genetic testing for CCM1, CCM2, CCM3 pathogenic variants is "
            "recommended (CNS 2025)."
        )
        genetic_counseling.append(
            "Autosomal dominant inheritance: Counsel on 50% risk to first-degree relatives."
        )
        genetic_counseling.append(
            "At-risk family members: Genetic testing can guide healthcare decisions. "
            "Genetic specialist consultation recommended before screening asymptomatic "
            "individuals."
        )
        genetic_counseling.append(
            "Psychological consequences of diagnostic testing: Counsel asymptomatic "
            "at-risk individuals before testing."
        )
        if truthy(data.get("pregnancyStatus")):
            genetic_counseling.append(
                "Pregnancy with familial/multifocal CCM: Consider genetic counseling "
                "before pregnancy."
            )

    # ── Pregnancy considerations ──────────────────────────────────────────────
    if truthy(data.get("pregnancyStatus")):
        warnings.append(
            "Pregnancy: Risk of neurological symptoms from CCM is likely not different "
            "than non-pregnant state (CNS 2025, Class IIb, Level C)."
        )
        warnings.append(
            "Surgery for asymptomatic CM with goal of safer pregnancy is NOT recommended "
            "(CNS 2025, Class III)."
        )
        if seizure_status != "no_seizure":
            medical_management.append(
                "Seizure disorder on ASM + pregnancy: Folate supplementation should be "
                "considered (CNS 2025)."
            )

    # ── Headache only — no hemorrhage, no seizure ─────────────────────────────
    if truthy(data.get("headacheOnly")) and not truthy(data.get("symptomatic")):
        medical_management.append(
            "CCM with headache and no secondary cause: Classify and treat according to "
            "standard headache practice (CNS 2025)."
        )
        medical_management.append(
            "Non-aspirin NSAIDs can be used with caution for nonhemorrhagic CCM lesions."
        )

    # ── Genetic testing first — familial criteria ─────────────────────────────
    if (ccm_type == "familial" or truthy(data.get("familyHistory"))) and not truthy(
        known_variant
    ):
        return {
            "primaryRecommendation": "genetic_testing_first",
            "recommendationTitle": "Genetic Testing — Familial CCM Criteria Met",
            "rationale": (
                "Clinical criteria for familial CCM are met. Genetic testing for CCM1, "
                "CCM2, CCM3 pathogenic variants is recommended. Pathogenic variant "
                "identification guides counseling of at-risk family members and management "
                "decisions."
            ),
            "evidenceClass": "IIa",
            "evidenceLevel": "C",
            "guidelineSource": (
                "CNS 2025 CCM Consensus; Akers A et al. Neurosurgery 2017 (PMID 28282516)"
            ),
            "surgicalConsiderations": surgical_considerations,
            "radiosurgeryConsiderations": radiosurgery_considerations,
            "medicalManagement": medical_management,
            "geneticCounseling": genetic_counseling,
            "monitoringPlan": [
                "MRI brain with SWI (susceptibility-weighted imaging) at diagnosis",
                "Annual MRI surveillance for known CCM",
                "Genetic specialist consultation",
            ],
            "urgentFlags": urgent_flags,
            "warnings": warnings,
            "nextSteps": [
                "Medical genetics consultation for CCM1/2/3 testing",
                "MRI brain with SWI for complete lesion inventory",
                "Counsel at-risk family members",
                "Neurosurgery consultation for symptomatic lesions",
            ],
            "references": _get_ccm_references(),
        }

    # ── Asymptomatic CCM — observation vs surgery ─────────────────────────────
    if truthy(data.get("incidentalFinding")) or (
        not truthy(data.get("symptomatic")) and not truthy(seizure_status)
    ):
        # Asymptomatic in eloquent/deep/brainstem or multiple — no surgery
        if (
            location == "eloquent_cortical"
            or location == "deep_subcortical"
            or location == "brainstem"
            or truthy(data.get("multiplelesions"))
        ):
            return {
                "primaryRecommendation": "observation",
                "recommendationTitle": (
                    "Observation — Asymptomatic CCM in Eloquent/Deep Location"
                ),
                "rationale": (
                    "Surgical resection is NOT recommended for asymptomatic CM in "
                    "eloquent, deep, or brainstem areas, or for multiple asymptomatic CMs "
                    "(CNS 2025, Class III). Annual hemorrhage risk for unruptured CCM is "
                    "approximately 0.5–1% per year."
                ),
                "evidenceClass": "III",
                "evidenceLevel": "B",
                "guidelineSource": (
                    "CNS 2025 CCM Consensus; Al-Shahi Salman R et al. Lancet Neurol 2012 "
                    "(PMID 22265208)"
                ),
                "surgicalConsiderations": [
                    "Surgery NOT recommended for asymptomatic eloquent/deep/brainstem CCM.",
                    "Surgery NOT recommended for multiple asymptomatic CCMs.",
                    "Surgery NOT recommended with goal of safer pregnancy.",
                ],
                "radiosurgeryConsiderations": [
                    "Radiosurgery NOT recommended for asymptomatic CCMs (CNS 2025, Class III).",
                ],
                "medicalManagement": [
                    *medical_management,
                    "Non-aspirin NSAIDs can be used with caution.",
                    "Avoid anticoagulation unless strong indication (DVT/PE) — discuss "
                    "risk/benefit.",
                ],
                "geneticCounseling": genetic_counseling,
                "monitoringPlan": [
                    "MRI brain with SWI annually × 3 years, then every 2 years if stable",
                    "Clinical assessment for new symptoms at each visit",
                    "Patient education: Report new headaches, seizures, focal deficits "
                    "immediately",
                ],
                "urgentFlags": urgent_flags,
                "warnings": [
                    w
                    for w in [
                        *warnings,
                        "Annual hemorrhage risk: ~0.5–1% for unruptured CCM; higher for "
                        "brainstem location (~2–3%/year).",
                        "CCM3 mutation: Higher hemorrhage rate — closer surveillance "
                        "recommended."
                        if known_variant == "ccm3"
                        else "",
                    ]
                    if truthy(w)
                ],
                "nextSteps": [
                    "Annual MRI with SWI",
                    "Patient education on warning symptoms",
                    "Neurosurgery follow-up annually",
                    "Genetic counseling if familial",
                ],
                "references": _get_ccm_references(),
            }

        # Asymptomatic in accessible noneloquent area — surgery may be considered
        if location == "noneloquent_cortical":
            surgical_considerations.append(
                "Solitary asymptomatic CM in easily accessible noneloquent area: Surgical "
                "resection MAY be considered to prevent future hemorrhage, reduce "
                "psychological burden, follow-up costs, and lifestyle/career considerations "
                "(CNS 2025, Class IIb)."
            )
            return {
                "primaryRecommendation": "observation",
                "recommendationTitle": (
                    "Observation (Surgery May Be Considered) — Accessible Noneloquent CCM"
                ),
                "rationale": (
                    "Solitary asymptomatic CM in easily accessible noneloquent area: "
                    "Observation is the default. Surgery may be considered after shared "
                    "decision-making, weighing future hemorrhage risk against surgical risk."
                ),
                "evidenceClass": "IIb",
                "evidenceLevel": "C",
                "guidelineSource": (
                    "CNS 2025 CCM Consensus; Akers A et al. Neurosurgery 2017 (PMID 28282516)"
                ),
                "surgicalConsiderations": surgical_considerations,
                "radiosurgeryConsiderations": [
                    "Radiosurgery not recommended for asymptomatic CCM.",
                ],
                "medicalManagement": medical_management,
                "geneticCounseling": genetic_counseling,
                "monitoringPlan": [
                    "MRI brain with SWI every 6–12 months",
                    "Shared decision-making discussion annually",
                ],
                "urgentFlags": urgent_flags,
                "warnings": warnings,
                "nextSteps": [
                    "Shared decision-making: Discuss observation vs surgery",
                    "MRI brain with SWI in 6 months",
                    "Neurosurgery consultation for surgical risk assessment",
                ],
                "references": _get_ccm_references(),
            }

    # ── Refractory seizure — surgery recommended ──────────────────────────────
    if seizure_status == "refractory_seizure":
        surgical_considerations.append(
            "Medically refractory epilepsy with epileptogenic CM identified: Early surgical "
            "resection for seizure control is beneficial (CNS 2025, Class IIa, Level B)."
        )
        surgical_considerations.append(
            "Nonhemorrhagic CM (especially familial): Careful review by neurologist and EEG "
            "to confirm CM-seizure relationship before resection."
        )
        return {
            "primaryRecommendation": "surgical_resection",
            "recommendationTitle": "Surgical Resection — Medically Refractory Epilepsy",
            "rationale": (
                "Medically refractory epilepsy with epileptogenic CCM identified: Early "
                "surgical resection is beneficial for seizure control (CNS 2025, Class IIa, "
                "Level B). EEG and neurologist review required to confirm CM-seizure "
                "relationship."
            ),
            "evidenceClass": "IIa",
            "evidenceLevel": "B",
            "guidelineSource": (
                "CNS 2025 CCM Consensus; Josephson CB et al. Neurology 2011 (PMID 21536040)"
            ),
            "surgicalConsiderations": surgical_considerations,
            "radiosurgeryConsiderations": [
                "Laser thermal ablation: May be considered for smaller symptomatic CM "
                "causing seizures (CNS 2025).",
            ],
            "medicalManagement": [
                *medical_management,
                "First-time seizure from CM without associated hemorrhage: Conservative "
                "approach with ASM recommended (CNS 2025).",
            ],
            "geneticCounseling": genetic_counseling,
            "monitoringPlan": [
                "MRI brain with SWI postoperatively",
                "EEG monitoring postoperatively",
                "Neurology follow-up for seizure management",
                "Neuropsychological assessment",
            ],
            "urgentFlags": urgent_flags,
            "warnings": [
                *warnings,
                "Nonhemorrhagic CM: Confirm CM is the epileptogenic focus with EEG before "
                "surgery.",
                "Familial CCM: Higher risk of de novo CM genesis — continued surveillance "
                "required.",
            ],
            "nextSteps": [
                "Epilepsy surgery evaluation (video-EEG monitoring)",
                "Neurosurgery consultation",
                "Neuropsychological testing",
                "Confirm CM-seizure relationship with EEG",
                "Discuss laser thermal ablation as alternative if smaller lesion",
            ],
            "references": _get_ccm_references(),
        }

    # ── Brainstem CCM — second symptomatic bleed ──────────────────────────────
    if location == "brainstem" and hemorrhage_status == "recurrent_hemorrhage":
        surgical_considerations.append(
            "Brainstem CCM with second symptomatic bleed: Complete surgical resection may "
            "be offered (CNS 2025, Class IIa)."
        )
        surgical_considerations.append(
            "Brainstem CCM with single disabling bleed: Resection may be considered (CNS "
            "2025, Class IIb)."
        )
        return {
            "primaryRecommendation": "surgical_resection",
            "recommendationTitle": (
                "Surgical Resection — Brainstem CCM with Recurrent Hemorrhage"
            ),
            "rationale": (
                "Brainstem CCM with second symptomatic bleed: Complete surgical resection "
                "may be offered (CNS 2025, Class IIa). Annual re-hemorrhage risk after first "
                "bleed is approximately 3–5% for brainstem CCM."
            ),
            "evidenceClass": "IIa",
            "evidenceLevel": "C",
            "guidelineSource": (
                "CNS 2025 CCM Consensus; Horne MA et al. Lancet Neurol 2016 (PMID 26708940)"
            ),
            "surgicalConsiderations": surgical_considerations,
            "radiosurgeryConsiderations": [
                "Radiosurgery: May be considered for eloquent areas with unacceptably high "
                "surgical risk (CNS 2025, Class IIb).",
                "Radiosurgery evidence for brainstem CCM is limited — discuss with "
                "multidisciplinary team.",
            ],
            "medicalManagement": medical_management,
            "geneticCounseling": genetic_counseling,
            "monitoringPlan": [
                "MRI brain with SWI postoperatively",
                "Annual MRI surveillance if observation chosen",
                "Neurologic assessment at each visit",
            ],
            "urgentFlags": urgent_flags,
            "warnings": [
                *warnings,
                "Brainstem CCM surgery: High-risk procedure requiring experienced skull "
                "base neurosurgeon.",
                "Timing of surgery: Wait 4–6 weeks after acute hemorrhage for clot "
                "liquefaction (easier resection).",
            ],
            "nextSteps": [
                "Neurosurgery consultation at high-volume skull base center",
                "MRI brain with SWI (thin-cut brainstem protocol)",
                "Multidisciplinary neurovascular team review",
                "Discuss radiosurgery if surgical risk is prohibitive",
            ],
            "references": _get_ccm_references(),
        }

    # ── Symptomatic accessible CCM — surgery ─────────────────────────────────
    if truthy(data.get("symptomatic")) and (
        location == "noneloquent_cortical" or location == "spinal_dorsal_dorsolateral"
    ):
        surgical_considerations.append(
            "Symptomatic easily accessible CM lesions: Surgery may be considered (CNS 2025, "
            "Class IIb)."
        )
        if truthy(data.get("spinalCM")):
            surgical_considerations.append(
                "Dorsal or dorsolateral spinal CCM with exophytic or pial presentation: "
                "Surgical resection may be considered (CNS 2025)."
            )
            if truthy(data.get("acuteNeurologicImpairment")):
                surgical_considerations.append(
                    "Single acute neurological impairing event: Surgical resection may be "
                    "considered."
                )
            if truthy(data.get("progressiveNeurologicDeterioration")):
                surgical_considerations.append(
                    "Progressive neurological deterioration: Surgical resection may be "
                    "considered."
                )
        return {
            "primaryRecommendation": "surgical_resection",
            "recommendationTitle": "Surgical Resection — Symptomatic Accessible CCM",
            "rationale": (
                "Symptomatic CCM in easily accessible location: Surgery may be considered "
                "(CNS 2025, Class IIb). Surgical resection eliminates re-hemorrhage risk and "
                "may improve neurologic symptoms."
            ),
            "evidenceClass": "IIb",
            "evidenceLevel": "C",
            "guidelineSource": (
                "CNS 2025 CCM Consensus; Akers A et al. Neurosurgery 2017 (PMID 28282516)"
            ),
            "surgicalConsiderations": surgical_considerations,
            "radiosurgeryConsiderations": radiosurgery_considerations,
            "medicalManagement": medical_management,
            "geneticCounseling": genetic_counseling,
            "monitoringPlan": [
                "MRI brain/spine with SWI postoperatively",
                "Neurologic assessment at 6 weeks, 3 months, then annually",
            ],
            "urgentFlags": urgent_flags,
            "warnings": warnings,
            "nextSteps": [
                "Neurosurgery consultation",
                "MRI with SWI for surgical planning",
                "Shared decision-making discussion",
            ],
            "references": _get_ccm_references(),
        }

    # ── Eloquent/deep CCM with prior hemorrhage — radiosurgery option ─────────
    if (
        (location == "eloquent_cortical" or location == "deep_subcortical")
        and hemorrhage_status != "no_hemorrhage"
        and surgical_risk == "high"
    ):
        radiosurgery_considerations.append(
            "Solitary CM with previous symptomatic hemorrhage in eloquent area with "
            "unacceptably high surgical risk: Radiosurgery may be considered (CNS 2025, "
            "Class IIb)."
        )
        return {
            "primaryRecommendation": "radiosurgery_srs",
            "recommendationTitle": (
                "Stereotactic Radiosurgery — Eloquent CCM with High Surgical Risk"
            ),
            "rationale": (
                "Solitary CM with previous symptomatic hemorrhage in eloquent area with "
                "unacceptably high surgical risk: Radiosurgery may be considered (CNS 2025, "
                "Class IIb). Evidence is limited — multidisciplinary review required."
            ),
            "evidenceClass": "IIb",
            "evidenceLevel": "C",
            "guidelineSource": "CNS 2025 CCM Consensus; Lunsford LD et al. J Neurosurg 2017",
            "surgicalConsiderations": [
                "Surgery not recommended due to high surgical risk in eloquent location.",
            ],
            "radiosurgeryConsiderations": radiosurgery_considerations,
            "medicalManagement": medical_management,
            "geneticCounseling": genetic_counseling,
            "monitoringPlan": [
                "MRI brain with SWI at 6 months post-SRS, then annually",
                "Neurologic assessment at each visit",
            ],
            "urgentFlags": urgent_flags,
            "warnings": [
                *warnings,
                "SRS for CCM: Evidence is limited. Radiosurgery does NOT eliminate "
                "re-hemorrhage risk in the first 2 years.",
                "Asymptomatic CCM: Radiosurgery is NOT recommended.",
            ],
            "nextSteps": [
                "Radiation oncology consultation for SRS planning",
                "Multidisciplinary neurovascular team review",
                "Discuss observation vs SRS trade-offs",
            ],
            "references": _get_ccm_references(),
        }

    # ── Default: observation ──────────────────────────────────────────────────
    monitoring_plan.append("MRI brain with SWI every 6–12 months")
    monitoring_plan.append("Clinical assessment for new symptoms")

    return {
        "primaryRecommendation": "observation",
        "recommendationTitle": "Observation — Active Surveillance",
        "rationale": (
            "Observation with serial MRI is the default management for most CCMs without "
            "high-risk features. Annual hemorrhage risk for unruptured CCM is approximately "
            "0.5–1% per year."
        ),
        "evidenceClass": "IIa",
        "evidenceLevel": "B",
        "guidelineSource": (
            "CNS 2025 CCM Consensus; Al-Shahi Salman R et al. Lancet Neurol 2012 "
            "(PMID 22265208)"
        ),
        "surgicalConsiderations": surgical_considerations,
        "radiosurgeryConsiderations": radiosurgery_considerations,
        "medicalManagement": [
            *medical_management,
            "Non-aspirin NSAIDs can be used with caution for nonhemorrhagic CCM.",
            "Anticoagulation: Use only if strong indication — discuss risk/benefit with "
            "neurosurgery.",
        ],
        "geneticCounseling": genetic_counseling,
        "monitoringPlan": monitoring_plan,
        "urgentFlags": urgent_flags,
        "warnings": warnings,
        "nextSteps": [
            s
            for s in [
                "MRI brain with SWI (susceptibility-weighted imaging) for complete lesion "
                "inventory",
                "Neurosurgery follow-up annually",
                "Patient education: Report new headaches, seizures, or focal deficits "
                "immediately",
                "Genetic counseling referral" if ccm_type == "familial" else "",
            ]
            if truthy(s)
        ],
        "references": _get_ccm_references(),
    }
