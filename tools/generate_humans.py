"""Generate varied rigged humans for the audience, headless.

    ~/tools/blender/blender --background --python tools/generate_humans.py -- <out_dir>

Requires Blender 4.5 with the MPFB extension installed (see PROJECT.md,
"Tooling"). Each figure is driven by a macro dict — gender, age, muscle,
weight, height, proportions, ethnicity, all 0..1 floats — which is the
"generate forty different audience members" plan from the brief made real.

Licence: the MakeHuman base mesh that every generated character derives
from was explicitly released as CC0 in September 2020 (the statement, with
the named copyright holders, is in the header of MPFB's data/3dobjs/base.obj).
MPFB itself is GPL, which covers the tool, not its output.

Export notes, learned by rendering rather than reading:
- export_apply=True is what REMOVES the helper scaffolding (the "skirt" and
  the face curtain) — it bakes the mask modifier that hides them. Without it
  every figure ships wearing its own rigging aids.
- export_morph=False drops the macro shape keys, which are the difference
  between 0.9 MB and 12-17 MB per figure.
"""
import os
import sys
import traceback

import bpy


def hash01(i, salt):
    """Deterministic per-index pseudo-random 0..1, same shape as the one in
    index.html — a given seat keeps its body across regenerations."""
    import math
    x = math.sin(i * 127.1 + salt * 311.7) * 43758.5453
    return x - math.floor(x)


def macro_for(i):
    """A plausible, varied audience member. Deliberately mid-heavy: real
    rooms are mostly unremarkable bodies with a few outliers."""
    return {
        "gender": hash01(i, 1),
        "age": 0.25 + hash01(i, 2) * 0.6,
        "muscle": 0.3 + hash01(i, 3) * 0.4,
        "weight": 0.3 + hash01(i, 4) * 0.45,
        "proportions": 0.35 + hash01(i, 5) * 0.3,
        "height": 0.3 + hash01(i, 6) * 0.4,
        "cupsize": 0.4 + hash01(i, 7) * 0.2,
        "firmness": 0.5,
        "race": {
            "asian": hash01(i, 8),
            "caucasian": hash01(i, 9),
            "african": hash01(i, 10),
        },
    }


def generate(out_dir, count):
    from bl_ext.user_default.mpfb.services.humanservice import HumanService

    os.makedirs(out_dir, exist_ok=True)
    for i in range(count):
        bpy.ops.wm.read_homefile(use_empty=True)

        mesh = HumanService.create_human(macro_detail_dict=macro_for(i))
        HumanService.add_builtin_rig(mesh, "default", import_weights=True)

        # Plain skin material; tone varies per figure. Textured skin can come
        # later from the CC0 system assets — this keeps the figure smaller
        # than any skin texture would be.
        tone = 0.25 + hash01(i, 11) * 0.55
        mat = bpy.data.materials.new("skin")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (
            tone, tone * 0.72, tone * 0.55, 1)
        bsdf.inputs["Roughness"].default_value = 0.8
        mesh.data.materials.clear()
        mesh.data.materials.append(mat)

        bpy.ops.object.select_all(action="SELECT")
        path = os.path.join(out_dir, "person_%02d.glb" % i)
        bpy.ops.export_scene.gltf(
            filepath=path,
            use_selection=True,
            export_apply=True,      # bakes the mask: removes helper geometry
            export_morph=False,     # drops shape keys: 0.9 MB not 12-17 MB
        )
        print("GEN person_%02d %.2f MB" % (i, os.path.getsize(path) / 1048576))


if __name__ == "__main__":
    try:
        argv = sys.argv[sys.argv.index("--") + 1:]
        out = argv[0] if argv else "/tmp/humans"
        count = int(argv[1]) if len(argv) > 1 else 8
        generate(out, count)
        print("GEN done: %d figures in %s" % (count, out))
    except Exception:
        traceback.print_exc()
        sys.exit(1)
