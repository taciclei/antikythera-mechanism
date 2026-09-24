"""Greek dial texts (FONT objects, built-in font, extrusion 0.025 = 0.05 thick, body frame,
AM_DIALS) and missing-glyph detection against the notdef box of U+10300."""
import math

import bpy
import numpy as np

EXTRUDE = 0.025
NOTDEF = '\U00010300'


def _text(name, body, size, coll, parent, mat, loc, rot):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = EXTRUDE
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    ob.parent = parent
    ob.matrix_parent_inverse.identity()
    ob.location = loc
    ob.rotation_euler = rot
    ob['status'] = 'SURVIVING'
    ob['role'] = 'Dial inscription (FONT, excluded from mesh/BVH/print checks)'
    ob['teeth'] = 0
    ob['module'] = 0.0
    ob['body'] = 'frame'
    ob['sources'] = 'spec dials'
    ob['kind'] = 'text'
    return ob


def glyph_signature(ch, coll):
    cu = bpy.data.curves.new('glyph_probe', 'FONT')
    cu.body = ch
    ob = bpy.data.objects.new('glyph_probe', cu)
    coll.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    n = len(me.vertices)
    if n:
        co = np.empty(n * 3, np.float32)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        sig = (n, tuple(np.round(co.min(0), 4)), tuple(np.round(co.max(0), 4)))
    else:
        sig = (0, (), ())
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return sig


def add_texts(spec, coll, frame_empty, mat):
    fr = spec.dials['front']
    back = spec.dials['back']
    made = []
    # zodiac signs (longitude increases clockwise seen from the front, 0 on +x)
    zr = fr['zodiac_ring']
    z = zr['z_face'] + 0.1 + EXTRUDE
    for k, lab in enumerate(zr['labels']):
        a = -math.radians(30 * k + 15)
        r = 66.2
        made.append(_text('txt_zodiac_%02d' % k, lab, 1.9, coll, frame_empty, mat,
                          (r * math.cos(a), r * math.sin(a), z), (0.0, 0.0, a - math.pi / 2)))
    # calendar months (12 x 30 days + 5 epagomenal days)
    cr = fr['calendar_ring']
    z = cr['z'][1] + EXTRUDE
    for k, lab in enumerate(cr['month_labels']):
        day = 30 * k + (15 if k < 12 else 2.5)
        a = -2 * math.pi * day / cr['day_divisions']
        r = 73.8
        size = 1.7 if k < 12 else 1.1
        made.append(_text('txt_month_%02d' % k, lab, size, coll, frame_empty, mat,
                          (r * math.cos(a), r * math.sin(a), z), (0.0, 0.0, a - math.pi / 2)))
    # back subsidiary dials (read from the back: flipped about Y, then rotated by psi)
    z = -16.5 - EXTRUDE
    for sd in back['subsidiary']:
        labels = sd.get('labels')
        if not labels:
            continue
        c = spec['axes_world_xy'][sd['centre']]
        tilt = sd.get('sector_tilt_deg', 0.0)
        n = sd['sectors']
        r = sd['radius'] - 0.8
        for k, lab in enumerate(labels):
            if not lab:
                continue
            psi = math.radians(tilt + 360.0 * (k + 0.5) / n)
            x = c[0] - r * math.sin(psi)
            y = c[1] + r * math.cos(psi)
            made.append(_text('txt_%s_%d' % (sd['id'], k), lab, 0.9, coll, frame_empty, mat,
                              (x, y, z), (0.0, math.pi, psi)))
    # glyph check
    chars = sorted({ch for ob in made for ch in ob.data.body if not ch.isspace()})
    ref = glyph_signature(NOTDEF, coll)
    missing = [ch for ch in chars if glyph_signature(ch, coll) == ref]
    bpy.context.view_layer.update()
    info = []
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in made:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3).astype(np.float64)
        M = np.array(ob.matrix_world)
        W = co @ M[:3, :3].T + M[:3, 3]
        ev.to_mesh_clear()
        info.append({'name': ob.name, 'body': ob.data.body, 'extrude': ob.data.extrude,
                     'z': [float(W[:, 2].min()), float(W[:, 2].max())],
                     'xy_min': W[:, :2].min(0).tolist(), 'xy_max': W[:, :2].max(0).tolist(),
                     'xy_hull': W[::max(1, len(W) // 200), :2].tolist()})
    return {'texts': info, 'chars': ''.join(chars), 'missing_glyphs': missing,
            'notdef_signature': str(ref)}
