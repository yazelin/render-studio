import sys
from render_studio.render import run_blender

# fake "blender": a python one-liner that writes out.png in cwd
FAKE = [sys.executable, "-c", "open('out.png','wb').write(b'\\x89PNG fake')"]

def test_collects_image(tmp_path):
    r = run_blender("print(1)", cmd=FAKE, scratch_base=tmp_path)
    assert r.ok and r.image_path and r.image_path.read_bytes().startswith(b"\x89PNG")

def test_timeout(tmp_path):
    slow = [sys.executable, "-c", "import time; time.sleep(5)"]
    r = run_blender("x", cmd=slow, timeout=0.5, scratch_base=tmp_path)
    assert r.timed_out and not r.ok

def test_failure_when_no_image(tmp_path):
    noop = [sys.executable, "-c", "pass"]
    r = run_blender("x", cmd=noop, scratch_base=tmp_path)
    assert not r.ok and r.image_path is None
