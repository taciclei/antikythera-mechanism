"""Colour the 7 ancient 'planets' and add labels + a legend to a built am.blend (idempotent).
Run: Blender -b out/am.blend --python-exit-code 1 -P annotate_planets.py -- --save
Labels are FONT objects in collection AM_LABELS, kept upright by a native Copy Location constraint that follows an
anchor Empty parented to the planet's body: no Python driver, so the file still animates without script auto-run."""
import bpy, bmesh, sys
from mathutils import Vector

PLANETS = [  # (marker object, label, linear RGB)
    ('marker_trueSun', 'Soleil',  (1.00, 0.72, 0.06)),
    ('phase_sphere_silver', 'Lune', (0.86, 0.88, 0.95)),
    ('marker_mercury', 'Mercure', (0.08, 0.60, 1.00)),
    ('marker_venus',   'Vénus',   (0.10, 0.85, 0.30)),
    ('marker_mars',    'Mars',    (1.00, 0.08, 0.05)),
    ('marker_jupiter', 'Jupiter', (1.00, 0.42, 0.02)),
    ('marker_saturn',  'Saturne', (0.62, 0.30, 1.00)),
]
LABEL_Z, MOON_LABEL_Z, LABEL_SIZE = 47.3, 60.0, 5.0   # above every cosmos ring / the Dragon Hand; in front of the Moon arm
LEGEND = dict(z=42.25, size=5.5, x_start=-44.0, rows_y=(-93.0, -104.0), title_xy=(-78.0, -93.0),
              rows=[['Soleil', 'Lune', 'Mercure', 'Vénus'], ['Mars', 'Jupiter', 'Saturne']])

def material(name, rgb, emit, rough=0.3):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1.0); bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Emission Color'].default_value = (*rgb, 1.0); bsdf.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = (*rgb, 1.0)
    return m

def main():
    coll = bpy.data.collections.get('AM_LABELS')
    if coll is None:
        coll = bpy.data.collections.new('AM_LABELS'); bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects): bpy.data.objects.remove(ob, do_unlink=True)
    font = bpy.data.fonts[0]; vl = bpy.context.view_layer
    dark = material('AM_label_shadow', (0.01, 0.01, 0.012), 0.0, rough=0.8)
    def text(name, body, size, mat, loc, align_x='LEFT'):
        cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.font = font; cu.size = size
        cu.align_x = align_x; cu.align_y = 'BOTTOM'; cu.materials.append(mat)
        ob = bpy.data.objects.new(name, cu); coll.objects.link(ob); ob.location = loc; vl.update(); return ob
    mats = {}
    for marker_name, name, rgb in PLANETS:
        mk = bpy.data.objects[marker_name]
        mats[name] = material('AM_label_' + name, rgb, 2.0)
        if marker_name == 'phase_sphere_silver':       # the Moon keeps its phase halves; centre = bbox of both halves
            pts = [v.co for n in ('phase_sphere_silver', 'phase_sphere_dark') for v in bpy.data.objects[n].data.vertices]
        else:
            mk.data.materials.clear(); mk.data.materials.append(material('AM_planet_' + name, rgb, 0.8))
            pts = [v.co for v in mk.data.vertices]
        lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
        c = (lo + hi)/2; r = (hi.x - lo.x)/2
        anchor = bpy.data.objects.new('ANCHOR_' + name, None); coll.objects.link(anchor)
        anchor.parent = mk.parent; anchor.matrix_parent_inverse.identity(); anchor.location = c
        anchor.empty_display_size = 0.5; anchor.hide_render = True
        zl = MOON_LABEL_Z if name == 'Lune' else LABEL_Z
        for suffix, mat, dxy, dz in (('', mats[name], (0.0, 0.0), 0.0), ('_shadow', dark, (0.35, -0.35), -0.05)):
            lab = text('LABEL_' + name + suffix, name, LABEL_SIZE, mat, (dxy[0], r + 1.0 + dxy[1], zl + dz), 'CENTER')
            con = lab.constraints.new('COPY_LOCATION')
            con.target = anchor; con.use_x = con.use_y = True; con.use_z = False; con.use_offset = True
            lab.color = (*rgb, 1.0)
    text('LEGEND_title', 'Planètes :', 6.0, dark, (*LEGEND['title_xy'], LEGEND['z']))
    for row, y in zip(LEGEND['rows'], LEGEND['rows_y']):
        x = LEGEND['x_start']
        for name in row:
            me = bpy.data.meshes.new('LEGEND_dot_' + name); bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.8); bm.to_mesh(me); bm.free()
            me.materials.append(mats[name]); [setattr(p, 'use_smooth', True) for p in me.polygons]
            dot = bpy.data.objects.new('LEGEND_dot_' + name, me); coll.objects.link(dot); dot.location = (x + 1.8, y + 1.8, LEGEND['z'] + 1.8)
            t = text('LEGEND_' + name, name, LEGEND['size'], mats[name], (x + 4.8, y, LEGEND['z']))
            x += 4.8 + t.dimensions.x + 6.0
    for o in coll.objects: o['status'] = 'ANNOTATION'
    print('[annotate] labels + legend:', [p[1] for p in PLANETS])

main()
if '--save' in sys.argv:
    bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath, compress=True); print('[annotate] saved', bpy.data.filepath)
