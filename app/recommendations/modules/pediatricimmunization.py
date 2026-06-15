"""Pediatric Immunization Schedule Clinical Compass (AAP 2026).

Ported 1:1 from
old_static_code/client/src/lib/pediatricImmunizationLogic.ts
(assessPediatricImmunization).
"""

from __future__ import annotations

from app.recommendations.jslib import truthy

LOGIC_KEY = "pediatricimmunization"

_NEXT_VISIT_MAP = {
    "newborn": "Return at 2 months for DTaP, Hib, IPV, PCV, RV, and HepB dose 2",
    "2_months": "Return at 4 months for DTaP dose 2, Hib dose 2, IPV dose 2, PCV dose 2, RV dose 2",
    "4_months": "Return at 6 months for DTaP dose 3, HepB dose 3, PCV dose 3, influenza (if in season)",
    "6_months": "Return at 9 months for developmental screening; 12 months for MMR, varicella, HepA, PCV booster",
    "9_months": "Return at 12 months for MMR, varicella, HepA dose 1, PCV booster",
    "12_months": "Return at 15 months for Hib booster, DTaP dose 4",
    "15_months": "Return at 18 months for HepA dose 2 (if dose 1 given at 12 months)",
    "18_months": "Return at 24 months for developmental screening",
    "24_months": "Annual influenza vaccine; next major vaccines at 4–6 years",
    "2_3_years": "Annual influenza vaccine; next major vaccines at 4–6 years",
    "4_6_years": "DTaP dose 5, IPV dose 4, MMR dose 2, varicella dose 2. Next: 11–12 years for Tdap, HPV, MenACWY",
    "7_10_years": "Annual influenza vaccine; catch-up any missed vaccines; next: 11–12 years for Tdap, HPV, MenACWY",
    "11_12_years": "Tdap, HPV series, MenACWY dose 1. MenACWY booster at 16 years",
    "13_15_years": "HPV series completion if started; annual influenza; MenACWY booster at 16",
    "16_18_years": "MenACWY booster (if not given at 16), MenB (shared decision), annual influenza, COVID-19 update",
}

_REFERENCES = [
    {
        "citation": "AAP Committee on Infectious Diseases. Recommended Childhood and Adolescent Immunization Schedule — United States, 2026. Pediatrics. 2026.",
        "url": "https://publications.aap.org/pediatrics",
    },
    {
        "citation": "CDC ACIP. Advisory Committee on Immunization Practices Recommended Immunization Schedule for Children and Adolescents 2025–2026.",
        "url": "https://www.cdc.gov/vaccines/schedules",
    },
    {
        "citation": "AAP Red Book: 2024–2027 Report of the Committee on Infectious Diseases (32nd edition). American Academy of Pediatrics. 2024.",
        "url": "https://redbook.solutions.aap.org",
    },
    {
        "citation": "Hammitt LL et al. Nirsevimab for Prevention of RSV in Healthy Late-Preterm and Term Infants. NEJM. 2022;386:837–846. (MELODY trial)",
        "url": "https://www.nejm.org/doi/10.1056/NEJMoa2110275",
    },
    {
        "citation": "AAP Policy Statement: Immunization of Preterm and Low Birth Weight Infants. Pediatrics. 2025.",
        "url": "https://publications.aap.org/pediatrics",
    },
]


def assess(data: dict) -> dict:
    scheduled: list[dict] = []
    catch_up: list[dict] = []
    high_risk: list[dict] = []
    shared_decision: list[dict] = []
    contraindications: list[str] = []
    precautions: list[str] = []
    urgent_flags: list[str] = []
    counseling_points: list[str] = []

    age_group = data.get("ageGroup")
    gestational_age_weeks = data.get("gestationalAgeWeeks")
    hiv_status = data.get("hivStatus")
    catch_up_vaccines = data.get("catchUpVaccines") or []

    # ─── Contraindications ──────────────────────────────────────────────
    if truthy(data.get("hasEggAllergy")):
        precautions.append(
            "Egg allergy: Influenza vaccine can be administered in any setting (AAP 2026). Severe anaphylaxis to egg → administer in medical setting with 15-min observation."
        )
    if truthy(data.get("hasGelatinAllergy")):
        contraindications.append(
            "Gelatin allergy: Avoid MMR, varicella, and some influenza vaccines containing gelatin. Consult allergist."
        )
    if truthy(data.get("isImmunocompromised")) or hiv_status == "positive":
        contraindications.append(
            "Live vaccines (MMR, varicella, LAIV, rotavirus) are CONTRAINDICATED in severely immunocompromised patients. Verify immune status before administration."
        )

    # ─── Age-specific routine vaccines ──────────────────────────────────
    if age_group == "newborn":
        if truthy(data.get("motherHBsAgPositive")):
            urgent_flags.append(
                "URGENT: Mother HBsAg-positive — administer HepB vaccine + HBIG within 12 hours of birth (AAP 2026)."
            )
            scheduled.append({
                "vaccine": "Hepatitis B (HepB) + HBIG",
                "doses": "Dose 1 within 12h of birth",
                "notes": "Mother HBsAg+: HBIG 0.5mL IM + HepB vaccine simultaneously at different sites",
                "priority": "routine",
            })
        else:
            scheduled.append({
                "vaccine": "Hepatitis B (HepB)",
                "doses": "Dose 1 at birth",
                "notes": "Administer before hospital discharge. If mother HBsAg unknown, test mother STAT and give HepB within 12h",
                "priority": "routine",
            })
        if truthy(data.get("isPreterm")) and _lt(gestational_age_weeks, 37):
            precautions.append(
                f"Preterm infant ({gestational_age_weeks} weeks): HepB series should begin at chronological age 1 month or at hospital discharge if before 1 month, regardless of weight. All other vaccines given at full chronological age per schedule."
            )

    elif age_group == "2_months":
        scheduled.extend([
            {"vaccine": "DTaP", "doses": "Dose 1", "notes": "Diphtheria, tetanus, pertussis. Preferred brands: Daptacel, Infanrix, Pediarix (combo)", "priority": "routine"},
            {"vaccine": "Hib (PRP-OMP or PRP-T)", "doses": "Dose 1", "notes": "Haemophilus influenzae type b. PedvaxHIB or ActHIB", "priority": "routine"},
            {"vaccine": "IPV", "doses": "Dose 1", "notes": "Inactivated poliovirus vaccine", "priority": "routine"},
            {"vaccine": "PCV15 or PCV20", "doses": "Dose 1", "notes": "Pneumococcal conjugate vaccine. PCV20 preferred (AAP 2026 — broader coverage)", "priority": "routine"},
            {"vaccine": "RV", "doses": "Dose 1", "notes": "Rotavirus. RV1 (Rotarix) or RV5 (RotaTeq). Max age for first dose: 14 weeks 6 days", "priority": "routine"},
            {"vaccine": "Hepatitis B (HepB)", "doses": "Dose 2 (if not given at 1–2 months)", "notes": "Complete series by 6–18 months", "priority": "routine"},
        ])

    elif age_group == "4_months":
        scheduled.extend([
            {"vaccine": "DTaP", "doses": "Dose 2", "notes": "4-week minimum interval from dose 1", "priority": "routine"},
            {"vaccine": "Hib", "doses": "Dose 2", "notes": "4-week minimum interval", "priority": "routine"},
            {"vaccine": "IPV", "doses": "Dose 2", "notes": "4-week minimum interval", "priority": "routine"},
            {"vaccine": "PCV15/PCV20", "doses": "Dose 2", "notes": "4-week minimum interval", "priority": "routine"},
            {"vaccine": "RV", "doses": "Dose 2", "notes": "4-week minimum interval. Max age for any dose: 8 months 0 days", "priority": "routine"},
        ])

    elif age_group == "6_months":
        scheduled.extend([
            {"vaccine": "DTaP", "doses": "Dose 3", "notes": "4-week minimum interval from dose 2", "priority": "routine"},
            {"vaccine": "Hib", "doses": "Dose 3 (if PRP-T series)", "notes": "Not needed if PRP-OMP (PedvaxHIB) series — only 2 primary doses", "priority": "routine"},
            {"vaccine": "IPV", "doses": "Dose 3", "notes": "4-week minimum interval", "priority": "routine"},
            {"vaccine": "PCV15/PCV20", "doses": "Dose 3", "notes": "4-week minimum interval", "priority": "routine"},
            {"vaccine": "HepB", "doses": "Dose 3", "notes": "Final dose. Minimum 8 weeks from dose 2, minimum 16 weeks from dose 1, minimum age 24 weeks", "priority": "routine"},
            {"vaccine": "Influenza (IIV4 or ccIIV4)", "doses": "Annual — 2 doses first season", "notes": "Start at 6 months. Two doses 4 weeks apart in first influenza season, then 1 dose annually", "priority": "routine"},
        ])
        if truthy(data.get("rsvSeasonActive")):
            scheduled.append({
                "vaccine": "Nirsevimab (Beyfortus)",
                "doses": "Single dose 50mg (<5kg) or 100mg (≥5kg)",
                "notes": "RSV monoclonal antibody. Administer before or during RSV season (October–March). NOT a vaccine — passive immunization. AAP 2024",
                "priority": "routine",
            })

    elif age_group == "12_months":
        scheduled.extend([
            {"vaccine": "MMR", "doses": "Dose 1", "notes": "Measles, mumps, rubella. Minimum age 12 months. CONTRAINDICATED in immunocompromised", "priority": "routine"},
            {"vaccine": "Varicella (VAR)", "doses": "Dose 1", "notes": "Minimum age 12 months. CONTRAINDICATED in immunocompromised. Can give MMRV (ProQuad)", "priority": "routine"},
            {"vaccine": "HepA", "doses": "Dose 1 of 2", "notes": "Two-dose series starting at 12–23 months. Minimum 6-month interval between doses", "priority": "routine"},
            {"vaccine": "PCV15/PCV20", "doses": "Dose 4 (booster)", "notes": "12–15 months. If PCV20 used throughout, no PPSV23 needed", "priority": "routine"},
        ])

    elif age_group == "15_months":
        scheduled.extend([
            {"vaccine": "Hib", "doses": "Booster dose", "notes": "12–15 months. Final dose of primary series", "priority": "routine"},
            {"vaccine": "DTaP", "doses": "Dose 4", "notes": "15–18 months. Minimum 6 months from dose 3", "priority": "routine"},
        ])

    elif age_group == "18_months":
        scheduled.extend([
            {"vaccine": "HepA", "doses": "Dose 2 (if dose 1 given at 12–17 months)", "notes": "Minimum 6-month interval from dose 1", "priority": "routine"},
        ])

    elif age_group == "4_6_years":
        scheduled.extend([
            {"vaccine": "DTaP", "doses": "Dose 5 (final)", "notes": "4–6 years. Not needed if dose 4 given at ≥4 years", "priority": "routine"},
            {"vaccine": "IPV", "doses": "Dose 4 (final)", "notes": "4–6 years. Minimum 6 months from dose 3", "priority": "routine"},
            {"vaccine": "MMR", "doses": "Dose 2", "notes": "4–6 years. Minimum 4 weeks from dose 1", "priority": "routine"},
            {"vaccine": "Varicella (VAR)", "doses": "Dose 2", "notes": "4–6 years. Minimum 3 months from dose 1", "priority": "routine"},
            {"vaccine": "Influenza", "doses": "Annual", "notes": "1 dose annually (unless first season)", "priority": "routine"},
        ])

    elif age_group == "11_12_years":
        scheduled.extend([
            {"vaccine": "Tdap", "doses": "Single dose", "notes": "Tetanus, diphtheria, pertussis booster. Preferred at 11–12 years", "priority": "routine"},
            {"vaccine": "HPV (Gardasil 9)", "doses": "2-dose series (if started <15 years)", "notes": "0, 6–12 months. If started ≥15 years: 3-dose series at 0, 1–2, 6 months. Recommended for all genders", "priority": "routine"},
            {"vaccine": "MenACWY (MenQuadfi or Menveo)", "doses": "Dose 1", "notes": "Meningococcal ACWY. Booster at 16 years", "priority": "routine"},
            {"vaccine": "COVID-19 (updated formulation)", "doses": "Per current CDC/AAP guidance", "notes": "Annual updated vaccine. Shared decision-making for low-risk adolescents per AAP 2026", "priority": "shared_decision"},
            {"vaccine": "Influenza", "doses": "Annual", "notes": "IIV4 or LAIV4 (healthy, non-immunocompromised). LAIV4 not for immunocompromised or pregnant", "priority": "routine"},
        ])
        if truthy(data.get("isPregnant")):
            precautions.append(
                "Pregnant adolescent: Tdap recommended during each pregnancy (27–36 weeks). HPV series should be deferred until after pregnancy. Influenza IIV4 (not LAIV4) recommended."
            )
            scheduled.append({
                "vaccine": "Tdap (during pregnancy)",
                "doses": "27–36 weeks gestation",
                "notes": "Protects newborn against pertussis via maternal antibody transfer",
                "priority": "routine",
            })

    elif age_group == "16_18_years":
        scheduled.extend([
            {"vaccine": "MenACWY booster", "doses": "Dose 2 at 16 years", "notes": "If dose 1 given at 11–12 years. Required for college entry in most states", "priority": "routine"},
            {"vaccine": "MenB (Bexsero or Trumenba)", "doses": "2-dose series (Bexsero) or 3-dose series (Trumenba)", "notes": "Shared decision-making at 16–23 years. Preferred age 16–18 years. Recommended for asplenia/complement deficiency", "priority": "shared_decision"},
            {"vaccine": "Influenza", "doses": "Annual", "notes": "Annual updated influenza vaccine", "priority": "routine"},
            {"vaccine": "COVID-19", "doses": "Annual updated formulation", "notes": "Per current AAP/CDC guidance", "priority": "shared_decision"},
        ])

    # ─── High-risk additions ────────────────────────────────────────────
    if truthy(data.get("hasAsplenia")) or truthy(data.get("hasSickleCellDisease")):
        high_risk.extend([
            {"vaccine": "PCV20 + PPSV23", "doses": "PCV20 then PPSV23 ≥8 weeks later", "notes": "Functional or anatomic asplenia: enhanced pneumococcal protection. Revaccinate with PPSV23 every 5 years", "priority": "high_risk"},
            {"vaccine": "MenACWY", "doses": "2-dose primary series + booster every 3 years", "notes": "Asplenia: 2-dose primary series at 8-week interval, then booster every 3 years", "priority": "high_risk"},
            {"vaccine": "MenB", "doses": "2- or 3-dose series", "notes": "Recommended (not shared decision-making) for asplenia/complement deficiency", "priority": "high_risk"},
            {"vaccine": "Hib", "doses": "1 dose if not previously vaccinated", "notes": "Unvaccinated asplenic patients ≥5 years: 1 dose Hib", "priority": "high_risk"},
        ])
        urgent_flags.append(
            "ASPLENIA/SICKLE CELL: Enhanced vaccination required — pneumococcal, meningococcal ACWY + B, Hib. Ensure daily penicillin prophylaxis (until age 5 minimum, often lifelong for SCD)."
        )

    if hiv_status == "positive":
        high_risk.extend([
            {"vaccine": "PCV20 + PPSV23", "doses": "Enhanced series per CD4 count", "notes": "HIV: PCV20 then PPSV23 ≥8 weeks later. Revaccinate PPSV23 every 5 years", "priority": "high_risk"},
            {"vaccine": "HepA + HepB", "doses": "Complete series", "notes": "HIV: ensure complete hepatitis A and B series. Check serology post-series", "priority": "high_risk"},
            {"vaccine": "Influenza IIV4", "doses": "Annual", "notes": "HIV: use IIV4 only (not LAIV4). High-dose IIV4 if CD4 <200", "priority": "high_risk"},
        ])
        if not truthy(data.get("isImmunocompromised")):
            high_risk.append({
                "vaccine": "MMR + Varicella",
                "doses": "Per schedule if CD4 ≥200 cells/μL",
                "notes": "HIV with CD4 ≥200: MMR and varicella can be given. CD4 <200: CONTRAINDICATED",
                "priority": "high_risk",
            })
        urgent_flags.append(
            "HIV-POSITIVE: Live vaccines (MMR, VAR, LAIV) CONTRAINDICATED if CD4 <200 or severely immunosuppressed. Verify CD4 count before any live vaccine."
        )

    if (
        truthy(data.get("hasChronicLungDisease"))
        or truthy(data.get("hasChronicHeartDisease"))
        or truthy(data.get("hasChronicKidneyDisease"))
        or truthy(data.get("hasDiabetes"))
    ):
        high_risk.extend([
            {"vaccine": "PCV20 + PPSV23", "doses": "Enhanced pneumococcal series", "notes": "Chronic disease: PCV20 then PPSV23 ≥8 weeks later if not previously vaccinated", "priority": "high_risk"},
            {"vaccine": "Influenza IIV4", "doses": "Annual — high priority", "notes": "Chronic disease: influenza vaccination is especially important. High-dose IIV4 preferred for CKD/immunosuppressed", "priority": "high_risk"},
        ])

    travel_destination = data.get("travelDestination")
    if travel_destination != "none":
        if travel_destination == "endemic_hepatitis_a":
            high_risk.append({"vaccine": "HepA", "doses": "Accelerated series if needed", "notes": "Travel to endemic area: ensure HepA series complete. Accelerated schedule: 0, 6–12 months", "priority": "high_risk"})
        elif travel_destination == "endemic_meningococcal":
            high_risk.append({"vaccine": "MenACWY + MenB", "doses": "Per age-appropriate schedule", "notes": "Travel to meningococcal belt (sub-Saharan Africa) or Saudi Arabia (Hajj): MenACWY required", "priority": "high_risk"})
        elif travel_destination == "endemic_typhoid":
            high_risk.append({"vaccine": "Typhoid (Ty21a oral or Vi polysaccharide)", "doses": "Per product labeling", "notes": "Travel to typhoid-endemic areas. Oral Ty21a: ≥6 years. Vi polysaccharide: ≥2 years", "priority": "high_risk"})
        elif travel_destination == "endemic_yellow_fever":
            high_risk.append({"vaccine": "Yellow Fever (YF-Vax)", "doses": "Single dose", "notes": "Travel to endemic areas. Minimum age 9 months. Contraindicated in immunocompromised and severe egg allergy", "priority": "high_risk"})

    # ─── Catch-up vaccines ──────────────────────────────────────────────
    if truthy(data.get("hasCatchUpNeeds")):
        catch_up.append({
            "vaccine": "Catch-up schedule",
            "doses": "Per AAP/CDC catch-up schedule",
            "notes": "Use minimum intervals between doses. Do not restart series — continue from where left off. Consult AAP catch-up immunization schedule 2026",
            "priority": "catch_up",
        })
        if len(catch_up_vaccines) > 0:
            for v in catch_up_vaccines:
                catch_up.append({
                    "vaccine": v,
                    "doses": "Per catch-up schedule",
                    "notes": "Minimum intervals apply. Consult AAP 2026 catch-up schedule",
                    "priority": "catch_up",
                })

    # ─── RSV nirsevimab ─────────────────────────────────────────────────
    if truthy(data.get("rsvSeasonActive")) and age_group in (
        "newborn", "2_months", "4_months", "6_months"
    ):
        if not any("Nirsevimab" in v["vaccine"] for v in scheduled):
            scheduled.append({
                "vaccine": "Nirsevimab (Beyfortus)",
                "doses": "50mg if <5kg; 100mg if ≥5kg",
                "notes": "RSV passive immunization. Administer before or during RSV season. Infants born during RSV season: administer before discharge. AAP 2024",
                "priority": "routine",
            })

    # ─── COVID-19 ───────────────────────────────────────────────────────
    covid_status = data.get("covidVaccinationStatus")
    if covid_status != "up_to_date":
        shared_decision.append({
            "vaccine": "COVID-19 (updated formulation)",
            "doses": "Per current AAP/CDC guidance",
            "notes": f"Status: {covid_status}. AAP 2026: recommends updated annual COVID-19 vaccine for all children ≥6 months. Note: federal guidance may diverge — shared decision-making for low-risk children.",
            "priority": "shared_decision",
        })

    # ─── Parent counseling ──────────────────────────────────────────────
    counseling_points.extend([
        "Vaccine Information Statements (VIS) must be provided before each vaccine dose (federal law).",
        "VAERS reporting: any serious adverse event after vaccination should be reported at vaers.hhs.gov.",
        "Combination vaccines (Pediarix, Pentacel, Vaxelis) reduce the number of injections — discuss with family.",
        "Fever after vaccination is expected and can be managed with acetaminophen or ibuprofen (≥6 months). Do NOT give aspirin to children.",
        "Immunization records should be maintained in the state immunization information system (IIS/registry).",
    ])

    if truthy(data.get("isPreterm")):
        counseling_points.append(
            f"Preterm infants ({gestational_age_weeks} weeks): vaccinate at full chronological age per schedule — NOT corrected age. Preterm infants are at higher risk for vaccine-preventable diseases."
        )

    # ─── Primary recommendation ─────────────────────────────────────────
    age_group_label = age_group.replace("_", " ") if isinstance(age_group, str) else str(age_group)
    primary_rec = f"ROUTINE IMMUNIZATION — Age Group: {age_group_label} | "
    if len(urgent_flags) > 0:
        primary_rec = urgent_flags[0] + " | "
    primary_rec += f"{len(scheduled)} routine vaccine(s) due. "
    if len(high_risk) > 0:
        primary_rec += f"{len(high_risk)} high-risk addition(s) indicated. "
    if len(catch_up) > 0:
        primary_rec += f"Catch-up needed for {len(catch_up_vaccines)} vaccine(s). "
    primary_rec += "Evidence Level A (AAP 2026 Schedule)."

    next_visit = _NEXT_VISIT_MAP.get(age_group)
    if next_visit is None:
        next_visit = "Follow AAP periodicity schedule"

    is_preterm = truthy(data.get("isPreterm"))
    preterm_str = f"Preterm {gestational_age_weeks} weeks." if is_preterm else ""
    hiv_str = f"HIV status: {hiv_status}." if hiv_status != "negative" else ""
    asplenia_str = "Asplenia present." if truthy(data.get("hasAsplenia")) else ""
    special_population = data.get("specialPopulation")
    rationale = (
        f"Age group: {age_group}. Special population: {special_population}. "
        f"{preterm_str} {hiv_str} {asplenia_str} "
        "Recommendations per AAP 2026 Immunization Schedule and Red Book 2024–2027."
    )

    return {
        "primaryRecommendation": primary_rec,
        "scheduledVaccines": scheduled,
        "catchUpVaccines": catch_up,
        "highRiskAdditions": high_risk,
        "sharedDecisionVaccines": shared_decision,
        "contraindications": contraindications,
        "precautions": precautions,
        "urgentFlags": urgent_flags,
        "nextVisitSchedule": next_visit,
        "parentCounselingPoints": counseling_points,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }


def _lt(value, threshold) -> bool:
    """JS ``<`` numeric comparison; None coerces to NaN (always False)."""
    try:
        return float(value) < threshold
    except (TypeError, ValueError):
        return False
