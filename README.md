# render-studio

Upload a 3D file, pick a few studio knobs (or describe a style in words), and
Blender EEVEE renders a studio product image. Standalone — point it at any mesh
or STEP file, not just one source.

This is the rendering stage of a two-tool pipeline: a CAD tool builds the part
(see the companion modeling app), and **render-studio turns it into a product
shot**. They are independent; use either alone.

## How it works

```
browser (upload + knob controls + style box + result image)
  | localhost
FastAPI backend
  |- ingest: STL/OBJ/PLY/glTF/GLB pass through; STEP/IGES -> freecad.cmd converts to STL
  |- brain (optional): claude -p maps a style phrase -> knob values
  |- scene:  a curated studio template + knobs -> a Blender bpy script
  |          (auto-frames the camera to the model, 3-point lighting, floor, material)
  |- render: blender --background --python <script>  (sandboxed) -> out.png (EEVEE)
browser shows the rendered image
```

The studio scene is a fixed, well-lit template; the knobs only adjust it, so
renders are consistently presentable rather than depending on AI to light a
scene.

## Knobs

- material: matte / plastic / metal / clay
- color: any hex
- background: white / grey / dark / gradient
- angle: front / iso / top_front / back
- resolution: 1024 / 2048

The optional "style in words" box (e.g. "brushed aluminium, dark background")
asks `claude` to fill the knobs for you.

## Requirements

- Python 3.11+
- [Blender](https://www.blender.org/) on `PATH` (renders via `blender --background`; EEVEE)
- Optional: [FreeCAD](https://www.freecad.org/) (`freecadcmd`/`freecad.cmd`) — only needed to render STEP/IGES
- Optional: the [`claude`](https://docs.claude.com/en/docs/claude-code) CLI — only for the "style in words" feature

## Install

```bash
git clone <this-repo> render-studio && cd render-studio
python -m venv .venv && . .venv/bin/activate   # or: uv venv && . .venv/bin/activate
pip install -e ".[dev]"                          # or: uv pip install -e ".[dev]"
```

## Run

```bash
python -m render_studio
# open http://127.0.0.1:8098, upload a 3D file, pick knobs, click render
```

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `RENDER_STUDIO_BLENDER` | `blender` | Force the Blender binary name/path |
| `RENDER_STUDIO_FREECAD` | auto-detect | Force the FreeCAD binary (STEP conversion) |
| `RENDER_STUDIO_SCRATCH` | `~/render-studio-scratch` | Where uploads render and the PNG lands |

The default scratch is a non-hidden directory under `$HOME` on purpose: a snap
Blender/FreeCAD has a private `/tmp` and its sandbox cannot read dotfiles, so
neither `/tmp` nor a `~/.dotdir` scratch would be visible to the renderer.

## Safety

The render runs generated Blender Python, so it is sandboxed lightly for
personal single-user use: a per-run scratch dir as the working dir, a timeout, a
scrubbed environment (secrets are not passed to the Blender/FreeCAD subprocess),
and a 50 MB upload cap. The optional `claude -p` brain runs with file/shell tools
disabled and in a throwaway directory. For multi-user or untrusted use, tighten
this with bubblewrap. Per-run scratch dirs accumulate under
`~/render-studio-scratch`; prune it periodically.

## Tests

```bash
pytest            # unit tests run anywhere; the real Blender end-to-end
                  # acceptance test auto-skips when Blender is absent
```

## License

MIT (c) 林亞澤
