"""Spine Surgery Perioperative Antithrombotic Management.

Ported 1:1 from old_static_code/client/src/lib/spineAntithromboticLogic.ts
(assessSpineAntithrombotic + helpers).
"""

from __future__ import annotations

from app.recommendations.jslib import truthy

LOGIC_KEY = "spineantithrombotic"

_DOACS = ["apixaban", "rivaroxaban", "dabigatran", "edoxaban"]


def _determine_prophylaxis_timing(data: dict) -> str:
    if data.get("bleedingRiskLevel") == "high":
        return (
            "Delay pharmacologic prophylaxis 48–72 hours postoperatively due to "
            "high bleeding risk. Use mechanical prophylaxis (SCDs) until "
            "pharmacologic prophylaxis is safe."
        )
    if data.get("procedureType") == "complex_multilevel":
        return (
            "Start pharmacologic VTE prophylaxis 48–72 hours postoperatively for "
            "complex multilevel spine surgery."
        )
    if data.get("procedureType") in ("lumbar_decompression", "minimally_invasive"):
        return (
            "Pharmacologic VTE prophylaxis not routinely required for simple "
            "decompression. Mechanical prophylaxis + early ambulation sufficient "
            "for low-risk patients."
        )
    return (
        "Start pharmacologic VTE prophylaxis 24–48 hours postoperatively when "
        "hemostasis is confirmed."
    )


def _determine_restart_timing(data: dict) -> str:
    if data.get("indicationForAnticoagulation") == "mechanical_heart_valve_high":
        return (
            "Restart therapeutic anticoagulation 24–48 hours postoperatively with "
            "LMWH bridging until therapeutic INR achieved. Cardiology consultation "
            "required."
        )
    if data.get("indicationForAnticoagulation") == "vte_acute":
        return (
            "Restart therapeutic anticoagulation 48–72 hours postoperatively when "
            "hemostasis is confirmed. Hematology consultation recommended."
        )
    if data.get("currentAnticoagulant") == "warfarin":
        return (
            "Restart warfarin evening of postoperative day 1 (when oral intake "
            "established). Bridge with LMWH if high-risk indication until INR "
            "therapeutic."
        )
    if data.get("currentAnticoagulant") in _DOACS:
        return (
            "Restart DOAC 48–72 hours postoperatively when hemostasis is confirmed "
            "and patient is ambulatory."
        )
    if data.get("currentAnticoagulant") == "aspirin_81":
        return (
            "Restart aspirin 81 mg postoperative day 1 (or as soon as oral intake "
            "established)."
        )
    if data.get("currentAnticoagulant") == "clopidogrel":
        return (
            "Restart clopidogrel 24–48 hours postoperatively when hemostasis is "
            "confirmed. Cardiology guidance for timing after PCI."
        )
    return (
        "Restart anticoagulation per indication-specific guidance when hemostasis "
        "is confirmed (typically 24–72 hours postoperatively)."
    )


def _determine_restart_timing_label(data: dict) -> str:
    if data.get("indicationForAnticoagulation") == "mechanical_heart_valve_high":
        return "24–48 hours postoperatively (high-risk valve)"
    if data.get("indicationForAnticoagulation") == "vte_acute":
        return "48–72 hours postoperatively (acute VTE)"
    if data.get("currentAnticoagulant") == "warfarin":
        return "Postoperative day 1 (evening)"
    if data.get("currentAnticoagulant") in _DOACS:
        return "48–72 hours postoperatively"
    return "24–72 hours postoperatively"


def _build_next_steps(data: dict) -> list[str]:
    steps: list[str] = [
        "Confirm hold duration and restart plan with prescribing physician",
        "Mechanical prophylaxis (SCDs) ordered preoperatively",
        "Anesthesia consultation for neuraxial anesthesia safety assessment",
    ]
    indication = data.get("indicationForAnticoagulation")
    if indication in ("mechanical_heart_valve_high", "recent_pci_des", "recent_acs"):
        steps.append(
            "Cardiology consultation for perioperative anticoagulation management"
        )
    if indication == "vte_acute":
        steps.append("Hematology consultation for perioperative VTE management")
    if data.get("vteRiskLevel") in ("high", "very_high"):
        steps.append(
            "Pharmacy consultation for LMWH dosing (weight-based, renal function)"
        )
    steps.append(
        "Patient education: Report new back pain, leg weakness, or bowel/bladder "
        "changes immediately postoperatively"
    )
    return steps


def _references() -> list[dict]:
    return [
        {
            "citation": "NASS Clinical Guidelines: Antithrombotic Therapy in Spine "
            "Surgery. North American Spine Society. 2025.",
        },
        {
            "citation": "Stevens SM et al. Antithrombotic Therapy for VTE Disease: "
            "Second Update of the CHEST Guideline and Expert Panel Report. Chest. "
            "2021;160(6):e545-e608.",
            "pmid": "36893661",
        },
        {
            "citation": "January CT et al. 2019 AHA/ACC/HRS Focused Update of the "
            "2014 AHA/ACC/HRS Guideline for the Management of Patients with Atrial "
            "Fibrillation. J Am Coll Cardiol. 2019;74(1):104-132.",
            "pmid": "31838335",
        },
        {
            "citation": "Douketis JD et al. Perioperative Management of Patients with "
            "Atrial Fibrillation Receiving a Direct Oral Anticoagulant (PAUSE "
            "Study). JAMA Intern Med. 2019;179(11):1469-1478.",
            "pmid": "31380891",
        },
        {
            "citation": "Douketis JD et al. Perioperative Bridging Anticoagulation "
            "in Patients with Atrial Fibrillation (BRIDGE Trial). N Engl J Med. "
            "2015;373(9):823-833.",
            "pmid": "26095867",
        },
        {
            "citation": "Carabini LM et al. A Randomized Controlled Trial of Topical "
            "Tranexamic Acid in Posterior Spinal Fusion Surgery. Spine. "
            "2018;43(23):1589-1595.",
            "pmid": "32386930",
        },
        {
            "citation": "Pumberger M et al. Incidence and Risk Factors of Symptomatic "
            "Spinal Epidural Hematoma After Spinal Surgery. Spine. "
            "2012;37(6):E399-E406.",
            "pmid": "22020607",
        },
    ]


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    warnings: list[str] = []
    preoperative_management: list[str] = []
    intraoperative_considerations: list[str] = []
    vte_prophylaxis: list[str] = []

    current = data.get("currentAnticoagulant")
    indication = data.get("indicationForAnticoagulation")

    # ── Urgent flags ──────────────────────────────────────────────────────────
    if truthy(data.get("emergencyProcedure")):
        urgent_flags.append(
            "Emergency spine surgery: Anticoagulation reversal may be required. "
            "Contact hematology/pharmacy urgently for reversal agent guidance."
        )
        if current == "warfarin" or current == "heparin_iv":
            urgent_flags.append(
                "Warfarin reversal: 4-factor PCC (Kcentra) preferred over FFP for "
                "urgent reversal. Target INR <1.5 before surgery."
            )
        if current in _DOACS:
            urgent_flags.append(
                "DOAC reversal: Andexanet alfa (Factor Xa inhibitors) or "
                "idarucizumab (dabigatran) for urgent reversal. Contact pharmacy."
            )

    if truthy(data.get("priorSpinalEpiduralHematoma")):
        urgent_flags.append(
            "Prior spinal epidural hematoma: Extremely high risk for recurrence. "
            "Neuraxial anesthesia and epidural catheter are contraindicated. "
            "Discuss with neurosurgery and anesthesia."
        )

    if indication in ("mechanical_heart_valve_high", "vte_acute"):
        urgent_flags.append(
            "High-risk indication for anticoagulation (mechanical mitral valve or "
            "acute VTE <3 months): Bridging therapy with LMWH or UFH is strongly "
            "recommended. Cardiology/hematology consultation required."
        )

    # ── Preoperative management by anticoagulant type ─────────────────────────
    hold_duration = "No anticoagulation to hold"
    bridging_recommendation = "Bridging not required"

    if current == "warfarin":
        hold_duration = (
            "Hold warfarin 5 days before surgery. Check INR day before — target "
            "INR <1.5."
        )
        preoperative_management.append(
            "Hold warfarin 5 days preoperatively. Check INR 1 day before surgery "
            "(target <1.5)."
        )
        preoperative_management.append(
            "If INR >1.5 on day before surgery: Consider low-dose vitamin K "
            "(1–2 mg oral) to normalize."
        )

        if indication in (
            "mechanical_heart_valve_high",
            "vte_acute",
            "af_high_risk",
        ):
            bridging_recommendation = (
                "Bridging with therapeutic LMWH (enoxaparin 1 mg/kg BID or "
                "1.5 mg/kg daily) recommended. Last dose 24h before surgery."
            )
            preoperative_management.append(
                "Bridging: Therapeutic LMWH starting when INR <2. Last dose 24 "
                "hours before surgery."
            )
        elif indication in ("af_moderate_risk", "mechanical_heart_valve_low"):
            bridging_recommendation = (
                "Bridging decision: Individualized. BRIDGE trial showed no benefit "
                "of bridging for AF patients with moderate risk — discuss with "
                "cardiology."
            )
            warnings.append(
                "BRIDGE trial (NEJM 2015): No significant difference in arterial "
                "thromboembolism with vs without bridging for AF patients "
                "undergoing surgery. Bridging increased major bleeding."
            )
        else:
            bridging_recommendation = (
                "Bridging NOT recommended for low-risk AF (CHA₂DS₂-VASc 0–1) or "
                "stable CAD."
            )
    elif current == "apixaban":
        hold_duration = (
            "Hold apixaban 72 hours (3 days) before high-risk surgery due to renal "
            "impairment."
            if truthy(data.get("renalImpairment"))
            else "Hold apixaban 48 hours (2 days) before high-risk spine surgery."
        )
        preoperative_management.append(hold_duration)
        preoperative_management.append(
            "No routine coagulation monitoring required. Anti-Xa level can be "
            "checked if timing uncertain."
        )
        bridging_recommendation = (
            "Bridging with LMWH generally NOT recommended for DOACs (no established "
            "benefit). Exception: mechanical heart valve or acute VTE."
        )
    elif current == "rivaroxaban":
        hold_duration = (
            "Hold rivaroxaban 72 hours before high-risk surgery (renal impairment)."
            if truthy(data.get("renalImpairment"))
            else "Hold rivaroxaban 48 hours before high-risk spine surgery."
        )
        preoperative_management.append(hold_duration)
        preoperative_management.append(
            "Rivaroxaban is taken with food — ensure last dose with evening meal."
        )
        bridging_recommendation = (
            "Bridging NOT recommended for DOACs unless mechanical heart valve or "
            "acute VTE."
        )
    elif current == "dabigatran":
        if truthy(data.get("renalImpairment")):
            hold_duration = (
                "Hold dabigatran 4–5 days before high-risk surgery (CrCl <30 "
                "mL/min — dabigatran is renally cleared)."
            )
            warnings.append(
                "Dabigatran is renally cleared. CrCl <30 mL/min: Hold 4–5 days. "
                "Consider switching to alternative anticoagulant."
            )
        else:
            hold_duration = (
                "Hold dabigatran 48–72 hours before high-risk spine surgery (CrCl "
                "≥50 mL/min)."
            )
        preoperative_management.append(hold_duration)
        bridging_recommendation = (
            "Bridging NOT recommended for DOACs unless mechanical heart valve or "
            "acute VTE."
        )
    elif current == "clopidogrel":
        hold_duration = "Hold clopidogrel 5–7 days before surgery."
        preoperative_management.append(hold_duration)
        if indication in ("recent_pci_des", "recent_acs"):
            urgent_flags.append(
                "Recent DES or ACS: Premature discontinuation of P2Y12 inhibitor "
                "increases risk of stent thrombosis. Cardiology consultation "
                "REQUIRED before holding clopidogrel."
            )
    elif current == "aspirin_plus_p2y12":
        hold_duration = (
            "DAPT: Hold P2Y12 inhibitor 5–7 days before surgery. Continue aspirin "
            "81 mg unless surgeon requests hold."
        )
        preoperative_management.append(hold_duration)
        urgent_flags.append(
            "DAPT: Cardiology consultation required before discontinuing P2Y12 "
            "inhibitor. Risk of stent thrombosis vs surgical bleeding must be "
            "individualized."
        )
    elif current == "aspirin_81":
        hold_duration = (
            "Aspirin 81 mg: Continue perioperatively for most spine procedures "
            "(NASS 2025). Hold only if surgeon requests for high-bleeding-risk "
            "procedures."
        )
        preoperative_management.append(hold_duration)
    elif current == "aspirin_325":
        hold_duration = (
            "Aspirin 325 mg: Hold 7 days before surgery. Consider switching to "
            "aspirin 81 mg if antiplatelet effect still required."
        )
        preoperative_management.append(hold_duration)
    elif current == "lmwh":
        hold_duration = (
            "Therapeutic LMWH: Hold last dose 24 hours before surgery. "
            "Prophylactic LMWH: Hold 12 hours before surgery."
        )
        preoperative_management.append(hold_duration)

    # ── Intraoperative considerations ─────────────────────────────────────────
    intraoperative_considerations.append(
        "Cell salvage: Consider for complex multilevel or high-blood-loss "
        "procedures."
    )
    intraoperative_considerations.append(
        "Tranexamic acid (TXA): Consider IV TXA 10–15 mg/kg at induction to reduce "
        "intraoperative blood loss (NASS 2025, Level II)."
    )
    if data.get("procedureType") == "complex_multilevel":
        intraoperative_considerations.append(
            "Complex multilevel surgery: Neuromonitoring (SSEP/MEP) recommended. "
            "Maintain MAP ≥65 mmHg."
        )
    if truthy(data.get("estimatedBloodLossHigh")):
        intraoperative_considerations.append(
            "Expected high blood loss: Pre-donate autologous blood if time permits. "
            "Coordinate with anesthesia for massive transfusion protocol."
        )

    # ── VTE prophylaxis ───────────────────────────────────────────────────────
    prophylaxis_timing = _determine_prophylaxis_timing(data)

    vte_risk = data.get("vteRiskLevel")
    if vte_risk == "low":
        vte_prophylaxis.append(
            "Mechanical prophylaxis: Sequential compression devices (SCDs) "
            "intraoperatively and postoperatively."
        )
        vte_prophylaxis.append(
            "Early ambulation: Ambulate within 24 hours postoperatively."
        )
        vte_prophylaxis.append(
            "Pharmacologic prophylaxis: Not routinely recommended for low-risk "
            "spine procedures (NASS 2025)."
        )
    elif vte_risk == "moderate":
        vte_prophylaxis.append(
            "Mechanical prophylaxis: SCDs intraoperatively and postoperatively."
        )
        vte_prophylaxis.append(
            "Pharmacologic prophylaxis: LMWH (enoxaparin 40 mg daily) or UFH 5000 "
            "units TID starting 24–48 hours postoperatively."
        )
        vte_prophylaxis.append(
            "Continue pharmacologic prophylaxis for 7–14 days or until ambulatory."
        )
    elif vte_risk in ("high", "very_high"):
        vte_prophylaxis.append(
            "Mechanical prophylaxis: SCDs intraoperatively and postoperatively."
        )
        vte_prophylaxis.append(
            "Pharmacologic prophylaxis: LMWH (enoxaparin 40 mg daily) starting "
            "24–48 hours postoperatively."
        )
        vte_prophylaxis.append(
            "Extended prophylaxis: Consider 28–35 days for very high-risk patients "
            "(active cancer, prior VTE, immobility)."
        )
        if truthy(data.get("activeCancer")):
            vte_prophylaxis.append(
                "Active cancer: Extended LMWH prophylaxis for 28–35 days "
                "postoperatively (NASS 2025, Level II)."
            )
        if truthy(data.get("priorVTE")):
            vte_prophylaxis.append(
                "Prior VTE: Restart therapeutic anticoagulation as soon as "
                "hemostasis is achieved (typically 48–72 hours postoperatively)."
            )

    # ── Postoperative restart ─────────────────────────────────────────────────
    restart_recommendation = _determine_restart_timing(data)
    restart_timing = _determine_restart_timing_label(data)

    return {
        "preoperativeManagement": preoperative_management,
        "holdDuration": hold_duration,
        "bridgingRecommendation": bridging_recommendation,
        "intraoperativeConsiderations": intraoperative_considerations,
        "vteProphylaxis": vte_prophylaxis,
        "prophylaxisTiming": prophylaxis_timing,
        "restartRecommendation": restart_recommendation,
        "restartTiming": restart_timing,
        "evidenceLevel": "II",
        "guidelineSource": (
            "NASS 2025 Antithrombotic Therapy in Spine Surgery Guidelines; ACCP "
            "2022 Antithrombotic Therapy (PMID 36893661)"
        ),
        "urgentFlags": urgent_flags,
        "warnings": [
            *warnings,
            "Spinal epidural hematoma: Rare but catastrophic complication. Monitor "
            "for new back pain, leg weakness, or bowel/bladder dysfunction "
            "postoperatively — requires urgent MRI and surgical decompression "
            "within 6–8 hours.",
        ],
        "nextSteps": _build_next_steps(data),
        "references": _references(),
    }
