"""Neonatal Hyperbilirubinemia Clinical Compass.

Ported 1:1 from
old_static_code/client/src/lib/neonatalHyperbilirubinemiaLogic.ts
(assessNeonatalHyperbilirubinemia). AAP Clinical Practice Guideline 2022.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "neonatalhyperbilirubinemia"

_REFERENCES_FULL = [
    {
        "citation": "Kemper AR et al. Clinical Practice Guideline Revision: Management of Hyperbilirubinemia in the Newborn Infant 35 or More Weeks of Gestation. Pediatrics. 2022;150(3):e2022058859.",
        "url": "https://publications.aap.org/pediatrics/article/150/3/e2022058859",
    },
    {
        "citation": "Bhutani VK et al. Predischarge Bilirubin Nomogram for Identifying Neonates at Risk. Pediatrics. 1999;103(1):6–14.",
        "url": "https://publications.aap.org/pediatrics/article/103/1/6/63498",
    },
]

_REFERENCE_EMERGENCY = [
    {
        "citation": "Kemper AR et al. Clinical Practice Guideline Revision: Management of Hyperbilirubinemia in the Newborn Infant 35 or More Weeks of Gestation. Pediatrics. 2022;150(3):e2022058859.",
        "url": "https://publications.aap.org/pediatrics/article/150/3/e2022058859",
    },
]


def _fmt_num(x: float) -> str:
    """Reproduce JS number-to-string for interpolation (integers without
    trailing .0, floats as-is)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def _to_fixed(x: float, digits: int) -> str:
    """JS ``Number.prototype.toFixed`` — round half away from zero."""
    factor = 10 ** digits
    scaled = x * factor
    rounded = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    return f"{rounded / factor:.{digits}f}"


def assess(data: dict) -> dict:
    gestational_age_weeks = num(data.get("gestationalAgeWeeks"), 0)
    age_hours = num(data.get("ageHours"), 0)
    total_serum_bilirubin = num(data.get("totalSerumBilirubin"), 0)
    direct_bilirubin = num(data.get("directBilirubin"), 0)

    has_isoimmunization = truthy(data.get("hasIsoimmunization"))
    has_g6pd_deficiency = truthy(data.get("hasG6PDDeficiency"))
    has_albumin_low = truthy(data.get("hasAlbuminLow"))
    has_sepsis = truthy(data.get("hasSepsis"))
    has_acidosis = truthy(data.get("hasAcidosis"))
    has_asphyxia = truthy(data.get("hasAsphyxia"))
    is_breastfeeding_only = truthy(data.get("isBreastfeedingOnly"))
    has_weight_loss = truthy(data.get("hasWeightLoss"))
    has_acute_biliary_encephalopathy = truthy(data.get("hasAcuteBiliaryEncephalopathy"))
    has_kernicterus = truthy(data.get("hasKernicterus"))
    currently_on_phototherapy = truthy(data.get("currentlyOnPhototherapy"))
    bilirubin_trend_rising = truthy(data.get("bilirubinTrendRising"))

    urgent_flags: list[str] = []

    # ─── Determine neurotoxicity risk level ──────────────────────────────────
    has_neurotoxicity_risk_factors = (
        has_isoimmunization
        or has_g6pd_deficiency
        or has_albumin_low
        or has_sepsis
        or has_acidosis
        or has_asphyxia
    )

    if gestational_age_weeks >= 38 and not has_neurotoxicity_risk_factors:
        neurotoxicity_risk = "lower"
    elif gestational_age_weeks < 37 and has_neurotoxicity_risk_factors:
        neurotoxicity_risk = "higher"
    else:
        neurotoxicity_risk = "medium"

    # ─── Acute bilirubin encephalopathy / kernicterus ────────────────────────
    if has_acute_biliary_encephalopathy or has_kernicterus:
        urgent_flags.append(
            "ACUTE BILIRUBIN ENCEPHALOPATHY / KERNICTERUS: EMERGENCY exchange transfusion. Intensive phototherapy as bridge. Neurology consult. NICU admission."
        )
        return {
            "primaryRecommendation": "EMERGENCY: Acute bilirubin encephalopathy — IMMEDIATE exchange transfusion. Intensive phototherapy as bridge. NICU admission.",
            "neurotoxicityRisk": neurotoxicity_risk,
            "phototherapyThreshold": 0,
            "exchangeTransfusionThreshold": 0,
            "treatmentDecision": "exchange_transfusion",
            "phototherapyGuidance": "Intensive phototherapy as bridge to exchange transfusion. Maximize skin surface area exposure.",
            "exchangeTransfusionGuidance": "EMERGENCY double-volume exchange transfusion. Use O-negative blood if type-specific not available. NICU required.",
            "feedingGuidance": "Continue breastfeeding/feeding during phototherapy. IV fluids if unable to feed.",
            "followUpBilirubin": "Bilirubin every 2–4 hours during exchange transfusion.",
            "urgentFlags": urgent_flags,
            "dischargeReadiness": "NOT ready for discharge. NICU admission required.",
            "evidenceLevel": "A",
            "rationale": f"Acute bilirubin encephalopathy present. TSB {_fmt_num(total_serum_bilirubin)} mg/dL at {_fmt_num(age_hours)} hours. Emergency exchange transfusion indicated.",
            "references": _REFERENCE_EMERGENCY,
        }

    # ─── Conjugated hyperbilirubinemia ───────────────────────────────────────
    if direct_bilirubin > 1.0 or (
        total_serum_bilirubin != 0
        and direct_bilirubin / total_serum_bilirubin > 0.2
        and total_serum_bilirubin > 5
    ):
        urgent_flags.append(
            f"CONJUGATED HYPERBILIRUBINEMIA (direct bilirubin {_fmt_num(direct_bilirubin)} mg/dL): Evaluate for biliary atresia, Alagille syndrome, metabolic disease. Urgent hepatology/GI referral. Phototherapy NOT effective for conjugated jaundice."
        )

    # ─── AAP 2022 phototherapy thresholds (hour-specific nomogram) ───────────
    if neurotoxicity_risk == "lower":
        if age_hours <= 24:
            phototherapy_threshold, exchange_threshold = 8, 19
        elif age_hours <= 48:
            phototherapy_threshold, exchange_threshold = 13, 22
        elif age_hours <= 72:
            phototherapy_threshold, exchange_threshold = 15, 24
        elif age_hours <= 96:
            phototherapy_threshold, exchange_threshold = 17, 25
        else:
            phototherapy_threshold, exchange_threshold = 17, 25
    elif neurotoxicity_risk == "medium":
        if age_hours <= 24:
            phototherapy_threshold, exchange_threshold = 6, 17
        elif age_hours <= 48:
            phototherapy_threshold, exchange_threshold = 10, 20
        elif age_hours <= 72:
            phototherapy_threshold, exchange_threshold = 13, 22
        elif age_hours <= 96:
            phototherapy_threshold, exchange_threshold = 15, 23
        else:
            phototherapy_threshold, exchange_threshold = 15, 23
    else:
        if age_hours <= 24:
            phototherapy_threshold, exchange_threshold = 5, 15
        elif age_hours <= 48:
            phototherapy_threshold, exchange_threshold = 8, 18
        elif age_hours <= 72:
            phototherapy_threshold, exchange_threshold = 11, 20
        elif age_hours <= 96:
            phototherapy_threshold, exchange_threshold = 13, 21
        else:
            phototherapy_threshold, exchange_threshold = 13, 21

    # ─── Treatment decision ───────────────────────────────────────────────────
    tsb = total_serum_bilirubin

    if tsb >= exchange_threshold:
        treatment_decision = "exchange_transfusion"
        urgent_flags.append(
            f"TSB {_fmt_num(tsb)} mg/dL ≥ EXCHANGE TRANSFUSION THRESHOLD ({exchange_threshold} mg/dL): Prepare for double-volume exchange transfusion. Intensive phototherapy as bridge. NICU admission."
        )
        phototherapy_guidance = "Intensive phototherapy as bridge to exchange transfusion. Maximize skin exposure. Continuous monitoring."
        exchange_guidance = f"EXCHANGE TRANSFUSION INDICATED: TSB {_fmt_num(tsb)} mg/dL ≥ threshold {exchange_threshold} mg/dL. Double-volume exchange (160–200 mL/kg). Use irradiated, CMV-negative blood. NICU required. Repeat bilirubin 2–4 hours post-exchange."
    elif (
        tsb >= phototherapy_threshold + 2
        and currently_on_phototherapy
        and bilirubin_trend_rising
    ):
        treatment_decision = "intensive_phototherapy"
        urgent_flags.append(
            f"TSB RISING DESPITE PHOTOTHERAPY: {_fmt_num(tsb)} mg/dL. Consider intensive phototherapy (multiple lights, fiber-optic blanket). Reassess for exchange transfusion if not responding within 4–6 hours."
        )
        phototherapy_guidance = "INTENSIVE PHOTOTHERAPY: Multiple phototherapy lights + fiber-optic blanket. Maximize skin surface area. Bilirubin every 2–4 hours. Discontinue phototherapy only when TSB ≥2 mg/dL below threshold."
        exchange_guidance = f"Exchange transfusion threshold: {exchange_threshold} mg/dL. Current TSB {_fmt_num(tsb)} mg/dL. Monitor closely — exchange if rising toward threshold."
    elif tsb >= phototherapy_threshold:
        treatment_decision = "phototherapy"
        phototherapy_guidance = f"PHOTOTHERAPY INDICATED: TSB {_fmt_num(tsb)} mg/dL ≥ threshold {phototherapy_threshold} mg/dL. Standard phototherapy (irradiance ≥30 μW/cm²/nm). Recheck bilirubin in 4–6 hours initially, then every 6–12 hours. Discontinue when TSB ≥2 mg/dL below threshold."
        exchange_guidance = f"Exchange transfusion threshold: {exchange_threshold} mg/dL. Current TSB {_fmt_num(tsb)} mg/dL — {_to_fixed(exchange_threshold - tsb, 1)} mg/dL below threshold."
    elif tsb >= phototherapy_threshold - 2:
        treatment_decision = "enhance_feeding"
        phototherapy_guidance = f"TSB {_fmt_num(tsb)} mg/dL — within 2 mg/dL of phototherapy threshold ({phototherapy_threshold} mg/dL). Enhance feeding, monitor closely. Recheck bilirubin in 4–6 hours."
        exchange_guidance = f"Exchange transfusion threshold: {exchange_threshold} mg/dL. Not currently indicated."
    else:
        treatment_decision = "observe"
        phototherapy_guidance = f"TSB {_fmt_num(tsb)} mg/dL — below phototherapy threshold ({phototherapy_threshold} mg/dL). Observe. Ensure adequate feeding. Follow-up bilirubin per predischarge nomogram zone."
        exchange_guidance = "Exchange transfusion not indicated."

    # ─── Feeding guidance ────────────────────────────────────────────────────
    if is_breastfeeding_only and has_weight_loss:
        feeding_guidance = "BREASTFEEDING JAUNDICE: Increase breastfeeding frequency to ≥8–12 times/day. Lactation consultant referral. Supplement with expressed breast milk or formula if weight loss >10% or inadequate milk supply. Do NOT routinely discontinue breastfeeding."
    else:
        feeding_guidance = "Ensure adequate feeding (≥8–12 feeds/day for breastfed infants). IV hydration only if severely dehydrated or unable to feed. Supplementation with formula acceptable if weight loss >10%."

    # ─── Follow-up bilirubin ─────────────────────────────────────────────────
    if treatment_decision in ("exchange_transfusion", "intensive_phototherapy"):
        follow_up_bilirubin = "Bilirubin every 2–4 hours during treatment. Rebound bilirubin 24 hours after phototherapy discontinuation."
    elif treatment_decision == "phototherapy":
        follow_up_bilirubin = "Recheck bilirubin in 4–6 hours initially, then every 6–12 hours. Rebound bilirubin 24 hours after phototherapy discontinuation."
    else:
        follow_up_bilirubin = "Follow-up bilirubin based on predischarge nomogram zone and risk factors. High-intermediate or high zone: recheck within 24 hours of discharge."

    # ─── Discharge readiness ─────────────────────────────────────────────────
    if treatment_decision in ("observe", "enhance_feeding"):
        discharge_readiness = "Discharge may be appropriate if TSB in low or low-intermediate zone, adequate feeding, and reliable follow-up arranged. Follow-up bilirubin within 24–48 hours of discharge if in high-intermediate zone."
    else:
        discharge_readiness = "NOT ready for discharge. Continue treatment and monitoring."

    if urgent_flags:
        primary_rec = urgent_flags[0]
    else:
        decision_display = treatment_decision.replace("_", " ").upper()
        primary_rec = f"NEONATAL JAUNDICE — TSB {_fmt_num(tsb)} mg/dL at {_fmt_num(age_hours)} hours. {_fmt_num(gestational_age_weeks)} weeks GA. Risk: {neurotoxicity_risk}. Phototherapy threshold: {phototherapy_threshold} mg/dL. Decision: {decision_display}."

    return {
        "primaryRecommendation": primary_rec,
        "neurotoxicityRisk": neurotoxicity_risk,
        "phototherapyThreshold": phototherapy_threshold,
        "exchangeTransfusionThreshold": exchange_threshold,
        "treatmentDecision": treatment_decision,
        "phototherapyGuidance": phototherapy_guidance,
        "exchangeTransfusionGuidance": exchange_guidance,
        "feedingGuidance": feeding_guidance,
        "followUpBilirubin": follow_up_bilirubin,
        "urgentFlags": urgent_flags,
        "dischargeReadiness": discharge_readiness,
        "evidenceLevel": "A",
        "rationale": f"TSB {_fmt_num(tsb)} mg/dL at {_fmt_num(age_hours)} hours. GA {_fmt_num(gestational_age_weeks)} weeks. Neurotoxicity risk: {neurotoxicity_risk}. Risk factors: isoimmunization={_js_bool(has_isoimmunization)}, G6PD={_js_bool(has_g6pd_deficiency)}, sepsis={_js_bool(has_sepsis)}. Per AAP 2022 CPG.",
        "references": _REFERENCES_FULL,
    }


def _js_bool(x: bool) -> str:
    """JS boolean string interpolation: ``${true}`` -> "true"."""
    return "true" if x else "false"
