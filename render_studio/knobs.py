import re
from dataclasses import dataclass

MATERIALS = {"matte": (0.0, 0.9), "plastic": (0.0, 0.4),
             "metal": (0.9, 0.3), "clay": (0.0, 0.7)}  # (metallic, roughness)
BACKGROUNDS = {"white": (0.9, 0.9, 0.9), "grey": (0.6, 0.6, 0.6),
               "dark": (0.05, 0.05, 0.06), "gradient": (0.6, 0.6, 0.6)}
# camera direction (unit-ish, scaled by model radius at render time)
ANGLES = {"front": (0.0, -1.0, 0.15), "iso": (1.0, -1.0, 0.8),
          "top_front": (0.0, -0.7, 1.2), "back": (0.0, 1.0, 0.3)}
RESOLUTIONS = {1024, 2048}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

@dataclass
class Knobs:
    material: str = "matte"
    color: str = "#9aa0a6"
    background: str = "grey"
    angle: str = "iso"
    resolution: int = 1024

def coerce(data: dict) -> Knobs:
    d = Knobs()
    mat = data.get("material"); d.material = mat if mat in MATERIALS else d.material
    bg = data.get("background"); d.background = bg if bg in BACKGROUNDS else d.background
    ang = data.get("angle"); d.angle = ang if ang in ANGLES else d.angle
    col = data.get("color"); d.color = col if isinstance(col, str) and _HEX.match(col) else d.color
    try:
        res = int(data.get("resolution"))
    except (TypeError, ValueError):
        res = None
    d.resolution = res if res in RESOLUTIONS else d.resolution
    return d
