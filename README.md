<<<<<<< HEAD
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
=======
# SevaSetu-AI


# SevaSetu AI 🇮🇳

### AI-Powered Access to Government Services

SevaSetu AI is an AI-driven platform designed to make government services easier to discover and understand. It aims to help citizens navigate public-service information through an accessible interface, intelligent assistance, and simplified workflows.

The project explores how artificial intelligence and digital technology can help bridge the gap between citizens and government services.

---

## 🌟 Overview

Finding the right government scheme, understanding eligibility requirements, and navigating application procedures can be challenging.

SevaSetu AI aims to simplify this experience by bringing relevant public-service information together in one platform.

### Objectives

- Improve access to government-service information.
- Make complex service details easier to understand.
- Explore AI-assisted citizen support.
- Provide a user-friendly digital experience.
- Support the development of more accessible public services.

## ✨ Key Features

> Update this section to reflect the features implemented in your current version.

- **AI-powered assistance:** Help users understand public-service information using AI.
- **Government-service discovery:** Organize relevant service and scheme information.
- **Citizen-focused interface:** Provide a straightforward way to explore available services.
- **Digital service accessibility:** Explore ways to make public-service information easier to access.
- **Modular architecture:** Separate application components to support future development.

## 🛠️ Technology Stack

The project uses a modular architecture with components for the application, AI functionality, data, and database management.

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | Project frontend (see `frontend/`) |
| AI / ML | Python-based AI components |
| Database | PostgreSQL |
| Geospatial capabilities | PostGIS, if configured |
| API documentation | FastAPI Swagger UI |

*Confirm the technologies and integrations against the current repository before publishing.*

## 🏗️ Project Structure

The repository is organized into separate components:

```text
SevaSetuAI/
├── backend/       # Backend API and application logic
├── frontend/      # User interface
├── ai/            # AI-related components
├── data/          # Project data and resources
├── database/      # Database-related files
├── docs/          # Project documentation
├── README.md
└── ...
```

The exact files and subdirectories may vary as the project evolves.

## 🚀 Getting Started

Follow these steps to set up the project locally.

### Prerequisites

Install the tools required by the components you intend to run:

- Python 3.10 or a compatible version specified by the project
- Git
- PostgreSQL, if the application uses a local PostgreSQL database
- Node.js and npm, if required by the frontend

### 1. Clone the repository

```bash
git clone https://github.com/ngupta1035/SevaSetu-AI.git
cd SevaSetu-AI
```

### 2. Create a Python virtual environment

**Windows — PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install backend dependencies

If the backend has a `requirements.txt` file:

```bash
pip install -r backend/requirements.txt
```

If the requirements file is located elsewhere, use its actual path.

### 4. Configure environment variables

Create a `.env` file in the location expected by the backend.

Example configuration:

```env
# Add the environment variables required by your application.
# Do not commit passwords, API keys, or other secrets.
```

Set up the database and any external API credentials required by your local configuration.

### 5. Run the backend

From the repository root, use the command appropriate for your FastAPI application.

For example, if the application entry point is `backend/app/main.py` and the Python package is importable as `app`:

```bash
python -m uvicorn app.main:app --reload --app-dir backend
```

If your entry point or package structure differs, update the command accordingly.

Once the backend starts, open:

- API: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 6. Run the frontend

If the frontend is a Node.js application, open a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Use the local address printed by the frontend development server.

## 🧠 AI Components

The `ai/` directory contains the project's AI-related components.

Depending on the current implementation, these components may support natural-language assistance, information retrieval, or other intelligent functionality.

AI-generated information should be checked against reliable and current official sources, particularly when it concerns government eligibility requirements, documents, deadlines, or application procedures.

## 🔒 Security and Privacy

- Keep credentials and API keys out of source control.
- Use environment variables for sensitive configuration.
- Avoid storing unnecessary personal information.
- Verify information before using it for official applications.

## 🗺️ Future Scope

Potential directions for further development include:

- Multilingual citizen assistance.
- Improved service and scheme search.
- More accessible user interfaces.
- Integration with verified public-service information sources.
- Expanded AI-assisted navigation and guidance.

These are potential enhancements, not a claim that every capability is currently available.

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome.

1. Fork the repository.
2. Create a branch for your changes.
3. Implement and test your changes.
4. Submit a pull request describing the improvement.

## 👩‍💻 Project

**SevaSetu AI** — A project exploring AI-assisted access to government services.

- GitHub repository: [ngupta1035/SevaSetu-AI](https://github.com/ngupta1035/SevaSetu-AI)

---

*Built with the goal of making public-service information more accessible through technology.*
