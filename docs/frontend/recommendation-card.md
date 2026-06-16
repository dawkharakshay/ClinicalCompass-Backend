# Recommendation Card — uniform API contract

`GET /submissions/{id}/recommendation` returns `result`: a **single, uniform JSON
shape** that every module produces, regardless of specialty. The frontend renders
it **generically** — it never needs per-module code. Optional pieces (`score`,
`badges`, `sections`) are simply absent when a module doesn't use them.

```
{ submission_id, module_id, logic_key, result: <RecommendationCard> }
```

This document describes `result` (the `RecommendationCard`).

---

## 1. The envelope

| Field | Type | Always present? | Renders as |
|---|---|---|---|
| `module` | string | yes | (not shown — the logicKey, for analytics) |
| `title` | string | yes | Card headline (the primary recommendation) |
| `subtitle` | string \| null | no | Sub-headline under the title |
| `badges` | `Badge[]` | yes (may be `[]`) | Row of colored chips (evidence level, COR/LOE, urgency, severity…) |
| `score` | `Score` \| null | no | Labeled progress bar. **`null` ⇒ render no bar** |
| `alerts` | `Alert[]` | yes (may be `[]`) | Colored callouts (urgent flags, warnings, contraindications) |
| `summary` | string \| null | no | Rationale paragraph |
| `sections` | `Section[]` | yes (may be `[]`) | Ordered content blocks — the module-specific body |
| `nextSteps` | string[] | yes (may be `[]`) | Numbered list |
| `evidence` | `Reference[]` | yes (may be `[]`) | Reference list (with PubMed links) |
| `guidelineSource` | string \| null | no | Small print under the card |

**Golden rule for the frontend:** iterate `badges`, then `score` (if not null),
then `alerts`, then `summary`, then `sections` in order, then `nextSteps`, then
`evidence`. Never hard-code a module name.

---

## 2. Sub-types

```ts
type Tone = "neutral" | "info" | "success" | "warning" | "danger";

interface Badge {
  label: string;   // e.g. "Evidence", "COR", "Urgency"
  value: string;   // e.g. "Category 2A", "I", "Urgent"
  tone: Tone;      // chip color
}

type ScoreLevel = "high" | "moderate" | "low-moderate" | "low";
interface Score {
  label: string;              // e.g. "Organ Preservation Score"
  value: number;              // e.g. 50
  max: number | null;         // e.g. 100; null when the scale has no fixed max
  level: ScoreLevel | null;   // bar color tier; null when higher≠better (render neutral)
  note?: string | null;       // short interpretation under the bar
}

interface Alert {
  tone: Tone;            // danger = urgent flag, warning = caution
  title?: string | null; // e.g. "Urgent", "Contraindications"
  items: string[];       // one bullet per string
}

type SectionType = "text" | "list" | "keyvalue";
type SectionIcon = "check" | "x" | "warning" | "arrow" | "info" | null;
interface KeyValue { key: string; value: string; }
interface Section {
  id: string;            // stable slug, e.g. "treatment_pathway"
  label: string;         // heading shown, e.g. "Treatment Pathway"
  type: SectionType;
  tone?: Tone;           // optional heading/accent color
  icon?: SectionIcon;    // optional list-item icon (for type "list")
  content?: string | null;        // for type "text"
  items?: (string | KeyValue)[];  // for type "list" (string[]) or "keyvalue" (KeyValue[])
}

interface Reference {
  title: string;
  source?: string | null;       // authors / journal
  description?: string | null;
  pmid?: string | null;         // link to https://pubmed.ncbi.nlm.nih.gov/<pmid>/
}

interface RecommendationCard {
  module: string;
  title: string;
  subtitle?: string | null;
  badges: Badge[];
  score?: Score | null;
  alerts: Alert[];
  summary?: string | null;
  sections: Section[];
  nextSteps: string[];
  evidence: Reference[];
  guidelineSource?: string | null;
}
```

---

## 3. Render guide (one component per piece)

| Piece | How to render |
|---|---|
| `badges[]` | Chips. Color by `tone`: neutral=grey, info=blue, success=green, warning=amber, danger=red. |
| `score` | Progress bar `value/max`. Bar color by `level`: high=green, moderate=yellow, low-moderate=orange, low=red; **`level: null` ⇒ neutral bar** (used where a higher number isn't "better", e.g. HAS-BLED). `max: null` ⇒ show the value without a fraction. Show `label` above, `note` below. If `score` itself is `null`, render nothing. |
| `alerts[]` | Callout boxes colored by `tone` (danger/warning most common). Show `title` then bulleted `items`. |
| `summary` | Muted paragraph. |
| `sections[]` | For each: heading = `label` (accent `tone`/`icon` if given). Then by `type`: `text` → paragraph from `content`; `list` → bulleted `items` (use `icon` per item if set); `keyvalue` → two-column rows from `items`. |
| `nextSteps[]` | Numbered (`1. 2. 3.`) list. |
| `evidence[]` | List; each row: `title` (link to PubMed if `pmid`), `source`, `description`. |
| `guidelineSource` | Small footnote. |

The frontend only needs to implement these ~7 renderers **once**. Every module —
all 101 — flows through them.

---

## 4. Example A — module WITH a score (Rectal Cancer)

Real output for a T3N1, mid-rectum, MRF-clear submission:

```json
{
  "submission_id": 1,
  "module_id": 1,
  "logic_key": "rectalcancer",
  "result": {
    "module": "rectalcancer",
    "title": "Standard Neoadjuvant CRT → TME",
    "subtitle": null,
    "badges": [
      { "label": "Evidence", "value": "Category 2A", "tone": "info" },
      { "label": "Urgency", "value": "Routine", "tone": "neutral" }
    ],
    "score": {
      "label": "Organ Preservation Score",
      "value": 50,
      "max": 100,
      "level": "moderate",
      "note": "Moderate — organ preservation possible, depends on response"
    },
    "alerts": [],
    "summary": "Standard neoadjuvant CRT followed by TME for intermediate-risk locally advanced rectal cancer.",
    "sections": [
      { "id": "surgical_approach", "label": "Surgical Approach", "type": "text",
        "content": "Low Anterior Resection (LAR) with TME" },
      { "id": "watch_and_wait", "label": "Watch-and-Wait", "type": "text", "tone": "neutral",
        "content": "Not indicated" }
    ],
    "nextSteps": [
      "High-resolution MRI pelvis (3T preferred) for baseline staging",
      "Multidisciplinary tumor board discussion (surgery, radiation, medical oncology, radiology)",
      "Standard long-course CRT (45-50.4 Gy + capecitabine)",
      "Surgery (TME) 6-8 weeks after CRT completion",
      "Adjuvant chemotherapy discussion based on pathologic response"
    ],
    "evidence": [
      { "title": "NCCN Clinical Practice Guidelines in Oncology: Rectal Cancer v3.2024",
        "source": "National Comprehensive Cancer Network",
        "description": "Comprehensive guidelines for staging, neoadjuvant therapy, surgery, and watch-and-wait.",
        "pmid": "39151454" },
      { "title": "RAPIDO Trial: Short-course RT + consolidation chemotherapy vs standard CRT",
        "source": "Bahadoer RR et al. Lancet Oncol. 2021",
        "description": "Short-course RT then CAPOX improved pCR (28% vs 14%) and 3-year DFS.",
        "pmid": "33301740" }
    ],
    "guidelineSource": "NCCN Rectal Cancer v3.2024 (PMID: 39151454); ESMO Living Guideline 2025 (PMID: 40412553); ASCO 2025 (PMID: 39236282)"
  }
}
```

A high-risk submission would instead carry `"level": "low"` (red bar), an
`"Urgency": "Urgent"` badge with `tone: "danger"`, and populated `alerts`.

---

## 5. Example B — module WITHOUT a score (TKA)

Note `"score": null` (frontend draws no bar) and the use of `badges` (COR/LOE/
urgency) plus a `danger` alert for contraindications:

```json
{
  "submission_id": 42,
  "module_id": 88,
  "logic_key": "tka",
  "result": {
    "module": "tka",
    "title": "TKA Recommended",
    "subtitle": "Class I — Benefit >>> Risk",
    "badges": [
      { "label": "COR", "value": "I", "tone": "success" },
      { "label": "LOE", "value": "A", "tone": "info" },
      { "label": "Urgency", "value": "Appropriate", "tone": "neutral" }
    ],
    "score": null,
    "alerts": [
      { "tone": "danger", "title": "Contraindications",
        "items": ["Active knee/periarticular infection — must be treated first"] }
    ],
    "summary": "Severe tricompartmental knee OA (KL ≥3) with refractory pain and functional limitation despite ≥3 months of non-operative management.",
    "sections": [
      { "id": "rationale", "label": "Clinical Rationale", "type": "list", "icon": "check",
        "items": [
          "Kellgren-Lawrence grade 3-4 on weight-bearing radiographs",
          "Failed conservative therapy (NSAIDs, PT, intra-articular injections)"
        ] },
      { "id": "optimization", "label": "Optimization Recommendations", "type": "list",
        "items": ["BMI optimization if >40", "HbA1c <7.5% before surgery", "Smoking cessation 4+ weeks pre-op"] }
    ],
    "nextSteps": [
      "Pre-operative medical clearance",
      "Anesthesia consultation",
      "Schedule with orthopedic surgery"
    ],
    "evidence": [
      { "title": "AAOS Clinical Practice Guideline: Surgical Management of Osteoarthritis of the Knee",
        "source": "American Academy of Orthopaedic Surgeons", "description": null, "pmid": null }
    ],
    "guidelineSource": "AAOS CPG (2nd ed.); AUC for SMOAK"
  }
}
```

---

## 6. Example C — `keyvalue` section (Glaucoma target IOP)

Where the old UI showed a value (not a bar), use a `keyvalue` section:

```json
{
  "id": "target_iop",
  "label": "Target IOP Range",
  "type": "keyvalue",
  "items": [
    { "key": "Target", "value": "≤ 18 mmHg" },
    { "key": "Reduction from baseline", "value": "20–30%" }
  ]
}
```

---

## 6b. Kitchen-sink example — every field, type, and tone

Synthetic card that exercises **all** render paths in one payload: a subtitle, all
five badge tones, a score with a level, both alert tones, all three section types
(`text`, `list` with icons, `keyvalue`), next steps, and evidence with and without
a PMID. Use it as the frontend's visual test fixture.

```json
{
  "submission_id": 999,
  "module_id": 1,
  "logic_key": "demo",
  "result": {
    "module": "demo",
    "title": "Total Neoadjuvant Therapy (TNT) — Preferred",
    "subtitle": "High-risk locally advanced disease",
    "badges": [
      { "label": "Severity", "value": "Severe",      "tone": "danger"  },
      { "label": "COR",      "value": "I",           "tone": "success" },
      { "label": "Evidence", "value": "Category 2A", "tone": "info"    },
      { "label": "Strength", "value": "Conditional", "tone": "warning" },
      { "label": "Urgency",  "value": "Routine",     "tone": "neutral" }
    ],
    "score": {
      "label": "Organ Preservation Score",
      "value": 50,
      "max": 100,
      "level": "moderate",
      "note": "Moderate — organ preservation possible, depends on response"
    },
    "alerts": [
      { "tone": "danger",  "title": "Urgent Flags",
        "items": ["T4b with MRF involvement — multivisceral resection likely"] },
      { "tone": "warning", "title": "Key Warnings",
        "items": ["Prior pelvic RT: re-irradiation toxicity risk",
                  "IBD: increased radiation toxicity risk"] }
    ],
    "summary": "TNT preferred for high-risk locally advanced rectal cancer; short-course RT followed by consolidation chemotherapy improves pCR and disease-free survival.",
    "sections": [
      { "id": "surgical_approach", "label": "Surgical Approach", "type": "text",
        "content": "Low Anterior Resection (LAR) with total mesorectal excision." },

      { "id": "recommended_agents", "label": "Recommended Agents", "type": "list",
        "icon": "check",
        "items": ["Short-course RT (5×5 Gy)", "CAPOX × 6 cycles", "Restaging MRI at 8–12 weeks"] },

      { "id": "agents_to_avoid", "label": "Agents to Avoid", "type": "list",
        "icon": "x", "tone": "danger",
        "items": ["Concurrent high-dose NSAIDs during chemoradiation"] },

      { "id": "target_iop", "label": "Target IOP Range", "type": "keyvalue",
        "items": [
          { "key": "Target", "value": "≤ 18 mmHg" },
          { "key": "Reduction from baseline", "value": "20–30%" }
        ] }
    ],
    "nextSteps": [
      "High-resolution MRI pelvis (3T preferred) for baseline staging",
      "Multidisciplinary tumor board discussion",
      "Initiate TNT per protocol"
    ],
    "evidence": [
      { "title": "RAPIDO Trial: Short-course RT + consolidation chemotherapy",
        "source": "Bahadoer RR et al. Lancet Oncol. 2021",
        "description": "Improved pCR (28% vs 14%) and 3-year DFS for high-risk LARC.",
        "pmid": "33301740" },
      { "title": "AAOS Clinical Practice Guideline (no PMID example)",
        "source": "American Academy of Orthopaedic Surgeons",
        "description": null,
        "pmid": null }
    ],
    "guidelineSource": "NCCN Rectal Cancer v3.2024 (PMID: 39151454); ESMO Living Guideline 2025 (PMID: 40412553)"
  }
}
```

### Edge-case variants the frontend must also handle

```jsonc
// 1. No score at all (85 of 101 modules) -> draw no score widget
"score": null

// 2. Score where higher is NOT better (e.g. HAS-BLED) -> neutral bar, no fixed max
"score": { "label": "HAS-BLED", "value": 4, "max": 9, "level": null, "note": null }

// 3. Minimal card — every list empty, optionals null (still valid)
{
  "module": "x", "title": "Recommendation", "subtitle": null,
  "badges": [], "score": null, "alerts": [], "summary": null,
  "sections": [], "nextSteps": [], "evidence": [], "guidelineSource": null
}

// 4. Section with no icon/tone (most common) — just label + content/items
{ "id": "monitoring_plan", "label": "Monitoring Plan", "type": "list",
  "items": ["Restaging MRI at 8–12 weeks", "CEA every 3 months"] }
```

---

## 7. Notes for the dev

- **Empty arrays, not missing keys:** `badges`, `alerts`, `sections`, `nextSteps`,
  `evidence` are always arrays (possibly empty). `score`, `subtitle`,
  `guidelineSource` may be `null`. Code defensively but the shape is stable.
- **Order matters:** render `sections` in the order received — clinical sequencing
  is intentional.
- **Unknown future `type`/`tone`/`icon` values:** fall back to a plain
  paragraph/neutral chip rather than crashing, so new modules can't break the UI.
- **PubMed links:** `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` when `pmid` is set.
