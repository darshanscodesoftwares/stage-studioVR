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
# Thighs horizontal, shins vertical, hands resting ON the thighs.
#
# Two earlier attempts, both rejected by rendering. Splitting the leg bend
# across upperleg01+02 to spare the garment fit stopped the silhouette
# reading as seated and became a splay. And a 45-degree elbow left the
# hands hovering in front of the belly with the fingers splayed - fine on
# one figure, but along a row at a shallow angle it reads as a thicket of
# reaching arms, which is what it looked like in the hall.
#
# The arm angles are SOLVED, not guessed - see tools/solve_arm_pose.py.
#
# Six hand-picked attempts all failed: palms turned up as if meditating,
# hands dangling beside the seat, forearms held out like a steering wheel.
# This rig's axes do not map onto any intuition about what x, y and z
# should do, and two behaviours are actively backwards - increasing the
# ELBOW angle RAISES the hand, and where the palm ends up facing is set by
# the UPPER ARM's roll rather than by the wrist.
#
# So the solver grid-searches upper-arm x/roll/z and elbow x, evaluates each
# pose, and scores it by how close the WRIST lands to a target measured on
# the figure's own thigh: 60% of the way from hip to knee, a little above
# the surface. The winner puts the wrist within 2cm of it. Rerun the solver
# if the seated leg pose ever changes, because the target moves with it.
POSE = {
    "upperleg01.L": (-88, 0, -6), "upperleg01.R": (-88, 0, 6),
    "lowerleg01.L": (86, 0, 0),   "lowerleg01.R": (86, 0, 0),
    "upperarm01.L": (10, -30, -76), "upperarm01.R": (10, 30, 76),
    "lowerarm01.L": (20, 0, 0),     "lowerarm01.R": (20, 0, 0),
    "spine03": (6, 0, 0), "spine02": (4, 0, 0),
}

# A resting hand curls. Applied to every finger joint on both hands.
FINGER_CURL = {"1": 10, "2": 30, "3": 32, "4": 30, "5": 26}

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


SEAT_TO_FLOOR = 0.44          # chair pan height; must match CHAIR_PAN_Y in index.html


def _lowest_z(objs):
    """Lowest world Z across the evaluated (deformed) meshes."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = 1e9
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            z = (mw @ v.co).z
            if z < lo:
                lo = z
        ev.to_mesh_clear()
    return lo


def _seat_contact_z(arm, body):
    """Height of the buttock: the lowest body vertex under the hip joint.

    Two earlier versions failed. A fixed vertex window reported the seat
    20cm high on three of six bodies, because the box that catches the
    buttock on one pelvis catches the crotch on another. Replacing it with
    "hip bone minus a constant" was worse in a subtler way - it agreed with
    itself but disagreed with the measurement the SCENE uses to place the
    figure, by up to 10cm, so the solver converged on the wrong answer.

    This anchors the search to the hip joint, so the window follows the
    body, and then takes the lowest actual vertex - the same quantity the
    placement measurement takes.
    """
    hip = arm.pose.bones.get("upperleg01.L")
    if not hip:
        return None
    hw = (arm.matrix_world @ hip.matrix).to_translation()

    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    mw = body.matrix_world
    lo = 1e9
    for v in me.vertices:
        w = mw @ v.co
        if abs(w.x) < 0.12 and abs(w.y - hw.y) < 0.18 and w.z < hw.z + 0.05:
            if w.z < lo:
                lo = w.z
    ev.to_mesh_clear()
    return None if lo > 1e8 else lo


def fit_feet_to_floor(arm, body, others):
    """Adjust the shin angle until the soles sit exactly SEAT_TO_FLOOR below
    the seat contact, so the figure's feet meet the floor when it is placed
    on a chair.

    Leg length varies with every body, and the figure is positioned in the
    scene by its seat contact - so with one fixed shin angle the soles land
    wherever they happen to. Measured across six figures that was anything
    from 10cm buried in the carpet to 9cm hovering above it. A real person
    just moves their feet; this does the same thing.
    """
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    seat = _seat_contact_z(arm, body)
    target = seat - SEAT_TO_FLOOR
    # `others` is the shoe meshes; fall back to the body if a figure has none
    meshes = list(others) if others else [body]

    def try_deg(deg):
        for side in ("L", "R"):
            pb = arm.pose.bones.get("lowerleg01.%s" % side)
            if pb:
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = (rad(deg), 0, 0)
        bpy.context.view_layer.update()
        sole = _lowest_z(meshes)
        return abs(sole - target), deg, sole

    # Coarse then fine. Evaluating the depsgraph over four skinned meshes is
    # the expensive part, so 11 + 7 samples replaces 43 and lands in the same
    # place - the error curve has one minimum.
    best = None
    for deg in range(40, 125, 8):
        r = try_deg(deg)
        if best is None or r[0] < best[0]:
            best = r
    centre = best[1]
    for deg in range(max(38, centre - 6), min(126, centre + 7), 2):
        r = try_deg(deg)
        if r[0] < best[0]:
            best = r

    for side in ("L", "R"):
        pb = arm.pose.bones.get("lowerleg01.%s" % side)
        if pb:
            pb.rotation_euler = (rad(best[1]), 0, 0)
    bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode="OBJECT")
    print("GEN   shin %d deg -> sole %.3f (target %.3f, err %.3fm)"
          % (best[1], best[2], target, best[0]))
    return best[1]


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

    for side in ("L", "R"):
        for digit, deg in FINGER_CURL.items():
            for joint in ("1", "2", "3"):
                pb = arm.pose.bones.get("finger%s-%s.%s" % (digit, joint, side))
                if pb:
                    pb.rotation_mode = "XYZ"
                    pb.rotation_euler = (rad(deg), 0, 0)
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

        # set the pose, fit the feet to the floor, THEN bake
        bpy.ops.object.select_all(action="DESELECT")
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")
        for name, (x, y, z) in POSE.items():
            pb = arm.pose.bones.get(name)
            if pb:
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = (rad(x), rad(y), rad(z))
        for side in ("L", "R"):
            for digit, deg in FINGER_CURL.items():
                for joint in ("1", "2", "3"):
                    pb = arm.pose.bones.get("finger%s-%s.%s" % (digit, joint, side))
                    if pb:
                        pb.rotation_mode = "XYZ"
                        pb.rotation_euler = (rad(deg), 0, 0)
        bpy.ops.object.mode_set(mode="OBJECT")

        # Measure the SOLE from the shoes alone. Scanning every mesh made the
        # lowest vertex a hair tip for the long-haired figures - hair hangs
        # below the seat when seated - and the solver then chased a target
        # the shins could not move, pinning itself at the search limits.
        soles = [o for o in bpy.data.objects
                 if o.type == "MESH" and any(s in o.name for s in SHOES)]
        fit_feet_to_floor(arm, mesh, soles)

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
