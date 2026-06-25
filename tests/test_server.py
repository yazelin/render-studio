import io
import render_studio.server as srv
from render_studio.render import RenderResult
from fastapi.testclient import TestClient
from render_studio.server import app

def test_index_serves_html():
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert "render-studio" in r.text

def test_render_success(tmp_path, monkeypatch):
    png = tmp_path / "out.png"; png.write_bytes(b"\x89PNG real")
    monkeypatch.setattr(srv.ingest, "prepare_mesh", lambda src, wd, **k: src)
    monkeypatch.setattr(srv.scene, "build_bpy", lambda mesh, knobs: "SCRIPT")
    monkeypatch.setattr(srv.render, "run_blender",
        lambda script, **k: RenderResult(True, False, "", "", png, tmp_path))
    srv._state["image_path"] = None
    r = TestClient(app).post("/render",
        files={"model": ("a.stl", io.BytesIO(b"solid x"), "application/octet-stream")},
        data={"material": "metal"})
    assert r.json() == {"ok": True, "image": "/image"}
    assert srv._state["image_path"] == png

def test_image_404_before_render(monkeypatch):
    srv._state["image_path"] = None
    assert TestClient(app).get("/image").status_code == 404
