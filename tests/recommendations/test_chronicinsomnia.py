"""Tests for the Chronic Insomnia Clinical Compass port.

Fixtures derived 1:1 from the TS branches in
old_static_code/client/src/pages/ChronicInsomniaCompass.tsx (evaluate).
"""

from app.recommendations.modules.chronicinsomnia import assess


def _base(**overrides):
    data = {
        "type": "both",
        "duration_months": "",
        "isi_score": "",
        "frequency_nights_per_week": "",
        "daytime_impairment": True,
        "cbti_completed": False,
        "cbti_response": "not_tried",
        "comorbid_depression": False,
        "comorbid_anxiety": False,
        "comorbid_pain": False,
        "comorbid_osa": False,
        "comorbid_rls": False,
        "comorbid_substance": False,
        "prior_benzo": False,
        "prior_zdrug": False,
        "prior_orexin": False,
        "prior_doxepin": False,
        "pregnancy": False,
        "age_over_65": False,
        "hepatic_impairment": False,
    }
    data.update(overrides)
    return data


def test_default_not_tried_subthreshold():
    r = assess(_base())
    assert r["isChronicInsomnia"] is False
    assert r["severity"] == "mild"
    assert r["authRequired"] is False
    assert r["appealStrength"] == "moderate"
    # CBT-I always first, then the not_tried warning
    assert r["firstLine"][0].startswith("Cognitive Behavioral Therapy for Insomnia (CBT-I)")
    assert any("CBT-I should be attempted before pharmacotherapy" in s for s in r["firstLine"])
    # no pharmacologic options when not_tried
    assert r["secondLine"] == []
    # default avoid list (no age/substance/pregnancy)
    assert r["avoidList"] == [
        "OTC antihistamines (diphenhydramine, doxylamine) — AASM: Against for chronic insomnia",
        "Melatonin — AASM: Weak evidence for chronic insomnia; not recommended as primary treatment",
        "Tryptophan, valerian — AASM: Insufficient evidence",
    ]
    assert r["keyFindings"] == []


def test_chronic_partial_response_full_pharmacotherapy():
    r = assess(
        _base(
            duration_months="6",
            frequency_nights_per_week="5",
            isi_score="24",
            type="both",
            cbti_response="partial",
        )
    )
    assert r["isChronicInsomnia"] is True
    assert r["severity"] == "severe"
    assert r["authRequired"] is True
    assert r["appealStrength"] == "strong"
    # orexin antagonists (no age/hepatic), doxepin (both), and 2026 combination note
    assert any("Suvorexant (Belsomra)" in s for s in r["firstLine"])
    assert any("Lemborexant (Dayvigo)" in s for s in r["firstLine"])
    assert any("Doxepin 3–6 mg" in s for s in r["firstLine"])
    assert any("AASM April 2026 CPG: Combination" in s for s in r["firstLine"])
    # second line: z-drugs/eszopiclone/triazolam (no substance), no trazodone (no depression)
    assert r["secondLine"] == [
        "Eszopiclone (Lunesta) 1–3 mg — AASM: Conditional recommendation",
        "Zolpidem (Ambien) 5–10 mg — AASM: Conditional recommendation",
        "Triazolam 0.125–0.25 mg — AASM: Conditional recommendation (short-term only)",
    ]
    assert any("ISI score: 24/28 — severe insomnia" == s for s in r["keyFindings"])
    assert any("Chronic insomnia disorder: ≥6 months, ≥5 nights/week" in s for s in r["keyFindings"])
    assert any("CBT-I trial: Partial response" in s for s in r["keyFindings"])


def test_inadequate_response_elderly_hepatic_substance_depression():
    r = assess(
        _base(
            duration_months="4",
            frequency_nights_per_week="4",
            isi_score="16",
            type="sleep_onset",
            cbti_response="inadequate",
            age_over_65=True,
            hepatic_impairment=True,
            comorbid_substance=True,
            comorbid_depression=True,
        )
    )
    assert r["severity"] == "moderate"
    # orexin blocked by age/hepatic; doxepin blocked by sleep_onset type
    assert not any("Suvorexant" in s for s in r["firstLine"])
    assert not any("Doxepin" in s for s in r["firstLine"])
    # no combination note (inadequate, not partial)
    assert not any("AASM April 2026 CPG: Combination" in s for s in r["firstLine"])
    # substance blocks z-drugs; depression still adds trazodone
    assert r["secondLine"] == [
        "Trazodone 50–150 mg — commonly used off-label; limited RCT evidence"
    ]
    # avoid additions from age + substance, before the static three
    assert r["avoidList"] == [
        "Benzodiazepines (fall risk, cognitive impairment — AASM: Against)",
        "Z-drugs at standard doses (reduce dose by 50% — AASM: Conditional)",
        "Diphenhydramine (Benadryl) — AASM: Against; anticholinergic risk",
        "Benzodiazepines and Z-drugs (abuse potential)",
        "OTC antihistamines (diphenhydramine, doxylamine) — AASM: Against for chronic insomnia",
        "Melatonin — AASM: Weak evidence for chronic insomnia; not recommended as primary treatment",
        "Tryptophan, valerian — AASM: Insufficient evidence",
    ]
    assert any("CBT-I trial: Inadequate response" in s for s in r["keyFindings"])
    assert any("Comorbid depression" in s for s in r["keyFindings"])


def test_chronic_but_not_tried_appeal_moderate():
    # chronic criteria met but cbti not tried -> appealStrength moderate, authRequired False
    r = assess(
        _base(
            duration_months="3",
            frequency_nights_per_week="3",
            daytime_impairment=True,
            cbti_response="not_tried",
        )
    )
    assert r["isChronicInsomnia"] is True
    assert r["authRequired"] is False
    assert r["appealStrength"] == "moderate"


def test_daytime_impairment_false_breaks_chronic():
    r = assess(
        _base(
            duration_months="12",
            frequency_nights_per_week="7",
            daytime_impairment=False,
        )
    )
    assert r["isChronicInsomnia"] is False


def test_pregnancy_avoid_all_agents():
    r = assess(_base(pregnancy=True))
    assert r["avoidList"][0] == (
        "All pharmacologic agents — safety data insufficient; CBT-I is first-line"
    )


def test_contraindicated_cbti_treated_like_not_tried():
    # cbti_response "contraindicated" != "not_tried" -> authRequired True, no warning,
    # but no pharmacotherapy block (only partial/inadequate trigger meds)
    r = assess(_base(cbti_response="contraindicated", duration_months="6",
                     frequency_nights_per_week="5"))
    assert r["authRequired"] is True
    assert r["appealStrength"] == "strong"
    assert not any("CBT-I should be attempted" in s for s in r["firstLine"])
    assert r["secondLine"] == []
    # keyFinding for cbti trial uses "Inadequate response" since not "partial"
    assert any("CBT-I trial: Inadequate response" in s for s in r["keyFindings"])
