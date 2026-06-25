from render_studio.knobs import Knobs, coerce

def test_defaults():
    k = coerce({})
    assert k == Knobs(material="matte", color="#9aa0a6", background="grey",
                      angle="iso", resolution=1024)

def test_valid_values_pass_through():
    k = coerce({"material": "metal", "color": "#4488cc", "background": "dark",
                "angle": "front", "resolution": 2048})
    assert k.material == "metal" and k.resolution == 2048

def test_invalid_values_fall_back_to_default():
    k = coerce({"material": "wood", "background": "neon", "angle": "sideways",
                "resolution": 99, "color": "not-a-hex"})
    assert k.material == "matte" and k.background == "grey"
    assert k.angle == "iso" and k.resolution == 1024 and k.color == "#9aa0a6"
