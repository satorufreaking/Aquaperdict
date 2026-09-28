# Architecture

```
React + Leaflet dashboard → FastAPI API → scenario validation
                                      ↓
                         independent raster simulation engine
                                      ↓
                  GeoJSON layer adapter + risk/exposure analysis
                                      ↓
                         map, KPIs, chart and report print view
```

`backend/app/simulation/engine.py` has no web dependencies, so it is the replacement seam for a HEC-RAS/TELEMAC/LISFLOOD-FP adapter. A future job queue should execute long solver jobs and persist rasters in PostGIS/object storage; this prototype completes the small synthetic grid synchronously.
