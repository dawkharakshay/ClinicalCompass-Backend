# Appeal Letters — per-module analysis (from old_static_code)

Source: the 80 legacy `client/src/pages/*AppealLetter.tsx` pages. Each module below is marked for whether it has an appeal letter, and (if so) how its placeholders are filled.

## How an appeal letter is filled (3 mechanisms)

1. **Derived from submitted data** — the compass passes the assessment **result** to the page as a base64 `?data=` param; the page decodes it and `generateDefaultLetterBody(result)` weaves `result.*` values into the prose via `${…}` interpolation. *(letter style = `dynamic-body`)*

2. **Filled on the page** — the page has provider/insurance/code inputs (`AppealLetterData`); on PDF export `generateLetterHTML` does `.replace('[X]', data.field)` to drop those into the letter.

3. **Shown as-is for the user to fill** — remaining `[BRACKET]` tokens (patient PII, history, clinical specifics) are left literal in the editable body for manual completion.

> `[]` count below = literal bracket placeholders in the letter body. `${}` count = values auto-woven from the submitted result.

## Summary

- Modules total: **129** | with appeal letter: **80** | without: **49**

- Letter style: **46 dynamic-body** (auto-derive prose from submitted result) · **34 static-body** (fixed prose, brackets only)


## Master table (all modules)

| id | module | speciality | letter? | style | `[]` | `${}` derived | page-filled | manual `[]` |
|---|---|---|:--:|---|--:|--:|--:|--:|
| 25 | Rectal Cancer | Oncology | ❌ | — | — | — | — | — |
| 26 | Colon Cancer | Oncology | ❌ | — | — | — | — | — |
| 27 | Gastric Cancer | Oncology | ❌ | — | — | — | — | — |
| 28 | Pancreatic Cancer | Oncology | ❌ | — | — | — | — | — |
| 29 | Liver Cancer | Oncology | ❌ | — | — | — | — | — |
| 30 | Breast Cancer | Oncology | ❌ | — | — | — | — | — |
| 31 | Lung Cancer | Oncology | ❌ | — | — | — | — | — |
| 32 | Prostate Cancer | Oncology | ❌ | — | — | — | — | — |
| 33 | Melanoma | Oncology | ❌ | — | — | — | — | — |
| 34 | Lymphoma | Oncology | ❌ | — | — | — | — | — |
| 35 | Leukemia | Oncology | ❌ | — | — | — | — | — |
| 36 | Cervical Cancer | Oncology | ❌ | — | — | — | — | — |
| 37 | Ovarian Cancer | Oncology | ❌ | — | — | — | — | — |
| 38 | Bladder Cancer | Oncology | ❌ | — | — | — | — | — |
| 39 | Thyroid Cancer | Oncology | ❌ | — | — | — | — | — |
| 40 | Esophageal Cancer | Oncology | ❌ | — | — | — | — | — |
| 41 | Renal Cell Carcinoma | Oncology | ❌ | — | — | — | — | — |
| 42 | Testicular Cancer | Oncology | ❌ | — | — | — | — | — |
| 43 | Glioma | Oncology | ❌ | — | — | — | — | — |
| 44 | Sarcoma | Oncology | ❌ | — | — | — | — | — |
| 45 | Head & Neck Cancer | Oncology | ❌ | — | — | — | — | — |
| 46 | Endometrial Cancer | Oncology | ❌ | — | — | — | — | — |
| 47 | Multiple Myeloma | Oncology | ❌ | — | — | — | — | — |
| 48 | Mesothelioma | Oncology | ❌ | — | — | — | — | — |
| 49 | Neuroblastoma | Oncology | ❌ | — | — | — | — | — |
| 50 | Pulmonary Embolism Clinical Compass | Interventional Radiology | ❌ | — | — | — | — | — |
| 51 | Women's Health Clinical Compass | Interventional Radiology | ✅ | static-body | 0 | 0 | 0 | 0 |
| 52 | Prostatic Artery Embolization Clinical Compass | Interventional Radiology | ✅ | dynamic-body | 10 | 3 | 0 | 10 |
| 53 | Varicocele Embolization Clinical Compass | Interventional Radiology | ✅ | dynamic-body | 9 | 3 | 9 | 0 |
| 54 | Portal Hypertension Clinical Compass | Interventional Radiology | ✅ | dynamic-body | 9 | 4 | 9 | 0 |
| 55 | Geniculate Artery Embolization Clinical Compass | Interventional Radiology | ✅ | dynamic-body | 10 | 3 | 9 | 1 |
| 56 | Percutaneous AV Fistula Clinical Compass | Interventional Radiology | ✅ | dynamic-body | 2 | 5 | 2 | 0 |
| 57 | Bone Cancer Interventional Oncology Clinical Compass | Interventional Radiology | ✅ | dynamic-body | 10 | 3 | 0 | 10 |
| 58 | Y-90 Radioembolization Clinical Compass | Interventional Radiology | ✅ | dynamic-body | 11 | 3 | 0 | 11 |
| 59 | Endovenous Ablation Clinical Compass | Interventional Radiology | ✅ | static-body | 13 | 0 | 2 | 11 |
| 60 | Sclerotherapy Clinical Compass | Interventional Radiology | ✅ | static-body | 13 | 0 | 0 | 13 |
| 61 | Vertebroplasty / Kyphoplasty Clinical Compass | Interventional Radiology | ✅ | static-body | 12 | 0 | 0 | 12 |
| 62 | Sacroplasty Clinical Compass | Interventional Radiology | ✅ | static-body | 12 | 0 | 0 | 12 |
| 63 | Peripheral Atherectomy Clinical Compass | Interventional Radiology | ❌ | — | — | — | — | — |
| 64 | Renal Cryoablation Clinical Compass | Interventional Radiology | ✅ | static-body | 14 | 0 | 0 | 14 |
| 65 | Vasectomy Reversal Clinical Compass | Urology & Male Reproductive Medicine | ✅ | static-body | 4 | 0 | 0 | 4 |
| 66 | Varicocelectomy Clinical Compass | Urology & Male Reproductive Medicine | ✅ | static-body | 8 | 0 | 0 | 8 |
| 67 | TESE / Micro-TESE Clinical Compass | Urology & Male Reproductive Medicine | ✅ | static-body | 6 | 0 | 0 | 6 |
| 68 | Peyronie's Disease Surgery Clinical Compass | Urology & Male Reproductive Medicine | ✅ | static-body | 7 | 0 | 0 | 7 |
| 69 | Gender-Affirming Urologic Procedures Clinical Compass | Urology & Male Reproductive Medicine | ✅ | static-body | 5 | 0 | 0 | 5 |
| 70 | In Vitro Fertilization Clinical Compass | Reproductive Endocrinology & Infertility | ✅ | static-body | 13 | 0 | 0 | 13 |
| 71 | Intracytoplasmic Sperm Injection Clinical Compass | Reproductive Endocrinology & Infertility | ✅ | static-body | 8 | 0 | 0 | 8 |
| 72 | Preimplantation Genetic Testing Clinical Compass | Reproductive Endocrinology & Infertility | ✅ | static-body | 10 | 0 | 0 | 10 |
| 73 | Oocyte Cryopreservation Clinical Compass | Reproductive Endocrinology & Infertility | ✅ | static-body | 8 | 0 | 0 | 8 |
| 74 | Embryo Cryopreservation Clinical Compass | Reproductive Endocrinology & Infertility | ✅ | static-body | 9 | 0 | 0 | 9 |
| 75 | Ovulation Induction Clinical Compass | Reproductive Endocrinology & Infertility | ✅ | static-body | 9 | 0 | 0 | 9 |
| 76 | Gestational Carrier Clinical Compass | Reproductive Endocrinology & Infertility | ✅ | static-body | 4 | 0 | 0 | 4 |
| 77 | Acute Coronary Syndrome Clinical Compass | Cardiology & Interventional Cardiology | ❌ | — | — | — | — | — |
| 78 | Dyslipidemia Clinical Compass | Cardiology & Interventional Cardiology | ✅ | dynamic-body | 10 | 11 | 7 | 3 |
| 79 | PAD Revascularization Clinical Compass | Vascular Medicine & Surgery | ✅ | dynamic-body | 9 | 1 | 9 | 0 |
| 80 | PAD Clinical Performance & Quality Measures Clinical Compass | Vascular Medicine & Surgery | ✅ | dynamic-body | 7 | 4 | 7 | 0 |
| 81 | Venous Thromboembolism Clinical Compass | Hematology | ✅ | dynamic-body | 9 | 4 | 9 | 0 |
| 82 | Acute Myeloid Leukemia Clinical Compass | Hematology | ❌ | — | — | — | — | — |
| 83 | Acute Lymphoblastic Leukemia & CAR-T Clinical Compass | Hematology | ❌ | — | — | — | — | — |
| 84 | Aplastic Anemia Clinical Compass | Hematology | ❌ | — | — | — | — | — |
| 85 | Rectal Cancer Clinical Compass | Surgery & Surgical Oncology | ✅ | dynamic-body | 9 | 4 | 9 | 0 |
| 86 | Liver Tumor Clinical Compass | Surgery & Surgical Oncology | ✅ | dynamic-body | 12 | 7 | 7 | 5 |
| 87 | Obesity Treatment Clinical Compass | Surgery & Surgical Oncology | ✅ | dynamic-body | 3 | 8 | 0 | 3 |
| 88 | Spine Surgery Clinical Compass | Surgery & Surgical Oncology | ✅ | dynamic-body | 14 | 12 | 8 | 6 |
| 89 | Thyroid Nodule Clinical Compass | ENT, Endocrine & Sleep Medicine | ✅ | dynamic-body | 6 | 11 | 6 | 0 |
| 90 | OSA Clinical Compass | ENT, Endocrine & Sleep Medicine | ✅ | dynamic-body | 11 | 11 | 8 | 3 |
| 91 | Narcolepsy Clinical Compass | ENT, Endocrine & Sleep Medicine | ✅ | dynamic-body | 6 | 1 | 0 | 6 |
| 92 | Chronic Insomnia Clinical Compass | ENT, Endocrine & Sleep Medicine | ✅ | dynamic-body | 6 | 1 | 0 | 6 |
| 93 | Central Sleep Apnea Clinical Compass | ENT, Endocrine & Sleep Medicine | ✅ | dynamic-body | 6 | 1 | 0 | 6 |
| 94 | RLS / PLMD Clinical Compass | ENT, Endocrine & Sleep Medicine | ✅ | dynamic-body | 6 | 1 | 0 | 6 |
| 95 | OSA + Obesity Clinical Compass | ENT, Endocrine & Sleep Medicine | ✅ | dynamic-body | 4 | 5 | 0 | 4 |
| 96 | Pituitary Adenoma Clinical Compass | Neurosurgery & Neuro-Oncology | ✅ | dynamic-body | 7 | 6 | 7 | 0 |
| 97 | Vestibular Schwannoma Clinical Compass | Neurosurgery & Neuro-Oncology | ✅ | dynamic-body | 9 | 7 | 9 | 0 |
| 98 | Brain Metastases Clinical Compass | Neurosurgery & Neuro-Oncology | ✅ | dynamic-body | 6 | 6 | 6 | 0 |
| 99 | Low-Grade Glioma Clinical Compass | Neurosurgery & Neuro-Oncology | ✅ | dynamic-body | 12 | 5 | 7 | 5 |
| 100 | Cerebral Cavernous Malformation Compass | Neurosurgery & Neuro-Oncology | ✅ | dynamic-body | 6 | 11 | 6 | 0 |
| 101 | Spine Antithrombotic Compass | Neurosurgery & Neuro-Oncology | ✅ | dynamic-body | 11 | 10 | 7 | 4 |
| 102 | Atopic Dermatitis Clinical Compass | Dermatology | ✅ | dynamic-body | 11 | 10 | 8 | 3 |
| 103 | Acne Vulgaris Clinical Compass | Dermatology | ✅ | dynamic-body | 10 | 17 | 6 | 4 |
| 104 | Psoriasis Clinical Compass | Dermatology | ✅ | dynamic-body | 12 | 8 | 12 | 0 |
| 105 | Melanoma Clinical Compass | Dermatology | ❌ | — | — | — | — | — |
| 106 | Hidradenitis Suppurativa Clinical Compass | Dermatology | ❌ | — | — | — | — | — |
| 107 | Amyloidosis Diagnostic Clinical Compass | Hematology | ❌ | — | — | — | — | — |
| 108 | Functional Seizures (PNES) | Neurology | ❌ | — | — | — | — | — |
| 109 | Acute Ischemic Stroke | Neurology | ❌ | — | — | — | — | — |
| 110 | Migraine | Neurology | ✅ | dynamic-body | 10 | 15 | 10 | 0 |
| 111 | Multiple Sclerosis | Neurology | ✅ | dynamic-body | 10 | 12 | 10 | 0 |
| 112 | Parkinson's Disease | Neurology | ✅ | dynamic-body | 10 | 9 | 9 | 1 |
| 113 | Age-Related Macular Degeneration | Ophthalmology | ✅ | dynamic-body | 10 | 15 | 9 | 1 |
| 114 | High Myopia / Pathologic Myopia | Ophthalmology | ✅ | dynamic-body | 10 | 8 | 9 | 1 |
| 115 | Glaucoma | Ophthalmology | ✅ | dynamic-body | 9 | 15 | 7 | 2 |
| 116 | Crohn's Disease Clinical Compass | Gastroenterology & Interventional GI | ❌ | — | — | — | — | — |
| 117 | Ulcerative Colitis Clinical Compass | Gastroenterology & Interventional GI | ❌ | — | — | — | — | — |
| 118 | MASLD / MASH Clinical Compass | Gastroenterology & Interventional GI | ❌ | — | — | — | — | — |
| 119 | Gastroparesis Clinical Compass | Gastroenterology & Interventional GI | ✅ | dynamic-body | 7 | 8 | 7 | 0 |
| 120 | CRC Screening Clinical Compass | Gastroenterology & Interventional GI | ✅ | dynamic-body | 9 | 8 | 9 | 0 |
| 121 | IBD Preventive Care Clinical Compass | Gastroenterology & Interventional GI | ❌ | — | — | — | — | — |
| 122 | Pancreatic Mass Evaluation Clinical Compass | Gastroenterology & Interventional GI | ❌ | — | — | — | — | — |
| 123 | Therapeutic EUS Clinical Compass | Gastroenterology & Interventional GI | ✅ | dynamic-body | 8 | 7 | 0 | 8 |
| 124 | Chronic Pancreatitis Clinical Compass | Gastroenterology & Interventional GI | ✅ | dynamic-body | 12 | 9 | 12 | 0 |
| 125 | Biliary Strictures Clinical Compass | Gastroenterology & Interventional GI | ✅ | dynamic-body | 9 | 8 | 9 | 0 |
| 126 | Pediatric Immunization Clinical Compass | Pediatrics | ❌ | — | — | — | — | — |
| 127 | Bright Futures Well-Child Clinical Compass | Pediatrics | ❌ | — | — | — | — | — |
| 128 | Pediatric Obesity Clinical Compass | Pediatrics | ✅ | dynamic-body | 12 | 12 | 8 | 4 |
| 129 | Febrile Infant Clinical Compass | Pediatrics | ❌ | — | — | — | — | — |
| 130 | Neonatal Hyperbilirubinemia Clinical Compass | Pediatrics | ❌ | — | — | — | — | — |
| 131 | Influenza Prevention Clinical Compass | Pediatrics | ❌ | — | — | — | — | — |
| 132 | RSV Prevention Clinical Compass | Pediatrics | ❌ | — | — | — | — | — |
| 133 | Pediatric Mental Health Clinical Compass | Pediatrics | ❌ | — | — | — | — | — |
| 134 | Radiation Oncology Clinical Compass | Radiation Oncology | ❌ | — | — | — | — | — |
| 135 | Psychiatry Clinical Compass | Psychiatry | ❌ | — | — | — | — | — |
| 136 | Total Knee Arthroplasty Clinical Compass | Orthopedics & Spine Surgery | ✅ | static-body | 15 | 0 | 0 | 15 |
| 137 | Total Hip Arthroplasty Clinical Compass | Orthopedics & Spine Surgery | ✅ | static-body | 14 | 0 | 0 | 14 |
| 138 | Spinal Fusion Clinical Compass | Orthopedics & Spine Surgery | ✅ | static-body | 18 | 0 | 0 | 18 |
| 139 | Artificial Disc Replacement Clinical Compass | Orthopedics & Spine Surgery | ✅ | static-body | 23 | 0 | 0 | 23 |
| 140 | Rotator Cuff Repair Clinical Compass | Orthopedics & Spine Surgery | ✅ | static-body | 27 | 0 | 0 | 27 |
| 141 | Meniscus Repair Clinical Compass | Orthopedics & Spine Surgery | ✅ | static-body | 24 | 0 | 0 | 24 |
| 142 | Epidural Steroid Injection Clinical Compass | Pain Medicine & Interventional Procedures | ✅ | static-body | 7 | 0 | 7 | 0 |
| 143 | Facet Joint Injection Clinical Compass | Pain Medicine & Interventional Procedures | ✅ | static-body | 7 | 0 | 7 | 0 |
| 144 | Radiofrequency Ablation Clinical Compass | Pain Medicine & Interventional Procedures | ✅ | static-body | 7 | 0 | 7 | 0 |
| 145 | Spinal Cord Stimulator Clinical Compass | Pain Medicine & Interventional Procedures | ✅ | dynamic-body | 7 | 1 | 7 | 0 |
| 146 | Elective PCI Clinical Compass | Cardiology & Interventional Cardiology | ✅ | dynamic-body | 18 | 1 | 0 | 18 |
| 147 | AF Ablation Clinical Compass | Cardiology & Interventional Cardiology | ✅ | static-body | 20 | 0 | 0 | 20 |
| 148 | LAAC / Watchman Clinical Compass | Cardiology & Interventional Cardiology | ✅ | dynamic-body | 16 | 2 | 0 | 16 |
| 149 | Bariatric Surgery Clinical Compass | General Surgery & GI Surgery | ✅ | static-body | 31 | 0 | 0 | 31 |
| 150 | Cholecystectomy Clinical Compass | General Surgery & GI Surgery | ✅ | static-body | 21 | 0 | 0 | 21 |
| 151 | Hernia Repair Clinical Compass | General Surgery & GI Surgery | ✅ | static-body | 22 | 0 | 0 | 22 |
| 152 | Breast Reduction Clinical Compass | Plastic & Reconstructive Surgery | ✅ | static-body | 32 | 0 | 0 | 32 |
| 153 | Blepharoplasty / Ptosis Repair Clinical Compass | Plastic & Reconstructive Surgery | ✅ | static-body | 20 | 0 | 0 | 20 |

## Per-module detail (modules with a letter)

### 51 — Women's Health Clinical Compass  
`WomensHealthAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=0 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill**: none

### 52 — Prostatic Artery Embolization Clinical Compass  
`MensHealthAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=3

- **Derived from submitted data** (`result.*` → prose): `criteriaMetCount`, `criteriaTotalCount`, `label`, `score`, `summary`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (10): `[CPT_CODES]`, `[ICD10_CODES]`, `[PHYSICIAN_ADDRESS]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_EMAIL]`, `[PHYSICIAN_FAX]`, `[PHYSICIAN_NAME]`, `[PHYSICIAN_NPI]`, `[PHYSICIAN_PHONE]`, `[PHYSICIAN_PRACTICE]`

  - buckets → provider:8 · patient/payer:0 · date:0 · codes:2 · **clinical (derivable):0**

### 53 — Varicocele Embolization Clinical Compass  
`VaricoceleAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=3

- **Derived from submitted data** (`result.*` → prose): `indicationReason`, `primaryRecommendation`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 54 — Portal Hypertension Clinical Compass  
`PortalHypertensionAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=4

- **Derived from submitted data** (`result.*` → prose): `primaryRecommendation`, `rationale`, `tipsIndication`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 55 — Geniculate Artery Embolization Clinical Compass  
`GAEAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=3

- **Derived from submitted data** (`result.*` → prose): `primaryRecommendation`, `rationale`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (1): `[clinical reasons]`

  - buckets → provider:0 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):1**

### 56 — Percutaneous AV Fistula Clinical Compass  
`PAVFAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=2 · `${}`=5

- **Derived from submitted data** (`result.*` → prose): `clinicalSummary`, `cptCode`, `cptDescription`, `deviceSuggestion`, `eligibility`, `eligibilityLabel`, `recommendations`, `vesselMappingAdequate`

- **Filled on the page** (`[X]`→input on export): `[CPT_CODES]`←`data.cptCodes`, `[ICD_CODES]`←`data.icdCodes`

- **Shown as-is to fill**: none

### 57 — Bone Cancer Interventional Oncology Clinical Compass  
`BoneCancerAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=3

- **Derived from submitted data** (`result.*` → prose): `candidacyLabel`, `candidacyScore`, `recommendedModalities`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (10): `[CPT_CODES]`, `[ICD10_CODES]`, `[PHYSICIAN_ADDRESS]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_EMAIL]`, `[PHYSICIAN_FAX]`, `[PHYSICIAN_NAME]`, `[PHYSICIAN_NPI]`, `[PHYSICIAN_PHONE]`, `[PHYSICIAN_PRACTICE]`

  - buckets → provider:8 · patient/payer:0 · date:0 · codes:2 · **clinical (derivable):0**

### 58 — Y-90 Radioembolization Clinical Compass  
`Y90AppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=11 · `${}`=3

- **Derived from submitted data** (`result.*` → prose): `candidacy`, `dosimetryNotes`, `summary`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (11): `[CPT_CODES]`, `[HCC]`, `[ICD10_CODES]`, `[PHYSICIAN_ADDRESS]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_EMAIL]`, `[PHYSICIAN_FAX]`, `[PHYSICIAN_NAME]`, `[PHYSICIAN_NPI]`, `[PHYSICIAN_PHONE]`, `[PHYSICIAN_PRACTICE]`

  - buckets → provider:8 · patient/payer:0 · date:0 · codes:2 · **clinical (derivable):1**

### 59 — Endovenous Ablation Clinical Compass  
`EndovenousAblationAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=13 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `urgency`

- **Filled on the page** (`[X]`→input on export): `[CLASS]`←`(literal)`, `[PATIENT NAME]`←`(literal)`

- **Shown as-is to fill** (11): `[CREDENTIALS]`, `[DATE]`, `[DOB]`, `[MEMBER ID]`, `[MILD/MODERATE/SEVERE]`, `[NPI]`, `[PROVIDER NAME]`, `[REFLUX DURATION]`, `[SYMPTOMS]`, `[VCSS SCORE]`, `[WEEKS]`

  - buckets → provider:3 · patient/payer:2 · date:1 · codes:0 · **clinical (derivable):5**

### 60 — Sclerotherapy Clinical Compass  
`SclerotherapyAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=13 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (13): `[CLASS]`, `[CREDENTIALS]`, `[DATE]`, `[DIAMETER]`, `[DOB]`, `[Duplex-confirmed venous reflux / Residual varicosities after prior ablation]`, `[MEMBER ID]`, `[NPI]`, `[PATIENT NAME]`, `[PROVIDER NAME]`, `[SYMPTOMS]`, `[VESSEL TYPE]`, `[WEEKS]`

  - buckets → provider:3 · patient/payer:3 · date:1 · codes:0 · **clinical (derivable):6**

### 61 — Vertebroplasty / Kyphoplasty Clinical Compass  
`VertebroplastyAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=12 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (12): `[CREDENTIALS]`, `[DATE]`, `[DOB]`, `[FRACTURE LEVEL]`, `[MEMBER ID]`, `[NPI]`, `[ODI]`, `[Osteoporotic / Pathologic]`, `[PATIENT NAME]`, `[PROVIDER NAME]`, `[VAS]`, `[WEEKS]`

  - buckets → provider:3 · patient/payer:3 · date:1 · codes:0 · **clinical (derivable):5**

### 62 — Sacroplasty Clinical Compass  
`SacroplastyAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=12 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (12): `[CREDENTIALS]`, `[DATE]`, `[DOB]`, `[FUNCTIONAL IMPAIRMENT]`, `[MEMBER ID]`, `[NPI]`, `[Osteoporotic / Pathologic / Radiation-induced]`, `[PATIENT NAME]`, `[PROVIDER NAME]`, `[VAS]`, `[WEEKS]`, `[ZONE]`

  - buckets → provider:3 · patient/payer:3 · date:1 · codes:0 · **clinical (derivable):5**

### 64 — Renal Cryoablation Clinical Compass  
`RenalCryoablationAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=14 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (14): `[CREDENTIALS]`, `[DATE]`, `[DOB]`, `[ENHANCEMENT CHARACTERISTICS]`, `[LOCATION]`, `[LOW/MODERATE/HIGH]`, `[MEMBER ID]`, `[NPI]`, `[PATIENT NAME]`, `[PROVIDER NAME]`, `[Patient comorbidities: e.g., CKD, solitary kidney, advanced age, cardiopulmonary disease]`, `[SCORE]`, `[SIZE]`, `[favorable/acceptable]`

  - buckets → provider:3 · patient/payer:4 · date:1 · codes:0 · **clinical (derivable):6**

### 65 — Vasectomy Reversal Clinical Compass  
`VasectomyReversalAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=4 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (4): `[Credentials]`, `[Date]`, `[Practice Name]`, `[Provider Name]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):0**

### 66 — Varicocelectomy Clinical Compass  
`VaricocelectomyAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=8 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (8): `[Credentials]`, `[Date]`, `[I/II/III]`, `[Practice Name]`, `[Provider Name]`, `[X]`, `[normal/completed]`, `[oligospermia/asthenospermia/teratospermia]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):4**

### 67 — TESE / Micro-TESE Clinical Compass  
`TESEAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=6 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (6): `[Credentials]`, `[Date]`, `[For NOA: Klinefelter syndrome / Y-chromosome microdeletion / idiopathic NOA as applicable.]`, `[Practice Name]`, `[Provider Name]`, `[obstructive/non-obstructive]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):2**

### 68 — Peyronie's Disease Surgery Clinical Compass  
`PeyroniesAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=7 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (7): `[Credentials]`, `[Date]`, `[Practice Name]`, `[Provider Name]`, `[X]`, `[direction]`, `[normal erections / mild-moderate ED / severe ED requiring IPP]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):3**

### 69 — Gender-Affirming Urologic Procedures Clinical Compass  
`GenderAffirmingUroAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=5 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (5): `[Credentials]`, `[Date]`, `[Practice Name]`, `[Provider Name]`, `[procedure name]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):1**

### 70 — In Vitro Fertilization Clinical Compass  
`IVFAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=13 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (13): `[Credentials]`, `[Date]`, `[If applicable]`, `[If state mandate applies]`, `[N97.x]`, `[Practice Name]`, `[Provider Name]`, `[X]`, `[indication]`, `[severe male factor]`, `[state]`, `[state statute]`, `[tubal factor]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):9**

### 71 — Intracytoplasmic Sperm Injection Clinical Compass  
`ICSIAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=8 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (8): `[0% / X%]`, `[Credentials]`, `[Date]`, `[If azoospermia: Sperm will be retrieved via TESE/PESA/micro-TESE.]`, `[Practice Name]`, `[Provider Name]`, `[X]`, `[date]`

  - buckets → provider:3 · patient/payer:0 · date:2 · codes:0 · **clinical (derivable):3**

### 72 — Preimplantation Genetic Testing Clinical Compass  
`PGTAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=10 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (10): `[25%/50%]`, `[Credentials]`, `[Date]`, `[For PGT-M]`, `[For RPL]`, `[Practice Name]`, `[Provider Name]`, `[X]`, `[disorder name]`, `[dominant/recessive]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):6**

### 73 — Oocyte Cryopreservation Clinical Compass  
`OocyteFreezeAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=8 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (8): `[Credentials]`, `[Date]`, `[For oncofertility]`, `[Practice Name]`, `[Provider Name]`, `[cancer diagnosis / premature ovarian insufficiency / genetic condition]`, `[chemotherapy/radiation/surgery]`, `[date]`

  - buckets → provider:3 · patient/payer:0 · date:2 · codes:0 · **clinical (derivable):3**

### 74 — Embryo Cryopreservation Clinical Compass  
`EmbryoCryoAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=9 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (9): `[Credentials]`, `[Date]`, `[Practice Name]`, `[Provider Name]`, `[Select applicable scenario:]`, `[X]`, `[cancer diagnosis]`, `[date]`, `[selected scenario above]`

  - buckets → provider:3 · patient/payer:0 · date:2 · codes:0 · **clinical (derivable):4**

### 75 — Ovulation Induction Clinical Compass  
`OvulationInductionAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=9 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (9): `[Credentials]`, `[Date]`, `[E28.2 / N97.0]`, `[If state mandate applies]`, `[PCOS / hypothalamic anovulation / anovulatory infertility]`, `[Practice Name]`, `[Provider Name]`, `[X]`, `[letrozole / clomiphene]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):5**

### 76 — Gestational Carrier Clinical Compass  
`GestationalCarrierAppealLetter.tsx` · style **static-body** · reads `?data`: False · `[]`=4 · `${}`=0

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (4): `[Credentials]`, `[Date]`, `[Practice Name]`, `[Provider Name]`

  - buckets → provider:3 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):0**

### 78 — Dyslipidemia Clinical Compass  
`DyslipidemiaDSAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=11

- **Derived from submitted data** (`result.*` → prose): `ascvdRisk`, `guidelineSource`, `ldlGoal`, `nextSteps`, `nonHDLGoal`, `primaryRecommendation`, `riskCategory`, `statinIntensity`, `treatmentIndicated`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (3): `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[relevant lab values, e.g., LDL-C of XXX mg/dL, non-HDL-C of YYY mg/dL]`

  - buckets → provider:0 · patient/payer:2 · date:0 · codes:0 · **clinical (derivable):1**

### 79 — PAD Revascularization Clinical Compass  
`PADAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=1

- **Derived from submitted data** (`result.*` → prose): `exerciseTherapyRequired`, `gdmtRequired`, `keyMessages`, `preferredModality`, `primaryRecommendation`, `revascularizationIndicated`, `riskAmplifiers`, `subsetLabel`, `urgency`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 80 — PAD Clinical Performance & Quality Measures Clinical Compass  
`PADQualityAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=7 · `${}`=4

- **Derived from submitted data** (`result.*` → prose): `qualityMeasure`, `rationale`, `recommendation`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 81 — Venous Thromboembolism Clinical Compass  
`VTEAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=4

- **Derived from submitted data** (`result.*` → prose): `primaryRecommendation`, `rationale`, `riskCategory`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 85 — Rectal Cancer Clinical Compass  
`RectalCancerAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=4

- **Derived from submitted data** (`result.*` → prose): `clinicalStage`, `primaryRecommendation`, `rationale`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 86 — Liver Tumor Clinical Compass  
`LiverTumorAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=12 · `${}`=7

- **Derived from submitted data** (`result.*` → prose): `evidenceLevel`, `rationale`, `recommendation`, `stagingLabel`, `treatmentStrategy`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (5): `[BRIEF_CLINICAL_SUMMARY_INCLUDING_DIAGNOSIS_AND_SYMPTOMS]`, `[EXPECTED_BENEFITS_E.G._ERADICATE_TUMOR,_CONTROL_DISEASE,_IMPROVE_QUALITY_OF_LIFE]`, `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[POLICY_NUMBER]`

  - buckets → provider:0 · patient/payer:3 · date:0 · codes:0 · **clinical (derivable):2**

### 87 — Obesity Treatment Clinical Compass  
`ObesityAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=3 · `${}`=8

- **Derived from submitted data** (`result.*` → prose): `bariatricProcedure`, `bmiCategory`, `evidenceLevel`, `glp1Indicated`, `guidelineSource`, `nextSteps`, `pharmacotherapyIndicated`, `primaryRecommendation`, `rationale`, `surgicalCandidate`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (3): `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[POLICY_NUMBER]`

  - buckets → provider:0 · patient/payer:3 · date:0 · codes:0 · **clinical (derivable):0**

### 88 — Spine Surgery Clinical Compass  
`SpineAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=14 · `${}`=12

- **Derived from submitted data** (`result.*` → prose): `evidenceLevel`, `procedureType`, `rationale`, `recommendation`, `surgicalIndication`

- **Filled on the page** (`[X]`→input on export): `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (6): `[IMAGING_FINDINGS]`, `[LIST_CONSERVATIVE_TREATMENTS]`, `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[POLICY_NUMBER]`, `[SYMPTOMS_DESCRIPTION]`

  - buckets → provider:0 · patient/payer:3 · date:0 · codes:0 · **clinical (derivable):3**

### 89 — Thyroid Nodule Clinical Compass  
`ThyroidNoduleAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=6 · `${}`=11

- **Derived from submitted data** (`result.*` → prose): `biopsyIndicated`, `evidenceLevel`, `followUpInterval`, `guidelineSource`, `nextSteps`, `noduleRiskLevel`, `primaryRecommendation`, `rationale`, `tiradsCategory`

- **Filled on the page** (`[X]`→input on export): `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 90 — OSA Clinical Compass  
`OSAAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=11 · `${}`=11

- **Derived from submitted data** (`result.*` → prose): `ahiCategory`, `cpapIndicated`, `evidenceLevel`, `guidelineSource`, `nextSteps`, `oralApplianceCandidate`, `primaryRecommendation`, `rationale`, `surgicalCandidate`

- **Filled on the page** (`[X]`→input on export): `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (3): `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[SYMPTOMS_HERE, e.g., excessive daytime sleepiness, loud snoring, observed apneas]`

  - buckets → provider:0 · patient/payer:2 · date:0 · codes:0 · **clinical (derivable):1**

### 91 — Narcolepsy Clinical Compass  
`NarcolepsyAppealLetter.tsx` · style **dynamic-body** · reads `?data`: False · `[]`=6 · `${}`=1

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (6): `[Fax]`, `[NPI Number]`, `[Phone]`, `[Physician Name, MD/DO]`, `[Practice Name]`, `[Specialty: Sleep Medicine / Neurology]`

  - buckets → provider:5 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):1**

### 92 — Chronic Insomnia Clinical Compass  
`ChronicInsomniaAppealLetter.tsx` · style **dynamic-body** · reads `?data`: False · `[]`=6 · `${}`=1

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (6): `[Fax]`, `[NPI Number]`, `[Phone]`, `[Physician Name, MD/DO]`, `[Practice Name]`, `[Specialty: Sleep Medicine / Psychiatry]`

  - buckets → provider:5 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):1**

### 93 — Central Sleep Apnea Clinical Compass  
`CentralSleepApneaAppealLetter.tsx` · style **dynamic-body** · reads `?data`: False · `[]`=6 · `${}`=1

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (6): `[Fax]`, `[NPI Number]`, `[Phone]`, `[Physician Name, MD/DO]`, `[Practice Name]`, `[Specialty: Sleep Medicine / Pulmonology]`

  - buckets → provider:5 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):1**

### 94 — RLS / PLMD Clinical Compass  
`RLSPLMDAppealLetter.tsx` · style **dynamic-body** · reads `?data`: False · `[]`=6 · `${}`=1

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (6): `[Fax]`, `[NPI Number]`, `[Phone]`, `[Physician Name, MD/DO]`, `[Practice Name]`, `[Specialty: Sleep Medicine / Neurology]`

  - buckets → provider:5 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):1**

### 95 — OSA + Obesity Clinical Compass  
`OSAObesityAppealLetter.tsx` · style **dynamic-body** · reads `?data`: False · `[]`=4 · `${}`=5

- **Derived from submitted data**: none (static body — the result is only appended as a JSON summary, not woven in)

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (4): `[NPI]`, `[PATIENT NAME]`, `[PROVIDER NAME]`, `[SPECIALTY]`

  - buckets → provider:2 · patient/payer:1 · date:0 · codes:0 · **clinical (derivable):1**

### 96 — Pituitary Adenoma Clinical Compass  
`PituitaryAdenomaAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=7 · `${}`=6

- **Derived from submitted data** (`result.*` → prose): `adenomaType`, `evidenceLevel`, `guidelineSource`, `medicalTherapyIndicated`, `nextSteps`, `primaryRecommendation`, `radiationIndicated`, `rationale`, `surgicalIndication`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 97 — Vestibular Schwannoma Clinical Compass  
`VestibularSchwannomaAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=7

- **Derived from submitted data** (`result.*` → prose): `evidenceLevel`, `guidelineSource`, `nextSteps`, `observationAppropriate`, `primaryRecommendation`, `rationale`, `srsCandidate`, `surgicalCandidate`, `treatmentApproach`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 98 — Brain Metastases Clinical Compass  
`BrainMetastasesAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=6 · `${}`=6

- **Derived from submitted data** (`result.*` → prose): `evidenceLevel`, `graded`, `guidelineSource`, `kpsScore`, `nextSteps`, `primaryRecommendation`, `rationale`, `srsIndicated`, `surgicalCandidate`, `wbrtIndicated`

- **Filled on the page** (`[X]`→input on export): `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 99 — Low-Grade Glioma Clinical Compass  
`LowGradeGliomaAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=12 · `${}`=5

- **Derived from submitted data** (`result.*` → prose): `chemotherapyIndicated`, `evidenceLevel`, `guidelineSource`, `nextSteps`, `primaryRecommendation`, `radiationIndicated`, `rationale`, `surgicalResectionIndicated`, `watchAndWaitAppropriate`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (5): `[AGE]`, `[DIAGNOSTIC_METHOD, e.g., biopsy/MRI findings]`, `[MALE/FEMALE]`, `[PATIENT_NAME]`, `[SYMPTOMS/CLINICAL_FINDINGS]`

  - buckets → provider:0 · patient/payer:1 · date:0 · codes:0 · **clinical (derivable):4**

### 100 — Cerebral Cavernous Malformation Compass  
`CCMAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=6 · `${}`=11

- **Derived from submitted data** (`result.*` → prose): `bleedRisk`, `evidenceLevel`, `guidelineSource`, `nextSteps`, `observationAppropriate`, `primaryRecommendation`, `rationale`, `srsCandidate`, `surgicalCandidate`, `surgicalIndication`

- **Filled on the page** (`[X]`→input on export): `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 101 — Spine Antithrombotic Compass  
`SpineAntithromboticAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=11 · `${}`=10

- **Derived from submitted data** (`result.*` → prose): `bridgingRequired`, `evidenceLevel`, `guidelineSource`, `holdDuration`, `nextSteps`, `primaryRecommendation`, `rationale`, `resumptionTiming`, `riskCategory`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (4): `[DIAGNOSIS_SUMMARY]`, `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[POLICY_NUMBER]`

  - buckets → provider:0 · patient/payer:3 · date:0 · codes:0 · **clinical (derivable):1**

### 102 — Atopic Dermatitis Clinical Compass  
`AtopicDermatitisAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=11 · `${}`=10

- **Derived from submitted data** (`result.*` → prose): `biologicIndicated`, `dupilumabIndicated`, `evidenceLevel`, `guidelineSource`, `jak1InhibitorIndicated`, `nextSteps`, `primaryRecommendation`, `rationale`, `severityCategory`, `topicalTherapyOptimized`

- **Filled on the page** (`[X]`→input on export): `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (3): `[EASI_SCORE]`, `[IGA_SCORE]`, `[PATIENT_NAME]`

  - buckets → provider:0 · patient/payer:1 · date:0 · codes:0 · **clinical (derivable):2**

### 103 — Acne Vulgaris Clinical Compass  
`AcneAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=17

- **Derived from submitted data** (`result.*` → prose): `antibioticIndicated`, `hormonalTherapyIndicated`, `isotretinoinIndicated`, `nextSteps`, `primaryRecommendation`, `rationale`, `severityCategory`

- **Filled on the page** (`[X]`→input on export): `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (4): `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[POLICY_NUMBER]`, `[PREVIOUS_TREATMENTS]`

  - buckets → provider:0 · patient/payer:3 · date:0 · codes:0 · **clinical (derivable):1**

### 104 — Psoriasis Clinical Compass  
`PsoriasisAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=12 · `${}`=8

- **Derived from submitted data** (`result.*` → prose): `biologicIndicated`, `evidenceLevel`, `guidelineSource`, `il17Indicated`, `il23Indicated`, `nextSteps`, `pdeInhibitorIndicated`, `primaryRecommendation`, `rationale`, `severityCategory`, `tnfInhibitorIndicated`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[BRIEF_CLINICAL_DESCRIPTION_OF_PSORIASIS]`←`(literal)`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[MEMBER_ID]`←`(literal)`, `[NPI]`←`data.npi`, `[PATIENT_DOB]`←`(literal)`, `[PATIENT_NAME]`←`(literal)`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`, `[PREVIOUS_TREATMENTS_FAILED]`←`(literal)`

- **Shown as-is to fill**: none

### 110 — Migraine  
`MigraineAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=15

- **Derived from submitted data** (`result.*` → prose): `acuteTherapyRecommendation`, `cgrpInhibitorIndicated`, `chronicMigraine`, `evidenceLevel`, `guidelineSource`, `migraineFrequency`, `nextSteps`, `patientName`, `preventiveTherapyIndicated`, `primaryRecommendation`, `rationale`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PATIENT_NAME]`←`(literal)`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 111 — Multiple Sclerosis  
`MultipleSclerosisAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=12

- **Derived from submitted data** (`result.*` → prose): `diseaseModifyingTherapy`, `evidenceLevel`, `guidelineSource`, `highEfficacyTherapyIndicated`, `msType`, `nextSteps`, `patientName`, `primaryRecommendation`, `rationale`, `relapseRate`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PATIENT_NAME]`←`(literal)`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 112 — Parkinson's Disease  
`ParkinsonsAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=9

- **Derived from submitted data** (`result.*` → prose): `dbsIndicated`, `evidenceLevel`, `guidelineSource`, `hoehnYahrStage`, `levodopaCandidacy`, `motorFluctuations`, `nextSteps`, `primaryRecommendation`, `rationale`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (1): `[PATIENT_NAME]`

  - buckets → provider:0 · patient/payer:1 · date:0 · codes:0 · **clinical (derivable):0**

### 113 — Age-Related Macular Degeneration  
`AMDAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=15

- **Derived from submitted data** (`result.*` → prose): `amdStage`, `amdType`, `antiVEGFIndicated`, `evidenceLevel`, `guidelineSource`, `nextSteps`, `primaryRecommendation`, `rationale`, `treatmentUrgency`

- **Filled on the page** (`[X]`→input on export): `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PATIENT_DOB]`←`(literal)`, `[PATIENT_NAME]`←`(literal)`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`, `[SYMPTOMS]`←`(literal)`

- **Shown as-is to fill** (1): `[TREATMENT_PLAN_DETAILS]`

  - buckets → provider:0 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):1**

### 114 — High Myopia / Pathologic Myopia  
`HighMyopiaAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=10 · `${}`=8

- **Derived from submitted data** (`result.*` → prose): `atropineIndicated`, `evidenceLevel`, `guidelineSource`, `myopiaControlIndicated`, `myopiaProgressionRisk`, `nextSteps`, `orthoKIndicated`, `primaryRecommendation`, `rationale`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (1): `[PATIENT_NAME]`

  - buckets → provider:0 · patient/payer:1 · date:0 · codes:0 · **clinical (derivable):0**

### 115 — Glaucoma  
`GlaucomaAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=15

- **Derived from submitted data** (`result.*` → prose): `evidenceLevel`, `glaucomaType`, `guidelineSource`, `iop`, `laserIndicated`, `nextSteps`, `primaryRecommendation`, `rationale`, `surgicalCandidate`, `surgicalIndication`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (2): `[PATIENT_NAME]`, `[SYMPTOMS/FINDINGS]`

  - buckets → provider:0 · patient/payer:1 · date:0 · codes:0 · **clinical (derivable):1**

### 119 — Gastroparesis Clinical Compass  
`GastroparesisAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=7 · `${}`=8

- **Derived from submitted data** (`result.*` → prose): `diabeticEtiology`, `evidenceLevel`, `gastricElectricalStimulationIndicated`, `guidelineSource`, `nextSteps`, `primaryRecommendation`, `pyloricInterventionIndicated`, `rationale`, `severityCategory`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 120 — CRC Screening Clinical Compass  
`CRCScreeningAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=8

- **Derived from submitted data** (`result.*` → prose): `colonoscopyIndicated`, `evidenceLevel`, `guidelineSource`, `nextSteps`, `primaryRecommendation`, `rationale`, `riskCategory`, `screeningInterval`, `screeningModality`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 123 — Therapeutic EUS Clinical Compass  
`TherapeuticEUSAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=8 · `${}`=7

- **Derived from submitted data** (`result.*` → prose): `celiacBlockIndicated`, `drainageIndicated`, `evidenceLevel`, `guidelineSource`, `necrosectomyIndicated`, `nextSteps`, `primaryRecommendation`, `procedureIndicated`, `rationale`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (8): `[DIAGNOSTIC_FINDINGS]`, `[EXPECTED_OUTCOME]`, `[PATIENT_CONDITION]`, `[PATIENT_DOB]`, `[PATIENT_NAME]`, `[PATIENT_SYMPTOMS]`, `[RISK_WITHOUT_TREATMENT]`, `[SPECIFIC_RISKS]`

  - buckets → provider:0 · patient/payer:4 · date:0 · codes:0 · **clinical (derivable):4**

### 124 — Chronic Pancreatitis Clinical Compass  
`ChronicPancreatitisAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=12 · `${}`=9

- **Derived from submitted data** (`result.*` → prose): `endoscopicTherapyIndicated`, `evidenceLevel`, `exocrineInsufficiency`, `guidelineSource`, `nextSteps`, `painManagementStrategy`, `patientDOB`, `patientName`, `policyNumber`, `primaryRecommendation`, `rationale`, `surgicalIndication`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PATIENT_DOB]`←`(literal)`, `[PATIENT_NAME]`←`(literal)`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[POLICY_NUMBER]`←`(literal)`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 125 — Biliary Strictures Clinical Compass  
`BiliaryStricturesAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=9 · `${}`=8

- **Derived from submitted data** (`result.*` → prose): `endoscopicTherapyIndicated`, `evidenceLevel`, `guidelineSource`, `nextSteps`, `percutaneousTherapyIndicated`, `primaryRecommendation`, `rationale`, `strictureType`, `surgicalIndication`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 128 — Pediatric Obesity Clinical Compass  
`PediatricObesityAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=12 · `${}`=12

- **Derived from submitted data** (`result.*` → prose): `bariatricSurgeryIndicated`, `bmiPercentile`, `evidenceLevel`, `guidelineSource`, `intensiveHealthBehaviorIntervention`, `nextSteps`, `pharmacotherapyIndicated`, `primaryRecommendation`, `rationale`

- **Filled on the page** (`[X]`→input on export): `[CPT_CODES]`←`data.cptCodes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[ICD_CODES]`←`data.icdCodes`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill** (4): `[AGE]`, `[GENDER]`, `[PATIENT_NAME]`, `[relevant co-morbidities, e.g., prediabetes, dyslipidemia, sleep apnea]`

  - buckets → provider:0 · patient/payer:1 · date:0 · codes:0 · **clinical (derivable):3**

### 136 — Total Knee Arthroplasty Clinical Compass  
`TKAAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=15 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `rationale`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (15): `[CREDENTIALS]`, `[DATES, RESPONSE]`, `[DESCRIBE varus/valgus deformity if present]`, `[DESCRIBE — difficulty with ambulation, stair climbing, ADLs]`, `[DETAILS]`, `[DURATION, NUMBER OF SESSIONS, OUTCOMES]`, `[EMAIL]`, `[GRADE]`, `[MEDICATIONS, DURATION, RESPONSE]`, `[NPI]`, `[NUMBER, DATES, RESPONSE]`, `[PHONE]`, `[PHYSICIAN NAME]`, `[PRACTICE NAME]`, `[SCORE]`

  - buckets → provider:6 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):9**

### 137 — Total Hip Arthroplasty Clinical Compass  
`THAAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=14 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `rationale`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (14): `[CREDENTIALS]`, `[DESCRIBE — difficulty with ambulation, stair climbing, ADLs, sleep disturbance]`, `[DESCRIBE — leg length discrepancy, acetabular dysplasia if applicable]`, `[DETAILS]`, `[DURATION, NUMBER OF SESSIONS, OUTCOMES]`, `[EMAIL]`, `[GRADE]`, `[MEDICATIONS, DURATION, RESPONSE]`, `[NPI]`, `[NUMBER, DATES, RESPONSE]`, `[PHONE]`, `[PHYSICIAN NAME]`, `[PRACTICE NAME]`, `[SCORE]`

  - buckets → provider:6 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):8**

### 138 — Spinal Fusion Clinical Compass  
`SpinalFusionAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=18 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `rationale`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (18): `[CREDENTIALS]`, `[DATE]`, `[DESCRIBE — bony anatomy, instability on flexion/extension]`, `[DESCRIBE — dynamic instability, >3mm translation or >10° angular motion]`, `[DESCRIBE — inability to work, perform ADLs, ambulate]`, `[DETAILS]`, `[DISTANCE before symptom onset]`, `[DURATION — minimum 6 weeks, NUMBER OF SESSIONS, OUTCOMES]`, `[EMAIL]`, `[Grade I / II]`, `[MEDICATIONS, DURATION, RESPONSE]`, `[NPI]`, `[NUMBER, DATES, RESPONSE — e.g., 3 ESIs with <50% relief]`, `[PHONE]`, `[PHYSICIAN NAME]`, `[PRACTICE NAME]`, `[SCORE]`, `[e.g., L4-L5, L5-S1]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):11**

### 139 — Artificial Disc Replacement Clinical Compass  
`ArtificialDiscAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=23 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `rationale`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (23): `[1 or 2]`, `[AGE]`, `[CREDENTIALS]`, `[DATE]`, `[DESCRIBE — arm pain, numbness, weakness, myelopathic symptoms]`, `[DESCRIBE — bony anatomy, osteophytes]`, `[DESCRIBE — disc herniation, foraminal stenosis, cord compression, disc height loss]`, `[DESCRIBE — foraminal narrowing, cord signal change if myelopathy]`, `[DETAILS]`, `[DURATION — minimum 6 weeks, OUTCOMES]`, `[EMAIL]`, `[LEVEL(S)]`, `[MEDICATIONS, DURATION, RESPONSE]`, `[NPI]`, `[NUMBER, DATES, RESPONSE]`, `[PERCENTAGE]`, `[PHONE]`, `[PHYSICIAN NAME]`, `[PRACTICE NAME]`, `[SCORE]`, `[e.g., C5-C6, C6-C7]`, `[radiculopathy / myelopathy]`, `[single / two-level]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):16**

### 140 — Rotator Cuff Repair Clinical Compass  
`RotatorCuffAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=27 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `rationale`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (27): `[0-4]`, `[Acute / Chronic — DURATION of symptoms]`, `[CREDENTIALS]`, `[DATE]`, `[DEGREES]`, `[DESCRIBE — AC joint arthritis, biceps pathology, labral tear if applicable]`, `[DESCRIBE — retraction, fatty infiltration, muscle atrophy, associated pathology]`, `[DESCRIBE — to level of humeral head / glenoid]`, `[DESCRIBE — weakness with abduction, external rotation, lift-off test]`, `[DESCRIBE: supraspinatus, infraspinatus, subscapularis involvement]`, `[DETAILS]`, `[DURATION — minimum 6 weeks, OUTCOMES]`, `[EMAIL]`, `[I/IIa]`, `[MEDICATIONS, DURATION, RESPONSE]`, `[NPI]`, `[NUMBER, DATES, RESPONSE]`, `[PHONE]`, `[PHYSICIAN NAME]`, `[PRACTICE NAME]`, `[Present / Absent]`, `[Right / Left]`, `[SCORE]`, `[SIZE]`, `[SMALL <1cm / MEDIUM 1-3cm / LARGE 3-5cm / MASSIVE >5cm]`, `[TENDON(S)]`, `[supraspinatus / infraspinatus / subscapularis]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):20**

### 141 — Meniscus Repair Clinical Compass  
`MeniscusRepairAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=24 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `rationale`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (24): `[AGE]`, `[Acute (<3 months) / Chronic]`, `[CREDENTIALS]`, `[DATE]`, `[DESCRIBE — ACL status, chondral status, other meniscal pathology]`, `[DESCRIBE — Tegner activity scale, occupational demands, sports participation]`, `[DESCRIBE — any extension deficit, flexion limitation]`, `[DESCRIBE — locking, clicking, catching, giving way]`, `[DESCRIBE — peripheral location, vertical orientation, adequate tissue quality]`, `[DESCRIBE — tear location, morphology, signal characteristics, associated findings]`, `[DESCRIBE — vertical longitudinal, bucket-handle, radial, horizontal, complex]`, `[EMAIL]`, `[LENGTH]`, `[Medial / Lateral]`, `[NPI]`, `[PHONE]`, `[PHYSICIAN NAME]`, `[PRACTICE NAME]`, `[Positive / Negative]`, `[Present / Absent]`, `[Red-red zone / Red-white zone / White-white zone]`, `[Right / Left]`, `[SCORE]`, `[posterior horn / body / anterior horn]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):17**

### 142 — Epidural Steroid Injection Clinical Compass  
`EpiduralSteroidAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=7 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `approach`, `contraindications`, `cor`, `rationale`, `recommendation`, `spineRegion`, `urgency`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 143 — Facet Joint Injection Clinical Compass  
`FacetJointAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=7 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `procedureType`, `rationale`, `recommendation`, `spineRegion`, `urgency`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 144 — Radiofrequency Ablation Clinical Compass  
`RFAAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=7 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `cor`, `positiveBlocks`, `rationale`, `recommendation`, `spineRegion`, `urgency`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 145 — Spinal Cord Stimulator Clinical Compass  
`SCSAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=7 · `${}`=1

- **Derived from submitted data** (`result.*` → prose): `contraindications`, `cor`, `indication`, `phase`, `rationale`, `recommendation`, `urgency`

- **Filled on the page** (`[X]`→input on export): `[ADDITIONAL CLINICAL NOTES]`←`data.additionalClinicalNotes`, `[CREDENTIALS]`←`data.physicianCredentials`, `[EMAIL]`←`data.practiceEmail`, `[NPI]`←`data.npi`, `[PHONE]`←`data.practicePhone`, `[PHYSICIAN_NAME]`←`data.physicianName`, `[PRACTICE_NAME]`←`data.practiceName`

- **Shown as-is to fill**: none

### 146 — Elective PCI Clinical Compass  
`PCIAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=18 · `${}`=1

- **Derived from submitted data** (`result.*` → prose): `keyFindings`, `preferredStrategy`, `recommendation`, `syntaxCategory`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (18): `[ADDITIONAL_CLINICAL_NOTES]`, `[DESCRIBE HIGH-RISK FEATURES]`, `[DESCRIBE LESION(S): vessel, percent stenosis, location]`, `[DESCRIBE SYMPTOMS — angina class, duration, functional limitation]`, `[DESCRIBE: stress test findings, FFR value, nuclear imaging results]`, `[DURATION]`, `[IF FFR/iFR PERFORMED]`, `[IF STRESS TEST HIGH-RISK]`, `[LIST MEDICATIONS: statin, beta-blocker, RAAS inhibitor, antiplatelet therapy]`, `[NPI]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[SPECIFY WHICH CRITERIA APPLY]`, `[SYNTAX SCORE]`, `[VALUE]`

  - buckets → provider:6 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):12**

### 147 — AF Ablation Clinical Compass  
`AFAblationAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=20 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `anticoagulationNote`, `cha2ds2vascScore`, `guidelineClass`, `keyFindings`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (20): `[ADDITIONAL_CLINICAL_NOTES]`, `[DATE]`, `[DESCRIBE AAD SIDE EFFECTS]`, `[DESCRIBE FUNCTIONAL IMPACT]`, `[DESCRIBE SYMPTOMS: palpitations, dyspnea, fatigue, exercise intolerance, presyncope]`, `[DESCRIBE — therapeutic DOAC/warfarin for ≥3 weeks pre-procedure]`, `[DOSE]`, `[DRUG 1]`, `[DRUG 2 if applicable]`, `[DURATION]`, `[IF HF PRESENT]`, `[INEFFICACY / INTOLERANCE: describe]`, `[NPI]`, `[PAROXYSMAL / PERSISTENT]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[RESULT — no LAA thrombus confirmed]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):13**

### 148 — LAAC / Watchman Clinical Compass  
`LAACAppealLetter.tsx` · style **dynamic-body** · reads `?data`: True · `[]`=16 · `${}`=2

- **Derived from submitted data** (`result.*` → prose): `cha2ds2vascScore`, `deviceConsideration`, `guidelineClass`, `hasbledScore`, `keyFindings`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (16): `[ADDITIONAL_CLINICAL_NOTES]`, `[CALCULATE FROM CHA2DS2-VASc]`, `[DATE]`, `[DESCRIBE OAC CONTRAINDICATION IN DETAIL — e.g.:]`, `[DRUG]`, `[IF PRIOR ICH]`, `[NPI]`, `[OTHER: absolute contraindication, intolerance, compliance issues, falls risk]`, `[PAROXYSMAL / PERSISTENT / LONG-STANDING PERSISTENT]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[REASON]`, `[SIZE]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):9**

### 149 — Bariatric Surgery Clinical Compass  
`BariatricAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=31 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `bmiCategory`, `keyFindings`, `metabolicBenefit`, `preferredProcedure`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (31): `[ADDITIONAL_CLINICAL_NOTES]`, `[BMI]`, `[CHANGE]`, `[Class III / Class II]`, `[DATE]`, `[DATE if applicable]`, `[DATE if applicable — for OSA]`, `[DATE if applicable — for T2DM]`, `[DESCRIBE]`, `[DESCRIBE: worsening T2DM, cardiovascular risk, OSA, joint deterioration, etc.]`, `[DIETITIAN]`, `[DIETITIAN NAME]`, `[DURATION]`, `[END DATE]`, `[END WEIGHT]`, `[HEIGHT]`, `[LIST ANY WEIGHT LOSS MEDICATIONS]`, `[LIST COMORBIDITIES: T2DM, HTN, OSA, dyslipidemia, GERD, osteoarthritis, etc.]`, `[NPI]`, `[PCP/INTERNIST]`, `[PHYSICIAN/PROVIDER NAME]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[PSYCHOLOGIST/PSYCHIATRIST]`, `[SPECIFY WHICH CRITERION]`, `[START DATE]`, `[START WEIGHT]`, `[WEIGHT]`

  - buckets → provider:7 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):23**

### 150 — Cholecystectomy Clinical Compass  
`CholecystectomyAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=21 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `approach`, `keyFindings`, `recommendation`, `urgency`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (21): `[ADDITIONAL_CLINICAL_NOTES]`, `[DATE]`, `[DESCRIBE]`, `[DESCRIBE IMAGING: ultrasound / CT / HIDA scan]`, `[DESCRIBE OUTCOME]`, `[DESCRIBE SEVERITY]`, `[DESCRIBE SYMPTOMS]`, `[DURATION]`, `[EF]`, `[FREQUENCY]`, `[HAS / HAS NOT]`, `[IF ACUTE CHOLECYSTITIS]`, `[IF BILIARY DYSKINESIA]`, `[NPI]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[POSITIVE/NEGATIVE]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[TEMP]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):14**

### 151 — Hernia Repair Clinical Compass  
`HerniaAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=22 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `approach`, `keyFindings`, `meshRecommendation`, `recommendation`, `urgency`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (22): `[ADDITIONAL_CLINICAL_NOTES]`, `[DATE]`, `[DESCRIBE FINDINGS]`, `[DESCRIBE IMPACT ON QUALITY OF LIFE]`, `[DESCRIBE ONGOING SYMPTOMS]`, `[DESCRIBE SYMPTOMS]`, `[DESCRIBE SYMPTOMS: pain, discomfort, bulge, limitation of activity]`, `[DESCRIBE: perform work duties, exercise, lift objects, perform activities of daily living]`, `[DESCRIBE: physical activity, lifting, prolonged standing]`, `[DURATION]`, `[HERNIA TYPE]`, `[IF FEMORAL HERNIA]`, `[LAPAROSCOPIC / OPEN]`, `[LOCATION]`, `[NPI]`, `[PAIN LEVEL]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[reducible / incarcerated]`

  - buckets → provider:6 · patient/payer:0 · date:1 · codes:0 · **clinical (derivable):15**

### 152 — Breast Reduction Clinical Compass  
`BreastReductionAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=32 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `conservativeTreatmentMet`, `keyFindings`, `recommendation`, `schnurCategory`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (32): `[ADD ADDITIONAL SYMPTOMS AS APPLICABLE]`, `[ADDITIONAL_CLINICAL_NOTES]`, `[BSA]`, `[DESCRIBE]`, `[DESCRIBE FUNCTIONAL LIMITATIONS: work, exercise, perform activities of daily living]`, `[DESCRIBE ONGOING SYMPTOMS]`, `[DESCRIBE medications tried, duration, outcome]`, `[DESCRIBE weight loss attempts, if applicable]`, `[DESCRIBE — bilateral/unilateral, severity, duration]`, `[DESCRIBE — depth, pain, skin changes]`, `[DESCRIBE — kyphosis, forward head posture]`, `[DESCRIBE — location, severity, duration]`, `[DESCRIBE — location, severity, duration, impact on function]`, `[DESCRIBE — minimal/no improvement in back/neck/shoulder pain]`, `[DESCRIBE — rash, skin breakdown, treatment required]`, `[DESCRIBE — shoulder grooving persists, pain not adequately controlled]`, `[DESCRIBE: postural strengthening, cervical/thoracic spine, shoulder girdle]`, `[DURATION]`, `[HEIGHT]`, `[MEETS / BORDERLINE MEETS]`, `[MET / NOT MET — if not met, emphasize functional symptoms]`, `[NPI]`, `[Note: weight loss does not predictably reduce breast size in macromastia.]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[PROVIDER]`, `[RESECTION_WEIGHT]`, `[SCHNUR_MIN]`, `[WEIGHT]`

  - buckets → provider:7 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):25**

### 153 — Blepharoplasty / Ptosis Repair Clinical Compass  
`BlepharoplastyAppealLetter.tsx` · style **static-body** · reads `?data`: True · `[]`=20 · `${}`=0

- **Derived from submitted data** (`result.*` → prose): `coverageExpectation`, `functionalCriteriaMet`, `keyFindings`, `ptosisGrade`, `recommendation`

- **Filled on the page**: none auto-substituted (provider block shown as separate PDF fields, not merged into body)

- **Shown as-is to fill** (20): `[ACTIVITIES]`, `[ADD ADDITIONAL FINDINGS AS APPLICABLE]`, `[ADDITIONAL_CLINICAL_NOTES]`, `[CONFIRM ATTACHED — document eyelid position and visual obstruction]`, `[DEGREES]`, `[DESCRIBE — Humphrey / Goldmann perimetry results]`, `[DESCRIBE — difficulty reading, driving, performing daily activities]`, `[DESCRIBE — if applicable — compensatory brow elevation causing headaches, brow ache]`, `[DESCRIBE — skin/ptosis obstructing superior visual field]`, `[MEETS / BORDERLINE MEETS]`, `[NPI]`, `[Normal: 4-5mm; Ptosis: ≤2mm]`, `[PHYSICIAN_CREDENTIALS]`, `[PHYSICIAN_NAME]`, `[PRACTICE_EMAIL]`, `[PRACTICE_NAME]`, `[PRACTICE_PHONE]`, `[Poor: <4mm, Fair: 4-7mm, Good: >7mm]`, `[UPPER EYELID DERMATOCHALASIS / PTOSIS / ECTROPION / ENTROPION — specify]`, `[VALUE]`

  - buckets → provider:6 · patient/payer:0 · date:0 · codes:0 · **clinical (derivable):14**


## 🔑 Dynamic-feature opportunities (highest impact)

These are the levers to auto-fill what's currently manual:

1. **Provider block → from the logged-in user.** `[PHYSICIAN_NAME]/[CREDENTIALS]/[PRACTICE_NAME]/[NPI]/[PHONE]/[EMAIL]` appear as manual or page-input across most letters. The `User` model already has identity fields — prefill these once from the authenticated user / a provider profile and they vanish from every letter.

2. **Codes → from the module's `auth_guide`.** `[CPT_CODES]/[ICD_CODES]` are page inputs with hardcoded defaults; the module's `auth_guide.cptCodes/icd10Codes` already hold the authoritative codes — wire them in (this is exactly what the appeal_letter_template seeding already did).

3. **Clinical brackets → from the submission/result.** Tokens like `[PREVIOUS_TREATMENTS]`, `[MEDICATIONS, DURATION, RESPONSE]`, `[SYMPTOMS]`, `[SCORE]`, `[GRADE]`, `[SIZE]`, `[LOCATION]` are left manual in static-body letters, but the module's **form already collects** these answers and the **ported recommendation engine** computes scores/severity. Feed `submission.data` + the engine `result` into these → the biggest dynamic win, and it converts static-body letters into dynamic-body ones.

4. **Patient/payer block → needs a patient record.** `[PATIENT_NAME]/[PATIENT_DOB]/[MEMBER ID]/[POLICY_NUMBER]/[CLAIM NUMBER]/[INSURANCE …]` are genuinely not collected anywhere today — to auto-fill, add a patient/case entity (or capture these on the submission). Until then they must stay manual.


The existing **`appeal_letter_template`** system (`app/appeal_letter.py`, `{{placeholders}}` + `defaults`/`derived`/`sections`) is already the dynamic engine for #1–#3 — these per-module manual brackets are the worklist for extending it.


_Manual-bracket totals across all letters_: provider 186, patient/payer 45, date 30, codes 6, clinical 306.
