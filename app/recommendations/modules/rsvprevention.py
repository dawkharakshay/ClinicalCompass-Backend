"""RSV Prevention Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/rsvPreventionLogic.ts
(assessRSVPrevention) — AAP 2024 Nirsevimab + Palivizumab policy statement.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "rsvprevention"

_REFERENCES = [
    {
        "citation": "AAP Committee on Infectious Diseases. Nirsevimab (Beyfortus) for RSV Prevention. Pediatrics. 2024.",
        "url": "https://publications.aap.org/pediatrics",
    },
    {
        "citation": "Hammitt LL et al. Nirsevimab for Prevention of RSV in Healthy Late-Preterm and Term Infants. NEJM. 2022;386:837–846. (MELODY trial)",
        "url": "https://www.nejm.org/doi/10.1056/NEJMoa2110275",
    },
    {
        "citation": "Griffin MP et al. Single-Dose Nirsevimab for Prevention of RSV in Preterm Infants. NEJM. 2020;383:415–425. (MEDLEY trial)",
        "url": "https://www.nejm.org/doi/10.1056/NEJMoa1913556",
    },
    {
        "citation": "Kampmann B et al. Bivalent Prefusion F Vaccine in Pregnancy to Prevent RSV Illness in Infants. NEJM. 2023;388:1451–1464. (Abrysvo maternal vaccine)",
        "url": "https://www.nejm.org/doi/10.1056/NEJMoa2216480",
    },
]


def assess(data: dict) -> dict:
    age_months = parse_float(data.get("ageMonths"))
    ga_weeks = parse_float(data.get("gestationalAgeWeeks"))

    is_current_rsv_season = truthy(data.get("isCurrentRSVSeason"))
    is_premature = truthy(data.get("isPremature"))
    has_chd = truthy(data.get("hasCongenitalHeartDisease"))
    chd_requires_medication = truthy(data.get("chdRequiresMedication"))
    has_cld = truthy(data.get("hasChronicLungDisease"))
    requires_supplemental_o2 = truthy(data.get("requiresSupplementalO2"))
    is_immunocompromised = truthy(data.get("isImmunocompromised"))
    has_down_syndrome = truthy(data.get("hasDownSyndrome"))
    has_cystic_fibrosis = truthy(data.get("hasCysticFibrosis"))
    has_neuromuscular_disease = truthy(data.get("hasNeuromuscularDisease"))

    received_nirsevimab = truthy(data.get("receivedNirsevimabThisSeason"))
    mother_received_rsv_vaccine = truthy(data.get("motherReceivedRSVVaccine"))
    has_active_rsv_infection = truthy(data.get("hasActiveRSVInfection"))

    # JS: motherVaccinationWeeksBeforeBirth !== null && >= 2. A missing/None
    # value parses to NaN, and NaN >= 2 is False, matching the null branch.
    mother_vax_weeks = parse_float(data.get("motherVaccinationWeeksBeforeBirth"))

    urgent_flags: list[str] = []
    counseling_points: list[str] = []

    # --- Active RSV infection ---
    if has_active_rsv_infection:
        urgent_flags.append(
            "ACTIVE RSV INFECTION: Nirsevimab/palivizumab are PREVENTIVE — not therapeutic. Supportive care: nasal suctioning, hydration, oxygen if SpO2 <90–92%. Hospitalize if respiratory distress, apnea, or poor feeding."
        )

    # --- Risk category ---
    if is_immunocompromised or (has_chd and chd_requires_medication and ga_weeks < 32):
        risk_category = "very_high_risk"
    elif ga_weeks < 29 or (has_chd and chd_requires_medication) or (has_cld and requires_supplemental_o2):
        risk_category = "high_risk"
    elif (
        (is_premature and ga_weeks >= 29 and ga_weeks <= 34)
        or has_chd
        or has_cld
        or has_down_syndrome
        or has_cystic_fibrosis
        or has_neuromuscular_disease
    ):
        risk_category = "moderate_risk"
    else:
        risk_category = "standard_risk"

    # --- Nirsevimab recommendation ---
    if age_months > 24:
        nirsevimab_rec = "Nirsevimab not indicated for children >24 months (approved for ≤24 months entering second RSV season only if high-risk)."
        dosing = "Not applicable"
    elif received_nirsevimab:
        nirsevimab_rec = "Nirsevimab already received this RSV season. Single dose provides season-long protection (5 months). No additional dose needed unless entering second RSV season with high-risk condition."
        dosing = "Already administered this season."
    elif not is_current_rsv_season:
        nirsevimab_rec = "Not currently RSV season. Administer nirsevimab at the start of RSV season (October) or at birth if born during RSV season."
        dosing = "Administer at RSV season onset."
    else:
        # Current RSV season + not yet received
        if mother_received_rsv_vaccine and mother_vax_weeks >= 2 and age_months < 6:
            nirsevimab_rec = "MATERNAL RSV VACCINE RECEIVED: Nirsevimab may be deferred for healthy term/late-preterm infants born ≥2 weeks after maternal Abrysvo vaccination (AAP 2024). Nirsevimab still recommended for high-risk infants regardless of maternal vaccination."
        else:
            qualifier = (
                "All infants <8 months entering first RSV season"
                if risk_category == "standard_risk"
                else "High-risk infant — strongly recommended"
            )
            nirsevimab_rec = f"NIRSEVIMAB (BEYFORTUS) RECOMMENDED: {qualifier}. Single dose provides ~5 months protection. MELODY trial: 74.5% efficacy against RSV LRTI."

        # Dosing
        if risk_category in ("high_risk", "very_high_risk"):
            dosing = "Nirsevimab 200mg IM (≥5kg) or 100mg IM (<5kg) for high-risk infants. Standard dose: 50mg (<5kg) or 100mg (≥5kg). Note: 200mg dose for high-risk children entering second RSV season (up to 24 months)."
        else:
            dosing = "Nirsevimab: 50mg IM if birth weight <5kg; 100mg IM if ≥5kg. Single dose. Administer before or during RSV season."

    # --- Palivizumab recommendation ---
    if risk_category in ("very_high_risk", "high_risk"):
        if received_nirsevimab:
            palivizumab_rec = "Nirsevimab received — palivizumab not needed. Nirsevimab has replaced palivizumab for most indications (AAP 2024)."
        else:
            palivizumab_rec = "PALIVIZUMAB (SYNAGIS) — ALTERNATIVE if nirsevimab unavailable: 15mg/kg IM monthly × 5 doses during RSV season. Indicated for: GA <29 weeks (≤12 months at start of season), hemodynamically significant CHD, severe CLD requiring medical therapy. Nirsevimab preferred when available."
    else:
        palivizumab_rec = "Palivizumab not indicated for standard/moderate risk. Nirsevimab is preferred for all eligible infants."

    # --- Maternal vaccination note ---
    maternal_vaccination_note = "Maternal RSV Vaccine (Abrysvo — Pfizer): FDA-approved for pregnant women at 32–36 weeks gestation. Provides passive immunity to newborn for first ~6 months. AAP 2024: shared decision-making for maternal vaccination vs. nirsevimab. Both strategies are effective. Maternal vaccination preferred if administered ≥2 weeks before birth."

    # --- Seasonal guidance ---
    seasonal_guidance = "RSV season: typically October–March in most US regions (earlier in some southern states). Administer nirsevimab at start of RSV season or at birth if born during season. Infants born during RSV season: administer before discharge from birth hospitalization."

    # --- Counseling ---
    counseling_points.append(
        "RSV is the leading cause of infant hospitalization in the US — 58,000–80,000 hospitalizations/year in children <5 years."
    )
    counseling_points.append(
        "Nirsevimab (Beyfortus) is a monoclonal antibody — NOT a vaccine. It provides passive immunization for one RSV season."
    )
    counseling_points.append(
        "Hand hygiene is the most important non-pharmacologic prevention: wash hands before touching infant."
    )
    counseling_points.append(
        "Avoid exposure to sick contacts, especially during RSV season (October–March)."
    )
    counseling_points.append(
        "Breastfeeding provides some protection against RSV — encourage breastfeeding."
    )
    counseling_points.append(
        "Return precautions: fast breathing, nasal flaring, retractions, poor feeding, cyanosis, apnea."
    )

    if risk_category in ("high_risk", "very_high_risk"):
        counseling_points.append(
            "HIGH-RISK INFANT: Avoid daycare during RSV season if possible. Limit visitors. Ensure all household contacts vaccinated against influenza."
        )
        # JS: riskCategory.replace("_", " ") replaces only the FIRST underscore.
        urgent_flags.append(
            f"HIGH-RISK RSV: {risk_category.replace('_', ' ', 1).upper()} — ensure nirsevimab administered before RSV season. Palivizumab as backup if nirsevimab unavailable."
        )

    if len(urgent_flags) > 0 and not has_active_rsv_infection:
        primary_rec = urgent_flags[0]
    elif has_active_rsv_infection:
        primary_rec = "ACTIVE RSV INFECTION: Supportive care. Prophylaxis not therapeutic."
    else:
        season_str = "RSV season ACTIVE." if is_current_rsv_season else "Off-season."
        nirsevimab_str = "Nirsevimab: RECEIVED." if received_nirsevimab else "Nirsevimab: NOT YET RECEIVED."
        # JS: riskCategory.replace(/_/g, " ") replaces ALL underscores.
        primary_rec = (
            f"RSV PREVENTION — {risk_category.replace('_', ' ').upper()}. "
            f"Age {_js_num(age_months, data.get('ageMonths'))} months. "
            f"GA {_js_num(ga_weeks, data.get('gestationalAgeWeeks'))} weeks. "
            f"{season_str} {nirsevimab_str}"
        )

    return {
        "primaryRecommendation": primary_rec,
        "riskCategory": risk_category,
        "nirsevimabRecommendation": nirsevimab_rec,
        "palivizumabRecommendation": palivizumab_rec,
        "maternalVaccinationNote": maternal_vaccination_note,
        "dosing": dosing,
        "seasonalGuidance": seasonal_guidance,
        "urgentFlags": urgent_flags,
        "counselingPoints": counseling_points,
        "evidenceLevel": "A",
        "rationale": (
            f"Age {_js_num(age_months, data.get('ageMonths'))} months. "
            f"GA {_js_num(ga_weeks, data.get('gestationalAgeWeeks'))} weeks. "
            f"Risk: {risk_category}. "
            f"RSV season: {_js_bool(is_current_rsv_season)}. "
            f"Nirsevimab received: {_js_bool(received_nirsevimab)}. "
            f"Maternal RSV vaccine: {_js_bool(mother_received_rsv_vaccine)}. "
            f"Per AAP 2024 nirsevimab policy."
        ),
        "references": _REFERENCES,
    }


def _js_num(parsed: float, raw) -> str:
    """Render a number the way JS template-literal interpolation would.

    The TS interpolates the raw numeric input directly (an integer renders
    without a trailing ``.0``). Mirror that: integral floats lose the decimal.
    """
    if parsed == parsed and parsed == int(parsed):  # not NaN and integral
        return str(int(parsed))
    return str(parsed)


def _js_bool(value: bool) -> str:
    return "true" if value else "false"
