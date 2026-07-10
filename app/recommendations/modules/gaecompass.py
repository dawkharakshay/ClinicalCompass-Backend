"""Geniculate Artery Embolization (GAE) — candidacy for knee osteoarthritis.

Authored net-new: unlike every other compass, the legacy app had **no** GAE
result-generation logic to port (``lib/gaeLogic.ts`` never existed — the old
``gae-compass`` module was an embedded external iframe). This engine derives a
candidacy assessment directly from the module's own intake form and the
published evidence the appeal-letter already cites (Okuno 2017, Bagla 2020,
Landers RCT 2021, ACR Appropriateness 2022, AOSSM/AAOS 2023).

Clinical model (evidence-based, refractory knee OA):
  * GAE targets mild-to-moderate knee OA (KL grade 2–3) with chronic pain
    refractory to ≥6 months of conservative therapy, in patients who are not
    surgical candidates or wish to defer arthroplasty.
  * Absolute exclusions (procedure should not proceed): active knee infection,
    inflammatory arthritis (GAE is for degenerative OA), uncorrected coagulopathy.
  * Relative exclusion: significant meniscal tear (mechanical symptoms may not
    respond to embolization of synovial neovascularity).
"""

from __future__ import annotations

import math

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "gaecompass"

EVIDENCE = [
    {
        "title": "Transcatheter Arterial Embolization of Geniculate Arteries for Knee OA (Okuno Y, et al.)",
        "source": "Okuno Y, Korchi AM, Shinjo T, Kato S.",
        "description": "Cardiovasc Intervent Radiol. 2017;40(3):411-418. Prospective study — VAS 7.4→2.4 at 12 months. PMID: 27921154",
        "pmid": "27921154",
    },
    {
        "title": "Genicular Artery Embolization for Knee OA: Multicenter Prospective Trial (Bagla S, et al.)",
        "source": "Bagla S, Piechowiak R, Sajan A, et al.",
        "description": "J Vasc Interv Radiol. 2020;31(7):1096-1102. 70% responder rate, durable relief at 12 months. PMID: 32340874",
        "pmid": "32340874",
    },
    {
        "title": "Genicular Artery Embolization vs Sham for Knee OA: Randomized Controlled Trial (Landers S, et al.)",
        "source": "Landers S, Hely R, Hely A, et al.",
        "description": "Cardiovasc Intervent Radiol. 2021;44(6):853-863. Superiority over sham for pain/function at 6 months. PMID: 33506278",
        "pmid": "33506278",
    },
    {
        "title": "ACR Appropriateness Criteria: Management of Knee Osteoarthritis",
        "source": "American College of Radiology",
        "description": "GAE appropriate for moderate-to-severe knee OA refractory to conservative therapy in non-surgical candidates. Updated 2022.",
        "pmid": None,
    },
    {
        "title": "AOSSM/AAOS Position Statement on Genicular Artery Embolization",
        "source": "American Orthopaedic Society for Sports Medicine / AAOS",
        "description": "GAE recognized as an emerging minimally invasive option for symptomatic knee OA after failed conservative therapy. 2023.",
        "pmid": None,
    },
]

# Exclusion attestations that must be affirmed for the procedure to proceed.
# The form phrases each as a positive "no <X>" checkbox → True means satisfied.
_ABSOLUTE_EXCLUSIONS = [
    ("noInfection", "Active knee/systemic infection",
     "Active infection — GAE contraindicated until fully treated"),
    ("noInflammatoryArthritis", "Inflammatory arthritis (e.g. RA, gout)",
     "Inflammatory arthritis — GAE is indicated for degenerative OA, not inflammatory disease"),
    ("noCoagulopathy", "Uncorrected coagulopathy",
     "Uncorrected coagulopathy — correct before any transcatheter embolization"),
]


def assess(data: dict) -> dict:
    key_findings: list[str] = []
    warnings: list[str] = []
    contraindications: list[str] = []
    eligibility: list[dict] = []
    score = 0

    # ── Kellgren–Lawrence radiographic grade (int, "0".."4") ──────────────────
    kl_raw = num(data.get("klGrade"), -1.0)
    kl = int(kl_raw) if kl_raw >= 0 and not math.isnan(kl_raw) else None
    if kl in (2, 3):
        score += 30
        key_findings.append(
            f"Kellgren–Lawrence grade {kl} — the mild-to-moderate OA range with the strongest GAE evidence (RCT + prospective)"
        )
    elif kl == 4:
        score += 10
        warnings.append(
            "KL grade 4 (severe/bone-on-bone) — less robust GAE evidence; evaluate for arthroplasty and set expectations accordingly"
        )
    elif kl == 1:
        score += 5
        warnings.append(
            "KL grade 1 (doubtful OA) — limited structural disease; confirm pain is OA-driven before GAE"
        )
    elif kl == 0:
        warnings.append(
            "KL grade 0 (no radiographic OA) — GAE is not indicated without established osteoarthritis"
        )
    else:
        warnings.append("Kellgren–Lawrence grade not provided — radiographic staging is required for candidacy")

    # ── Conservative therapy refractoriness (core indication) ─────────────────
    if truthy(data.get("conservativeTherapyFailed")):
        score += 25
        key_findings.append(
            "Refractory to conservative therapy — the primary indication for GAE"
        )
    else:
        warnings.append(
            "Conservative therapy not documented as failed — exhaust first-line management (PT, NSAIDs, injections) before GAE"
        )

    if truthy(data.get("symptomDurationOver6Months")):
        score += 10
        key_findings.append("Chronic symptoms >6 months — adequate duration for a GAE trial")
    else:
        warnings.append("Symptoms <6 months — ensure an adequate conservative trial before proceeding")

    # ── Symptom burden ────────────────────────────────────────────────────────
    pain = num(data.get("painScore"), 0.0)
    if pain >= 5:
        score += 10
        key_findings.append(f"Moderate-to-severe pain (intensity {pain:g}/10) — appropriate symptom target")
    functional = num(data.get("functionalLimitation"), 0.0)
    qol = num(data.get("qolImpact"), 0.0)
    if functional >= 5 or qol >= 5:
        score += 5
        key_findings.append("Substantial functional/quality-of-life impact")

    # KOOS (0 worst – 100 best) and Oxford Knee Score (0 worst – 48 best):
    # low values indicate a high symptom burden that GAE is meant to address.
    koos = num(data.get("koosScore"), -1.0)
    if 0 <= koos <= 50:
        score += 10
        key_findings.append(f"KOOS {koos:g} — high symptom burden consistent with GAE candidacy")
    oxford = num(data.get("oxfordKneeScore"), -1.0)
    if 0 <= oxford <= 27:
        score += 5
        key_findings.append(f"Oxford Knee Score {oxford:g} — moderate-to-severe impairment")

    if truthy(data.get("subchondralDisruption")):
        score += 5
        key_findings.append("Subchondral changes present — correlates with the neovascular pain generators GAE targets")

    # ── Exclusion / eligibility gates ─────────────────────────────────────────
    absolute_present = False
    for field, label, message in _ABSOLUTE_EXCLUSIONS:
        satisfied = truthy(data.get(field))
        eligibility.append({"key": label, "value": "Excluded" if satisfied else "NOT CONFIRMED"})
        if not satisfied:
            absolute_present = True
            contraindications.append(message)

    meniscal_ok = truthy(data.get("noMeniscalTear"))
    eligibility.append({"key": "Significant meniscal tear", "value": "Excluded" if meniscal_ok else "NOT CONFIRMED"})
    if not meniscal_ok:
        score -= 10
        warnings.append(
            "Possible significant meniscal tear — mechanical symptoms may not respond to GAE; consider orthopedic evaluation"
        )

    score = max(0, min(100, score))

    # ── Recommendation tier ───────────────────────────────────────────────────
    if absolute_present:
        score = min(score, 20)
        recommendation = "Not a Candidate — Exclusion Criteria Present"
        candidacy_label = "Not a candidate"
        guideline_class = "GAE should not proceed until the flagged absolute exclusions are resolved."
        clinical_rationale = (
            "One or more absolute exclusion criteria are not confirmed. Address these before "
            "reconsidering geniculate artery embolization."
        )
        next_steps = [
            "Resolve or exclude the flagged contraindications (infection, inflammatory arthritis, coagulopathy)",
            "Reassess candidacy once eligibility criteria are met",
        ]
    elif score >= 70:
        recommendation = "Strong Candidate for GAE"
        candidacy_label = "Strong candidate"
        guideline_class = "Reasonable — supported by RCT (Landers 2021) and prospective evidence (Okuno 2017, Bagla 2020)."
        clinical_rationale = (
            "Mild-to-moderate knee OA refractory to conservative therapy with meaningful symptom burden "
            "and no exclusion criteria — a favorable profile for genicular artery embolization."
        )
        next_steps = [
            "Confirm patent geniculate arterial anatomy with CT angiography / catheter angiography",
            "Shared decision-making: expected 60–70% responder rate, benefit durable to 12 months",
            "Document conservative-therapy failure for prior authorization",
        ]
    elif score >= 50:
        recommendation = "Reasonable Candidate for GAE"
        candidacy_label = "Reasonable candidate"
        guideline_class = "May be considered after multidisciplinary discussion and shared decision-making."
        clinical_rationale = (
            "The clinical profile supports GAE, though one or more factors are less than ideal. "
            "Individualize after reviewing alternatives with the patient."
        )
        next_steps = [
            "Multidisciplinary review (interventional radiology + orthopedics)",
            "Optimize any outstanding conservative measures",
            "CT angiography for procedural planning if proceeding",
        ]
    elif score >= 30:
        recommendation = "Borderline — Individualized Decision"
        candidacy_label = "Borderline"
        guideline_class = "Limited/indeterminate benefit — individualized decision."
        clinical_rationale = (
            "Candidacy is borderline: the symptom or radiographic profile is not clearly aligned with "
            "the populations that benefited in published GAE studies."
        )
        next_steps = [
            "Reassess radiographic grade and symptom burden",
            "Ensure conservative therapy is fully exhausted",
            "Consider orthopedic co-evaluation",
        ]
    else:
        recommendation = "Not a Candidate at This Time"
        candidacy_label = "Not a candidate"
        guideline_class = "Insufficient indication — GAE not supported by current profile."
        clinical_rationale = (
            "The current profile does not support GAE — typically insufficient structural disease, "
            "inadequate conservative trial, or low symptom burden."
        )
        next_steps = [
            "Continue/optimize conservative management",
            "Reassess if symptoms progress or radiographic OA advances",
        ]

    return {
        "recommendation": recommendation,
        "candidacyScore": score,
        "candidacyLabel": candidacy_label,
        "clinicalRationale": clinical_rationale,
        "guidelineClass": guideline_class,
        "keyFindings": key_findings,
        "eligibilityAssessment": eligibility,
        "warnings": warnings,
        "contraindications": contraindications,
        "nextSteps": next_steps,
        "guidelineSource": "SIR / ACR Appropriateness Criteria; AOSSM/AAOS 2023 (emerging evidence)",
    }
