"""Colorectal Cancer (CRC) Screening Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/crcScreeningLogic.ts
(assessCRCScreening).
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "crcscreening"

_REFERENCES = [
    {
        "citation": "US Preventive Services Task Force. Colorectal Cancer Screening: USPSTF Recommendation Statement. JAMA. 2021;325(19):1965-1977.",
        "pmid": "34003228",
        "url": "https://pubmed.ncbi.nlm.nih.gov/34003228/",
    },
    {
        "citation": "Shaukat A, et al. ACG Clinical Guidelines: Colorectal Cancer Screening 2021. Am J Gastroenterol. 2021;116(3):458-479.",
        "pmid": "33657038",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33657038/",
    },
    {
        "citation": "Gupta S, et al. Recommendations for Follow-Up After Colonoscopy and Polypectomy: A Consensus Update by the US Multi-Society Task Force on Colorectal Cancer. Gastroenterology. 2020;158(4):1131-1153.",
        "pmid": "32044092",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32044092/",
    },
    {
        "citation": "Wolf AMD, et al. Colorectal Cancer Screening for Average-Risk Adults: 2018 Guideline Update from the American Cancer Society. CA Cancer J Clin. 2018;68(4):250-281.",
        "pmid": "29846947",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29846947/",
    },
]


def _replace_underscores(s: str) -> str:
    """JS ``.replace(/_/g, ' ')`` — replace every underscore with a space."""
    return str(s).replace("_", " ")


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    next_steps: list[str] = []

    age_years = data.get("ageYears")
    risk_category = data.get("riskCategory")
    race_ethnicity = data.get("raceEthnicity")
    adenoma_history = data.get("adenomaHistory")
    family_history_age = data.get("familyHistoryAge")
    screening_test_preference = data.get("screeningTestPreference")

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if (
        truthy(data.get("hasRectalBleeding"))
        or truthy(data.get("hasIronDeficiencyAnemia"))
        or truthy(data.get("hasUnexplainedWeightLoss"))
        or truthy(data.get("hasChangeInBowelHabits"))
    ):
        urgent_flags.append(
            "ALARM SYMPTOMS present (rectal bleeding, iron deficiency anemia, weight loss, change in bowel habits): diagnostic colonoscopy required — do NOT use screening tests (FIT, Cologuard) in symptomatic patients"
        )
        next_steps.append(
            "Diagnostic colonoscopy (not screening) — expedited referral to gastroenterology"
        )
    if truthy(data.get("hasSuspectedLynchSyndrome")) and not truthy(
        data.get("hasConfirmedLynchSyndrome")
    ):
        urgent_flags.append(
            "Suspected Lynch syndrome: genetic counseling and germline testing required before finalizing surveillance plan"
        )
        next_steps.append("Genetic counseling referral for Lynch syndrome evaluation")
        next_steps.append("Tumor MMR/MSI testing if CRC present")
    if truthy(data.get("hasPSC")) and truthy(data.get("hasIBD")):
        urgent_flags.append(
            "PSC + IBD: annual colonoscopy with chromoendoscopy required from time of PSC diagnosis — very high CRC risk"
        )

    # ─── Screening Initiation Age ─────────────────────────────────────────────
    screening_initiation_age = ""
    recommended_screening_test = ""
    screening_interval = ""
    surveillance_protocol = ""
    alternative_tests = ""
    genetic_counseling_indication = "Not indicated based on current risk profile."

    if risk_category == "average_risk":
        if race_ethnicity == "black_african_american":
            screening_initiation_age = (
                "Age 40–45 (ACG 2021 recommends age 40 for Black/African American patients — higher incidence and earlier onset of CRC). "
                "USPSTF recommends age 45 for all average-risk adults."
            )
        else:
            screening_initiation_age = (
                "Age 45 (USPSTF 2021 Grade B recommendation — expanded from age 50). "
                "Continue screening through age 75 (Grade A). "
                "Age 76–85: individualized decision (Grade C). "
                "Age >85: screening not recommended."
            )

        if (
            screening_test_preference == "prefers_noninvasive"
            or screening_test_preference == "prefers_annual_stool_test"
        ):
            recommended_screening_test = (
                "Annual high-sensitivity guaiac FOBT (gFOBT) or fecal immunochemical test (FIT): "
                "FIT preferred over gFOBT — no dietary restrictions, higher sensitivity. "
                "FIT sensitivity: ~79% for CRC, ~24% for advanced adenoma. "
                "Any positive FIT requires diagnostic colonoscopy within 6–8 weeks."
            )
            screening_interval = "Annual FIT. Colonoscopy if FIT positive."
            alternative_tests = (
                "Cologuard (stool DNA + FIT): every 1–3 years. Higher sensitivity (92% CRC) but lower specificity (87%) than FIT. "
                "Higher cost; positive result requires diagnostic colonoscopy. "
                "CT colonography (virtual colonoscopy): every 5 years. Requires full bowel prep; incidental findings common."
            )
        elif screening_test_preference == "prefers_cologuard":
            recommended_screening_test = (
                "Cologuard (multitarget stool DNA + FIT): every 1–3 years. "
                "Sensitivity 92% for CRC, 42% for advanced adenoma. "
                "Specificity 87% — higher false positive rate than FIT. "
                "Any positive result requires diagnostic colonoscopy. "
                "Not recommended for high-risk patients (Lynch syndrome, FAP, IBD)."
            )
            screening_interval = "Every 1–3 years (Cologuard). Colonoscopy if positive."
            alternative_tests = "Annual FIT (lower cost, similar CRC detection). Colonoscopy every 10 years (most cost-effective long-term)."
        else:
            # Default: colonoscopy
            recommended_screening_test = (
                "Colonoscopy every 10 years (preferred — single test, diagnostic + therapeutic). "
                "Highest sensitivity for CRC and adenomas. "
                "Allows polypectomy at time of screening. "
                "Requires bowel preparation and sedation. "
                "Perforation risk: ~1 in 1,000."
            )
            screening_interval = "Every 10 years (colonoscopy). Earlier if polyps found."
            alternative_tests = (
                "Annual FIT (if colonoscopy declined). "
                "Cologuard every 1–3 years (if colonoscopy declined). "
                "Flexible sigmoidoscopy every 5 years + annual FIT (alternative to colonoscopy)."
            )
    elif risk_category == "increased_risk_family_history":
        if parse_float(family_history_age) < 60:
            screening_initiation_age = (
                "Age 40 OR 10 years before the youngest affected relative's diagnosis (whichever is earlier). "
                "First-degree relative with CRC diagnosed <60 years."
            )
            screening_interval = "Every 5 years (colonoscopy)."
        else:
            screening_initiation_age = (
                "Age 40 (ACG 2021) — first-degree relative with CRC at any age. "
                "USPSTF: age 45 for average risk; ACG recommends earlier for family history."
            )
            screening_interval = "Every 5 years (colonoscopy)."
        recommended_screening_test = (
            "Colonoscopy every 5 years (ACG 2021 recommendation for first-degree family history). "
            "Noninvasive tests (FIT, Cologuard) are not recommended as primary screening for high-risk individuals."
        )
        alternative_tests = "Colonoscopy is preferred — noninvasive tests have lower sensitivity in high-risk populations."
    elif risk_category == "high_risk_lynch":
        genetic_counseling_indication = (
            "Lynch syndrome confirmed or suspected: genetic counseling and germline MMR gene testing required. "
            "Cascade testing of first-degree relatives recommended."
        )
        screening_initiation_age = "Age 20–25 (or 2–5 years before earliest family member diagnosis)."
        recommended_screening_test = (
            "Colonoscopy every 1–2 years (Lynch syndrome surveillance). "
            "MLH1/MSH2: every 1 year. MSH6/PMS2: every 1–2 years. "
            "Annual gynecologic exam + endometrial sampling for women (Lynch-associated endometrial cancer risk)."
        )
        screening_interval = "Every 1–2 years (gene-dependent)."
        surveillance_protocol = (
            "Lynch syndrome surveillance: "
            "Colonoscopy every 1–2 years (MLH1/MSH2: annual). "
            "Upper GI endoscopy every 2–3 years (gastric/duodenal cancer risk). "
            "Annual urinalysis (urothelial cancer). "
            "Women: annual gynecologic exam + endometrial biopsy from age 30–35."
        )
        urgent_flags.append(
            "Lynch syndrome: multidisciplinary hereditary cancer program referral recommended"
        )
    elif risk_category == "high_risk_fap":
        genetic_counseling_indication = "FAP confirmed: APC gene testing and genetic counseling for all first-degree relatives."
        screening_initiation_age = "Age 10–12 (classic FAP) or age 18–20 (attenuated FAP)."
        recommended_screening_test = (
            "Annual flexible sigmoidoscopy or colonoscopy starting age 10–12 (classic FAP). "
            "Once polyps detected: colectomy planning with colorectal surgery. "
            "Attenuated FAP: colonoscopy every 1–2 years starting age 18–20."
        )
        screening_interval = "Annual (classic FAP). Every 1–2 years (attenuated FAP)."
        surveillance_protocol = (
            "FAP surveillance: "
            "Annual colonoscopy until colectomy. "
            "Upper GI endoscopy every 1–3 years (duodenal polyposis — Spigelman staging). "
            "Thyroid ultrasound annually (papillary thyroid cancer risk). "
            "Desmoid tumor surveillance if prior abdominal surgery."
        )
        urgent_flags.append("FAP: colorectal surgery consultation for colectomy planning")
    elif risk_category == "high_risk_ibd":
        screening_initiation_age = (
            "8 years after onset of extensive colitis (UC or Crohn's colitis involving ≥1/3 of colon). "
            "Immediate surveillance if PSC diagnosed at any time."
        )
        recommended_screening_test = (
            "Colonoscopy with chromoendoscopy or high-definition white light endoscopy. "
            "Targeted biopsies of visible lesions + random biopsies every 10cm (4 quadrant). "
            "Chromoendoscopy (indigo carmine or methylene blue) improves dysplasia detection."
        )
        screening_interval = (
            "Annual colonoscopy (PSC + IBD — very high risk)"
            if truthy(data.get("hasPSC"))
            else "Every 1–3 years depending on risk factors (extent, duration, PSC, prior dysplasia)."
        )
        surveillance_protocol = (
            "IBD CRC surveillance (ACG 2021): "
            "Low risk (remission, no PSC, no prior dysplasia): every 3 years. "
            "Intermediate risk (active inflammation, family history): every 1–2 years. "
            "High risk (PSC, prior dysplasia, stricture): annual. "
            "Dysplasia found: multidisciplinary discussion — endoscopic resection vs colectomy."
        )
    elif risk_category == "high_risk_prior_adenoma":
        screening_initiation_age = "Surveillance colonoscopy — not initial screening."
        if adenoma_history == "low_risk_1_2_tubular":
            recommended_screening_test = "Colonoscopy in 7–10 years (low-risk adenoma: 1–2 tubular adenomas <10mm, no HGD)."
            screening_interval = "7–10 years."
        elif adenoma_history == "high_risk_3_4_adenomas":
            recommended_screening_test = "Colonoscopy in 3 years (3–4 adenomas)."
            screening_interval = "3 years."
        elif adenoma_history == "high_risk_5_plus":
            recommended_screening_test = "Colonoscopy in 1 year (≥5 adenomas — high-risk)."
            screening_interval = "1 year."
        elif adenoma_history == "advanced_adenoma":
            recommended_screening_test = "Colonoscopy in 3 years (advanced adenoma: ≥10mm, villous features, or HGD)."
            screening_interval = "3 years."
        elif (
            adenoma_history == "serrated_polyp_10mm_plus"
            or adenoma_history == "sessile_serrated_lesion"
        ):
            recommended_screening_test = "Colonoscopy in 3 years (sessile serrated lesion ≥10mm or with dysplasia)."
            screening_interval = "3 years."
        surveillance_protocol = (
            "Post-polypectomy surveillance (MSTF 2022): "
            "1–2 tubular adenomas <10mm: 7–10 years. "
            "3–4 adenomas or advanced adenoma (≥10mm, villous, HGD): 3 years. "
            "≥5 adenomas: 1 year. "
            "Sessile serrated lesion ≥10mm or with dysplasia: 3 years. "
            "Piecemeal resection of large polyp: 3–6 months."
        )
        alternative_tests = "Colonoscopy is required for surveillance — noninvasive tests not appropriate."
    elif risk_category == "high_risk_prior_crc":
        screening_initiation_age = "Post-CRC surveillance — not initial screening."
        recommended_screening_test = (
            "Colonoscopy 1 year after curative resection (or 3–6 months if incomplete preoperative colonoscopy). "
            "If normal: repeat at 3 years, then every 5 years."
        )
        screening_interval = "1 year post-resection, then 3 years, then every 5 years."
        surveillance_protocol = (
            "Post-CRC surveillance (ACG 2021): "
            "Colonoscopy at 1 year post-resection. "
            "CEA every 3 months x2 years, then every 6 months x3 years (stage II–III). "
            "CT chest/abdomen/pelvis every 6–12 months x5 years (stage II–III). "
            "Annual colonoscopy if Lynch syndrome."
        )

    if len(next_steps) == 0:
        if (
            parse_float(age_years) >= 45
            and risk_category == "average_risk"
            and not truthy(data.get("lastColonoscopyYear"))
        ):
            next_steps.append("Initiate CRC screening — age 45+ and no prior screening")
            next_steps.append(
                "Discuss test options: colonoscopy (every 10y), annual FIT, or Cologuard (every 1–3y)"
            )
            next_steps.append("Order FIT if patient prefers noninvasive test")
        elif (
            parse_float(age_years) < 45
            and risk_category == "average_risk"
        ):
            next_steps.append(
                "No screening indicated at this time — begin at age 45 (USPSTF) or age 40 (ACG for Black patients)"
            )
        else:
            next_steps.append("Schedule colonoscopy per surveillance interval")
            next_steps.append("Document prior colonoscopy findings in chart")

    rationale = (
        f"Age: {age_years}. "
        f"Risk category: {_replace_underscores(risk_category)}. "
        f"Race/ethnicity: {_replace_underscores(race_ethnicity)}. "
        f"Prior adenoma: {_replace_underscores(adenoma_history)}. "
        f"IBD: {'Yes' if truthy(data.get('hasIBD')) else 'No'}. "
        f"Lynch: {'Confirmed' if truthy(data.get('hasConfirmedLynchSyndrome')) else ('Suspected' if truthy(data.get('hasSuspectedLynchSyndrome')) else 'No')}."
    )

    if len(urgent_flags) > 0 and truthy(data.get("hasRectalBleeding")):
        primary_recommendation = (
            "ALARM SYMPTOMS: diagnostic colonoscopy required — do not use screening tests in symptomatic patients."
        )
    elif risk_category == "high_risk_lynch":
        primary_recommendation = (
            "Lynch syndrome: annual colonoscopy starting age 20–25 + gynecologic surveillance for women."
        )
    elif risk_category == "high_risk_fap":
        primary_recommendation = (
            "FAP: annual flexible sigmoidoscopy/colonoscopy starting age 10–12 + colorectal surgery consultation."
        )
    elif risk_category == "high_risk_ibd":
        primary_recommendation = (
            "IBD: colonoscopy with chromoendoscopy every 1–3 years starting 8 years after extensive colitis onset."
        )
    elif risk_category == "average_risk" and parse_float(age_years) >= 45:
        primary_recommendation = (
            "Average-risk CRC screening: colonoscopy every 10 years (preferred) or annual FIT starting age 45."
        )
    elif risk_category == "average_risk" and parse_float(age_years) < 45:
        primary_recommendation = (
            "Below screening age — begin CRC screening at age 45 (USPSTF) or age 40 (ACG for Black patients)."
        )
    else:
        primary_recommendation = (
            f"{_replace_underscores(risk_category)} — individualized surveillance per guideline."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "screeningInitiationAge": screening_initiation_age,
        "recommendedScreeningTest": recommended_screening_test,
        "screeningInterval": screening_interval,
        "surveillanceProtocol": surveillance_protocol,
        "alternativeTests": alternative_tests,
        "urgentFlags": urgent_flags,
        "geneticCounselingIndication": genetic_counseling_indication,
        "nextSteps": next_steps,
        "evidenceLevel": "A",
        "rationale": rationale,
        "references": _REFERENCES,
    }
