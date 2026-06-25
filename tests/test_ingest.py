import sys
import pytest
from pathlib import Path
from render_studio.ingest import prepare_mesh

def test_mesh_passthrough(tmp_path):
    src = tmp_path / "a.stl"; src.write_text("solid x")
    assert prepare_mesh(src, tmp_path) == src

def test_unsupported_raises(tmp_path):
    src = tmp_path / "a.3mf"; src.write_text("x")
    with pytest.raises(ValueError):
        prepare_mesh(src, tmp_path)

def test_step_conversion_uses_freecad(tmp_path):
    src = tmp_path / "a.step"; src.write_text("ISO-10303")
    # fake freecad: a python that writes converted.stl into cwd's workdir arg
    # convert_cmd receives the generated freecad script path appended; emulate by
    # writing the expected output file directly.
    fake = [sys.executable, "-c",
            "import sys,os; open(os.path.join(os.path.dirname(sys.argv[-1]),'converted.stl'),'w').write('solid s')"]
    out = prepare_mesh(src, tmp_path, convert_cmd=fake)
    assert out == tmp_path / "converted.stl" and out.read_text().startswith("solid")

def test_step_conversion_failure_raises(tmp_path):
    src = tmp_path / "a.step"; src.write_text("x")
    noop = [sys.executable, "-c", "pass"]
    with pytest.raises(RuntimeError):
        prepare_mesh(src, tmp_path, convert_cmd=noop)
