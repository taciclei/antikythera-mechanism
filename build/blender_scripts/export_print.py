"""Print export (step 7): for each profile, regenerate teeth (profile backlash), bores, holes, slots
and grooves (bore clearance), re-run the 2D check, export one STL per part from an unparented
temporary copy in its body-local frame, write one 3MF, re-import checks, bed and wall report.
Run: Blender -b --factory-startup --python-exit-code 1 -P blender_scripts/export_print.py -- [profile]"""
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

from am import spec as S, kinematics as K, involute as INV, layout as LAY  # noqa: E402
from am import interference2d as X2, threemf  # noqa: E402
import meshing  # noqa: E402


def export_stl(ob, path, s):
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o is not None and o is not ob:
            o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, use_batch=False, global_scale=s,
                          use_scene_unit=False, apply_modifiers=True, ascii_format=False,
                          forward_axis='Y', up_axis='Z')


def walls(spec, cat, prof, pp):
    """min_wall_mm report (rims, arms, hubs, slot/bore walls) and fragile tip lands."""
    s = prof.s
    mw = pp['min_wall_mm']
    rows, fragile = [], []
    for gid, info in cat.gear_info.items():
        g = spec.gears[gid]
        m = g['module']
        if info['n_windows']:
            rows.append((gid, 'rim', max(1.5, 2 * m) * s))
            rows.append((gid, 'hub', 2.0 * s))
            rows.append((gid, 'arm', max(1.5, 0.12 * g['pitch_radius']) * s))
        elif g['kind'] != 'annulus_external':
            rows.append((gid, 'bore-root', (info['rf'] - info['bore']) * s))
        else:
            rows.append((gid, 'annulus', (info['rf'] - info['bore']) * s))
        for ps in spec.pin_slots:
            if ps['slot_gear'] == gid:
                hw = prof.slot_hw
                r1 = ps['pin_radius'] + ps['offset'] + 0.6 + (hw - 0.55)
                r0 = ps['pin_radius'] - ps['offset'] - 0.6 - (hw - 0.55)
                rows.append((gid, 'slot-root', (info['rf'] - r1) * s))
                rows.append((gid, 'slot-bore', (r0 - info['bore']) * s))
        tl = INV.Involute(g['teeth'], m * s, j=pp['backlash_mm']).tip_land()
        if tl < 0.2 * m * s:
            fragile.append({'gear': gid, 'tip_land_mm': round(tl, 4), 'limit': round(0.2 * m * s, 4)})
    for p in cat.parts:
        if 'lever' in p['extra']:
            rows.append((p['name'], 'slot side wall', (1.5 - prof.slot_hw) * s))
        if p['name'].startswith('hub_') or p['name'] in ('b_hub', 'pipe_e', 'fixed_tube') or \
                p['name'].startswith('t_') and p['kind'] == 'prism':
            f = p['foot'].get('ann')
            if f:
                rows.append((p['name'], 'tube wall', (f[3] - f[2]) * s))
    thin = [{'part': a, 'what': b, 'wall_mm': round(c, 4)} for a, b, c in rows if c < mw - 1e-9]
    return {'min_wall_mm': mw, 'checked': len(rows), 'below_min': thin,
            'min_found_mm': round(min(c for _, _, c in rows), 4), 'fragile_tip_lands': fragile}


def run_profile(spec, laws, phases, prof, pp):
    t0 = time.time()
    s = prof.s
    d = os.path.join(OUT, 'print', prof.name)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.stl') or f.endswith('.3mf'):
            os.remove(os.path.join(d, f))
    inter = X2.check_all(spec, laws, phases, j=pp['backlash_mm'], scale=s)
    cat = LAY.build(spec, laws, prof=prof, phases=phases)
    bed = sorted(pp['bed_mm'])
    col = bpy.context.scene.collection
    objs3mf, parts, oversize, mesh_fail = [], [], [], []
    for p in cat.parts:
        me, area = meshing.part_mesh(spec, p, shrink=prof.j / 2 if p['kind'] == 'crown' else 0.0,
                                     name='tmp_' + p['name'])
        chk = meshing.check_mesh(me)
        ob = bpy.data.objects.new('tmp_' + p['name'], me)
        col.objects.link(ob)           # unparented, identity transform = body-local frame
        path = os.path.join(d, p['name'] + '.stl')
        export_stl(ob, path, s)
        V, T = meshing.mesh_arrays(me)
        V = V * s
        lo, hi = V.min(0), V.max(0)
        dims = hi - lo
        fits = sorted(dims[:2].tolist())
        big = fits[0] > bed[0] or fits[1] > bed[1]
        if big:
            oversize.append({'part': p['name'], 'size_mm': [round(x, 2) for x in dims.tolist()]})
        if not chk['ok']:
            mesh_fail.append(p['name'])
        parts.append({'part': p['name'], 'size_mm': [round(x, 3) for x in dims.tolist()],
                      'stl_bytes': os.path.getsize(path), 'closed': chk['ok']})
        objs3mf.append((p['name'], V, T))
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
        bpy.context.view_layer.update()
    tmf = os.path.join(d, 'antikythera.3mf')
    threemf.write(tmf, objs3mf)
    back, n_items = threemf.read(tmf)
    tmf_ok = (len(back) == len(objs3mf) and n_items == len(objs3mf)
              and all(threemf.closed(T) for _, _, T in back))
    # re-import one STL of every kind and compare its size to the local copy x scale
    reimp = []
    for name in ('b1', 'a1', 'main_plate', 'marker_trueSun'):
        path = os.path.join(d, name + '.stl')
        before = set(bpy.data.objects)
        bpy.ops.wm.stl_import(filepath=path, global_scale=1.0, use_scene_unit=False,
                              forward_axis='Y', up_axis='Z')
        new = [o for o in bpy.data.objects if o not in before][0]
        co = np.empty(len(new.data.vertices) * 3, np.float32)
        new.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        dims = co.max(0) - co.min(0)
        exp = next(q['size_mm'] for q in parts if q['part'] == name)
        err = float(np.max(np.abs(dims - np.array(exp)) / np.maximum(np.array(exp), 1e-9)))
        reimp.append({'part': name, 'dims': dims.tolist(), 'expected': exp, 'rel_err': err, 'ok': err <= 1e-3})
        bpy.data.objects.remove(new)
    wr = walls(spec, cat, prof, pp)
    rep = {'profile': prof.name, 'scale': s, 'backlash_mm': pp['backlash_mm'],
           'bore_clearance_mm': pp['bore_clearance_mm'], 'bed_mm': pp['bed_mm'],
           'n_parts': len(parts), 'n_stl': sum(1 for f in os.listdir(d) if f.endswith('.stl')),
           'interference2d_ok': all(r['ok'] for r in inter),
           'interference2d_min_signed': min(r['min_signed'] for r in inter),
           'interference2d_backlash_near': [min(r['backlash_near_min'] for r in inter),
                                            max(r['backlash_near_max'] for r in inter)],
           'interference2d_failed': [r['mesh'] for r in inter if not r['ok']],
           'mesh_failed': mesh_fail, 'oversize': oversize, 'reimport': reimp,
           'threemf': {'path': tmf, 'bytes': os.path.getsize(tmf), 'objects': len(back), 'ok': tmf_ok},
           'walls': wr, 'parts': parts, 'seconds': time.time() - t0}
    rep['ok'] = (rep['interference2d_ok'] and not mesh_fail and tmf_ok and all(r['ok'] for r in reimp)
                 and rep['n_stl'] == len(parts))
    with open(os.path.join(d, 'print_report.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=float)
    log('%s: %d STL, 3MF %s (%.1f MB), 2D %s (backlash near %.4f..%.4f), oversize %d, thin walls %d, '
        'fragile tips %d, reimport %s (%.0f s) -> %s' % (
            prof.name, rep['n_stl'], tmf_ok, rep['threemf']['bytes'] / 1e6, rep['interference2d_ok'],
            rep['interference2d_backlash_near'][0], rep['interference2d_backlash_near'][1], len(oversize),
            len(wr['below_min']), len(wr['fragile_tip_lands']), all(r['ok'] for r in reimp),
            rep['seconds'], rep['ok']))
    return rep['ok']


def main():
    a = bootstrap.args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    spec = S.load()
    laws = K.Laws(spec)
    phases, _ = INV.compute_phases(spec, laws)
    ok = True
    for prof, pp in LAY.print_profiles(spec):
        if a and prof.name not in a:
            continue
        ok &= run_profile(spec, laws, phases, prof, pp)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
