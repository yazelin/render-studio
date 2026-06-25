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

def test_style_maps_nl(monkeypatch):
    monkeypatch.setattr(srv.brain, "nl_to_knobs",
                        lambda text: {"material": "metal", "background": "dark"})
    r = TestClient(app).post("/style", json={"text": "industrial metal dark"})
    assert r.json()["material"] == "metal" and r.json()["background"] == "dark"

def test_render_blender_error_returns_400(tmp_path, monkeypatch):
    # I2: run_blender raising FileNotFoundError must return 400, not 500
    monkeypatch.setattr(srv.ingest, "prepare_mesh", lambda src, wd, **k: src)
    monkeypatch.setattr(srv.scene, "build_bpy", lambda mesh, knobs: "SCRIPT")
    monkeypatch.setattr(srv.render, "run_blender",
        lambda script, **k: (_ for _ in ()).throw(FileNotFoundError("blender not found")))
    r = TestClient(app).post("/render",
        files={"model": ("a.stl", io.BytesIO(b"solid x"), "application/octet-stream")},
        data={"material": "metal"})
    assert r.status_code == 400

def test_render_file_too_large_returns_400(monkeypatch):
    # I3: file exceeding MAX_UPLOAD_BYTES must return 400
    monkeypatch.setattr(srv, "MAX_UPLOAD_BYTES", 4)
    r = TestClient(app).post("/render",
        files={"model": ("a.stl", io.BytesIO(b"1234567"), "application/octet-stream")},
        data={"material": "metal"})
    assert r.status_code == 400
    assert "too large" in r.json()["detail"]


def test_handoff_status_and_file(tmp_path, monkeypatch):
    h = tmp_path / "latest.stl"
    monkeypatch.setattr(srv, "HANDOFF_STL", h)
    c = TestClient(app)
    assert c.get("/handoff").json() == {"available": False}
    assert c.get("/handoff-file").status_code == 404
    h.write_text("solid x")
    assert c.get("/handoff").json() == {"available": True}
    r = c.get("/handoff-file")
    assert r.status_code == 200 and r.content == b"solid x"
