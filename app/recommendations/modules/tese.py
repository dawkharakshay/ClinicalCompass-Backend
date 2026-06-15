"""TESE / Micro-TESE Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/TESECompass.tsx (the inline
``evaluate()`` decision function — there is no separate *Logic.ts for this
module; the engine lives inline in the Compass page).
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "tese"

_REFERENCES = [
    "Schlegel PN. Testicular sperm extraction: microdissection improves sperm yield with minimal tissue excision. Hum Reprod. 1999;14(1):131-135.",
    "Bernie AM, et al. Predictive factors of successful microdissection testicular sperm extraction in men with non-obstructive azoospermia. J Urol. 2015;194(6):1685-1689.",
    "Esteves SC, et al. Reproductive outcomes of testicular versus ejaculated sperm for intracytoplasmic sperm injection among men with high sperm DNA fragmentation in semen: systematic review and meta-analysis. Fertil Steril. 2017;108(3):456-467.",
    "Wosnitzer MS, Goldstein M. Obstructive azoospermia. Urol Clin North Am. 2014;41(1):83-95.",
    "Practice Committee of the American Society for Reproductive Medicine. The management of infertility due to obstructive azoospermia. Fertil Steril. 2019;111(5):873-880.",
]


def assess(data: dict) -> dict:
    azoospermia_type = data.get("azoospermiaType")
    fsh_level = num(data.get("fshLevel"), 0)
    inhibin_b = num(data.get("inhibinB"), 0)
    karyotype = data.get("karyotype")
    histology_pattern = data.get("histologyPattern")
    partner_age = num(data.get("partnerAge"), 0)
    oncology_patient = truthy(data.get("oncologyPatient"))
    prior_tese = truthy(data.get("priorTESE"))
    prior_tese_result = data.get("priorTESEResult")

    warnings: list[str] = []
    rationale: list[str] = []

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "B"
    success_rate = ""

    if azoospermia_type == "obstructive":
        recommendation = "indicated"
        procedure = "Conventional TESE or PESA/MESA (obstructive azoospermia)"
        cor = "I"
        loe = "A"
        success_rate = "~90–100% sperm retrieval"
        rationale.append("Obstructive azoospermia: sperm retrieval rates are very high (90–100%) with PESA, MESA, or conventional TESE.")
        rationale.append("PESA (percutaneous epididymal sperm aspiration) is minimally invasive and preferred first approach.")
    elif azoospermia_type == "non_obstructive":
        # micro-TESE for NOA
        recommendation = "indicated"
        procedure = "Microdissection TESE (micro-TESE) — preferred for NOA"
        cor = "I"
        loe = "B"

        # Predict success rate based on histology and hormones
        if histology_pattern == "hypospermatogenesis":
            success_rate = "~70–80% sperm retrieval"
            rationale.append("Hypospermatogenesis pattern: highest micro-TESE success rate (~70–80%).")
        elif histology_pattern == "maturation_arrest":
            success_rate = "~30–50% sperm retrieval"
            rationale.append("Maturation arrest: moderate success rate (~30–50%) with micro-TESE.")
        elif histology_pattern == "sertoli_only":
            success_rate = "~15–30% sperm retrieval"
            rationale.append("Sertoli cell-only (SCO) pattern: lower success rate (~15–30%) but micro-TESE remains the best option.")
        else:
            success_rate = "~40–60% sperm retrieval (estimated)"
            rationale.append("Micro-TESE (Schlegel 1999) improves sperm retrieval by 1.5× over conventional TESE in NOA through direct visualization of spermatogenic foci.")

        # AZF deletions
        if karyotype == "y_deletion_azfa" or karyotype == "y_deletion_azfb":
            recommendation = "not_indicated"
            procedure = "TESE NOT recommended — AZFa or AZFb deletion"
            warnings.append("Complete AZFa or AZFb deletion: sperm retrieval is virtually impossible (<1%). TESE is not recommended. Donor sperm should be discussed.")
            cor = "III"
            loe = "A"
        elif karyotype == "y_deletion_azfc":
            warnings.append("AZFc deletion: sperm retrieval possible in ~50–70% of cases. Genetic counseling required — 50% of male offspring will inherit deletion.")
        elif karyotype == "klinefelter":
            success_rate = "~40–60% sperm retrieval"
            warnings.append("Klinefelter syndrome (47,XXY): micro-TESE success ~40–60%. Testosterone supplementation should be stopped 3–6 months pre-operatively.")
            rationale.append("Klinefelter syndrome: micro-TESE is the preferred approach; conventional TESE has significantly lower yield.")

    if fsh_level > 20:
        warnings.append(f"Markedly elevated FSH ({_fmt(fsh_level)} mIU/mL): suggests severe spermatogenic impairment; however, FSH alone cannot exclude sperm retrieval.")
    if inhibin_b < 40 and inhibin_b > 0:
        warnings.append(f"Low inhibin B ({_fmt(inhibin_b)} pg/mL): associated with reduced sperm retrieval rates in NOA.")
    if partner_age > 37:
        warnings.append(f"Partner age {_fmt(partner_age)}: time-sensitive — expedite evaluation and procedure planning.")
    if oncology_patient:
        warnings.append("Oncology patient: sperm cryopreservation is urgent — perform before gonadotoxic therapy. Coordinate with oncology team.")
        rationale.append("ASCO guidelines recommend fertility preservation counseling and sperm banking before any gonadotoxic therapy.")
    if prior_tese and prior_tese_result == "no_sperm":
        warnings.append("Prior TESE with no sperm found: repeat micro-TESE may still yield sperm in 20–30% of cases; refer to high-volume center.")

    return {
        "recommendation": recommendation,
        "procedure": procedure,
        "successRate": success_rate,
        "cor": cor,
        "loe": loe,
        "warnings": warnings,
        "rationale": rationale,
        "references": list(_REFERENCES),
    }


def _fmt(x: float) -> str:
    """Render a number like JS template-literal interpolation (no trailing .0)."""
    return str(int(x)) if x == int(x) else str(x)
