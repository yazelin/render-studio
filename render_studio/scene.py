from pathlib import Path
from .knobs import Knobs, MATERIALS, BACKGROUNDS, ANGLES

IMPORT_OPS = {
    ".stl": "bpy.ops.wm.stl_import(filepath={path!r})",
    ".obj": "bpy.ops.wm.obj_import(filepath={path!r})",
    ".ply": "bpy.ops.wm.ply_import(filepath={path!r})",
    ".gltf": "bpy.ops.import_scene.gltf(filepath={path!r})",
    ".glb": "bpy.ops.import_scene.gltf(filepath={path!r})",
}

def _hex_to_rgb(h: str) -> tuple:
    return tuple(round(int(h[i:i+2], 16) / 255.0, 3) for i in (1, 3, 5))

def build_bpy(mesh_path: str, knobs: Knobs) -> str:
    ext = Path(mesh_path).suffix.lower()
    if ext not in IMPORT_OPS:
        raise ValueError(f"unsupported extension: {ext}")
    import_call = IMPORT_OPS[ext].format(path=mesh_path)
    metallic, roughness = MATERIALS[knobs.material]
    r, g, b = _hex_to_rgb(knobs.color)
    bg = BACKGROUNDS[knobs.background]
    cam_dir = ANGLES[knobs.angle]
    return f'''import bpy, mathutils

# ---- clean factory scene ----
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---- import subject ----
before = set(bpy.data.objects)
{import_call}
imported = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
assert imported, "import produced no mesh"

# ---- combined bounding box (world space) ----
import math
mins = [1e18, 1e18, 1e18]; maxs = [-1e18, -1e18, -1e18]
for o in imported:
    for corner in o.bound_box:
        wc = o.matrix_world @ mathutils.Vector(corner)
        for i in range(3):
            mins[i] = min(mins[i], wc[i]); maxs[i] = max(maxs[i], wc[i])
center = mathutils.Vector([(mins[i] + maxs[i]) / 2.0 for i in range(3)])
radius = max((maxs[i] - mins[i]) for i in range(3)) / 2.0 or 1.0

# ---- material ----
mat = bpy.data.materials.new("studio"); mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = ({r}, {g}, {b}, 1.0)
bsdf.inputs["Metallic"].default_value = {metallic}
bsdf.inputs["Roughness"].default_value = {roughness}
for o in imported:
    o.data.materials.clear(); o.data.materials.append(mat)

# ---- floor at bottom of subject (shadow catcher) ----
bpy.ops.mesh.primitive_plane_add(size=radius * 20, location=(center.x, center.y, mins[2]))
floor = bpy.context.active_object
floor.is_shadow_catcher = True

# ---- 3-point area lights, scaled to subject ----
def area(name, offset, energy):
    l = bpy.data.lights.new(name, "AREA"); l.size = radius * 4
    l.energy = energy * (radius ** 2)
    ob = bpy.data.objects.new(name, l)
    ob.location = center + mathutils.Vector(offset) * radius
    bpy.context.collection.objects.link(ob)
area("key", (4, -4, 6), 60); area("fill", (-5, -2, 3), 20); area("rim", (0, 5, 4), 30)

# ---- camera framing the subject ----
CAM_DIR = {cam_dir}
cam_data = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = center + mathutils.Vector(CAM_DIR).normalized() * radius * 3.2
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- world background ----
world = bpy.data.worlds.new("w"); bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = ({bg[0]}, {bg[1]}, {bg[2]}, 1.0)

# ---- render EEVEE ----
sc = bpy.context.scene
engs = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engs else "BLENDER_EEVEE"
sc.render.film_transparent = False
sc.render.resolution_x = {knobs.resolution}
sc.render.resolution_y = {knobs.resolution}
# absolute path: Blender resolves a bare relative filepath against the .blend
# location (unsaved here), which fails; cwd is the per-run scratch dir.
sc.render.filepath = __import__("os").path.abspath("out.png")
bpy.ops.render.render(write_still=True)
'''
