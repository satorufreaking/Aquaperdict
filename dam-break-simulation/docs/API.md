# API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/scenarios` | Validate and save a scenario |
| POST | `/api/simulation/run` | Run a supplied scenario and return metrics/series |
| GET | `/api/simulation/{id}/status` | Status/progress |
| GET | `/api/simulation/{id}/results` | Results summary |
| GET | `/api/flood/{depth|velocity|arrival|elevation|risk}?simulation_id=` | GeoJSON cells |
| GET | `/api/infrastructure/impact?simulation_id=` | Synthetic asset overlay summary |
| POST | `/api/scenarios/compare` | Compare 2–5 saved IDs |
| POST | `/api/reports/generate?simulation_id=` | Printable HTML assessment brief (save to PDF from browser) |

FastAPI exposes live schemas and request testing at `/docs`. Invalid physical inputs return standard 422 responses with readable validation details.
