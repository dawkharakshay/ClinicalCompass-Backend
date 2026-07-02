"""Gastroparesis Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/gastroparesisLogic.ts
(assessGastroparesis).

Based on AGA (2022/2025) and ACG (2022) clinical guidelines on gastroparesis.
"""

from __future__ import annotations

from app.recommendations.jslib import coalesce, parse_float, truthy

LOGIC_KEY = "gastroparesis"

_REFERENCES = [
    {
        "citation": "Camilleri M, et al. Clinical Guideline: Management of Gastroparesis. Am J Gastroenterol. 2022;117(8):1197-1220.",
        "pmid": "35767360",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35767360/",
    },
    {
        "citation": "AGA Clinical Practice Guideline on the Pharmacological Management of Irritable Bowel Syndrome and Gastroparesis. Gastroenterology. 2022;163(6):1440-1471.",
        "pmid": "36122912",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36122912/",
    },
    {
        "citation": "Mekaroonkamol P, et al. Outcomes of Per Oral Endoscopic Pyloromyotomy in Gastroparesis Worldwide (GALACTIC). Gut. 2023;72(4):686-694.",
        "pmid": "36202553",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36202553/",
    },
    {
        "citation": "McCallum RW, et al. Gastric Electrical Stimulation with Enterra Therapy for Gastroparesis. Gastroenterology. 2010;138(7):2456-2462.",
        "pmid": "20176023",
        "url": "https://pubmed.ncbi.nlm.nih.gov/20176023/",
    },
]


def assess(data: dict) -> dict:
    urgent_flags: list[str] = []
    recommended_agents: list[str] = []
    medications_to_avoid: list[str] = []
    next_steps: list[str] = []

    diagnostic_status = data.get("diagnosticStatus")
    etiology = data.get("etiology")
    severity = data.get("severity")
    weight_loss_kg = data.get("weightLossKg")
    hba1c_percent = data.get("hba1cPercent")
    gastric_retention_4h = data.get("gastricRetentionPercent4h")
    is_on_prokinetic = truthy(data.get("isOnProkinetic"))
    has_hospitalizations = truthy(data.get("hasHospitalizationsInPastYear"))

    # ─── Urgent Flags ─────────────────────────────────────────────────────────
    if truthy(data.get("hasDehydration")) or (
        severity == "severe" and truthy(data.get("hasVomiting"))
    ):
        urgent_flags.append(
            "Severe dehydration/vomiting: IV fluid resuscitation and electrolyte "
            "replacement required — consider hospitalization"
        )
    if (
        truthy(data.get("requiresNutritionalSupport"))
        and weight_loss_kg is not None
        and parse_float(weight_loss_kg) > 5
    ):
        urgent_flags.append(
            f"Significant weight loss ({_fmt(parse_float(weight_loss_kg))}kg): nutritional assessment "
            "and enteral nutrition support required"
        )
    if truthy(data.get("isOnOpioids")):
        urgent_flags.append(
            "OPIOIDS: strongly worsen gastroparesis — opioid-induced gastroparesis "
            "is a recognized entity. Opioid taper/discontinuation is a priority."
        )
        medications_to_avoid.append(
            "Opioids — significantly delay gastric emptying; taper and discontinue if possible"
        )
    if truthy(data.get("isOnGLP1Agonist")):
        urgent_flags.append(
            "GLP-1 agonists (semaglutide, liraglutide, tirzepatide) delay gastric "
            "emptying — consider dose reduction or discontinuation in symptomatic gastroparesis"
        )
        medications_to_avoid.append(
            "GLP-1 agonists — delay gastric emptying; reassess risk-benefit in gastroparesis"
        )
    if truthy(data.get("isOnAnticholinergics")):
        medications_to_avoid.append(
            "Anticholinergic medications — delay gastric emptying; review and discontinue if possible"
        )
    if truthy(data.get("hasTardivedyskinesia")):
        urgent_flags.append(
            "Tardive dyskinesia: metoclopramide is CONTRAINDICATED — do not use"
        )
        medications_to_avoid.append(
            "Metoclopramide — contraindicated with tardive dyskinesia"
        )
    if truthy(data.get("hasQTProlongation")):
        urgent_flags.append(
            "QT prolongation: metoclopramide and domperidone increase QT — use with "
            "caution or avoid; obtain baseline ECG"
        )
        medications_to_avoid.append(
            "Metoclopramide, domperidone — QT-prolonging; caution with QT prolongation"
        )
    if etiology == "diabetic" and hba1c_percent is not None and parse_float(hba1c_percent) > 9:
        urgent_flags.append(
            f"Poorly controlled diabetes (HbA1c {_fmt(parse_float(hba1c_percent))}%): glycemic "
            "optimization is critical — hyperglycemia acutely worsens gastric "
            "motility. Target HbA1c <8%."
        )

    # ─── Diagnostic Plan ──────────────────────────────────────────────────────
    if diagnostic_status == "not_tested" or diagnostic_status == "ges_2h_only":
        diagnostic_plan = (
            "4-HOUR GASTRIC EMPTYING SCINTIGRAPHY (GES) REQUIRED (AGA 2022 Strong Recommendation): "
            "The 4-hour study is the gold standard — 2-hour studies have poor sensitivity and are insufficient. "
            "Standardized protocol: 99mTc-sulfur colloid egg meal, images at 0, 1, 2, 4 hours. "
            "Hold prokinetics 48h before test. Hold opioids 48h before test. "
            "Abnormal: >10% retention at 4 hours (mild: 10–20%; moderate: 20–35%; severe: >35%). "
            "Alternative: wireless motility capsule (SmartPill) or 13C-octanoate breath test."
        )
        next_steps.append("4-hour gastric emptying scintigraphy (standardized protocol)")
        next_steps.append("Hold prokinetics and opioids 48h before test")
    elif diagnostic_status == "ges_4h_confirmed":
        diagnostic_plan = (
            f"4-hour GES confirmed gastroparesis ({coalesce(gastric_retention_4h, '?')}% "
            "retention at 4h). Diagnosis established."
        )
    else:
        diagnostic_plan = (
            "Diagnosis established by alternative validated method. Confirm with "
            "4-hour GES if clinical uncertainty."
        )

    # ─── Dietary Modification ─────────────────────────────────────────────────
    dietary_modification = (
        "DIETARY MODIFICATION (first-line — AGA 2022): "
        "1) Small, frequent meals: 4–6 small meals/day instead of 3 large meals. "
        "2) Low-fat diet: fat delays gastric emptying — limit to <40g/day. "
        "3) Low-fiber diet: avoid indigestible fiber (raw vegetables, high-fiber foods) — risk of bezoar formation. "
        "4) Liquid-predominant diet: liquids empty faster than solids — use liquid nutritional supplements if needed. "
        "5) Avoid carbonated beverages. "
        "6) Eat sitting upright; avoid lying down for 2 hours after meals. "
        "7) Registered dietitian referral for individualized meal planning."
    )

    # ─── Pharmacotherapy ──────────────────────────────────────────────────────
    if severity == "mild" or not is_on_prokinetic:
        pharmacotherapy = (
            "PHARMACOTHERAPY HIERARCHY (AGA 2022 — limited strong evidence): "
            "1) METOCLOPRAMIDE 5–10mg TID–QID (30 min before meals) — ONLY FDA-APPROVED PROKINETIC for gastroparesis. "
            "   Dopamine D2 antagonist + 5-HT4 agonist. "
            "   FDA Black Box Warning: tardive dyskinesia risk with >12 weeks use. "
            "   Limit to 12 weeks; reassess risk-benefit for longer use. "
            "   Contraindicated: tardive dyskinesia, Parkinson's disease, bowel obstruction. "
            "2) DOMPERIDONE 10mg TID–QID — peripheral D2 antagonist (less CNS penetration). "
            "   Not FDA-approved in US — available via FDA compassionate use IND. "
            "   Superior tolerability vs metoclopramide (less CNS side effects). "
            "   QT prolongation risk — baseline ECG required. "
            "3) ERYTHROMYCIN 125–250mg TID (before meals) — motilin receptor agonist. "
            "   Rapid tachyphylaxis (tolerance within 4 weeks). "
            "   Use for short-term acute exacerbations or IV in hospitalized patients. "
            "4) PRUCALOPRIDE (Motegrity) — 5-HT4 agonist: emerging evidence for gastroparesis. "
            "5) ANTIEMETICS for symptom control: ondansetron, promethazine, prochlorperazine. "
            "   Note: antiemetics treat symptoms but do not improve gastric emptying."
        )
        if not truthy(data.get("hasTardivedyskinesia")) and not truthy(data.get("hasParkinson")):
            recommended_agents.append(
                "Metoclopramide 5–10mg TID–QID (FDA-approved — limit to 12 weeks)"
            )
        if not truthy(data.get("hasQTProlongation")):
            recommended_agents.append(
                "Domperidone 10mg TID (via FDA compassionate use IND — superior tolerability)"
            )
        recommended_agents.append("Erythromycin 125–250mg TID (short-term/acute exacerbations)")
        recommended_agents.append("Ondansetron 4–8mg TID (antiemetic — symptom control)")
        recommended_agents.append("Prucalopride 2mg QD (5-HT4 agonist — emerging evidence)")
    else:
        pharmacotherapy = (
            "Currently on prokinetic therapy. Assess response and tolerability. "
            "If inadequate response: optimize dose, switch prokinetic class, or consider interventional options. "
            "Therapeutic drug monitoring not applicable for prokinetics."
        )

    # ─── Interventional Options ───────────────────────────────────────────────
    if severity == "severe" or has_hospitalizations:
        interventional_options = (
            "INTERVENTIONAL OPTIONS for refractory/severe gastroparesis: "
            "1) GASTRIC PERORAL ENDOSCOPIC MYOTOMY (G-POEM): "
            "   Endoscopic pyloromyotomy — disrupts pyloric sphincter. "
            "   Emerging evidence: 80–90% clinical response in observational studies. "
            "   GALACTIC RCT (2023): G-POEM superior to sham procedure at 6 months. "
            "   Preferred over surgical pyloroplasty (less invasive). "
            "2) GASTRIC ELECTRICAL STIMULATION (GES — Enterra Therapy): "
            "   FDA humanitarian device exemption (HDE) for refractory diabetic/idiopathic gastroparesis. "
            "   Reduces vomiting and nausea (symptom benefit) but does NOT reliably improve gastric emptying. "
            "   Best evidence for diabetic gastroparesis with predominant nausea/vomiting. "
            "3) BOTULINUM TOXIN INJECTION (pylorus): "
            "   AGA 2022: NOT recommended — RCTs show no benefit over sham. "
            "4) SURGICAL PYLOROPLASTY: "
            "   Alternative to G-POEM; higher morbidity. "
            "5) TOTAL PARENTERAL NUTRITION (TPN): last resort for severe malnutrition — high complication risk."
        )
        if not truthy(data.get("hasPriorGPOEM")):
            recommended_agents.append(
                "G-POEM (gastric peroral endoscopic myotomy) — preferred interventional option"
            )
        if not truthy(data.get("hasPriorGES")):
            recommended_agents.append(
                "Gastric electrical stimulation (Enterra) — for refractory diabetic/idiopathic gastroparesis with predominant vomiting"
            )
    else:
        interventional_options = (
            "Interventional options not yet indicated — optimize dietary modification and pharmacotherapy first. "
            "Consider G-POEM or GES if refractory to medical management."
        )

    # ─── Nutritional Support ──────────────────────────────────────────────────
    if truthy(data.get("requiresNutritionalSupport")) or severity == "severe":
        nutritional_support = (
            "NUTRITIONAL SUPPORT (AGA 2022): "
            "1) Oral liquid nutritional supplements first (Ensure, Boost, Carnation Breakfast Essentials). "
            "2) Jejunal feeding (NJ tube or PEJ): preferred over gastric feeding — bypasses gastroparesis. "
            "   Indicated for: weight loss >10%, inability to maintain oral intake, recurrent hospitalizations. "
            "3) Total parenteral nutrition (TPN): last resort — high infection/complication risk. "
            "   Only if enteral access not feasible."
        )
        next_steps.append("Registered dietitian consultation for nutritional assessment")
        next_steps.append("Consider jejunal feeding tube if oral intake inadequate")
    else:
        nutritional_support = (
            "Oral diet with dietary modifications sufficient at this stage. "
            "Monitor weight and nutritional status."
        )

    if len(next_steps) == 0 or not any("GES" in s for s in next_steps):
        next_steps.append("Optimize glycemic control if diabetic (target HbA1c <8%)")
        next_steps.append(
            "Review and discontinue medications that worsen gastric emptying (opioids, anticholinergics, GLP-1 agonists)"
        )
        next_steps.append("Registered dietitian referral for dietary modification")
        next_steps.append("Gastroenterology/motility specialist referral")

    etiology_str = str(coalesce(etiology, "")).replace("_", " ")
    severity_str = severity if severity is not None else ""
    diag_str = str(coalesce(diagnostic_status, "")).replace("_", " ")
    rationale = (
        f"Etiology: {etiology_str}. "
        f"Severity: {severity_str}. "
        f"Diagnostic status: {diag_str}. "
        f"4h retention: {coalesce(gastric_retention_4h, 'not measured')}%. "
        f"On prokinetic: {'Yes' if is_on_prokinetic else 'No'}. "
        f"Hospitalizations past year: {'Yes' if has_hospitalizations else 'No'}."
    )

    if diagnostic_status == "not_tested" or diagnostic_status == "ges_2h_only":
        primary_recommendation = (
            "4-hour gastric emptying scintigraphy required for diagnosis — "
            "2-hour studies are insufficient (AGA 2022 Strong Recommendation)."
        )
    elif severity == "severe" or has_hospitalizations:
        primary_recommendation = (
            "Severe/refractory gastroparesis: G-POEM or gastric electrical "
            "stimulation after failure of dietary + pharmacotherapy."
        )
    else:
        primary_recommendation = (
            "Gastroparesis confirmed: dietary modification (small, low-fat, "
            "low-fiber meals) + metoclopramide (first-line pharmacotherapy)."
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "diagnosticPlan": diagnostic_plan,
        "dietaryModification": dietary_modification,
        "pharmacotherapy": pharmacotherapy,
        "interventionalOptions": interventional_options,
        "nutritionalSupport": nutritional_support,
        "medicationsToAvoid": medications_to_avoid,
        "urgentFlags": urgent_flags,
        "recommendedAgents": recommended_agents,
        "nextSteps": next_steps,
        "evidenceLevel": "B",
        "rationale": rationale,
        "references": _REFERENCES,
    }


def _fmt(x: float) -> str:
    """Render a number the way JS string interpolation would (no trailing .0)."""
    if x == int(x):
        return str(int(x))
    return repr(x)
