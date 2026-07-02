"""Pancreatic Mass Evaluation Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/pancreaticMassLogic.ts
(assessPancreaticMass).
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "pancreaticmass"


def _js_str(v) -> str:
    """JS template-literal coercion for the values used here (None -> 'undefined')."""
    if v is None:
        return "undefined"
    return str(v)


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    next_steps: list[str] = []

    mass_type = data.get("massType")
    cystic_type = data.get("cysticType")
    tissue_result = data.get("tissueResult")
    resectability_status = data.get("resectabilityStatus")
    ca199 = data.get("ca199")
    age_years = data.get("ageYears")

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if data.get("hasJaundice") and data.get("hasBileDuctDilation"):
        urgent_flags.append(
            "OBSTRUCTIVE JAUNDICE: biliary decompression may be required before "
            "resection — ERCP/EUS-BD vs percutaneous drainage. Urgent GI/surgery "
            "consultation."
        )
    if data.get("hasHighRiskStigmata"):
        urgent_flags.append(
            "HIGH-RISK IPMN STIGMATA (obstructive jaundice, enhancing mural nodule, "
            "MPD ≥10mm): surgical resection recommended without delay — high "
            "malignancy risk"
        )
    if data.get("hasDistantMetastases"):
        urgent_flags.append(
            "Distant metastases: pancreatic cancer is metastatic — systemic "
            "chemotherapy discussion (FOLFIRINOX or gemcitabine/nab-paclitaxel). "
            "Palliative care consultation."
        )
    if parse_float(ca199) > 1000:
        urgent_flags.append(
            f"CA 19-9 {_js_str(ca199)} U/mL (>1000): very high likelihood of "
            "pancreatic adenocarcinoma — expedite tissue acquisition and oncology "
            "referral"
        )
    if (
        data.get("hasNewOnsetDiabetes")
        and parse_float(age_years) > 50
        and mass_type == "solid_mass"
    ):
        urgent_flags.append(
            "New-onset diabetes in patient >50 with pancreatic mass: high "
            "suspicion for pancreatic adenocarcinoma — expedite workup"
        )

    # ─── Diagnostic Workup ────────────────────────────────────────────────────
    if not data.get("hasCTScan") and not data.get("hasMRIPancreas"):
        diagnostic_workup = (
            "IMAGING REQUIRED before EUS: "
            "1) CT pancreas protocol (triple-phase): preferred for resectability "
            "assessment and vascular involvement. "
            "2) MRI/MRCP: preferred for cystic lesions, biliary anatomy, and IPMN "
            "characterization. "
            "3) Both CT and MRI/MRCP are complementary — CT for vascular anatomy, "
            "MRI for soft tissue/cystic detail."
        )
        next_steps.append(
            "CT pancreas protocol (triple-phase) for resectability assessment"
        )
        next_steps.append("MRI/MRCP for cystic lesion characterization")
    elif (
        data.get("hasCTScan")
        and not data.get("hasMRIPancreas")
        and mass_type == "cystic_lesion"
    ):
        diagnostic_workup = (
            "MRI/MRCP recommended for cystic lesion characterization — superior to "
            "CT for duct communication, mural nodules, and IPMN features."
        )
        next_steps.append("MRI/MRCP for cystic lesion characterization")
    else:
        diagnostic_workup = (
            "Cross-sectional imaging performed. Proceed with EUS for tissue "
            "acquisition and detailed characterization."
        )

    # ─── EUS Strategy ─────────────────────────────────────────────────────────
    if mass_type == "solid_mass" or mass_type == "mixed_solid_cystic":
        eus_strategy = (
            "EUS-GUIDED TISSUE ACQUISITION for solid pancreatic mass (ASGE 2024): "
            "1) EUS provides real-time imaging + tissue acquisition in a single "
            "procedure. "
            "2) EUS-FNB (fine needle biopsy) is PREFERRED over FNA (ASGE 2024 "
            "Strong Recommendation): "
            "   - FNB needles (Franseen, Fork-tip, ProCore): provide core tissue "
            "for histology + IHC. "
            "   - Superior for: neuroendocrine tumors, autoimmune pancreatitis, "
            "lymphoma, metastases. "
            "   - Diagnostic yield: 85–95% with FNB vs 75–85% with FNA. "
            "3) Rapid on-site evaluation (ROSE) by cytopathologist: improves "
            "diagnostic yield when available. "
            "4) Approach: transgastric (body/tail), transduodenal (head/uncinate). "
            "5) Avoid transgastric approach if surgical resection planned "
            "(theoretical seeding risk — controversial)."
        )
    elif mass_type == "cystic_lesion":
        eus_strategy = (
            "EUS for cystic pancreatic lesion (ASGE 2024): "
            "1) EUS provides detailed morphology: mural nodules, septa, wall "
            "thickness, duct communication. "
            "2) EUS-FNA of cyst fluid: indicated for worrisome features or "
            "diagnostic uncertainty. "
            "   - Cyst fluid analysis: CEA >192 ng/mL = mucinous (MCN or IPMN). "
            "   - Amylase: high = pseudocyst or IPMN with duct communication. "
            "   - Cytology: low sensitivity but high specificity for malignancy. "
            "3) Molecular analysis (Cologuard-type cyst fluid DNA): KRAS/GNAS "
            "mutation + VHL mutation. "
            "   - KRAS/GNAS: mucinous cyst (IPMN/MCN). VHL: serous cystadenoma. "
            "4) EUS-guided through-the-needle biopsy (TTNB): emerging — forceps "
            "biopsy of cyst wall."
        )
    else:
        eus_strategy = (
            "EUS indicated for further characterization. Approach depends on final "
            "mass type and location."
        )

    # ─── Tissue Acquisition Approach ─────────────────────────────────────────
    if not data.get("hasTissueAcquired"):
        tissue_acquisition_approach = (
            "TISSUE ACQUISITION STRATEGY (ASGE 2024): "
            "1) EUS-FNB with 22G or 25G Franseen or Fork-tip needle (preferred "
            "over FNA for solid masses). "
            "2) Pass count: 2–3 passes with FNB (vs 5–7 with FNA) — fewer passes "
            "needed. "
            "3) Fanning technique: sample multiple areas of the mass to improve "
            "yield. "
            "4) ROSE (rapid on-site evaluation): use if available — reduces "
            "inadequate samples. "
            "5) For cystic lesions: aspirate cyst fluid completely, send for CEA, "
            "amylase, cytology, and molecular analysis. "
            "6) If EUS-FNB non-diagnostic: repeat EUS-FNB or consider CT-guided "
            "biopsy (if surgically unresectable)."
        )
        next_steps.append(
            "EUS-FNB (fine needle biopsy) with 22G Franseen or Fork-tip needle"
        )
        next_steps.append(
            "Send tissue for: H&E histology, IHC (CK7, CK20, synaptophysin, "
            "chromogranin, IgG4), molecular testing"
        )
    elif tissue_result == "non_diagnostic":
        tissue_acquisition_approach = (
            "Non-diagnostic prior tissue acquisition: "
            "1) Repeat EUS-FNB with different needle type (Franseen vs Fork-tip). "
            "2) Increase pass count or use ROSE. "
            "3) Consider CT-guided biopsy if EUS access suboptimal. "
            "4) If clinically high suspicion for malignancy: proceed to surgery "
            "without tissue confirmation (resectable disease)."
        )
        next_steps.append("Repeat EUS-FNB with alternative needle type")
        next_steps.append("Consider multidisciplinary tumor board review")
    else:
        tissue_acquisition_approach = (
            f"Tissue acquired — result: {_js_str(tissue_result)}. Proceed with "
            "management based on pathology."
        )

    # ─── Molecular Diagnostics ────────────────────────────────────────────────
    molecular_diagnostics = (
        "MOLECULAR DIAGNOSTICS (ASGE 2024 — integration with tissue acquisition): "
        "1) Solid mass: "
        "   - Next-generation sequencing (NGS): KRAS, TP53, SMAD4, CDKN2A — "
        "diagnostic + prognostic. "
        "   - BRCA1/2, PALB2 germline testing: 5–7% of pancreatic cancer — "
        "actionable (PARP inhibitors, platinum). "
        "   - MSI/MMR testing: rare in pancreatic cancer but actionable "
        "(pembrolizumab). "
        "   - NTRK fusion, RET fusion: rare but highly actionable (larotrectinib, "
        "selpercatinib). "
        "2) Cystic lesion fluid: "
        "   - KRAS/GNAS mutation: mucinous cyst (IPMN/MCN) — high specificity. "
        "   - VHL mutation: serous cystadenoma. "
        "   - TP53/SMAD4/CDKN2A: high-grade dysplasia or malignancy in mucinous "
        "cyst. "
        "   - CEA >192 ng/mL: mucinous cyst. "
        "3) Liquid biopsy (ctDNA): emerging — not yet standard of care for initial "
        "diagnosis."
    )

    # ─── Cystic Lesion Management ─────────────────────────────────────────────
    cystic_lesion_management = "Not applicable — solid mass."
    if mass_type == "cystic_lesion" or mass_type == "mixed_solid_cystic":
        if data.get("hasHighRiskStigmata"):
            cystic_lesion_management = (
                "HIGH-RISK IPMN STIGMATA: surgical resection recommended "
                "(AGA/ASGE 2024). "
                "High-risk features: obstructive jaundice, enhancing mural nodule, "
                "MPD ≥10mm. "
                "Pancreaticoduodenectomy (Whipple) for head/uncinate; distal "
                "pancreatectomy for body/tail. "
                "Surgical oncology referral urgently."
            )
            next_steps.append("Surgical oncology referral for pancreatic resection")
            next_steps.append("Preoperative staging CT + MRI/MRCP")
        elif data.get("hasWorrisomeFeatures"):
            cystic_lesion_management = (
                "WORRISOME IPMN FEATURES: EUS evaluation recommended (AGA 2024). "
                "Worrisome features: cyst >3cm, thickened/enhancing wall, MPD "
                "5–9mm, non-enhancing mural nodule, abrupt MPD change, "
                "lymphadenopathy. "
                "EUS-FNA with cyst fluid analysis (CEA, amylase, cytology, "
                "molecular). "
                "If EUS confirms high-risk features: surgical resection. "
                "If no high-risk features on EUS: close surveillance (MRI/MRCP "
                "every 3–6 months)."
            )
            next_steps.append(
                "EUS with cyst fluid aspiration and molecular analysis"
            )
            next_steps.append("Multidisciplinary pancreatic cyst program review")
        elif cystic_type == "mucinous_cystic_neoplasm":
            cystic_lesion_management = (
                "MUCINOUS CYSTIC NEOPLASM (MCN): surgical resection recommended for "
                "all fit patients (AGA 2024). "
                "MCN has malignant potential (10–15% harbor invasive carcinoma). "
                "Distal pancreatectomy (body/tail location). "
                "Surgical oncology referral."
            )
            next_steps.append("Surgical oncology referral for MCN resection")
        elif cystic_type == "serous_cystadenoma":
            cystic_lesion_management = (
                "SEROUS CYSTADENOMA: benign — surveillance only. "
                "Resection only if symptomatic or >4cm with rapid growth. "
                "MRI/MRCP every 2 years."
            )
        elif cystic_type == "pseudocyst":
            cystic_lesion_management = (
                "PANCREATIC PSEUDOCYST: drainage if symptomatic (pain, infection, "
                "compression). "
                "EUS-guided cyst drainage with LAMS (lumen-apposing metal stent) — "
                "preferred over surgical or percutaneous drainage. "
                "Asymptomatic pseudocysts: observe — many resolve spontaneously."
            )
        else:
            cystic_lesion_management = (
                "Cystic lesion of uncertain type: MRI/MRCP + EUS for "
                "characterization. "
                "Cyst fluid analysis (CEA, amylase, cytology, molecular) to "
                "determine mucinous vs non-mucinous. "
                "Surveillance interval based on size and features."
            )

    # ─── Resectability Assessment ─────────────────────────────────────────────
    resectability_assessment = ""
    if mass_type == "solid_mass" or tissue_result == "malignant":
        if resectability_status == "resectable":
            resectability_assessment = (
                "RESECTABLE: upfront surgery recommended (NCCN 2025). "
                "Pancreaticoduodenectomy (Whipple) for head/uncinate; distal "
                "pancreatectomy for body/tail. "
                "Adjuvant chemotherapy: modified FOLFIRINOX (mFOLFIRINOX) x6 months "
                "post-resection (PRODIGE 24 trial). "
                "High-volume pancreatic surgery center preferred (lower mortality)."
            )
            next_steps.append(
                "Surgical oncology referral at high-volume pancreatic center"
            )
            next_steps.append(
                "Preoperative staging: CT chest/abdomen/pelvis + CA 19-9"
            )
        elif resectability_status == "borderline_resectable":
            resectability_assessment = (
                "BORDERLINE RESECTABLE: neoadjuvant chemotherapy ± radiation "
                "recommended before surgery (NCCN 2025). "
                "FOLFIRINOX x4–6 months → restaging CT → surgery if downstaged. "
                "Multidisciplinary tumor board review required. "
                "Biliary stenting if jaundiced (SEMS preferred over plastic stent)."
            )
            next_steps.append("Multidisciplinary pancreatic tumor board")
            next_steps.append("Neoadjuvant FOLFIRINOX chemotherapy")
            next_steps.append("Biliary stenting if jaundiced")
        elif resectability_status == "locally_advanced":
            resectability_assessment = (
                "LOCALLY ADVANCED (unresectable): systemic chemotherapy ± "
                "radiation. "
                "FOLFIRINOX or gemcitabine/nab-paclitaxel. "
                "SBRT (stereotactic body radiation therapy) for local control. "
                "Biliary and/or gastric outlet decompression as needed."
            )
        elif resectability_status == "metastatic":
            resectability_assessment = (
                "METASTATIC: systemic chemotherapy. "
                "FOLFIRINOX (fit patients, ECOG 0–1) or gemcitabine/nab-paclitaxel. "
                "BRCA1/2 mutation: platinum-based chemotherapy + olaparib "
                "maintenance (POLO trial). "
                "MSI-H: pembrolizumab. "
                "Palliative care consultation."
            )
        else:
            resectability_assessment = (
                "Resectability not yet assessed — CT pancreas protocol required."
            )

    # ─── Multidisciplinary Plan ───────────────────────────────────────────────
    multidisciplinary_plan = (
        "MULTIDISCIPLINARY TEAM (MDT) APPROACH (NCCN 2025 — required for all "
        "pancreatic masses): "
        "1) Gastroenterology/interventional endoscopy: EUS, tissue acquisition, "
        "biliary drainage. "
        "2) Surgical oncology: resectability assessment, pancreatic surgery. "
        "3) Medical oncology: chemotherapy planning "
        "(neoadjuvant/adjuvant/palliative). "
        "4) Radiation oncology: SBRT for locally advanced disease. "
        "5) Radiology: imaging interpretation, CT/MRI staging. "
        "6) Pathology: tissue diagnosis, molecular profiling. "
        "7) Palliative care: symptom management, goals of care. "
        "8) Genetic counseling: germline testing (BRCA1/2, PALB2, ATM, Lynch "
        "syndrome)."
    )

    if len(next_steps) == 0:
        next_steps.append(
            "CT pancreas protocol (triple-phase) for resectability assessment"
        )
        next_steps.append(
            "MRI/MRCP for biliary anatomy and cystic lesion characterization"
        )
        next_steps.append("EUS-FNB for tissue acquisition")
        next_steps.append("CA 19-9, CEA, IgG4 serum markers")
        next_steps.append("Multidisciplinary pancreatic tumor board referral")
        next_steps.append(
            "Genetic counseling for germline testing (BRCA1/2, PALB2)"
        )

    mass_size_cm = data.get("massSizeCm")
    size_str = f"{_js_str(mass_size_cm)}cm" if truthy(parse_float(mass_size_cm)) else "not measured"
    rationale = (
        f"Mass type: {_js_str(mass_type).replace('_', ' ')}. "
        f"Location: {_js_str(data.get('massLocation'))}. "
        f"Size: {size_str}. "
        f"Cystic type: {_js_str(cystic_type).replace('_', ' ')}. "
        f"High-risk stigmata: {'Yes' if data.get('hasHighRiskStigmata') else 'No'}. "
        f"Tissue acquired: "
        f"{('Yes (' + _js_str(tissue_result) + ')') if data.get('hasTissueAcquired') else 'No'}. "
        f"Resectability: {_js_str(resectability_status).replace('_', ' ')}."
    )

    if data.get("hasHighRiskStigmata"):
        primary_recommendation = (
            "HIGH-RISK IPMN: surgical resection recommended — surgical oncology "
            "referral urgently."
        )
    elif data.get("hasDistantMetastases"):
        primary_recommendation = (
            "Metastatic pancreatic cancer: systemic chemotherapy (FOLFIRINOX or "
            "gemcitabine/nab-paclitaxel) + palliative care."
        )
    elif not data.get("hasTissueAcquired") and mass_type == "solid_mass":
        primary_recommendation = (
            "Solid pancreatic mass: EUS-FNB (fine needle biopsy) preferred over "
            "FNA for tissue acquisition (ASGE 2024)."
        )
    elif (
        mass_type == "cystic_lesion"
        and not data.get("hasHighRiskStigmata")
        and not data.get("hasWorrisomeFeatures")
    ):
        primary_recommendation = (
            "Cystic pancreatic lesion without high-risk features: MRI/MRCP "
            "surveillance per lesion type and size."
        )
    else:
        primary_recommendation = (
            "Pancreatic mass evaluation: multidisciplinary team approach with EUS, "
            "cross-sectional imaging, and tissue acquisition."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "diagnosticWorkup": diagnostic_workup,
        "eusStrategy": eus_strategy,
        "tissueAcquisitionApproach": tissue_acquisition_approach,
        "molecularDiagnostics": molecular_diagnostics,
        "cysticLesionManagement": cystic_lesion_management,
        "resectabilityAssessment": resectability_assessment,
        "multidisciplinaryPlan": multidisciplinary_plan,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "B",
        "rationale": rationale,
        "references": [
            {
                "citation": (
                    "ASGE Standards of Practice Committee. The role of endoscopy in "
                    "the evaluation and management of patients with solid and "
                    "cystic pancreatic lesions. Gastrointest Endosc. 2024."
                ),
                "url": (
                    "https://www.asge.org/home/guidelines-quality/"
                    "guidelines-standards/guidelines-standards-detail/"
                    "the-role-of-endoscopy-in-the-evaluation-and-management-of-"
                    "patients-with-solid-and-cystic-pancreatic-lesions"
                ),
            },
            {
                "citation": (
                    "Elta GH, et al. ACG Clinical Guideline: Diagnosis and "
                    "Management of Pancreatic Cysts. Am J Gastroenterol. "
                    "2018;113(4):464-479."
                ),
                "pmid": "29485131",
                "url": "https://pubmed.ncbi.nlm.nih.gov/29485131/",
            },
            {
                "citation": (
                    "Conroy T, et al. FOLFIRINOX or Gemcitabine as Adjuvant "
                    "Therapy for Pancreatic Cancer (PRODIGE 24). N Engl J Med. "
                    "2018;379(25):2395-2406."
                ),
                "pmid": "30575490",
                "url": "https://pubmed.ncbi.nlm.nih.gov/30575490/",
            },
            {
                "citation": (
                    "Gonda TA, et al. Molecular Classification and Biomarkers of "
                    "Clinical Outcome in Pancreatic Cysts. Gastroenterology. "
                    "2021;160(5):1718-1732."
                ),
                "pmid": "33454340",
                "url": "https://pubmed.ncbi.nlm.nih.gov/33454340/",
            },
        ],
    }
