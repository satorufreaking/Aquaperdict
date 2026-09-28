# Hydrodynamic methodology

The demo begins with a deterministic 40×40 synthetic valley DEM (120 m cells) and a shallow downstream channel. At each time step, reservoir storage is released at the dam cell with a breach-width and hydraulic-head relation. Breach capacity rises linearly through the supplied formation time.

For each cardinal neighbour, the model derives a positive water-surface slope and applies Manning's wide-channel approximation `v=(1/n)h^(2/3)S^(1/2)`. A capped finite-volume transfer routes water down-gradient. The cap is a numerical stability/non-negativity guard, not a physical calibration. First time with depth > 0.05 m is recorded as estimated arrival.

Risk is transparent: depth and velocity indicate hazard; only supplied asset points form exposure. “Low / Moderate / High / Very High” labels are screening categories and should be reviewed/configured for a governing authority.

Validation status: unit tests check positive release, propagation and the expected increase in peak discharge from a wider breach. No real event or analytical benchmark accuracy claim is made.
