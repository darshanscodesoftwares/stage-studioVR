import bpy, math, mathutils, traceback

def rad(d): return d*math.pi/180
BASE = {"upperleg01.L": (-88,0,-6), "upperleg01.R": (-88,0,6),
        "lowerleg01.L": (86,0,0),   "lowerleg01.R": (86,0,0),
        "spine03": (6,0,0), "spine02": (4,0,0)}
try:
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    bpy.ops.wm.read_homefile(use_empty=True)
    m = HumanService.create_human()
    HumanService.add_builtin_rig(m, 'default', import_weights=True)
    arm = [o for o in bpy.data.objects if o.type=='ARMATURE'][0]
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True); bpy.context.view_layer.objects.active=arm
    bpy.ops.object.mode_set(mode='POSE')
    for n,(x,y,z) in BASE.items():
        pb = arm.pose.bones.get(n)
        if pb: pb.rotation_mode='XYZ'; pb.rotation_euler=(rad(x),rad(y),rad(z))
    bpy.context.view_layer.update()

    def world(nm):
        pb = arm.pose.bones.get(nm)
        return (arm.matrix_world @ pb.matrix).to_translation() if pb else None

    hip  = world('upperleg01.L')
    knee = world('lowerleg01.L')
    sh   = world('upperarm01.L')
    print('PROBE hipL  = %.3f %.3f %.3f' % tuple(hip))
    print('PROBE kneeL = %.3f %.3f %.3f' % tuple(knee))
    print('PROBE shldrL= %.3f %.3f %.3f' % tuple(sh))
    # target: on top of the thigh, 60% toward the knee, a little above the surface
    t = hip.lerp(knee, 0.60)
    target = mathutils.Vector((t.x, t.y, t.z + 0.085))
    print('PROBE targetL = %.3f %.3f %.3f' % tuple(target))

    ua = arm.pose.bones['upperarm01.L']; la = arm.pose.bones['lowerarm01.L']
    ua.rotation_mode='XYZ'; la.rotation_mode='XYZ'

    best = None
    for ux in range(-10, 41, 10):
      for uy in range(-90, -29, 15):
        for uz in range(-92, -59, 8):
          for lx in range(10, 81, 10):
            ua.rotation_euler = (rad(ux), rad(uy), rad(uz))
            la.rotation_euler = (rad(lx), 0, 0)
            bpy.context.view_layer.update()
            w = world('wrist.L')
            d = (w - target).length
            # palm should face DOWN: normal from the hand plane
            f3 = world('finger3-1.L'); f1 = world('finger1-1.L')
            score = d
            if f3 and f1:
                fdir = (f3 - w).normalized()
                tdir = (f1 - w).normalized()
                n = fdir.cross(tdir).normalized()
                score = d + 0.16 * (1.0 - max(0.0, -n.z))   # -z is down
            if best is None or score < best[0]:
                best = (score, d, ux, uy, uz, lx)
    print('PROBE BEST score=%.3f dist=%.3fm  upperarm=(%d,%d,%d) lowerarm=(%d,0,0)'
          % best)
except Exception:
    traceback.print_exc(); print('PROBE FAILED')
