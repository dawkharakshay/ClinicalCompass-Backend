"""Pediatric Influenza Prevention & Control Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/influenzaPreventionLogic.ts
(assessInfluenzaPrevention). AAP 2025-2026 Influenza Policy Statement /
CDC ACIP 2025-26.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "influenzaprevention"

_REFERENCES = [
    {
        "citation": "AAP Committee on Infectious Diseases. Recommendations for Prevention and Control of Influenza in Children, 2025–2026. Pediatrics. 2025.",
        "url": "https://publications.aap.org/pediatrics",
    },
    {
        "citation": "CDC ACIP. Prevention and Control of Seasonal Influenza with Vaccines: Recommendations of the Advisory Committee on Immunization Practices — United States, 2025–26 Influenza Season. MMWR. 2025.",
        "url": "https://www.cdc.gov/mmwr",
    },
    {
        "citation": "AAP Red Book 2024–2027: Influenza. American Academy of Pediatrics. 2024.",
        "url": "https://redbook.solutions.aap.org",
    },
]


def _js_str(v) -> str:
    """Render a value the way TS template literals do (true/false/null)."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    return str(v)


def _num_str(v) -> str:
    """Render a number in a TS template literal (drop a trailing .0)."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def assess(data: dict) -> dict:
    age_months = num(data.get("ageMonths"), 0)
    symptoms_onset_hours = num(data.get("symptomsOnsetHours"), 0)

    is_first_influenza_season = to_bool(data.get("isFirstInfluenzaSeason"))
    has_chronic_lung_disease = to_bool(data.get("hasChronicLungDisease"))
    has_chronic_heart_disease = to_bool(data.get("hasChronicHeartDisease"))
    has_immunosuppression = to_bool(data.get("hasImmunosuppression"))
    has_hiv = to_bool(data.get("hasHIV"))
    has_neurologic_disorder = to_bool(data.get("hasNeurologicDisorder"))
    has_hemoglobinopathy = to_bool(data.get("hasHemoglobinopathy"))
    has_diabetes = to_bool(data.get("hasDiabetes"))
    has_chronic_kidney_disease = to_bool(data.get("hasChronicKidneyDisease"))
    has_obesity = to_bool(data.get("hasObesity"))
    is_pregnant_adolescent = to_bool(data.get("isPregnantAdolescent"))
    is_resident_long_term_care = to_bool(data.get("isResidentLongTermCareFacility"))
    egg_allergy_type = data.get("eggAllergyType")
    is_immunocompromised = to_bool(data.get("isImmunocompromised"))
    has_asthma = to_bool(data.get("hasAsthma"))
    has_wheezing = to_bool(data.get("hasWheezing"))
    received_prior_season = to_bool(data.get("receivedInfluenzaVaccinePriorSeason"))
    current_season_vaccine_received = to_bool(data.get("currentSeasonVaccineReceived"))
    antiviral_indication_present = to_bool(data.get("antiviralIndicationPresent"))
    influenza_test_positive = to_bool(data.get("influenzaTestPositive"))
    household_contact_high_risk = to_bool(data.get("householdContactHighRisk"))

    urgent_flags: list[str] = []
    counseling_points: list[str] = []

    # --- Risk category ---
    is_high_risk = (
        age_months < 24
        or has_chronic_lung_disease
        or has_chronic_heart_disease
        or has_immunosuppression
        or has_hiv
        or has_neurologic_disorder
        or has_hemoglobinopathy
        or has_diabetes
        or has_chronic_kidney_disease
        or has_obesity
        or is_pregnant_adolescent
        or is_resident_long_term_care
    )

    risk_category = "high_risk" if is_high_risk else "standard"

    # --- Vaccine type selection ---
    can_receive_laiv = (
        age_months >= 24
        and not is_immunocompromised
        and not has_hiv
        and not is_pregnant_adolescent
        and not has_asthma
        and not has_wheezing
        and not has_chronic_lung_disease
    )

    if age_months < 6:
        urgent_flags.append(
            "INFLUENZA VACCINE NOT APPROVED <6 MONTHS: Vaccinate all household contacts and caregivers (cocooning strategy). Ensure mother vaccinated during pregnancy."
        )
        vaccine_type = "Not applicable — cocooning strategy"
        vaccination_rec = "Influenza vaccine NOT approved for infants <6 months. Vaccinate all household contacts and caregivers. Maternal vaccination during pregnancy provides passive protection."
    elif egg_allergy_type == "anaphylaxis":
        vaccine_type = "ccIIV4 (cell-culture based, egg-free) or RIV4 (recombinant, egg-free)"
        vaccination_rec = "EGG ANAPHYLAXIS: Use egg-free vaccine — ccIIV4 (Flucelvax) or RIV4 (Flublok, ≥18 years). Administer in medical setting with 15-min observation. Epinephrine available."
    elif can_receive_laiv:
        vaccine_type = "LAIV4 (FluMist) preferred for healthy children 2–17 years OR IIV4"
        vaccination_rec = "LAIV4 (FluMist intranasal) is an acceptable alternative for healthy children 2–17 years. IIV4 (injectable) is equally effective. Patient/family preference acceptable."
    else:
        vaccine_type = "IIV4 (inactivated influenza vaccine, quadrivalent)"
        _immuno = "immunosuppression" if is_immunocompromised else ""
        _asthma = "asthma/wheezing" if (has_asthma or has_wheezing) else ""
        _preg = "pregnancy" if is_pregnant_adolescent else ""
        vaccination_rec = (
            f"IIV4 (injectable) required. LAIV4 contraindicated due to: {_immuno} {_asthma} {_preg}."
        )

    # --- Doses required ---
    if age_months < 6:
        doses_required = "Not applicable"
    elif is_first_influenza_season and not received_prior_season:
        doses_required = "2 DOSES required (first influenza season): 0.5mL IM × 2, minimum 4 weeks apart. Children 6 months–8 years who have never received influenza vaccine require 2 doses in first season."
    else:
        doses_required = "1 DOSE annually. Children ≥9 years: always 1 dose. Children 6 months–8 years who received ≥2 prior doses: 1 dose."

    # --- Antiviral treatment ---
    if influenza_test_positive and symptoms_onset_hours <= 48:
        if is_high_risk:
            antiviral_rec = "ANTIVIRAL TREATMENT INDICATED (high-risk, symptoms ≤48h): Oseltamivir (Tamiflu) — dose by weight/age. ≥1 year: 30–75mg BID × 5 days. <1 year: 3mg/kg BID × 5 days. Start ASAP — greatest benefit within 48 hours of symptom onset. Do NOT wait for confirmatory test in high-risk patients."
        else:
            antiviral_rec = "Antiviral treatment: Oseltamivir recommended for influenza-positive patients with symptoms ≤48 hours. Reduces duration by ~1 day and severity. Consider for all hospitalized patients regardless of symptom onset timing."
    elif influenza_test_positive and symptoms_onset_hours > 48 and is_high_risk:
        antiviral_rec = "HIGH-RISK + SYMPTOMS >48h: Oseltamivir still recommended for high-risk patients even beyond 48 hours — may reduce complications and hospitalization. Benefit diminishes but risk-benefit favors treatment."
        urgent_flags.append(
            "HIGH-RISK INFLUENZA >48h: Oseltamivir still indicated — reduces hospitalization risk in high-risk patients."
        )
    elif (not influenza_test_positive) and is_high_risk and antiviral_indication_present:
        antiviral_rec = "HIGH-RISK PATIENT with influenza-like illness: Do NOT wait for test results — initiate oseltamivir empirically. Rapid antigen tests have low sensitivity (50–70%). PCR preferred for confirmation."
    else:
        antiviral_rec = "Antiviral treatment not currently indicated. Supportive care (acetaminophen/ibuprofen for fever, hydration). Avoid aspirin (Reye syndrome risk)."

    # --- Chemoprophylaxis ---
    if household_contact_high_risk and influenza_test_positive:
        chemoprophylaxis = "POST-EXPOSURE PROPHYLAXIS (PEP): Oseltamivir for high-risk household contacts. Start within 48 hours of exposure. Duration: 10 days. Dose: same as treatment dose once daily."
        urgent_flags.append(
            "HIGH-RISK HOUSEHOLD CONTACT: Post-exposure prophylaxis with oseltamivir indicated within 48 hours."
        )
    else:
        chemoprophylaxis = "Chemoprophylaxis not routinely indicated. Vaccination is the primary prevention strategy. PEP reserved for high-risk unvaccinated contacts within 48 hours of exposure."

    # --- Counseling ---
    counseling_points.append(
        "Annual influenza vaccination is the most effective prevention strategy — recommend for all children ≥6 months."
    )
    counseling_points.append(
        "Vaccination timing: ideally by end of October. Vaccinate any time during influenza season."
    )
    counseling_points.append(
        "Avoid aspirin and aspirin-containing products in children with influenza (Reye syndrome risk)."
    )
    counseling_points.append(
        "Fever management: acetaminophen or ibuprofen (≥6 months). Ibuprofen NOT for <6 months."
    )
    counseling_points.append(
        "Return precautions: worsening after initial improvement, respiratory distress, persistent fever >5 days, altered mental status."
    )
    counseling_points.append(
        "Cocooning: vaccinate all household contacts of infants <6 months and immunocompromised individuals."
    )

    if is_high_risk:
        counseling_points.append(
            "HIGH-RISK CHILD: Prioritize early vaccination. Do not delay antiviral treatment — initiate empirically if influenza suspected."
        )

    if len(urgent_flags) > 0:
        primary_rec = urgent_flags[0]
    else:
        years = math.floor(age_months / 12)
        months = age_months % 12
        if current_season_vaccine_received:
            season_str = "Current season vaccine: RECEIVED."
        else:
            season_str = "Current season vaccine: NOT YET RECEIVED — vaccinate now."
        test_str = "Influenza test POSITIVE — antiviral indicated." if influenza_test_positive else ""
        primary_rec = (
            f"INFLUENZA PREVENTION — {risk_category.replace('_', ' ').upper()}. "
            f"Age {_num_str(years)} years {_num_str(months)} months. "
            f"{season_str} {test_str}"
        )

    return {
        "primaryRecommendation": primary_rec,
        "riskCategory": risk_category,
        "vaccinationRecommendation": vaccination_rec,
        "vaccineType": vaccine_type,
        "dosesRequired": doses_required,
        "antiviralRecommendation": antiviral_rec,
        "chemoprophylaxisRecommendation": chemoprophylaxis,
        "urgentFlags": urgent_flags,
        "counselingPoints": counseling_points,
        "evidenceLevel": "A",
        "rationale": (
            f"Age {_num_str(age_months)} months. Risk: {risk_category}. "
            f"Egg allergy: {_js_str(egg_allergy_type)}. "
            f"Immunocompromised: {_js_str(is_immunocompromised)}. "
            f"Influenza positive: {_js_str(influenza_test_positive)}. "
            f"Symptom onset: {_num_str(symptoms_onset_hours)}h. "
            f"Per AAP 2025–2026 Influenza Policy Statement."
        ),
        "references": _REFERENCES,
    }
