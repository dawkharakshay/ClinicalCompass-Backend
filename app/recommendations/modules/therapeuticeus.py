"""Therapeutic EUS (EUS-Guided Biliary Drainage) Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/therapeuticEUSLogic.ts
(assessTherapeuticEUS).
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "therapeuticeus"

_REFERENCES = [
    {
        "citation": "ASGE Standards of Practice Committee. The role of endoscopy in the management of choledocholithiasis. Gastrointest Endosc. 2019;89(6):1075-1105.",
        "pmid": "30979521",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30979521/",
    },
    {
        "citation": "Paik WH, et al. EUS-Guided Biliary Drainage vs ERCP for Malignant Biliary Obstruction (ELEMENT). Lancet Gastroenterol Hepatol. 2023;8(2):132-141.",
        "pmid": "36462521",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36462521/",
    },
    {
        "citation": "Teoh AYB, et al. EUS-Guided Gallbladder Drainage vs Percutaneous Cholecystostomy for Acute Cholecystitis (ENDOCATCH). Gut. 2024;73(1):50-58.",
        "pmid": "37793794",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37793794/",
    },
    {
        "citation": "Nakai Y, et al. International consensus statements for endoscopic management of distal biliary stricture. J Gastroenterol Hepatol. 2020;35(6):967-979.",
        "pmid": "32162356",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32162356/",
    },
]


def _underscores(value: object) -> str:
    return str(value).replace("_", " ")


def _fmt_num(x: float) -> str:
    """Render a number the way JS string interpolation would (whole numbers
    without a trailing ``.0``). Only called on real (non-NaN) numbers."""
    return str(int(x)) if x == int(x) else str(x)


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    next_steps: list[str] = []

    indication = data.get("indication")
    obstruction_level = data.get("obstructionLevel")
    # Numeric fields arrive as raw strings (or absent); TS treats them as
    # `number | undefined`. parse_float -> NaN mirrors `undefined` (guarded via
    # x == x below), matching TS `!== undefined && <compare>` semantics.
    cbd_diameter_mm = parse_float(data.get("cbdDiameterMm"))
    inr_value = parse_float(data.get("inrValue"))
    platelet_count = parse_float(data.get("plateletCount"))

    has_acute_cholecystitis = truthy(data.get("hasAcuteCholecystitis"))
    is_surgical_high_risk = truthy(data.get("isSurgicalHighRisk"))
    has_intrahepatic_dilation = truthy(data.get("hasIntrahepticDilation"))
    has_altered_anatomy = truthy(data.get("hasAlteredAnatomy"))
    has_ascites = truthy(data.get("hasAscites"))
    has_pancreatic_duct_dilation = truthy(data.get("hasPancreaticDuctDilation"))
    has_coagulopathy = truthy(data.get("hasCoagulopathy"))
    has_malignant_obstruction = truthy(data.get("hasMalignantObstruction"))
    is_resectable = truthy(data.get("isResectable"))

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if has_coagulopathy and inr_value == inr_value and inr_value > 1.5:
        urgent_flags.append(
            f"Coagulopathy (INR {_fmt_num(inr_value)}): correct to INR <1.5 before EUS-BD — FFP, vitamin K, or hold anticoagulation"
        )
    if platelet_count == platelet_count and platelet_count < 50000:
        urgent_flags.append(
            f"Thrombocytopenia (platelets {_fmt_num(platelet_count)}): transfuse to >50,000 before EUS-BD"
        )
    if has_acute_cholecystitis and not is_surgical_high_risk:
        urgent_flags.append(
            "Acute cholecystitis in surgical candidate: laparoscopic cholecystectomy is preferred over EUS-GBD — consult surgery"
        )
    if indication == "malignant_biliary_obstruction" and is_resectable:
        urgent_flags.append(
            "Resectable malignancy: biliary drainage should be performed only if surgery delayed >2 weeks or jaundice severe — avoid pre-op stenting if surgery within 2 weeks (increases infection risk)"
        )

    # ─── EUS-BD Approach Selection ────────────────────────────────────────────
    eus_bd_approach = ""
    stent_selection = ""
    procedure_sequence = ""

    if indication == "gallbladder_drainage" or has_acute_cholecystitis:
        eus_bd_approach = (
            "EUS-GUIDED GALLBLADDER DRAINAGE (EUS-GBD) with LAMS (ASGE 2024): "
            "Indication: acute cholecystitis in surgical high-risk patients. "
            "Approach: transgastric or transduodenal access to gallbladder. "
            "LAMS (lumen-apposing metal stent): Hot AXIOS or SPAXUS — creates fistula between GI lumen and gallbladder. "
            "Technical success: 93–98%. Clinical success: 90–95%. "
            "Advantages over percutaneous cholecystostomy: no external drain, better quality of life, comparable efficacy. "
            "ENDOCATCH trial (2024): EUS-GBD superior to percutaneous drainage for clinical success and adverse events."
        )
        stent_selection = (
            "LAMS selection for EUS-GBD: "
            "Hot AXIOS 10mm × 10mm or 15mm × 10mm (most commonly used). "
            "Electrocautery-enhanced delivery system (Hot AXIOS) — single-step deployment. "
            "Remove stent at 4 weeks if patient becomes surgical candidate."
        )
        next_steps.append("EUS-GBD with LAMS (Hot AXIOS)")
        next_steps.append("Surgical consultation for interval cholecystectomy")
    elif (
        obstruction_level == "distal_cbd"
        and cbd_diameter_mm == cbd_diameter_mm
        and cbd_diameter_mm >= 12
    ):
        eus_bd_approach = (
            "EUS-CHOLEDOCHODUODENOSTOMY (EUS-CDS) — PREFERRED for distal CBD obstruction (ASGE 2025): "
            "Most common EUS-BD approach (70–80% of EUS-BD cases). "
            "Requires: dilated CBD ≥12mm, accessible from duodenal bulb. "
            "Approach: 19G needle → wire → dilation → LAMS or SEMS deployment. "
            "Technical success: 90–95%. Clinical success: 85–92%. "
            "ELEMENT trial (2023): EUS-CDS non-inferior to ERCP for malignant distal biliary obstruction. "
            "DRAINBIL trial: EUS-CDS superior to PTBD for ERCP failure."
        )
        stent_selection = (
            "Stent selection for EUS-CDS: "
            "1) LAMS (Hot AXIOS 6mm × 8mm or 8mm × 8mm): preferred for benign disease or short-term drainage. "
            "2) SEMS (covered or partially covered): preferred for malignant obstruction — longer patency. "
            "3) Plastic stent: not recommended for EUS-CDS (higher migration risk)."
        )
        next_steps.append("EUS-CDS with SEMS (malignant) or LAMS (benign/short-term)")
        next_steps.append("Post-procedure LFTs at 48h and 1 week")
    elif has_intrahepatic_dilation or has_altered_anatomy:
        eus_bd_approach = (
            "EUS-HEPATICOGASTROSTOMY (EUS-HGS) — for hilar obstruction or altered anatomy (ASGE 2025): "
            "Approach: transgastric access to left intrahepatic duct (B3 or B2). "
            "Indication: hilar obstruction, altered anatomy (Roux-en-Y, Whipple) where EUS-CDS not feasible. "
            "Technical success: 85–92%. Clinical success: 80–88%. "
            "Higher adverse event rate than EUS-CDS (bile leak, stent migration). "
            "Avoid if significant ascites (bile peritonitis risk)."
        )
        stent_selection = (
            "Stent selection for EUS-HGS: "
            "Partially covered SEMS (8–10mm × 60–80mm) — preferred for malignant hilar obstruction. "
            "Plastic stent: 7–10Fr for benign disease or bridge to surgery."
        )
        if has_ascites:
            urgent_flags.append(
                "Ascites: EUS-HGS has higher bile leak risk with ascites — consider percutaneous transhepatic biliary drainage (PTBD) as alternative"
            )
        next_steps.append("EUS-HGS with partially covered SEMS")
        next_steps.append("Hepatology/IR consultation if EUS-HGS not feasible")
    elif indication == "choledocholithiasis_ercp_failed":
        eus_bd_approach = (
            "EUS-RENDEZVOUS (EUS-RV) for failed ERCP cannulation: "
            "EUS-guided wire access through papilla → wire retrieved at papilla → ERCP completes cannulation. "
            "Preferred when ERCP failure is due to difficult cannulation (not anatomy). "
            "Technical success: 75–85%. "
            "Alternative: EUS-antegrade stenting (EUS-AG) — wire advanced antegrade through stricture."
        )
        stent_selection = "Plastic stent or SEMS depending on stricture etiology."
        next_steps.append("EUS-rendezvous technique")
        next_steps.append("If rendezvous fails: EUS-CDS or EUS-HGS")
    elif obstruction_level == "pancreatic_duct" or has_pancreatic_duct_dilation:
        eus_bd_approach = (
            "EUS-GUIDED PANCREATIC DUCT DRAINAGE (EUS-PD) (ASGE 2025): "
            "Indication: failed ERCP for pancreatic duct stricture, disconnected pancreatic duct syndrome, chronic pancreatitis with MPD dilation. "
            "Approach: transgastric (body/tail) or transduodenal (head) access to MPD. "
            "Technical success: 75–85%. Clinical success: 70–80%. "
            "Technically demanding — requires expert interventional endoscopist. "
            "Disconnected pancreatic duct syndrome: LAMS preferred (creates fistula for sustained drainage)."
        )
        stent_selection = (
            "Stent for EUS-PD: "
            "5–7Fr plastic stent (standard). "
            "LAMS for disconnected duct syndrome."
        )
        next_steps.append("EUS-PD at expert center")
        next_steps.append("Surgical consultation for pancreatic duct drainage alternatives")
    else:
        eus_bd_approach = "EUS-BD approach to be determined based on anatomy and ERCP findings. Interventional endoscopy consultation recommended."
        stent_selection = "Stent selection pending procedural planning."

    # ─── Procedure Sequence ───────────────────────────────────────────────────
    if not procedure_sequence:
        procedure_sequence = (
            "PROCEDURE SEQUENCE (ASGE 2025): "
            "1) Confirm ERCP failure or contraindication before EUS-BD. "
            "2) Cross-sectional imaging (CT/MRCP) to plan approach. "
            "3) Correct coagulopathy (INR <1.5, platelets >50,000). "
            "4) Hold anticoagulation per procedural guidelines (5 days for warfarin; 24–48h for DOAC). "
            "5) EUS-BD performed under general anesthesia or deep sedation. "
            "6) Fluoroscopy guidance throughout procedure. "
            "7) Post-procedure: NPO 4–6h, IV antibiotics (ceftriaxone), LFTs at 24–48h."
        )

    # ─── Alternative Approach ─────────────────────────────────────────────────
    alternative_approach = (
        "ALTERNATIVES TO EUS-BD: "
        "1) Percutaneous transhepatic biliary drainage (PTBD): IR-guided, external drain. "
        "   Preferred if: EUS-BD technically not feasible, ascites, coagulopathy not correctable. "
        "   Higher adverse event rate than EUS-BD (bile leak, cholangitis, tube dislodgement). "
        "2) Surgical bypass: hepaticojejunostomy or choledochojejunostomy. "
        "   For: benign strictures, fit patients with long life expectancy. "
        "3) Repeat ERCP at expert center: if prior ERCP failed at non-expert center."
    )

    # ─── Post-Procedure Management ────────────────────────────────────────────
    post_procedure_management = (
        "POST-PROCEDURE MANAGEMENT: "
        "IV antibiotics: ceftriaxone 1g IV x24–48h (or piperacillin-tazobactam for high-risk). "
        "LFTs at 24–48h and 1 week. "
        "CT abdomen if fever, pain, or LFT worsening (assess for bile leak, stent migration). "
        "Stent surveillance: SEMS — every 3–6 months; LAMS — remove at 4 weeks (benign) or leave for malignant. "
        "Stent occlusion: repeat EUS-BD or ERCP for stent exchange."
    )

    # ─── Adverse Event Risk ───────────────────────────────────────────────────
    adverse_event_risk = (
        "ADVERSE EVENTS (EUS-BD overall rate: 10–15%): "
        "Bile leak/peritonitis: 3–5% (most serious). "
        "Stent migration: 5–8% (LAMS higher than SEMS). "
        "Cholangitis/infection: 3–5%. "
        "Bleeding: 1–3%. "
        "Pneumoperitoneum: 2–3%. "
        "Stent occlusion (long-term): 15–25% at 6 months. "
        "EUS-BD adverse event rate is comparable to PTBD and lower than surgical bypass."
    )

    if len(next_steps) == 0:
        next_steps.append("Confirm ERCP failure documentation")
        next_steps.append("Cross-sectional imaging (CT/MRCP) for anatomy planning")
        next_steps.append("Correct coagulopathy before procedure")
        next_steps.append("Interventional endoscopy referral at expert center")
        next_steps.append("Multidisciplinary discussion (GI, surgery, IR)")

    cbd_text = f"{_fmt_num(cbd_diameter_mm)}mm" if truthy(cbd_diameter_mm) else "not measured"
    rationale = (
        f"Indication: {_underscores(indication)}. "
        f"ERCP failure reason: {_underscores(data.get('erpFailureReason'))}. "
        f"Obstruction level: {_underscores(obstruction_level)}. "
        f"CBD diameter: {cbd_text}. "
        f"Altered anatomy: {'Yes' if has_altered_anatomy else 'No'}. "
        f"Malignant: {'Yes' if has_malignant_obstruction else 'No'}."
    )

    if has_acute_cholecystitis and is_surgical_high_risk:
        primary_recommendation = "Acute cholecystitis in surgical high-risk patient: EUS-guided gallbladder drainage (EUS-GBD) with LAMS — superior to percutaneous drainage (ENDOCATCH trial)."
    elif indication == "ercp_failure" and obstruction_level == "distal_cbd":
        primary_recommendation = "ERCP failure with distal CBD obstruction: EUS-choledochoduodenostomy (EUS-CDS) is preferred approach — non-inferior to ERCP (ELEMENT trial)."
    elif has_altered_anatomy:
        primary_recommendation = "Altered anatomy (Roux-en-Y/Whipple): EUS-BD is preferred over repeat ERCP — EUS-hepaticogastrostomy or EUS-antegrade stenting."
    else:
        primary_recommendation = "Therapeutic EUS indicated: interventional endoscopy referral at expert center for EUS-guided biliary drainage."

    return {
        "primaryRecommendation": primary_recommendation,
        "eusBDApproach": eus_bd_approach,
        "stentSelection": stent_selection,
        "procedureSequence": procedure_sequence,
        "alternativeApproach": alternative_approach,
        "postProcedureManagement": post_procedure_management,
        "adverseEventRisk": adverse_event_risk,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "B",
        "rationale": rationale,
        "references": _REFERENCES,
    }
