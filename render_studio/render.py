import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCRATCH = Path(
    os.environ.get("RENDER_STUDIO_SCRATCH", str(Path.home() / "render-studio-scratch"))
)
SAFE_ENV_KEYS = {"PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "DISPLAY", "TMPDIR",
                 "XDG_RUNTIME_DIR"}

@dataclass
class RenderResult:
    ok: bool
    timed_out: bool
    stdout: str
    stderr: str
    image_path: Path | None
    workdir: Path

def default_blender_cmd() -> list[str]:
    binary = os.environ.get("RENDER_STUDIO_BLENDER", "blender")
    return [binary, "--background", "--factory-startup", "--python"]

def _scrubbed_env() -> dict:
    return {k: v for k, v in os.environ.items() if k in SAFE_ENV_KEYS}

def run_blender(script: str, *, timeout: float = 180.0,
                cmd: list[str] | None = None,
                scratch_base: Path | None = None) -> RenderResult:
    base = scratch_base or DEFAULT_SCRATCH
    workdir = base / uuid.uuid4().hex[:12]
    workdir.mkdir(parents=True, exist_ok=True)
    script_path = workdir / "scene.py"
    script_path.write_text(script)
    run_cmd = (cmd or default_blender_cmd()) + [str(script_path)]
    try:
        proc = subprocess.run(run_cmd, cwd=workdir, env=_scrubbed_env(),
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return RenderResult(False, True, e.stdout or "", e.stderr or "", None, workdir)
    img = workdir / "out.png"
    ok = proc.returncode == 0 and img.exists()
    return RenderResult(ok, False, proc.stdout, proc.stderr,
                        img if img.exists() else None, workdir)
