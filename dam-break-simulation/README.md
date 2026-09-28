# Dam Break Inundation Modelling & Emergency Decision Support

An offline-first Smart India Hackathon prototype for screening downstream dam-break inundation. It couples a React/Leaflet GIS dashboard with a FastAPI numerical service and immediately runs against a deterministic synthetic basin. It is intentionally a **decision-support prototype**, not an engineering-certified hydraulic model.

## What works now

- Configurable dam, reservoir, breach, roughness, duration and time-step inputs with server validation.
- A repeatable raster flood calculation returning depth, velocity, estimated arrival time and flood extent.
- Map layers, click-to-inspect cell values, risk/exposure overlay, KPI cards and hydrograph.
- Synthetic villages, hospital, school and shelter (explicitly marked demo data); no population is presented as real.
- Saved scenario API, comparison API, report-print view, automated physics-sanity tests and OpenAPI documentation at `/docs`.

## Quick start

Prerequisites: Python 3.11+ and Node 20+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite address (normally `http://localhost:5173`), retain the defaults and select **Run simulation**. To test the backend: `cd backend; pytest`.

## Model and limitations

The breach discharge is a broad-crested/weir screening relation, `Q = 0.62 B h^(3/2)`, smoothly ramped by breach formation time. Water storage enters a 120 m raster and moves down water-surface gradients using a Manning-limited velocity, with per-step transfer caps to keep storage non-negative. Output is maximum-over-time depth and velocity plus first wetting time.

The current solver has no calibrated boundaries, rainfall, structures, sediment, sub-grid channels, CRS-aware real DEM ingestion, or formal benchmark validation. Therefore it must never determine engineering design, warnings, evacuations or official incident actions. Replace the adapter with a calibrated HEC-RAS 2D, TELEMAC or LISFLOOD-FP workflow for operational use.

See [architecture](docs/ARCHITECTURE.md), [methodology](docs/MODEL_METHODOLOGY.md), [API](docs/API.md), and [data notes](docs/DATA_SOURCES.md).
