from fastapi.testclient import TestClient
from render_studio.server import app

def test_index_serves_html():
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert "render-studio" in r.text
