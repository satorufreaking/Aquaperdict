from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_run_then_fetch_depth_layer():
    response = client.post('/api/simulation/run', json={"duration_min": 10, "timestep_s": 10})
    assert response.status_code == 200
    payload = response.json()
    assert payload['maximum_discharge_m3s'] > 0
    layer = client.get(f"/api/flood/depth?simulation_id={payload['id']}")
    assert layer.status_code == 200
    assert len(layer.json()['features']) > 0

def test_rejects_invalid_breach_depth():
    response = client.post('/api/simulation/run', json={"dam_height_m": 10, "breach_depth_m": 20})
    assert response.status_code == 422
