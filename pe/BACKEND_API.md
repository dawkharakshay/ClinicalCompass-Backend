# PE Compass — Backend API Specification

## Context

PE Compass is a clinical decision-support React app (Vite + Capacitor) for acute pulmonary
embolism management. It currently uses **Supabase** for auth, database, and a push-notification
edge function. The goal is to replace Supabase with a **custom backend** using:

- **Database:** PostgreSQL (reuse the existing schema in `supabase/migrations/`)
- **Auth:** Custom JWT (access + refresh tokens), no third-party provider

This doc lists every API endpoint the backend must expose, with request/response shapes, so the
frontend can drop Supabase and call these instead.

---

## Conventions

- Base URL: `/api` (suggested)
- All request/response bodies are JSON.
- **Auth:** protected endpoints require `Authorization: Bearer <access_token>`. The backend
  verifies the JWT, extracts `user_id`, and **scopes every query to that user**. This replaces
  Supabase Row-Level Security (RLS), which is enforced at the DB layer today — you must now
  enforce ownership in application code.
- Timestamps are ISO 8601 strings.
- `patient_data`, `classification_result`, `indications`, `contraindications`,
  `assessment_details` are stored as Postgres `jsonb`.

---

## 1. Auth — replaces `supabase.auth.*`

### POST `/auth/signup`
Create user + auto-create profile (replaces the old `handle_new_user` DB trigger).
```jsonc
// Request
{ "email": "dr@hospital.org", "password": "…", "full_name": "Jane Doe", "hospital_affiliation": "Temple" }
// Response 201
{ "access_token": "…", "refresh_token": "…", "user": { "id": "uuid", "email": "dr@hospital.org" } }
```

### POST `/auth/login`
```jsonc
// Request
{ "email": "dr@hospital.org", "password": "…" }
// Response 200
{ "access_token": "…", "refresh_token": "…", "user": { "id": "uuid", "email": "…" } }
```

### POST `/auth/logout`
Invalidate the refresh token. Requires auth. → `204`

### POST `/auth/refresh`
Replaces Supabase `autoRefreshToken`.
```jsonc
// Request
{ "refresh_token": "…" }
// Response 200
{ "access_token": "…", "refresh_token": "…" }
```

### GET `/auth/session`
Replaces `getSession()` / `getUser()`. Requires auth.
```jsonc
// Response 200
{ "user": { "id": "uuid", "email": "…" } }   // 401 if token invalid/expired
```

### POST `/auth/forgot-password`
Send a reset link pointing to the app's `/reset-password` page.
```jsonc
{ "email": "dr@hospital.org" }   // → 200 always (don't leak which emails exist)
```

### POST `/auth/reset-password`
Replaces `updateUser({ password })` after recovery.
```jsonc
{ "token": "<reset-token-from-email>", "password": "newpass" }   // → 200
```

### (Optional) Google OAuth — `/auth/oauth/google`
Currently handled via Lovable (`lovable.auth.signInWithOAuth("google")`). Only build if you want
to keep Google sign-in; otherwise drop it.

---

## 2. Profiles — table `profiles`

> No create endpoint — the profile row is created during signup.

### GET `/profile` *(auth)*
```jsonc
// Response 200
{ "display_name": "Jane Doe", "hospital_affiliation": "Temple" }
```

### PATCH `/profile` *(auth)*
```jsonc
// Request (any subset)
{ "display_name": "Jane D.", "hospital_affiliation": "Temple University Hospital" }
// Response 200 → updated profile
```

---

## 3. Patient Classifications — table `patient_classifications`

### GET `/patient-classifications` *(auth)*
List the current user's records, newest first.
```jsonc
// Response 200
[
  {
    "id": "uuid",
    "patient_name": "…",
    "patient_data": { /* PatientData */ },
    "classification_result": { /* ClassificationResult */ },
    "category": "C1",
    "risk_level": "high",
    "respiratory_modifier": false,
    "created_at": "2026-06-30T…"
  }
]
```

### POST `/patient-classifications` *(auth)*
```jsonc
// Request
{
  "patient_name": "…",
  "patient_data": { /* PatientData */ },
  "classification_result": { /* ClassificationResult */ },
  "category": "C1",
  "risk_level": "high",
  "respiratory_modifier": false
}
// Response 201 → created record (user_id taken from JWT, not the body)
```

### DELETE `/patient-classifications/:id` *(auth)*
Deletes only if the record belongs to the caller. → `204` (or `404` if not owned).

---

## 4. ECMO Candidacy Assessments — table `ecmo_candidacy_assessments`

### POST `/ecmo-assessments` *(auth)*
```jsonc
// Request
{
  "patient_name": "…",
  "patient_data": { /* PatientData */ },
  "pe_category": "C3",
  "indications": [ /* … */ ],
  "contraindications": [ /* … */ ],
  "save_score": 3,
  "save_risk_class": "III",
  "recommended_config": "VA-ECMO",
  "candidacy_result": "candidate",
  "assessment_details": { /* ECMOAssessmentResult */ }
}
// Response 201 → created record
```

> The frontend currently only **inserts** ECMO assessments. Add `GET /ecmo-assessments` and
> `DELETE /ecmo-assessments/:id` later if you want to list/manage them.

---

## 5. Device Tokens — table `device_tokens` (mobile push)

### POST `/device-tokens` *(auth)*
Upsert on conflict of `(user_id, token)`.
```jsonc
{ "token": "fcm-or-apns-token", "platform": "ios" }   // platform ∈ ios|android|web → 200
```

### DELETE `/device-tokens` *(auth)*
Delete all of the current user's tokens (used on sign-out). → `204`

---

## 6. Push Notification Sender — replaces the `send-push-notification` edge function

### POST `/notifications/send`
Server-to-server / admin endpoint. Looks up the user's device tokens and delivers via FCM
(Android) / APNs (iOS). The current Supabase edge function is a stub — wire up `FCM_SERVER_KEY`.
```jsonc
// Request
{ "user_id": "uuid", "title": "…", "body": "…", "data": { } }
// Response 200
{ "success": true, "sent": 2 }
```

---

## Database Tables (already defined in `supabase/migrations/`)

| Table | Key columns |
|---|---|
| `profiles` | id, user_id (unique FK), display_name, hospital_affiliation, created_at, updated_at |
| `patient_classifications` | id, user_id, patient_name, patient_data (jsonb), classification_result (jsonb), category, risk_level, respiratory_modifier, created_at |
| `ecmo_candidacy_assessments` | id, user_id, patient_name, patient_data (jsonb), pe_category, indications (jsonb), contraindications (jsonb), save_score, save_risk_class, recommended_config, candidacy_result, assessment_details (jsonb), created_at, updated_at |
| `device_tokens` | id, user_id, token, platform (ios/android/web), created_at, updated_at; unique (user_id, token) |

> You'll need your own `users` table (email, password_hash, created_at) to replace Supabase's
> `auth.users`. Point the existing `user_id` foreign keys at it.

---

## Endpoint Summary

| # | Group | Endpoints |
|---|---|---|
| 1 | Auth | signup, login, logout, refresh, session, forgot-password, reset-password (+ optional Google OAuth) |
| 2 | Profiles | GET /profile, PATCH /profile |
| 3 | Patient Classifications | GET, POST, DELETE /:id |
| 4 | ECMO Assessments | POST (GET/DELETE optional) |
| 5 | Device Tokens | POST, DELETE |
| 6 | Notifications | POST /notifications/send |

**~17 endpoints total.** Minimum to make the app fully functional: **Auth + Profiles +
Patient Classifications + ECMO Assessments**. Device tokens & notifications are only needed if
you ship the Capacitor mobile push feature.

---

## Frontend Files to Update (swap Supabase → fetch calls)

- `src/integrations/supabase/client.ts` → replace with an `apiClient` (base URL + JWT header + token refresh)
- `src/contexts/AuthContext.tsx` → session/login/logout against `/auth/*`
- `src/pages/Auth.tsx` → signup / login / forgot-password
- `src/pages/ResetPassword.tsx` → `/auth/reset-password`
- `src/hooks/usePatientHistory.ts` → `/patient-classifications`
- `src/hooks/useProfile.ts` + `src/pages/Profile.tsx` → `/profile`
- `src/pages/ECMOAssessment.tsx` → `/ecmo-assessments`
- `src/services/pushNotifications.ts` → `/device-tokens`

The core clinical logic (`src/lib/peClassification.ts`, `src/lib/ecmoCandidacy.ts`) is
client-side and needs **no** backend changes.
