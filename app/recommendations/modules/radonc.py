"""Radiation Oncology Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/radOncLogic.ts (evaluateRadOnc).

Covers 13 disease site categories (CNS, Head & Neck, NSCLC, SCLC, Prostate,
Esophageal, Gastric, Rectal, Lymphoma, HCC, Breast, Skin, Palliative/
Oligometastatic) with NCCN/ASTRO guideline-based RT recommendations.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "radonc"


def _rec(
    indication: str,
    technique: list[str],
    dose_regimen: str,
    fractionation: str,
    target_volumes: str,
    sequencing: str,
    concurrent_systemic: str,
    cor: str,
    loe: str,
    guideline_source: str,
    notes: str,
) -> dict:
    return {
        "indication": indication,
        "technique": technique,
        "doseRegimen": dose_regimen,
        "fractionation": fractionation,
        "targetVolumes": target_volumes,
        "sequencing": sequencing,
        "concurrentSystemic": concurrent_systemic,
        "cor": cor,
        "loe": loe,
        "guidelineSource": guideline_source,
        "notes": notes,
    }


def _result(
    disease_category: str,
    primary: dict,
    alternatives: list[dict],
    rt_role: str,
    flags: list[str],
    safety: list[str],
    mdt: list[str],
    refs: list[dict],
    nccn_category: str,
    astro_guideline: str,
) -> dict:
    return {
        "diseaseCategory": disease_category,
        "primaryRecommendation": primary,
        "alternativeRecommendations": alternatives,
        "rtRole": rt_role,
        "urgentFlags": flags,
        "safetyConsiderations": safety,
        "multidisciplinaryConsult": mdt,
        "references": refs,
        "nccnCategory": nccn_category,
        "astroGuideline": astro_guideline,
    }


# ─── CNS ────────────────────────────────────────────────────────────────────


def _evaluate_cns(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "Obtain MRI brain with and without contrast before planning",
        "Neurocognitive baseline recommended before WBRT",
    ]
    mdt = ["Neuro-oncology", "Neurosurgery", "Neuropathology"]
    refs = [
        {"citation": "NCCN CNS Tumors Guidelines v2.2025", "year": 2025, "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1425"},
        {"citation": "Stupp R et al. NEJM 2005 (TMZ+RT for GBM)", "year": 2005},
        {"citation": "Perry JR et al. NEJM 2017 (Hypofractionated RT for elderly GBM)", "year": 2017},
        {"citation": "ASTRO SRS/SBRT Safety White Paper 2023", "year": 2023},
    ]

    cns_histology = data.get("cnsHistology")
    kps = num(data.get("kpsScore"), 0)
    mgmt = truthy(data.get("mgmtMethylated"))
    idh1 = truthy(data.get("idh1Mutated"))

    if cns_histology == "GBM":
        if kps >= 60:
            primary = _rec(
                "Newly diagnosed GBM, KPS ≥60",
                ["IMRT", "VMAT"],
                "60 Gy in 30 fractions (standard) or 40 Gy in 15 fractions (elderly/KPS 60–70)",
                "Standard: 2 Gy/fx × 30 fx. Hypofractionated: 2.67 Gy/fx × 15 fx for age ≥65 or KPS 60–70",
                "GTV = enhancing tumor + surgical cavity; CTV = GTV + 2 cm; PTV = CTV + 3–5 mm",
                "Concurrent with temozolomide (75 mg/m²/day), then adjuvant TMZ × 6 cycles",
                "Temozolomide concurrent and adjuvant (Stupp protocol). Consider TTFields post-RT.",
                "Category 1", "A",
                "NCCN CNS v2.2025 / Stupp NEJM 2005",
                "MGMT methylated: TMZ benefit confirmed (Category 1). Consider TMZ alone if RT not feasible." if mgmt else "MGMT unmethylated: TMZ benefit less clear but standard of care maintained.",
            )
            if mgmt:
                flags.append("MGMT methylated — TMZ benefit confirmed (Category 1)")
            return _result("cns", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO SRS/SBRT Safety White Paper 2023")
        else:
            primary = _rec(
                "Newly diagnosed GBM, KPS <60 or elderly",
                ["IMRT", "VMAT"],
                "34 Gy in 10 fractions or 25 Gy in 5 fractions (palliative intent)",
                "3.4 Gy/fx × 10 fx or 5 Gy/fx × 5 fx",
                "GTV = enhancing tumor + cavity; CTV = GTV + 1.5 cm; PTV = CTV + 3–5 mm",
                "TMZ alone or RT alone depending on MGMT status and performance status",
                "TMZ alone if MGMT methylated and KPS <60. RT alone if MGMT unmethylated.",
                "Category 2A", "B",
                "NCCN CNS v2.2025 / Perry NEJM 2017",
                "For KPS <60: RT alone or TMZ alone preferred over combined approach.",
            )
            flags.append("KPS <60 — consider hypofractionated or palliative RT regimen")
            return _result("cns", primary, [], "Definitive", flags, safety, mdt, refs, "Category 2A", "ASTRO SRS/SBRT Safety White Paper 2023")

    if cns_histology == "Brain_Mets":
        count = num(data.get("brainMetsCount"), 0)
        max_d = num(data.get("brainMetsMaxDiameter"), 0)
        if count <= 4 and max_d <= 3:
            primary = _rec(
                "Brain metastases — limited (1–4 lesions, ≤3 cm each)",
                ["SRS"],
                "Single fraction: 15–24 Gy (size-dependent). 3-fraction: 27 Gy/3 fx for 2–3 cm lesions.",
                "Single fraction for ≤2 cm; 3–5 fraction FSRT for 2–4 cm",
                "GTV = contrast-enhancing lesion(s); PTV = GTV + 1–2 mm",
                "SRS preferred over WBRT for limited mets to preserve neurocognition",
                "Continue systemic therapy per primary tumor guidelines. Immunotherapy may be given concurrently with SRS.",
                "Category 1", "A",
                "NCCN CNS v2.2025 / ASTRO SRS Safety White Paper 2023",
                "WBRT with hippocampal avoidance + memantine if WBRT required. SRS preferred for ≤4 lesions.",
            )
            alt = _rec(
                "WBRT with hippocampal avoidance (if SRS not feasible)",
                ["WBRT"],
                "30 Gy in 10 fractions with hippocampal avoidance",
                "3 Gy/fx × 10 fx; hippocampal avoidance + memantine",
                "Whole brain with hippocampal avoidance (RTOG 0933 technique)",
                "Add memantine 20 mg/day during and after WBRT",
                "Memantine (Category 1 for neurocognitive protection)",
                "Category 1", "A",
                "NCCN CNS v2.2025 / RTOG 0933",
                "Hippocampal avoidance WBRT + memantine reduces neurocognitive decline vs standard WBRT.",
            )
            return _result("cns", primary, [alt], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO SRS/SBRT Safety White Paper 2023")
        else:
            primary = _rec(
                "Brain metastases — multiple (>4 lesions or >3 cm)",
                ["WBRT", "SRS"],
                "WBRT: 30 Gy/10 fx with hippocampal avoidance. SRS to dominant/symptomatic lesions.",
                "3 Gy/fx × 10 fx (WBRT) ± SRS boost to large lesions",
                "Whole brain ± SRS boost to lesions >1.5 cm",
                "Systemic therapy per primary tumor guidelines",
                "Memantine concurrent with WBRT (Category 1)",
                "Category 1", "A",
                "NCCN CNS v2.2025",
                "Consider SRS alone for 5–10 small lesions at experienced centers (JLGK0901 data).",
            )
            return _result("cns", primary, [], "Palliative", flags, safety, mdt, refs, "Category 1", "ASTRO SRS/SBRT Safety White Paper 2023")

    if cns_histology == "LGG":
        primary = _rec(
            "Low-grade glioma (IDH-mutant, Grade 2)",
            ["IMRT", "VMAT"],
            "54 Gy in 30 fractions (standard) or 45 Gy in 25 fractions (low-dose arm)",
            "1.8 Gy/fx × 30 fx",
            "GTV = T2/FLAIR abnormality; CTV = GTV + 1–2 cm; PTV = CTV + 3–5 mm",
            "RT after surgery (resection or biopsy). PCV chemotherapy or temozolomide per risk stratification.",
            "PCV (procarbazine, CCNU, vincristine) × 6 cycles after RT for high-risk LGG (RTOG 9802). Temozolomide alternative.",
            "Category 1", "A",
            "NCCN CNS v2.2025 / RTOG 9802",
            "IDH1 mutated — favorable prognosis. Consider observation for low-risk (age <40, gross total resection)." if idh1 else "IDH wild-type LGG — behaves more aggressively; treat as high-grade.",
        )
        if not idh1:
            flags.append("IDH wild-type LGG — consider treating as high-grade glioma")
        return _result("cns", primary, [], "Adjuvant", flags, safety, mdt, refs, "Category 1", "")

    # Default CNS
    primary = _rec("CNS tumor — specify histology for detailed recommendation", ["IMRT"], "Per NCCN CNS guidelines", "Per histology", "Per histology", "Per MDT", "Per histology", "Category 2A", "B", "NCCN CNS v2.2025", "Please specify CNS histology for detailed recommendation.")
    return _result("cns", primary, [], "Insufficient data", flags, safety, mdt, refs, "Category 2A", "")


# ─── Head & Neck ────────────────────────────────────────────────────────────


def _evaluate_head_neck(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "Dental evaluation and extraction before RT",
        "Speech/swallowing baseline assessment",
        "Salivary gland sparing with IMRT mandatory",
        "Thyroid function monitoring post-RT",
    ]
    mdt = ["Head & Neck Surgery", "Medical Oncology", "Speech Pathology", "Nutrition/Dietetics", "Dental Oncology"]
    refs = [
        {"citation": "NCCN Head and Neck Cancers v2.2025", "year": 2025, "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1437"},
        {"citation": "Ang KK et al. NEJM 2010 (HPV and oropharyngeal cancer)", "year": 2010},
        {"citation": "ASTRO Head and Neck Cancer Guideline 2024", "year": 2024},
        {"citation": "Bonner JA et al. NEJM 2006 (Cetuximab + RT)", "year": 2006},
    ]

    is_m1 = data.get("hnM") == "M1"
    if is_m1:
        flags.append("M1 disease — RT is palliative intent")
        primary = _rec("Metastatic H&N — palliative RT", ["IMRT", "SBRT"], "20–30 Gy in 5–10 fractions (palliative)", "Hypofractionated palliative", "Primary + involved nodes", "Concurrent systemic per MDT", "Pembrolizumab ± chemotherapy (KEYNOTE-048)", "Category 2A", "B", "NCCN H&N v2.2025", "Palliative RT for symptom control. Systemic therapy is primary treatment.")
        return _result("head_neck", primary, [], "Palliative", flags, safety, mdt, refs, "Category 2A", "")

    if data.get("hnSite") == "Oropharynx":
        if data.get("hpvStatus") == "Positive":
            primary = _rec(
                "HPV+ Oropharyngeal SCC — definitive CRT",
                ["IMRT", "VMAT"],
                "70 Gy/35 fx to gross disease; 63 Gy/35 fx to high-risk CTV; 56 Gy/35 fx to elective nodes (SIB technique)",
                "2 Gy/fx × 35 fx (SIB: 2.0/1.8/1.6 Gy/fx)",
                "GTV-P (primary), GTV-N (nodes), CTV-HR, CTV-IR, CTV-LR per RTOG contouring atlas",
                "Concurrent cisplatin 100 mg/m² q3w × 3 cycles or weekly 40 mg/m²",
                "Cisplatin concurrent (Category 1). Cetuximab alternative if cisplatin ineligible.",
                "Category 1", "A",
                "NCCN H&N v2.2025 / ASTRO H&N 2024",
                "HPV+ p16+ oropharyngeal SCC: consider de-escalation trials (ECOG-ACRIN 3311, NRG-HN002) for low-risk patients.",
            )
            flags.append("HPV+ oropharyngeal SCC — de-escalation trial eligibility should be assessed")
            return _result("head_neck", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO Head and Neck Cancer Guideline 2024")

    # Post-op H&N
    if data.get("postOpMargins") == "Positive" or truthy(data.get("ece")):
        primary = _rec(
            "Post-op H&N — high-risk features (positive margins or ECE)",
            ["IMRT", "VMAT"],
            "66 Gy/33 fx to high-risk CTV; 60 Gy/30 fx to intermediate-risk; 54 Gy/27 fx to elective",
            "2 Gy/fx × 33 fx (SIB technique)",
            "High-risk CTV (surgical bed + positive margin/ECE region), intermediate CTV, elective nodal CTV",
            "Concurrent cisplatin 100 mg/m² q3w × 2–3 cycles (RTOG 9501/EORTC 22931)",
            "Cisplatin concurrent (Category 1 for ECE or positive margins)",
            "Category 1", "A",
            "NCCN H&N v2.2025 / RTOG 9501 / EORTC 22931",
            "ECE and/or positive margins are the two indications for concurrent cisplatin post-op (Category 1).",
        )
        if truthy(data.get("ece")):
            flags.append("Extracapsular extension — concurrent cisplatin mandatory (Category 1)")
        if data.get("postOpMargins") == "Positive":
            flags.append("Positive surgical margins — concurrent cisplatin mandatory (Category 1)")
        return _result("head_neck", primary, [], "Adjuvant", flags, safety, mdt, refs, "Category 1", "ASTRO Head and Neck Cancer Guideline 2024")

    # Default H&N definitive
    primary = _rec(
        "Head & Neck SCC — definitive or adjuvant RT",
        ["IMRT", "VMAT"],
        "70 Gy/35 fx definitive; 60–66 Gy/30–33 fx adjuvant",
        "2 Gy/fx standard fractionation",
        "Primary tumor + regional lymphatics per NCCN/RTOG contouring guidelines",
        "Concurrent cisplatin for locally advanced disease",
        "Cisplatin 100 mg/m² q3w or weekly 40 mg/m²",
        "Category 1", "A",
        "NCCN H&N v2.2025",
        "IMRT mandatory for all H&N cases to spare salivary glands, spinal cord, and brainstem.",
    )
    return _result("head_neck", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO Head and Neck Cancer Guideline 2024")


# ─── NSCLC ──────────────────────────────────────────────────────────────────


def _evaluate_nsclc(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "4DCT for respiratory motion management",
        "PET-CT for nodal staging before RT planning",
        "Pulmonary function tests before treatment",
        "Esophageal and cardiac dose constraints per QUANTEC",
    ]
    mdt = ["Thoracic Surgery", "Pulmonology", "Medical Oncology", "Thoracic Radiology"]
    refs = [
        {"citation": "NCCN NSCLC v4.2025", "year": 2025, "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1450"},
        {"citation": "ASTRO NSCLC Guideline 2024", "year": 2024},
        {"citation": "Timmerman R et al. JAMA 2010 (SBRT for early-stage NSCLC)", "year": 2010},
        {"citation": "Antonia SJ et al. NEJM 2017 (PACIFIC trial — durvalumab after CRT)", "year": 2017},
    ]

    lung_stage = data.get("lungStage")
    if lung_stage == "IA" or lung_stage == "IB":
        if truthy(data.get("medicallyInoperable")):
            primary = _rec(
                "Stage I NSCLC — medically inoperable, SBRT (SABR)",
                ["SBRT"],
                "54 Gy/3 fx (peripheral) or 50 Gy/5 fx or 60 Gy/8 fx (central/ultracentral)",
                "Peripheral: 18 Gy/fx × 3 fx. Central: 10 Gy/fx × 5 fx. Ultracentral: 7.5 Gy/fx × 8 fx.",
                "GTV = primary tumor; ITV = GTV with respiratory motion; PTV = ITV + 5 mm",
                "SBRT alone — no concurrent systemic therapy",
                "None for SBRT. Adjuvant osimertinib if EGFR-mutant after resection (not applicable here).",
                "Category 1", "A",
                "NCCN NSCLC v4.2025 / ASTRO NSCLC 2024 / Timmerman JAMA 2010",
                "SBRT achieves >90% local control for Stage I NSCLC. 4DCT mandatory for ITV generation.",
            )
            return _result("nsclc", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO NSCLC Guideline 2024")
        else:
            primary = _rec(
                "Stage I NSCLC — surgical candidate",
                ["SBRT"],
                "SBRT as alternative to surgery: 54 Gy/3 fx or 50 Gy/5 fx",
                "SBRT if surgery declined or high surgical risk",
                "GTV + ITV + PTV per 4DCT",
                "Surgery preferred (lobectomy). SBRT if surgery declined.",
                "None",
                "Category 2A", "B",
                "NCCN NSCLC v4.2025",
                "SBRT is preferred for medically inoperable. For operable patients who decline surgery, SBRT is Category 2A.",
            )
            return _result("nsclc", primary, [], "Definitive", flags, safety, mdt, refs, "Category 2A", "ASTRO NSCLC Guideline 2024")

    if lung_stage == "IIIA" or lung_stage == "IIIB" or lung_stage == "IIIC":
        primary = _rec(
            "Stage III NSCLC — definitive concurrent CRT + durvalumab consolidation",
            ["IMRT", "VMAT"],
            "60 Gy in 30 fractions (standard). 66 Gy/33 fx for dose escalation (select cases).",
            "2 Gy/fx × 30 fx concurrent with chemotherapy",
            "GTV = primary tumor + involved nodes (PET-based); CTV = GTV + 8 mm; PTV = CTV + 5–10 mm",
            "Concurrent platinum-doublet chemotherapy (carboplatin/paclitaxel or cisplatin/etoposide). Durvalumab consolidation after CRT × 12 months.",
            "Durvalumab 10 mg/kg q2w × 12 months post-CRT (PACIFIC trial — Category 1 for unresectable Stage III)",
            "Category 1", "A",
            "NCCN NSCLC v4.2025 / PACIFIC NEJM 2017",
            "PACIFIC trial: durvalumab after CRT improved OS (HR 0.68) and PFS. Standard of care for unresectable Stage III NSCLC.",
        )
        flags.append("Stage III NSCLC — durvalumab consolidation after CRT is Category 1 (PACIFIC trial)")
        return _result("nsclc", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO NSCLC Guideline 2024")

    # Default NSCLC
    primary = _rec("NSCLC — specify stage for detailed recommendation", ["IMRT", "SBRT"], "Per NCCN NSCLC guidelines", "Per stage", "Per stage", "Per MDT", "Per stage", "Category 1", "A", "NCCN NSCLC v4.2025", "Specify stage and operability for detailed recommendation.")
    return _result("nsclc", primary, [], "Insufficient data", flags, safety, mdt, refs, "Category 1", "ASTRO NSCLC Guideline 2024")


# ─── SCLC ───────────────────────────────────────────────────────────────────


def _evaluate_sclc(data: dict) -> dict:
    flags: list[str] = []
    safety = ["PCI neurocognitive monitoring", "Esophageal dose constraints", "Cardiac dose constraints"]
    mdt = ["Medical Oncology", "Pulmonology", "Thoracic Surgery"]
    refs = [
        {"citation": "NCCN SCLC v2.2025", "year": 2025, "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1462"},
        {"citation": "Turrisi AT et al. NEJM 1999 (Twice-daily RT for LS-SCLC)", "year": 1999},
        {"citation": "Slotman B et al. NEJM 2007 (PCI for ES-SCLC)", "year": 2007},
        {"citation": "Takahashi T et al. Lancet Oncol 2017 (PCI vs MRI surveillance for ES-SCLC)", "year": 2017},
    ]

    lve = data.get("limitedVsExtensive")
    if lve == "Limited":
        primary = _rec(
            "Limited-stage SCLC — concurrent CRT + PCI",
            ["IMRT", "3DCRT"],
            "45 Gy/30 fx BID (1.5 Gy/fx twice daily) — preferred. Alternative: 60–70 Gy/30–35 fx once daily.",
            "BID: 1.5 Gy/fx × 30 fx (15 fx/week). Once daily: 2 Gy/fx × 30–35 fx.",
            "GTV = primary tumor + involved nodes; CTV = GTV + 1.5 cm; PTV = CTV + 5 mm",
            "Start RT with cycle 1 or 2 of chemotherapy (EP: etoposide + cisplatin/carboplatin)",
            "Etoposide + cisplatin (EP) × 4 cycles concurrent with RT. PCI 25 Gy/10 fx after CR.",
            "Category 1", "A",
            "NCCN SCLC v2.2025 / Turrisi NEJM 1999",
            "BID RT (45 Gy/30 fx) superior to once-daily 45 Gy (Turrisi 1999). PCI recommended after CR (Category 1).",
        )
        flags.append("Limited-stage SCLC — PCI recommended after complete response (25 Gy/10 fx, Category 1)")
        return _result("sclc", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "")

    if lve == "Extensive":
        primary = _rec(
            "Extensive-stage SCLC — thoracic RT consolidation + PCI consideration",
            ["IMRT"],
            "Thoracic consolidation: 30 Gy/10 fx. PCI: 25 Gy/10 fx (if no brain mets on MRI).",
            "3 Gy/fx × 10 fx (thoracic). 2.5 Gy/fx × 10 fx (PCI).",
            "Residual thoracic disease after chemotherapy",
            "After 4–6 cycles of platinum-etoposide ± atezolizumab",
            "Atezolizumab maintenance (IMpower133). PCI vs MRI surveillance — shared decision (Takahashi 2017).",
            "Category 2A", "B",
            "NCCN SCLC v2.2025 / Slotman NEJM 2007 / Takahashi Lancet Oncol 2017",
            "Thoracic RT for ES-SCLC: CREST trial showed OS benefit in residual thoracic disease. PCI: consider MRI surveillance as alternative (Takahashi 2017).",
        )
        flags.append("ES-SCLC — PCI vs MRI surveillance: shared decision making recommended (Takahashi 2017)")
        return _result("sclc", primary, [], "Consolidation", flags, safety, mdt, refs, "Category 2A", "")

    primary = _rec("SCLC — specify limited vs extensive stage", ["IMRT"], "Per NCCN SCLC guidelines", "Per stage", "Per stage", "Per MDT", "Per stage", "Category 1", "A", "NCCN SCLC v2.2025", "Specify limited vs extensive stage for detailed recommendation.")
    return _result("sclc", primary, [], "Insufficient data", flags, safety, mdt, refs, "Category 1", "")


# ─── Prostate ───────────────────────────────────────────────────────────────


def _evaluate_prostate(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "Rectal spacer (SpaceOAR) recommended to reduce rectal dose",
        "Fiducial markers or CBCT for daily image guidance (IGRT)",
        "Baseline bowel/urinary/sexual function assessment",
        "Testosterone monitoring if ADT used",
    ]
    mdt = ["Urology", "Medical Oncology", "Radiation Oncology"]
    refs = [
        {"citation": "NCCN Prostate Cancer v4.2025", "year": 2025, "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1459"},
        {"citation": "ASTRO/AUA Prostate Cancer RT Guideline 2022", "year": 2022},
        {"citation": "Widmark A et al. Lancet 2019 (SPCG-15: EBRT vs brachytherapy boost)", "year": 2019},
        {"citation": "Kishan AU et al. JAMA Oncol 2019 (HDR brachytherapy boost)", "year": 2019},
        {"citation": "Fizazi K et al. NEJM 2017 (STAMPEDE: abiraterone + ADT)", "year": 2017},
    ]

    if truthy(data.get("biochemicalRecurrence")):
        primary = _rec(
            "Biochemical recurrence after prostatectomy — salvage RT",
            ["IMRT", "VMAT"],
            "64–72 Gy in 32–36 fractions to prostate bed. Add pelvic nodal RT if pN1 or high-risk.",
            "1.8–2 Gy/fx × 32–36 fx",
            "Prostate bed CTV per RTOG/FROGG consensus. Pelvic nodes if pN1 or high-risk features.",
            "Early salvage RT (PSA <0.5 ng/mL) preferred. ADT 4–24 months per risk.",
            "Short-course ADT (4–6 months) for intermediate-risk BCR. Long-course (24 months) for high-risk.",
            "Category 1", "A",
            "NCCN Prostate v4.2025 / ASTRO/AUA 2022",
            "Early salvage RT (PSA <0.5) associated with superior outcomes. PSMA PET-CT for staging before salvage RT.",
        )
        if truthy(data.get("psmaPositive")):
            flags.append("PSMA PET-CT positive — directed salvage RT to PSMA-avid sites")
        return _result("prostate", primary, [], "Adjuvant", flags, safety, mdt, refs, "Category 1", "ASTRO/AUA Prostate Cancer RT Guideline 2022")

    risk = data.get("prostateRiskGroup")
    if risk == "Very_Low" or risk == "Low":
        primary = _rec(
            "Low/Very-Low risk prostate cancer — active surveillance preferred; RT if treatment elected",
            ["IMRT", "SBRT", "Brachytherapy"],
            "EBRT: 78–80 Gy/39–40 fx (conventional) or 36.25 Gy/5 fx (SBRT). LDR brachytherapy: 145 Gy (I-125) or 125 Gy (Pd-103).",
            "SBRT: 7.25 Gy/fx × 5 fx (HYPO-RT-PC). LDR brachy monotherapy preferred for low-risk.",
            "Prostate ± seminal vesicles (proximal 1 cm). No pelvic nodal RT.",
            "No ADT for low-risk disease",
            "No ADT (Category 1 for low-risk)",
            "Category 1", "A",
            "NCCN Prostate v4.2025 / ASTRO/AUA 2022",
            "Active surveillance is preferred for very-low and low-risk disease. LDR brachytherapy monotherapy has excellent long-term outcomes.",
        )
        return _result("prostate", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO/AUA Prostate Cancer RT Guideline 2022")

    if risk == "High" or risk == "Very_High":
        primary = _rec(
            "High/Very-High risk prostate cancer — EBRT + long-course ADT ± brachytherapy boost",
            ["IMRT", "VMAT", "Brachytherapy"],
            "EBRT: 78–80 Gy/39–40 fx + HDR brachy boost (15 Gy × 1 or 10 Gy × 2). Or SBRT 36.25 Gy/5 fx.",
            "Conventional: 2 Gy/fx × 39–40 fx. SBRT: 7.25 Gy/fx × 5 fx.",
            "Prostate + seminal vesicles + pelvic nodes (if pN1 or high-risk). Pelvic nodal RT: 45–50.4 Gy.",
            "Long-course ADT 18–36 months (RTOG 9202/9413). Start ADT 2–3 months before RT.",
            "LHRH agonist/antagonist ± abiraterone (STAMPEDE). Long-course ADT 18–36 months (Category 1).",
            "Category 1", "A",
            "NCCN Prostate v4.2025 / ASTRO/AUA 2022 / STAMPEDE NEJM 2017",
            "Brachytherapy boost (HDR or LDR) superior to EBRT alone for high-risk disease (ASCENDE-RT). Pelvic nodal RT recommended if pN1 or risk >15%.",
        )
        flags.append("High-risk prostate — long-course ADT (18–36 months) is Category 1")
        if truthy(data.get("pelvicNodeInvolvement")):
            flags.append("Pelvic node involvement — pelvic nodal RT mandatory")
        return _result("prostate", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO/AUA Prostate Cancer RT Guideline 2022")

    # Intermediate risk
    primary = _rec(
        "Intermediate-risk prostate cancer — EBRT ± short-course ADT",
        ["IMRT", "SBRT", "Brachytherapy"],
        "EBRT: 78 Gy/39 fx or 36.25 Gy/5 fx (SBRT). LDR brachy ± EBRT for unfavorable intermediate.",
        "Moderate hypofractionation: 60 Gy/20 fx or 70 Gy/28 fx. SBRT: 7.25 Gy/fx × 5 fx.",
        "Prostate ± proximal seminal vesicles. No pelvic nodal RT for favorable intermediate.",
        "Short-course ADT 4–6 months for unfavorable intermediate (RTOG 9408)",
        "ADT 4–6 months for unfavorable intermediate risk (Category 1)",
        "Category 1", "A",
        "NCCN Prostate v4.2025 / ASTRO/AUA 2022",
        "Favorable intermediate: RT alone acceptable. Unfavorable intermediate: short-course ADT 4–6 months (Category 1).",
    )
    return _result("prostate", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO/AUA Prostate Cancer RT Guideline 2022")


# ─── Esophageal ─────────────────────────────────────────────────────────────


def _evaluate_esophageal(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "4DCT for motion management",
        "Cardiac and pulmonary dose constraints",
        "Nutritional support (PEG/NJ tube consideration)",
        "Baseline PFTs",
    ]
    mdt = ["Thoracic Surgery", "GI Oncology", "Gastroenterology", "Nutrition"]
    refs = [
        {"citation": "NCCN Esophageal and Esophagogastric Junction Cancers v2.2025", "year": 2025},
        {"citation": "van Hagen P et al. NEJM 2012 (CROSS trial — neoadjuvant CRT)", "year": 2012},
        {"citation": "ASTRO Gastric Cancer RT Guideline 2025", "year": 2025},
        {"citation": "Cunningham D et al. NEJM 2006 (MAGIC trial — perioperative chemo)", "year": 2006},
    ]

    primary = _rec(
        "Resectable esophageal/GEJ cancer — neoadjuvant CRT (CROSS regimen)",
        ["IMRT", "VMAT"],
        "41.4 Gy in 23 fractions (CROSS regimen)",
        "1.8 Gy/fx × 23 fx concurrent with weekly carboplatin/paclitaxel",
        "GTV = primary tumor + involved nodes; CTV = GTV + 3–4 cm longitudinal, 0.5–1 cm radial; PTV = CTV + 5–7 mm",
        "Neoadjuvant CRT → surgery (esophagectomy) 6–8 weeks after RT completion",
        "Carboplatin AUC 2 + paclitaxel 50 mg/m² weekly × 5 cycles concurrent with RT (CROSS protocol)",
        "Category 1", "A",
        "NCCN Esophageal v2.2025 / CROSS NEJM 2012",
        "CROSS trial: neoadjuvant CRT improved OS vs surgery alone (HR 0.657). Standard of care for resectable esophageal/GEJ cancer.",
    )
    flags.append("Esophageal cancer — CROSS neoadjuvant CRT is Category 1 for resectable disease")
    return _result("esophageal", primary, [], "Neoadjuvant", flags, safety, mdt, refs, "Category 1", "ASTRO Gastric Cancer RT Guideline 2025")


# ─── Gastric ────────────────────────────────────────────────────────────────


def _evaluate_gastric(data: dict) -> dict:
    flags: list[str] = []
    safety = ["Renal dose constraints (bilateral kidneys)", "Hepatic dose constraints", "Nutritional support mandatory"]
    mdt = ["GI Surgery", "GI Oncology", "Gastroenterology"]
    refs = [
        {"citation": "NCCN Gastric Cancer v2.2025", "year": 2025},
        {"citation": "ASTRO Gastric Cancer RT Guideline 2025 (first dedicated ASTRO guideline)", "year": 2025},
        {"citation": "Macdonald JS et al. NEJM 2001 (INT-0116: adjuvant CRT)", "year": 2001},
        {"citation": "Cats A et al. Lancet Oncol 2018 (CRITICS trial)", "year": 2018},
    ]

    primary = _rec(
        "Resectable gastric cancer — adjuvant CRT (post-D0/D1 resection) or perioperative chemotherapy",
        ["IMRT", "VMAT"],
        "45 Gy in 25 fractions (INT-0116 regimen). 50.4 Gy/28 fx for R1 resection.",
        "1.8 Gy/fx × 25 fx concurrent with 5-FU/leucovorin",
        "Tumor bed + regional lymphatics (celiac, perigastric, porta hepatis). Per ASTRO 2025 contouring atlas.",
        "Adjuvant CRT after D0/D1 resection (INT-0116). Perioperative FLOT preferred after D2 resection.",
        "5-FU/leucovorin concurrent (INT-0116). FLOT perioperative chemotherapy preferred for D2 resection.",
        "Category 1", "A",
        "NCCN Gastric v2.2025 / ASTRO Gastric 2025 / INT-0116 NEJM 2001",
        "ASTRO 2025 Gastric Guideline: first dedicated ASTRO guideline clarifying RT role in multimodal gastric cancer care. RT benefit greatest after D0/D1 resection.",
    )
    flags.append("ASTRO 2025 Gastric Guideline — first dedicated ASTRO guideline for gastric cancer RT")
    return _result("gastric", primary, [], "Adjuvant", flags, safety, mdt, refs, "Category 1", "ASTRO Gastric Cancer RT Guideline 2025")


# ─── Rectal ─────────────────────────────────────────────────────────────────


def _evaluate_rectal(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "MRI pelvis for staging and MRF assessment",
        "Bowel dose constraints (V45 <195 cc)",
        "Bladder dose constraints",
        "Sexual function baseline",
    ]
    mdt = ["Colorectal Surgery", "GI Oncology", "Gastroenterology", "Radiology (MRI staging)"]
    refs = [
        {"citation": "NCCN Rectal Cancer v3.2025", "year": 2025},
        {"citation": "Sauer R et al. NEJM 2004 (German Rectal Cancer Study — preop vs postop CRT)", "year": 2004},
        {"citation": "Bahadoer RR et al. Lancet Oncol 2021 (RAPIDO trial — short-course RT + systemic)", "year": 2021},
        {"citation": "Conroy T et al. NEJM 2021 (PRODIGE 23 — TNT)", "year": 2021},
    ]

    if truthy(data.get("rectalMRFInvolvement")) or data.get("rectalT") == "T4":
        primary = _rec(
            "Locally advanced rectal cancer — total neoadjuvant therapy (TNT) or long-course CRT",
            ["IMRT", "VMAT"],
            "Long-course CRT: 50.4 Gy/28 fx. Short-course RT: 25 Gy/5 fx (RAPIDO). TNT: SCRT + FOLFOX or LCRT + CAPOX.",
            "Long-course: 1.8 Gy/fx × 28 fx. Short-course: 5 Gy/fx × 5 fx.",
            "GTV = primary tumor + involved nodes; CTV = GTV + mesorectal fascia + presacral + lateral pelvic nodes; PTV = CTV + 5–7 mm",
            "TNT (total neoadjuvant therapy) preferred: SCRT + FOLFOX × 6 cycles, then surgery. Or LCRT + CAPOX, then surgery.",
            "FOLFOX or CAPOX concurrent/sequential. Capecitabine 825 mg/m² BID concurrent with LCRT.",
            "Category 1", "A",
            "NCCN Rectal v3.2025 / RAPIDO Lancet Oncol 2021 / PRODIGE 23 NEJM 2021",
            "TNT (RAPIDO/PRODIGE 23) achieves higher pCR rates and may enable watch-and-wait. MRF involvement mandates aggressive neoadjuvant approach.",
        )
        if truthy(data.get("rectalMRFInvolvement")):
            flags.append("MRF involvement — aggressive neoadjuvant TNT or LCRT mandatory")
        if truthy(data.get("rectalWatchAndWait")):
            flags.append("Watch-and-wait strategy — requires clinical CR assessment at 8–12 weeks post-RT")
        return _result("rectal", primary, [], "Neoadjuvant", flags, safety, mdt, refs, "Category 1", "")

    primary = _rec(
        "Rectal cancer T3N0 or T1-3N1 — neoadjuvant CRT or short-course RT",
        ["IMRT", "VMAT"],
        "50.4 Gy/28 fx (standard LCRT) or 25 Gy/5 fx (SCRT, RAPIDO/Stockholm III)",
        "Long-course: 1.8 Gy/fx × 28 fx. Short-course: 5 Gy/fx × 5 fx.",
        "Mesorectal CTV + presacral nodes. Lateral pelvic nodes if T4 or N2.",
        "Surgery 6–8 weeks after LCRT or 1 week after SCRT (immediate) or 8 weeks (delayed)",
        "Capecitabine 825 mg/m² BID concurrent with LCRT (preferred over 5-FU infusion)",
        "Category 1", "A",
        "NCCN Rectal v3.2025 / Sauer NEJM 2004",
        "Preoperative CRT preferred over postoperative (German trial). SCRT equivalent to LCRT for non-MRF-involved disease.",
    )
    return _result("rectal", primary, [], "Neoadjuvant", flags, safety, mdt, refs, "Category 1", "")


# ─── Lymphoma ───────────────────────────────────────────────────────────────


def _evaluate_lymphoma(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "PET-CT before and after chemotherapy for response assessment",
        "Cardiac dose constraints (V25 <10% for heart)",
        "Pulmonary dose constraints",
        "Thyroid monitoring post-RT for mediastinal RT",
    ]
    mdt = ["Hematology/Oncology", "Hematopathology", "Nuclear Medicine (PET)"]
    refs = [
        {"citation": "NCCN Hodgkin Lymphoma v2.2025", "year": 2025},
        {"citation": "NCCN DLBCL v4.2025", "year": 2025},
        {"citation": "Engert A et al. NEJM 2012 (GHSG HD16 — PET-guided RT)", "year": 2012},
        {"citation": "Lister TA et al. JCO 1989 (Cotswolds staging)", "year": 1989},
        {"citation": "ASTRO Lymphoma RT Consensus 2024", "year": 2024},
    ]

    lymphoma_type = data.get("lymphomaType")
    lymphoma_stage = data.get("lymphomaStage")
    deauville = num(data.get("deauvilleScore"), 0)

    if lymphoma_type == "Hodgkin":
        if lymphoma_stage == "I" or lymphoma_stage == "II":
            primary = _rec(
                "Early-stage Hodgkin Lymphoma — combined modality therapy (CMT) or PET-guided approach",
                ["IMRT", "VMAT"],
                "20 Gy/10 fx (PET-negative after ABVD × 2). 30 Gy/15 fx (PET-positive or bulky).",
                "2 Gy/fx × 10–15 fx (involved-site RT, ISRT)",
                "Involved-site RT (ISRT): pre-chemotherapy GTV + 1.5 cm longitudinal, 1 cm axial. No elective nodal RT.",
                "ABVD × 2–4 cycles → PET assessment → ISRT if PET-positive or bulky. PET-negative: RT may be omitted (GHSG HD16).",
                "ABVD × 2 cycles. Escalated BEACOPP for high-risk early-stage.",
                "Category 1", "A",
                "NCCN HL v2.2025 / GHSG HD16 NEJM 2012",
                "PET-guided approach: ABVD × 2 → PET. If PET-negative (Deauville 1–2): RT may be omitted. If PET-positive: ISRT 30 Gy.",
            )
            if deauville >= 3:
                flags.append(f"Deauville score {deauville:g} — ISRT recommended after chemotherapy")
            if truthy(data.get("bulkyDisease")):
                flags.append("Bulky disease (≥10 cm) — ISRT 30 Gy recommended regardless of PET response")
            return _result("lymphoma", primary, [], "Consolidation", flags, safety, mdt, refs, "Category 1", "ASTRO Lymphoma RT Consensus 2024")

    if lymphoma_type == "DLBCL":
        primary = _rec(
            "DLBCL — consolidation RT after R-CHOP (limited stage or bulky disease)",
            ["IMRT", "VMAT"],
            "30–36 Gy/15–18 fx to sites of initial bulky disease or PET-positive residual",
            "2 Gy/fx × 15–18 fx (ISRT)",
            "ISRT: pre-chemotherapy GTV + 1.5 cm. No elective nodal RT.",
            "R-CHOP × 4–6 cycles → PET assessment → ISRT for PET-positive residual or initial bulky disease",
            "R-CHOP (rituximab + CHOP) × 4–6 cycles",
            "Category 2A", "B",
            "NCCN DLBCL v4.2025",
            "RT consolidation for limited-stage DLBCL (Stage I–II, non-bulky): R-CHOP × 4 + ISRT 30 Gy. Bulky disease: ISRT 36 Gy regardless of PET.",
        )
        if truthy(data.get("bulkyDisease")):
            flags.append("Bulky DLBCL — ISRT 36 Gy recommended after R-CHOP")
        return _result("lymphoma", primary, [], "Consolidation", flags, safety, mdt, refs, "Category 2A", "ASTRO Lymphoma RT Consensus 2024")

    primary = _rec("Lymphoma — specify type and stage for detailed recommendation", ["IMRT"], "Per NCCN Lymphoma guidelines", "Per type/stage", "ISRT per ILROG guidelines", "Per MDT", "Per type", "Category 2A", "B", "NCCN Lymphoma v2.2025", "Specify lymphoma type and stage for detailed recommendation.")
    return _result("lymphoma", primary, [], "Insufficient data", flags, safety, mdt, refs, "Category 2A", "")


# ─── HCC ────────────────────────────────────────────────────────────────────


def _evaluate_hcc(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "Liver function reserve assessment (Child-Pugh, MELD)",
        "Mean liver dose <28–32 Gy for SBRT",
        "Portal vein dose constraints",
        "Baseline AFP and imaging",
    ]
    mdt = ["Hepatology", "Transplant Surgery", "IR (TACE/ablation)", "GI Oncology"]
    refs = [
        {"citation": "NCCN Hepatocellular Carcinoma v3.2025", "year": 2025},
        {"citation": "ASTRO HCC RT Guideline 2024", "year": 2024},
        {"citation": "Dawson LA et al. JCO 2000 (Liver SBRT dose-response)", "year": 2000},
        {"citation": "Yoon SM et al. JAMA Oncol 2018 (SBRT for HCC with PVT)", "year": 2018},
    ]

    if data.get("hccChildPugh") == "C":
        flags.append("Child-Pugh C — RT generally not recommended; liver function insufficient")
        primary = _rec("HCC Child-Pugh C — RT not recommended", ["None"], "Not indicated", "N/A", "N/A", "Best supportive care or transplant evaluation", "None", "Category 2B", "C", "NCCN HCC v3.2025", "Child-Pugh C: RT risk of radiation-induced liver disease (RILD) is prohibitive. Transplant evaluation if eligible.")
        return _result("hcc", primary, [], "Not indicated", flags, safety, mdt, refs, "Category 2B", "")

    if truthy(data.get("hccPortalVeinThrombosis")):
        primary = _rec(
            "HCC with portal vein thrombosis — SBRT or hypofractionated RT",
            ["SBRT", "IMRT"],
            "SBRT: 40–50 Gy/5 fx or 45 Gy/3 fx (if adequate liver reserve). Hypofractionated: 36–54 Gy/6–18 fx.",
            "SBRT: 8–10 Gy/fx × 5 fx. Hypofractionated: 4–6 Gy/fx × 6–18 fx.",
            "GTV = HCC + PVT thrombus; ITV per 4DCT; PTV = ITV + 5 mm",
            "SBRT ± sorafenib/lenvatinib. TACE contraindicated with PVT.",
            "Sorafenib or lenvatinib systemic therapy concurrent or sequential",
            "Category 2A", "B",
            "NCCN HCC v3.2025 / ASTRO HCC 2024 / Yoon JAMA Oncol 2018",
            "SBRT for HCC with PVT: Yoon 2018 showed 72% local control at 2 years. TACE contraindicated with main PVT.",
        )
        flags.append("Portal vein thrombosis — TACE contraindicated; SBRT is preferred RT approach")
        return _result("hcc", primary, [], "Definitive", flags, safety, mdt, refs, "Category 2A", "ASTRO HCC RT Guideline 2024")

    primary = _rec(
        "HCC — SBRT for unresectable or bridge to transplant",
        ["SBRT"],
        "36–54 Gy in 3–6 fractions (Child-Pugh A). 40–50 Gy/5 fx standard.",
        "8–10 Gy/fx × 5 fx (Child-Pugh A). Reduce dose for Child-Pugh B.",
        "GTV = HCC tumor; ITV per 4DCT; PTV = ITV + 5 mm",
        "SBRT as bridge to transplant or definitive treatment if TACE-refractory/ineligible",
        "Sorafenib or lenvatinib for BCLC-B/C. Immunotherapy (atezolizumab + bevacizumab) for advanced HCC.",
        "Category 2A", "B",
        "NCCN HCC v3.2025 / ASTRO HCC 2024",
        "SBRT for HCC: 90% local control at 2 years for ≤5 cm lesions. Bridge to transplant: RT can achieve CR in 30–50% of patients.",
    )
    if truthy(data.get("hccTransplantCandidate")):
        flags.append("Transplant candidate — SBRT as bridge to transplant; coordinate with transplant team")
    return _result("hcc", primary, [], "Definitive", flags, safety, mdt, refs, "Category 2A", "ASTRO HCC RT Guideline 2024")


# ─── Breast ─────────────────────────────────────────────────────────────────


def _evaluate_breast(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "Prone positioning for large-breasted patients to reduce heart/lung dose",
        "Deep inspiration breath hold (DIBH) for left-sided breast cancer",
        "Cardiac dose constraints: mean heart dose <4 Gy (left-sided)",
        "Brachial plexus dose constraints for nodal RT",
    ]
    mdt = ["Breast Surgery", "Medical Oncology", "Plastic Surgery (if reconstruction)", "Genetics (if BRCA)"]
    refs = [
        {"citation": "NCCN Breast Cancer v4.2025", "year": 2025},
        {"citation": "ASTRO Breast Cancer RT Guideline 2024 (preoperative RT endorsement)", "year": 2024},
        {"citation": "Whelan TJ et al. NEJM 2010 (OCOG — hypofractionated WBI)", "year": 2010},
        {"citation": "Murray Brunt A et al. Lancet 2020 (FAST-Forward — 5-fraction WBI)", "year": 2020},
        {"citation": "Giuliano AE et al. JAMA 2011 (Z0011 — SLNB vs ALND)", "year": 2011},
    ]

    if truthy(data.get("breastPreopRT")):
        primary = _rec(
            "Breast cancer — preoperative RT (ASTRO 2024 endorsement)",
            ["IMRT", "VMAT"],
            "Preoperative APBI: 30 Gy/5 fx or 38.5 Gy/10 fx. Preoperative WBI: 40–42.5 Gy/15–16 fx.",
            "Hypofractionated preoperative RT",
            "Partial breast (APBI) or whole breast per clinical trial protocol",
            "Preoperative RT → surgery 4–8 weeks after RT completion",
            "Neoadjuvant chemotherapy may precede or follow preoperative RT per MDT",
            "Category 2A", "B",
            "NCCN Breast v4.2025 / ASTRO Breast 2024",
            "ASTRO 2024 endorsement of preoperative RT for select patients. NRG-BR007 and other trials ongoing.",
        )
        flags.append("Preoperative RT — ASTRO 2024 endorsement; coordinate with surgery for timing")
        return _result("breast", primary, [], "Neoadjuvant", flags, safety, mdt, refs, "Category 2A", "ASTRO Breast Cancer RT Guideline 2024")

    surgery = data.get("breastSurgery")
    if surgery == "Lumpectomy":
        primary = _rec(
            "Breast-conserving surgery — whole breast irradiation (WBI) or APBI",
            ["IMRT", "3DCRT"],
            "Hypofractionated WBI: 40 Gy/15 fx (OCOG) or 26 Gy/5 fx (FAST-Forward). APBI: 30 Gy/5 fx (ASTRO suitable) or 38.5 Gy/10 fx BID.",
            "Preferred: 40 Gy/15 fx (2.67 Gy/fx). Ultra-hypo: 26 Gy/5 fx (5.2 Gy/fx). APBI: 6 Gy/fx × 5 fx.",
            "Whole breast ± boost (10–16 Gy/5–8 fx to lumpectomy cavity). APBI: lumpectomy cavity + 1.5 cm.",
            "Adjuvant RT after lumpectomy. Nodal RT if pN1–3 or high-risk pN0.",
            "Endocrine therapy (if HR+). Trastuzumab (if HER2+). Capecitabine/olaparib per residual disease.",
            "Category 1", "A",
            "NCCN Breast v4.2025 / OCOG NEJM 2010 / FAST-Forward Lancet 2020",
            "FAST-Forward 26 Gy/5 fx: non-inferior to 40 Gy/15 fx at 5 years. APBI appropriate for low-risk patients (ASTRO suitable criteria: age ≥50, T1, ER+, LN-).",
        )
        if truthy(data.get("breastNodePositive")):
            flags.append("Node-positive — regional nodal irradiation (RNI) recommended")
        if truthy(data.get("breastLVI")):
            flags.append("LVI present — boost to lumpectomy cavity recommended")
        if truthy(data.get("breastCloseMargins")):
            flags.append("Close margins — boost dose escalation recommended")
        return _result("breast", primary, [], "Adjuvant", flags, safety, mdt, refs, "Category 1", "ASTRO Breast Cancer RT Guideline 2024")

    if surgery == "Mastectomy":
        primary = _rec(
            "Post-mastectomy RT (PMRT) — pT3-4 or pN1-3",
            ["IMRT", "VMAT"],
            "50 Gy/25 fx or 42.5 Gy/16 fx (hypofractionated PMRT). Chest wall + regional nodes.",
            "Conventional: 2 Gy/fx × 25 fx. Hypofractionated: 2.65 Gy/fx × 16 fx (FAST-Forward equivalent).",
            "Chest wall + ipsilateral supraclavicular/infraclavicular ± IMN ± axilla (per nodal status)",
            "Adjuvant RT after mastectomy. Reconstruct with tissue expander/implant — coordinate with plastics.",
            "Endocrine therapy, trastuzumab, or capecitabine per receptor status and residual disease",
            "Category 1", "A",
            "NCCN Breast v4.2025 / ASTRO Breast 2024",
            "PMRT indications: pT3-4, pN2-3 (Category 1). pN1: PMRT recommended (Category 1 per NCCN 2025 update). IMN RT: consider for medial/central tumors with pN1+.",
        )
        if truthy(data.get("breastNodePositive")):
            flags.append("pN1+ post-mastectomy — PMRT is Category 1 per NCCN 2025")
        return _result("breast", primary, [], "Adjuvant", flags, safety, mdt, refs, "Category 1", "ASTRO Breast Cancer RT Guideline 2024")

    primary = _rec("Breast cancer — specify surgery type for detailed recommendation", ["IMRT"], "Per NCCN Breast guidelines", "Per surgery type", "Per surgery type", "Per MDT", "Per receptor status", "Category 1", "A", "NCCN Breast v4.2025", "Specify surgery type (lumpectomy vs mastectomy) for detailed recommendation.")
    return _result("breast", primary, [], "Insufficient data", flags, safety, mdt, refs, "Category 1", "ASTRO Breast Cancer RT Guideline 2024")


# ─── Skin ───────────────────────────────────────────────────────────────────


def _evaluate_skin(data: dict) -> dict:
    flags: list[str] = []
    safety = ["Bolus material for superficial skin tumors", "Eye shielding for periorbital lesions", "Dose to underlying bone/cartilage constraints"]
    mdt = ["Dermatology", "Dermatologic Surgery (Mohs)", "Medical Oncology (for advanced cSCC)"]
    refs = [
        {"citation": "NCCN Basal Cell Skin Cancer v2.2025", "year": 2025},
        {"citation": "NCCN Squamous Cell Skin Cancer v2.2025", "year": 2025},
        {"citation": "ASTRO Skin Cancer RT Guideline 2023", "year": 2023},
        {"citation": "Migden MR et al. NEJM 2018 (cemiplimab for advanced cSCC)", "year": 2018},
    ]

    if truthy(data.get("skinUnresectable")):
        primary = _rec(
            "Unresectable BCC or cSCC — definitive RT",
            ["IMRT", "3DCRT"],
            "60–70 Gy in 30–35 fractions (conventional). Hypofractionated: 45 Gy/15 fx or 35 Gy/5 fx.",
            "2 Gy/fx × 30–35 fx (conventional). Hypofractionated for elderly/poor PS.",
            "GTV = gross tumor; CTV = GTV + 1–2 cm; PTV = CTV + 3–5 mm. Bolus for superficial tumors.",
            "Definitive RT for unresectable disease. Cemiplimab for advanced cSCC.",
            "Cemiplimab (anti-PD-1) for locally advanced/metastatic cSCC (Category 1). Vismodegib/sonidegib for advanced BCC.",
            "Category 1", "A",
            "NCCN Skin v2.2025 / ASTRO Skin 2023 / Migden NEJM 2018",
            "Cemiplimab: 47% ORR for locally advanced cSCC (EMPOWER-CSCC-1). RT as definitive treatment for unresectable disease.",
        )
        flags.append("Unresectable skin cancer — cemiplimab (cSCC) or vismodegib (BCC) + RT consideration")
        return _result("skin", primary, [], "Definitive", flags, safety, mdt, refs, "Category 1", "ASTRO Skin Cancer RT Guideline 2023")

    primary = _rec(
        "High-risk BCC/cSCC — adjuvant RT after surgery",
        ["3DCRT", "IMRT"],
        "60–66 Gy/30–33 fx (adjuvant after R1). 50–54 Gy/25–27 fx (adjuvant after R0 with high-risk features).",
        "2 Gy/fx × 25–33 fx",
        "Surgical bed + 1–2 cm margin. Regional nodes if perineural invasion or nodal involvement.",
        "Adjuvant RT after surgery for high-risk features (perineural invasion, positive margins, recurrent disease)",
        "Cemiplimab for cSCC with nodal disease or recurrence",
        "Category 2A", "B",
        "NCCN Skin v2.2025 / ASTRO Skin 2023",
        "High-risk features for adjuvant RT: perineural invasion, positive margins, recurrent disease, immunosuppression, size >2 cm.",
    )
    if truthy(data.get("skinHighRisk")):
        flags.append("High-risk features present — adjuvant RT recommended")
    if truthy(data.get("skinImmuncompromised")):
        flags.append("Immunocompromised patient — higher RT dose and broader margins recommended")
    return _result("skin", primary, [], "Adjuvant", flags, safety, mdt, refs, "Category 2A", "ASTRO Skin Cancer RT Guideline 2023")


# ─── Palliative / Oligometastatic ───────────────────────────────────────────


def _evaluate_palliative(data: dict) -> dict:
    flags: list[str] = []
    safety = [
        "Assess prior RT to same site before re-irradiation",
        "Spinal cord dose constraints for vertebral RT",
        "Assess fracture risk before bone RT (SINS score)",
    ]
    mdt = ["Palliative Care", "Medical Oncology", "Orthopedic Surgery (if impending fracture)", "Neurosurgery (if cord compression)"]
    refs = [
        {"citation": "NCCN Palliative Care v2.2025", "year": 2025},
        {"citation": "Chow E et al. JCO 2007 (8 Gy single fraction for bone mets)", "year": 2007},
        {"citation": "Patchell RA et al. Lancet 2005 (Surgery + RT for cord compression)", "year": 2005},
        {"citation": "Palma DA et al. Lancet 2019 (SABR-COMET — oligometastatic SBRT)", "year": 2019},
        {"citation": "Gomez DR et al. Lancet Oncol 2016 (NSCLC oligomets — local consolidative therapy)", "year": 2016},
    ]

    palliative_intent = data.get("palliativeIntent")
    if palliative_intent == "Oligomets" or data.get("diseaseCategory") == "oligometastatic":
        if num(data.get("oligoMetCount"), 0) <= 5 and truthy(data.get("oligoPrimaryControlled")):
            primary = _rec(
                "Oligometastatic disease — SBRT/SABR for all sites (SABR-COMET)",
                ["SBRT"],
                "SBRT per site: bone 16–24 Gy/1 fx or 30 Gy/3 fx; lung 54 Gy/3 fx; liver 45–60 Gy/3–5 fx; adrenal 40–50 Gy/5 fx",
                "Site-specific SBRT fractionation",
                "GTV = each metastatic lesion; ITV per 4DCT; PTV = ITV + 3–5 mm",
                "SBRT to all oligometastatic sites. Continue systemic therapy per primary tumor.",
                "Continue systemic therapy. Immunotherapy may be combined with SBRT (abscopal effect).",
                "Category 2A", "B",
                "NCCN Palliative v2.2025 / SABR-COMET Lancet 2019 / Gomez Lancet Oncol 2016",
                "SABR-COMET: SBRT to all oligomets improved OS (41 vs 28 months, HR 0.57). ≤5 mets, controlled primary. NSCLC oligomets: local consolidative therapy improved PFS (Gomez 2016).",
            )
            flags.append("Oligometastatic disease — SBRT to all sites may improve OS (SABR-COMET, Category 2A)")
            return _result("oligometastatic", primary, [], "Definitive", flags, safety, mdt, refs, "Category 2A", "")

    if palliative_intent == "Cord_Compression":
        primary = _rec(
            "Malignant spinal cord compression — urgent RT ± surgery",
            ["3DCRT", "IMRT"],
            "30 Gy/10 fx (standard). 8 Gy/1 fx or 20 Gy/5 fx (poor prognosis). SBRT 24 Gy/2 fx (post-surgical stabilization).",
            "30 Gy/10 fx (3 Gy/fx) standard. 8 Gy single fraction for very poor prognosis.",
            "Involved vertebral body/bodies ± 1 level above and below",
            "Urgent: start RT within 24 hours of diagnosis. Surgery (decompression + stabilization) if single-level, good PS, radioresistant histology.",
            "Dexamethasone 10 mg IV loading → 4 mg q6h during RT",
            "Category 1", "A",
            "NCCN Palliative v2.2025 / Patchell Lancet 2005",
            "Patchell 2005: surgery + RT superior to RT alone for ambulatory preservation. Urgent RT within 24 hours mandatory.",
        )
        flags.append("URGENT: Malignant spinal cord compression — RT must start within 24 hours")
        flags.append("Dexamethasone loading dose required immediately")
        return _result("palliative", primary, [], "Palliative", flags, safety, mdt, refs, "Category 1", "")

    if palliative_intent == "Bone":
        primary = _rec(
            "Bone metastases — palliative RT",
            ["3DCRT", "SBRT"],
            "8 Gy/1 fx (single fraction — equivalent to multifraction for pain). 20 Gy/5 fx or 30 Gy/10 fx (multifraction). SBRT 24 Gy/2 fx for spine (post-op or radioresistant).",
            "Single fraction 8 Gy preferred for uncomplicated bone mets (equivalent efficacy, more convenient).",
            "Involved bone ± 2 cm margin",
            "Systemic therapy per primary tumor. Bone-modifying agents (zoledronic acid/denosumab).",
            "Bone-modifying agents. Radium-223 for castration-resistant prostate cancer with bone mets.",
            "Category 1", "A",
            "NCCN Palliative v2.2025 / Chow JCO 2007",
            "Single fraction 8 Gy: equivalent pain relief to multifraction (Chow 2007 meta-analysis). Higher re-treatment rate with single fraction. SBRT for spine: superior local control for radioresistant histologies.",
        )
        return _result("palliative", primary, [], "Palliative", flags, safety, mdt, refs, "Category 1", "")

    primary = _rec("Palliative RT — specify intent for detailed recommendation", ["3DCRT", "SBRT"], "Per NCCN Palliative guidelines", "Per site and intent", "Per site", "Per MDT", "Per primary tumor", "Category 1", "A", "NCCN Palliative v2.2025", "Specify palliative intent (bone, cord compression, brain, oligomets) for detailed recommendation.")
    return _result("palliative", primary, [], "Palliative", flags, safety, mdt, refs, "Category 1", "")


# ─── Main entry point ───────────────────────────────────────────────────────


def assess(data: dict) -> dict:
    disease_category = data.get("diseaseCategory")
    if disease_category == "cns":
        return _evaluate_cns(data)
    if disease_category == "head_neck":
        return _evaluate_head_neck(data)
    if disease_category == "nsclc":
        return _evaluate_nsclc(data)
    if disease_category == "sclc":
        return _evaluate_sclc(data)
    if disease_category == "prostate":
        return _evaluate_prostate(data)
    if disease_category == "esophageal":
        return _evaluate_esophageal(data)
    if disease_category == "gastric":
        return _evaluate_gastric(data)
    if disease_category == "rectal":
        return _evaluate_rectal(data)
    if disease_category == "lymphoma":
        return _evaluate_lymphoma(data)
    if disease_category == "hcc":
        return _evaluate_hcc(data)
    if disease_category == "breast":
        return _evaluate_breast(data)
    if disease_category == "skin":
        return _evaluate_skin(data)
    if disease_category == "palliative" or disease_category == "oligometastatic":
        return _evaluate_palliative(data)

    return {
        "diseaseCategory": "",
        "primaryRecommendation": _rec(
            "Select a disease site to begin",
            ["None"],
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "Category 2A",
            "C",
            "NCCN / ASTRO",
            "Please select a disease category to receive guideline-based recommendations.",
        ),
        "alternativeRecommendations": [],
        "rtRole": "Insufficient data",
        "urgentFlags": [],
        "safetyConsiderations": [],
        "multidisciplinaryConsult": [],
        "references": [],
        "nccnCategory": "",
        "astroGuideline": "",
    }
