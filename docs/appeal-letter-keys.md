# Appeal-letter page-fill keys

The canonical placeholder vocabulary used by appeal-letter templates
(`{{key}}` in the body, with a fallback in the template's `defaults` block).
All 80 file-driven templates in `forms/appeal_letter_templates/` carry the same
22 keys; the renderer is `app/appeal_letter.py` and the source of truth for the
vocabulary is the `CANON` dict in `scripts/build_appeal_letter_templates.py`.

## Patient / claim (admin)

| key | default |
|---|---|
| `patient_name` | `[Patient Name]` |
| `patient_dob` | `[Date of Birth]` |
| `member_id` | `[Member ID]` |
| `policy_number` | `[Policy Number]` |
| `claim_number` | `[Claim Number]` |
| `letter_date` | `[Date]` |

## Provider / practice

| key | default |
|---|---|
| `physician_name` | `[Physician Name]` |
| `credentials` | `[Credentials]` |
| `npi` | `[NPI]` |
| `practice_name` | `[Practice Name]` |
| `practice_phone` | `[Phone]` |
| `practice_email` | `[Email]` |
| `practice_fax` | `[Fax]` |
| `practice_address` | `[Practice Address]` |

## Payer

| key | default |
|---|---|
| `insurance_name` | `the plan` |
| `insurance_address` | `[Insurance Address]` |
| `medical_director` | `Medical Director` |

## Clinical

| key | default |
|---|---|
| `specialty` | `[Specialty]` |
| `procedure_description` | `[Procedure Description]` |
| `cpt_codes` | from the module's auth guide, else `[CPT Code(s)]` |
| `icd_codes` | from the module's auth guide, else `[ICD-10 Code(s)]` |
| `additional_clinical_notes` | `""` (empty) |

## Plain list

```
patient_name, patient_dob, member_id, policy_number, claim_number, letter_date,
physician_name, credentials, npi, practice_name, practice_phone, practice_email,
practice_fax, practice_address, insurance_name, insurance_address, medical_director,
specialty, procedure_description, cpt_codes, icd_codes, additional_clinical_notes
```

## Notes

- `{{sections}}` is renderer-internal (assembled from conditional `sections`), not
  a fillable key, so it never appears in `defaults`.
- Uniformity is applied by `scripts/uniform_appeal_letter_keys.py` and synced into
  Postgres via `scripts/seed_appeal_letter_templates.py` (matches modules by title).
- The legacy module **id 25 "Rectal Cancer"** uses a separate camelCase set
  (`patientName`, `physicianName`, `insuranceCompany`, `cptCodes`) and is **not**
  part of these 22 keys — see the canonical "Rectal Cancer Clinical Compass" (id 85).
