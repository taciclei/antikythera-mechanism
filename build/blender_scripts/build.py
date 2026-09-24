"""Build the animated Antikythera model: scene, units, collections, bodies, parts, materials,
drivers, dials -> out/am.blend (+ out/build_report.json).
Run: Blender -b --factory-startup --python-exit-code 1 -P blender_scripts/build.py"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bootstrap  # noqa: E402,F401
from bootstrap import OUT, log  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from am import spec as S, kinematics as K, involute as INV, layout as LAY, expr as EX  # noqa: E402
import animate  # noqa: E402
import materials  # noqa: E402
import meshing  # noqa: E402


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    us = sc.unit_settings
    us.system = 'METRIC'
    us.length_unit = 'MILLIMETERS'
    us.scale_length = 0.001
    assert math.isclose(us.scale_length, 0.001, rel_tol=1e-6)
    sc.name = 'Antikythera'
    return sc


def collections(spec, sc):
    out = {}
    for name in spec['collections']:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
        out[name] = c
    return out


def body_empties(spec, coll):
    E = {}
    zc_a = spec.crowns['a1']['axis_z']
    zc_q = spec.crowns['q1']['axis_z']
    order = ['frame'] + [b['id'] for b in spec['bodies'] if b['id'] != 'frame']
    for bid in order:
        b = spec.bodies[bid]
        ob = bpy.data.objects.new('B_' + bid, None)
        coll.objects.link(ob)
        ob.empty_display_type = 'ARROWS'
        ob.empty_display_size = 4.0
        ob.rotation_mode = 'XYZ'
        E[bid] = ob
    for bid in order:
        b = spec.bodies[bid]
        ob = E[bid]
        p = b['parent']
        if p in ('b', 'e_table', 'moon'):
            ob.parent = E[p]
            ob.matrix_parent_inverse.identity()
        x, y = b['axis_xy_in_parent'] or (0.0, 0.0)
        z = zc_a if bid == 'a' else (zc_q if bid == 'q' else 0.0)
        ob.location = (x, y, z)
        ob['body'] = bid
        ob['status'] = spec.status_of_body(bid) if b['gears'] else 'HYPOTHETICAL'
        ob['role'] = 'Body empty (%s)' % b['kind']
        ob['teeth'] = 0
        ob['module'] = 0.0
        ob['sources'] = ''
    return E


def main():
    t0 = time.time()
    spec = S.load()
    laws = K.Laws(spec)
    phases, comps = INV.compute_phases(spec, laws)
    cat = LAY.build(spec, laws, phases=phases)
    sc = reset_scene()
    C = collections(spec, sc)
    ctl = animate.controller(C['AM_HELPERS'])
    E = body_empties(spec, C['AM_HELPERS'])
    mats = materials.make_all(spec, ctl)
    colors = spec['materials']['status_debug_colors']
    report = {'parts': {}, 'errors': []}
    for p in cat.parts:
        try:
            me, area = meshing.part_mesh(spec, p)
        except meshing.MeshError as e:
            report['errors'].append('%s: %s' % (p['name'], e))
            log('MESH ERROR', p['name'], e)
            continue
        me.materials.append(mats.get(p['material'], mats['bronze']))
        ob = bpy.data.objects.new(p['name'], me)
        C[p['coll']].objects.link(ob)
        ob.parent = E[p['body']]
        ob.matrix_parent_inverse.identity()
        ob.color = colors[p['status']]
        ob['status'] = p['status']
        ob['role'] = p['role']
        ob['teeth'] = int(p['teeth'])
        ob['module'] = float(p['module'])
        ob['body'] = p['body']
        ob['sources'] = p['sources']
        ob['kind'] = p['kind']
        if p['extra'].get('hidden'):
            ob.hide_viewport = True
            ob.hide_render = True
        chk = meshing.check_mesh(me)
        if p['extruded']:
            z0, z1 = float(np.float32(p['z'][0])), float(np.float32(p['z'][1]))
            expect = area * (z1 - z0)
            chk['volume_expected'] = expect
            chk['volume_rel_err'] = abs(chk['volume'] - expect) / abs(expect)
            chk['ok'] = chk['ok'] and chk['volume_rel_err'] <= 1e-6
        report['parts'][p['name']] = chk
        if not chk['ok']:
            report['errors'].append('%s: mesh check %s' % (p['name'], chk))
            log('MESH CHECK FAIL', p['name'], chk)
    # drivers
    exprs = EX.build(spec)
    fcs = animate.body_drivers(exprs)
    sl = EX.slider_exprs(spec)
    for p in cat.parts:
        if 'slider' in p['extra']:
            animate.slider_driver(bpy.data.objects[p['name']], sl[p['extra']['slider']])
    animate.crank_action(ctl, sc)
    # dial texts
    import dials
    report['texts'] = dials.add_texts(spec, C['AM_DIALS'], E['frame'], mats['text'])
    # cameras and lights
    import render
    render.setup_cameras_lights(sc, C['AM_HELPERS'])
    bpy.context.view_layer.update()
    # driver validation
    drv = []
    for ob in bpy.data.objects:
        ad = ob.animation_data
        if not ad:
            continue
        for fc in ad.drivers:
            d = fc.driver
            drv.append({'object': ob.name, 'path': fc.data_path, 'index': fc.array_index,
                        'expr': d.expression, 'valid': d.is_valid, 'simple': d.is_simple_expression})
    for m in bpy.data.materials:
        if m.node_tree and m.node_tree.animation_data:
            for fc in m.node_tree.animation_data.drivers:
                d = fc.driver
                drv.append({'object': m.name, 'path': fc.data_path, 'index': fc.array_index,
                            'expr': d.expression, 'valid': d.is_valid, 'simple': d.is_simple_expression})
    expected = {('B_' + b, e['expr']) for b, e in exprs.items()}
    got = {(d['object'], d['expr']) for d in drv}
    report['drivers'] = drv
    report['drivers_ok'] = (all(d['valid'] and d['simple'] for d in drv) and expected <= got
                            and all(len(d['expr']) <= 255 for d in drv))
    report['n_objects'] = len(bpy.data.objects)
    report['n_mesh_objects'] = sum(1 for o in bpy.data.objects if o.type == 'MESH')
    report['n_font_objects'] = sum(1 for o in bpy.data.objects if o.type == 'FONT')
    report['n_parts_catalog'] = len(cat.parts)
    report['n_empties'] = sum(1 for o in bpy.data.objects if o.type == 'EMPTY')
    report['n_bodies'] = len(spec['bodies'])
    report['count_ok'] = (report['n_mesh_objects'] == len(cat.parts)
                          and report['n_empties'] == len(spec['bodies']) + 1)
    report['meshes_ok'] = not report['errors'] and all(c['ok'] for c in report['parts'].values())
    report['scale_length'] = sc.unit_settings.scale_length
    report['build_seconds'] = time.time() - t0
    report['ok'] = report['drivers_ok'] and report['count_ok'] and report['meshes_ok']
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'am.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    with open(os.path.join(OUT, 'build_report.json'), 'w') as f:
        json.dump(report, f, indent=1, default=float)
    log('objects %d (mesh %d, font %d, empties %d), catalog %d parts' % (
        report['n_objects'], report['n_mesh_objects'], report['n_font_objects'], report['n_empties'],
        len(cat.parts)))
    log('drivers %d, all valid/simple/untruncated: %s' % (len(drv), report['drivers_ok']))
    log('meshes closed/manifold/volume: %s (%d errors)' % (report['meshes_ok'], len(report['errors'])))
    log('saved %s in %.1f s -> %s' % (path, report['build_seconds'], 'OK' if report['ok'] else 'FAIL'))
    if not report['ok']:
        sys.exit(1)


if __name__ == '__main__':
    main()
