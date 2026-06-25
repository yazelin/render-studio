import shutil
import struct
import tempfile
import zlib
from pathlib import Path

import pytest

from render_studio import scene, render
from render_studio.knobs import Knobs

pytestmark = pytest.mark.skipif(shutil.which("blender") is None,
                                reason="blender not installed")


def _make_cube_stl(path: Path) -> None:
    # minimal ascii STL: a single triangle is enough to import and render
    path.write_text(
        "solid c\n"
        "facet normal 0 0 1\n"
        "outer loop\n"
        "vertex 0 0 0\n"
        "vertex 10 0 0\n"
        "vertex 0 10 0\n"
        "endloop\n"
        "endfacet\n"
        "endsolid c\n"
    )


def _png_is_non_uniform(path: Path) -> bool:
    # decode the PNG far enough to confirm the pixels are not all one color
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    idat = b""
    i = 8
    while i < len(data):
        ln = struct.unpack(">I", data[i:i + 4])[0]
        ctype = data[i + 4:i + 8]
        if ctype == b"IDAT":
            idat += data[i + 8:i + 8 + ln]
        i += 12 + ln
    raw = zlib.decompress(idat)
    return len(set(raw[:4096])) > 4  # many distinct byte values => real content


def test_render_a_real_mesh_end_to_end():
    # snap Blender cannot read /tmp; use a non-hidden dir under $HOME
    home_scratch = Path(tempfile.mkdtemp(prefix="render-studio-test-", dir=Path.home()))
    try:
        stl = home_scratch / "cube.stl"
        _make_cube_stl(stl)
        script = scene.build_bpy(str(stl), Knobs(material="metal", angle="iso"))
        result = render.run_blender(script, scratch_base=home_scratch, timeout=240)
        assert result.ok, f"render failed: {result.stderr[-800:]}"
        assert result.image_path and result.image_path.stat().st_size > 0
        assert _png_is_non_uniform(result.image_path), "render looks blank/uniform"
    finally:
        shutil.rmtree(home_scratch, ignore_errors=True)
