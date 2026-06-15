"""No-data-loss verification gate for extracted auth guides.

For every guide in forms/auth_guides/_map.json, parse the source *AuthGuide.tsx
and the produced JSON, then assert that every CPT code and every ICD-10 code in
the source appears in the JSON (structured fields OR the verbatim `raw` block).
Also reports payer-block and table coverage as advisory signals.

Writes forms/auth_guides/_authguide_gaps.json and exits non-zero if any guide
loses a code or fails to parse.

    uv run python scripts/verify_auth_guides.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / "old_static_code"
GEN = ROOT / "forms" / "auth_guides"

CPT_RE = re.compile(r'"(\d{5})"')                      # 5-digit codes in quotes
ICD_RE = re.compile(r'"([A-TV-Z]\d{2}(?:\.\d{1,4})?)"')  # e.g. C64.1, M75.100, Z85.528


def codes_in_text(text: str) -> tuple[set[str], set[str]]:
    return set(CPT_RE.findall(text)), set(ICD_RE.findall(text))


def codes_in_json(guide: dict) -> tuple[set[str], set[str]]:
    """All codes anywhere in the auth_guide object (structured + raw), as strings."""
    blob = json.dumps(guide, ensure_ascii=False)
    # Match the same shapes, but JSON-escaped quotes are the same char here.
    cpt = set(re.findall(r'\b(\d{5})\b', blob))
    icd = set(re.findall(r'\b([A-TV-Z]\d{2}(?:\.\d{1,4})?)\b', blob))
    return cpt, icd


def run() -> int:
    mp = json.loads((GEN / "_map.json").read_text(encoding="utf-8"))
    rows = []
    failures = 0
    for g in mp["guides"]:
        out = GEN / g["outFile"]
        src = OLD / g["sourceFile"]
        rec = {"slug": g["slug"], "outFile": g["outFile"], "title": g.get("title"),
               "status": "ok", "issues": []}

        if not out.exists():
            rec["status"] = "MISSING_FILE"; rec["issues"].append("output JSON not written")
            failures += 1; rows.append(rec); continue
        try:
            payload = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            rec["status"] = "BAD_JSON"; rec["issues"].append(f"invalid JSON: {e}")
            failures += 1; rows.append(rec); continue

        guide = payload.get("auth_guide") or {}
        src_text = src.read_text(encoding="utf-8")
        src_cpt, src_icd = codes_in_text(src_text)
        j_cpt, j_icd = codes_in_json(guide)

        missing_cpt = sorted(src_cpt - j_cpt)
        missing_icd = sorted(src_icd - j_icd)
        rec.update({
            "src_cpt": len(src_cpt), "json_cpt": len(j_cpt),
            "src_icd": len(src_icd), "json_icd": len(j_icd),
            "structured_cpt": len(guide.get("cptCodes") or []),
            "structured_icd": len(guide.get("icd10Codes") or []),
            "payers": len(guide.get("payers") or []),
            "customSections": len(guide.get("customSections") or []),
            "raw_md_chars": len((guide.get("raw") or {}).get("markdown") or ""),
            "raw_tables": len((guide.get("raw") or {}).get("tables") or []),
        })
        if missing_cpt:
            rec["issues"].append(f"CPT codes in source missing from JSON: {missing_cpt}")
        if missing_icd:
            rec["issues"].append(f"ICD codes in source missing from JSON: {missing_icd}")
        # advisory: raw.markdown suspiciously short relative to source
        if rec["raw_md_chars"] < 0.15 * len(src_text):
            rec["issues"].append(
                f"raw.markdown short ({rec['raw_md_chars']} chars vs {len(src_text)} source) — possible summarization")
        if any("missing from JSON" in i for i in rec["issues"]):
            rec["status"] = "DATA_LOSS"; failures += 1
        elif rec["issues"]:
            rec["status"] = "warn"
        rows.append(rec)

    (GEN / "_authguide_gaps.json").write_text(
        json.dumps({"failures": failures, "guides": rows}, indent=2, ensure_ascii=False), encoding="utf-8")

    loss = [r for r in rows if r["status"] in ("DATA_LOSS", "BAD_JSON", "MISSING_FILE")]
    warn = [r for r in rows if r["status"] == "warn"]
    print(f"verified {len(rows)} guides | hard failures: {len(loss)} | warnings: {len(warn)}")
    for r in loss:
        print(f"  ✗ {r['slug']} [{r['status']}]: {'; '.join(r['issues'])}")
    for r in warn:
        print(f"  ⚠ {r['slug']}: {'; '.join(r['issues'])}")
    print("report: forms/auth_guides/_authguide_gaps.json")
    return 1 if loss else 0


if __name__ == "__main__":
    sys.exit(run())
