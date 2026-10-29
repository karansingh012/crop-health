# Architecture and API

Browser -> Nginx -> FastAPI -> PostgreSQL and private local image volume. FastAPI invokes CPU PyTorch inference when an approved checkpoint exists and retrieves weather from Open-Meteo on explicit requests. The offline research pipeline writes checkpoints; the serving process does not train models.

## Source boundaries

- `frontend/src/main.jsx`: reusable view components, routing, pages, auth context and data loading. `api.js`: JSON/multipart client and protected download helper. `styles.css`: responsive design and theme tokens.
- `backend/app/main.py`: REST routes, request logging, bounds, error middleware and rate limits.
- `backend/app/security.py`: hashing, login sessions and current-user dependency.
- `backend/app/db.py`: SQLAlchemy entities; `schemas.py`: Pydantic API contracts.
- `backend/app/services`: inference, weather, guidance, reports and storage are independent modules.
- `backend/migrations`: explicit versioned schema migration. Migration is a separate Compose job before backend startup.
- `ml`: offline dataset inspection, architectures, training, evaluation, external mapping and result aggregation.

## Schema

| Table | Key / relationships | Content |
|---|---|---|
| users | integer id, unique indexed email | name, Argon2 hash, created_at |
| sessions | token_hash PK, indexed user_id FK | expiry; raw bearer token is never stored |
| fields | id, indexed user_id FK | name, crop, area in hectares, location, timestamp |
| scans | id, indexed user_id and field_id FKs | opaque image key, notes, JSON prediction with guidance and model metadata, timestamp |
| followups | id, user_id and scan_id FKs, due_at index | due date, completion flag |

Prediction and report metadata are embedded in the immutable scan record; PDF bytes are generated on demand. Disease content is a versioned code catalog instead of an editable table. There is no expert request inbox because the implementation uses explicit email composition. Deleting a field detaches scans rather than deleting observations.

## API inventory

All paths start with `/api`. Health, registration and login are public. Everything else needs `Authorization: Bearer <token>`.

| Method | Path | Behavior |
|---|---|---|
| GET | /health | DB availability and model file configuration |
| POST | /auth/register | create account and issue session (201) |
| POST | /auth/login | verify credentials and issue session |
| POST | /auth/logout | revoke current session (204) |
| GET/PATCH | /me | view/update display name |
| GET/POST | /fields | list/create fields |
| PATCH/DELETE | /fields/{id} | edit/delete owned field |
| POST | /scans | multipart file, optional field_id, notes (201) |
| GET | /scans | list with field_id, limit <=500, offset |
| GET | /scans/{id} | observation and nested assessment |
| GET | /scans/{id}/image | private normalized JPEG |
| GET | /scans/{id}/report | private PDF download; language=en or hi |
| GET/POST | /followups | list/create reminder, optional aware due_at |
| PATCH/DELETE | /followups/{id} | mark done/undo or delete |
| GET | /locations | authenticated city/village/postal-code lookup; q and en/hi language |
| GET | /weather | internal bounded coordinates supplied by place selection or device location; no coordinate-entry UI |
| POST | /scans/{id}/reanalyze | reassess owned saved image into a new record; preserve original |
| GET | /diseases | available sourced guidance catalog |
| GET | /risk/{id} | stored guidance for owned observation |
| GET | /experts | operator-configured contact or explicit unavailable state |

Errors use `detail` and appropriate 401, 404, 409, 413, 422, 429, 502, 503 statuses. Unexpected errors are logged server-side and return a generic 500. Validation errors retain FastAPI's field-level detail format. Request IDs and structured request logs support diagnostics.

## Security and limits

The browser stores a short-lived bearer token in sessionStorage, so an XSS vulnerability would expose it. Production Nginx supplies a restrictive CSP; no raw HTML insertion is used. Add a hardened HttpOnly-cookie design with CSRF protection if your deployment requires it. No password recovery/email verification is implemented. Use an identity provider or implement verified recovery before opening public enrollment.

Compose publishes only the frontend to loopback. The database and backend have no host ports. Nginx rejects oversized bodies and applies request limits. The app rate limiter is per process and includes a separate auth bucket; at scale use a trusted edge/WAF or distributed limiter. Do not trust arbitrary forwarded headers. Uploads are bounded again by decoded pixel count and read size. The server runs as a non-root user.

LocalStorage exposes save/path/delete as a small abstraction. For multi-instance AWS deployment implement an S3 adapter with private bucket access; the provided code only implements the local-volume adapter. Object storage and disaster recovery are not simulated.

## Language and fonts

`shared/hi.json` holds the shared interface/report catalog; `shared/class-hi.json` maps crop and disease display names. API identifiers and user-entered text are never translated or mutated. Language is stored locally and updates document language, dates, accessible labels and reports. Noto fonts are bundled under SIL OFL; HarfBuzz shapes Devanagari in PDFs. The PDF font combines Noto Sans Latin and Devanagari glyphs to avoid mixed-font shaping defects.
