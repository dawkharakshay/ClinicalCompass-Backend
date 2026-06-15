"""Radiation Oncology Clinical Compass — ported 1:1 from
old_static_code/server/rad-onc.test.ts (oracle cases).
"""

import json

from app.recommendations.modules.radonc import assess

# Defaults mirror createDefaultRadOncInput(): real bools for checkboxes,
# numbers default to 0, strings default to "".
_DEFAULT = {
    "diseaseCategory": "",
    "histology": "",
    "clinicalStage": "",
    "metastatic": False,
    "cnsHistology": "",
    "kpsScore": 0,
    "idh1Mutated": False,
    "mgmtMethylated": False,
    "brainMetsCount": 0,
    "brainMetsMaxDiameter": 0,
    "hnSite": "",
    "hpvStatus": "Unknown",
    "hnT": "",
    "hnN": "",
    "hnM": "",
    "postOpMargins": "Unknown",
    "ece": False,
    "lungHistology": "",
    "lungStage": "",
    "medicallyInoperable": False,
    "pdl1Expression": 0,
    "egfrMutation": False,
    "alk": False,
    "limitedVsExtensive": "",
    "prostateRiskGroup": "",
    "gleasonScore": 0,
    "psaAtDx": 0,
    "pelvicNodeInvolvement": False,
    "priorProstatectomy": False,
    "biochemicalRecurrence": False,
    "psmaPositive": False,
    "esophagealLocation": "",
    "gastricResectable": False,
    "gastricHer2": False,
    "esophagealHistology": "",
    "rectalT": "",
    "rectalN": "",
    "rectalDistanceFromVerge": 0,
    "rectalMRFInvolvement": False,
    "rectalWatchAndWait": False,
    "lymphomaType": "",
    "lymphomaStage": "",
    "bulkyDisease": False,
    "petCrAfterChemo": False,
    "deauvilleScore": 0,
    "hccChildPugh": "",
    "hccBCLC": "",
    "hccTumorCount": 0,
    "hccMaxDiameter": 0,
    "hccPortalVeinThrombosis": False,
    "hccPriorTACE": False,
    "hccTransplantCandidate": False,
    "breastStage": "",
    "breastSurgery": "None",
    "breastReceptorStatus": "",
    "breastNodePositive": False,
    "breastAge": 0,
    "breastLVI": False,
    "breastCloseMargins": False,
    "breastPreopRT": False,
    "skinType": "",
    "skinHighRisk": False,
    "skinImmuncompromised": False,
    "skinUnresectable": False,
    "palliativeIntent": "",
    "oligoMetCount": 0,
    "oligoPrimaryControlled": False,
    "ecogPs": 0,
    "priorRTSite": False,
}


def make(overrides):
    return assess({**_DEFAULT, **overrides})


def alltext(r):
    return json.dumps(r).lower()


# ─── CNS — GBM ──────────────────────────────────────────────────────────────


def test_gbm_standard_stupp():
    r = make({"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 80, "mgmtMethylated": False})
    assert r["diseaseCategory"] == "cns"
    assert r["rtRole"] == "Definitive"
    assert "60 Gy" in r["primaryRecommendation"]["doseRegimen"]
    assert "temozolomide" in r["primaryRecommendation"]["concurrentSystemic"].lower()
    assert len(r["references"]) > 0


def test_gbm_mgmt_methylated():
    r = make({"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 80, "mgmtMethylated": True})
    assert r["rtRole"] == "Definitive"
    assert "60 Gy" in r["primaryRecommendation"]["doseRegimen"]


def test_gbm_elderly_poor_kps():
    r = make({"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 50, "mgmtMethylated": True})
    assert r["rtRole"] == "Definitive"
    import re
    assert re.search(r"40|34|25", r["primaryRecommendation"]["doseRegimen"])


def test_gbm_category1():
    r = make({"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 80})
    import re
    assert re.search(r"Category 1|1", r["nccnCategory"])


# ─── CNS — LGG ──────────────────────────────────────────────────────────────


def test_lgg_idh_mutant():
    r = make({"diseaseCategory": "cns", "cnsHistology": "LGG", "idh1Mutated": True, "kpsScore": 90})
    assert r["rtRole"] in ["Definitive", "Adjuvant", "Insufficient data"]
    import re
    assert re.search(r"lgg|low.grade|glioma|45|50|54|pcv|temozolomide", alltext(r))


# ─── CNS — Brain Mets ───────────────────────────────────────────────────────


def test_brain_mets_limited_srs():
    r = make({"diseaseCategory": "cns", "cnsHistology": "Brain_Mets", "brainMetsCount": 2, "brainMetsMaxDiameter": 2.5, "kpsScore": 80})
    assert r["rtRole"] == "Definitive"
    assert "SRS" in r["primaryRecommendation"]["technique"]


def test_brain_mets_multiple():
    r = make({"diseaseCategory": "cns", "cnsHistology": "Brain_Mets", "brainMetsCount": 12, "brainMetsMaxDiameter": 1.5, "kpsScore": 40})
    assert r["rtRole"] in ["Palliative", "Definitive"]


# ─── Head & Neck ────────────────────────────────────────────────────────────


def test_hn_hpv_pos_oropharynx():
    r = make({"diseaseCategory": "head_neck", "hnSite": "Oropharynx", "hpvStatus": "Positive", "hnT": "T2", "hnN": "N1", "hnM": "M0"})
    assert r["rtRole"] == "Definitive"
    assert "IMRT" in r["primaryRecommendation"]["technique"]
    assert "cisplatin" in r["primaryRecommendation"]["concurrentSystemic"].lower()


def test_hn_hpv_deescalation_note():
    r = make({"diseaseCategory": "head_neck", "hnSite": "Oropharynx", "hpvStatus": "Positive", "hnT": "T1", "hnN": "N0", "hnM": "M0"})
    import re
    assert re.search(r"de-escal|reduced dose|60 gy|54 gy", alltext(r))


def test_hn_postop_ece_margins():
    r = make({"diseaseCategory": "head_neck", "hnSite": "Oral_Cavity", "hpvStatus": "Negative", "hnT": "T3", "hnN": "N2b", "hnM": "M0", "ece": True, "postOpMargins": "Positive"})
    assert r["rtRole"] in ["Adjuvant", "Definitive"]
    assert "cisplatin" in r["primaryRecommendation"]["concurrentSystemic"].lower()


def test_hn_larynx_t1_2():
    r = make({"diseaseCategory": "head_neck", "hnSite": "Larynx", "hpvStatus": "Unknown", "hnT": "T2", "hnN": "N0", "hnM": "M0"})
    assert r["rtRole"] == "Definitive"
    import re
    assert re.search(r"63|66|70", r["primaryRecommendation"]["doseRegimen"])


# ─── NSCLC ──────────────────────────────────────────────────────────────────


def test_nsclc_ia_inoperable_sbrt():
    r = make({"diseaseCategory": "nsclc", "lungStage": "IA", "medicallyInoperable": True, "lungHistology": "Adenocarcinoma"})
    assert r["rtRole"] == "Definitive"
    assert "SBRT" in r["primaryRecommendation"]["technique"]
    import re
    assert re.search(r"54|48|50|60", r["primaryRecommendation"]["doseRegimen"])


def test_nsclc_iiia_durvalumab():
    r = make({"diseaseCategory": "nsclc", "lungStage": "IIIA", "medicallyInoperable": False, "lungHistology": "Squamous", "pdl1Expression": 30})
    assert r["rtRole"] == "Definitive"
    import re
    assert re.search(r"60|66", r["primaryRecommendation"]["doseRegimen"])
    assert re.search(r"durvalumab|consolidat", alltext(r))


def test_nsclc_iva_palliative():
    r = make({"diseaseCategory": "nsclc", "lungStage": "IVA", "metastatic": True, "lungHistology": "Adenocarcinoma"})
    assert r["rtRole"] in ["Palliative", "Definitive", "Insufficient data"]


def test_nsclc_references_nccn():
    r = make({"diseaseCategory": "nsclc", "lungStage": "IIIA"})
    refs = [ref["citation"].lower() for ref in r["references"]]
    assert any("nccn" in c for c in refs)


# ─── SCLC ───────────────────────────────────────────────────────────────────


def test_sclc_limited():
    r = make({"diseaseCategory": "sclc", "limitedVsExtensive": "Limited"})
    assert r["rtRole"] == "Definitive"
    import re
    assert re.search(r"pci|prophylactic cranial", alltext(r))
    assert re.search(r"cisplatin|etoposide", alltext(r))


def test_sclc_extensive():
    r = make({"diseaseCategory": "sclc", "limitedVsExtensive": "Extensive"})
    assert r["rtRole"] in ["Consolidation", "Palliative", "Definitive"]


# ─── Prostate ───────────────────────────────────────────────────────────────


def test_prostate_low():
    r = make({"diseaseCategory": "prostate", "prostateRiskGroup": "Low", "gleasonScore": 6, "psaAtDx": 8})
    import re
    assert re.search(r"active surveillance|observation|watchful", alltext(r))


def test_prostate_intermediate_unfavorable():
    r = make({"diseaseCategory": "prostate", "prostateRiskGroup": "Intermediate_Unfavorable", "gleasonScore": 7, "psaAtDx": 12})
    assert r["rtRole"] == "Definitive"
    import re
    assert re.search(r"adt|androgen deprivation", alltext(r))


def test_prostate_high():
    r = make({"diseaseCategory": "prostate", "prostateRiskGroup": "High", "gleasonScore": 8, "psaAtDx": 25})
    assert r["rtRole"] == "Definitive"
    import re
    assert re.search(r"adt|androgen deprivation|2.year|long.term", alltext(r))


def test_prostate_bcr_salvage():
    r = make({"diseaseCategory": "prostate", "prostateRiskGroup": "High", "biochemicalRecurrence": True, "priorProstatectomy": True})
    assert r["rtRole"] in ["Adjuvant", "Definitive"]
    import re
    assert re.search(r"salvage|post.prostatectomy|adjuvant", alltext(r))


def test_prostate_favorable_intermediate_sbrt():
    r = make({"diseaseCategory": "prostate", "prostateRiskGroup": "Intermediate_Favorable", "gleasonScore": 7, "psaAtDx": 9})
    import re
    assert re.search(r"sbrt|hypofractionat", alltext(r))


# ─── Esophageal ─────────────────────────────────────────────────────────────


def test_esophageal_scc():
    r = make({"diseaseCategory": "esophageal", "esophagealHistology": "SCC", "esophagealLocation": "Middle"})
    assert r["rtRole"] in ["Neoadjuvant", "Definitive"]
    import re
    assert re.search(r"cross|41.4|carboplatin|paclitaxel", alltext(r))


def test_esophageal_adeno_gej():
    r = make({"diseaseCategory": "esophageal", "esophagealHistology": "Adenocarcinoma", "esophagealLocation": "Lower_GEJ"})
    assert r["rtRole"] in ["Neoadjuvant", "Definitive"]


# ─── Gastric ────────────────────────────────────────────────────────────────


def test_gastric_resectable():
    r = make({"diseaseCategory": "gastric", "gastricResectable": True, "gastricHer2": False})
    assert r["rtRole"] in ["Adjuvant", "Neoadjuvant", "Definitive"]
    import re
    assert re.search(r"astro|gastric", alltext(r))


# ─── Rectal ─────────────────────────────────────────────────────────────────


def test_rectal_t3n1_tnt():
    r = make({"diseaseCategory": "rectal", "rectalT": "T3", "rectalN": "N1", "rectalDistanceFromVerge": 6, "rectalMRFInvolvement": False})
    assert r["rtRole"] in ["Neoadjuvant", "Definitive"]
    import re
    assert re.search(r"tnt|total neoadjuvant|neoadjuvant", alltext(r))


def test_rectal_t4_mrf():
    r = make({"diseaseCategory": "rectal", "rectalT": "T4", "rectalN": "N2", "rectalMRFInvolvement": True, "rectalDistanceFromVerge": 4})
    assert r["rtRole"] in ["Neoadjuvant", "Definitive"]
    import re
    assert re.search(r"45|50|54|long.course", alltext(r))


def test_rectal_watch_and_wait():
    r = make({"diseaseCategory": "rectal", "rectalT": "T2", "rectalN": "N0", "rectalWatchAndWait": True})
    import re
    assert re.search(r"rectal|crt|neoadjuvant|watch|organ.preserv|surgery", alltext(r))


# ─── Lymphoma ───────────────────────────────────────────────────────────────


def test_lymphoma_hodgkin_isrt():
    r = make({"diseaseCategory": "lymphoma", "lymphomaType": "Hodgkin", "lymphomaStage": "II", "bulkyDisease": False, "petCrAfterChemo": True, "deauvilleScore": 2})
    assert r["rtRole"] in ["Adjuvant", "Consolidation", "Definitive"]
    import re
    assert re.search(r"isrt|involved.site|20 gy|30 gy", alltext(r))


def test_lymphoma_hodgkin_bulky():
    r = make({"diseaseCategory": "lymphoma", "lymphomaType": "Hodgkin", "lymphomaStage": "II", "bulkyDisease": True, "petCrAfterChemo": False, "deauvilleScore": 4})
    import re
    assert re.search(r"30|36 gy|isrt", alltext(r))


def test_lymphoma_dlbcl():
    r = make({"diseaseCategory": "lymphoma", "lymphomaType": "DLBCL", "lymphomaStage": "I", "bulkyDisease": False, "petCrAfterChemo": True})
    assert r["rtRole"] in ["Consolidation", "Adjuvant", "Definitive"]


def test_lymphoma_follicular():
    r = make({"diseaseCategory": "lymphoma", "lymphomaType": "Follicular", "lymphomaStage": "I", "bulkyDisease": False})
    assert r["rtRole"] in ["Definitive", "Adjuvant", "Consolidation", "Insufficient data"]
    import re
    assert re.search(r"follicular|lymphoma|rt|isrt|24 gy", alltext(r))


# ─── HCC ────────────────────────────────────────────────────────────────────


def test_hcc_bclc_a_childpugh_a():
    r = make({"diseaseCategory": "hcc", "hccBCLC": "A", "hccChildPugh": "A", "hccTumorCount": 1, "hccMaxDiameter": 4, "hccTransplantCandidate": False})
    assert r["rtRole"] in ["Definitive", "Adjuvant"]
    assert "SBRT" in r["primaryRecommendation"]["technique"]


def test_hcc_transplant_candidate():
    r = make({"diseaseCategory": "hcc", "hccBCLC": "A", "hccChildPugh": "A", "hccTumorCount": 1, "hccMaxDiameter": 3, "hccTransplantCandidate": True})
    import re
    assert re.search(r"bridge|transplant|sbrt", alltext(r))


def test_hcc_pvt():
    r = make({"diseaseCategory": "hcc", "hccBCLC": "C", "hccChildPugh": "A", "hccPortalVeinThrombosis": True, "hccTumorCount": 2, "hccMaxDiameter": 6})
    import re
    assert re.search(r"portal vein|pvt|sbrt|rt", alltext(r))


# ─── Breast ─────────────────────────────────────────────────────────────────


def test_breast_lumpectomy():
    r = make({"diseaseCategory": "breast", "breastStage": "I", "breastSurgery": "Lumpectomy", "breastReceptorStatus": "HR+HER2-", "breastNodePositive": False, "breastAge": 55})
    assert r["rtRole"] == "Adjuvant"
    import re
    assert re.search(r"hypofractionat|40 gy|42.5 gy|whole breast", alltext(r))


def test_breast_mastectomy_node_pos():
    r = make({"diseaseCategory": "breast", "breastStage": "II", "breastSurgery": "Mastectomy", "breastReceptorStatus": "TNBC", "breastNodePositive": True, "breastAge": 45})
    assert r["rtRole"] == "Adjuvant"
    import re
    assert re.search(r"pmrt|post.mastectomy|chest wall", alltext(r))


def test_breast_apbi_eligible():
    r = make({"diseaseCategory": "breast", "breastStage": "I", "breastSurgery": "Lumpectomy", "breastReceptorStatus": "HR+HER2-", "breastNodePositive": False, "breastAge": 60, "breastLVI": False, "breastCloseMargins": False})
    import re
    assert re.search(r"apbi|accelerated partial|brachytherapy|sbrt", alltext(r))


def test_breast_preop():
    r = make({"diseaseCategory": "breast", "breastStage": "II", "breastSurgery": "None", "breastReceptorStatus": "TNBC", "breastPreopRT": True})
    import re
    assert re.search(r"preoperative|neoadjuvant|astro", alltext(r))


# ─── Skin ───────────────────────────────────────────────────────────────────


def test_skin_bcc_unresectable():
    r = make({"diseaseCategory": "skin", "skinType": "BCC", "skinUnresectable": True, "skinHighRisk": True})
    assert r["rtRole"] == "Definitive"
    import re
    assert re.search(r"60|66|70|electron|orthovoltage|imrt", alltext(r))


def test_skin_cscc_highrisk_postop():
    r = make({"diseaseCategory": "skin", "skinType": "cSCC", "skinHighRisk": True, "skinUnresectable": False})
    assert r["rtRole"] in ["Adjuvant", "Definitive"]


def test_skin_immunocompromised():
    r = make({"diseaseCategory": "skin", "skinType": "cSCC", "skinHighRisk": True, "skinImmuncompromised": True})
    import re
    assert re.search(r"immunocompromised|immunosuppress", alltext(r))


# ─── Palliative / Oligometastatic ───────────────────────────────────────────


def test_palliative_bone():
    r = make({"diseaseCategory": "palliative", "palliativeIntent": "Bone", "ecogPs": 2})
    assert r["rtRole"] == "Palliative"
    import re
    assert re.search(r"8 gy|30 gy|single fraction|3 gy", alltext(r))


def test_palliative_cord_compression():
    r = make({"diseaseCategory": "palliative", "palliativeIntent": "Cord_Compression", "ecogPs": 2})
    assert r["rtRole"] == "Palliative"
    import re
    assert re.search(r"cord|compression|urgent|24 hour", alltext(r))
    assert len(r["urgentFlags"]) > 0


def test_oligomets():
    r = make({"diseaseCategory": "palliative", "palliativeIntent": "Oligomets", "oligoMetCount": 3, "oligoPrimaryControlled": True, "ecogPs": 1})
    assert r["rtRole"] in ["Definitive", "Palliative"]
    import re
    assert re.search(r"sbrt|sabr|stereotactic", alltext(r))


def test_reirradiation_flag():
    r = make({"diseaseCategory": "palliative", "palliativeIntent": "Bone", "priorRTSite": True, "ecogPs": 2})
    import re
    assert re.search(r"re.irradiation|reirradiation|prior rt|cumulative dose", alltext(r))


# ─── MDT ────────────────────────────────────────────────────────────────────


def test_mdt_gbm():
    r = make({"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 80})
    mdt = [m.lower() for m in r["multidisciplinaryConsult"]]
    assert any("neurosurg" in m or "neuro-oncol" in m for m in mdt)


def test_mdt_prostate():
    r = make({"diseaseCategory": "prostate", "prostateRiskGroup": "High", "gleasonScore": 9})
    mdt = [m.lower() for m in r["multidisciplinaryConsult"]]
    assert any("urol" in m for m in mdt)


def test_mdt_breast():
    r = make({"diseaseCategory": "breast", "breastStage": "II", "breastSurgery": "Mastectomy", "breastNodePositive": True})
    mdt = [m.lower() for m in r["multidisciplinaryConsult"]]
    assert any("oncol" in m for m in mdt)


# ─── Safety ─────────────────────────────────────────────────────────────────


def test_safety_present():
    sites = [
        {"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 80},
        {"diseaseCategory": "nsclc", "lungStage": "IIIA"},
        {"diseaseCategory": "prostate", "prostateRiskGroup": "High"},
        {"diseaseCategory": "breast", "breastStage": "I", "breastSurgery": "Lumpectomy"},
    ]
    for s in sites:
        r = make(s)
        assert len(r["safetyConsiderations"]) > 0


# ─── References ─────────────────────────────────────────────────────────────


def test_references_min2():
    sites = [
        {"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 80},
        {"diseaseCategory": "head_neck", "hnSite": "Oropharynx", "hpvStatus": "Positive", "hnT": "T2", "hnN": "N1", "hnM": "M0"},
        {"diseaseCategory": "nsclc", "lungStage": "IIIA"},
        {"diseaseCategory": "sclc", "limitedVsExtensive": "Limited"},
        {"diseaseCategory": "prostate", "prostateRiskGroup": "High"},
        {"diseaseCategory": "esophageal", "esophagealHistology": "SCC", "esophagealLocation": "Middle"},
        {"diseaseCategory": "gastric", "gastricResectable": True},
        {"diseaseCategory": "rectal", "rectalT": "T3", "rectalN": "N1"},
        {"diseaseCategory": "lymphoma", "lymphomaType": "Hodgkin", "lymphomaStage": "II"},
        {"diseaseCategory": "hcc", "hccBCLC": "A", "hccChildPugh": "A", "hccTumorCount": 1},
        {"diseaseCategory": "breast", "breastStage": "I", "breastSurgery": "Lumpectomy"},
        {"diseaseCategory": "skin", "skinType": "BCC", "skinUnresectable": True},
        {"diseaseCategory": "palliative", "palliativeIntent": "Bone"},
    ]
    for s in sites:
        r = make(s)
        assert len(r["references"]) >= 2


def test_nccn_cited():
    sites = [
        {"diseaseCategory": "nsclc", "lungStage": "IIIA"},
        {"diseaseCategory": "prostate", "prostateRiskGroup": "High"},
        {"diseaseCategory": "cns", "cnsHistology": "GBM", "kpsScore": 80},
    ]
    for s in sites:
        r = make(s)
        refs = [ref["citation"].lower() for ref in r["references"]]
        assert any("nccn" in c for c in refs)


def test_astro_cited():
    sites = [
        {"diseaseCategory": "gastric", "gastricResectable": True},
        {"diseaseCategory": "breast", "breastStage": "I", "breastSurgery": "Lumpectomy"},
        {"diseaseCategory": "skin", "skinType": "cSCC", "skinHighRisk": True},
    ]
    for s in sites:
        r = make(s)
        assert "astro" in alltext(r)
