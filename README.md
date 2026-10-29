# Canopy - Crop Health Assistant

A React/FastAPI application and a separate PyTorch research pipeline implementing the supplied crop-health synopsis. Real records, PostgreSQL persistence, private images, downloadable PDF reports and configurable weather/expert services. **A real PlantVillage research-preview model is installed and included in the project archive.** See `docs/MODEL_CARD.md` for measured results and limits. Without a checkpoint the application records observations with `model_unavailable`, no class and no score.

## Start with Docker

Requires Docker Engine and Compose, roughly several GB free disk for Python/PyTorch images, and an available localhost port 8080. Run from this directory:

```sh
cp .env.example .env
# Replace POSTGRES_PASSWORD in .env with a long random URL-safe secret.
mkdir -p models
docker compose up --build -d
```

If `.env` already exists, preserve it. The implementation session generated a local secret for the running installation. Do not commit or share it.

Open http://localhost:8080 and register a new account. API documentation: http://localhost:8080/api/docs. The generated OpenAPI document is also in `docs/openapi.json`.

```sh
docker compose ps
docker compose logs --tail=100 backend
docker compose stop       # preserve records and images
docker compose start
```

Do not use `docker compose down -v` unless you intend to delete the database and image volumes.

## Local development

Python 3.11+, Node 22+, PostgreSQL 16 for normal operation. SQLite is supported for isolated tests or a lightweight explicit development session.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt -r ml/requirements.txt
# Set DATABASE_URL to your PostgreSQL SQLAlchemy URL for persistent deployment.
# For development only:
export DATABASE_URL=sqlite:///./development.db
alembic -c backend/alembic.ini upgrade head
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. The Vite proxy forwards `/api` to port 8000. Production Nginx serves the compiled frontend and proxies the same path. Never use the Vite development server publicly.

## Features

- Landing, registration, login, dashboard, scanner, observation result, fields, history, reports, follow-ups, weather, expert support, profile and help pages.
- Responsive green/neutral design, light/dark theme, persistent Hindi/English switching, loading and error states, form constraints, toast feedback and protected navigation. Interface strings, guidance and PDF reports follow the selected language; names and notes remain as entered.
- Argon2 password hashing; random bearer sessions stored as SHA-256 digests in the database; 12-hour expiry and server-side logout revocation.
- Every field, scan, image, report and reminder is checked against the current user. Private images have no public static route.
- Image bytes are decoded, dimensions and pixel count checked, metadata stripped by re-encoding; maximum 8 MB, JPEG/PNG/WebP only. Basic lighting/contrast checks are informational, not a validated quality/OOD detector.
- Field CRUD, persistent notes and model assessment, field filtering, paginated history, side-by-side record comparison, per-scan PDF download.
- Follow-up dates default to seven days and can be configured. Completion/deletion supported. **In-app reminders only; no background email/push delivery.**
- Weather by city/village/postal-code search or an explicit browser location request; no coordinate entry. Matching places include region/country to avoid choosing the wrong town. Open-Meteo weather estimates with timestamps/units, provider timeouts and error handling. The free noncommercial endpoint needs no key; commercial customer keys use `OPEN_METEO_API_KEY`. Set `WEATHER_ENABLED=false` to disable. Review provider terms before production.
- Expert details are operator-configured; `mailto` opens the user's client. Users explicitly download and attach a report. No invented experts or automatic sharing.
- Disease-specific content currently covers tomato/potato early blight only, based on UMN Extension. Other classes receive clearly labeled general guidance. Weather context is not a validated disease risk score.

## Model installation and experiments

See [research methodology](docs/RESEARCH.md) and [installed model card](docs/MODEL_CARD.md). Saved observations created before model installation can be reassessed using **Assess this image again**, which creates a new record and preserves the original. The application expects `models/selected.pt` in Compose. Restart the backend after replacing it. The checkpoint must be produced by this pipeline, match its classes/architecture/preprocessing and have `trained=true`, `development_only=false`. Development fixtures are deliberately rejected. Only load trusted local checkpoints.

Without a validation-selected threshold, every real model prediction is marked uncertain. Scores are explicitly uncalibrated. There is no reliable unsupported-crop/non-plant detector and no validated probability calibration. No crop-performance numbers should be inferred from synthetic smoke tests.

## Tests

```sh
pytest backend/tests -q
cd frontend
npm run build
npx playwright install chromium
# Start Compose first; provide any valid >=64px PNG/JPEG test image.
TEST_IMAGE=/absolute/path/to/test-leaf.png npm test
```

The browser tests create separate accounts and records against the actual API and verify both observation-only and trained-model states as applicable. The multilingual suite also exercises live place search, location permission/denial and Hindi PDF downloads. Do not run it against a production database. Tests cover isolation, CRUD, upload validation, session revocation, weather failures, PDF download, navigation, desktop/mobile layout and model tensor paths. See [verification status](docs/STATUS.md) for actual executed checks.

## Documentation

- [Architecture, API and schema](docs/ARCHITECTURE.md)
- [Datasets, training, evaluation and limitations](docs/RESEARCH.md)
- [AWS deployment, backup and recovery](docs/DEPLOYMENT.md)
- [Demo, troubleshooting and viva notes](docs/DEMO_AND_VIVA.md)
- [Actual implementation and verification status](docs/STATUS.md)

Dependency versions are pinned in `backend/requirements.txt`, `ml/requirements.txt`, and `frontend/package.json`; the frontend includes an npm lockfile. Review vulnerability scans again before public deployment. No AWS resources were created.
