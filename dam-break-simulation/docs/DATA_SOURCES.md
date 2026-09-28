# Data sources and demo data

The current data are generated in code and are entirely synthetic: terrain is a deterministic mathematical valley; dam, river, villages, road context, population labels and critical assets are fictional demonstration content. It works with no network access and must not be represented as a real location or impact estimate.

For a study-area deployment, provide a documented DEM (GeoTIFF with valid projected CRS), surveyed dam/breach information, channel and roughness data, boundaries, official infrastructure and population datasets. Verify licensing, CRS, vertical datum, date, resolution and completeness before use. An ingestion adapter for GeoTIFF/GeoJSON is the intended next phase; it must reject missing/invalid CRS and dimensions.
