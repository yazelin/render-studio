import pytest
from render_studio.knobs import Knobs
from render_studio import scene

def test_unsupported_extension_raises():
    with pytest.raises(ValueError):
        scene.build_bpy("/x/model.3mf", Knobs())

def test_stl_uses_stl_importer():
    s = scene.build_bpy("/tmp/a.stl", Knobs())
    assert "bpy.ops.wm.stl_import" in s
    assert "/tmp/a.stl" in s

def test_obj_and_gltf_importers():
    assert "bpy.ops.wm.obj_import" in scene.build_bpy("/tmp/a.obj", Knobs())
    assert "bpy.ops.import_scene.gltf" in scene.build_bpy("/tmp/a.glb", Knobs())

def test_knobs_drive_engine_resolution_material():
    s = scene.build_bpy("/tmp/a.stl", Knobs(material="metal", resolution=2048,
                                            color="#4488cc"))
    assert "BLENDER_EEVEE" in s
    assert "2048" in s
    assert "0.9" in s          # metal metallic
    # hex color converted to 0..1 floats; red channel 0x44/255 ~= 0.267
    assert "0.267" in s

def test_camera_direction_from_angle():
    s = scene.build_bpy("/tmp/a.stl", Knobs(angle="front"))
    assert "CAM_DIR = (0.0, -1.0, 0.15)" in s
