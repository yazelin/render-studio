import json
import re
import subprocess
import tempfile

STYLE_SYSTEM_PROMPT = """You map a product-render style description to knob values.
Reply with ONLY a JSON object (no prose, no fences). Keys (all optional):
  material: one of matte, plastic, metal, clay
  color:    a #rrggbb hex
  background: one of white, grey, dark, gradient
  angle:    one of front, iso, top_front, back
  resolution: 1024 or 2048
Omit any key you are unsure about."""

DEFAULT_CLAUDE_CMD = [
    "claude", "-p",
    "--disallowed-tools", "Write", "Edit", "MultiEdit", "NotebookEdit", "Bash",
]
_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)

def build_prompt(text: str) -> str:
    return STYLE_SYSTEM_PROMPT + "\n\nStyle: " + text

def parse_knobs(stdout: str) -> dict:
    m = _JSON_RE.search(stdout)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}

def nl_to_knobs(text: str, *, claude_cmd: list[str] | None = None,
                timeout: float = 60) -> dict:
    prompt = build_prompt(text)
    cmd = claude_cmd or DEFAULT_CLAUDE_CMD
    with tempfile.TemporaryDirectory(prefix="render-studio-brain-") as cwd:
        proc = subprocess.run(cmd, input=prompt, cwd=cwd, capture_output=True,
                              text=True, timeout=timeout)
    return parse_knobs(proc.stdout)
