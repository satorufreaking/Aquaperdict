"""A conservative, educational raster-routing dam-break approximation.

This is deliberately not a replacement for HEC-RAS/TELEMAC. A synthetic DEM is
sampled on a square grid; stored water is released through a broad-crested weir
and routed only down local water-surface gradients. A Manning-limited discharge
and a CFL-style transfer cap preserve non-negative cell storage. It provides
repeatable screening indicators (depth, speed, arrival), not design values.
"""
from dataclasses import dataclass
import numpy as np
from ..models import Scenario

G = 9.81
CELL = 120.0  # metres; 40 x 40 grid covers 23.04 km2
N = 40

@dataclass
class Result:
    elevation: np.ndarray; depth: np.ndarray; velocity: np.ndarray; arrival: np.ndarray
    discharge: np.ndarray; area: np.ndarray; maxdepth: np.ndarray; maxvelocity: np.ndarray

def terrain():
    """Deterministic valley DEM: north-west reservoir, incised diagonal river valley."""
    y, x = np.mgrid[0:N, 0:N]
    base = 192 - 1.35*y - .30*x
    valley_center = 9 + .55*y
    valley = 13*np.exp(-((x-valley_center)/3.0)**2)
    undulation = 1.8*np.sin(x*.38)*np.cos(y*.27)
    return base - valley + undulation

def run(s: Scenario) -> Result:
    z = terrain(); h = np.zeros((N,N), float)
    # pre-existing shallow water in the river corridor
    y, x = np.mgrid[0:N, 0:N]; h[np.abs(x-(9+.55*y)) < 1.2] = s.downstream_depth_m
    peak_h = min(s.breach_depth_m, s.reservoir_level_m)
    storage = s.reservoir_volume_m3
    steps = int(s.duration_min*60/s.timestep_s)
    every = max(1, steps//90)
    arrival = np.full((N,N), np.nan); max_h=h.copy(); max_v=np.zeros_like(h)
    q_series=[]; area_series=[]; depth_series=[]; vel_series=[]
    dam = (2, 10)
    for step in range(steps):
        t = step*s.timestep_s
        # broad-crested/weir release, ramped during breach formation
        ramp = min(1., t/(s.breach_formation_min*60))
        head = peak_h * max(0.15, storage/s.reservoir_volume_m3)
        q = min(storage/s.timestep_s, 0.62*s.breach_width_m*(head**1.5)*ramp)
        vol = q*s.timestep_s; h[dam] += vol/(CELL*CELL); storage -= vol
        surface = z+h
        transfers = np.zeros_like(h); vfield=np.zeros_like(h)
        # Four-direction finite-volume routing; only positive surface gradients.
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            src=(slice(max(0,-dy), min(N,N-dy)), slice(max(0,-dx), min(N,N-dx)))
            dst=(slice(max(0,dy), min(N,N+dy)), slice(max(0,dx), min(N,N+dx)))
            slope=np.maximum(0, (surface[src]-surface[dst])/CELL)
            hs=h[src]
            # Manning velocity v=(1/n) R^(2/3) S^(1/2), wide-channel R~h
            v=np.where(hs>.001, (1/s.manning_n)*np.maximum(hs,.001)**(2/3)*np.sqrt(slope), 0)
            flux=np.minimum(hs*0.20, v*hs*s.timestep_s/CELL/4) # capped so four faces cannot drain a cell
            transfers[src] -= flux; transfers[dst] += flux
            vfield[src]=np.maximum(vfield[src], v)
        h=np.maximum(0, h+transfers)
        wet=h>0.05
        arrival[np.isnan(arrival)&wet]=t/60
        max_h=np.maximum(max_h,h); max_v=np.maximum(max_v,vfield)
        if step % every == 0 or step == steps-1:
            q_series.append(round(q,2)); area_series.append(round(float(wet.sum()*CELL*CELL/1e6),3))
            depth_series.append(round(float(max_h.max()),2)); vel_series.append(round(float(max_v.max()),2))
    return Result(z,max_h,max_v,arrival,np.array(q_series),np.array(area_series),np.array(depth_series),np.array(vel_series))

def cell_features(result: Result, layer: str):
    """Return grid cells as GeoJSON WGS84-like demo coordinates; swap adapter for real CRS data."""
    prop = {"depth":result.depth,"velocity":result.velocity,"arrival":result.arrival,"elevation":result.elevation}.get(layer,result.depth)
    features=[]; origin_lon,origin_lat=77.35,12.45; d=.008
    for r in range(N):
        for c in range(N):
            val=float(prop[r,c]) if not np.isnan(prop[r,c]) else None
            flooded=result.depth[r,c]>.05
            if layer != "elevation" and not flooded: continue
            lon=origin_lon+c*d; lat=origin_lat-r*d
            risk="Very High" if result.depth[r,c]>2 or result.velocity[r,c]>2.5 else "High" if result.depth[r,c]>1 else "Moderate" if flooded else "Low"
            features.append({"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[lon,lat],[lon+d,lat],[lon+d,lat-d],[lon,lat-d],[lon,lat]]]},"properties":{"value":val,"depth":round(float(result.depth[r,c]),2),"velocity":round(float(result.velocity[r,c]),2),"arrival_min":None if np.isnan(result.arrival[r,c]) else round(float(result.arrival[r,c]),1),"elevation":round(float(result.elevation[r,c]),1),"risk":risk}})
    return {"type":"FeatureCollection","features":features}
