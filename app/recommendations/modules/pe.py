"""Pulmonary Embolism Clinical Compass.

Ported 1:1 from the logic the live old app actually uses: ``classifyPE`` in
``old_static_code/client/src/lib/peClassification.ts`` — the engine that
``PECompass.tsx`` (the "Generate Recommendation" action), the patient form,
history, and PDF report all import. The full port lives in
:mod:`app.recommendations.shared.pe_classification`; this module simply
registers it under ``LOGIC_KEY = "pe"``.

Why this file changed: the previous engine here was a port of ``peLogic.ts`` /
``evaluatePE``, an *alternate* implementation the old app never wired up
(``grep`` finds no import of ``evaluatePE`` anywhere in the client). Its
``PEInput`` field names (``presentation``, ``hemodynamicStatus``, ``rvStatus``,
``sPESI``, ``lactateLevel``, ...) do **not** match what the PE form submits —
the ``PatientData`` field names (``symptomatic``, ``systolicBP``,
``refractoryShock``, ``rvDysfunction``, ``tapse``, ...). Because the keys never
lined up, every real submission fell through to ``defaultPEInput`` and
mis-categorised patients (e.g. a cardiac-arrest / Category E2 patient was
reported as C2). Delegating to ``classify_pe`` reproduces the old
recommendation exactly.

Input keys equal the ``PatientData`` interface field names. Checkbox fields
arrive already coerced to bool (``coerce_submission``); the numeric vitals/labs
are coerced here so blank or stringy inputs never crash the direct numeric
comparisons inside ``classify_pe``.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import parse_float
from app.recommendations.shared.pe_classification import classify_pe, patient_data

LOGIC_KEY = "pe"

# PatientData numeric fields (all default to 0 in the form). ``tapse`` is
# ``number | null`` and is handled separately so a blank echo stays null.
_NUMERIC_FIELDS = (
    "age",
    "weight",
    "heartRate",
    "systolicBP",
    "diastolicBP",
    "respiratoryRate",
    "spO2",
    "temperature",
    "troponin",
    "bnp",
    "lactate",
)


def _coerce_number(value, default: float = 0.0):
    """Coerce a *stringy/blank* submitted value to a number; pass real numbers
    through untouched.

    Real ``int``/``float`` inputs are returned as-is so the output is byte-for-
    byte identical to the old ``classifyPE`` (which received real numbers from
    the form and renders them into rationale strings, e.g. ``"SBP 90 mmHg"``).
    Only strings/None get parsed, so a blank or ``"12.5"`` text field never
    crashes the direct numeric comparisons inside ``classify_pe``.
    """
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        return value
    pf = parse_float(value)
    return default if math.isnan(pf) else pf


def _coerce_numbers(data: dict) -> dict:
    out = dict(data)
    for f in _NUMERIC_FIELDS:
        if f in out:
            out[f] = _coerce_number(out[f])
    # tapse: number | null — keep null when absent/blank; parse only a string.
    t = out.get("tapse")
    if isinstance(t, str):
        t = t.strip()
        pf = parse_float(t)
        out["tapse"] = None if (t == "" or math.isnan(pf)) else pf
    elif isinstance(t, bool):
        out["tapse"] = None
    return out


def assess(data: dict) -> dict:
    """Classify a PE submission into an AHA/ACC 2026 category (A–E2) and full
    recommendation, exactly as the old ``classifyPE`` did."""
    patient = patient_data(_coerce_numbers(data or {}))
    return classify_pe(patient)


# ─── Card presentation ──────────────────────────────────────────────────────
# classify_pe returns nested objects (scores, contraindications,
# esc2019Equivalent) that the generic build_card cannot fold well — it would
# drop the contraindications, mis-tone the "critical" risk badge, and title the
# card "Recommendation". This present() mirrors what the old PE Compass result
# screen (PECompass.tsx) displayed: category + label as the heading, the risk /
# hemodynamic badges, treatment as the summary, and explicit sections for the
# rationale, the sPESI/BOVA/NEWS scores, and the ESC 2019 equivalent.

_RISK_TONE = {
    "critical": "danger",
    "high": "danger",
    "moderate": "warning",
    "low": "success",
    "minimal": "success",
}


def present(native: dict) -> dict:
    from app.recommendations.card import _normalize_evidence

    native = dict(native or {})
    category = str(native.get("category", "") or "")
    label = str(native.get("label", "") or "")
    risk = str(native.get("riskLevel", "") or "")
    scores = native.get("scores") or {}
    contra = native.get("contraindications") or {}
    esc = native.get("esc2019Equivalent") or {}
    resp_mod = bool(native.get("respiratoryModifier"))
    resp_detail = str(native.get("respiratoryModifierDetail", "") or "")
    hemo = str(native.get("hemodynamicStatus", "") or "")
    treatment = str(native.get("treatment", "") or "")
    rationale = native.get("rationale") or []

    badges: list[dict] = []
    if category:
        badges.append({
            "label": "Category",
            "value": category,
            "tone": _RISK_TONE.get(risk, "info"),
        })
    if risk:
        badges.append({
            "label": "Risk",
            "value": risk.title(),
            "tone": _RISK_TONE.get(risk, "info"),
        })
    if hemo:
        badges.append({
            "label": "Hemodynamics",
            "value": hemo.title(),
            "tone": "danger" if hemo == "unstable" else "success",
        })

    alerts: list[dict] = []
    contra_items: list[str] = []
    for lbl, obj in (
        ("Systemic thrombolysis", contra.get("systemicThrombolysis") or {}),
        ("CDT", contra.get("cdt") or {}),
    ):
        for c in obj.get("absolute") or []:
            contra_items.append(f"{lbl} — absolute: {c}")
        for c in obj.get("relative") or []:
            contra_items.append(f"{lbl} — relative: {c}")
    for c in (contra.get("anticoagulation") or {}).get("cautions") or []:
        contra_items.append(f"Anticoagulation caution: {c}")
    if contra_items:
        alerts.append({"tone": "danger", "title": "Contraindications & Cautions",
                       "items": contra_items})
    if resp_mod and resp_detail:
        alerts.append({"tone": "warning", "title": "Respiratory Modifier (R)",
                       "items": [resp_detail]})

    sections: list[dict] = []
    if rationale:
        sections.append({"id": "rationale", "label": "Rationale", "type": "list",
                         "items": [str(x) for x in rationale]})
    sp, bv, nw = scores.get("sPESI") or {}, scores.get("BOVA") or {}, scores.get("NEWS") or {}
    score_items: list[dict] = []
    if sp:
        score_items.append({"key": "sPESI", "value": str(sp.get("score"))})
    if bv:
        score_items.append({"key": "BOVA", "value": f"{bv.get('score')} ({bv.get('stage')})"})
    if nw:
        score_items.append({"key": "NEWS", "value": f"{nw.get('score')} ({nw.get('risk')})"})
    if score_items:
        sections.append({"id": "scores", "label": "Risk Scores", "type": "keyvalue",
                         "items": score_items})
    if esc.get("category"):
        sections.append({"id": "esc_equivalent",
                         "label": f"ESC 2019 Equivalent — {esc['category']}",
                         "type": "text", "content": esc.get("description", "")})

    title = f"Category {category} — {label}".strip(" —") if (category or label) else "Recommendation"
    subtitle = (f"Respiratory modifier (R): {resp_detail}"
                if (resp_mod and resp_detail) else (esc.get("category") or None))

    return {
        "module": LOGIC_KEY,
        "title": title,
        "subtitle": subtitle,
        "badges": badges,
        "score": None,
        "alerts": alerts,
        "summary": treatment or None,
        "sections": sections,
        "nextSteps": [],
        "evidence": _normalize_evidence(native.get("evidence")),
        "guidelineSource": (
            "2026 AHA/ACC/ACCP/ACEP/CHEST/SCAI/SHM/SIR/SVM/SVN Guideline for the "
            "Evaluation and Management of Acute Pulmonary Embolism in Adults. "
            "Circulation. 2026;153:e977-e1051."
        ),
    }
