import os
import shutil
import subprocess
from pathlib import Path

MESH_EXTS = {".stl", ".obj", ".ply", ".gltf", ".glb"}
CAD_EXTS = {".step", ".stp", ".iges", ".igs"}
FREECAD_CANDIDATES = ("freecadcmd", "freecad.cmd", "FreeCADCmd")

def default_freecad_cmd() -> str:
    override = os.environ.get("RENDER_STUDIO_FREECAD")
    if override:
        return override
    for c in FREECAD_CANDIDATES:
        if shutil.which(c):
            return c
    return "freecadcmd"

_CONVERT_TEMPLATE = """import Part
shape = Part.Shape()
shape.read({src!r})
shape.exportStl({dst!r})
"""

def prepare_mesh(src: Path, workdir: Path, *,
                 convert_cmd: list[str] | None = None) -> Path:
    ext = src.suffix.lower()
    if ext in MESH_EXTS:
        return src
    if ext not in CAD_EXTS:
        raise ValueError(f"unsupported extension: {ext}")
    dst = workdir / "converted.stl"
    script = workdir / "_convert.py"
    script.write_text(_CONVERT_TEMPLATE.format(src=str(src), dst=str(dst)))
    cmd = (convert_cmd or [default_freecad_cmd()]) + [str(script)]
    subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=120)
    if not dst.exists():
        raise RuntimeError("STEP/IGES conversion produced no mesh (FreeCAD missing or failed)")
    return dst
