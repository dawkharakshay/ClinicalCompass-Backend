"""Extract the Denial Template Library (a cross-module catalog of pre-written
appeal paragraphs, organized by denial reason) from the legacy code into a
single shared JSON file.

Source: old_static_code/client/src/lib/denialTemplates.ts
  - DENIAL_CATEGORIES : 12 denial-reason categories ({value, label, color})
  - DENIAL_TEMPLATES  : 36 templates ({id, category, title, denialReason,
                        applicableTo[], text, references[]})

This is a global library (not per-module), so it is emitted as one file rather
than the per-module pattern used for auth guides / appeal letters / recommendations.

Output: forms/denial_templates.json

    uv run python scripts/build_denial_templates.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "old_static_code" / "client" / "src" / "lib" / "denialTemplates.ts"
OUT = ROOT / "forms" / "denial_templates.json"

_CATEGORY = re.compile(
    r"\{\s*value:\s*'([^']*)',\s*label:\s*'([^']*)',\s*color:\s*'([^']*)'\s*\}"
)
_TEMPLATE = re.compile(
    r"id:\s*'(?P<id>[^']*)',\s*"
    r"category:\s*'(?P<category>[^']*)',\s*"
    r"title:\s*'(?P<title>[^']*)',\s*"
    r"denialReason:\s*'(?P<denialReason>[^']*)',\s*"
    r"applicableTo:\s*\[(?P<applicableTo>[^\]]*)\],\s*"
    r"text:\s*`(?P<text>.*?)`,\s*"
    r"references:\s*\[(?P<references>[^\]]*)\],?",
    re.S,
)


def _str_array(raw: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"'([^']*)'", raw)]


def run() -> None:
    text = SRC.read_text(encoding="utf-8")

    # Categories live in the DENIAL_CATEGORIES block; templates after it.
    cat_blob = text[text.index("DENIAL_CATEGORIES"):text.index("DENIAL_TEMPLATES")]
    tpl_blob = text[text.index("DENIAL_TEMPLATES"):]

    categories = [
        {"value": v, "label": lbl, "color": color}
        for v, lbl, color in _CATEGORY.findall(cat_blob)
    ]
    templates = []
    for m in _TEMPLATE.finditer(tpl_blob):
        templates.append({
            "id": m.group("id"),
            "category": m.group("category"),
            "title": m.group("title"),
            "denialReason": m.group("denialReason"),
            "applicableTo": _str_array(m.group("applicableTo")),
            "text": m.group("text"),
            "references": _str_array(m.group("references")),
        })

    # Integrity: category counts in source vs parsed, and every template's
    # category must be a declared category value.
    declared = {c["value"] for c in categories}
    unknown = sorted({t["category"] for t in templates} - declared)
    assert len(categories) == 12, f"expected 12 categories, got {len(categories)}"
    assert len(templates) == 36, f"expected 36 templates, got {len(templates)}"
    assert not unknown, f"templates reference undeclared categories: {unknown}"

    payload = {
        "sourceFile": "client/src/lib/denialTemplates.ts",
        "description": "Cross-module library of pre-written appeal paragraphs, "
                       "organized by denial reason, inserted into appeal letters.",
        "categories": categories,
        "templates": templates,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    by_cat = {c["value"]: sum(1 for t in templates if t["category"] == c["value"])
              for c in categories}
    print(f"[build_denial_templates] wrote {OUT.relative_to(ROOT)} "
          f"({len(categories)} categories, {len(templates)} templates)")
    for v, n in by_cat.items():
        print(f"    {n:>2}  {v}")


if __name__ == "__main__":
    run()
