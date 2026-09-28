from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import Scenario, CompareRequest
from .simulation.engine import run, cell_features
from .risk.analysis import impact
from uuid import uuid4

app=FastAPI(title="Dam Break DSS", version="0.1.0")
# Development UI ports vary when 5173 is already occupied. Keep this permissive
# only for the local prototype; production must use an explicit allowed origin.
app.add_middleware(CORSMiddleware,allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
store={}

def summary(s,r):
    i=impact(r)
    return {"scenario":s.model_dump(),"maximum_discharge_m3s":float(r.discharge.max()),"maximum_depth_m":round(float(r.depth.max()),2),"maximum_velocity_mps":round(float(r.velocity.max()),2),"inundated_area_km2":i['inundated_area_km2'],"impact":i,"series":{"discharge":r.discharge.tolist(),"area":r.area.tolist(),"depth":r.maxdepth.tolist(),"velocity":r.maxvelocity.tolist()}}

@app.get('/api/health')
def health(): return {"status":"ok","model":"simplified raster hydraulic screening model"}
@app.post('/api/scenarios')
def create(s:Scenario):
    sid=str(uuid4()); store[sid]={"scenario":s,"status":"created"}; return {"id":sid,"status":"created"}
@app.post('/api/simulation/run')
def simulate(s:Scenario):
    sid=str(uuid4()); r=run(s); store[sid]={"scenario":s,"result":r,"status":"complete"}; return {"id":sid,"status":"complete",**summary(s,r)}
@app.get('/api/simulation/{sid}/status')
def status(sid:str):
    if sid not in store: raise HTTPException(404,'Simulation not found')
    return {"id":sid,"status":store[sid]['status'],"progress":100 if store[sid]['status']=='complete' else 0}
@app.get('/api/simulation/{sid}/results')
def results(sid:str):
    x=store.get(sid)
    if not x or 'result' not in x: raise HTTPException(404,'Completed simulation not found')
    return summary(x['scenario'],x['result'])
@app.get('/api/flood/{layer}')
def layer(layer:str,simulation_id:str):
    x=store.get(simulation_id)
    if not x or 'result' not in x: raise HTTPException(404,'Completed simulation not found')
    if layer not in ['depth','velocity','arrival','elevation','risk']: raise HTTPException(422,'Unsupported layer')
    return cell_features(x['result'],layer)
@app.get('/api/infrastructure/impact')
def infrastructure(simulation_id:str):
    x=store.get(simulation_id)
    if not x or 'result' not in x: raise HTTPException(404,'Completed simulation not found')
    return impact(x['result'])
@app.post('/api/scenarios/compare')
def compare(req:CompareRequest):
    rows=[]
    for sid in req.scenario_ids:
        x=store.get(sid)
        if not x or 'result' not in x: raise HTTPException(404,f'Completed simulation {sid} not found')
        r=summary(x['scenario'],x['result']); rows.append({"id":sid,"name":x['scenario'].name,**{k:r[k] for k in ['maximum_discharge_m3s','maximum_depth_m','maximum_velocity_mps','inundated_area_km2']},"affected_population_demo":r['impact']['affected_population_demo']})
    return {"scenarios":rows}

@app.post('/api/reports/generate', response_class=HTMLResponse)
def report(simulation_id: str):
    """Printable assessment brief; browser print can save PDF without a proprietary PDF engine."""
    x=store.get(simulation_id)
    if not x or 'result' not in x: raise HTTPException(404,'Completed simulation not found')
    r=summary(x['scenario'],x['result']); s=x['scenario']; assets=''.join(f"<li>{a['name']} — {a['type']}, depth {a['depth_m']} m, arrival {a['arrival_min']} min</li>" for a in r['impact']['affected_assets']) or '<li>No demo assets crossed the 0.05 m depth threshold.</li>'
    return f'''<!doctype html><title>Flood Assessment — {s.name}</title><style>body{{font:15px Arial;max-width:850px;margin:35px auto;line-height:1.5}}h1{{color:#093b4b}}.warn{{background:#fff4d6;padding:12px}}</style><h1>Flood Assessment Report</h1><p><b>Study area:</b> Synthetic Suryanagar demonstration basin<br><b>Dam:</b> {s.dam_name}<br><b>River:</b> {s.river_name}<br><b>Scenario:</b> {s.name}</p><h2>Scenario parameters</h2><p>Breach: {s.breach_width_m} m width × {s.breach_depth_m} m depth; formation: {s.breach_formation_min} min; Manning n: {s.manning_n}; duration: {s.duration_min} min.</p><h2>Screening outputs</h2><p>Peak discharge: {r['maximum_discharge_m3s']:.1f} m³/s<br>Maximum depth: {r['maximum_depth_m']} m<br>Maximum velocity: {r['maximum_velocity_mps']} m/s<br>Inundated area: {r['inundated_area_km2']} km²<br>Demo population exposed: {r['impact']['affected_population_demo']}</p><h2>Potentially affected demo assets</h2><ul>{assets}</ul><h2>Method, limitations and data sources</h2><p>Broad-crested release and Manning-limited raster routing on a synthetic DEM. All terrain, settlements, assets and population labels are synthetic. Results are screening estimates only.</p><p class="warn"><b>Prototype limitation:</b> Not a substitute for validated engineering hydraulic modelling or official emergency-management decisions. Human authority and engineering verification are required before any operational action.</p>'''
