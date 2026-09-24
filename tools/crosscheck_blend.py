"""Independent cross-check of a built am.blend: rotations read from Blender vs tools/check_kinematics.py angle laws.
Run: Blender -b <am.blend> --python-exit-code 1 -P crosscheck_blend.py   (auto-exec OFF: only simple expressions evaluate)"""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parent.parent)   # repository root
import bpy, math, sys, numpy as np
sys.path.insert(0, f'{ROOT}/tools')
sys.argv = [sys.argv[0], f'{ROOT}/spec/antikythera.json']
import importlib.util
spec = importlib.util.spec_from_file_location('ck', f'{ROOT}/tools/check_kinematics.py')
src = open(f'{ROOT}/tools/check_kinematics.py').read().split('rng = np.random.default_rng')[0]
ns = {}; exec(src, ns)
angles = ns['angles']; B = ns['B']
print("autoexec enabled:", bpy.app.autoexec_fail is False and bpy.context.preferences.filepaths.use_scripts_auto_execute)
ctl = bpy.data.objects['AM_Controller']
vl = bpy.context.view_layer
def wrap(x): return (x + math.pi) % (2*math.pi) - math.pi
rng = np.random.default_rng(7)
worst = {}; missing = []
for v in list(rng.uniform(-40, 40, 40)) + [0.0, 1.0, 19.0]:
    c = float(np.float32(v)); ctl['crank'] = c; ctl.update_tag(); vl.update()
    A = ns['angles'](np.array([c]))
    for bid, b in B.items():
        name = 'B_' + bid
        ob = bpy.data.objects.get(name)
        if ob is None: missing.append(bid); continue
        if bid in ('frame',): continue
        if bid == 'a': ref = -2*math.pi*223/48*c; got = ob.rotation_euler[0]
        elif bid == 'q': ref = float(A['q_rel'][0]); got = ob.rotation_euler[0]
        elif b['parent'] == 'b': ref = float(A.get(bid + '_local', A.get(bid))[0]); got = ob.rotation_euler[2]
        elif b['parent'] == 'e_table': ref = float(A[bid + '_local'][0] if bid + '_local' in A else A[bid][0]); got = ob.rotation_euler[2]
        else: ref = float(A[bid][0]); got = ob.rotation_euler[2]
        e = abs(wrap(got - ref)); worst[bid] = max(worst.get(bid, 0), e)
bad = {k: v for k, v in worst.items() if v > 1e-5}
print(f"bodies compared: {len(worst)}, missing Empties: {sorted(set(missing))}")
print(f"max |Blender - independent solver|: {max(worst.values()):.2e} rad (body {max(worst, key=worst.get)})")
# animation: frames 1/61/481 without auto-exec
scn = bpy.context.scene
vals = []
for f in (1, 61, 481):
    scn.frame_set(f); vals.append(round(float(ctl['crank']), 6))
b1 = bpy.data.objects['B_b']; scn.frame_set(61); r61 = b1.rotation_euler[2]
print("crank at frames 1/61/481:", vals, "| B_b rotation at frame 61:", round(r61, 6), "(expected", round(wrap(-2*math.pi*0.5), 6), ")")
mc = bpy.data.movieclips.load(f'{ROOT}/build/out/renders/antikythera.mp4')
print("mp4 frame_duration:", mc.frame_duration, "size:", tuple(mc.size))
print("CROSSCHECK", "OK" if not bad and not missing and vals == [0.0, 0.5, 4.0] and mc.frame_duration == 480 else f"FAIL {bad}")
