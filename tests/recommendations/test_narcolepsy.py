"""Tests for the narcolepsy module, ported from the inline evaluate() in
old_static_code/client/src/pages/NarcolepsyCompass.tsx."""

from app.recommendations.modules.narcolepsy import assess


def _base(**overrides) -> dict:
    data = {
        "ess": "",
        "cataplexy": False,
        "mslt_sol": "",
        "mslt_sorems": "",
        "csf_hypocretin": "not_tested",
        "psg_performed": False,
        "psg_rem_latency": "",
        "type": "unknown",
        "comorbid_osa": False,
    }
    data.update(overrides)
    return data


def test_type1_cataplexy_plus_csf_low():
    r = assess(_base(cataplexy=True, csf_hypocretin="low", ess="14"))
    assert r["diagnosisLikelihood"] == "high"
    assert r["diagnosisType"] == "type1"
    assert r["authRequired"] is True
    assert r["appealStrength"] == "strong"
    assert r["csfLow"] is True
    # type1/cataplexy branch adds cataplexy-specific first/second line meds
    assert any("also addresses cataplexy" in m for m in r["firstLine"])
    assert "Venlafaxine 75–225 mg/day for cataplexy (AASM: Conditional)" in r["secondLine"]
    assert "Clomipramine 25–200 mg/day for cataplexy (AASM: Conditional)" in r["secondLine"]


def test_type1_cataplexy_plus_mslt_positive():
    r = assess(_base(cataplexy=True, mslt_sol="5", mslt_sorems="3"))
    assert r["diagnosisLikelihood"] == "high"
    assert r["diagnosisType"] == "type1"
    assert r["msltPositive"] is True


def test_type2_mslt_positive_no_cataplexy_no_csf():
    r = assess(_base(cataplexy=False, mslt_sol="8", mslt_sorems="2", ess="12"))
    assert r["diagnosisLikelihood"] == "high"
    assert r["diagnosisType"] == "type2"
    assert r["appealStrength"] == "strong"
    assert r["msltPositive"] is True
    # No cataplexy / not type1 -> no second-line cataplexy meds
    assert r["secondLine"] == []
    assert len(r["firstLine"]) == 4


def test_moderate_eds_with_psg_sorem():
    r = assess(_base(ess="11", psg_performed=True, psg_rem_latency="15"))
    assert r["diagnosisLikelihood"] == "moderate"
    assert r["diagnosisType"] == "unknown"
    assert r["appealStrength"] == "moderate"
    assert r["authRequired"] is True
    assert len(r["firstLine"]) == 4
    assert "PSG: REM latency ≤15 min (sleep-onset REM period)" in r["keyFindings"]


def test_moderate_eds_with_mslt_positive_but_csf_low_no_cataplexy():
    # No cataplexy + MSLT positive + csfLow: type1 needs cataplexy, type2 needs
    # !csfLow -> both high branches fail; EDS + msltPositive -> moderate.
    r = assess(_base(ess="10", mslt_sol="7", mslt_sorems="2", csf_hypocretin="low"))
    assert r["diagnosisLikelihood"] == "moderate"
    assert r["appealStrength"] == "moderate"
    assert r["csfLow"] is True


def test_low_eds_only():
    r = assess(_base(ess="10"))
    assert r["diagnosisLikelihood"] == "low"
    assert r["authRequired"] is False
    assert r["appealStrength"] == "weak"
    assert r["firstLine"] == []
    assert r["adjunctive"] == []
    assert any("ESS score 10" in k for k in r["keyFindings"])


def test_no_data_defaults_low():
    r = assess(_base())
    assert r["diagnosisLikelihood"] == "low"
    assert r["authRequired"] is False
    assert r["essNum"] is None
    assert r["msltPositive"] is False
    assert r["keyFindings"] == []


def test_cataplexy_without_confirmation_not_type1():
    # cataplexy present but no csfLow and MSLT negative -> falls through.
    # ess<10 so not EDS either -> low likelihood, but cataplexy keyFinding shown.
    r = assess(_base(cataplexy=True, ess="5"))
    assert r["diagnosisLikelihood"] == "low"
    assert r["diagnosisType"] == "unknown"
    assert "Cataplexy present (pathognomonic for NT1)" in r["keyFindings"]


def test_comorbid_osa_keyfinding():
    r = assess(_base(ess="12", comorbid_osa=True, mslt_sol="6", mslt_sorems="2"))
    assert "Comorbid OSA — ensure adequate OSA treatment before MSLT" in r["keyFindings"]


def test_mslt_boundary_sorems_one_negative():
    # sorems must be >=2; 1 is negative even with low SOL
    r = assess(_base(ess="12", mslt_sol="3", mslt_sorems="1"))
    assert r["msltPositive"] is False
    # EDS but no positive study -> low
    assert r["diagnosisLikelihood"] == "low"


def test_ess_float_formatting_in_keyfinding():
    r = assess(_base(ess="12.5"))
    assert any("ESS score 12.5" in k for k in r["keyFindings"])
    assert r["essNum"] == 12.5
