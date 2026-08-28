"""Generate varied, clothed, seated humans for the audience front rows.

    ~/tools/blender/blender --background --python tools/generate_humans.py -- <out_dir> [count]

Requires Blender 4.5 + the MPFB extension, plus the CC0 "MakeHuman system
assets" pack extracted into MPFB's user data dir (see PROJECT.md, Tooling).

Licences, settled at the source:
- The MakeHuman base mesh was "explicitly released as CC0 in september 2020"
  - stated in the header of MPFB's own data/3dobjs/base.obj.
- The system assets pack is distributed as makehuman_system_assets_cc0.zip,
  every asset in it listed CC0 on its page.
- MPFB itself is GPL, which covers the tool, not its output.

Hard-won facts baked in below, each found by rendering, not reading:
- Rig FIRST, clothes after, with set_up_rigging=True - clothes added before
  the rig never follow the pose, and render as jeans standing beside a
  seated pair of legs.
- Shape keys must be collapsed (apply_mix) before any modifier can be
  applied; the macro system leaves dozens of them.
- export_apply removes MPFB's helper scaffolding; export_morph=False is the
  difference between ~1 MB and ~17 MB.
- The seated arm pose that reads as "audience" is upperarm z=?70 with a 45?
  elbow: hands folded in the lap. Arms swept forward or raised read as
  zombies or surrender.
- The hips KEEP their standing height through the pose bake - the thighs
  rotate away from them - so the figure "sits in the air" with its feet
  dangling well above y=0. Scene placement must go by measured seat-contact
  height per figure, not by feet.
"""
import math
import os
import sys
import traceback

import bpy

DATA = os.path.expanduser(
    "~/.config/blender/4.5/extensions/.user/user_default/mpfb/data")

# hands folded in the lap - candidate B of the rendered arm sweep
# Hands folded in the lap, thighs horizontal, shins vertical - candidate B
# of the rendered arm sweep. Splitting the leg bend across upperleg01+02
# was tried to spare the garment fit and made it worse: the silhouette
# stopped reading as seated and became a splay. One joint, full angle.
POSE = {
    "upperleg01.L": (-88, 0, -6), "upperleg01.R": (-88, 0, 6),
    "lowerleg01.L": (86, 0, 0),   "lowerleg01.R": (86, 0, 0),
    "upperarm01.L": (0, 0, -70),  "upperarm01.R": (0, 0, 70),
    "lowerarm01.L": (45, 0, 0),   "lowerarm01.R": (45, 0, 0),
    "spine03": (6, 0, 0), "spine02": (4, 0, 0),
}

MALE_SUITS = ["male_casualsuit01", "male_casualsuit02", "male_casualsuit03",
              "male_casualsuit04", "male_casualsuit05", "male_casualsuit06"]
FEMALE_SUITS = ["female_casualsuit01", "female_casualsuit02",
                "female_elegantsuit01"]
HAIR = ["short01", "short02", "short03", "short04", "bob01", "bob02",
        "long01", "ponytail01", "afro01"]
SHOES = ["shoes01", "shoes02", "shoes03", "shoes05", "shoes06"]


def rad(d):
    return d * math.pi / 180


def hash01(i, salt):
    x = math.sin(i * 127.1 + salt * 311.7) * 43758.5453
    return x - math.floor(x)


def macro_for(i):
    return {
        "gender": 0.15 + 0.7 * ((i % 2) + hash01(i, 1) * 0.6 - 0.3),
        "age": 0.3 + hash01(i, 2) * 0.5,
        "muscle": 0.35 + hash01(i, 3) * 0.3,
        "weight": 0.35 + hash01(i, 4) * 0.35,
        "proportions": 0.4 + hash01(i, 5) * 0.2,
        "height": 0.35 + hash01(i, 6) * 0.3,
        "cupsize": 0.4 + hash01(i, 7) * 0.2,
        "firmness": 0.5,
        "race": {"asian": hash01(i, 8), "caucasian": hash01(i, 9),
                 "african": hash01(i, 10)},
    }


def clothe(HumanService, mesh, i, male):
    suit = (MALE_SUITS if male else FEMALE_SUITS)[
        int(hash01(i, 12) * 10) % len(MALE_SUITS if male else FEMALE_SUITS)]
    hair = HAIR[int(hash01(i, 13) * 10) % len(HAIR)]
    shoe = SHOES[int(hash01(i, 14) * 10) % len(SHOES)]
    for kind, name in (("Clothes", "clothes/%s/%s.mhclo" % (suit, suit)),
                       ("Hair", "hair/%s/%s.mhclo" % (hair, hair)),
                       ("Clothes", "clothes/%s/%s.mhclo" % (shoe, shoe))):
        path = os.path.join(DATA, name)
        if os.path.exists(path):
            HumanService.add_mhclo_asset(path, mesh, asset_type=kind,
                                         set_up_rigging=True,
                                         interpolate_weights=True)


def bake_pose(arm):
    """Make the seated pose the REST pose, keeping the armature live.

    The figure ships as a skinned mesh with its skeleton intact, so the
    scene can rotate neck bones and the mesh deforms continuously. The
    earlier approach - bake the pose flat, then cut the head off as a
    separate object - left an open hole at the neck that showed as white
    shrapnel, and swung a rigid head off the shoulders when it turned.
    """
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for name, (x, y, z) in POSE.items():
        pb = arm.pose.bones.get(name)
        if pb:
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (rad(x), rad(y), rad(z))
    bpy.ops.object.mode_set(mode="OBJECT")

    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        if o.data.shape_keys:
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        for m in list(o.modifiers):
            if m.type == "SUBSURF":
                o.modifiers.remove(m)              # never ship subdivision
            elif m.type == "MASK":
                try:
                    bpy.ops.object.modifier_apply(modifier=m.name)
                except Exception:
                    pass
        # Bake the pose into the vertices via a COPY of the armature
        # modifier, so the original stays behind to keep driving the mesh
        # once the pose becomes the rest pose.
        arms = [m for m in o.modifiers if m.type == "ARMATURE"]
        if arms:
            bpy.ops.object.modifier_copy(modifier=arms[0].name)
            dup = [m for m in o.modifiers if m.type == "ARMATURE"][-1]
            try:
                bpy.ops.object.modifier_apply(modifier=dup.name)
            except Exception:
                pass

    # current pose becomes rest: every bone back to identity, mesh unchanged
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.armature_apply()
    bpy.ops.object.mode_set(mode="OBJECT")


def decimate(obj, ratio):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier="dec")


def generate(out_dir, count):
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    os.makedirs(out_dir, exist_ok=True)

    for i in range(count):
        bpy.ops.wm.read_homefile(use_empty=True)
        macros = macro_for(i)
        mesh = HumanService.create_human(macro_detail_dict=macros)
        HumanService.add_builtin_rig(mesh, "default", import_weights=True)
        arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]

        clothe(HumanService, mesh, i, macros["gender"] > 0.5)
        bake_pose(arm)

        # skin material for the body mesh (clothes keep their own)
        tone = 0.3 + hash01(i, 11) * 0.5
        mat = bpy.data.materials.new("skin")
        mat.use_nodes = True
        b = mat.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (tone, tone * 0.72,
                                                tone * 0.55, 1)
        b.inputs["Roughness"].default_value = 0.85
        mesh.data.materials.clear()
        mesh.data.materials.append(mat)

        # Decimation now also has to preserve skin weights, which the
        # collapse modifier interpolates - another reason to stay gentle.
        # Decimation has to stay gentle, and the reason is fit, not looks.
        # The body and its clothes are separate meshes fitted to each other
        # vertex by vertex; decimating them independently moves their
        # surfaces apart and the body erupts through the shirt. Hair is
        # worse - below about 0.5 it stops being strands and becomes white
        # shrapnel round the neck. Both found by rendering. The budget is
        # not the constraint: eight figures at 5k tris is nothing against
        # the measured headroom.
        # Only the BODY is decimated. Clothes and hair are fitted meshes -
        # every vertex of a garment is tied to the body surface beneath it,
        # so collapsing its edges tears the fit open: jeans shear into
        # shards and forearms punch through the trouser leg. Verified by
        # rendering one figure large. They are cheap anyway; the body is
        # the part with the polygons.
        for o in [o for o in bpy.data.objects if o.type == "MESH"]:
            fitted = any(h in o.name for h in HAIR) or \
                any(c in o.name for c in MALE_SUITS + FEMALE_SUITS + SHOES)
            if fitted:
                continue
            decimate(o, 0.45)

        # the armature ships too: the scene turns neck bones
        bpy.ops.object.select_all(action="SELECT")
        path = os.path.join(out_dir, "person_%02d.glb" % i)
        bpy.ops.export_scene.gltf(filepath=path, use_selection=True,
                                  export_apply=True, export_morph=False)
        print("GEN person_%02d %.2f MB" % (i, os.path.getsize(path) / 1048576))


if __name__ == "__main__":
    try:
        argv = sys.argv[sys.argv.index("--") + 1:]
        out = argv[0] if argv else "/tmp/humans"
        count = int(argv[1]) if len(argv) > 1 else 6
        generate(out, count)
        print("GEN done: %d figures in %s" % (count, out))
    except Exception:
        traceback.print_exc()
        sys.exit(1)
