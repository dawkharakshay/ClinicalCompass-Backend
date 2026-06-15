"""Extract each module's result-generation logic (form data -> recommendation)
into per-module reference files, mirroring the auth_guide extraction.

Source: the "old data/<specialty>/*.md" spec files. Each has a verbatim
"## 3. Result-Generation Logic" section (narrative + the legacy *Logic.ts code).
We store that section as documentation; it is NOT executed. The legacy logic
source files are pulled from "old data/_manifest.json" (_src.logic).

Each output file is {"title": <module title>, "recommendation": {<reference>}}:

    {
      "title": "...",
      "recommendation": {
        "sourceFiles": ["client/src/lib/acsLogic.ts", ...],
        "hasLogic": true,
        "raw": { "markdown": "## 3. Result-Generation Logic ..." }
      }
    }

Output: forms/recommendations/<slug>.json (+ _recommendations_report.json),
seeded into Module.recommendation by scripts/seed_recommendations.py.

    uv run python scripts/build_recommendations.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD_DATA = ROOT / "old data"
MANIFEST = OLD_DATA / "_manifest.json"
OUT_DIR = ROOT / "forms" / "recommendations"

_H1 = re.compile(r"(?m)^#\s+(.+?)\s*$")
# The whole "## 3. ..." section, up to the next "## <n>." heading or EOF.
_SEC3 = re.compile(r"(?ms)^##\s*3\.\s.*?(?=^##\s*\d|\Z)")
_NO_LOGIC = re.compile(r"_No logic exists", re.I)
# Backtick-quoted .ts/.tsx source paths cited inline (e.g. "Source: `.../acsLogic.ts`").
_SRC_PATH = re.compile(r"`([^`]*\.tsx?)`")


def title_to_logic() -> dict[str, list[str]]:
    mani = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for sp in mani["specialties"]:
        for mod in sp["modules"]:
            out[mod["name"]] = (mod.get("_src") or {}).get("logic") or []
    return out


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logic_map = title_to_logic()
    mds = sorted(p for p in OLD_DATA.rglob("*.md") if not p.name.startswith("_"))

    written = 0
    stubs: list[str] = []
    no_h1: list[str] = []
    no_sec3: list[str] = []
    rows = []

    for p in mds:
        text = p.read_text(encoding="utf-8", errors="replace")
        h1 = _H1.search(text)
        if not h1:
            no_h1.append(p.name)
            continue
        title = h1.group(1).strip()
        m = _SEC3.search(text)
        if not m:
            no_sec3.append(p.name)
            continue
        section = m.group(0).strip()
        has_logic = not _NO_LOGIC.search(section)
        if not has_logic:
            stubs.append(title)

        # Union the manifest's logic list with any *Logic.ts paths cited inline
        # in the section, keeping only lib/logic sources and preserving order.
        cited = [s for s in _SRC_PATH.findall(section) if "Logic" in s or "/lib/" in s]
        seen: dict[str, None] = {}
        for s in list(logic_map.get(title, [])) + cited:
            seen.setdefault(s, None)
        source_files = list(seen)

        slug = p.stem
        payload = {
            "title": title,
            "recommendation": {
                "sourceFiles": source_files,
                "hasLogic": has_logic,
                "raw": {"markdown": section},
            },
        }
        (OUT_DIR / f"{slug}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        written += 1
        rows.append({"slug": slug, "title": title, "hasLogic": has_logic,
                     "sourceFiles": len(source_files), "chars": len(section)})

    report = {
        "written": written,
        "stubs_without_logic": sorted(stubs),
        "files_without_h1": no_h1,
        "files_without_section3": no_sec3,
        "guides": sorted(rows, key=lambda r: r["slug"]),
    }
    (OUT_DIR / "_recommendations_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[build_recommendations] written: {written} | substantive: {written - len(stubs)} | "
          f"stubs(no logic): {len(stubs)}")
    if no_h1 or no_sec3:
        print(f"  ! no H1: {no_h1} | no section 3: {no_sec3}")
    if stubs:
        print("  stubs:", ", ".join(stubs))


if __name__ == "__main__":
    run()
