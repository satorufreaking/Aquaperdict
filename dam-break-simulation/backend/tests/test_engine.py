from app.models import Scenario
from app.simulation.engine import run

def test_breach_generates_positive_downstream_flood_and_speed():
    r=run(Scenario(duration_min=15, timestep_s=10))
    assert r.depth.max() > 0.5
    assert r.velocity.max() > 0
    assert (r.arrival == r.arrival).sum() > 20 # excludes NaN

def test_larger_breach_has_higher_initial_discharge():
    small=run(Scenario(breach_width_m=10,duration_min=10,timestep_s=10))
    large=run(Scenario(breach_width_m=50,duration_min=10,timestep_s=10))
    assert large.discharge.max() > small.discharge.max()
