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


class StyleReq(BaseModel):
    text: str

@app.post("/style")
def style(req: StyleReq) -> dict:
    raw = brain.nl_to_knobs(req.text)
    k = coerce(raw)
    return {"material": k.material, "color": k.color, "background": k.background,
            "angle": k.angle, "resolution": k.resolution}

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
    workdir = DEFAULT_SCRATCH / ("upload-" + uuid.uuid4().hex[:12])
    workdir.mkdir(parents=True, exist_ok=True)
    src = workdir / Path(model.filename).name
    src.write_bytes(await model.read())
    try:
        mesh = ingest.prepare_mesh(src, workdir)
        script = scene.build_bpy(str(mesh), knobs)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = render.run_blender(script)
    if not result.ok:
        raise HTTPException(
            status_code=400, detail=(result.stderr or "render failed")[-500:]
        )
    _state["image_path"] = result.image_path
    return {"ok": True, "image": "/image"}
