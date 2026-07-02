"""Biliary Strictures & Malignancy Workup Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/biliaryStricturesLogic.ts
(assessBiliaryStricture).
"""

from __future__ import annotations

from app.recommendations.jslib import coalesce, parse_float, truthy

LOGIC_KEY = "biliarystrictures"

_REFERENCES = [
    {
        "citation": "ASGE Standards of Practice Committee. The role of endoscopy in the evaluation of suspected choledocholithiasis. Gastrointest Endosc. 2019;89(6):1075-1105.",
        "pmid": "30979521",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30979521/",
    },
    {
        "citation": "Morizane C, et al. Gemcitabine, Cisplatin, and Durvalumab for Biliary Tract Cancers (TOPAZ-1). N Engl J Med. 2022;386(19):1807-1818.",
        "pmid": "35551092",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35551092/",
    },
    {
        "citation": "Primrose JN, et al. Capecitabine Compared with Observation in Resected Biliary Tract Cancer (BILCAP). Lancet Oncol. 2019;20(5):663-673.",
        "pmid": "30922733",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30922733/",
    },
    {
        "citation": "Chapman MH, et al. British Society of Gastroenterology and UK-PSC Guidelines for the Diagnosis and Management of Primary Sclerosing Cholangitis. Gut. 2019;68(8):1356-1378.",
        "pmid": "31154395",
        "url": "https://pubmed.ncbi.nlm.nih.gov/31154395/",
    },
    {
        "citation": "Navaneethan U, et al. Cholangioscopy as an Adjunct to ERCP for Tissue Sampling in Indeterminate Biliary Strictures. Gastrointest Endosc. 2024.",
        "url": "https://www.asge.org",
    },
]


def _undef(data: dict, key: str):
    """Return the value or None to mirror JS ``!== undefined`` checks."""
    return data.get(key)


def assess(data: dict) -> dict:
    stricture_location = data.get("strictureLocation")
    suspected_etiology = data.get("suspectedEtiology")
    tissue_result = data.get("tissueAcquisitionResult")

    has_fever = truthy(data.get("hasFever"))
    has_chills = truthy(data.get("hasChills"))
    has_jaundice = truthy(data.get("hasJaundice"))
    has_stent_occlusion = truthy(data.get("hasStentOcclusion"))
    has_psc = truthy(data.get("hasPSC"))
    has_dominant_stricture = truthy(data.get("hasDominantStricture"))
    has_biliary_stenosis = truthy(data.get("hasBiliaryStenosis"))
    imaging_malignant = truthy(data.get("imagingFindingsMalignantFeatures"))
    has_ct = truthy(data.get("hasCTScan"))
    has_mrcp = truthy(data.get("hasMRCP"))
    has_weight_loss = truthy(data.get("hasWeightLoss"))
    has_lymphadenopathy = truthy(data.get("hasLymphadenopathy"))
    is_resectable = truthy(data.get("isResectable"))
    has_distant_mets = truthy(data.get("hasDistantMetastases"))

    bilirubin = _undef(data, "bilirubinMgDl")
    igg4 = _undef(data, "igg4")
    ca199 = _undef(data, "ca199")
    stricture_length = _undef(data, "strictureLengthCm")
    age_years = data.get("ageYears")
    prior_attempts = _undef(data, "numberOfPriorBiopsyAttempts")

    def _loc_starts_hilar() -> bool:
        return isinstance(stricture_location, str) and stricture_location.startswith("hilar")

    def _replace_underscores(s) -> str:
        return str(s).replace("_", " ") if s is not None else str(s)

    urgent_flags: list[str] = []
    next_steps: list[str] = []

    # ─── Urgent Flags ────────────────────────────────────────────────────────
    if has_fever and has_chills and has_jaundice:
        urgent_flags.append(
            "ACUTE CHOLANGITIS (Charcot's triad): urgent biliary decompression required — ERCP within 24–48h. IV antibiotics (piperacillin-tazobactam or ceftriaxone + metronidazole)."
        )
    if parse_float(bilirubin) > 15:
        urgent_flags.append(
            f"Severe jaundice (bilirubin {bilirubin} mg/dL): biliary drainage required before any systemic therapy — ERCP or EUS-BD"
        )
    if has_stent_occlusion:
        urgent_flags.append(
            "Biliary stent occlusion: ERCP for stent exchange — risk of cholangitis. Upgrade to SEMS if recurrent occlusion."
        )
    if has_psc and has_dominant_stricture:
        urgent_flags.append(
            "PSC with dominant stricture: high risk of cholangiocarcinoma — ERCP with brush cytology + FISH, cholangioscopy with biopsy, and CA 19-9 + IgG4 measurement"
        )
    if parse_float(igg4) > 135:
        urgent_flags.append(
            f"IgG4 {igg4} mg/dL (>135): IgG4-related sclerosing cholangitis — steroid trial (prednisone 40mg/day x4 weeks) before biliary stenting if clinically stable"
        )

    # ─── Malignancy Risk Assessment ──────────────────────────────────────────
    malignancy_risk_score = 0
    malignancy_features: list[str] = []

    if imaging_malignant:
        malignancy_risk_score += 2
        malignancy_features.append("Malignant imaging features (mass, vascular involvement)")
    if parse_float(ca199) > 100:
        malignancy_risk_score += 2
        malignancy_features.append(f"CA 19-9 {ca199} U/mL (>100)")
    if has_weight_loss:
        malignancy_risk_score += 1
        malignancy_features.append("Weight loss")
    if has_lymphadenopathy:
        malignancy_risk_score += 1
        malignancy_features.append("Lymphadenopathy")
    if has_psc:
        malignancy_risk_score += 1
        malignancy_features.append("PSC (13x higher CCA risk)")
    if parse_float(stricture_length) > 2:
        malignancy_risk_score += 1
        malignancy_features.append(f"Long stricture ({stricture_length}cm)")
    if parse_float(age_years) > 60:
        malignancy_risk_score += 1
        malignancy_features.append("Age >60")

    malignancy_risk = (
        "HIGH"
        if malignancy_risk_score >= 4
        else "INTERMEDIATE"
        if malignancy_risk_score >= 2
        else "LOW"
    )

    malignancy_risk_assessment = (
        f"MALIGNANCY RISK: {malignancy_risk} (score {malignancy_risk_score}/9). "
        + (
            f"Risk features: {', '.join(malignancy_features)}. "
            if len(malignancy_features) > 0
            else ""
        )
        + (
            "IgG4 elevated — consider IgG4-related cholangiopathy (benign) before assuming malignancy. "
            if (parse_float(igg4) > 135)
            else ""
        )
        + "Benign causes to exclude: PSC, IgG4-related cholangiopathy, post-surgical stricture, chronic pancreatitis, Mirizzi syndrome."
    )

    # ─── Diagnostic Workup ───────────────────────────────────────────────────
    if not has_ct and not has_mrcp:
        diagnostic_workup = (
            "IMAGING REQUIRED (ASGE 2024): "
            "1) MRCP (preferred for biliary strictures): best for stricture characterization, extent, and duct anatomy. "
            "2) CT abdomen/pelvis (triple-phase): vascular involvement, lymphadenopathy, metastases. "
            "3) Both CT and MRCP are complementary — perform both for suspected malignant stricture."
        )
        next_steps.append("MRCP for biliary stricture characterization")
        next_steps.append("CT abdomen/pelvis (triple-phase) for staging")
    elif not has_mrcp:
        diagnostic_workup = (
            "MRCP recommended — superior to CT for biliary anatomy and stricture characterization."
        )
        next_steps.append("MRCP for biliary anatomy")
    else:
        diagnostic_workup = (
            "Cross-sectional imaging performed. Proceed with tissue acquisition strategy."
        )

    # ─── Tissue Acquisition Strategy ─────────────────────────────────────────
    tissue_acquisition_strategy = ""
    if tissue_result == "not_performed" or tissue_result == "non_diagnostic":
        if stricture_location == "distal_cbd" or stricture_location == "hilar_bismuth_I":
            tissue_acquisition_strategy = (
                "TISSUE ACQUISITION for biliary stricture (ASGE 2024 — sequential strategy): "
                "1) ERCP BRUSH CYTOLOGY: sensitivity 30–40% (low), specificity 99%. "
                "   Inadequate alone — always combine with additional techniques. "
                "2) ERCP FORCEPS BIOPSY: sensitivity 40–50%. Combine with cytology. "
                "3) FLUORESCENCE IN SITU HYBRIDIZATION (FISH): improves sensitivity to 50–60% when added to cytology. "
                "4) CHOLANGIOSCOPY (SpyGlass DS) with TARGETED BIOPSY: "
                "   PREFERRED for indeterminate strictures (ASGE 2024 Strong Recommendation). "
                "   Direct visualization of stricture + targeted forceps biopsy. "
                "   Sensitivity: 60–80% for malignancy. Specificity: 95–98%. "
                "   SpyBite Max forceps: larger biopsy samples — improved yield. "
                "5) EUS-FNB: preferred for distal CBD strictures with periductal mass. "
                "   Avoid if resectable — theoretical seeding risk (controversial). "
                "6) NEXT-GENERATION SEQUENCING (NGS) on bile/brush cytology: emerging — improves diagnostic yield."
            )
            if parse_float(prior_attempts) >= 1:
                next_steps.append(
                    "Cholangioscopy (SpyGlass DS) with targeted biopsy — preferred for indeterminate stricture after failed ERCP cytology"
                )
            else:
                next_steps.append("ERCP with brush cytology + forceps biopsy + FISH")
                next_steps.append("Cholangioscopy if ERCP cytology non-diagnostic")
        elif _loc_starts_hilar():
            tissue_acquisition_strategy = (
                "TISSUE ACQUISITION for HILAR STRICTURE (ASGE 2024): "
                "1) ERCP brush cytology + FISH: first-line. "
                "2) Cholangioscopy (SpyGlass DS): preferred for hilar strictures — allows direct visualization of both hepatic ducts. "
                "   Bilateral cholangioscopy for Bismuth III–IV. "
                "3) EUS-FNB: limited access to hilar strictures — use for accessible periductal lymph nodes. "
                "4) Percutaneous transhepatic cholangioscopy (PTCS): if ERCP access not feasible."
            )
            next_steps.append("ERCP with brush cytology + FISH for hilar stricture")
            next_steps.append("Cholangioscopy if cytology non-diagnostic")
    elif tissue_result == "malignant" or tissue_result == "high_grade_dysplasia":
        tissue_acquisition_strategy = (
            f"Tissue acquisition confirmed: {_replace_underscores(tissue_result)}. "
            "Proceed with oncologic staging and multidisciplinary planning."
        )
    elif tissue_result == "benign":
        tissue_acquisition_strategy = (
            "Benign tissue result: does NOT exclude malignancy (false negative rate 20–40%). "
            "If clinical suspicion remains high: repeat tissue acquisition with cholangioscopy or EUS-FNB. "
            "Consider steroid trial if IgG4-related cholangiopathy suspected."
        )
    else:
        tissue_acquisition_strategy = (
            f"Tissue result: {_replace_underscores(tissue_result)}. "
            "Repeat tissue acquisition with cholangioscopy if clinically indicated."
        )

    # ─── Biliary Drainage Strategy ───────────────────────────────────────────
    biliar_drainage_strategy = ""
    if has_jaundice or has_biliary_stenosis:
        if stricture_location == "distal_cbd":
            biliar_drainage_strategy = (
                "BILIARY DRAINAGE for DISTAL CBD STRICTURE: "
                "1) ERCP with SEMS (self-expanding metal stent): preferred for malignant distal stricture. "
                "   Covered SEMS (CSEMS): longer patency (6–12 months), removable — preferred for benign or uncertain etiology. "
                "   Uncovered SEMS: permanent — use only for confirmed malignant, unresectable disease. "
                "2) Plastic stent: bridge to surgery or for benign strictures (exchange every 3 months). "
                "3) EUS-CDS (choledochoduodenostomy): if ERCP fails. "
                "4) Avoid pre-op stenting if surgery within 2 weeks (increases infection risk)."
            )
        elif _loc_starts_hilar():
            biliar_drainage_strategy = (
                "BILIARY DRAINAGE for HILAR STRICTURE (Klatskin tumor): "
                "1) Unilateral vs bilateral drainage: drain ≥50% of liver volume. "
                "   Bismuth I–II: unilateral drainage often sufficient. "
                "   Bismuth III–IV: bilateral drainage may be needed. "
                "2) ERCP: preferred approach for hilar drainage. "
                "3) PTBD: if ERCP not feasible (altered anatomy, failed ERCP). "
                "4) Stent type: uncovered SEMS for unresectable malignant hilar stricture (longer patency than plastic). "
                "5) Avoid draining undrained segments (cholangitis risk)."
            )
        elif stricture_location == "anastomotic":
            biliar_drainage_strategy = (
                "POST-TRANSPLANT ANASTOMOTIC STRICTURE: "
                "ERCP with balloon dilation + multiple plastic stents (side-by-side technique). "
                "Stent exchange every 3 months x12 months. "
                "Fully covered SEMS (FCSEMS): emerging alternative — better stricture resolution. "
                "Surgical revision if endoscopic therapy fails."
            )
    else:
        biliar_drainage_strategy = (
            "No biliary drainage required at this time. Monitor bilirubin and LFTs."
        )

    # ─── PSC Management ──────────────────────────────────────────────────────
    psc_management = "PSC not identified."
    if has_psc:
        psc_management = (
            "PRIMARY SCLEROSING CHOLANGITIS (PSC) MANAGEMENT (ACG 2023): "
            "1) DOMINANT STRICTURE: ERCP with dilation ± short-term plastic stent. "
            "   Cholangioscopy + biopsy + FISH to exclude cholangiocarcinoma. "
            "   CA 19-9 + IgG4 measurement. "
            "2) URSODEOXYCHOLIC ACID (UDCA): "
            "   Low-dose UDCA (13–15 mg/kg/day): not recommended by ACG 2023 (no survival benefit). "
            "   High-dose UDCA (28–30 mg/kg/day): HARMFUL — increased risk of colorectal cancer. "
            "   UDCA NOT recommended for PSC (ACG 2023). "
            "3) CRC SURVEILLANCE: annual colonoscopy with chromoendoscopy (PSC + IBD). "
            "4) CHOLANGIOCARCINOMA SURVEILLANCE: annual MRCP + CA 19-9. "
            "5) LIVER TRANSPLANT: only curative option for PSC. "
            "   MELD exception points for PSC-related complications. "
            "   5-year post-transplant survival: 85%."
        )
        if has_dominant_stricture:
            next_steps.append("ERCP with dilation of dominant stricture")
            next_steps.append("Cholangioscopy + biopsy + FISH to exclude cholangiocarcinoma")

    # ─── Resectability and Oncology ──────────────────────────────────────────
    resectability_and_oncology = ""
    if tissue_result == "malignant" or imaging_malignant:
        if is_resectable and not has_distant_mets:
            resectability_and_oncology = (
                "RESECTABLE BILIARY TRACT CANCER (NCCN 2025): "
                "Distal cholangiocarcinoma/ampullary: pancreaticoduodenectomy (Whipple). "
                "Hilar cholangiocarcinoma (Klatskin): extended hepatectomy ± caudate lobe resection. "
                "Intrahepatic CCA: hepatectomy with negative margins. "
                "Adjuvant chemotherapy: capecitabine x6 months (BILCAP trial — OS benefit). "
                "Surgical oncology referral at high-volume hepatobiliary center."
            )
            next_steps.append("Surgical oncology referral at high-volume hepatobiliary center")
            next_steps.append("Preoperative biliary drainage if bilirubin >10 mg/dL")
        elif has_distant_mets or not is_resectable:
            resectability_and_oncology = (
                "UNRESECTABLE/METASTATIC BILIARY TRACT CANCER (NCCN 2025): "
                "First-line: gemcitabine + cisplatin + durvalumab (TOPAZ-1 trial — OS benefit with PD-L1 inhibitor). "
                "Alternatively: gemcitabine + cisplatin (ABC-02 trial). "
                "FGFR2 fusion (intrahepatic CCA): pemigatinib or infigratinib (FGFR inhibitors). "
                "IDH1 mutation: ivosidenib (ClarIDHy trial). "
                "MSI-H/dMMR: pembrolizumab. "
                "BRAF V600E: dabrafenib + trametinib. "
                "Palliative biliary drainage (SEMS) for jaundice."
            )
            next_steps.append("Medical oncology referral")
            next_steps.append("NGS/molecular profiling of tumor tissue (FGFR2, IDH1, MSI, BRAF)")
            next_steps.append("Palliative SEMS for biliary decompression")
    else:
        resectability_and_oncology = (
            "Malignancy not confirmed. Complete diagnostic workup before oncologic planning."
        )

    # ─── Surveillance Plan ───────────────────────────────────────────────────
    if has_psc:
        surveillance_plan = (
            "PSC surveillance: annual MRCP + CA 19-9 + annual colonoscopy with chromoendoscopy (if IBD). "
            "Cholangioscopy if dominant stricture or rising CA 19-9."
        )
    elif tissue_result == "benign" and malignancy_risk != "LOW":
        surveillance_plan = (
            "Indeterminate stricture: repeat MRCP at 3 months. Repeat tissue acquisition if stricture persists or progresses."
        )
    else:
        surveillance_plan = (
            "Follow-up MRCP at 3–6 months for benign strictures. Annual MRCP for PSC."
        )

    if len(next_steps) == 0:
        next_steps.append("MRCP for biliary anatomy")
        next_steps.append("CA 19-9, CEA, IgG4 serum markers")
        next_steps.append("ERCP with brush cytology + FISH")
        next_steps.append("Cholangioscopy if ERCP cytology non-diagnostic")
        next_steps.append("Multidisciplinary hepatobiliary tumor board")

    rationale = (
        f"Location: {_replace_underscores(stricture_location)}. "
        f"Suspected etiology: {_replace_underscores(suspected_etiology)}. "
        f"Malignancy risk: {malignancy_risk}. "
        f"CA 19-9: {coalesce(ca199, 'not measured')}. "
        f"IgG4: {coalesce(igg4, 'not measured')}. "
        f"Tissue result: {_replace_underscores(tissue_result)}. "
        f"PSC: {'Yes' if has_psc else 'No'}."
    )

    if has_fever and has_chills and has_jaundice:
        primary_recommendation = (
            "ACUTE CHOLANGITIS: urgent ERCP for biliary decompression + IV antibiotics."
        )
    elif has_psc and has_dominant_stricture:
        primary_recommendation = (
            "PSC with dominant stricture: ERCP dilation + cholangioscopy to exclude cholangiocarcinoma."
        )
    elif parse_float(igg4) > 135:
        primary_recommendation = (
            "IgG4-related sclerosing cholangitis: steroid trial (prednisone 40mg/day) before biliary stenting."
        )
    elif malignancy_risk == "HIGH":
        primary_recommendation = (
            "High malignancy risk: cholangioscopy with targeted biopsy + ERCP biliary drainage + multidisciplinary tumor board."
        )
    else:
        primary_recommendation = (
            "Biliary stricture of uncertain etiology: MRCP + ERCP with brush cytology + FISH + cholangioscopy for tissue acquisition."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "malignancyRiskAssessment": malignancy_risk_assessment,
        "diagnosticWorkup": diagnostic_workup,
        "tissueAcquisitionStrategy": tissue_acquisition_strategy,
        "biliarDrainageStrategy": biliar_drainage_strategy,
        "pscManagement": psc_management,
        "resectabilityAndOncology": resectability_and_oncology,
        "surveillancePlan": surveillance_plan,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "B",
        "rationale": rationale,
        "references": _REFERENCES,
    }
