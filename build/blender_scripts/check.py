"""3D verification of out/am.blend (spec 5.9, points 5-6) -> out/check_<mode>.json, merged into
out/check.json. Run: Blender -b --factory-startup --python-exit-code 1 -P blender_scripts/check.py -- <mode> [i n]
 modes: static | meshes | pins | pairs <batch> <n_batches> | spiral | texts | merge"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bootstrap  # noqa: E402
from bootstrap import OUT, log  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

from am import spec as S, kinematics as K, involute as INV, layout as LAY, regions as REG  # noqa: E402
from am import spiral as SP, expr as EX  # noqa: E402
import meshing  # noqa: E402

SEED = 20260924


class Scene:
    def __init__(self):
        bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'am.blend'))
        self.sc = bpy.context.scene
        self.vl = bpy.context.view_layer
        self.ctl = bpy.data.objects['AM_Controller']
        self.crank_fc = None
        ad = self.ctl.animation_data
        if ad and ad.action:
            from bpy_extras import anim_utils
            cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
            self.crank_fc = next(fc for fc in cb.fcurves if fc.data_path == '["crank"]')
            self.crank_values = {f: self.crank_fc.evaluate(f) for f in (1, 61, 481, 961)}
            self.crank_extrap = self.crank_fc.extrapolation
            self.crank_interp = [k.interpolation for k in self.crank_fc.keyframe_points]
            ad.action = None       # the property is driven by hand below
        self.mesh = {}
        self.static_bvh = {}

    def set_crank(self, v):
        c = float(np.float32(v))
        self.ctl['crank'] = c
        self.ctl.update_tag()
        self.vl.update()
        return c

    def dg(self):
        return bpy.context.evaluated_depsgraph_get()

    def arrays(self, name):
        if name not in self.mesh:
            me = bpy.data.objects[name].data
            V, T = meshing.mesh_arrays(me)
            self.mesh[name] = (V, T.tolist())
        return self.mesh[name]

    def world(self, name, dg=None):
        ob = bpy.data.objects[name].evaluated_get(dg or self.dg())
        M = np.array(ob.matrix_world)
        V, T = self.arrays(name)
        return V @ M[:3, :3].T + M[:3, 3], T

    def bvh(self, name, static=False, dg=None):
        if static and name in self.static_bvh:
            return self.static_bvh[name]
        W, T = self.world(name, dg)
        t = BVHTree.FromPolygons(W.tolist(), T, all_triangles=True)
        if static:
            self.static_bvh[name] = t
        return t

    def rot(self, body, index, dg=None):
        ob = bpy.data.objects['B_' + body].evaluated_get(dg or self.dg())
        return float(ob.rotation_euler[index])


def catalog():
    spec = S.load()
    laws = K.Laws(spec)
    phases, _ = INV.compute_phases(spec, laws)
    cat = LAY.build(spec, laws, phases=phases)
    return spec, laws, cat


def write(mode, rep):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'check_%s.json' % mode), 'w') as f:
        json.dump(rep, f, indent=1, default=float)


# ---------------------------------------------------------------- static: drivers, readback, cycles
def mode_static():
    sc = Scene()
    spec, laws, cat = catalog()
    ex = EX.build(spec)
    rep = {}
    # driver validity
    drv = []
    for ob in bpy.data.objects:
        if ob.animation_data:
            for fc in ob.animation_data.drivers:
                d = fc.driver
                drv.append((ob.name, d.expression, d.is_valid, d.is_simple_expression))
    exp = {('B_' + b, e['expr']) for b, e in ex.items()}
    rep['drivers'] = {'count': len(drv), 'all_valid': all(d[2] for d in drv),
                      'all_simple': all(d[3] for d in drv),
                      'expressions_match': exp <= {(d[0], d[1]) for d in drv},
                      'max_len': max(len(d[1]) for d in drv)}
    # readback over 50 crank values in [-50, 50]
    rng = np.random.default_rng(SEED)
    vals = list(rng.uniform(-50, 50, 46)) + [-50.0, 0.0, 0.5, 50.0]
    worst, where = 0.0, None
    for v in vals:
        c = sc.set_crank(v)
        dg = sc.dg()
        A = laws.local(c)
        for body, e in ex.items():
            got = sc.rot(body, e['index'], dg)
            err = abs(K.wrap(got - A[body]))
            if err > worst:
                worst, where = err, (body, c)
    rep['readback'] = {'samples': len(vals), 'max_err_rad': worst, 'worst': where, 'ok': worst < 1e-5}
    # cycles
    cyc = {}
    for name, body, T in (('metonic', 'n', 19.0), ('olympiad', 'o', 4.0), ('callippic', 'cal', 76.0),
                          ('saros', 'g', float(np.float32(4237 / 235)))):
        errs = []
        for c0 in (0.0, 1.0, 2.5):
            sc.set_crank(c0)
            a0 = sc.rot(body, 2)
            sc.set_crank(c0 + T)
            a1 = sc.rot(body, 2)
            errs.append(abs(K.wrap(a1 - a0)))
        cyc[name] = {'period_years': T, 'max_err_rad': max(errs), 'ok': max(errs) < 1e-5}
    rep['cycles'] = cyc
    # crank F-curve
    cv = sc.crank_values if sc.crank_fc else {}
    rep['crank_fcurve'] = {'values': cv, 'extrapolation': getattr(sc, 'crank_extrap', None),
                           'interpolation': getattr(sc, 'crank_interp', None),
                           'ok': bool(cv) and cv[1] == 0.0 and abs(cv[61] - 0.5) < 1e-6
                           and abs(cv[481] - 4.0) < 1e-6 and abs(cv[961] - 8.0) < 1e-5}
    # controller properties, units, cameras
    us = bpy.context.scene.unit_settings
    rep['scene'] = {'crank_is_float': type(sc.ctl['crank']) is float,
                    'patina_is_float': type(sc.ctl['patina']) is float,
                    'patina_range': [sc.ctl.id_properties_ui('patina').as_dict().get(k) for k in ('min', 'max')],
                    'units': [us.system, us.length_unit, us.scale_length],
                    'scale_ok': math.isclose(us.scale_length, 0.001, rel_tol=1e-6),
                    'cameras_clip': {o.name: [o.data.clip_start, o.data.clip_end]
                                     for o in bpy.data.objects if o.type == 'CAMERA'}}
    # hierarchy
    bad = []
    for ob in bpy.data.objects:
        if ob.parent is not None and not np.allclose(np.array(ob.matrix_parent_inverse), np.eye(4)):
            bad.append(ob.name)
    rep['hierarchy'] = {'non_identity_parent_inverse': bad, 'ok': not bad}
    # meshes (re-check on the saved file)
    mres = {}
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            mres[ob.name] = meshing.check_mesh(ob.data)
    rep['meshes'] = {'count': len(mres), 'all_ok': all(m['ok'] for m in mres.values()),
                     'failed': [k for k, m in mres.items() if not m['ok']]}
    rep['collections'] = {c.name: len(c.objects) for c in bpy.data.collections}
    rep['ok'] = (rep['drivers']['all_valid'] and rep['drivers']['all_simple'] and rep['drivers']['expressions_match']
                 and rep['readback']['ok'] and all(v['ok'] for v in cyc.values()) and rep['crank_fcurve']['ok']
                 and rep['scene']['crank_is_float'] and rep['scene']['scale_ok'] and rep['hierarchy']['ok']
                 and rep['meshes']['all_ok'])
    write('static', rep)
    log('readback max %.3e rad; cycles %s; crank fcurve %s; meshes %s -> %s' % (
        worst, {k: '%.1e' % v['max_err_rad'] for k, v in cyc.items()}, rep['crank_fcurve']['ok'],
        rep['meshes']['all_ok'], rep['ok']))
    return rep['ok']


# ---------------------------------------------------------------- BVH helpers
def overlap_pairs(sc, pairs, static_names, dg=None):
    dg = dg or sc.dg()
    trees = {}
    hits = []
    for a, b in pairs:
        for n in (a, b):
            if n not in trees:
                trees[n] = sc.bvh(n, static=n in static_names, dg=dg)
        ov = trees[a].overlap(trees[b])
        if ov:
            hits.append((a, b, len(ov)))
    return hits


def static_set(cat):
    return {p['name'] for p in cat.parts if p['body'] == 'frame'}


# ---------------------------------------------------------------- (a) meshes over one pitch
def mode_meshes():
    sc = Scene()
    spec, laws, cat = catalog()
    st = static_set(cat)
    res = []
    t0 = time.time()
    rates = K.solve(spec)['rates']
    for k, m in enumerate(spec.meshes):
        g1 = spec.gears[m['driver']]
        z1 = g1['teeth']
        if m['type'] == 'crown' and m['driver'] == 'a1':
            rate = float(laws.crank_rate)
        elif m['type'] == 'crown':
            rate = float(rates['b'] - rates['moon'])       # q relative to the Moon (mean)
        else:
            C = m['carrier']
            rate = float(rates[g1['body']] - (rates[C] if C != 'frame' else 0))
        pitch_years = abs(1.0 / (z1 * rate))
        c0 = 0.2 + 0.37 * k
        hits = 0
        cs = []
        for i in range(50):
            c = sc.set_crank(c0 + pitch_years * i / 50)
            cs.append(c)
            h = overlap_pairs(sc, [(m['driver'], m['driven'])], st)
            hits += len(h)
        res.append({'mesh': '%s~%s' % (m['driver'], m['driven']), 'type': m['type'],
                    'pitch_years': pitch_years, 'positions': 50, 'distinct_c': len(set(cs)),
                    'overlaps': hits})
    rep = {'meshes': res, 'total_overlaps': sum(r['overlaps'] for r in res),
           'seconds': time.time() - t0}
    rep['ok'] = rep['total_overlaps'] == 0 and len(res) == 39
    write('meshes', rep)
    log('meshes: %d pairs x 50 positions, overlaps %d (%.0f s)' % (len(res), rep['total_overlaps'], rep['seconds']))
    return rep['ok']





# ---------------------------------------------------------------- (b) pin-slots and followers
def mode_pins():
    sc = Scene()
    spec, laws, cat = catalog()
    st = static_set(cat)
    by = cat.by_name()
    pre = json.load(open(os.path.join(OUT, 'prefilter_pairs.json')))
    retained = [(r['a'], r['b']) for r in pre['retained']]
    cases = []
    for p in spec['shafts']['pins']:
        pin, slot = p['id'], p['slot_in']
        body = by[pin]['body']
        T = 1.0 / abs(float(laws.rel[body]))
        cases.append((pin, slot, T))
    for which, T in (('metonic', 19.0), ('saros', 4237 / 235)):
        cases.append((which + '_slider_pin', 'back_plate', T))
    res = []
    t0 = time.time()
    for pin, slot, T in cases:
        names = {pin, slot}
        pairs = sorted({(a, b) for a, b in retained if a in names or b in names} | {(pin, slot)})
        hits = []
        for i in range(72):
            sc.set_crank(0.05 + T * i / 72)
            hits += overlap_pairs(sc, pairs, st)
        res.append({'pin': pin, 'slot': slot, 'cycle_years': T, 'positions': 72,
                    'pairs_tested': len(pairs), 'overlaps': hits})
    rep = {'cases': res, 'total_overlaps': sum(len(r['overlaps']) for r in res),
           'seconds': time.time() - t0}
    rep['ok'] = rep['total_overlaps'] == 0
    write('pins', rep)
    log('pins/followers/sliders: %d cases x 72, overlaps %d (%.0f s)' % (len(res), rep['total_overlaps'],
                                                                          rep['seconds']))
    return rep['ok']


# ---------------------------------------------------------------- (c) retained pairs x 240 cranks
def crank_samples():
    rng = np.random.default_rng(SEED)
    return list(np.linspace(0.0, 1.0, 120)) + list(rng.uniform(0.0, 76.0, 120))


def mode_pairs(batch, nb):
    sc = Scene()
    spec, laws, cat = catalog()
    st = static_set(cat)
    pre = json.load(open(os.path.join(OUT, 'prefilter_pairs.json')))
    pairs = sorted({(r['a'], r['b']) for r in pre['retained']})
    names = {p['name'] for p in cat.parts}
    missing = [p for p in pairs if p[0] not in names or p[1] not in names]
    samples = crank_samples()
    mine = samples[batch::nb]
    t0 = time.time()
    hits = []
    for v in mine:
        c = sc.set_crank(v)
        for a, b, n in overlap_pairs(sc, pairs, st):
            hits.append({'a': a, 'b': b, 'n': n, 'crank': c})
    rep = {'batch': batch, 'n_batches': nb, 'samples': len(mine), 'pairs': len(pairs),
           'missing_objects': missing, 'overlaps': hits, 'seconds': time.time() - t0}
    rep['ok'] = not hits and not missing
    write('pairs_%d' % batch, rep)
    log('pairs batch %d/%d: %d samples x %d pairs, overlaps %d (%.0f s)' % (
        batch, nb, len(mine), len(pairs), len(hits), rep['seconds']))
    return rep['ok']


# ---------------------------------------------------------------- point 6: spirals follow rho(psi)
def mode_spiral():
    sc = Scene()
    spec, laws, cat = catalog()
    rng = np.random.default_rng(SEED + 6)
    vals = rng.uniform(-76, 76, 500)
    res = {}
    for which, body in (('metonic', 'n'), ('saros', 'g')):
        d, c = SP.dial(spec, which)
        worst = 0.0
        for v in vals:
            cc = sc.set_crank(v)
            ob = bpy.data.objects[which + '_slider_pin'].evaluated_get(sc.dg())
            P = np.array(ob.matrix_world.translation)[:2]
            W = laws.world_z(cc)
            turns = d['turns']
            # psi_mod from the exact rates
            psi = -2 * math.pi * float(laws.rel[body]) * cc
            psi = psi % (2 * math.pi * turns)
            Q = SP.uv_to_xy(SP.point_uv(psi, d['r_start'], d['pitch']), c)
            worst = max(worst, float(np.linalg.norm(P - Q)))
            del W
        res[which] = {'samples': len(vals), 'max_err_mm': worst, 'ok': worst < 0.01}
    rep = {'spirals': res, 'ok': all(r['ok'] for r in res.values())}
    write('spiral', rep)
    log('spirals: %s' % {k: '%.2e mm' % v['max_err_mm'] for k, v in res.items()})
    return rep['ok']


# ---------------------------------------------------------------- texts z clearance (pure geometry)
def mode_texts():
    spec, laws, cat = catalog()
    br = json.load(open(os.path.join(OUT, 'build_report.json')))
    pf = REG.Prefilter(spec, cat)
    rows, ok = [], True
    for t in br['texts']['texts']:
        pts = np.array(t['xy_hull'])
        worst = None
        for p in cat.parts:
            if p['body'] == 'frame':
                continue
            R = pf.region(p, 'frame')
            if R[0] == 'ann':
                _, cx, cy, r1, r2, _ = R
                d = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
                hit = bool(np.any((d >= r1 - 0.2) & (d <= r2 + 0.2)))
            else:
                hit = any(REG.inside(pts, isl[0]).any() for isl in R[1])
            if not hit:
                continue
            dz = max(p['fz'][0] - t['z'][1], t['z'][0] - p['fz'][1])
            if worst is None or dz < worst[0]:
                worst = (dz, p['name'])
        good = worst is None or worst[0] >= 0.1 - 1e-6
        ok &= good
        rows.append({'text': t['name'], 'body': t['body'], 'z': t['z'], 'extrude': t['extrude'],
                     'closest_moving': worst, 'ok': good})
    rep = {'texts': rows, 'missing_glyphs': br['texts']['missing_glyphs'], 'ok': ok,
           'max_extrude': max(t['extrude'] for t in br['texts']['texts'])}
    rep['ok'] = ok and 2 * rep['max_extrude'] <= 0.05 + 1e-9
    write('texts', rep)
    log('texts: %d, min z gap to overlapping moving parts %.3f -> %s' % (
        len(rows), min(r['closest_moving'][0] for r in rows if r['closest_moving']), rep['ok']))
    return rep['ok']


def mode_sanity():
    """The BVH test must detect known intersections (same-body overlaps, a mis-phased gear)."""
    sc = Scene()
    spec, laws, cat = catalog()
    sc.set_crank(0.3)
    res = {}
    for a, b in (('phase_sphere_dark', 'q_arbor'), ('hub_me20', 'mercury_disk'), ('b2', 'c1')):
        res['%s|%s' % (a, b)] = len(overlap_pairs(sc, [(a, b)], set()))
    ob = bpy.data.objects['c1']
    ob.rotation_euler[2] += math.pi / 38      # half a tooth pitch of c1
    sc.set_crank(0.3)
    res['c1 mis-phased|b2'] = len(overlap_pairs(sc, [('b2', 'c1')], set()))
    ob.rotation_euler[2] -= math.pi / 38
    rep = {'detections': res,
           'ok': res['phase_sphere_dark|q_arbor'] > 0 and res['hub_me20|mercury_disk'] > 0
           and res['b2|c1'] == 0 and res['c1 mis-phased|b2'] > 0}
    write('sanity', rep)
    log('sanity', res, rep['ok'])
    return rep['ok']


def mode_merge():
    out = {}
    ok = True
    for f in sorted(os.listdir(OUT)):
        if f.startswith('check_') and f.endswith('.json') and f != 'check.json':
            d = json.load(open(os.path.join(OUT, f)))
            out[f[6:-5]] = d
            ok &= bool(d.get('ok'))
    pairs = [v for k, v in out.items() if k.startswith('pairs_')]
    out['summary'] = {
        'readback_ok': out.get('static', {}).get('readback', {}).get('ok'),
        'cycles_ok': all(v['ok'] for v in out.get('static', {}).get('cycles', {}).values()),
        'crank_fcurve_ok': out.get('static', {}).get('crank_fcurve', {}).get('ok'),
        'meshes_manifold_ok': out.get('static', {}).get('meshes', {}).get('all_ok'),
        'bvh_meshes_overlaps': out.get('meshes', {}).get('total_overlaps'),
        'bvh_pins_overlaps': out.get('pins', {}).get('total_overlaps'),
        'bvh_pairs_samples': sum(p['samples'] for p in pairs),
        'bvh_pairs_overlaps': sum(len(p['overlaps']) for p in pairs),
        'spirals_ok': out.get('spiral', {}).get('ok'),
        'texts_ok': out.get('texts', {}).get('ok'),
        'ok': ok and sum(p['samples'] for p in pairs) == 240,
    }
    with open(os.path.join(OUT, 'check.json'), 'w') as f:
        json.dump(out, f, indent=1, default=float)
    log('check.json summary', out['summary'])
    return out['summary']['ok']


if __name__ == '__main__':
    a = bootstrap.args()
    mode = a[0] if a else 'static'
    if mode == 'static':
        ok = mode_static()
    elif mode == 'meshes':
        ok = mode_meshes()
    elif mode == 'pins':
        ok = mode_pins()
    elif mode == 'pairs':
        ok = mode_pairs(int(a[1]), int(a[2]))
    elif mode == 'spiral':
        ok = mode_spiral()
    elif mode == 'texts':
        ok = mode_texts()
    elif mode == 'sanity':
        ok = mode_sanity()
    elif mode == 'merge':
        ok = mode_merge()
    else:
        raise SystemExit('unknown mode ' + mode)
    sys.exit(0 if ok else 1)
