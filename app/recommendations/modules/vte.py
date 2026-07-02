"""Venous Thromboembolism (VTE) Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/vteLogic.ts.

The legacy library exports five separate entry functions (one per ASH
guideline pathway). The FastAPI engine exposes a single ``assess(data)``;
dispatch is driven by the ``pathway`` input field, whose values mirror the
TS ``VTEPathway`` union:

    dvt_pe_treatment | cancer_associated_thrombosis | thrombophilia_testing
    | pediatric_vte | pregnancy_vte

Each pathway helper consumes the field names of its corresponding TS input
interface (DVTPEInput, CATInput, ThrombophiliaInput, PediatricVTEInput,
PregnancyVTEInput). Output shape matches VTEResult exactly:
``pathway, primaryRecommendation, additionalRecommendations, clinicalAlerts,
summary``.
"""

from __future__ import annotations

from app.recommendations.jslib import coalesce, num, truthy

LOGIC_KEY = "vte"


# ─── Pathway 1: DVT/PE Treatment (Non-Cancer Adults) ─────────────────────────


def _assess_dvt_pe(input: dict) -> dict:
    recommendations: list[dict] = []
    alerts: list[str] = []

    vte_type = input.get("vteType")
    pe_status = input.get("peHemodynamicStatus")
    provoked = input.get("provoked")
    prior = input.get("priorVTEHistory")
    renal = input.get("renalFunction")
    liver = input.get("liverDisease")

    # Redirect cancer patients
    if truthy(input.get("cancerPresent")):
        alerts.append(
            "Cancer-associated thrombosis detected — please use the Cancer-Associated Thrombosis pathway for treatment recommendations."
        )

    # APS alert
    if truthy(input.get("antiphospholipidSyndrome")):
        alerts.append(
            "Antiphospholipid syndrome: DOACs are generally NOT recommended. LMWH or VKA (INR 2-3) preferred. Consult hematology."
        )

    # Renal function alert
    if renal == "severe_impairment":
        alerts.append(
            "Severe renal impairment (CrCl <30 mL/min): Most DOACs are contraindicated or require dose adjustment. LMWH or UFH preferred."
        )

    # Liver disease alert
    if liver == "moderate_severe":
        alerts.append(
            "Moderate-to-severe liver disease: DOACs are generally contraindicated. Consult hepatology/hematology."
        )

    # ── Setting of Care ──
    if vte_type == "dvt_proximal" or vte_type == "dvt_distal":
        setting_rec = {
            "id": "dvt_pe_rec1",
            "statement": "For uncomplicated DVT, home treatment is suggested over hospital treatment.",
            "strength": "conditional",
            "certainty": "low",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 1",
            "pmid": "33007077",
            "remarks": "Does not apply to patients with limb-threatening DVT, limited home support, inability to afford medications, or poor compliance history.",
        }
    elif vte_type == "pe" or vte_type == "dvt_and_pe":
        if pe_status == "massive":
            setting_rec = {
                "id": "dvt_pe_rec6",
                "statement": "For PE with hemodynamic compromise, thrombolytic therapy followed by anticoagulation is RECOMMENDED over anticoagulation alone.",
                "strength": "strong",
                "certainty": "low",
                "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 6",
                "pmid": "33007077",
                "remarks": "Strong recommendation despite low certainty evidence, given the high mortality of hemodynamically unstable PE and potential lifesaving effect of thrombolytics.",
                "alert": "EMERGENT: Systemic thrombolysis (alteplase 100 mg IV over 2h) or catheter-directed therapy for hemodynamically unstable PE.",
            }
        elif pe_status == "submassive":
            setting_rec = {
                "id": "dvt_pe_rec7",
                "statement": "For submassive PE (RV dysfunction, no hemodynamic compromise), anticoagulation alone is suggested over routine thrombolysis.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 7",
                "pmid": "33007077",
                "remarks": "Thrombolysis is reasonable for submassive PE with low bleeding risk in selected younger patients or those at high risk for decompensation. Monitor closely for hemodynamic deterioration.",
            }
        else:
            setting_rec = {
                "id": "dvt_pe_rec2",
                "statement": "For PE at low risk for complications, home treatment is suggested over hospital treatment.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 2",
                "pmid": "33007077",
                "remarks": "Use validated risk stratification tools (PESI or simplified PESI). Does not apply to submassive/massive PE, high bleeding risk, or patients requiring IV analgesics.",
            }
    else:
        setting_rec = {
            "id": "dvt_pe_rec1",
            "statement": "Home treatment is suggested for uncomplicated VTE at low risk for complications.",
            "strength": "conditional",
            "certainty": "low",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendations 1-2",
            "pmid": "33007077",
        }

    # ── Anticoagulant Choice ──
    if (
        truthy(input.get("antiphospholipidSyndrome"))
        or renal == "severe_impairment"
        or liver == "moderate_severe"
    ):
        ac_rec = {
            "id": "dvt_pe_rec3_exception",
            "statement": "DOACs are NOT preferred in this patient due to APS, severe renal impairment, or moderate-severe liver disease. Use LMWH or VKA (INR 2.0–3.0) as appropriate.",
            "strength": "conditional",
            "certainty": "moderate",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 3 (exceptions)",
            "pmid": "33007077",
            "alert": "Consult hematology for anticoagulant selection in this high-complexity patient.",
        }
    else:
        ac_rec = {
            "id": "dvt_pe_rec3",
            "statement": "DOACs are suggested over vitamin K antagonists (VKAs) for treatment of DVT and/or PE.",
            "strength": "conditional",
            "certainty": "moderate",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 3",
            "pmid": "33007077",
            "remarks": "No preference among individual DOACs (Rec 4). Factors influencing DOAC choice: lead-in parenteral requirement (edoxaban, dabigatran), dosing frequency, out-of-pocket cost, renal function, CYP3A4/P-gp interactions.",
        }

    # ── Distal DVT Special Handling ──
    if vte_type == "dvt_distal":
        if input.get("distalDVTSymptoms") == "symptomatic":
            recommendations.append(
                {
                    "id": "dvt_pe_rec9",
                    "statement": "For symptomatic isolated distal DVT, anticoagulation is suggested over no anticoagulation.",
                    "strength": "conditional",
                    "certainty": "very_low",
                    "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 9",
                    "pmid": "33007077",
                }
            )
        else:
            recommendations.append(
                {
                    "id": "dvt_pe_rec10",
                    "statement": "For asymptomatic (incidentally detected) isolated distal DVT, no anticoagulation is suggested over anticoagulation.",
                    "strength": "conditional",
                    "certainty": "very_low",
                    "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 10",
                    "pmid": "33007077",
                    "remarks": "Serial imaging to monitor for proximal extension may be considered.",
                }
            )

    # ── Duration of Treatment ──
    if provoked == "provoked_transient" and prior == "none":
        duration_rec = {
            "id": "dvt_pe_rec12",
            "statement": "For DVT/PE provoked by a transient risk factor with no prior VTE history, 3 months of anticoagulation is suggested.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 12",
            "pmid": "33007077",
            "remarks": "After 3 months, anticoagulation may be stopped if the transient risk factor has resolved.",
        }
    elif provoked == "provoked_transient" and prior == "prior_transient_provoked":
        duration_rec = {
            "id": "dvt_pe_rec24b",
            "statement": "For VTE provoked by a transient risk factor with a history of prior VTE also provoked by a transient risk factor, stopping anticoagulation after completion of primary treatment (3 months) is suggested over indefinite therapy.",
            "strength": "conditional",
            "certainty": "moderate",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 24b",
            "pmid": "33007077",
        }
    elif provoked == "provoked_transient" and (
        prior == "prior_unprovoked" or prior == "prior_chronic_provoked"
    ):
        duration_rec = {
            "id": "dvt_pe_rec24a",
            "statement": "For VTE provoked by a transient risk factor with a history of prior unprovoked VTE or VTE provoked by a chronic risk factor, indefinite antithrombotic therapy is suggested over stopping after primary treatment.",
            "strength": "conditional",
            "certainty": "moderate",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 24a",
            "pmid": "33007077",
        }
    elif provoked == "provoked_chronic":
        duration_rec = {
            "id": "dvt_pe_rec13",
            "statement": "For DVT/PE provoked by a chronic risk factor, at least 3 months of anticoagulation is suggested, with reassessment for indefinite therapy.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 13",
            "pmid": "33007077",
            "remarks": "Reassess the ongoing risk factor at 3 months to determine whether indefinite anticoagulation is warranted.",
        }
    elif provoked == "unprovoked" and prior == "none":
        if truthy(input.get("highBleedingRisk")):
            duration_rec = {
                "id": "dvt_pe_rec19_bleed",
                "statement": "For first unprovoked DVT/PE with high bleeding risk, stopping anticoagulation after 3–6 months of primary treatment may be appropriate. Indefinite therapy is generally preferred but must be weighed against bleeding risk.",
                "strength": "conditional",
                "certainty": "moderate",
                "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 19 (modified for high bleed risk)",
                "pmid": "33007077",
                "alert": "High bleeding risk identified. Individualize duration decision. Consider hematology consultation.",
            }
        else:
            duration_rec = {
                "id": "dvt_pe_rec19",
                "statement": "For first unprovoked DVT/PE without high bleeding risk, indefinite antithrombotic therapy is suggested over stopping anticoagulation after primary treatment.",
                "strength": "conditional",
                "certainty": "moderate",
                "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 19",
                "pmid": "33007077",
                "remarks": "Reassess at least annually for changes in bleeding risk, patient preferences, and continued indication.",
            }
    else:
        # Recurrent unprovoked
        duration_rec = {
            "id": "dvt_pe_rec25",
            "statement": "For recurrent unprovoked DVT/PE, indefinite antithrombotic therapy is RECOMMENDED over stopping anticoagulation after primary treatment.",
            "strength": "strong",
            "certainty": "moderate",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 25",
            "pmid": "33007077",
        }

    # ── Secondary Prevention Agent ──
    sec_prev_rec = {
        "id": "dvt_pe_rec20_22",
        "statement": "For secondary prevention, anticoagulation is preferred over aspirin. If using a DOAC, either standard dose or lower dose (rivaroxaban 10 mg/day or apixaban 2.5 mg BID) may be used after completing primary treatment.",
        "strength": "conditional",
        "certainty": "moderate",
        "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendations 20, 22",
        "pmid": "33007077",
        "remarks": "If VKA is used for secondary prevention, target INR 2.0–3.0 (strong recommendation). Suspend aspirin for the duration of anticoagulation in patients with stable CVD (Rec 26).",
    }

    # ── Breakthrough VTE on VKA ──
    if truthy(input.get("currentlyOnVKA")):
        alerts.append(
            "Breakthrough VTE on therapeutic VKA: LMWH is suggested over DOAC for management. Evaluate for underlying causes and contraindications."
        )
        recommendations.append(
            {
                "id": "dvt_pe_rec23",
                "statement": "For breakthrough DVT/PE during therapeutic VKA treatment, LMWH is suggested over DOAC therapy.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendation 23",
                "pmid": "33007077",
                "remarks": "Evaluate for poor INR control (in which case a DOAC may be reasonable), APS, and other underlying causes.",
            }
        )

    # Compression stockings
    recommendations.append(
        {
            "id": "dvt_pe_rec27_28",
            "statement": "Routine use of compression stockings for prevention of post-thrombotic syndrome (PTS) is NOT suggested for most DVT patients.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2020 DVT/PE Treatment Guidelines — Recommendations 27-28",
            "pmid": "33007077",
            "remarks": "Stockings may help reduce edema and pain in selected patients with acute DVT.",
        }
    )

    doac_contra = (
        truthy(input.get("antiphospholipidSyndrome"))
        or renal == "severe_impairment"
        or liver == "moderate_severe"
    )
    summary = (
        f"DVT/PE treatment pathway: {str(provoked).replace('_', ' ')} VTE. "
        + (
            "DOAC contraindicated — use LMWH or VKA."
            if doac_contra
            else "DOACs preferred over VKA."
        )
        + f" Duration: {duration_rec['statement'].split('.')[0]}."
    )

    return {
        "pathway": "dvt_pe_treatment",
        "primaryRecommendation": setting_rec,
        "additionalRecommendations": [ac_rec, duration_rec, sec_prev_rec, *recommendations],
        "clinicalAlerts": alerts,
        "summary": summary,
    }


# ─── Pathway 2: Cancer-Associated Thrombosis ──────────────────────────────────


def _assess_cat(input: dict) -> dict:
    recommendations: list[dict] = []
    alerts: list[str] = []

    context = input.get("clinicalContext")
    cancer_type = input.get("cancerType")
    vte_type = input.get("vteType")
    phase = input.get("treatmentPhase")
    surgical = input.get("surgicalProcedure")

    # GI/GU cancer DOAC bleeding alert
    if cancer_type == "gi_cancer" or cancer_type == "gu_cancer":
        alerts.append(
            "GI/GU cancer: Higher risk of major bleeding with DOACs (especially edoxaban and rivaroxaban). Apixaban may have a more favorable bleeding profile. Individualize DOAC vs LMWH decision."
        )

    primary_rec: dict | None = None

    if context == "hospitalized_medical":
        primary_rec = {
            "id": "cat_rec1",
            "statement": "For hospitalized medical patients with cancer, pharmacological thromboprophylaxis (LMWH preferred over UFH) is suggested over no thromboprophylaxis.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendations 1-2",
            "pmid": "33570602",
            "remarks": "Discontinue thromboprophylaxis at hospital discharge (Rec 5). Pharmacological preferred over mechanical thromboprophylaxis (Rec 2).",
        }
    elif context == "ambulatory_systemic_therapy":
        khorana = num(input.get("khoranaScore"), 0)
        if khorana >= 2:
            primary_rec = {
                "id": "cat_rec6",
                "statement": "Khorana score ≥2 (high risk): Pharmacological thromboprophylaxis with LMWH or DOAC is suggested for ambulatory patients with cancer receiving systemic therapy.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 6",
                "pmid": "33570602",
                "remarks": "Khorana score ≥2 identifies high-risk ambulatory cancer patients who benefit from primary prophylaxis.",
            }
        else:
            primary_rec = {
                "id": "cat_rec7",
                "statement": "Khorana score <2 (low risk): No pharmacological thromboprophylaxis is suggested for ambulatory patients with cancer receiving systemic therapy.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 7",
                "pmid": "33570602",
            }
    elif context == "surgical":
        if surgical == "high_bleed_risk":
            primary_rec = {
                "id": "cat_rec14",
                "statement": "For cancer surgical patients at high bleeding risk, mechanical thromboprophylaxis is suggested over pharmacological thromboprophylaxis.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 14",
                "pmid": "33570602",
            }
        elif surgical == "major_abdominal_pelvic":
            primary_rec = {
                "id": "cat_rec16",
                "statement": "For cancer patients undergoing major abdominal/pelvic surgery, extended thromboprophylaxis for 4 weeks post-surgery is suggested.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 16",
                "pmid": "33570602",
                "remarks": "Use LMWH or fondaparinux (not UFH) for surgical prophylaxis (Rec 17).",
            }
        else:
            primary_rec = {
                "id": "cat_rec13",
                "statement": "For cancer surgical patients at low bleeding risk, pharmacological thromboprophylaxis is suggested over mechanical thromboprophylaxis.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 13",
                "pmid": "33570602",
                "remarks": "Use LMWH or fondaparinux (not UFH) for surgical prophylaxis (Rec 17).",
            }
    elif context == "cvc_related":
        primary_rec = {
            "id": "cat_rec18_19",
            "statement": "For patients with cancer and a central venous catheter (CVC), neither parenteral nor oral thromboprophylaxis is suggested.",
            "strength": "conditional",
            "certainty": "low",
            "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendations 18-19",
            "pmid": "33570602",
        }
        if vte_type == "cvc_related_vte":
            recommendations.append(
                {
                    "id": "cat_rec29",
                    "statement": "For cancer patients with CVC-related VTE receiving anticoagulant treatment, keeping the CVC is suggested over removing it.",
                    "strength": "conditional",
                    "certainty": "very_low",
                    "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 29",
                    "pmid": "33570602",
                }
            )
    else:
        # Treatment of VTE
        if phase == "initial_first_week":
            primary_rec = {
                "id": "cat_rec20_21",
                "statement": "For initial treatment of cancer-associated VTE (first week): DOAC (apixaban or rivaroxaban) OR LMWH is suggested. LMWH is RECOMMENDED over UFH.",
                "strength": "strong",
                "certainty": "moderate",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendations 20-21",
                "pmid": "33570602",
                "remarks": "LMWH is strongly recommended over UFH (Rec 21, moderate certainty). DOAC vs LMWH is a conditional recommendation (Rec 20, very low certainty).",
            }
        elif phase == "short_term_3_6mo":
            primary_rec = {
                "id": "cat_rec23_24",
                "statement": "For short-term treatment of cancer-associated VTE (3–6 months): DOAC (apixaban, edoxaban, or rivaroxaban) is suggested over LMWH and over VKA.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendations 23-24",
                "pmid": "33570602",
                "remarks": "LMWH is suggested over VKA (Rec 25, moderate certainty). For GI/GU cancers, use caution with DOACs due to higher bleeding risk — apixaban may be preferred.",
            }
            if vte_type == "incidental_pe":
                recommendations.append(
                    {
                        "id": "cat_rec26",
                        "statement": "For incidental (unsuspected) PE in cancer patients, short-term anticoagulation treatment is suggested over observation.",
                        "strength": "conditional",
                        "certainty": "very_low",
                        "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 26",
                        "pmid": "33570602",
                    }
                )
            if vte_type == "subsegmental_pe":
                recommendations.append(
                    {
                        "id": "cat_rec27",
                        "statement": "For subsegmental PE (SSPE) in cancer patients, short-term anticoagulation treatment is suggested over observation.",
                        "strength": "conditional",
                        "certainty": "very_low",
                        "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 27",
                        "pmid": "33570602",
                    }
                )
            if vte_type == "visceral_splanchnic":
                recommendations.append(
                    {
                        "id": "cat_rec28",
                        "statement": "For visceral/splanchnic vein thrombosis in cancer patients, short-term anticoagulation OR observation may be considered.",
                        "strength": "conditional",
                        "certainty": "very_low",
                        "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 28",
                        "pmid": "33570602",
                    }
                )
        else:
            # Long-term >6 months
            primary_rec = {
                "id": "cat_rec32_33_34",
                "statement": "For active cancer with VTE: long-term anticoagulation (>6 months) is suggested over short-term alone. Indefinite anticoagulation is suggested over stopping after a fixed period. DOACs or LMWH are preferred for long-term treatment.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendations 32-34",
                "pmid": "33570602",
                "remarks": "Reassess periodically for cancer status, bleeding risk, and patient preferences.",
            }

    # Recurrent VTE management
    if truthy(input.get("recurrentVTEOnLMWH")):
        recommendations.append(
            {
                "id": "cat_rec30",
                "statement": "For recurrent VTE despite therapeutic LMWH: increase LMWH to supratherapeutic level OR continue at therapeutic dose.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 30",
                "pmid": "33570602",
            }
        )
    if truthy(input.get("recurrentVTEOnAnticoagulation")):
        recommendations.append(
            {
                "id": "cat_rec31",
                "statement": "For recurrent VTE despite anticoagulation: IVC filter is NOT suggested.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2021 Cancer-Associated Thrombosis — Recommendation 31",
                "pmid": "33570602",
            }
        )

    summary = f"Cancer-associated thrombosis — {str(context).replace('_', ' ')} context. " + (
        "GI/GU cancer: DOAC bleeding risk elevated."
        if (cancer_type == "gi_cancer" or cancer_type == "gu_cancer")
        else ""
    )

    return {
        "pathway": "cancer_associated_thrombosis",
        "primaryRecommendation": primary_rec,
        "additionalRecommendations": recommendations,
        "clinicalAlerts": alerts,
        "summary": summary,
    }


# ─── Pathway 3: Thrombophilia Testing ────────────────────────────────────────


def _assess_thrombophilia(input: dict) -> dict:
    alerts: list[str] = []
    additional_recs: list[dict] = []

    vte_type = input.get("vteType")
    standard_of_care = input.get("standardOfCareAnticoagulation")

    if vte_type == "unprovoked":
        primary_rec = {
            "id": "thrombo_r1",
            "statement": "For unprovoked VTE, thrombophilia testing is NOT suggested. Indefinite anticoagulation is recommended regardless of thrombophilia status.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2023 Thrombophilia Testing — Recommendation 1",
            "pmid": "37195076",
            "remarks": "Testing would not change management (indefinite anticoagulation is already indicated).",
        }
    elif vte_type == "provoked_surgical":
        primary_rec = {
            "id": "thrombo_r2",
            "statement": "For VTE provoked by surgery, thrombophilia testing is NOT suggested.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2023 Thrombophilia Testing — Recommendation 2",
            "pmid": "37195076",
            "remarks": "Surgical provocation is a sufficient explanation; testing would not change the recommendation to stop anticoagulation after 3 months.",
        }
    elif vte_type == "provoked_nonsurgical_major_transient":
        primary_rec = {
            "id": "thrombo_r3",
            "statement": "For VTE provoked by a nonsurgical major transient risk factor, thrombophilia testing IS suggested. If positive, indefinite anticoagulation is recommended.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2023 Thrombophilia Testing — Recommendation 3",
            "pmid": "37195076",
            "remarks": "Testing may change management: a positive result for high-risk thrombophilia (antithrombin, protein C, or protein S deficiency; APS; homozygous FVL or PGM) would support indefinite anticoagulation.",
        }
    elif vte_type == "provoked_pregnancy_postpartum":
        primary_rec = {
            "id": "thrombo_r4",
            "statement": "For VTE provoked by pregnancy or postpartum, thrombophilia testing IS suggested. If positive, indefinite anticoagulation is recommended.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2023 Thrombophilia Testing — Recommendation 4",
            "pmid": "37195076",
        }
    elif vte_type == "provoked_coc":
        primary_rec = {
            "id": "thrombo_r5",
            "statement": "For VTE associated with combined oral contraceptive (COC) use, thrombophilia testing IS suggested. If positive, indefinite anticoagulation is recommended.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2023 Thrombophilia Testing — Recommendation 5",
            "pmid": "37195076",
            "remarks": "Positive thrombophilia result also informs future contraceptive choices.",
        }
    elif vte_type == "unusual_site_cvt":
        if standard_of_care == "would_stop":
            primary_rec = {
                "id": "thrombo_r7",
                "statement": "For cerebral venous thrombosis (CVT) in settings where anticoagulation would otherwise be discontinued: thrombophilia testing IS suggested. If positive, indefinite anticoagulation is recommended.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2023 Thrombophilia Testing — Recommendation 7",
                "pmid": "37195076",
            }
        else:
            primary_rec = {
                "id": "thrombo_r8",
                "statement": "For CVT in settings where anticoagulation would otherwise be continued indefinitely: thrombophilia testing is NOT suggested.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2023 Thrombophilia Testing — Recommendation 8",
                "pmid": "37195076",
            }
    elif vte_type == "unusual_site_splanchnic":
        if standard_of_care == "would_stop":
            primary_rec = {
                "id": "thrombo_r9",
                "statement": "For splanchnic venous thrombosis in settings where anticoagulation would otherwise be discontinued: thrombophilia testing IS suggested. If positive, indefinite anticoagulation is recommended.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2023 Thrombophilia Testing — Recommendation 9",
                "pmid": "37195076",
            }
        else:
            primary_rec = {
                "id": "thrombo_r10",
                "statement": "For splanchnic venous thrombosis in settings where anticoagulation would otherwise be continued indefinitely: thrombophilia testing is NOT suggested.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2023 Thrombophilia Testing — Recommendation 10",
                "pmid": "37195076",
            }
    elif vte_type == "asymptomatic_family_history":
        if truthy(input.get("familyHistoryHighRiskThrombophilia")):
            primary_rec = {
                "id": "thrombo_r11",
                "statement": "For asymptomatic individuals with a family history of high-risk thrombophilia (antithrombin, protein C, or protein S deficiency): selective thrombophilia testing is conditionally suggested to guide prophylaxis decisions during minor provoking risk factors and to avoid COCs/HRT.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2023 Thrombophilia Testing — Recommendations 11-14",
                "pmid": "37195076",
            }
        else:
            primary_rec = {
                "id": "thrombo_r_no_test",
                "statement": "For asymptomatic individuals without a family history of high-risk thrombophilia, thrombophilia testing is NOT suggested.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2023 Thrombophilia Testing — General principle",
                "pmid": "37195076",
                "remarks": "Strong recommendation against testing the general population before starting combined oral contraceptives.",
            }
    else:
        primary_rec = {
            "id": "thrombo_default",
            "statement": "Thrombophilia testing is generally not suggested unless it would change clinical management.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2023 Thrombophilia Testing",
            "pmid": "37195076",
        }

    additional_recs.append(
        {
            "id": "thrombo_panel_note",
            "statement": "When testing is indicated, a full thrombophilia panel is recommended: factor V Leiden (FVL), prothrombin G20210A mutation (PGM), antithrombin deficiency, protein C deficiency, protein S deficiency, and antiphospholipid antibodies (APLA) compatible with APS.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH 2023 Thrombophilia Testing — Methods",
            "pmid": "37195076",
            "remarks": "Timing: Avoid testing during acute thrombosis or while on anticoagulation (may affect protein C, S, antithrombin levels). Optimal timing is 4–6 weeks after completing anticoagulation.",
        }
    )

    return {
        "pathway": "thrombophilia_testing",
        "primaryRecommendation": primary_rec,
        "additionalRecommendations": additional_recs,
        "clinicalAlerts": alerts,
        "summary": f"Thrombophilia testing pathway: {str(vte_type).replace('_', ' ')}. {primary_rec['statement'].split('.')[0]}.",
    }


# ─── Pathway 4: Pediatric VTE (ASH/ISTH 2025) ────────────────────────────────


def _assess_pediatric_vte(input: dict) -> dict:
    recommendations: list[dict] = []
    alerts: list[str] = []

    age_group = input.get("ageGroup")
    vte_type = input.get("vteType")

    # 2025 DOAC update
    doac_rec = {
        "id": "ped_rec17_20",
        "statement": "For pediatric patients with VTE, DOACs (rivaroxaban or dabigatran) are suggested over standard-of-care anticoagulants (LMWH, UFH, VKA, fondaparinux). Either rivaroxaban or dabigatran may be used; individual populations or jurisdictional availability may guide choice.",
        "strength": "conditional",
        "certainty": "low",
        "source": "ASH/ISTH 2025 Pediatric VTE — Recommendations 17-20",
        "pmid": "40423983",
        "remarks": "New 2025 recommendation. Rivaroxaban and dabigatran are the only DOACs with pediatric-specific dosing data. Consult pediatric hematology for dosing guidance.",
    }

    if vte_type == "symptomatic_dvt_or_pe":
        primary_rec = {
            "id": "ped_rec1",
            "statement": "For symptomatic DVT or PE in pediatric patients, anticoagulation is suggested over no anticoagulation.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 1",
            "pmid": "40423983",
            "remarks": "Strength downgraded from strong (2018) to conditional (2025) based on updated evidence review.",
        }
        recommendations.append(doac_rec)
        if truthy(input.get("hemodynamicCompromise")):
            recommendations.append(
                {
                    "id": "ped_rec15",
                    "statement": "For PE with hemodynamic compromise in pediatric patients, thrombolysis followed by anticoagulation is suggested over anticoagulation alone.",
                    "strength": "conditional",
                    "certainty": "very_low",
                    "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 15",
                    "pmid": "40423983",
                }
            )
        else:
            recommendations.append(
                {
                    "id": "ped_rec14",
                    "statement": "For PE with evidence of right ventricular dysfunction but no hemodynamic compromise, anticoagulation alone is suggested over thrombolysis followed by anticoagulation.",
                    "strength": "conditional",
                    "certainty": "very_low",
                    "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 14",
                    "pmid": "40423983",
                }
            )

    elif vte_type == "clinically_unsuspected":
        primary_rec = {
            "id": "ped_rec2",
            "statement": "For clinically unsuspected (incidentally detected) DVT or PE in pediatric patients, either anticoagulation or no anticoagulation may be considered.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 2",
            "pmid": "40423983",
            "remarks": "Individualize based on clot burden, location, risk factors, and bleeding risk.",
        }

    elif vte_type == "provoked_vte":
        if truthy(input.get("provokedExclusions")):
            primary_rec = {
                "id": "ped_rec3_excluded",
                "statement": "This patient has exclusion criteria for the 6-week recommendation (recurrent VTE, persistent occlusive thrombus, cancer-associated, persistent APLA, major thrombophilia, or ongoing VTE risk factors). Anticoagulation for 3 months or longer is suggested.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 3 (exclusions)",
                "pmid": "40423983",
            }
        else:
            primary_rec = {
                "id": "ped_rec3",
                "statement": "For select pediatric patients with provoked VTE (without exclusion criteria), anticoagulation for 6 weeks is suggested over 3 months.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 3",
                "pmid": "40423983",
                "remarks": "Exclusions: recurrent VTE, persistent occlusive thrombus at 6 weeks, cancer-associated thrombosis, persistent antiphospholipid antibodies, major thrombophilia, or ongoing VTE risk factors.",
            }
        recommendations.append(doac_rec)

    elif vte_type == "unprovoked_vte":
        primary_rec = {
            "id": "ped_rec4",
            "statement": "For unprovoked DVT or PE in pediatric patients, anticoagulation for 6 to 12 months is suggested over indefinite anticoagulation.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 4",
            "pmid": "40423983",
            "remarks": "Changed from 2018 comparison (6-12 months vs >6-12 months) to 2025 comparison (6-12 months vs indefinite). Reassess at end of treatment.",
        }
        recommendations.append(doac_rec)

    elif vte_type == "csvt":
        primary_rec = {
            "id": "ped_rec5_6",
            "statement": f"For cerebral sinus venous thrombosis (CSVT) {'with' if truthy(input.get('csvtHemorrhage')) else 'without'} hemorrhage secondary to venous congestion: anticoagulation alone is suggested over thrombolysis followed by anticoagulation.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH/ISTH 2025 Pediatric VTE — Recommendations 5-6",
            "pmid": "40423983",
            "remarks": "Anticoagulation is suggested over no anticoagulation for CSVT (Rec 5). Anticoagulation alone is suggested over thrombolysis (Rec 6).",
        }

    elif vte_type == "rat_right_atrial_thrombus":
        if truthy(input.get("ratHighRiskFeatures")) and input.get("ratBleedingRisk") == "low":
            primary_rec = {
                "id": "ped_rec7a",
                "statement": "For neonates/pediatric patients with right atrial thrombus (RAT) with high-risk features AND low perceived bleeding risk: anticoagulation is suggested over no anticoagulation.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 7a",
                "pmid": "40423983",
            }
        else:
            primary_rec = {
                "id": "ped_rec7b",
                "statement": "For neonates/pediatric patients with RAT without high-risk features OR with unacceptable perceived bleeding risk: no anticoagulation is suggested over anticoagulation.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 7b",
                "pmid": "40423983",
            }
        recommendations.append(
            {
                "id": "ped_rec8",
                "statement": "For neonates/pediatric patients with RAT requiring antithrombotic treatment: anticoagulation alone is suggested over thrombolysis followed by anticoagulation.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 8",
                "pmid": "40423983",
            }
        )

    elif vte_type == "rvt_renal_vein_thrombosis":
        primary_rec = {
            "id": "ped_rec9",
            "statement": "For neonates with renal vein thrombosis (RVT): anticoagulation is suggested over no anticoagulation.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 9",
            "pmid": "40423983",
        }
        if truthy(input.get("rvtLifeThreatening")):
            recommendations.append(
                {
                    "id": "ped_rec10b",
                    "statement": "For life-threatening RVT in neonates: thrombolysis followed by anticoagulation is suggested over anticoagulation alone.",
                    "strength": "conditional",
                    "certainty": "very_low",
                    "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 10b",
                    "pmid": "40423983",
                }
            )
        else:
            recommendations.append(
                {
                    "id": "ped_rec10a",
                    "statement": "For non-life-threatening RVT in neonates: anticoagulation alone is RECOMMENDED over thrombolysis followed by anticoagulation.",
                    "strength": "strong",
                    "certainty": "very_low",
                    "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 10a",
                    "pmid": "40423983",
                }
            )

    elif vte_type == "pvt_portal_vein_thrombosis":
        if truthy(input.get("pvtOcclusive")):
            primary_rec = {
                "id": "ped_rec11a",
                "statement": "For neonates/children with occlusive portal vein thrombosis (PVT), or children with non-occlusive PVT post liver transplant or unprovoked PVT: anticoagulation is suggested over no anticoagulation.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 11a",
                "pmid": "40423983",
            }
        else:
            primary_rec = {
                "id": "ped_rec11b",
                "statement": "For neonates with non-occlusive PVT or children who have already developed portal hypertension: no anticoagulation is suggested over anticoagulation.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 11b",
                "pmid": "40423983",
            }

    elif vte_type == "cvad_related":
        if input.get("cvadFunctioning") is False:
            primary_rec = {
                "id": "ped_rec16",
                "statement": "For symptomatic CVAD-related thrombosis where the CVAD is no longer required or non-functioning: either immediate or delayed removal of the CVAD is suggested.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 16",
                "pmid": "40423983",
                "remarks": "Evidence upgraded from very low (2018) to low (2025). Either immediate or delayed removal is acceptable.",
            }
        else:
            primary_rec = {
                "id": "ped_rec_cvad_functioning",
                "statement": "For symptomatic CVAD-related thrombosis with a functioning CVAD still required: anticoagulation with the CVAD in place is generally preferred. Consult pediatric hematology.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH/ISTH 2025 Pediatric VTE — Recommendation 9 (2018, not updated)",
                "pmid": "40423983",
            }

    else:
        primary_rec = {
            "id": "ped_default",
            "statement": "Consult pediatric hematology for management of this VTE presentation.",
            "strength": "conditional",
            "certainty": "very_low",
            "source": "ASH/ISTH 2025 Pediatric VTE",
            "pmid": "40423983",
        }

    alerts.append(
        "Pediatric VTE management: Always consult pediatric hematology. DOAC dosing in children requires weight-based calculation and age-specific formulations."
    )

    return {
        "pathway": "pediatric_vte",
        "primaryRecommendation": primary_rec,
        "additionalRecommendations": recommendations,
        "clinicalAlerts": alerts,
        "summary": f"Pediatric VTE — {str(age_group).replace('_', ' ')}, {str(vte_type).replace('_', ' ')}. {primary_rec['statement'].split('.')[0]}.",
    }


# ─── Pathway 5: Pregnancy-Associated VTE ─────────────────────────────────────


def _assess_pregnancy_vte(input: dict) -> dict:
    recommendations: list[dict] = []
    alerts: list[str] = []

    context = input.get("clinicalContext")
    trimester = input.get("trimester")
    thrombophilia_type = input.get("thrombophiliaType")

    alerts.append(
        "DOACs are CONTRAINDICATED in pregnancy. LMWH is the anticoagulant of choice throughout pregnancy. Warfarin may be used postpartum."
    )
    alerts.append(
        "Anticoagulant dosing in pregnancy requires monitoring. Consult maternal-fetal medicine and hematology."
    )

    if context == "treatment_acute_vte":
        primary_rec = {
            "id": "preg_treatment",
            "statement": "For acute VTE during pregnancy, therapeutic-dose LMWH is recommended throughout pregnancy and for at least 6 weeks postpartum (minimum total duration 3 months).",
            "strength": "strong",
            "certainty": "low",
            "source": "ASH 2018 Pregnancy VTE Guidelines",
            "pmid": "30482763",
            "remarks": "LMWH is preferred over UFH for treatment. DOACs are contraindicated. Warfarin may be used postpartum (safe with breastfeeding). Anti-Xa monitoring is recommended for LMWH dosing in pregnancy.",
        }
        recommendations.append(
            {
                "id": "preg_duration",
                "statement": "Anticoagulation should continue for at least 6 weeks postpartum, with a minimum total treatment duration of 3 months.",
                "strength": "conditional",
                "certainty": "low",
                "source": "ASH 2018 Pregnancy VTE Guidelines",
                "pmid": "30482763",
            }
        )
    elif context == "prophylaxis_prior_vte":
        if truthy(input.get("priorVTEProvoked")) and not truthy(thrombophilia_type):
            primary_rec = {
                "id": "preg_prophylaxis_provoked",
                "statement": "For women with a single prior VTE provoked by a transient risk factor (no thrombophilia): antepartum surveillance without prophylaxis may be considered, with postpartum prophylaxis for 6 weeks.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2018 Pregnancy VTE Guidelines",
                "pmid": "30482763",
                "remarks": "Individualize based on the nature of the prior provoking factor, patient preferences, and risk of recurrence.",
            }
        else:
            primary_rec = {
                "id": "preg_prophylaxis_unprovoked",
                "statement": "For women with a prior unprovoked VTE or VTE associated with thrombophilia: antepartum prophylactic-dose LMWH is suggested, with postpartum prophylaxis for at least 6 weeks.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2018 Pregnancy VTE Guidelines",
                "pmid": "30482763",
            }
    elif context == "prophylaxis_thrombophilia":
        if (
            thrombophilia_type == "high_risk"
            or thrombophilia_type == "antiphospholipid_syndrome"
        ):
            primary_rec = {
                "id": "preg_thrombophilia_high",
                "statement": "For women with high-risk thrombophilia (antithrombin deficiency, protein C/S deficiency, homozygous FVL/PGM, or APS) without prior VTE: antepartum prophylactic-dose LMWH is suggested, with postpartum prophylaxis for 6 weeks.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2018 Pregnancy VTE Guidelines",
                "pmid": "30482763",
                "remarks": "APS with obstetric complications: low-dose aspirin + prophylactic LMWH throughout pregnancy and postpartum.",
            }
            if thrombophilia_type == "antiphospholipid_syndrome":
                alerts.append(
                    "Antiphospholipid syndrome (APS): Low-dose aspirin (81 mg/day) plus prophylactic LMWH is recommended throughout pregnancy and postpartum. DOACs are contraindicated."
                )
        elif thrombophilia_type == "low_risk":
            primary_rec = {
                "id": "preg_thrombophilia_low",
                "statement": "For women with low-risk thrombophilia (heterozygous FVL or PGM) without prior VTE: antepartum surveillance without prophylaxis is generally suggested, with individualized postpartum management.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2018 Pregnancy VTE Guidelines",
                "pmid": "30482763",
                "remarks": "Postpartum prophylaxis for 6 weeks may be considered if additional risk factors are present (e.g., cesarean delivery, obesity, immobility).",
            }
        else:
            primary_rec = {
                "id": "preg_no_thrombophilia",
                "statement": "For women without thrombophilia or prior VTE, routine antepartum thromboprophylaxis is not indicated.",
                "strength": "conditional",
                "certainty": "very_low",
                "source": "ASH 2018 Pregnancy VTE Guidelines",
                "pmid": "30482763",
                "remarks": "Consider postpartum prophylaxis after cesarean delivery or in the presence of additional risk factors.",
            }
    else:
        # Postpartum management
        primary_rec = {
            "id": "preg_postpartum",
            "statement": "For postpartum anticoagulation: LMWH or warfarin (target INR 2.0–3.0) may be used. Both are safe with breastfeeding. DOACs should be avoided while breastfeeding (insufficient safety data).",
            "strength": "conditional",
            "certainty": "low",
            "source": "ASH 2018 Pregnancy VTE Guidelines",
            "pmid": "30482763",
            "remarks": "Postpartum prophylaxis duration: 6 weeks for most patients; longer if prior unprovoked VTE or high-risk thrombophilia.",
        }

    return {
        "pathway": "pregnancy_vte",
        "primaryRecommendation": primary_rec,
        "additionalRecommendations": recommendations,
        "clinicalAlerts": alerts,
        "summary": f"Pregnancy VTE — {str(context).replace('_', ' ')}, {coalesce(trimester, 'unspecified')} trimester/postpartum. {primary_rec['statement'].split('.')[0]}.",
    }


# ─── Dispatch ────────────────────────────────────────────────────────────────

_PATHWAYS = {
    "dvt_pe_treatment": _assess_dvt_pe,
    "cancer_associated_thrombosis": _assess_cat,
    "thrombophilia_testing": _assess_thrombophilia,
    "pediatric_vte": _assess_pediatric_vte,
    "pregnancy_vte": _assess_pregnancy_vte,
}


def assess(data: dict) -> dict:
    """Dispatch to the relevant ASH VTE guideline pathway.

    The active pathway is selected by ``data["pathway"]`` (mirrors the TS
    ``VTEPathway`` union). Unknown/missing pathway defaults to DVT/PE treatment.
    """
    pathway = data.get("pathway")
    handler = _PATHWAYS.get(pathway, _assess_dvt_pe)
    return handler(data)
