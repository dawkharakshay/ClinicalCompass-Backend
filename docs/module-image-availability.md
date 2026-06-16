# ClinicalCompass — Specialties, Modules & Image Availability

_Generated 2026-06-16. Source: `app/seed/modules_seed.json` (logo_url) verified live against https://clinicalcompass.net and its CloudFront CDN._
**Summary: 20 specialties, 104 modules — 103/104 module images available.**

> **Note on specialty images:** The `Speciality` model has an `image` column (admin-uploadable), but **no specialty images are seeded or provisioned** — all 20 specialties have `image = NULL` in the database. There is no `logo_url` for specialties in `app/seed/modules_seed.json` and no fetch script for them (unlike module logos). Specialties render without an image. The table below covers **module** images only.


## Surgery & Surgical Oncology (4 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Rectal Cancer Clinical Compass | ✅ | CDN | 200 |
| Liver Tumor Clinical Compass | ✅ | CDN | 200 |
| Obesity Treatment Clinical Compass | ✅ | CDN | 200 |
| Spine Surgery Clinical Compass | ✅ | CDN | 200 |

## ENT, Endocrine & Sleep Medicine (7 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Thyroid Nodule Clinical Compass | ✅ | CDN | 200 |
| OSA Clinical Compass | ✅ | CDN | 200 |
| Narcolepsy Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Chronic Insomnia Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Central Sleep Apnea Clinical Compass | ✅ | clinicalcompass.net | 200 |
| RLS / PLMD Clinical Compass | ✅ | clinicalcompass.net | 200 |
| OSA + Obesity Clinical Compass | ✅ | CDN | 200 |

## Interventional Radiology (15 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Pulmonary Embolism Clinical Compass | ✅ | CDN | 200 |
| Women's Health Clinical Compass | ✅ | CDN | 200 |
| Prostatic Artery Embolization Clinical Compass | ✅ | CDN | 200 |
| Varicocele Embolization Clinical Compass | ✅ | CDN | 200 |
| Portal Hypertension Clinical Compass | ✅ | CDN | 200 |
| Geniculate Artery Embolization Clinical Compass | ✅ | CDN | 200 |
| Percutaneous AV Fistula Clinical Compass | ✅ | CDN | 200 |
| Bone Cancer Interventional Oncology Clinical Compass | ✅ | CDN | 200 |
| Y-90 Radioembolization Clinical Compass | ✅ | CDN | 200 |
| Endovenous Ablation Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Sclerotherapy Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Vertebroplasty / Kyphoplasty Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Sacroplasty Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Peripheral Atherectomy Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Renal Cryoablation Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Cardiology & Interventional Cardiology (5 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Acute Coronary Syndrome Clinical Compass | ✅ | CDN | 200 |
| Dyslipidemia Clinical Compass | ✅ | CDN | 200 |
| Elective PCI Clinical Compass | ✅ | clinicalcompass.net | 200 |
| AF Ablation Clinical Compass | ✅ | clinicalcompass.net | 200 |
| LAAC / Watchman Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Vascular Medicine & Surgery (2 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| PAD Revascularization Clinical Compass | ✅ | CDN | 200 |
| PAD Clinical Performance & Quality Measures Clinical Compass | ✅ | CDN | 200 |

## Hematology (5 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Venous Thromboembolism Clinical Compass | ✅ | CDN | 200 |
| Acute Myeloid Leukemia Clinical Compass | ✅ | CDN | 200 |
| Acute Lymphoblastic Leukemia & CAR-T Clinical Compass | ✅ | CDN | 200 |
| Aplastic Anemia Clinical Compass | ✅ | CDN | 200 |
| Amyloidosis Diagnostic Clinical Compass | ✅ | CDN | 200 |

## Neurosurgery & Neuro-Oncology (6 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Pituitary Adenoma Clinical Compass | ✅ | CDN | 200 |
| Vestibular Schwannoma Clinical Compass | ✅ | CDN | 200 |
| Brain Metastases Clinical Compass | ✅ | CDN | 200 |
| Low-Grade Glioma Clinical Compass | ✅ | CDN | 200 |
| Cerebral Cavernous Malformation Compass | ✅ | CDN | 200 |
| Spine Antithrombotic Compass | ✅ | CDN | 200 |

## Dermatology (5 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Atopic Dermatitis Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Acne Vulgaris Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Psoriasis Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Melanoma Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Hidradenitis Suppurativa Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Neurology (5 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Functional Seizures (PNES) | ✅ | clinicalcompass.net | 200 |
| Acute Ischemic Stroke | ✅ | clinicalcompass.net | 200 |
| Migraine | ✅ | clinicalcompass.net | 200 |
| Multiple Sclerosis | ✅ | clinicalcompass.net | 200 |
| Parkinson's Disease | ✅ | clinicalcompass.net | 200 |

## Ophthalmology (3 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Age-Related Macular Degeneration | ✅ | clinicalcompass.net | 200 |
| High Myopia / Pathologic Myopia | ✅ | clinicalcompass.net | 200 |
| Glaucoma | ✅ | clinicalcompass.net | 200 |

## Gastroenterology & Interventional GI (10 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Crohn's Disease Clinical Compass | ✅ | CDN | 200 |
| Ulcerative Colitis Clinical Compass | ✅ | CDN | 200 |
| MASLD / MASH Clinical Compass | ✅ | CDN | 200 |
| Gastroparesis Clinical Compass | ✅ | CDN | 200 |
| CRC Screening Clinical Compass | ✅ | CDN | 200 |
| IBD Preventive Care Clinical Compass | ✅ | CDN | 200 |
| Pancreatic Mass Evaluation Clinical Compass | ✅ | CDN | 200 |
| Therapeutic EUS Clinical Compass | ✅ | CDN | 200 |
| Chronic Pancreatitis Clinical Compass | ✅ | CDN | 200 |
| Biliary Strictures Clinical Compass | ✅ | CDN | 200 |

## Pediatrics (8 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Pediatric Immunization Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Bright Futures Well-Child Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Pediatric Obesity Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Febrile Infant Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Neonatal Hyperbilirubinemia Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Influenza Prevention Clinical Compass | ✅ | clinicalcompass.net | 200 |
| RSV Prevention Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Pediatric Mental Health Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Radiation Oncology (1 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Radiation Oncology Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Psychiatry (1 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Psychiatry Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Orthopedics & Spine Surgery (6 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Total Knee Arthroplasty Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Total Hip Arthroplasty Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Spinal Fusion Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Artificial Disc Replacement Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Rotator Cuff Repair Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Meniscus Repair Clinical Compass | ❌ MISSING | clinicalcompass.net | 403 |

## Pain Medicine & Interventional Procedures (4 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Epidural Steroid Injection Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Facet Joint Injection Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Radiofrequency Ablation Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Spinal Cord Stimulator Clinical Compass | ✅ | clinicalcompass.net | 200 |

## General Surgery & GI Surgery (3 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Bariatric Surgery Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Cholecystectomy Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Hernia Repair Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Plastic & Reconstructive Surgery (2 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Breast Reduction Clinical Compass | ✅ | clinicalcompass.net | 200 |
| Blepharoplasty / Ptosis Repair Clinical Compass | ✅ | clinicalcompass.net | 200 |

## Urology & Male Reproductive Medicine (5 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| Vasectomy Reversal Clinical Compass | ✅ | CDN | 200 |
| Varicocelectomy Clinical Compass | ✅ | CDN | 200 |
| TESE / Micro-TESE Clinical Compass | ✅ | CDN | 200 |
| Peyronie's Disease Surgery Clinical Compass | ✅ | CDN | 200 |
| Gender-Affirming Urologic Procedures Clinical Compass | ✅ | CDN | 200 |

## Reproductive Endocrinology & Infertility (7 modules)

| Module | Image | Source | HTTP |
|---|---|---|---|
| In Vitro Fertilization Clinical Compass | ✅ | CDN | 200 |
| Intracytoplasmic Sperm Injection Clinical Compass | ✅ | CDN | 200 |
| Preimplantation Genetic Testing Clinical Compass | ✅ | CDN | 200 |
| Oocyte Cryopreservation Clinical Compass | ✅ | CDN | 200 |
| Embryo Cryopreservation Clinical Compass | ✅ | CDN | 200 |
| Ovulation Induction Clinical Compass | ✅ | CDN | 200 |
| Gestational Carrier Clinical Compass | ✅ | CDN | 200 |
