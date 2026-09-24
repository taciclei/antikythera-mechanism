"""Add AM_Controller['explode'] (0..1): every part moves along z so that its z becomes FACTOR*z at explode = 1
(same law as render.explode). Implemented with simple-expression drivers on delta_location.z (no Python drivers).
Parts under B_a (x-axis crank) and B_q (radial Moon-phase arbor) move through their body Empty instead.
Labels move with their planet, the legend with the lower parapegma plate. Idempotent."""
import bpy, sys
import numpy as np
from mathutils import Vector
FACTOR = 3.0
ctl = bpy.data.objects['AM_Controller']
ctl['explode'] = 0.0
ctl.id_properties_ui('explode').update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description='Exploded view (0 = assembled, 1 = z tripled)')
for c in ('crank',): pass
ctl['crank'] = 0.0; ctl.update_tag(); bpy.context.view_layer.update()
SKIP_COLL = {'AM_HELPERS', 'AM_STAGE'}
def in_skip(ob): return any(c.name in SKIP_COLL for c in ob.users_collection)
def centroid_z(ob):
    if ob.type == 'MESH' and len(ob.data.vertices):
        co = np.empty(len(ob.data.vertices)*3, np.float64); ob.data.vertices.foreach_get('co', co)
        return (ob.matrix_world @ Vector(co.reshape(-1, 3).mean(0).tolist())).z
    return ob.matrix_world.translation.z
def remove_driver(ob):
    if ob.animation_data:
        for fc in list(ob.animation_data.drivers):
            if fc.data_path == 'delta_location' and fc.array_index == 2: ob.animation_data.drivers.remove(fc)
    ob.delta_location.z = 0.0
def add_driver(ob, K):
    remove_driver(ob)
    fc = ob.driver_add('delta_location', 2); d = fc.driver; d.type = 'SCRIPTED'
    v = d.variables.new(); v.name = 'e'; v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'OBJECT'; v.targets[0].id = ctl; v.targets[0].data_path = '["explode"]'
    d.expression = f"e*{K:.4f}"
    fc.keyframe_points.clear()
    for m in list(fc.modifiers): fc.modifiers.remove(m)
    assert d.is_simple_expression and d.expression == f"e*{K:.4f}", ob.name
    ob['explode_K'] = K
subtree = {'B_a': [], 'B_q': []}
Kmap = {}
for ob in bpy.data.objects:
    if ob.type not in ('MESH', 'FONT') or in_skip(ob): continue
    p = ob.parent
    while p is not None and p.name not in subtree: p = p.parent
    if p is not None: subtree[p.name].append(ob); remove_driver(ob); continue
    if ob.name.startswith(('LABEL_', 'LEGEND_')): continue
    Kmap[ob.name] = (FACTOR - 1.0)*centroid_z(ob)
for bname, obs in subtree.items():
    zc = float(np.mean([centroid_z(o) for o in obs if o.type == 'MESH']))
    Kmap[bname] = (FACTOR - 1.0)*zc
MARK = {'Soleil': 'marker_trueSun', 'Lune': 'B_q', 'Mercure': 'marker_mercury', 'Vénus': 'marker_venus',
        'Mars': 'marker_mars', 'Jupiter': 'marker_jupiter', 'Saturne': 'marker_saturn'}
para = min((o for o in bpy.data.objects if o.name.startswith('parapegma_') and 'lines' not in o.name),
           key=lambda o: o.matrix_world.translation.y + sum(v.co.y for v in o.data.vertices)/max(1, len(o.data.vertices)))
n = 0
for ob in bpy.data.objects:
    if ob.name in Kmap and ob.type in ('MESH', 'FONT'): add_driver(ob, Kmap[ob.name]); n += 1
    elif ob.name.startswith('LABEL_'):
        planet = ob.name[6:].replace('_shadow', ''); add_driver(ob, Kmap[MARK[planet]]); n += 1
    elif ob.name.startswith('LEGEND_'):
        add_driver(ob, Kmap[para.name]); n += 1
for bname in subtree: add_driver(bpy.data.objects[bname], Kmap[bname]); n += 1
bpy.context.view_layer.update()
print(f'[explode] {n} drivers; legend follows {para.name} (K {Kmap[para.name]:.2f}); B_a K {Kmap["B_a"]:.2f}, B_q K {Kmap["B_q"]:.2f}')
if '--save' in sys.argv:
    bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath, compress=True); print('[explode] saved')
