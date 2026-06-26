from pathlib import Path
from fastapi.testclient import TestClient
import render_studio.server as srv
from render_studio.server import app
from render_studio.render import RenderResult

def _patch_pipeline(monkeypatch, result):
    monkeypatch.setattr(srv.ingest, "prepare_mesh", lambda src, wd, **k: src)
    monkeypatch.setattr(srv.scene, "build_bpy", lambda mesh, knobs: "BPY")
    monkeypatch.setattr(srv.render, "run_blender", lambda script, **k: result)

def test_agentos_render_success(tmp_path, monkeypatch):
    stl = tmp_path / "in.stl"; stl.write_text("solid x")
    png = tmp_path / "out.png"; png.write_bytes(b"\x89PNG")
    _patch_pipeline(monkeypatch, RenderResult(True, False, "", "", png, tmp_path))
    r = TestClient(app).post("/agentos/render", json={"stl_path": str(stl), "material": "metal"})
    body = r.json()
    assert body["ok"] is True and body["image_path"] == str(png) and body["error"] is None

def test_agentos_render_missing_path_no_500(tmp_path):
    r = TestClient(app).post("/agentos/render", json={"stl_path": str(tmp_path / "nope.stl")})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False and body["image_path"] is None and "not found" in body["error"]

def test_agentos_render_failure(tmp_path, monkeypatch):
    stl = tmp_path / "in.stl"; stl.write_text("solid x")
    _patch_pipeline(monkeypatch, RenderResult(False, False, "", "boom", None, tmp_path))
    r = TestClient(app).post("/agentos/render", json={"stl_path": str(stl)})
    body = r.json()
    assert body["ok"] is False and body["image_path"] is None and "boom" in body["error"]
