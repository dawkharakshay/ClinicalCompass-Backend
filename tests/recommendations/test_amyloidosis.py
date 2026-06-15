"""Tests for the Amyloidosis diagnostic engine.

No TS .test.ts oracle exists for amyloidosisLogic.ts; fixtures are derived
directly from the TS branches (assessAmyloidosis / detectRedFlags / getALStage),
covering each major decision path plus the BSC / contraindication path.
"""

from __future__ import annotations

from app.recommendations.modules.amyloidosis import assess


def _symptoms(**over) -> dict:
    base = {
        "heartFailure": False,
        "unexplainedHypertrophicCM": False,
        "lowVoltageECG": False,
        "bilateralCarpalTunnel": False,
        "spinalStenosis": False,
        "peripheralNeuropathy": False,
        "autonomicDysfunction": False,
        "nephrotic": False,
        "hepatomegaly": False,
        "macroglossia": False,
        "periorbitalPurpura": False,
        "unexplainedWeightLoss": False,
        "fatigue": False,
    }
    base.update(over)
    return base


def _base(**over) -> dict:
    base = {
        "age": 65,
        "sex": "male",
        "ethnicity": "other",
        "symptoms": _symptoms(),
        "hasMGUS": False,
        "hasPlasmaCellDyscrasia": False,
        "sflcRatio": "not_done",
        "boneScanResult": "not_done",
        "echoLVWallThickness": 0,
        "echoRelativeWallThickness": "normal",
        "echoGLS": "normal",
        "ntproBNP": 0,
        "troponinT": 0,
        "egfr": 90,
        "proteinuria": 0,
        "ttrGeneticTest": "not_done",
        "ttrMutation": "none_wild_type",
        "biopsyResult": "not_done",
        "biopsySite": "none",
        "amyloidType": "unknown",
        "ecogPS": 1,
        "nyhaClass": 1,
        "priorTherapy": False,
        "patientPreference": "moderate",
    }
    base.update(over)
    return base


# ── BSC path ──────────────────────────────────────────────────────────────────
def test_bsc_by_preference():
    r = assess(_base(patientPreference="bsc", amyloidType="al_amyloidosis"))
    assert r["diagnosticLabel"] == "Best Supportive Care"
    assert r["suspectedType"] == "al_amyloidosis"
    assert r["urgencyFlag"] == "routine"
    assert r["keyWarnings"] == ["Ensure goals-of-care discussion is documented."]


def test_bsc_by_ecog4():
    r = assess(_base(ecogPS=4, amyloidType="attr_wt"))
    assert r["diagnosticLabel"] == "Best Supportive Care"
    assert r["nextDiagnosticSteps"] == []


# ── AL amyloidosis ──────────────────────────────────────────────────────────────
def test_al_stage1_transplant_eligible():
    r = assess(_base(amyloidType="al_amyloidosis", ntproBNP=500, troponinT=10, egfr=90))
    assert r["diagnosticConfidence"] == "confirmed"
    assert r["suspectedType"] == "al_amyloidosis"
    assert r["stagingInfo"] == "Mayo 2012 Stage: Stage I (Median OS >5 years)"
    assert r["urgencyFlag"] == "urgent"
    assert "induction → Autologous Stem Cell Transplant" in r["treatmentRecommendation"]


def test_al_stage3b_emergent():
    # all three: ntproBNP>=1800, troponinT>=25, egfr<50 -> stage3b
    r = assess(_base(amyloidType="al_amyloidosis", ntproBNP=9000, troponinT=80, egfr=20))
    assert r["stagingInfo"] == "Mayo 2012 Stage: Stage IIIb (Median OS ~6 months) — Very High Risk"
    assert r["urgencyFlag"] == "emergent"
    assert "Avoid ASCT" in r["treatmentRecommendation"]
    assert any("Stage IIIb AL Amyloidosis" in w for w in r["keyWarnings"])


def test_al_transplant_ineligible_not_3b():
    # stage2 (one criterion: high troponin), but nyhaClass 3 makes ineligible
    r = assess(
        _base(
            amyloidType="al_amyloidosis",
            ntproBNP=500,
            troponinT=30,
            egfr=90,
            nyhaClass=3,
            symptoms=_symptoms(heartFailure=True),
        )
    )
    assert "transplant-ineligible AL amyloidosis" in r["treatmentRecommendation"]
    assert any("Advanced cardiac involvement" in w for w in r["keyWarnings"])


def test_al_via_biopsy():
    r = assess(_base(biopsyResult="positive_al", ntproBNP=500, troponinT=10, egfr=90))
    assert r["diagnosticLabel"] == "AL Amyloidosis (Light Chain Amyloidosis)"


# ── ATTR amyloidosis ────────────────────────────────────────────────────────────
def test_attr_wt_cardiomyopathy():
    r = assess(
        _base(
            amyloidType="attr_wt",
            echoLVWallThickness=16,
            symptoms=_symptoms(heartFailure=True),
            nyhaClass=3,
        )
    )
    assert r["suspectedType"] == "attr_wt"
    assert r["diagnosticLabel"].startswith("Wild-Type ATTR Amyloidosis")
    assert "Tafamidis" in r["treatmentRecommendation"]
    assert r["urgencyFlag"] == "urgent"
    assert "NYHA Class: 3" in r["stagingInfo"]


def test_attr_hereditary_neuropathy():
    r = assess(
        _base(
            amyloidType="attr_hereditary",
            symptoms=_symptoms(peripheralNeuropathy=True, autonomicDysfunction=True),
            ttrMutation="val30met",
        )
    )
    assert r["suspectedType"] == "attr_hereditary"
    assert "Patisiran" in r["treatmentRecommendation"]
    assert any("V30M TTR mutation" in w for w in r["keyWarnings"])
    assert "Nerve conduction studies / EMG" in r["nextDiagnosticSteps"]
    assert "Family screening with TTR genetic testing (autosomal dominant)" in r["nextDiagnosticSteps"]


def test_attr_non_biopsy_highly_likely():
    r = assess(
        _base(
            amyloidType="attr_wt",
            boneScanResult="grade2",
            hasMGUS=False,
            sflcRatio="normal",
            symptoms=_symptoms(heartFailure=True),
            ttrMutation="val122ile",
        )
    )
    assert r["diagnosticConfidence"] == "highly_likely"
    assert "Non-biopsy diagnosis criteria met" in r["diagnosticRationale"]
    assert any("V122I TTR mutation" in w for w in r["keyWarnings"])


def test_attr_biopsy_confirmed():
    r = assess(_base(biopsyResult="positive_attr", symptoms=_symptoms(heartFailure=True)))
    assert r["diagnosticConfidence"] == "confirmed"


def test_attr_hereditary_mixed_no_neuropathy_no_cm():
    # hereditary via genetic test, no neuropathy, no cardiomyopathy -> mixed branch
    r = assess(
        _base(
            amyloidType="attr_hereditary",
            echoLVWallThickness=10,
            symptoms=_symptoms(),
        )
    )
    assert "Initiate based on predominant organ involvement." in r["treatmentRecommendation"]
    assert r["diagnosticConfidence"] == "suspected"


# ── Unknown / suspected workup ───────────────────────────────────────────────────
def test_unknown_high_suspicion_three_red_flags():
    # red flags: HCM+lowVoltage, macroglossia, periorbitalPurpura = 3
    r = assess(
        _base(
            amyloidType="unknown",
            symptoms=_symptoms(
                unexplainedHypertrophicCM=True,
                lowVoltageECG=True,
                macroglossia=True,
                periorbitalPurpura=True,
            ),
        )
    )
    assert len(r["redFlags"]) == 3
    assert r["diagnosticConfidence"] == "suspected"
    assert r["diagnosticLabel"] == "Amyloidosis Suspected — Urgent Workup Required"
    assert r["urgencyFlag"] == "urgent"
    assert r["diagnosticRationale"].startswith("3 red flag(s) identified")
    assert any("CRITICAL: Always type the amyloid" in w for w in r["keyWarnings"])


def test_unknown_low_suspicion_default_steps():
    r = assess(_base(amyloidType="unknown"))
    assert r["diagnosticConfidence"] == "low_suspicion"
    assert r["diagnosticLabel"] == "Low Suspicion — Screening Recommended"
    assert r["urgencyFlag"] == "routine"
    assert r["nextDiagnosticSteps"][0].startswith("Complete amyloidosis screening")


def test_unknown_mgus_pathway():
    r = assess(_base(amyloidType="unknown", hasMGUS=True))
    assert r["nextDiagnosticSteps"][0].startswith("MGUS/abnormal SFLC")


def test_red_flag_carpal_tunnel_age():
    flags = assess(
        _base(amyloidType="unknown", age=70, symptoms=_symptoms(bilateralCarpalTunnel=True))
    )["redFlags"]
    assert any("Bilateral carpal tunnel" in f for f in flags)


def test_red_flag_carpal_tunnel_age_not_old_enough():
    flags = assess(
        _base(amyloidType="unknown", age=55, symptoms=_symptoms(bilateralCarpalTunnel=True))
    )["redFlags"]
    assert not any("Bilateral carpal tunnel" in f for f in flags)


def test_red_flag_african_american_hf():
    flags = assess(
        _base(
            amyloidType="unknown",
            age=62,
            ethnicity="african_american",
            symptoms=_symptoms(heartFailure=True),
        )
    )["redFlags"]
    assert any("African American patient ≥60" in f for f in flags)
