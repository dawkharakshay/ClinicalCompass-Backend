# ClinicalCompass — Form Input Types (frontend reference)

Generated from the **live backend** (Postgres `modules.form`). **129 forms, 2,355 fields, 10 input types.**

Companion files:
- `forms-live.json` — every module's full form JSON (the real data to render).
- `input-types.json` — this spec, machine-readable.

## Form shape

`module.form` = `{ version, layout, submitLabel, logicKey, hiddenDefaults, steps[] }`.
Each step = `{ id, shortLabel, title, fields[] }`. (`logicKey` selects the backend recommendation engine — the UI can ignore it.)

Every field has `id`, `type`, `label`. **Input** fields also have `name` (the answer key written into the submission), and optionally `defaultValue`, `required` (bool), and `visibleWhen` (conditional visibility).

## The 10 types — 9 inputs + 1 display

| `type` | Count | Submits | Type-specific attributes | Widget |
|---|---|---|---|---|
| `checkbox` | 610 | `boolean` | — | checkbox |
| `switch` | 492 | `boolean` | — | toggle |
| `select` | 426 | option value | `options[]` | dropdown |
| `number` | 356 | `number` | `min`, `max`, `step`, `unit`, `placeholder`, `keyboardType` | numeric input |
| `radio` | 239 | option value | `options[]`, `optionLayout` | radio group |
| `slider` | 62 | `number` | `min`, `max`, `step`, `unit` | slider |
| `text` | 55 | `string` | `placeholder`, `multiline`, `keyboardType`, `unit` | text / textarea |
| `alert` | 49 | **nothing (display only)** | `text`, `severity` | banner (no `name`) |
| `multiselect` | 36 | `array` of option values | `options[]` | multi-select |
| `buttongroup` | 30 | option value | `options[]` | segmented buttons |

## Shared structures

### `options[]` (select / radio / buttongroup / multiselect)
Array of `{ label, value }`.
⚠️ **`value` keeps its native JSON type** — across the data: string ×2290, boolean ×340, int ×142, null ×3. **Do not stringify it**; submit it back as-is (so `select`/`radio` answers may be a string, number, boolean, or null; `multiselect` is an array of those).

### `visibleWhen` (on any field or alert — show/hide, evaluated client-side)
- **Leaf:** `{ field, op, value? }` where `op` ∈ `eq`, `ne`, `in` (`value` is an array), `gt`, `gte`, `truthy` (no `value`).
- **Combinators:** `{ all: [cond, …] }`, `{ any: [cond, …] }` — nestable.
- `field` references another field's `name` in the same form.

### Enums
- `keyboardType` (number/text): `decimal`, `numeric`
- `optionLayout` (radio): `row`, `column`
- `severity` (alert): `info`, `warning`, `error`

### `unit` (number / slider / text — display suffix, 46 values)
`%`, `/10`, `/min`, `Gy`, `bpm`, `cells/µL`, `cm`, `dB`, `days`, `degrees`, `events/hour`, `g/24h`, `g/dL`, `g/day`, `hours/day`, `kPa`, `kg`, `kg/m²`, `mIU/L`, `mIU/mL`, `mL`, `mL/min/1.73m²`, `mL/s`, `mg`, `mg/L`, `mg/dL`, `million`, `million/mL`, `minutes`, `mm`, `mmHg`, `mmol/L`, `months`, `ng/L`, `ng/dL`, `ng/mL`, `nmol/L`, `pg/mL`, `sec`, `seconds`, `weeks`, `years`, `°C`, `×10³/µL`, `μm`

## Two gotchas
1. **Preserve `option.value` type** (bool/int/null/string) on submit.
2. **Every field may carry `visibleWhen`** — implement the `eq/ne/in/gt/gte/truthy` + `all/any` evaluator to drive show/hide.

## Submitting answers
`POST /submissions` with `{ module_id, data: { <fieldName>: <value>, … } }` — `data` is keyed by each input field's `name`, values typed per the table above.
