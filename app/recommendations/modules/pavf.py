"""Percutaneous AV Fistula (pAVF) Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/pavfLogic.ts (assessPAVF).
Based on: SIR Practice Guidance Document on Percutaneous Arteriovenous Fistulae
for Dialysis Access — Dolmatch et al., JVIR 2025.
"""

from __future__ import annotations

from app.recommendations.jslib import coalesce, parse_float, truthy

LOGIC_KEY = "pavf"

BARBEAU_DESCRIPTIONS = {
    "A": "Type A — No damping of pulse tracing immediately after compression. Patent palmar arch.",
    "B": "Type B — Damping of pulse tracing. Adequate collateral flow.",
    "C": "Type C — Loss of pulse tracing followed by recovery within 120 seconds. Adequate collateral flow.",
    "D": "Type D — Loss of pulse tracing without recovery within 120 seconds. INADEQUATE palmar arch — pAVF/radial access contraindicated.",
}

ELIGIBILITY_COLORS = {
    "ELIGIBLE": "#16a34a",
    "ELIGIBLE_PREFERRED": "#15803d",
    "CONSIDER_SURGICAL_FIRST": "#ca8a04",
    "INELIGIBLE": "#dc2626",
    "NEEDS_FURTHER_WORKUP": "#ea580c",
}


def assess(data: dict) -> dict:
    contraindications: list[dict] = []
    warnings: list[str] = []
    recommendations: list[dict] = []
    vessel_mapping_issues: list[str] = []
    maturation_interventions: list[str] = []

    barbeau_test = data.get("barbeauTest")
    arterial_calcification = data.get("arterialCalcification")

    perforator_vein_patent = truthy(data.get("perforatorVeinPatent"))
    perforator_vein_diameter = parse_float(data.get("perforatorVeinDiameter"))
    superficial_vein_patent = truthy(data.get("superficialVeinPatent"))
    superficial_vein_depth = parse_float(data.get("superficialVeinDepth"))
    deep_vein_diameter = parse_float(data.get("deepVeinDiameter"))
    central_veins_patent = truthy(data.get("centralVeinsPatent"))
    arterial_doppler_normal = truthy(data.get("arterialDopplerNormal"))
    superficial_chest_collaterals = truthy(data.get("superficialChestCollaterals"))
    active_infection = truthy(data.get("activeInfection"))
    prior_central_venous_devices = truthy(data.get("priorCentralVenousDevices"))
    prior_av_access_surgeries = truthy(data.get("priorAVAccessSurgeries"))

    surgical_avf_feasible = truthy(data.get("surgicalAVFFeasible"))
    surgical_availability = truthy(data.get("surgicalAvailability"))
    patient_prefers_pavf = truthy(data.get("patientPrefersPAVF"))
    urgent_dialysis_needed = truthy(data.get("urgentDialysisNeeded"))

    # ── 1. Absolute Contraindications ──────────────────────────────────────────

    if barbeau_test == "D":
        contraindications.append({
            "id": "barbeau_d",
            "label": "Barbeau Test Type D — Inadequate palmar arch collateral circulation",
            "severity": "absolute",
            "guidance": (
                "Loss of pulse tracing without recovery within 120 seconds indicates inadequate ulnopalmar collateral flow. "
                "pAVF creation risks hand ischemia. Surgical AVF at wrist is also contraindicated. Consider upper arm access or AV graft. (GS-1)"
            ),
        })

    if active_infection:
        contraindications.append({
            "id": "active_infection",
            "label": "Active infection — Contraindication to brachial plexus block",
            "severity": "absolute",
            "guidance": (
                "Nerve blocks are contraindicated when the needle path passes through inflamed or infected tissue. "
                "Delay procedure until infection resolves. (GS-6)"
            ),
        })

    if superficial_chest_collaterals and not central_veins_patent:
        contraindications.append({
            "id": "central_vein_obstruction",
            "label": "Suspected thoracic central venous obstruction",
            "severity": "absolute",
            "guidance": (
                "Superficial chest collateral veins indicate chronic thoracic venous obstruction. Venography is required to "
                "determine the degree of obstruction before pAVF creation. Treat obstruction prior to proceeding. (GS-1)"
            ),
        })

    if arterial_calcification == "severe":
        contraindications.append({
            "id": "severe_calcification",
            "label": "Severe arterial calcification",
            "severity": "absolute",
            "guidance": (
                "Severe mural calcification prevents radiofrequency fistula creation with the WavelinQ device. "
                "Consider surgical AVF or AV graft. (GS-9)"
            ),
        })

    # ── 2. Vessel Mapping Assessment ───────────────────────────────────────────

    if not perforator_vein_patent:
        vessel_mapping_issues.append(
            "No patent perforator vein identified — pAVF creation not possible without a connecting perforator vein"
        )
        contraindications.append({
            "id": "no_perforator",
            "label": "No patent perforator vein",
            "severity": "absolute",
            "guidance": (
                "A patent perforator vein connecting the deep to superficial venous systems is essential for pAVF creation. "
                "Without it, pAVF cannot be performed. (GS-2)"
            ),
        })
    elif perforator_vein_diameter < 2:
        vessel_mapping_issues.append(
            f"Perforator vein diameter {_fmt(data.get('perforatorVeinDiameter'))} mm — below the recommended ≥2 mm threshold"
        )
        warnings.append(
            "Perforator vein <2 mm: pAVF creation is possible but not recommended as standard practice. Proceed with caution. (GS-2, refs 7,8)"
        )

    if not superficial_vein_patent:
        vessel_mapping_issues.append("No patent superficial outflow vein — cannulation not possible")
        contraindications.append({
            "id": "no_superficial_vein",
            "label": "No patent superficial outflow vein",
            "severity": "absolute",
            "guidance": (
                "Patent superficial upper arm outflow veins are required for 2-needle cannulation. "
                "Without them, hemodialysis cannot be performed via pAVF. (GS-2)"
            ),
        })
    elif superficial_vein_depth > 6:
        vessel_mapping_issues.append(
            f"Superficial vein depth {_fmt(data.get('superficialVeinDepth'))} mm — exceeds the ≤6 mm cannulation threshold"
        )
        warnings.append(
            "Superficial vein >6 mm from skin: Cannulation will be difficult. Surgical elevation or liposuction may be needed post-maturation. (GS-2, ref 7)"
        )

    if not arterial_doppler_normal:
        vessel_mapping_issues.append("Abnormal arterial Doppler waveforms or velocities")
        warnings.append("Abnormal arterial Doppler findings: Evaluate for inflow disease before proceeding. (GS-2)")

    if arterial_calcification == "moderate":
        vessel_mapping_issues.append("Moderate arterial calcification noted")
        warnings.append(
            "Moderate calcification may impede WavelinQ radiofrequency activation. Have PTA balloon available as rescue (balloon 1 mm larger than artery diameter). (GS-9)"
        )

    if not central_veins_patent and not superficial_chest_collaterals:
        warnings.append(
            "Central vein patency uncertain. If thoracic central vein obstruction is suspected, venography may be required. (GS-1)"
        )

    if prior_central_venous_devices:
        warnings.append(
            "Prior or current thoracic central venous devices (pacemakers/catheters) noted — assess for central venous obstruction before proceeding. (GS-1)"
        )

    if prior_av_access_surgeries:
        warnings.append(
            "Prior AV access surgeries: Review anatomy carefully. Prior surgical scarring may alter venous anatomy. (GS-1)"
        )

    # ── 3. Eligibility Determination ───────────────────────────────────────────

    has_absolute_contraindication = any(c["severity"] == "absolute" for c in contraindications)

    if has_absolute_contraindication:
        eligibility = "INELIGIBLE"
        eligibility_label = "Not a Candidate for pAVF"
        eligibility_color = "red"
    elif len(vessel_mapping_issues) > 0:
        eligibility = "NEEDS_FURTHER_WORKUP"
        eligibility_label = "Further Workup Required"
        eligibility_color = "orange"
    elif surgical_avf_feasible and surgical_availability and not patient_prefers_pavf and not urgent_dialysis_needed:
        eligibility = "CONSIDER_SURGICAL_FIRST"
        eligibility_label = "Consider Surgical AVF First"
        eligibility_color = "yellow"
    elif (
        not surgical_avf_feasible
        or not surgical_availability
        or patient_prefers_pavf
        or urgent_dialysis_needed
    ):
        eligibility = "ELIGIBLE_PREFERRED"
        eligibility_label = "pAVF Preferred — Proceed"
        eligibility_color = "green"
    else:
        eligibility = "ELIGIBLE"
        eligibility_label = "Eligible for pAVF"
        eligibility_color = "green"

    # ── 4. Device Suggestion ───────────────────────────────────────────────────

    device_suggestion = "WavelinQ"
    device_rationale = (
        "WavelinQ 4F dual-catheter system (BD) is the currently available device. Requires US + fluoroscopic guidance. "
        "Physician must complete 2-hour didactic webinar, 1-on-1 training, and 3 simulated proctored cases before first procedure. (GS-7, GS-9)"
    )

    if arterial_calcification == "severe":
        device_suggestion = "None"
        device_rationale = "Severe calcification prevents radiofrequency activation. Neither device is suitable."
    elif arterial_calcification == "moderate":
        device_rationale += (
            " Note: moderate calcification may impede activation — have rescue PTA balloon (1 mm > artery diameter) available."
        )

    # ── 5. CPT Code ────────────────────────────────────────────────────────────

    if eligibility == "INELIGIBLE":
        cpt_code = "N/A"
    elif device_suggestion == "WavelinQ":
        cpt_code = "36837"
    else:
        cpt_code = "36836"

    if cpt_code == "36837":
        cpt_description = (
            "CPT 36837 — Percutaneous AVF creation, upper extremity, separate access sites (artery + vein). "
            "Includes maturation procedures, imaging guidance, and radiologic supervision. RVU: 9.30"
        )
    elif cpt_code == "36836":
        cpt_description = (
            "CPT 36836 — Percutaneous AVF creation, upper extremity, single access. "
            "Includes maturation procedures, imaging guidance, and radiologic supervision. RVU: 7.20"
        )
    else:
        cpt_description = "No CPT code applicable — patient not a candidate."

    # ── 6. Recommendations ────────────────────────────────────────────────────

    if eligibility != "INELIGIBLE":
        recommendations.append({
            "category": "Pre-Procedure",
            "recommendation": (
                "Perform comprehensive vessel mapping with tourniquet on upper arm, patient relaxed and warm. Assess: "
                "arterial calcification, Doppler waveforms, Barbeau test, perforator vein (≥2 mm), superficial vein depth (≤6 mm), central vein patency."
            ),
            "guidanceStatementRef": "GS-1, GS-2, GS-3",
        })

        recommendations.append({
            "category": "Anesthesia",
            "recommendation": (
                "Brachial plexus block (supraclavicular or infraclavicular) under US guidance using 2% lidocaine (15–30 mL). "
                "Avoid bupivacaine (prolonged block). Give anticoagulation after block. Block takes effect in 10–15 minutes."
            ),
            "guidanceStatementRef": "GS-5, GS-6",
        })

        recommendations.append({
            "category": "Patient Counseling",
            "recommendation": (
                "Inform patient: technical success >95%, but ~80% achieve successful cannulation. Additional maturation procedures are common, "
                "especially in year 1. Dialysis center staff training is often required. Risks: bleeding, infection, nerve irritation, swelling, steal syndrome, surgical revision."
            ),
            "guidanceStatementRef": "GS-4",
        })

        recommendations.append({
            "category": "Procedure",
            "recommendation": (
                "WavelinQ: Apply tourniquet for venous dilation. Administer vasodilator cocktail (verapamil + heparin + nitroglycerin) via arterial sheath. "
                "Achieve parallel catheter alignment (magnets) just distal to perforator connection. Activate RF pulse (0.7 s; may increase to 1.0 s if needed). "
                "Confirm fistula with contrast injection. If blush seen, wait — fistula usually becomes apparent within minutes."
            ),
            "guidanceStatementRef": "GS-9",
        })

        if deep_vein_diameter > 0:
            recommendations.append({
                "category": "Intraoperative",
                "recommendation": (
                    "Assess for preferential deep brachial vein flow after creation. If deep vein diversion reduces superficial cannulation flow, "
                    "perform coil embolization of one brachial vein (4/5F catheter via US-guided retrograde brachial vein access or radial artery access). "
                    "Can be performed at time of creation or later visit."
                ),
                "guidanceStatementRef": "GS-9",
            })

        recommendations.append({
            "category": "Follow-Up",
            "recommendation": (
                "Schedule office visit + US study at 1–2 weeks post-procedure. Assess: brachial artery flow (mL/min), cannulation vein diameter, "
                "cannulation vein depth, perforator vein patency. Address maturation issues early. Goal: 2-needle cannulation allowing hemodialysis as prescribed."
            ),
            "guidanceStatementRef": "GS-11",
        })

        recommendations.append({
            "category": "Maturation Target (Rule of 6s)",
            "recommendation": (
                "Cannulation vein: diameter ≥6 mm, depth ≤6 mm from skin, flow ≥600 mL/min. For pAVFs specifically: fistula should be palpable with "
                "tourniquet downstream at time of cannulation attempt. pAVFs feel softer than surgical fistulae — train dialysis staff accordingly."
            ),
            "guidanceStatementRef": "GS-15, GS-16",
        })

        if urgent_dialysis_needed:
            recommendations.append({
                "category": "Urgency",
                "recommendation": (
                    "Urgent dialysis need: A well-functioning pAVF program can map and create the pAVF within 1 week. Successful cannulation of a mature "
                    "pAVF is expected approximately 4 weeks after creation. Coordinate with nephrology for bridging access if needed."
                ),
                "guidanceStatementRef": "GS-4",
            })

    if eligibility == "CONSIDER_SURGICAL_FIRST":
        recommendations.append({
            "category": "Surgical Referral",
            "recommendation": (
                "Surgical Brescia-Cimino AVF or snuff-box AVF at the wrist should be considered first when feasible and surgical expertise is available. "
                "pAVF is preferred when forearm veins are unsuitable for surgical AVF, surgical access is unavailable, or patient preference favors percutaneous approach."
            ),
            "guidanceStatementRef": "GS-1",
        })

    # ── 7. Maturation Assessment (Post-Procedure) ─────────────────────────────

    maturation_status = None
    maturation_label = None

    is_post_procedure = truthy(data.get("isPostProcedure"))
    weeks_post_procedure = data.get("weeksPostProcedure")

    if is_post_procedure and weeks_post_procedure is not None:
        weeks = parse_float(weeks_post_procedure)
        if weeks < 1:
            maturation_status = "EARLY_FOLLOW_UP_NEEDED"
            maturation_label = "Schedule 1–2 Week Follow-Up Visit + US Study"
        elif weeks < 4:
            maturation_status = "TOO_EARLY_TO_ASSESS"
            maturation_label = "Too Early for Cannulation Assessment — Continue Monitoring"
        else:
            rule_of_6_met = (
                parse_float(coalesce(_nullify(data.get("cannulationVeinDiameterMm")), 0)) >= 6
                and parse_float(coalesce(_nullify(data.get("cannulationVeinDepthMm")), 99)) <= 6
                and truthy(coalesce(_nullify(data.get("fistulaPalpableWithTourniquet")), False))
            )

            if rule_of_6_met:
                maturation_status = "MATURE_READY_FOR_CANNULATION"
                maturation_label = "Mature — Ready for Cannulation"
            elif truthy(data.get("deepVeinDiversionPresent")):
                maturation_status = "IMMATURE_DEEP_VEIN_DIVERSION"
                maturation_label = "Immature — Deep Vein Diversion"
                maturation_interventions.append(
                    "Coil embolization of one brachial vein (4/5F catheter via US-guided retrograde brachial vein or radial artery access). "
                    "Avoid excessive embolization to prevent venous hypertension. (GS-13)"
                )
            elif truthy(data.get("superficialVeinDiversionPresent")):
                maturation_status = "IMMATURE_SUPERFICIAL_DIVERSION"
                maturation_label = "Immature — Superficial Vein Diversion"
                maturation_interventions.append(
                    "Banding or ligation of median basilic or median cubital vein to redirect flow to cephalic cannulation vein. "
                    "Avoid banding basilic vein 2–3 cm from antecubital fossa (risk of medial antebrachial cutaneous nerve injury). (GS-13)"
                )
            elif truthy(data.get("cannulationVeinTooDeep")):
                maturation_status = "IMMATURE_VEIN_TOO_DEEP"
                maturation_label = "Immature — Cannulation Vein Too Deep"
                maturation_interventions.append(
                    "Surgical vein elevation (especially basilic vein) or liposuction to reduce subcutaneous adipose tissue between cannulation vein and skin. (GS-13)"
                )
            else:
                maturation_status = "IMMATURE_INFLOW_STENOSIS"
                maturation_label = "Immature — Evaluate for Inflow/Perforator Stenosis"
                maturation_interventions.append(
                    "Balloon angioplasty of anastomosis and/or perforator vein stenosis. Consider peripheral cutting balloon for resistant stenoses. "
                    "Use arterial access for diagnosis and intervention. (GS-13, GS-14)"
                )

    # ── 8. Follow-Up Schedule ─────────────────────────────────────────────────

    follow_up_schedule = [
        "1–2 weeks post-procedure: Office visit + US study. Assess brachial artery flow, cannulation vein diameter/depth, perforator vein patency. Address early maturation issues.",
        "4 weeks post-procedure: Assess cannulation readiness (Rule of 6s: vein ≥6 mm diameter, ≤6 mm depth, palpable with tourniquet).",
        "Ongoing: Dialysis center staff training on pAVF cannulation technique. IR physician is primary contact for cannulation troubleshooting.",
        "If cannulation fails: IR physician should visit dialysis unit to assess and assist with successful cannulation.",
        "Subsequent interventions: Use CPT codes 36901–36909 for pAVF maintenance procedures after initial creation date.",
    ]

    # ── 9. Vessel Mapping Summary ─────────────────────────────────────────────

    vessel_mapping_adequate = (
        perforator_vein_patent
        and perforator_vein_diameter >= 2
        and superficial_vein_patent
        and superficial_vein_depth <= 6
        and central_veins_patent
        and arterial_doppler_normal
        and arterial_calcification != "severe"
    )

    # ── 10. Clinical Summary ──────────────────────────────────────────────────

    if eligibility == "INELIGIBLE":
        labels = "; ".join(c["label"] for c in contraindications)
        tail = "Consider upper arm AV graft." if barbeau_test == "D" else "Alternative access strategy required."
        clinical_summary = f"Patient is NOT a candidate for pAVF creation due to: {labels}. {tail}"
    elif eligibility == "NEEDS_FURTHER_WORKUP":
        clinical_summary = (
            f"Patient requires further workup before pAVF candidacy can be confirmed: {'; '.join(vessel_mapping_issues)}. "
            "Repeat vessel mapping after addressing these issues."
        )
    elif eligibility == "CONSIDER_SURGICAL_FIRST":
        clinical_summary = (
            "Patient has suitable anatomy for pAVF but surgical AVF (Brescia-Cimino or snuff-box) should be considered first given "
            "surgical feasibility and availability. If surgical AVF fails or is declined, pAVF is an appropriate next step."
        )
    elif eligibility == "ELIGIBLE_PREFERRED":
        reasons: list[str] = []
        if not surgical_avf_feasible:
            reasons.append("forearm veins unsuitable for surgical AVF")
        if not surgical_availability:
            reasons.append("no local surgical expertise")
        if patient_prefers_pavf:
            reasons.append("patient preference")
        if urgent_dialysis_needed:
            reasons.append("urgent dialysis need (pAVF achievable within 1 week)")
        clinical_summary = (
            f"Patient is a preferred candidate for pAVF ({', '.join(reasons)}). Vessel mapping is adequate. "
            f"Proceed with {device_suggestion} system. Technical success expected >95%; cannulation success ~80%. Maturation procedures may be required."
        )
    else:
        clinical_summary = (
            "Patient is eligible for pAVF creation. Vessel mapping is adequate. Proceed with WavelinQ system. "
            "Technical success expected >95%; cannulation success ~80%. Maturation procedures may be required in year 1."
        )

    return {
        "eligibility": eligibility,
        "eligibilityLabel": eligibility_label,
        "eligibilityColor": eligibility_color,
        "contraindications": contraindications,
        "warnings": warnings,
        "recommendations": recommendations,
        "vesselMappingAdequate": vessel_mapping_adequate,
        "vesselMappingIssues": vessel_mapping_issues,
        "deviceSuggestion": device_suggestion,
        "deviceRationale": device_rationale,
        "maturationStatus": maturation_status,
        "maturationLabel": maturation_label,
        "maturationInterventions": maturation_interventions if len(maturation_interventions) > 0 else None,
        "cptCode": cpt_code,
        "cptDescription": cpt_description,
        "followUpSchedule": follow_up_schedule,
        "clinicalSummary": clinical_summary,
    }


def _nullify(x):
    """Treat empty-string submissions as missing (None) so JS ``??`` semantics
    on optional numeric/boolean post-procedure fields match. A real 0/False is
    preserved; only None/"" become None."""
    if x is None or x == "":
        return None
    return x


def _fmt(x):
    """Render a numeric value the way JS string interpolation would (e.g. 1.5
    not 1.50, 3 not 3.0)."""
    if isinstance(x, bool) or x is None:
        return str(x)
    if isinstance(x, str):
        return x
    f = float(x)
    if f.is_integer():
        return str(int(f))
    return repr(f)
