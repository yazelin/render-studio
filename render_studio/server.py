import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from . import brain, ingest, render, scene
from .knobs import coerce
from .render import DEFAULT_SCRATCH

app = FastAPI()
WEB = Path(__file__).parent / "web"
_state: dict = {"image_path": None}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
# shared handoff with the cad-agent modeling app: it writes its latest STL here
HANDOFF_STL = Path.home() / "3d-pipeline" / "latest.stl"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (WEB / "index.html").read_text()


@app.get("/tools")
def tools() -> dict:
    freecad_cmd = ingest.default_freecad_cmd()
    return {
        "blender": shutil.which("blender") is not None,
        "freecad": bool(freecad_cmd) and shutil.which(freecad_cmd) is not None,
    }


@app.get("/image")
def image() -> FileResponse:
    if not _state["image_path"]:
        raise HTTPException(status_code=404, detail="no render yet")
    return FileResponse(_state["image_path"], media_type="image/png")


@app.get("/handoff")
def handoff() -> dict:
    return {"available": HANDOFF_STL.exists()}


@app.get("/handoff-file")
def handoff_file() -> FileResponse:
    if not HANDOFF_STL.exists():
        raise HTTPException(status_code=404, detail="no cad-agent model yet")
    return FileResponse(HANDOFF_STL, media_type="model/stl", filename="cad-agent.stl")


class StyleReq(BaseModel):
    text: str

@app.post("/style")
def style(req: StyleReq) -> dict:
    raw = brain.nl_to_knobs(req.text)
    k = coerce(raw)
    return {"material": k.material, "color": k.color, "background": k.background,
            "angle": k.angle, "resolution": k.resolution}

class AgentosRenderReq(BaseModel):
    stl_path: str
    material: str = "matte"
    color: str = "#9aa0a6"
    background: str = "grey"
    angle: str = "iso"
    resolution: int = 1024

@app.post("/agentos/render")
async def agentos_render(req: AgentosRenderReq) -> dict:
    src = Path(req.stl_path)
    if not src.exists():
        return {"ok": False, "image_path": None, "error": f"file not found: {req.stl_path}"}
    knobs = coerce({"material": req.material, "color": req.color,
                    "background": req.background, "angle": req.angle,
                    "resolution": req.resolution})
    workdir = render.DEFAULT_SCRATCH / ("agentos-" + uuid.uuid4().hex[:12])
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        mesh = await asyncio.to_thread(ingest.prepare_mesh, src, workdir)
        script = scene.build_bpy(str(mesh), knobs)
    except (ValueError, RuntimeError) as e:
        return {"ok": False, "image_path": None, "error": str(e)}
    result = await asyncio.to_thread(render.run_blender, script, scratch_base=workdir)
    if result.ok and result.image_path:
        return {"ok": True, "image_path": str(result.image_path), "error": None}
    return {"ok": False, "image_path": None, "error": (result.stderr or "render failed")[-500:]}

@app.post("/render")
async def do_render(
    model: UploadFile = File(...),
    material: str = Form("matte"),
    color: str = Form("#9aa0a6"),
    background: str = Form("grey"),
    angle: str = Form("iso"),
    resolution: str = Form("1024"),
) -> dict:
    knobs = coerce(
        {
            "material": material,
            "color": color,
            "background": background,
            "angle": angle,
            "resolution": resolution,
        }
    )
    data = await model.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="file too large (max 50 MB)")
    workdir = DEFAULT_SCRATCH / ("upload-" + uuid.uuid4().hex[:12])
    workdir.mkdir(parents=True, exist_ok=True)
    src = workdir / Path(model.filename or "upload.bin").name
    src.write_bytes(data)
    try:
        mesh = ingest.prepare_mesh(src, workdir)
        script = scene.build_bpy(str(mesh), knobs)
        result = render.run_blender(script)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (FileNotFoundError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"render failed: {e}")
    if not result.ok:
        raise HTTPException(
            status_code=400, detail=(result.stderr or "render failed")[-500:]
        )
    _state["image_path"] = result.image_path
    return {"ok": True, "image": "/image"}
