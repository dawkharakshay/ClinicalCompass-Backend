"""Chronic Pancreatitis Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/chronicPancreatitisLogic.ts
(assessChronicPancreatitis).
"""

from __future__ import annotations

from app.recommendations.jslib import coalesce

LOGIC_KEY = "chronicpancreatitis"

_REFERENCES = [
    {
        "citation": "Löhr JM, et al. United European Gastroenterology Evidence-Based Guidelines for the Diagnosis and Therapy of Chronic Pancreatitis. United European Gastroenterol J. 2017;5(2):153-199.",
        "pmid": "28344786",
        "url": "https://pubmed.ncbi.nlm.nih.gov/28344786/",
    },
    {
        "citation": "Issa Y, et al. Effect of Early Surgery vs Endoscopy-First Approach on Pain in Patients with Chronic Pancreatitis (ESCAPE). JAMA. 2020;323(3):237-247.",
        "pmid": "31961409",
        "url": "https://pubmed.ncbi.nlm.nih.gov/31961409/",
    },
    {
        "citation": "Dumonceau JM, et al. Endoscopic Treatment of Chronic Pancreatitis: European Society of Gastrointestinal Endoscopy (ESGE) Guideline. Endoscopy. 2023;55(12):1124-1145.",
        "pmid": "37797618",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37797618/",
    },
    {
        "citation": "Gardner TB, et al. ACG Clinical Guideline: Chronic Pancreatitis. Am J Gastroenterol. 2020;115(3):322-339.",
        "pmid": "32022720",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32022720/",
    },
]


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    next_steps: list[str] = []

    igg4_level = data.get("igg4Level")
    pseudocyst_size = data.get("pseudocystSizeCm")
    pseudocyst_symptoms = data.get("pseudocystSymptoms")
    duct_anatomy = data.get("ductAnatomy")

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if data.get("suspectedMalignancy"):
        urgent_flags.append(
            "Suspected malignancy in chronic pancreatitis: EUS-FNB + CT staging required — pancreatic cancer risk 13x higher in CP. Multidisciplinary tumor board review."
        )
    if data.get("hasPseudocyst") and pseudocyst_symptoms == "infected":
        urgent_flags.append(
            "Infected pancreatic pseudocyst: IV antibiotics + urgent drainage (EUS-guided preferred) — risk of sepsis"
        )
    if data.get("hasDuodenalObstruction"):
        urgent_flags.append(
            "Duodenal obstruction: surgical or endoscopic bypass required — gastrojejunostomy or EUS-guided gastroenterostomy"
        )
    if data.get("hasBiliaryStenosis"):
        urgent_flags.append(
            "Biliary stenosis in CP: ERCP with SEMS placement or surgical biliary bypass — monitor for secondary biliary cirrhosis"
        )
    if data.get("hasSplenicVeinThrombosis"):
        urgent_flags.append(
            "Splenic vein thrombosis: risk of gastric varices and bleeding — anticoagulation discussion + splenectomy if bleeding"
        )
    if igg4_level is not None and igg4_level > 135:
        urgent_flags.append(
            f"IgG4 {igg4_level} mg/dL (>135): autoimmune pancreatitis type 1 — trial of prednisone 40mg/day x4 weeks before invasive intervention"
        )
        next_steps.append("Prednisone 40mg/day x4 weeks (autoimmune pancreatitis type 1)")
        next_steps.append("Repeat imaging after steroid trial")

    # ─── Pain Management ──────────────────────────────────────────────────────
    pain_management = (
        "PAIN MANAGEMENT (APA/IAP 2024 — stepwise approach): "
        "1) LIFESTYLE: alcohol and smoking cessation — most important modifiable factors. "
        "   Smoking cessation reduces pain and slows disease progression. "
        "2) ANALGESICS: "
        "   Step 1: Non-opioid (acetaminophen, NSAIDs — caution with renal function). "
        "   Step 2: Weak opioids (tramadol, codeine). "
        "   Step 3: Strong opioids (oxycodone, morphine) — last resort; risk of addiction. "
        "3) ADJUVANT: "
        "   Pregabalin/gabapentin: neuropathic pain component. "
        "   Antidepressants (duloxetine, amitriptyline): central sensitization. "
        "   Pancreatic enzyme replacement (PERT): may reduce pain via CCK feedback (controversial). "
        "4) ENDOSCOPIC/INTERVENTIONAL: "
        "   EUS-guided celiac plexus block: short-term pain relief (3–6 months). "
        "   Endoscopic pancreatic duct decompression: for obstructive pain. "
    )
    if data.get("isOnOpioids"):
        pain_management += (
            f"Current opioid dose: {coalesce(data.get('opioidDoseEquivalent'), 'unknown')} MME/day. "
            "Consider opioid rotation or pain specialist referral. "
        )

    # ─── Endoscopic Therapy ───────────────────────────────────────────────────
    is_endoscopic_candidate = duct_anatomy in (
        "dilated_with_stricture",
        "stones_with_stricture",
        "stones_without_stricture",
        "dilated_without_stricture",
    )

    if is_endoscopic_candidate:
        endoscopic_therapy = (
            "ENDOSCOPIC THERAPY (ASGE 2024 / ESGE 2023): "
            "1) ERCP + PANCREATIC DUCT STENTING: "
            "   Indication: dominant stricture with upstream MPD dilation (≥5mm). "
            "   Technique: sphincterotomy + stricture dilation + plastic stent (7–10Fr). "
            "   Multiple plastic stents (ESGE 2023): superior to single stent — 3–4 stents side-by-side. "
            "   Stent exchange every 3–6 months x12 months → assess for stricture resolution. "
            "   Fully covered SEMS (FCSEMS): emerging — better stricture resolution than multiple plastic stents (RESPONDER trial). "
            "2) ESWL (Extracorporeal Shock Wave Lithotripsy): "
            "   Indication: pancreatic duct stones >5mm preventing endoscopic clearance. "
            "   Fragmentation of stones → ERCP for clearance. "
            "   ESWL + ERCP: 70–80% stone clearance. "
            "   ESWL alone: effective for fragmentation without subsequent ERCP in select cases. "
            "3) PANCREATOSCOPY (SpyGlass): "
            "   Direct visualization of duct + laser/EHL lithotripsy for refractory stones. "
            "   Reserved for stones not amenable to ESWL. "
            "4) EUS-GUIDED CELIAC PLEXUS BLOCK: "
            "   Short-term pain relief (3–6 months). "
            "   Repeat as needed. Less effective than in pancreatic cancer."
        )
        next_steps.append("ERCP with pancreatic sphincterotomy and stent placement")
        next_steps.append("ESWL if stones >5mm preventing endoscopic access")
    elif duct_anatomy == "divisum":
        endoscopic_therapy = (
            "PANCREAS DIVISUM (ASGE 2024): "
            "Minor papilla sphincterotomy + dorsal duct stenting for symptomatic divisum. "
            "Technical success: 80–90%. Clinical success: 50–70%. "
            "Surgical minor papilla sphincteroplasty if endoscopic therapy fails."
        )
        next_steps.append("Minor papilla sphincterotomy + dorsal duct stenting")
    elif duct_anatomy == "disrupted_duct":
        endoscopic_therapy = (
            "DISCONNECTED PANCREATIC DUCT SYNDROME (DPDS): "
            "Transmural drainage (EUS-guided) with LAMS — creates fistula for sustained drainage. "
            "Transpapillary stenting (ERCP) if duct continuity preserved. "
            "Surgical resection for refractory DPDS."
        )
        next_steps.append("EUS-guided transmural drainage with LAMS for disconnected duct syndrome")
    else:
        endoscopic_therapy = (
            "Endoscopic therapy not indicated for current duct anatomy. "
            "Medical management and lifestyle modification are the focus. "
            "Reassess if pain worsens or duct anatomy changes."
        )

    # ─── Surgical Consideration ───────────────────────────────────────────────
    if data.get("isSurgicalCandidate"):
        surgical_consideration = (
            "SURGICAL OPTIONS (APA/IAP 2024 — surgery superior to endoscopy for long-term pain relief): "
            "1) LATERAL PANCREATICOJEJUNOSTOMY (Puestow/Partington-Rochelle): "
            "   Indication: dilated MPD ≥7mm without dominant head mass. "
            "   Long-term pain relief: 70–80% at 5 years. "
            "   ESCAPE trial (2020): surgery superior to endoscopy for pain at 18 months. "
            "2) DUODENUM-PRESERVING PANCREATIC HEAD RESECTION (Frey/Beger): "
            '   Indication: inflammatory head mass ("head of the worm") + dilated duct. '
            "   Preserves duodenum — lower morbidity than Whipple. "
            "3) PANCREATICODUODENECTOMY (Whipple): "
            "   Indication: cannot exclude malignancy, dominant head mass, failed Frey/Beger. "
            "4) TOTAL PANCREATECTOMY + ISLET AUTOTRANSPLANTATION (TP-IAT): "
            "   Indication: hereditary/genetic CP, refractory pain, failed all other interventions. "
            "   Preserves insulin secretion (islet autotransplantation). "
            "   Best outcomes when performed before diabetes develops."
        )
        if not data.get("hasPriorEndoscopicDrainage") or data.get("endoscopicDrainageResponse") == "none":
            next_steps.append(
                "Surgical consultation for lateral pancreaticojejunostomy (Puestow) or Frey procedure"
            )
    else:
        surgical_consideration = (
            "Patient not surgical candidate — optimize endoscopic and medical management. "
            "Reassess surgical candidacy after optimization."
        )

    # ─── Pseudocyst Management ────────────────────────────────────────────────
    pseudocyst_management = "No pseudocyst identified."
    if data.get("hasPseudocyst"):
        if pseudocyst_symptoms == "none" and (pseudocyst_size is None or pseudocyst_size < 6):
            pseudocyst_management = (
                "Asymptomatic pseudocyst <6cm: observation. "
                "MRI/MRCP every 3–6 months. "
                "Many resolve spontaneously (30–40% within 6 weeks)."
            )
        elif pseudocyst_symptoms != "none" or (pseudocyst_size is not None and pseudocyst_size >= 6):
            pseudocyst_management = (
                "Symptomatic or large (≥6cm) pseudocyst: drainage indicated. "
                "1) EUS-GUIDED TRANSMURAL DRAINAGE (preferred): "
                "   LAMS (Hot AXIOS) or double-pigtail plastic stents. "
                "   Technical success: 92–97%. Clinical success: 85–92%. "
                "   Preferred over surgical or percutaneous drainage. "
                "2) TRANSPAPILLARY DRAINAGE (ERCP): if duct communication present. "
                "3) Surgical cystgastrostomy: if EUS drainage fails or anatomy unfavorable."
            )
            next_steps.append("EUS-guided pseudocyst drainage with LAMS or double-pigtail stents")

    # ─── Exocrine Support ─────────────────────────────────────────────────────
    if data.get("hasExocrineInsufficiency") or data.get("hasSteatorrhea"):
        exocrine_support_plan = (
            "PANCREATIC EXOCRINE INSUFFICIENCY (PEI): "
            "PERT (Pancreatic Enzyme Replacement Therapy): "
            "Starting dose: 40,000–50,000 lipase units per main meal; 25,000 units per snack. "
            "Titrate up to 75,000–80,000 lipase units per meal if inadequate response. "
            "Take with FIRST bite of food. "
            "Brands: Creon, Zenpep, Pancreaze, Viokace (non-enteric coated — use with PPI). "
            "Add PPI (omeprazole 20–40mg) if inadequate response — gastric acid inactivates enzymes. "
            "Monitor: fat-soluble vitamins (A, D, E, K), B12, zinc. "
            "Nutritional support: dietitian referral; medium-chain triglycerides (MCT) supplements."
        )
    else:
        exocrine_support_plan = (
            "No exocrine insufficiency identified. Monitor for development — annual fecal elastase-1 if at risk."
        )

    # ─── Endocrine Support ────────────────────────────────────────────────────
    if data.get("hasType3cDiabetes"):
        endocrine_support_plan = (
            "TYPE 3c DIABETES (Pancreatogenic Diabetes): "
            "Distinct from T1DM and T2DM — loss of both alpha and beta cells. "
            "Hypoglycemia risk is HIGH (glucagon deficiency). "
            "Treatment: "
            "1) Insulin (preferred): basal-bolus regimen. Start low, titrate carefully. "
            "2) Metformin: may be used if residual beta-cell function. "
            "3) GLP-1 agonists: use with caution — may worsen exocrine insufficiency. "
            "4) Avoid sulfonylureas — high hypoglycemia risk. "
            "Endocrinology referral recommended. "
            "Continuous glucose monitoring (CGM) for hypoglycemia detection."
        )
    else:
        endocrine_support_plan = (
            "No diabetes identified. Annual HbA1c and fasting glucose monitoring recommended (CP increases T3cDM risk)."
        )

    # ─── Malignancy Surveillance ──────────────────────────────────────────────
    malignancy_surveillance = (
        "PANCREATIC CANCER SURVEILLANCE in CP (APA 2024): "
        "CP increases pancreatic cancer risk 13–16x (hereditary CP: 50–70x). "
        "Annual MRI/MRCP or EUS for: hereditary/genetic CP (PRSS1, SPINK1, CFTR), CP duration >20 years, new-onset diabetes in CP. "
        "Alarm features requiring immediate workup: new/worsening pain, weight loss, new-onset DM, rising CA 19-9. "
        "EUS-FNB if solid mass detected."
    )

    # ─── Lifestyle Modification ───────────────────────────────────────────────
    lifestyle_modification = (
        "LIFESTYLE MODIFICATION (cornerstone — APA/IAP 2024): "
        "1) ALCOHOL CESSATION: most important — reduces pain and slows progression. "
        "   Alcohol abstinence counseling + referral to addiction medicine. "
        "2) SMOKING CESSATION: independent risk factor for CP progression and pancreatic cancer. "
        "3) LOW-FAT DIET: reduces stimulation of pancreatic secretion. "
        "4) SMALL FREQUENT MEALS: 4–6 small meals/day. "
        "5) ANTIOXIDANTS: vitamin C, E, selenium, methionine — modest pain benefit (controversial). "
        "6) HYDRATION: adequate fluid intake."
    )

    if len(next_steps) == 0:
        next_steps.append("Alcohol and smoking cessation counseling")
        next_steps.append("PERT initiation if exocrine insufficiency")
        next_steps.append("ERCP evaluation for ductal anatomy and stenting")
        next_steps.append("EUS for celiac plexus block if pain refractory to medical management")
        next_steps.append("Surgical consultation if endoscopic therapy fails")

    etiology = str(coalesce(data.get("etiology"), "")).replace("_", " ")
    pain_pattern = str(coalesce(data.get("painPattern"), "")).replace("_", " ")
    duct_anatomy_str = str(coalesce(duct_anatomy, "")).replace("_", " ")
    mpd = data.get("mpdDiameterMm")
    rationale = (
        f"Etiology: {etiology}. "
        f"Pain pattern: {pain_pattern}. "
        f"Duct anatomy: {duct_anatomy_str}. "
        f"MPD diameter: {f'{mpd}mm' if mpd else 'not measured'}. "
        f"Stones: {'Yes' if data.get('hasStones') else 'No'}. "
        f"Exocrine insufficiency: {'Yes' if data.get('hasExocrineInsufficiency') else 'No'}. "
        f"Type 3c DM: {'Yes' if data.get('hasType3cDiabetes') else 'No'}."
    )

    if data.get("suspectedMalignancy"):
        primary_recommendation = (
            "Suspected malignancy in chronic pancreatitis: EUS-FNB + CT staging required urgently."
        )
    elif igg4_level is not None and igg4_level > 135:
        primary_recommendation = (
            "Autoimmune pancreatitis type 1 (IgG4 >135): prednisone trial before invasive intervention."
        )
    elif data.get("hasPseudocyst") and pseudocyst_symptoms == "infected":
        primary_recommendation = "Infected pseudocyst: urgent EUS-guided drainage + IV antibiotics."
    elif is_endoscopic_candidate:
        primary_recommendation = (
            "Obstructive chronic pancreatitis: ERCP with pancreatic duct stenting ± ESWL for stones."
        )
    else:
        primary_recommendation = (
            "Chronic pancreatitis: alcohol/smoking cessation + pain management + PERT if exocrine insufficiency."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "painManagement": pain_management,
        "endoscopicTherapy": endoscopic_therapy,
        "surgicalConsideration": surgical_consideration,
        "pseudocystManagement": pseudocyst_management,
        "exocrineSupportPlan": exocrine_support_plan,
        "endocrineSupportPlan": endocrine_support_plan,
        "malignancySurveillance": malignancy_surveillance,
        "lifestyleModification": lifestyle_modification,
        "urgentFlags": urgent_flags,
        "nextSteps": next_steps,
        "evidenceLevel": "B",
        "rationale": rationale,
        "references": _REFERENCES,
    }
