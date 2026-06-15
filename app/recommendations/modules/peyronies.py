"""Peyronie's Disease Surgery appropriateness.

Ported 1:1 from old_static_code/client/src/pages/PeyroniesCompass.tsx (evaluate()).
The decision logic lives inline in the Compass page (there is no peyroniesLogic.ts).
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "peyronies"

_REFERENCES = [
    "Nehra A, et al. Peyronie's Disease: AUA Guideline. J Urol. 2015;194(3):745-753.",
    "Hatzimouratidis K, et al. EAU Guidelines on Penile Curvature. Eur Urol. 2012;62(3):543-552.",
    "Gelbard M, et al. Clinical efficacy, safety and tolerability of collagenase clostridium histolyticum for the treatment of Peyronie disease in 2 large double-blind, randomized, placebo controlled phase 3 studies. J Urol. 2013;190(1):199-207.",
    "Levine LA, Burnett AL. Standard operating procedures for Peyronie's disease. J Sex Med. 2013;10(1):230-244.",
    "Coyne KS, et al. The validation of the Peyronie's Disease Questionnaire. J Sex Med. 2015;12(4):1005-1016.",
]


def assess(data: dict) -> dict:
    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    disease_phase = data.get("diseasePhase")
    curvature_degrees = num(data.get("curvatureDegrees"), 0)
    er_dysfunction = data.get("erDysfunction")
    iief5_score = num(data.get("iief5Score"), 0)
    penis_shortening_cm = num(data.get("penisShorteningCm"), 0)
    stable_months = num(data.get("stableMonths"), 0)
    hinge = truthy(data.get("hinge"))
    hourglass = truthy(data.get("hourglass"))
    partner_consent = truthy(data.get("partnerConsent"))
    prior_collagenase = truthy(data.get("priorCollagenaseInjections"))

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "B"

    if disease_phase == "acute":
        recommendation = "not_indicated"
        procedure = "Non-surgical management — disease not yet stable"
        cor = "III"
        loe = "C"
        warnings.append(
            "Acute phase (active disease): surgery is contraindicated until curvature has been stable for ≥12 months."
        )
        rationale.append(
            "AUA Guideline: surgery should only be performed after disease stability for ≥12 months (no change in curvature, pain resolution)."
        )
    elif stable_months < 12:
        recommendation = "not_indicated"
        procedure = "Continue observation — await 12 months of stability"
        warnings.append(
            f"Disease stable for only {_fmt(stable_months)} months. AUA requires ≥12 months of stability before surgical correction."
        )
    elif curvature_degrees < 30:
        recommendation = "consider"
        procedure = "Observation or non-surgical management"
        cor = "IIb"
        loe = "C"
        rationale.append(
            "Curvature <30°: may not significantly impair sexual function. Shared decision-making with patient."
        )
    else:
        # Surgical candidate
        if er_dysfunction == "severe" or iief5_score < 11:
            recommendation = "indicated"
            procedure = "Penile Prosthesis Implantation (IPP) with intraoperative modeling"
            cor = "I"
            loe = "B"
            rationale.append(
                "Severe ED + Peyronie's disease: penile prosthesis is the preferred surgical option — treats both ED and curvature simultaneously."
            )
            rationale.append(
                "AUA Guideline: IPP with intraoperative modeling/plication is recommended for men with severe ED and Peyronie's disease."
            )
        elif curvature_degrees <= 60 and not hinge and not hourglass and penis_shortening_cm < 1:
            recommendation = "indicated"
            procedure = "Plication (Nesbit/modified Nesbit) — shortening procedure"
            cor = "I"
            loe = "B"
            rationale.append(
                "Curvature ≤60°, no hinge/hourglass, minimal shortening: plication (Nesbit) is appropriate — simpler, lower complication rate."
            )
            rationale.append(
                "Expected straightening: 85–95% success rate with plication for moderate curvature."
            )
        else:
            recommendation = "indicated"
            procedure = "Plaque Incision/Excision with Grafting (Lue procedure)"
            cor = "I"
            loe = "B"
            rationale.append(
                "Curvature >60°, hinge/hourglass deformity, or significant shortening: grafting procedure is preferred to restore length and correct complex deformity."
            )
            warnings.append(
                "Grafting procedures carry higher risk of post-operative ED (10–20%). Ensure adequate pre-operative erectile function."
            )

    if hinge:
        warnings.append(
            "Hinge deformity present: associated with higher risk of buckling and penetration difficulty; grafting procedure preferred."
        )
    if hourglass:
        warnings.append(
            "Hourglass deformity: complex correction required; refer to high-volume Peyronie's specialist."
        )
    if not partner_consent:
        warnings.append(
            "Partner has not been counseled: AUA recommends partner involvement in surgical decision-making."
        )
    if prior_collagenase and curvature_degrees > 30:
        rationale.append(
            "Prior collagenase injections with residual curvature >30°: surgery is appropriate next step per AUA guidelines."
        )

    return {
        "recommendation": recommendation,
        "procedure": procedure,
        "cor": cor,
        "loe": loe,
        "warnings": warnings,
        "rationale": rationale,
        "references": references,
    }


def _fmt(x: float) -> str:
    """Render a JS number like template-literal interpolation (no trailing .0)."""
    if x == int(x):
        return str(int(x))
    return str(x)
