# SevaSetu AI

AI-powered civic issue detection, prioritisation and resolution tracking — a working prototype built for the
Seva Innovation Challenge (Urban Development).

**Flow:** citizen photo + location → AI analysis → duplicate check → priority score → department routing →
authority action → resolution with before/after photos → verification.

## Features
- **Citizen portal:** register/login, report with photo + GPS/map pin, track status timeline, see before/after.
- **AI:** YOLO road-damage detector (RDD2022 classes) → issue category, *model confidence*, severity heuristic.
  If no model is installed the app falls back to manual category selection (it never fabricates a detection).
- **Priority engine:** 30% severity · 20% report frequency · 20% location criticality · 15% traffic/footfall (proxy) ·
  15% time unresolved. A prototype decision-support rule, not an official policy; the per-factor breakdown is shown.
- **Duplicate detection (PostGIS):** same category within 25 m → merged into one issue; 25–60 m → flagged for review.
- **Authority dashboard:** KPIs, Recharts analytics, filterable priority queue, assignment, status workflow,
  duplicate review, resolution + human verification.
- **Hotspot map:** Leaflet/OpenStreetMap markers and DBSCAN hotspot clusters.

## Stack
React (Vite) · FastAPI · PostgreSQL + PostGIS · SQLAlchemy + Alembic · Ultralytics YOLO · Leaflet · Recharts · Pytest

## Requirements
Python 3.11–3.13 · Node.js 18+ · PostgreSQL 14+ **with the PostGIS extension** (on Windows, tick PostGIS in
Stack Builder after installing PostgreSQL). Tested here on PostgreSQL 16 + PostGIS 3.4, Python 3.13, Node 22.

## Quick start (Windows / PowerShell)
```powershell
# 1. databases (the app DB and a SEPARATE test DB)
psql -U postgres -c "CREATE DATABASE sevasetu_db;"
psql -U postgres -c "CREATE DATABASE sevasetu_test_db;"

# 2. backend
cd backend
python -m venv venv ; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # edit: put your postgres password in DATABASE_URL, set a long SECRET_KEY
alembic upgrade head            # creates the PostGIS extension, tables and views (head: 7462ac3c272d)
python -m app.seed              # departments + demo accounts
python -m app.seed_demo         # OPTIONAL synthetic demo data (49 issues, clearly labelled synthetic)
uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs  and  /health

# 3. frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173  (proxies /api and /uploads to port 8000)
```
Demo logins (password `demo1234`): `citizen@demo.sevasetu`, `authority@demo.sevasetu`, `demo01@demo.sevasetu`…

## AI model
See `ai/README.md`. Train on Colab with `ai/training/rdd_pipeline.py`, put the weights at
`ai/models/sevasetu_road_damage.pt`, then `pip install ultralytics` in the backend venv. Without weights the app
runs normally and asks the citizen to pick the category (the AI panel says "model not loaded").
Evaluate on your own labelled photos:
`python -m app.evaluation.run_eval --data ../data/validation` (writes `docs/ai_eval_app.*`).
The detector is trained on road damage only; garbage, water leakage and streetlight are **manual categories**.

## Tests (use the separate test database)
The suite creates many rows, so it refuses to run unless `DATABASE_URL` names a database containing "test".
```powershell
cd backend
$env:DATABASE_URL = "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/sevasetu_test_db"
alembic upgrade head            # migrate the test DB once
python -m pytest -q tests       # 77 tests; AI tests use fake detectors, no weights needed
python scripts/generate_test_report.py   # re-runs and rewrites docs/TEST_REPORT.md
```
(Close the PowerShell window or run `Remove-Item Env:DATABASE_URL` afterwards so the app uses `.env` again.)

## Repository map
`backend/` API, services, models, migrations, tests · `frontend/` React app · `ai/` training + model ·
`data/` validation set layout · `docs/` diagrams, screenshots, demo script, test report.

## Honest limitations
- Synthetic demo data only; no real citizen data, no pilot, no government integration.
- Real-model metrics exist only after you train and evaluate (the harness writes `docs/ai_eval_app.*`; no measured numbers are claimed until then).
- Traffic/footfall is a per-category proxy; location criticality is keyword-based.
- Duplicate detection uses distance, category and time only (no image similarity).
- Resolution verification is human-confirmed (no computer-vision check).
- Images are stored on local disk; no production hardening (rate limits, HTTPS, object storage).
