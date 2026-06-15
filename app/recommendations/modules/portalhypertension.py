"""Portal Hypertension & Portal Vein Complications Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/portalHypertensionLogic.ts
(assessPortalHypertension).

Guidelines: Baveno VII (2022/2024), AASLD (2023/2024), EASL (2023/2024),
SIR TIPS (2024), ACG HE (2022).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, truthy

LOGIC_KEY = "portalhypertension"

_REFERENCES = [
    {
        "citation": "de Franchis R, Bosch J, Garcia-Tsao G, et al. Baveno VII — Renewing consensus in portal hypertension. J Hepatol. 2022;76(4):959-974.",
        "pmid": "35120736",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35120736/",
    },
    {
        "citation": "Baveno VII Faculty. Expanding consensus in portal hypertension: Report of the Baveno VII Consensus Workshop. J Hepatol. 2024 (Update).",
        "url": "https://www.baveno.net",
    },
    {
        "citation": "Garcia-Tsao G, Abraldes JG, Berzigotti A, Bosch J. Portal hypertensive bleeding in cirrhosis: Risk stratification, diagnosis, and management: 2016 practice guidance by the American Association for the Study of Liver Diseases. Hepatology. 2017;65(1):310-335.",
        "pmid": "27786365",
        "url": "https://pubmed.ncbi.nlm.nih.gov/27786365/",
    },
    {
        "citation": "EASL Clinical Practice Guidelines for the management of patients with decompensated cirrhosis. J Hepatol. 2018;69(2):406-460. (Updated 2023)",
        "pmid": "29653741",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29653741/",
    },
    {
        "citation": "EASL Clinical Practice Guidelines: Vascular diseases of the liver. J Hepatol. 2016;64(1):179-202. (Updated 2024)",
        "pmid": "26516032",
        "url": "https://pubmed.ncbi.nlm.nih.gov/26516032/",
    },
    {
        "citation": "Northup PG, Garcia-Pagan JC, Garcia-Tsao G, et al. Vascular Liver Disorders, Portal Vein Thrombosis, and the Coagulation System in Liver Disease: 2020 Practice Guidance by the American Association for the Study of Liver Diseases. Hepatology. 2021;73(1):366-413.",
        "pmid": "33219529",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33219529/",
    },
    {
        "citation": "Wong F, Pappas SC, Boyer TD, et al. Terlipressin plus Albumin for the Treatment of Type 1 Hepatorenal Syndrome–Acute Kidney Injury (CONFIRM Trial). N Engl J Med. 2021;384(9):818-828.",
        "pmid": "33657294",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33657294/",
    },
    {
        "citation": "Bass NM, Mullen KD, Sanyal A, et al. Rifaximin Treatment in Hepatic Encephalopathy. N Engl J Med. 2010;362(12):1071-1081.",
        "pmid": "20335583",
        "url": "https://pubmed.ncbi.nlm.nih.gov/20335583/",
    },
    {
        "citation": "Garcia-Pagán JC, Caca K, Bureau C, et al. Early Use of TIPS in Patients with Cirrhosis and Variceal Bleeding (Pre-emptive TIPS). N Engl J Med. 2010;362(25):2370-2379.",
        "pmid": "20573925",
        "url": "https://pubmed.ncbi.nlm.nih.gov/20573925/",
    },
]


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    next_steps: list[str] = []
    recommended_agents: list[str] = []

    has_active_variceal_bleeding = truthy(data.get("hasActiveVaricealBleeding"))
    has_intestinal_ischemia = truthy(data.get("hasIntestinalIschemia"))
    has_sbp = truthy(data.get("hasSBP"))
    has_prior_sbp = truthy(data.get("hasPriorSBP"))
    has_hrs = truthy(data.get("hasHRS"))
    hrs_type = data.get("hrsType")
    he_grade = data.get("heGrade")
    pvt_extent = data.get("pvtExtent")
    pvt_acuity = data.get("pvtAcuity")
    varices_grade = data.get("varicesGrade")
    ascites_grade = data.get("ascitesGrade")
    child_pugh_class = data.get("childPughClass")
    meld_category = data.get("meldCategory")
    has_cirrhosis = truthy(data.get("hasCirrhosis"))
    has_red_wale_marks = truthy(data.get("hasRedWaleMarks"))
    has_prior_variceal_bleeding = truthy(data.get("hasPriorVaricealBleeding"))
    is_on_nsbb = truthy(data.get("isOnNSBB"))
    has_prior_ebl = truthy(data.get("hasPriorEBL"))
    has_gastric_varices = truthy(data.get("hasGastricVarices"))
    has_anticoagulation_contraindication = truthy(data.get("hasAnticoagulationContraindication"))
    baveno_vii_criteria_met = truthy(data.get("bavenoVIICriteriaMet"))
    is_diuretic_refractory = truthy(data.get("isDiureticRefractory"))
    ascites_protein_low = truthy(data.get("ascitesProteinLow"))
    has_prior_he_episode = truthy(data.get("hasPriorHEEpisode"))
    is_on_rifaximin = truthy(data.get("isOnRifaximin"))
    is_transplant_candidate = truthy(data.get("isTransplantCandidate"))
    is_listed_for_transplant = truthy(data.get("isListedForTransplant"))
    has_tips_contraindication = truthy(data.get("hasTIPSContraindication"))

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if has_active_variceal_bleeding:
        urgent_flags.append(
            "ACTIVE VARICEAL BLEEDING: Airway protection (intubate if GCS ≤8 or massive bleed), IV octreotide 50mcg bolus then 25–50mcg/hr infusion, IV ceftriaxone 1g/day (7-day course), urgent upper endoscopy within 12 hours (ideally <6h). Target Hgb 7–8 g/dL (restrictive transfusion — Baveno VII Strong Recommendation). TIPS within 72h if Child-Pugh B/C or HVPG ≥20 mmHg (pre-emptive TIPS)."
        )
        next_steps.extend([
            "Urgent upper endoscopy (within 12h)",
            "IV octreotide infusion",
            "IV ceftriaxone 1g/day x7 days",
            "ICU admission",
            "Hepatology + IR + GI consult",
        ])

    if has_intestinal_ischemia:
        urgent_flags.append(
            "INTESTINAL ISCHEMIA with PVT: Emergency surgical/IR consultation required. Anticoagulation must be started immediately (LMWH or UFH). CT angiography to assess mesenteric vein involvement. Surgical resection if bowel necrosis."
        )
        next_steps.extend([
            "Emergency surgery/IR consultation",
            "CT angiography of mesenteric vessels",
            "Immediate anticoagulation",
        ])

    if has_sbp:
        urgent_flags.append(
            "SPONTANEOUS BACTERIAL PERITONITIS: IV cefotaxime 2g Q8h x5 days (or ceftriaxone 1g/day). IV albumin 1.5g/kg on day 1 + 1g/kg on day 3 (prevents HRS — SORT trial). Diagnostic paracentesis to confirm (PMN ≥250/mm³). After resolution: indefinite norfloxacin 400mg/day or TMP-SMX for secondary SBP prophylaxis."
        )
        next_steps.extend([
            "Diagnostic paracentesis (PMN count)",
            "IV cefotaxime or ceftriaxone",
            "IV albumin protocol",
        ])

    if he_grade == "grade3" or he_grade == "grade4":
        grade_label = "3" if he_grade == "grade3" else "4"
        urgent_flags.append(
            f"SEVERE HEPATIC ENCEPHALOPATHY (Grade {grade_label}): Airway protection, ICU admission. Identify and treat precipitant urgently. Lactulose via NG tube if unable to take PO. Rifaximin 550mg BID. Avoid TIPS in uncontrolled HE Grade 3–4 (absolute contraindication). Liver transplant evaluation if refractory."
        )

    if has_hrs and hrs_type == "HRS_AKI":
        urgent_flags.append(
            "HEPATORENAL SYNDROME — ACUTE (HRS-AKI): Hold nephrotoxins/diuretics. IV albumin 1g/kg/day (max 100g) x2 days. Terlipressin 0.5–2mg IV Q4–6h (preferred — CONFIRM trial) or norepinephrine 0.5–3mg/hr + albumin if terlipressin unavailable. Liver transplant evaluation urgently — HRS-AKI has 50% 30-day mortality without transplant."
        )
        next_steps.extend([
            "Hold diuretics and nephrotoxins",
            "IV albumin challenge",
            "Terlipressin or norepinephrine",
            "Urgent transplant evaluation",
        ])

    if meld_category == "very_high" and is_transplant_candidate and not is_listed_for_transplant:
        urgent_flags.append(
            "MELD ≥20: Urgent liver transplant evaluation and listing. All interventions (TIPS, anticoagulation, paracentesis) are bridges to transplant — do not delay listing."
        )

    # ─── PVT Management ───────────────────────────────────────────────────────
    pvt_management = ""
    anticoagulation_plan = ""

    if pvt_extent == "none":
        pvt_management = "No portal vein thrombosis identified. Routine surveillance per cirrhosis guidelines (6-monthly ultrasound + AFP)."
        anticoagulation_plan = "No anticoagulation indicated for PVT. Assess for other anticoagulation indications (AF, DVT, etc.) separately."
    elif pvt_extent == "cavernous_transformation":
        pvt_management = (
            "Chronic PVT with cavernous transformation: recanalization is not feasible. Focus on portal hypertension complications management. "
            "TIPS is technically challenging but may be possible via transhepatic or trans-splenic approach at experienced centers. "
            "Anticoagulation for cavernous transformation: benefit uncertain — assess on case-by-case basis (thrombophilia, progression risk)."
        )
        anticoagulation_plan = (
            "Cavernous transformation: anticoagulation does not reverse established cavernoma. "
            "Consider anticoagulation only if: active thrombophilia, progressive thrombosis, or pre-transplant (to maintain mesenteric vein patency for surgical anastomosis)."
        )
    else:
        # Acute/subacute/partial/complete PVT
        is_high_risk_pvt = (
            pvt_extent == "complete_main"
            or pvt_extent == "extending_smv"
            or pvt_acuity == "acute"
        )

        if pvt_acuity == "acute":
            pvt_management = (
                "Acute PVT (≤6 months): anticoagulation is strongly recommended — recanalization rates 40–80% with early treatment (AASLD 2024, EASL Vascular 2024). "
                "Start LMWH (enoxaparin 1mg/kg SC BID) or direct oral anticoagulant (rivaroxaban, apixaban — preferred in non-cirrhotic PVT). "
                "In cirrhosis: LMWH preferred (DOACs under-studied in Child-Pugh B/C). Treat for minimum 6 months; indefinitely if thrombophilia or recurrent."
            )
        elif pvt_acuity == "subacute":
            pvt_management = (
                "Subacute PVT (6 weeks–6 months): anticoagulation still beneficial — partial recanalization achievable. LMWH or DOAC. "
                "Reassess with Doppler ultrasound at 3 months to assess response."
            )
        else:
            pvt_management = (
                "Chronic PVT (>6 months): anticoagulation less likely to achieve recanalization but prevents progression. "
                "Weigh bleeding risk (varices) vs thrombosis progression. Baveno VII: anticoagulate if thrombophilia, pre-transplant, or progressive thrombosis."
            )

        if has_anticoagulation_contraindication:
            pvt_management += (
                " ANTICOAGULATION CONTRAINDICATED: Consider TIPS if anatomy permits (TIPS creates portosystemic shunt, reduces portal pressure, and may allow recanalization). Discuss risks/benefits with multidisciplinary team."
            )

        if has_anticoagulation_contraindication:
            anticoagulation_plan = "Anticoagulation contraindicated. Evaluate TIPS candidacy. Multidisciplinary review required."
        elif has_cirrhosis and (child_pugh_class == "B" or child_pugh_class == "C"):
            anticoagulation_plan = (
                "Cirrhotic PVT (Child-Pugh B/C): LMWH enoxaparin 1mg/kg SC BID preferred over DOACs (limited data in decompensated cirrhosis). "
                "Monitor anti-Xa levels. Transition to warfarin (INR 2–3) or rivaroxaban 15mg BID if stable. Duration: minimum 6 months, reassess at 3 months with Doppler."
            )
        else:
            anticoagulation_plan = (
                "Non-cirrhotic or compensated cirrhotic PVT: rivaroxaban 15mg BID x21 days then 20mg/day (DOAC preferred — AASLD 2024) or apixaban 10mg BID x7 days then 5mg BID. "
                "Thrombophilia workup: JAK2 V617F, antiphospholipid antibody, factor V Leiden, prothrombin G20210A, protein C/S, antithrombin. Duration: minimum 6 months; indefinitely if thrombophilia confirmed."
            )

        if is_high_risk_pvt:
            recommended_agents.extend([
                "Enoxaparin 1mg/kg SC BID (preferred in Child-Pugh B/C cirrhosis)",
                "Rivaroxaban 15mg BID x21 days then 20mg/day (non-cirrhotic or compensated)",
                "Apixaban 10mg BID x7 days then 5mg BID (alternative DOAC)",
            ])

    # ─── Varices — Primary Prophylaxis ────────────────────────────────────────
    varices_prophylaxis = ""

    if varices_grade == "none" or varices_grade == "small":
        if baveno_vii_criteria_met:
            varices_prophylaxis = (
                "Baveno VII criteria met (LSM <20 kPa + platelets >150k): varices unlikely to be clinically significant. "
                "Endoscopy can be safely avoided. Repeat non-invasive assessment in 2 years (or annually if ongoing liver injury)."
            )
        elif varices_grade == "small" and not has_red_wale_marks and child_pugh_class == "A":
            varices_prophylaxis = (
                "Small varices without red wale marks in Child-Pugh A: NSBB (carvedilol 6.25mg/day, titrate to 12.5mg/day) or surveillance endoscopy every 1–2 years. "
                "Baveno VII: carvedilol preferred over propranolol (superior portal pressure reduction). No EBL for small varices."
            )
            recommended_agents.append("Carvedilol 6.25mg/day → 12.5mg/day (preferred NSBB — Baveno VII)")
        else:
            varices_prophylaxis = (
                "No varices or small varices: surveillance upper endoscopy every 2–3 years (compensated cirrhosis) or every 1–2 years (decompensated). "
                "Non-invasive alternatives: Baveno VII criteria, platelet count + LSM algorithm."
            )
    elif varices_grade == "medium" or varices_grade == "large" or has_red_wale_marks:
        varices_prophylaxis = (
            "Medium/large varices or high-risk stigmata (red wale marks): primary prophylaxis REQUIRED. "
            "Option 1: Non-selective beta-blocker — carvedilol 6.25mg/day (preferred) or propranolol 20mg BID titrated to HR 55–60 bpm or max tolerated dose. "
            "Option 2: Endoscopic band ligation (EBL) every 2–4 weeks until eradication — equivalent to NSBB but requires repeated endoscopy. "
            "Baveno VII: NSBB preferred over EBL as first-line (avoids procedural risk, systemic benefits including reduced bacterial translocation). "
            "NSBB + EBL combination: NOT recommended for primary prophylaxis (no added benefit, increased adverse events)."
        )
        recommended_agents.extend([
            "Carvedilol 6.25mg/day → 12.5mg/day (preferred NSBB for primary prophylaxis)",
            "Propranolol 20mg BID → titrate to HR 55–60 bpm (alternative NSBB)",
            "Nadolol 40mg/day (alternative — once daily dosing)",
        ])
    elif varices_grade == "not_screened":
        varices_prophylaxis = (
            "Varices not screened: upper endoscopy required. Apply Baveno VII non-invasive criteria first: "
            "if LSM <20 kPa AND platelets >150k → endoscopy can be safely avoided. Otherwise, perform EGD."
        )
        next_steps.append("Upper endoscopy for variceal screening (or apply Baveno VII criteria)")

    # ─── Acute Variceal Bleed Management ──────────────────────────────────────
    acute_bleed_management = ""

    if has_active_variceal_bleeding or has_prior_variceal_bleeding:
        acute_bleed_management = (
            "ACUTE VARICEAL BLEED PROTOCOL (Baveno VII 2022 + AASLD 2024):\n"
            "1. RESUSCITATION: Restrictive transfusion (Hgb target 7–8 g/dL — TRANSFUSE trial). Avoid over-transfusion (worsens portal pressure). Correct coagulopathy cautiously (INR is unreliable in cirrhosis).\n"
            "2. VASOACTIVE THERAPY: IV octreotide 50mcg bolus then 25–50mcg/hr x5 days (or terlipressin 2mg Q4h x48h then 1mg Q4h — superior to octreotide, not available in all countries).\n"
            "3. ANTIBIOTICS: IV ceftriaxone 1g/day x7 days (reduces bacterial infections, rebleeding, and mortality — Baveno VII Strong Recommendation).\n"
            "4. ENDOSCOPY: Within 12 hours (ideally <6h in unstable patients). EBL is first-line for esophageal varices. Tissue adhesive (cyanoacrylate) for gastric varices (GOV2/IGV1).\n"
            "5. PRE-EMPTIVE TIPS: Within 72 hours if Child-Pugh B (active bleeding at endoscopy) or Child-Pugh C (score ≤13) or HVPG ≥20 mmHg — reduces 6-week mortality (NEJM 2010, Baveno VII Strong Recommendation).\n"
            "6. BALLOON TAMPONADE: Sengstaken-Blakemore tube as BRIDGE only (max 24h) if endoscopy unavailable or failed — not definitive therapy."
        )

        if has_gastric_varices:
            acute_bleed_management += (
                "\n\nGASTRIC VARICES (Baveno VII):\n"
                "• GOV1 (extension of esophageal varices along lesser curve): EBL + cyanoacrylate injection.\n"
                "• GOV2 (extension along greater curve) / IGV1 (isolated fundal): Cyanoacrylate injection preferred. BRTO (balloon-occluded retrograde transvenous obliteration) if gastrorenal shunt present — superior to TIPS for GOV2/IGV1 (BRTO trial). TIPS if no gastrorenal shunt or refractory."
            )

        recommended_agents.extend([
            "Octreotide 50mcg IV bolus then 25–50mcg/hr x5 days",
            "Terlipressin 2mg IV Q4h x48h then 1mg Q4h (if available)",
            "Ceftriaxone 1g IV/day x7 days",
            "Cyanoacrylate (gastric varices — GOV2/IGV1)",
            "Carvedilol or propranolol (secondary prophylaxis after bleed control)",
        ])

    # ─── Secondary Prophylaxis ────────────────────────────────────────────────
    secondary_prophylaxis = ""

    if has_prior_variceal_bleeding:
        secondary_prophylaxis = (
            "Secondary prophylaxis (prevention of re-bleed) — Baveno VII Strong Recommendation:\n"
            "• NSBB + EBL COMBINATION is standard of care (superior to either alone — Baveno VII).\n"
            "• Start NSBB within 5 days of bleed (carvedilol 6.25mg/day → 12.5mg/day preferred; propranolol 20mg BID alternative).\n"
            "• EBL every 2–4 weeks until variceal eradication, then endoscopy at 1–3 months, then every 6–12 months.\n"
            "• TIPS for secondary prophylaxis: indicated if NSBB + EBL fails (rebleeding despite optimal medical/endoscopic therapy). TIPS reduces rebleeding to <10% vs ~30% with NSBB + EBL.\n"
            "• Gastric varices (GOV2/IGV1): BRTO preferred if gastrorenal shunt present; TIPS if no shunt or refractory."
        )

        if not is_on_nsbb:
            next_steps.append("Start carvedilol 6.25mg/day for secondary prophylaxis")
        if not has_prior_ebl:
            next_steps.append("Schedule EBL for variceal eradication (secondary prophylaxis)")

    # ─── Ascites Management ───────────────────────────────────────────────────
    ascites_management = ""
    sbp_prophylaxis = ""

    if ascites_grade == "none":
        ascites_management = "No ascites. Maintain low-sodium diet (<2g/day). Monitor with 6-monthly ultrasound. NSBB for portal hypertension if varices present."
    elif ascites_grade == "grade1":
        ascites_management = (
            "Grade 1 ascites (detectable by ultrasound only): sodium restriction (<2g/day). "
            "Low-dose spironolactone 50–100mg/day. Avoid NSAIDs, aminoglycosides, ACE inhibitors. "
            "Monitor renal function and electrolytes every 2–4 weeks."
        )
        recommended_agents.append("Spironolactone 50–100mg/day (start low, titrate)")
    elif ascites_grade == "grade2":
        ascites_management = (
            "Grade 2 ascites (moderate): sodium restriction + diuretics. "
            "Spironolactone 100mg/day + furosemide 40mg/day (5:2 ratio — EASL guideline). "
            "Titrate every 3–5 days: max spironolactone 400mg/day + furosemide 160mg/day. "
            "Target weight loss: 0.5kg/day (no peripheral edema) or 1kg/day (with peripheral edema). "
            "Avoid hyponatremia (Na <125 mEq/L → hold diuretics). Avoid renal impairment (Cr increase >2mg/dL → hold diuretics)."
        )
        recommended_agents.extend([
            "Spironolactone 100mg/day + furosemide 40mg/day (5:2 ratio)",
            "Titrate to spironolactone 400mg + furosemide 160mg/day max",
        ])
    elif ascites_grade == "grade3":
        ascites_management = (
            "Grade 3 (tense) ascites: large-volume paracentesis (LVP) — remove all ascites in single session. "
            "IV albumin 6–8g per liter removed (prevents post-paracentesis circulatory dysfunction — PPCD). "
            "After LVP: restart diuretics at lower dose. "
            "If recurrent tense ascites: consider TIPS (Child-Pugh ≤11, MELD <15, no HE) — TIPS superior to LVP for refractory ascites (CONFIRM trial). "
            "Sodium restriction <2g/day. Avoid nephrotoxins."
        )
        recommended_agents.extend([
            "IV albumin 6–8g per liter of ascites removed (PPCD prevention)",
            "Spironolactone + furosemide after LVP (restart at lower dose)",
        ])
        next_steps.append("Large-volume paracentesis with IV albumin replacement")
    elif ascites_grade == "refractory":
        ascites_management = (
            "REFRACTORY ASCITES (failed spironolactone 400mg + furosemide 160mg, or diuretic-intolerant):\n"
            "• TIPS (transjugular intrahepatic portosystemic shunt): first-line for refractory ascites in eligible patients. "
            "Criteria: Child-Pugh ≤11, MELD <18–20, no HE Grade ≥2, no severe cardiopulmonary disease. "
            "TIPS reduces portal pressure, controls ascites in 70–80%, improves survival vs LVP (meta-analysis). "
            "• Serial LVP + albumin: for patients not eligible for TIPS. Every 2–4 weeks. "
            "• Tolvaptan (V2 receptor antagonist): for hyponatremic ascites (Na <130 mEq/L) — short-term use only (hepatotoxicity risk). "
            "• Alfapump (automated low-flow ascites pump): investigational — POSEIDON trial ongoing. "
            "• Liver transplant evaluation: refractory ascites is a decompensation event — MELD exception points may apply."
        )
        next_steps.extend([
            "TIPS evaluation (IR consultation)",
            "Liver transplant evaluation",
        ])
        recommended_agents.extend([
            "IV albumin 6–8g/L removed (serial LVP)",
            "Tolvaptan 15mg/day (hyponatremia — short-term only)",
        ])

    # SBP Prophylaxis
    if has_prior_sbp or ascites_protein_low or meld_category == "very_high":
        sbp_prophylaxis = (
            "SBP PROPHYLAXIS INDICATED (EASL 2023 / AASLD 2024):\n"
            "• Prior SBP: norfloxacin 400mg/day indefinitely (or TMP-SMX DS daily as alternative).\n"
            "• Ascitic protein <1.5g/dL + Child-Pugh ≥9 or bilirubin ≥3 or renal impairment: norfloxacin 400mg/day.\n"
            "• Acute variceal bleed: ceftriaxone 1g/day x7 days (covers SBP prevention during bleed episode).\n"
            "• IV albumin: 1.5g/kg day 1 + 1g/kg day 3 during SBP episode (prevents HRS — SORT trial)."
        )
        recommended_agents.extend([
            "Norfloxacin 400mg/day (primary SBP prophylaxis)",
            "TMP-SMX DS daily (alternative to norfloxacin)",
        ])
    else:
        sbp_prophylaxis = "No current SBP prophylaxis indication. Reassess if ascites protein <1.5g/dL, prior SBP, or MELD ≥20."

    # ─── Hepatic Encephalopathy ───────────────────────────────────────────────
    he_management = ""

    if he_grade == "none" and not has_prior_he_episode:
        he_management = "No hepatic encephalopathy. Covert HE screening with psychometric tests (EncephalApp Stroop, PHES) recommended in cirrhotic patients — affects driving and quality of life."
    elif he_grade == "minimal" or he_grade == "grade1":
        he_management = (
            "Covert/Minimal HE (Grade 1): lactulose 15–30mL BID–TID (titrate to 2–3 soft stools/day). "
            "Rifaximin 550mg BID if lactulose intolerant or recurrent HE. "
            "Identify and correct precipitants: infection, GI bleed, constipation, electrolyte disturbance, benzodiazepines/opioids. "
            "Driving restriction counseling. Nutritional support (1.2–1.5g/kg/day protein — do NOT restrict protein in HE)."
        )
        recommended_agents.extend([
            "Lactulose 15–30mL BID–TID (titrate to 2–3 soft stools/day)",
            "Rifaximin 550mg BID (recurrent HE or lactulose intolerant)",
        ])
    elif he_grade == "grade2":
        he_management = (
            "Overt HE (Grade 2): lactulose 30–45mL Q1–2h until bowel movement, then TID maintenance. "
            "Rifaximin 550mg BID (add to lactulose for recurrent HE — reduces hospitalizations 58% — NEJM 2010). "
            "Identify and treat precipitant urgently. "
            "Zinc supplementation (zinc deficiency common in cirrhosis). "
            "TIPS contraindicated if uncontrolled HE — assess HE before TIPS."
        )
        recommended_agents.extend([
            "Lactulose 30–45mL Q1–2h (acute), then TID maintenance",
            "Rifaximin 550mg BID (add for recurrent HE)",
            "Zinc acetate 50mg BID (adjunct)",
        ])
    elif he_grade == "grade3" or he_grade == "grade4":
        he_management = (
            "Severe HE (Grade 3–4): ICU admission, airway protection (intubate if GCS ≤8). "
            "Lactulose via NG tube (30mL Q2h until bowel movement). "
            "Rifaximin 550mg BID via NG. "
            "Identify precipitant (infection most common — blood cultures, urine culture, diagnostic paracentesis). "
            "Avoid sedatives/benzodiazepines. "
            "Liver transplant evaluation — severe refractory HE is a transplant indication. "
            "TIPS is CONTRAINDICATED in HE Grade 3–4 (absolute contraindication — worsens HE)."
        )

    if has_prior_he_episode and not is_on_rifaximin:
        next_steps.append("Start rifaximin 550mg BID for secondary HE prophylaxis (reduces recurrence 58%)")
        recommended_agents.append("Rifaximin 550mg BID (secondary HE prophylaxis)")

    # ─── HRS Management ───────────────────────────────────────────────────────
    hrs_management = ""

    if not has_hrs:
        hrs_management = "No HRS identified. Monitor renal function closely — AKI in cirrhosis is common (infections, diuretics, NSAIDs). Avoid nephrotoxins. Albumin infusion during SBP and large-volume paracentesis."
    elif hrs_type == "HRS_AKI":
        hrs_management = (
            "HRS-AKI (Hepatorenal Syndrome — Acute Kidney Injury):\n"
            "• STOP diuretics, NSAIDs, nephrotoxins, beta-blockers.\n"
            "• IV albumin 1g/kg/day (max 100g) x2 days (volume expansion challenge).\n"
            "• If no response: terlipressin 0.5mg IV Q4h → titrate to 2mg Q4h (CONFIRM trial: 32% HRS reversal vs 17% placebo). "
            "Terlipressin FDA-approved 2022 for HRS-AKI.\n"
            "• Alternative if terlipressin unavailable: norepinephrine 0.5–3mg/hr IV + albumin 20–40g/day.\n"
            "• Midodrine 7.5mg TID + octreotide 100–200mcg SC TID + albumin: outpatient option if terlipressin/NE unavailable.\n"
            "• Liver transplant is the only definitive treatment — urgent evaluation required.\n"
            "• TIPS as bridge to transplant: may improve renal function in HRS but limited data."
        )
        recommended_agents.extend([
            "Terlipressin 0.5–2mg IV Q4h (FDA-approved 2022 — CONFIRM trial)",
            "Norepinephrine 0.5–3mg/hr IV + albumin (if terlipressin unavailable)",
            "IV albumin 1g/kg/day x2 days (volume challenge)",
            "Midodrine 7.5mg TID + octreotide 100–200mcg SC TID (outpatient alternative)",
        ])
    else:
        hrs_management = (
            "HRS-CKD (Chronic Kidney Disease in cirrhosis): "
            "Optimize fluid status, avoid nephrotoxins. Renal replacement therapy as bridge to liver transplant. "
            "Simultaneous liver-kidney transplant (SLK) if CKD ≥90 days or GFR <25 mL/min — UNOS criteria."
        )

    # ─── TIPS Assessment ──────────────────────────────────────────────────────
    tips_contras = data.get("tipsContraindications") or []
    has_he_contraindication = (
        includes(tips_contras, "he_grade3_4")
        or he_grade == "grade3"
        or he_grade == "grade4"
    )

    tips_indication_list: list[str] = []
    if has_active_variceal_bleeding and (child_pugh_class == "B" or child_pugh_class == "C"):
        tips_indication_list.append("Pre-emptive TIPS (within 72h) — acute variceal bleed in Child-Pugh B/C")
    if has_prior_variceal_bleeding and is_on_nsbb and has_prior_ebl:
        tips_indication_list.append("Secondary prophylaxis TIPS — rebleeding despite NSBB + EBL")
    if ascites_grade == "refractory" or is_diuretic_refractory:
        tips_indication_list.append("Refractory ascites — TIPS preferred over serial LVP (if MELD <18–20)")
    if (
        pvt_extent != "none"
        and pvt_extent != "cavernous_transformation"
        and has_anticoagulation_contraindication
    ):
        tips_indication_list.append("PVT with anticoagulation contraindication — TIPS for portal decompression")
    if has_hrs and hrs_type == "HRS_AKI":
        tips_indication_list.append("HRS-AKI — TIPS as bridge to transplant (limited evidence, case-by-case)")

    if tips_indication_list:
        tips_indication = "TIPS INDICATIONS IDENTIFIED:\n" + "\n".join(
            f"{i + 1}) {t}" for i, t in enumerate(tips_indication_list)
        )
    else:
        tips_indication = "No current TIPS indication. Reassess if refractory ascites, rebleeding despite NSBB + EBL, or pre-emptive TIPS criteria met."

    contra_list: list[str] = []
    if has_he_contraindication:
        contra_list.append("Uncontrolled HE Grade 3–4 (absolute contraindication)")
    if includes(tips_contras, "heart_failure"):
        contra_list.append("Congestive heart failure (TIPS increases right heart preload)")
    if includes(tips_contras, "severe_pulmonary_htn"):
        contra_list.append("Severe pulmonary arterial hypertension (mean PAP >45 mmHg)")
    if includes(tips_contras, "uncontrolled_infection"):
        contra_list.append("Uncontrolled systemic infection / sepsis")
    if includes(tips_contras, "biliary_obstruction"):
        contra_list.append("Biliary obstruction (relative — may worsen biliary-venous fistula)")
    if child_pugh_class == "C" and meld_category == "very_high":
        contra_list.append("Child-Pugh C + MELD ≥20: high procedural mortality — transplant preferred over TIPS")

    if contra_list:
        tips_contraindication_assessment = (
            "TIPS CONTRAINDICATIONS PRESENT:\n"
            + "\n".join(f"{i + 1}) {c}" for i, c in enumerate(contra_list))
            + "\n\nReview contraindications with hepatology + IR. Transplant evaluation should be prioritized."
        )
    else:
        tips_contraindication_assessment = "No absolute TIPS contraindications identified. Proceed with hepatology + IR evaluation if TIPS indicated."

    # ─── Transplant Consideration ─────────────────────────────────────────────
    transplant_consideration = ""
    transplant_indicators: list[str] = []

    if meld_category == "very_high":
        transplant_indicators.append("MELD ≥20")
    if ascites_grade == "refractory":
        transplant_indicators.append("Refractory ascites")
    if has_prior_variceal_bleeding:
        transplant_indicators.append("Prior variceal hemorrhage")
    if has_prior_he_episode:
        transplant_indicators.append("Prior hepatic encephalopathy episode")
    if has_sbp or has_prior_sbp:
        transplant_indicators.append("Spontaneous bacterial peritonitis")
    if has_hrs:
        transplant_indicators.append("Hepatorenal syndrome")

    if transplant_indicators:
        transplant_consideration = (
            "LIVER TRANSPLANT EVALUATION RECOMMENDED:\n"
            "Decompensation events present: " + ", ".join(transplant_indicators) + ".\n"
            "Refer to transplant center. MELD-Na score determines listing priority. "
            "All interventions (TIPS, anticoagulation, paracentesis) are bridges to transplant — do not delay evaluation."
        )
        if is_transplant_candidate and not is_listed_for_transplant:
            next_steps.append("Urgent liver transplant evaluation and listing")
    else:
        transplant_consideration = (
            "No current decompensation events. Maintain surveillance per compensated cirrhosis guidelines. "
            "Reassess transplant candidacy if decompensation occurs."
        )

    # ─── Monitoring Plan ──────────────────────────────────────────────────────
    monitoring_plan = (
        "PORTAL HYPERTENSION MONITORING (Baveno VII / AASLD 2024):\n"
        "• Ultrasound + AFP: every 6 months (HCC surveillance in cirrhosis).\n"
        "• Doppler ultrasound of portal vein: every 3–6 months if PVT present (assess recanalization).\n"
        "• Upper endoscopy: per variceal grade (see above). Baveno VII: non-invasive criteria can replace endoscopy in low-risk patients.\n"
        "• Renal function + electrolytes: every 1–3 months (diuretics, HRS risk).\n"
        "• Serum sodium: monitor closely — hyponatremia (Na <130) is a MELD-Na component and transplant indicator.\n"
        "• MELD-Na: reassess every 3–6 months (or more frequently if decompensating).\n"
        "• Nutritional assessment: DEXA scan for sarcopenia (common in cirrhosis — worsens prognosis). Target 1.2–1.5g/kg/day protein."
    )

    # ─── Primary Recommendation ───────────────────────────────────────────────
    if has_active_variceal_bleeding:
        primary_recommendation = "ACUTE VARICEAL HEMORRHAGE: Activate variceal bleed protocol — octreotide + ceftriaxone + urgent endoscopy (EBL). Pre-emptive TIPS within 72h if Child-Pugh B/C (Baveno VII Strong Recommendation)."
    elif has_intestinal_ischemia:
        primary_recommendation = "INTESTINAL ISCHEMIA with PVT: Emergency anticoagulation + surgical/IR consultation. CT angiography of mesenteric vessels."
    elif has_sbp:
        primary_recommendation = "SPONTANEOUS BACTERIAL PERITONITIS: IV cefotaxime/ceftriaxone + IV albumin protocol (SORT trial). Initiate long-term SBP prophylaxis after resolution."
    elif has_hrs and hrs_type == "HRS_AKI":
        primary_recommendation = "HRS-AKI: Hold diuretics/nephrotoxins, IV albumin challenge, terlipressin (FDA-approved 2022). Urgent liver transplant evaluation."
    elif he_grade == "grade3" or he_grade == "grade4":
        primary_recommendation = "SEVERE HEPATIC ENCEPHALOPATHY (Grade 3–4): ICU, airway protection, lactulose via NG, rifaximin. TIPS contraindicated. Transplant evaluation."
    elif pvt_extent != "none" and pvt_extent != "cavernous_transformation" and pvt_acuity == "acute":
        primary_recommendation = "ACUTE PVT: Anticoagulation (LMWH or DOAC) — start immediately. 40–80% recanalization with early treatment (AASLD 2024). Thrombophilia workup."
    elif ascites_grade == "refractory" or is_diuretic_refractory:
        primary_recommendation = "REFRACTORY ASCITES: TIPS evaluation (if MELD <18–20, no HE) — superior to serial LVP. Serial LVP + albumin if TIPS not feasible. Transplant evaluation."
    elif varices_grade == "large" or has_red_wale_marks:
        primary_recommendation = "HIGH-RISK VARICES: Primary prophylaxis with carvedilol (Baveno VII preferred) or EBL. Target HR 55–60 bpm on NSBB."
    else:
        primary_recommendation = "Portal hypertension management: individualized approach based on Baveno VII framework. Assess varices, ascites, PVT, and HE systematically."

    # ─── Evidence Level ───────────────────────────────────────────────────────
    if has_active_variceal_bleeding or has_sbp or has_hrs:
        evidence_level = "A"
    elif ascites_grade != "none" or pvt_extent != "none":
        evidence_level = "A"
    else:
        evidence_level = "B"

    # ─── Rationale ────────────────────────────────────────────────────────────
    primary_scenario = data.get("primaryScenario") or ""
    cirrhosis_str = (
        f"Yes (Child-Pugh {child_pugh_class}, MELD {meld_category})"
        if has_cirrhosis
        else "No"
    )
    rationale = (
        f"Clinical scenario: {str(primary_scenario).replace('_', ' ')}. "
        f"Cirrhosis: {cirrhosis_str}. "
        f"PVT: {str(pvt_extent).replace('_', ' ')} ({pvt_acuity}). "
        f"Varices: {varices_grade}{' + red wale marks' if has_red_wale_marks else ''}. "
        f"Ascites: {ascites_grade}. "
        f"HE: Grade {he_grade}. "
        f"TIPS candidate: {'No (contraindication)' if has_tips_contraindication else 'Evaluate'}. "
        f"Transplant listed: {'Yes' if is_listed_for_transplant else 'No'}."
    )

    return {
        "primaryRecommendation": primary_recommendation,
        "pvtManagement": pvt_management,
        "anticoagulationPlan": anticoagulation_plan,
        "varicesProphylaxis": varices_prophylaxis,
        "acuteBleedManagement": acute_bleed_management,
        "secondaryProphylaxis": secondary_prophylaxis,
        "ascitesManagement": ascites_management,
        "sbpProphylaxis": sbp_prophylaxis,
        "heManagement": he_management,
        "hrsManagement": hrs_management,
        "tipsIndication": tips_indication,
        "tipsContraindicationAssessment": tips_contraindication_assessment,
        "transplantConsideration": transplant_consideration,
        "monitoringPlan": monitoring_plan,
        "urgentFlags": urgent_flags,
        "recommendedAgents": recommended_agents,
        "nextSteps": next_steps,
        "evidenceLevel": evidence_level,
        "rationale": rationale,
        "references": _REFERENCES,
    }
