"""High Myopia / Pathologic Myopia clinical recommendation engine.

Ported 1:1 from old_static_code/client/src/lib/highMyopiaLogic.ts
(assessHighMyopia). Based on IMI 2023, AAO 2024 PPP, WSPOS 2023 consensus.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "highmyopia"

_REFERENCES = [
    {
        "citation": "Flitcroft DI, et al. IMI – Defining and Classifying Myopia: A Proposed Set of Standards for Clinical and Epidemiologic Studies. Invest Ophthalmol Vis Sci. 2019;60(3):M20-M30.",
        "pmid": "30817826",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30817826/",
    },
    {
        "citation": "Yam JC, et al. Low-Concentration Atropine for Myopia Progression (LAMP) Study. Ophthalmology. 2019;126(1):113-124.",
        "pmid": "30514630",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30514630/",
    },
    {
        "citation": "Bullimore MA, et al. The IMI 2023 Myopia Control Report. Invest Ophthalmol Vis Sci. 2023;64(6):3.",
        "pmid": "37195759",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37195759/",
    },
    {
        "citation": "Wolf S, et al. RADIANCE: A Randomized Controlled Study of Ranibizumab in Patients with Choroidal Neovascularization Secondary to Pathologic Myopia. Ophthalmology. 2014;121(3):682-692.",
        "pmid": "24289920",
        "url": "https://pubmed.ncbi.nlm.nih.gov/24289920/",
    },
    {
        "citation": "Ohno-Matsui K, et al. International Photographic Classification and Grading System for Myopic Maculopathy. Am J Ophthalmol. 2015;159(5):877-883.",
        "pmid": "25634530",
        "url": "https://pubmed.ncbi.nlm.nih.gov/25634530/",
    },
    {
        "citation": "AAO Preferred Practice Pattern: Myopia. American Academy of Ophthalmology. 2024.",
        "url": "https://www.aao.org/preferred-practice-pattern/myopia-ppp",
    },
]


def _se(data: dict) -> float:
    """sphericalEquivalent as a raw JS number (negative diopters)."""
    v = parse_float(data.get("sphericalEquivalent"))
    return 0.0 if v != v else v  # NaN -> 0 (NaN comparisons are false in JS)


def _age(data: dict) -> float:
    v = parse_float(data.get("age"))
    return 0.0 if v != v else v


def assess(data: dict) -> dict:
    age = _age(data)
    spherical_equivalent = _se(data)
    axial_length = data.get("axialLength")
    myopia_level = data.get("myopiaLevel")
    is_progressing = truthy(data.get("isProgressing"))
    myopia_control_history = data.get("myopiaControlHistory")
    pathologic_complication = data.get("pathologicComplication")
    has_myopic_cnv = truthy(data.get("hasMyopicCNV"))
    cnv_anti_vegf_history = data.get("cnvAntiVEGFHistory")
    is_surgical_candidate = truthy(data.get("isSurgicalCandidateForRefractiveSurgery"))
    has_keratoconus = truthy(data.get("hasKeratoconus"))

    urgent_flags: list[str] = []
    next_steps: list[str] = []

    # Urgent flags
    if pathologic_complication == "retinal_detachment":
        urgent_flags.append(
            "RETINAL DETACHMENT: urgent surgical referral required — same-day evaluation"
        )
    if has_myopic_cnv and cnv_anti_vegf_history == "none":
        urgent_flags.append(
            "MYOPIC CNV: urgent anti-VEGF injection required — ranibizumab or "
            "bevacizumab. Delay worsens prognosis."
        )
    if pathologic_complication == "myopic_traction_maculopathy":
        urgent_flags.append(
            "Myopic traction maculopathy: urgent vitreoretinal surgery referral — "
            "risk of foveal detachment"
        )
    if spherical_equivalent <= -10 and axial_length == "very_long":
        urgent_flags.append(
            "Extreme myopia (>-10D) with very long axial length: high risk for "
            "pathologic complications — annual dilated exam with OCT macula mandatory"
        )

    # Myopia control strategy (primarily for children/adolescents)
    myopia_control_strategy = ""
    if age <= 18 and is_progressing:
        if myopia_control_history == "none":
            myopia_control_strategy = (
                "Progressing myopia in child/adolescent: myopia control intervention "
                "recommended (IMI 2023 Level A). "
                "Options by efficacy: "
                "1) Low-dose atropine 0.01–0.05% nightly — ATOM2 trial: 50–60% reduction "
                "in progression. Minimal side effects. PREFERRED first-line. "
                "2) Orthokeratology (OK lenses) — 30–50% reduction in axial elongation. "
                "Good for moderate myopia. "
                "3) Multifocal soft contact lenses (MiSight 1-day) — FDA-approved; 59% "
                "reduction in progression (Cooper Vision BLINK study). "
                "4) Combination atropine + OK lenses — highest efficacy for rapidly "
                "progressing myopia. "
                "Outdoor time: ≥2 hours/day reduces myopia onset by 50% (meta-analysis). "
                "Counsel family."
            )
            next_steps.append("Cycloplegic refraction to confirm myopia level")
            next_steps.append(
                "Axial length measurement (IOLMaster or Lenstar) — baseline and every 6 months"
            )
            next_steps.append("Discuss myopia control options with family")
            next_steps.append("Prescribe low-dose atropine 0.01–0.05% nightly as first-line")
            next_steps.append("Encourage ≥2 hours outdoor time daily")
        elif myopia_control_history == "on_atropine_low":
            myopia_control_strategy = (
                "On low-dose atropine with continued progression: increase atropine "
                "concentration (0.025% or 0.05%) or add orthokeratology. "
                "Combination therapy (atropine + OK lenses) provides additive benefit "
                "for rapidly progressing cases."
            )
            next_steps.append("Increase atropine to 0.025% or 0.05%")
            next_steps.append("Consider adding orthokeratology")
            next_steps.append("Recheck axial length in 6 months")
        else:
            history_label = str(myopia_control_history).replace("_", " ")
            myopia_control_strategy = (
                f"On {history_label}: assess axial length progression rate. "
                "If >0.3mm/year axial elongation, consider escalating or combining therapies. "
                "Reassess every 6 months."
            )
    elif age > 18:
        myopia_control_strategy = (
            "Adult myopia: stabilization expected after age 18–25. Myopia control "
            "interventions not indicated for adults. "
            "Focus on correction (spectacles, contact lenses, refractive surgery) and "
            "monitoring for pathologic complications."
        )
    else:
        myopia_control_strategy = (
            "Stable myopia: continue current correction. Encourage outdoor time. "
            "Annual monitoring."
        )

    # Pathologic myopia management
    pathologic_management = ""
    if pathologic_complication == "myopic_cnv" or has_myopic_cnv:
        pathologic_management = (
            "Myopic CNV: anti-VEGF is first-line treatment (RADIANCE trial — ranibizumab "
            "superior to PDT). "
            "Ranibizumab 0.5mg IVT — RADIANCE trial: 1–3 injections typically sufficient "
            "(myopic CNV often self-limiting). "
            "Bevacizumab 1.25mg IVT — off-label, similar efficacy, lower cost. "
            "Aflibercept and faricimab — less data for myopic CNV specifically. "
            "Prognosis: generally better than nAMD — smaller lesions, younger patients, "
            "fewer injections needed."
        )
        next_steps.append("FA/OCTA to confirm CNV type and activity")
        next_steps.append("Anti-VEGF injection (ranibizumab or bevacizumab)")
        next_steps.append("OCT at 4–6 weeks post-injection to assess response")
    elif pathologic_complication == "myopic_traction_maculopathy":
        pathologic_management = (
            "Myopic traction maculopathy (MTM): observation for mild cases (no foveal "
            "detachment). "
            "Vitrectomy + ILM peeling for progressive MTM or foveal detachment. "
            "Macular buckle is an alternative for dome-shaped macula with MTM. "
            "OCT macula every 3–6 months to monitor for progression."
        )
        next_steps.append("OCT macula (assess foveal detachment, schisis, macular hole)")
        next_steps.append(
            "Vitreoretinal surgery referral if foveal detachment or progressive schisis"
        )
    elif pathologic_complication == "posterior_staphyloma":
        pathologic_management = (
            "Posterior staphyloma: no direct treatment available. Monitor for secondary "
            "complications (MTM, CNV, atrophy). "
            "Annual OCT macula + fundus photography. Avoid contact sports and activities "
            "with risk of ocular trauma."
        )
        next_steps.append("Annual OCT macula")
        next_steps.append("Fundus photography for documentation")
        next_steps.append("Low vision referral if BCVA <20/200")
    elif pathologic_complication == "lacquer_cracks":
        pathologic_management = (
            "Lacquer cracks: monitor for CNV development (occurs in ~5% of eyes with "
            "lacquer cracks). "
            "OCT + FA if any new visual symptoms. Annual dilated exam."
        )
        next_steps.append("Annual OCT macula")
        next_steps.append(
            "Educate patient to report any sudden vision change or metamorphopsia"
        )
    else:
        if myopia_level == "high" or myopia_level == "extreme":
            pathologic_management = (
                "High/extreme myopia without current pathologic complication: annual "
                "dilated fundus exam + OCT macula mandatory. "
                "Educate patient on warning symptoms (flashes, floaters, curtain/shadow "
                "in vision — retinal detachment). "
                "Avoid contact sports and high-impact activities."
            )
        else:
            pathologic_management = (
                "No pathologic complication identified. Standard monitoring."
            )

    # Surgical consideration
    surgical_consideration = ""
    if is_surgical_candidate and not has_keratoconus:
        if spherical_equivalent >= -10:
            surgical_consideration = (
                "Refractive surgery considerations: "
                "LASIK: suitable for myopia up to -8D to -10D (corneal thickness "
                "dependent). Requires corneal thickness >500μm and residual stromal bed "
                ">250μm. "
                "PRK/LASEK: preferred over LASIK for thin corneas or high-risk "
                "occupations (contact sports). "
                "ICL (implantable collamer lens): preferred for high myopia >-8D or thin "
                "corneas — STAAR Visian ICL. Excellent safety profile. "
                "SMILE (small incision lenticule extraction): up to -10D, no flap created."
            )
        else:
            surgical_consideration = (
                "Extreme myopia (>-10D): ICL (implantable collamer lens) is preferred over "
                "laser refractive surgery. "
                "LASIK/PRK may be combined with ICL for residual correction. "
                "Refractive lens exchange (RLE) for patients >40 years with presbyopia."
            )
    elif has_keratoconus:
        surgical_consideration = (
            "Keratoconus present: LASIK is CONTRAINDICATED. "
            "Rigid gas-permeable (RGP) or scleral contact lenses for correction. "
            "Corneal collagen cross-linking (CXL) to halt keratoconus progression. "
            "ICL may be considered in stable keratoconus with specialist evaluation."
        )
        urgent_flags.append(
            "Keratoconus: LASIK contraindicated — refer to cornea specialist"
        )
    else:
        surgical_consideration = (
            "Refractive surgery candidacy not assessed or not indicated at this time."
        )

    # Monitoring plan
    monitoring_plan = ""
    if myopia_level == "high" or myopia_level == "extreme":
        monitoring_plan = (
            "High/extreme myopia: annual dilated fundus exam + OCT macula + fundus "
            "photography. "
            "Axial length measurement every 6–12 months (children). "
            "Immediate evaluation for: flashes, floaters, new scotoma, curtain/shadow in "
            "vision (retinal detachment risk)."
        )
    elif age <= 18 and is_progressing:
        monitoring_plan = (
            "Progressing childhood myopia: axial length every 6 months. Cycloplegic "
            "refraction annually. "
            "Reassess myopia control therapy efficacy every 6–12 months."
        )
    else:
        monitoring_plan = (
            "Annual dilated fundus exam. Refraction as needed for symptom changes."
        )

    rationale = (
        f"Myopia level: {myopia_level} ({_fmt_num(spherical_equivalent)}D). "
        f"Age: {_fmt_num(age)}. "
        f"Axial length: {axial_length}. "
        f"Progressing: {'Yes' if is_progressing else 'No'}. "
        f"Pathologic complication: {str(pathologic_complication).replace('_', ' ')}. "
        f"Myopic CNV: {'Yes' if has_myopic_cnv else 'No'}."
    )

    if pathologic_complication != "none" or has_myopic_cnv:
        complication_label = (
            "myopic CNV"
            if has_myopic_cnv
            else str(pathologic_complication).replace("_", " ")
        )
        primary_recommendation = (
            f"Pathologic myopia with {complication_label}: urgent management indicated."
        )
    elif age <= 18 and is_progressing:
        primary_recommendation = (
            "Progressing childhood myopia: myopia control intervention recommended to "
            "reduce long-term pathologic risk."
        )
    else:
        level_str = str(myopia_level)
        capitalized = (level_str[:1].upper() + level_str[1:]) if level_str else level_str
        suffix = (
            "Annual OCT macula mandatory."
            if (myopia_level == "high" or myopia_level == "extreme")
            else ""
        )
        primary_recommendation = f"{capitalized} myopia: correction and monitoring. {suffix}"

    return {
        "primaryRecommendation": primary_recommendation,
        "myopiaControlStrategy": myopia_control_strategy,
        "pathologicManagement": pathologic_management,
        "surgicalConsideration": surgical_consideration,
        "monitoringPlan": monitoring_plan,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }


def _fmt_num(x: float) -> str:
    """Render a number the way JS string interpolation does (no trailing .0)."""
    if x == int(x):
        return str(int(x))
    return repr(x)
