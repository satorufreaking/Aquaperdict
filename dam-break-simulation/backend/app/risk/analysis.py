import numpy as np
from ..simulation.engine import CELL

ASSETS=[
 {"name":"Suryanagar","type":"Village","population":1200,"row":12,"col":16},
 {"name":"Kaveripura","type":"Village","population":850,"row":24,"col":23},
 {"name":"District Hospital","type":"Hospital","population":0,"row":19,"col":18},
 {"name":"Government School","type":"School","population":0,"row":29,"col":27},
 {"name":"Relief Shelter","type":"Shelter","population":0,"row":33,"col":29},]

def impact(result):
    affected=[]
    for a in ASSETS:
        depth=float(result.depth[a['row'],a['col']]); velocity=float(result.velocity[a['row'],a['col']])
        if depth>.05: affected.append({**a,"depth_m":round(depth,2),"velocity_mps":round(velocity,2),"arrival_min":None if np.isnan(result.arrival[a['row'],a['col']]) else round(float(result.arrival[a['row'],a['col']]),1)})
    population=sum(a['population'] for a in affected)
    return {"method":"Hazard = depth/velocity; exposure = supplied demo asset locations. Risk = hazard × exposure; thresholds are configurable in a production deployment.","affected_assets":affected,"affected_villages":sum(a['type']=="Village" for a in affected),"affected_population_demo":population,"affected_hospitals":sum(a['type']=="Hospital" for a in affected),"affected_schools":sum(a['type']=="School" for a in affected),"inundated_area_km2":round(float((result.depth>.05).sum()*CELL*CELL/1e6),3)}
