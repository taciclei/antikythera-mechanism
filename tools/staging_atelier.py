"""ATELIER (daylight workshop) staging for the Antikythera Mechanism scene (Blender 5.2, 1 BU = 1 mm).

"Atelier a la lumiere du jour": the mechanism rests on two wooden battens on a large oak
workbench, pushed against a whitewashed wall pierced by a window.  Warm afternoon sun comes in
through the window (Sun lamp; the wall and its reveal cut the light into a soft-edged patch
on the bench), the sky seen through the opening fills the room (large soft area light in the
window), the room bounces some warm light back from the camera side, and a designed "room"
world (plaster walls, bright window, darker ceiling and bench) is what the bronze reflects in
both engines.  A few quiet period props (papyrus scroll, clay oil lamp, bronze dividers) sit at
the edges of the frames.  AgX colour management, EEVEE ray tracing.

Idempotent: everything lives in the collection AM_ATELIER (datablocks prefixed ATL_), removed and
rebuilt on every run.  The museum staging (collection AM_STAGE) is hidden (render, viewport and
view-layer exclude), never deleted; its world STAGE_world is kept with a fake user.  Nothing of
the mechanism's motion (drivers, B_* bodies, constraints) is touched.  Look v2 (2026-09-25) changes,
in this file only: the AM_bronze node tree is rebuilt (bronze_look: warm golden-brown metal with tone
and roughness variation, patina growing from cavities; the 'patina' driver node is kept), AM_engraving
becomes a dark matte infill (engraving_look), dark floors are added inside the spiral slots
(groove_floors, in AM_ATELIER), and a Bevel modifier 'ATL_bevel' is added to the non-gear bronze parts
(edge_bevels, removed and re-added on every run); AM_Controller["patina"] is set to PATINA; four
cameras CAM_front_close, CAM_back_close, CAM_games_close and CAM_saros_close are created or updated in
AM_HELPERS (next to the build's CAM_* cameras).  The dial content of the film copy (Games pairs,
larger labels, computed Saros glyphs) is made by tools/dial_content.py.

Geometry: the room is built in a local frame (u towards the back wall, v to the left of the
hero camera, z up), azimuth ROOM_AZ = 129.6 deg = mean viewing direction of CAM_front34 (same as
the museum cyclorama).  The bench top is at ground_z = min(lowest z assembled, lowest z exploded
x3) - GAP, so the exploded stack never touches it; the two battens under the back-plate margins
(|x| 76..87, clear of every rotating back pointer) are driven by AM_Controller['explode'] so that
their top always stays 0.2 mm under the back plate (the mechanism never floats).

Usage
  "$BL" -b am_atelier.blend -P staging_atelier.py [-- --save]   (applies in memory, --save writes the file)
  import staging_atelier as st; st.apply(scene)
  st.stage_visibility(mode) before each render
     mode in 'front34' | 'front' | 'back' | 'close_front' | 'close_back' | 'exploded' | 'anim' | 'case' | 'wide'
     'back' / 'close_back' (cameras below the mechanism, looking up at the back dials): the bench,
     wall, props and battens are hidden, a mirrored bench top appears ABOVE the mechanism (the
     machine looks as if it were lying face down on the bench), the lights and the world are
     mirrored in z.
  st.finish(scene, 'eevee'|'cycles') AFTER render.engine_setup(): EEVEE quality settings or the
     Cycles exposure offset.
Cameras must stay on the room side of the back wall (u < WALL_U, see room_uv()).
"""
import math
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

STAGE = 'AM_ATELIER'
PREFIX = 'ATL_'
MUSEUM = 'AM_STAGE'
GAP = 6.0                  # mm between the lowest (exploded) part and the bench top
EXPLODE_FACTOR = 3.0
CENTER = Vector((0.0, -10.0, 0.0))
MECH_Z = 15.0              # mid height of the mechanism (window light aimed here)
MIRROR_Z = 12.0            # 'back' views: lights, world and bench are mirrored about z = MIRROR_Z

# room (local frame: u -> back wall, v -> left of CAM_front34, z up)
ROOM_AZ = 129.6
WALL_U = 430.0             # inner face of the back wall
WALL_T = 160.0             # wall thickness (window reveal)
WALL_HALF_W = 1800.0
WALL_H = 1900.0            # above the bench top
BENCH_FRONT_U = -420.0
BENCH_HALF_W = 1050.0
BENCH_T = 48.0
BENCH_PLANKS = 4
BENCH_HEIGHT = 780.0       # floor = bench top - BENCH_HEIGHT
WIN_W, WIN_H = 600.0, 700.0

# sun: direction TOWARDS the sun, world azimuth / elevation (deg)
SUN_AZ = 166.0
SUN_EL = 40.0
SUN_STRENGTH = 3.2         # W/m2 (irradiance)
SUN_ANGLE = 2.5            # deg: soft edge of the window patch
SUN_K = 5600
SKY_K = 6200
BOUNCE_K = 4800
SKY_L = 2.6                # radiances of the area lights (energy = L * pi * area)
BOUNCE_L = 0.22
CEIL_L = 0.12
WASH_L = 0.85
SKY_SPEC = 0.2

# look / grade
# Khronos PBR Neutral: keeps the hue and saturation of the bronze and of the planet colours up
# to the highlights (AgX turned the polished bronze beige in daylight; Standard clips the window)
VIEW_TRANSFORM = 'Khronos PBR Neutral'
LOOK = 'None'
EXPOSURE = 0.15            # v2: +0.15 EV with the bronze v2 (darker, saturated metal)
# Cycles (true multi-bounce GI from the sunlit bench) comes out ~1.27x brighter than EEVEE at
# the median on the three look cameras (measured 1.21..1.31): finish(scene, 'cycles') compensates
CYCLES_EXPOSURE_OFFSET = -0.35
PATINA = 0.15              # daylight default (museum 0.06).  0.30 was tested with the v1 bronze: at that
                           # noise scale it read as a pinkish speckle and lowered the contrast of the labels
# bronze v2 (bronze_look): the v1 metal (0.92, 0.70, 0.47), roughness 0.30, read as pale beige cardboard
# in daylight; v2 is a warmer, more saturated golden brown with tone and roughness variation
BRONZE_BASE = (0.72, 0.45, 0.19)       # linear (sRGB ~ 0.87, 0.70, 0.48)
BRONZE_LIGHT = (0.80, 0.54, 0.25)
BRONZE_DARK = (0.64, 0.38, 0.155)
BRONZE_METALLIC = 1.0
BRONZE_ROUGH = (0.18, 0.24)            # polished areas .. hand-worked areas (features ~7 mm)
BEVEL_WIDTH = 0.15                     # mm: rounded edges on the non-gear bronze parts (highlights)
PATINA_BROWN = (0.075, 0.038, 0.016)   # cuprite / dark brown crust
PATINA_MID = (0.10, 0.085, 0.05)       # olive-brown
PATINA_GREEN = (0.11, 0.18, 0.13)      # a little verdigris
PATINA_AO_DIST = 1.5                   # mm: cavities where the patina starts
PATINA_CAVITY = 0.55
PATINA_SPREAD = 1.4                    # patina = smoothstep(1 - SPREAD p, + SOFT) of (blotch + CAVITY (1 - AO))
PATINA_SOFT = 0.16
ENGRAVE_INFILL = (0.022, 0.013, 0.007) # dark infill of the engraved lines and letters
GROOVE_FLOOR = (0.030, 0.019, 0.011)   # floor of the spiral slots
GROOVE_FLOOR_Z = -15.3
GROOVE_FLOOR_W = 1.6
EEVEE_SAMPLES = 64

# colours (linear)
PLASTER = (0.70, 0.665, 0.60)
OAK_LIGHT = (0.43, 0.275, 0.135)
OAK_DARK = (0.20, 0.112, 0.050)
WOOD_OLD_LIGHT = (0.20, 0.135, 0.08)
WOOD_OLD_DARK = (0.085, 0.055, 0.034)
TERRACOTTA = (0.46, 0.21, 0.105)
PAPYRUS = (0.46, 0.36, 0.215)


# ----------------------------------------------------------------------------- helpers
def _log(*a):
    print('[atelier]', *a, flush=True)


def _set(obj, attr, value):
    if hasattr(obj, attr):
        try:
            setattr(obj, attr, value)
            return True
        except (TypeError, ValueError, AttributeError) as ex:
            _log('cannot set', attr, ex)
    else:
        _log('missing property', attr)
    return False


def _dir(az_deg, el_deg):
    a, e = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def room_uv(p):
    """World point -> (u, v, z) in the room frame."""
    a = math.radians(ROOM_AZ)
    d = Vector(p) - CENTER
    return (d.x * math.cos(a) + d.y * math.sin(a), -d.x * math.sin(a) + d.y * math.cos(a), d.z)


def room_to_world(u, v, z):
    a = math.radians(ROOM_AZ)
    return Vector((CENTER.x + u * math.cos(a) - v * math.sin(a),
                   CENTER.y + u * math.sin(a) + v * math.cos(a), z))


def _look_at(ob, target, up=(0.0, 0.0, 1.0)):
    f = (Vector(target) - ob.location).normalized()
    upv = Vector(up)
    if abs(f.dot(upv)) > 0.999:
        upv = Vector((0.0, 1.0, 0.0))
    r = f.cross(upv).normalized()
    u = r.cross(f)
    m = Matrix((r, u, -f)).transposed()
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = m.to_euler('XYZ')


def _hide_from_reflections(ob):
    """Room geometry is not seen in glossy rays (Cycles) nor in the EEVEE sphere probes: the
    bronze reflects the designed room world in both engines (same approach as the museum)."""
    ob.visible_glossy = False
    ob.hide_probe_sphere = True


def remove_stage():
    coll = bpy.data.collections.get(STAGE)
    if coll:
        for ob in list(coll.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for c in list(coll.children_recursive):
            bpy.data.collections.remove(c)
        bpy.data.collections.remove(coll)
    for ob in [o for o in bpy.data.objects if o.name.startswith(PREFIX)]:
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in [c for c in bpy.data.collections if c.name.startswith(PREFIX)]:
        bpy.data.collections.remove(c)
    for w in [w for w in bpy.data.worlds if w.name.startswith(PREFIX)]:
        bpy.data.worlds.remove(w)
    for bank in (bpy.data.lights, bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        for idb in [i for i in bank if i.name.startswith(PREFIX) and i.users == 0]:
            bank.remove(idb)


def hide_museum(scene):
    coll = bpy.data.collections.get(MUSEUM)
    if coll is None:
        return
    coll.hide_render = True
    coll.hide_viewport = True
    for vl in scene.view_layers:
        lc = _find_layer_coll(vl.layer_collection, MUSEUM)
        if lc is not None:
            lc.exclude = True
    for ob in bpy.data.objects:          # the build's original lights stay off
        if ob.type == 'LIGHT' and ob.name.startswith('LIGHT_'):
            ob.hide_render = True
            ob.hide_viewport = True


def _find_layer_coll(lc, name):
    if lc.collection.name == name:
        return lc
    for ch in lc.children:
        r = _find_layer_coll(ch, name)
        if r is not None:
            return r
    return None


# ----------------------------------------------------------------------------- ground height
def _world_z_min(ob, dg):
    ev = ob.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        return None
    n = len(me.vertices)
    if n == 0:
        ev.to_mesh_clear()
        return None
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world)
    return float((co @ M[2, :3] + M[2, 3]).min())


def lowest_points(scene, factor=EXPLODE_FACTOR):
    """Lowest z of the mechanism (crank 0), assembled and at explode = 1 (evaluated with the
    explode drivers).  The case walls count (they are shown in the 'case' views)."""
    ctl = bpy.data.objects.get('AM_Controller')
    ad = ctl.animation_data if ctl else None
    saved = (ad.action if ad else None, ctl.get('crank', 0.0), ctl.get('explode', 0.0),
             scene.frame_current) if ctl else None
    res = []
    for e in (0.0, 1.0):
        if ctl is not None:
            if ad:
                ad.action = None
            ctl['crank'] = 0.0
            ctl['explode'] = e
            ctl.update_tag()
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        z = float('inf')
        for ob in scene.objects:
            if ob.type not in ('MESH', 'FONT') or ob.name.startswith((PREFIX, 'STAGE_')):
                continue
            if ob.name.startswith('case_cover'):
                continue
            if ob.hide_render and not ob.name.startswith('case_'):
                continue
            zz = _world_z_min(ob, dg)
            if zz is not None:
                z = min(z, zz)
        res.append(z)
    if ctl is not None:
        action, crank, explode, frame = saved
        if action is not None:
            ctl.animation_data.action = action
        ctl['crank'] = crank
        ctl['explode'] = explode
        ctl.update_tag()
        scene.frame_set(frame)
    bpy.context.view_layer.update()
    return res[0], res[1]


# ----------------------------------------------------------------------------- mesh helpers
def _mesh_from_bm(name, bm, smooth=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)     # lathe poles
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    return me


def _box_bm(bm, x0, x1, y0, y1, z0, z1):
    geom = bmesh.ops.create_cube(bm, size=1.0)
    for v in geom['verts']:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    return geom


def _obj(name, me, coll, mat=None, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new(PREFIX + name, me)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def _box(name, coll, mat, bounds, parent=None, bevel=0.0, seg=2):
    bm = bmesh.new()
    _box_bm(bm, *bounds)
    ob = _obj(name, _mesh_from_bm(PREFIX + name, bm), coll, mat, parent)
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = seg
        md.limit_method = 'ANGLE'
        md.harden_normals = False
    return ob


def _lathe_bm(bm, profile, seg=48, axis='Z', close_ends=True):
    """Revolve a (r, h) profile around the local axis; returns the created verts rings."""
    rings = []
    for (r, h) in profile:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            c, s = r * math.cos(a), r * math.sin(a)
            co = {'Z': (c, s, h), 'X': (h, c, s), 'Y': (c, h, s)}[axis]
            ring.append(bm.verts.new(co))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(seg):
            a, b = rings[i][k], rings[i][(k + 1) % seg]
            c, d = rings[i + 1][(k + 1) % seg], rings[i + 1][k]
            bm.faces.new((a, b, c, d))
    if close_ends:
        if profile[0][0] > 1e-6:
            bm.faces.new(list(reversed(rings[0])))
        if profile[-1][0] > 1e-6:
            bm.faces.new(rings[-1])
    return rings


def _torus_bm(bm, R, r, seg=40, rseg=14, mat=None):
    """Torus in the local XZ plane (axis = Y)."""
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            rr = R + r * math.cos(b)
            ring.append(bm.verts.new((rr * math.cos(a), r * math.sin(b), rr * math.sin(a))))
        rings.append(ring)
    for i in range(seg):
        for j in range(rseg):
            a, b = rings[i][j], rings[i][(j + 1) % rseg]
            c, d = rings[(i + 1) % seg][(j + 1) % rseg], rings[(i + 1) % seg][j]
            bm.faces.new((a, b, c, d))


# ----------------------------------------------------------------------------- materials
def _nodes(mat):
    # (Blender 5.x: new materials always have a node tree)
    nt = mat.node_tree
    pb = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    return nt, nt.nodes, nt.links, pb


def _ramp(N, stops, loc=(0, 0)):
    cr = N.new('ShaderNodeValToRGB')
    cr.location = loc
    els = cr.color_ramp.elements
    while len(els) > len(stops):
        els.remove(els[-1])
    while len(els) < len(stops):
        els.new(0.5)
    for e, (pos, col) in zip(els, stops):
        e.position = pos
        e.color = (*col, 1.0) if len(col) == 3 else col
    return cr


def _math(N, op, a=None, b=None, loc=(0, 0)):
    m = N.new('ShaderNodeMath')
    m.operation = op
    m.location = loc
    if a is not None and not hasattr(a, 'is_linked'):
        m.inputs[0].default_value = a
    if b is not None and not hasattr(b, 'is_linked'):
        m.inputs[1].default_value = b
    return m


def _mix_rgb(N, L, fac, a, b, blend='MIX', loc=(0, 0)):
    m = N.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = blend
    m.location = loc
    for sock, val in ((m.inputs['Factor'], fac), (m.inputs['A'], a), (m.inputs['B'], b)):
        if hasattr(val, 'node'):
            L.new(val, sock)
        elif isinstance(val, (tuple, list)):
            sock.default_value = (*val, 1.0) if len(val) == 3 else val
        else:
            sock.default_value = val
    return m


def wood_material(name, light, dark, ring_mm=4.5, pith_depth=260.0, plank_axis='Y',
                  rough=(0.52, 0.68), bump=0.22, pores=True, world_coords=False):
    """Flat-sawn wood: growth rings of a log whose pith runs along the grain axis below the
    board (Wave RINGS on Object coordinates, distorted), latewood darker and slightly raised,
    fine pores stretched along the grain, per-object random tone (Object Info Random)."""
    mat = bpy.data.materials.new(PREFIX + name)
    nt, N, L, pb = _nodes(mat)
    tc = N.new('ShaderNodeTexCoord')
    oi = N.new('ShaderNodeObjectInfo')
    # objects whose scale is animated (battens) use world positions: no stretched grain
    coord = N.new('ShaderNodeNewGeometry').outputs['Position'] if world_coords else tc.outputs['Object']
    # per-object pith offset: across the board +-60 mm, below by pith_depth
    rnd = _math(N, 'MULTIPLY_ADD', None, 120.0)
    rnd.inputs[2].default_value = -60.0
    L.new(oi.outputs['Random'], rnd.inputs[0])
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(coord, sep.inputs['Vector'])
    across, along = ('X', 'Y') if plank_axis == 'Y' else ('Y', 'X')
    ax = _math(N, 'ADD')
    L.new(sep.outputs[across], ax.inputs[0])
    L.new(rnd.outputs[0], ax.inputs[1])
    az = _math(N, 'ADD', None, pith_depth)
    L.new(sep.outputs['Z'], az.inputs[0])
    al = _math(N, 'MULTIPLY', None, 0.035)          # compress along the grain
    L.new(sep.outputs[along], al.inputs[0])
    al2 = _math(N, 'ADD')                             # decorrelate objects along the grain
    L.new(al.outputs[0], al2.inputs[0])
    rnd2 = _math(N, 'MULTIPLY', None, 500.0)
    L.new(oi.outputs['Random'], rnd2.inputs[0])
    L.new(rnd2.outputs[0], al2.inputs[1])
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(ax.outputs[0], comb.inputs['X'])
    L.new(al2.outputs[0], comb.inputs['Y'])
    L.new(az.outputs[0], comb.inputs['Z'])
    wave = N.new('ShaderNodeTexWave')
    wave.wave_type = 'RINGS'
    wave.rings_direction = 'Y'
    wave.wave_profile = 'SAW'
    wave.inputs['Scale'].default_value = 2 * math.pi / (20.0 * ring_mm)
    wave.inputs['Distortion'].default_value = 5.0
    wave.inputs['Detail'].default_value = 3.0
    wave.inputs['Detail Scale'].default_value = 1.2
    wave.inputs['Detail Roughness'].default_value = 0.55
    L.new(comb.outputs['Vector'], wave.inputs['Vector'])
    # latewood = the last ~30 % of each ring
    late = N.new('ShaderNodeMapRange')
    late.interpolation_type = 'SMOOTHSTEP'
    late.inputs['From Min'].default_value = 0.55
    late.inputs['From Max'].default_value = 0.95
    L.new(wave.outputs['Fac'], late.inputs['Value'])
    # large-scale tone variation (+ per object)
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.004
    nz.inputs['Detail'].default_value = 3.0
    L.new(comb.outputs['Vector'], nz.inputs['Vector'])
    tone = _ramp(N, [(0.3, tuple(c * 0.86 for c in light)), (0.7, tuple(min(1.0, c * 1.08) for c in light))])
    L.new(nz.outputs['Fac'], tone.inputs['Fac'])
    col = _mix_rgb(N, L, late.outputs['Result'], tone.outputs['Color'], dark)
    colf = col
    if pores:
        # pores / fibres: fine noise stretched along the grain
        pv = N.new('ShaderNodeMapping')
        pv.inputs['Scale'].default_value = (1.0, 0.06, 1.0) if plank_axis == 'Y' else (0.06, 1.0, 1.0)
        L.new(coord, pv.inputs['Vector'])
        pn = N.new('ShaderNodeTexNoise')
        pn.inputs['Scale'].default_value = 1.6
        pn.inputs['Detail'].default_value = 6.0
        pn.inputs['Roughness'].default_value = 0.65
        L.new(pv.outputs['Vector'], pn.inputs['Vector'])
        pr = N.new('ShaderNodeMapRange')
        pr.inputs['From Min'].default_value = 0.35
        pr.inputs['From Max'].default_value = 0.65
        pr.inputs['To Min'].default_value = 0.0
        pr.inputs['To Max'].default_value = 1.0
        L.new(pn.outputs['Fac'], pr.inputs['Value'])
        pf = _math(N, 'MULTIPLY', None, 0.28)
        L.new(pr.outputs['Result'], pf.inputs[0])
        colf = _mix_rgb(N, L, pf.outputs[0], col.outputs['Result'], tuple(c * 0.55 for c in dark))
        pore_out = pr.outputs['Result']
    else:
        pore_out = None
    L.new(colf.outputs['Result'], pb.inputs['Base Color'])
    # roughness: latewood a bit glossier (oiled, worn)
    rr = N.new('ShaderNodeMapRange')
    rr.inputs['To Min'].default_value = rough[1]
    rr.inputs['To Max'].default_value = rough[0]
    L.new(late.outputs['Result'], rr.inputs['Value'])
    L.new(rr.outputs['Result'], pb.inputs['Roughness'])
    pb.inputs['Specular IOR Level'].default_value = 0.45
    # bump: raised latewood (weathered grain) + pores
    bmp = N.new('ShaderNodeBump')
    bmp.inputs['Strength'].default_value = bump
    bmp.inputs['Distance'].default_value = 0.25
    if pore_out is not None:
        hsum = _math(N, 'MULTIPLY_ADD', None, -0.35)
        L.new(pore_out, hsum.inputs[0])
        L.new(late.outputs['Result'], hsum.inputs[2])
        L.new(hsum.outputs[0], bmp.inputs['Height'])
    else:
        L.new(late.outputs['Result'], bmp.inputs['Height'])
    L.new(bmp.outputs['Normal'], pb.inputs['Normal'])
    return mat


def plaster_material():
    mat = bpy.data.materials.new(PREFIX + 'plaster')
    nt, N, L, pb = _nodes(mat)
    tc = N.new('ShaderNodeTexCoord')
    n1 = N.new('ShaderNodeTexNoise')           # blotches of the whitewash
    n1.inputs['Scale'].default_value = 0.0035
    n1.inputs['Detail'].default_value = 5.0
    n1.inputs['Roughness'].default_value = 0.6
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    col = _ramp(N, [(0.35, tuple(c * 0.90 for c in PLASTER)), (0.65, PLASTER)])
    L.new(n1.outputs['Fac'], col.inputs['Fac'])
    L.new(col.outputs['Color'], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = 0.93
    pb.inputs['Specular IOR Level'].default_value = 0.3
    n2 = N.new('ShaderNodeTexNoise')           # trowel undulation + grit
    n2.inputs['Scale'].default_value = 0.02
    n2.inputs['Detail'].default_value = 10.0
    n2.inputs['Roughness'].default_value = 0.62
    L.new(tc.outputs['Object'], n2.inputs['Vector'])
    bmp = N.new('ShaderNodeBump')
    bmp.inputs['Strength'].default_value = 0.35
    bmp.inputs['Distance'].default_value = 1.5
    L.new(n2.outputs['Fac'], bmp.inputs['Height'])
    L.new(bmp.outputs['Normal'], pb.inputs['Normal'])
    return mat


def simple_material(name, color, rough=0.7, noise_amt=0.12, noise_scale=0.08, bump=0.15, metallic=0.0):
    mat = bpy.data.materials.new(PREFIX + name)
    nt, N, L, pb = _nodes(mat)
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = noise_scale
    nz.inputs['Detail'].default_value = 6.0
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = _ramp(N, [(0.3, tuple(c * (1 - noise_amt) for c in color)),
                   (0.7, tuple(min(1.0, c * (1 + noise_amt)) for c in color))])
    L.new(nz.outputs['Fac'], cr.inputs['Fac'])
    L.new(cr.outputs['Color'], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = rough
    pb.inputs['Metallic'].default_value = metallic
    if bump > 0:
        n2 = N.new('ShaderNodeTexNoise')
        n2.inputs['Scale'].default_value = noise_scale * 12
        n2.inputs['Detail'].default_value = 8.0
        L.new(tc.outputs['Object'], n2.inputs['Vector'])
        bmp = N.new('ShaderNodeBump')
        bmp.inputs['Strength'].default_value = bump
        bmp.inputs['Distance'].default_value = 0.4
        L.new(n2.outputs['Fac'], bmp.inputs['Height'])
        L.new(bmp.outputs['Normal'], pb.inputs['Normal'])
    return mat


def papyrus_material():
    mat = simple_material('papyrus', PAPYRUS, rough=0.82, noise_amt=0.14, noise_scale=0.05, bump=0.1)
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    pb = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    tc = next(n for n in N if n.type == 'TEX_COORD')
    cr = next(n for n in N if n.type == 'VALTORGB')
    # fibres: fine bands along the scroll axis (local Y) crossed by a weaker layer
    wv = N.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = 0.35
    wv.inputs['Distortion'].default_value = 6.0
    wv.inputs['Detail'].default_value = 4.0
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    fm = _math(N, 'MULTIPLY', None, 0.18)
    L.new(wv.outputs['Fac'], fm.inputs[0])
    mix = _mix_rgb(N, L, fm.outputs[0], cr.outputs['Color'], tuple(c * 0.7 for c in PAPYRUS))
    L.new(mix.outputs['Result'], pb.inputs['Base Color'])
    return mat


def exterior_material():
    """What the window shows: a bright hazy Mediterranean afternoon (sky gradient, a band of
    distant hills).  Emission only; seen by camera rays only."""
    mat = bpy.data.materials.new(PREFIX + 'exterior')
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Generated'], sep.inputs['Vector'])
    sky = N.new('ShaderNodeMapRange')
    sky.inputs['From Min'].default_value = 0.35
    sky.inputs['From Max'].default_value = 1.0
    L.new(sep.outputs['Z'], sky.inputs['Value'])
    skycol = _ramp(N, [(0.0, (1.0, 0.93, 0.80)), (1.0, (0.60, 0.74, 1.0))])
    L.new(sky.outputs['Result'], skycol.inputs['Fac'])
    # hills: top edge = 0.38 + noise(x)
    nz = N.new('ShaderNodeTexNoise')
    nz.noise_dimensions = '1D'
    nz.inputs['Scale'].default_value = 3.0
    nz.inputs['Detail'].default_value = 4.0
    L.new(sep.outputs['X'], nz.inputs['W'])
    edge = _math(N, 'MULTIPLY_ADD', None, 0.22)
    edge.inputs[2].default_value = 0.26
    L.new(nz.outputs['Fac'], edge.inputs[0])
    hill = _math(N, 'LESS_THAN')
    L.new(sep.outputs['Z'], hill.inputs[0])
    L.new(edge.outputs[0], hill.inputs[1])
    col = _mix_rgb(N, L, hill.outputs[0], skycol.outputs['Color'], (0.55, 0.58, 0.42))
    em = N.new('ShaderNodeEmission')
    L.new(col.outputs['Result'], em.inputs['Color'])
    st = _math(N, 'MULTIPLY_ADD', None, -1.6)
    st.inputs[2].default_value = 3.6
    L.new(hill.outputs[0], st.inputs[0])
    L.new(st.outputs[0], em.inputs['Strength'])
    L.new(em.outputs['Emission'], out.inputs['Surface'])
    return mat


# ----------------------------------------------------------------------------- room
def window_centre():
    """(v, z) of the window centre: where the ray from the mechanism centre towards the sun
    crosses the middle of the wall thickness."""
    s = _dir(SUN_AZ - ROOM_AZ, SUN_EL)            # in the room frame
    t = (WALL_U + WALL_T / 2) / s.x
    return s.y * t, MECH_Z + s.z * t


def build_room(coll, top_z):
    room = bpy.data.objects.new(PREFIX + 'room', None)
    coll.objects.link(room)
    room.location = (CENTER.x, CENTER.y, 0.0)
    room.rotation_euler = (0.0, 0.0, math.radians(ROOM_AZ))
    room.empty_display_size = 100
    floor_z = top_z - BENCH_HEIGHT
    oak = wood_material('oak_bench', OAK_LIGHT, OAK_DARK)
    old = wood_material('wood_old', WOOD_OLD_LIGHT, WOOD_OLD_DARK, ring_mm=3.0, pith_depth=180.0,
                        plank_axis='Y', rough=(0.6, 0.78), bump=0.3)
    plaster = plaster_material()
    obs = {}
    # --- bench top: planks along v, tiny gaps and height differences
    depth = WALL_U - BENCH_FRONT_U
    pw = depth / BENCH_PLANKS
    rng = np.random.default_rng(7)
    for i in range(BENCH_PLANKS):
        u0 = BENCH_FRONT_U + i * pw + (0.0 if i == 0 else 0.8)
        u1 = BENCH_FRONT_U + (i + 1) * pw - (0.0 if i == BENCH_PLANKS - 1 else 0.8)
        dz = float(rng.uniform(-0.35, 0.25)) if i else 0.0
        ob = _box('bench_plank_%d' % i, coll, oak, (u0, u1, -BENCH_HALF_W, BENCH_HALF_W,
                                                     top_z - BENCH_T, top_z + dz), room, bevel=1.6)
        _hide_from_reflections(ob)
        obs['plank%d' % i] = ob
    # --- legs and aprons
    for su in (-1, 1):
        for sv in (-1, 1):
            uc = (BENCH_FRONT_U + 60) if su < 0 else (WALL_U - 60)
            vc = sv * (BENCH_HALF_W - 70)
            ob = _box('bench_leg_%d%d' % (su > 0, sv > 0), coll, old,
                      (uc - 40, uc + 40, vc - 40, vc + 40, floor_z, top_z - BENCH_T), room, bevel=2.0)
            _hide_from_reflections(ob)
    for su in (-1, 1):
        uc = (BENCH_FRONT_U + 60) if su < 0 else (WALL_U - 60)
        ob = _box('bench_apron_%d' % (su > 0), coll, old,
                  (uc - 18, uc + 18, -BENCH_HALF_W + 70, BENCH_HALF_W - 70,
                   top_z - BENCH_T - 110, top_z - BENCH_T), room, bevel=1.5)
        _hide_from_reflections(ob)
    # --- floor (terracotta tiles)
    fm = bpy.data.materials.new(PREFIX + 'floor')
    nt, N, L, pb = _nodes(fm)
    tc = N.new('ShaderNodeTexCoord')
    br = N.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0 / 600.0
    br.inputs['Color1'].default_value = (*TERRACOTTA, 1.0)
    br.inputs['Color2'].default_value = (*(c * 0.75 for c in TERRACOTTA), 1.0)
    br.inputs['Mortar'].default_value = (0.30, 0.26, 0.21, 1.0)
    br.inputs['Mortar Size'].default_value = 0.012
    br.offset = 0.5
    br.squash = 1.0
    L.new(tc.outputs['Object'], br.inputs['Vector'])
    L.new(br.outputs['Color'], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = 0.85
    ob = _box('floor', coll, fm, (-3000, 3000, -3000, 3000, floor_z - 20, floor_z), room)
    _hide_from_reflections(ob)
    # --- back wall with the window opening (4 blocks around the hole)
    vc, zc = window_centre()
    wv0, wv1 = vc - WIN_W / 2, vc + WIN_W / 2
    wz0, wz1 = zc - WIN_H / 2, zc + WIN_H / 2
    u0, u1 = WALL_U, WALL_U + WALL_T
    ztop = top_z + WALL_H
    parts = {
        'wall_right': (u0, u1, -WALL_HALF_W, wv0, floor_z, ztop),
        'wall_left': (u0, u1, wv1, WALL_HALF_W, floor_z, ztop),
        'wall_below': (u0, u1, wv0, wv1, floor_z, wz0),
        'wall_above': (u0, u1, wv0, wv1, wz1, ztop),
    }
    for name, b in parts.items():
        ob = _box(name, coll, plaster, b, room, bevel=6.0, seg=3)
        _hide_from_reflections(ob)
        obs[name] = ob
    for name, b in (('wall_side_L', (BENCH_FRONT_U - 2600, u0, WALL_HALF_W - 200, WALL_HALF_W - 40, floor_z, ztop)),
                    ('wall_side_R', (BENCH_FRONT_U - 2600, u0, -WALL_HALF_W + 40, -WALL_HALF_W + 200, floor_z, ztop))):
        ob = _box(name, coll, plaster, b, room)
        _hide_from_reflections(ob)
        obs[name] = ob
    # sill (protrudes into the room), lintel beam
    ob = _box('window_sill', coll, old, (u0 - 28, u1 + 10, wv0 - 40, wv1 + 40, wz0 - 22, wz0 + 4), room, bevel=2.0)
    _hide_from_reflections(ob)
    ob = _box('window_lintel', coll, old, (u0 - 14, u0 + 90, wv0 - 110, wv1 + 110, wz1, wz1 + 70), room, bevel=2.0)
    _hide_from_reflections(ob)
    # two shutters opened against the inner face of the wall (3 boards + 2 battens each)
    for side, hinge_v, sgn in (('R', wv0, -1), ('L', wv1, 1)):
        leaf_w = WIN_W / 2 - 4
        bm = bmesh.new()
        for k in range(3):
            b0 = k * leaf_w / 3 + 1.0
            b1 = (k + 1) * leaf_w / 3 - 1.0
            _box_bm(bm, -22, 0, b0, b1, wz0 + 6, wz1 - 6)
        for zz in (wz0 + 90, wz1 - 90):
            _box_bm(bm, -34, -22, 20, leaf_w - 20, zz - 30, zz + 30)
        me = _mesh_from_bm(PREFIX + 'shutter_' + side, bm)
        ob = _obj('shutter_' + side, me, coll, old, room)
        # leaf hinged at (u0, hinge_v), opened ~100 deg: lies almost flat against the wall
        # local +y = along the leaf, local -x = towards the room; ~8 deg off the wall
        ang = math.radians(8.0)
        ob.location = (u0 - 2, hinge_v + sgn * 4, 0.0)
        ob.rotation_euler = (0.0, 0.0, ang if sgn > 0 else -ang)
        if sgn < 0:
            ob.scale = (1.0, -1.0, 1.0)
        _hide_from_reflections(ob)
    # outside view (camera rays only)
    em = exterior_material()
    bm = bmesh.new()
    geom = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in geom['verts']:
        x, y = v.co.x, v.co.y
        v.co = Vector((0.0, x * 5200.0, y * 3400.0))
    me = _mesh_from_bm(PREFIX + 'exterior', bm)
    ob = _obj('exterior', me, coll, em, room, loc=(u1 + 1400.0, vc, zc + 600.0))
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.visible_diffuse = ob.visible_glossy = ob.visible_shadow = False
    ob.visible_transmission = ob.visible_volume_scatter = False
    ob.hide_probe_sphere = ob.hide_probe_volume = ob.hide_probe_plane = True
    obs['exterior'] = ob
    obs['room'] = room
    return obs, oak, old


def build_back_bench(coll, top_z, oak):
    """'back' views only: a copy of the bench top mirrored above the mechanism."""
    zb = 2 * MIRROR_Z - top_z
    room = bpy.data.objects.new(PREFIX + 'room_back', None)
    coll.objects.link(room)
    room.location = (CENTER.x, CENTER.y, 0.0)
    room.rotation_euler = (0.0, 0.0, math.radians(ROOM_AZ))
    obs = [room]
    depth = WALL_U - BENCH_FRONT_U
    pw = depth / BENCH_PLANKS
    for i in range(BENCH_PLANKS):
        u0 = BENCH_FRONT_U + i * pw + (0.0 if i == 0 else 0.8)
        u1 = BENCH_FRONT_U + (i + 1) * pw - (0.0 if i == BENCH_PLANKS - 1 else 0.8)
        ob = _box('back_plank_%d' % i, coll, oak, (u0, u1, -BENCH_HALF_W, BENCH_HALF_W, zb, zb + BENCH_T),
                  room, bevel=1.6)
        _hide_from_reflections(ob)
        ob['atl_only'] = 'back'
        obs.append(ob)
    return obs


# ----------------------------------------------------------------------------- battens
def build_battens(coll, top_z, oak):
    """Two battens under the back-plate margins; their height follows the explode slider so
    that their top stays 0.2 mm under the back plate for every explode value."""
    bp = bpy.data.objects.get('back_plate')
    k = -31.5
    z0 = -16.5
    if bp is not None:
        z0 = _world_z_min(bp, bpy.context.evaluated_depsgraph_get()) or z0
        k = float(bp.get('explode_K', k))
    ctl = bpy.data.objects.get('AM_Controller')
    obs = []
    for sx in (-1, 1):
        x0, x1 = (76.0, 87.0) if sx > 0 else (-87.0, -76.0)
        bm = bmesh.new()
        _box_bm(bm, x0, x1, -150.0, 130.0, 0.0, 1.0)
        me = _mesh_from_bm(PREFIX + 'batten_%s' % ('R' if sx > 0 else 'L'), bm)
        ob = _obj('batten_%s' % ('R' if sx > 0 else 'L'), me, coll, oak)
        ob.location = (0.0, 0.0, top_z)
        h0 = z0 - 0.2 - top_z
        ob.scale = (1.0, 1.0, h0)
        if ctl is not None:
            fc = ob.driver_add('scale', 2)
            d = fc.driver
            d.type = 'SCRIPTED'
            v = d.variables.new()
            v.name = 'e'
            v.type = 'SINGLE_PROP'
            v.targets[0].id_type = 'OBJECT'
            v.targets[0].id = ctl
            v.targets[0].data_path = '["explode"]'
            d.expression = '%.4f+e*%.4f' % (h0, k)
            fc.keyframe_points.clear()
            for m in list(fc.modifiers):
                fc.modifiers.remove(m)
        _hide_from_reflections(ob)
        obs.append(ob)
    return obs


# ----------------------------------------------------------------------------- props
def build_props(coll, top_z, room):
    """Quiet period props at the edges of the frames (room frame coordinates)."""
    obs = []
    terra = simple_material('terracotta', TERRACOTTA, rough=0.72, noise_amt=0.12, noise_scale=0.06, bump=0.25)
    soot = simple_material('soot', (0.03, 0.025, 0.02), rough=0.9, noise_amt=0.0, bump=0.0)
    # --- clay oil lamp (lathe body, nozzle flattened in z, ring handle), unlit
    prof = [(0.0, 0.0), (15.0, 0.0), (22.0, 1.0), (27.0, 4.0), (29.0, 7.5), (28.0, 10.5),
            (24.0, 13.0), (19.0, 13.6), (13.0, 12.6), (7.0, 12.2), (5.5, 12.8), (4.5, 11.5), (0.0, 11.0)]
    nprof = [(9.0, 16.0), (8.6, 30.0), (8.0, 42.0), (7.2, 47.0), (5.0, 50.0), (0.0, 51.0)]
    bm = bmesh.new()
    _lathe_bm(bm, prof, seg=48)
    rings = _lathe_bm(bm, nprof, seg=24, axis='X', close_ends=True)
    for ring in rings:
        for v in ring:
            v.co.z = 7.0 + v.co.z * 0.72
    tstart = len(bm.verts)
    _torus_bm(bm, 8.0, 2.6)
    bm.verts.ensure_lookup_table()
    for v in bm.verts[tstart:]:
        v.co.x -= 31.0
        v.co.z += 9.0
    lamp_me = _mesh_from_bm(PREFIX + 'oil_lamp', bm, smooth=True)
    lamp = _obj('oil_lamp', lamp_me, coll, terra, room)
    # wick hole + filling hole (dark discs)
    bm = bmesh.new()
    _lathe_bm(bm, [(0.0, 0.0), (3.4, 0.0)], seg=20)
    me_h = _mesh_from_bm(PREFIX + 'lamp_holes', bm)
    hole1 = _obj('lamp_wick_hole', me_h, coll, soot, lamp, loc=(43.0, 0.0, 13.5))
    hole2 = _obj('lamp_fill_hole', me_h.copy(), coll, soot, lamp, loc=(0.0, 0.0, 11.3))
    hole2.scale = (1.25, 1.25, 1.0)
    lamp.location = (390.0, -250.0, top_z)
    lamp.rotation_euler = (0.0, 0.0, math.radians(215.0))
    obs += [lamp, hole1, hole2]
    # --- papyrus scroll: spiral ribbon + an unrolled tail lying on the bench
    pap = papyrus_material()
    r0, r1, turns, length = 3.0, 13.0, 7.0, 230.0
    pts = []
    n = int(turns * 64)
    th_end = turns * 2 * math.pi
    for i in range(n + 1):
        th = th_end * i / n
        r = r0 + (r1 - r0) * th / th_end
        a = th - th_end - math.pi / 2          # the outer end at the bottom of the roll
        pts.append((r * math.cos(a), r * math.sin(a)))
    # tail: from the bottom of the roll, along +x on the bench, slight lift near the roll
    xe, ze = pts[-1]
    for i in range(1, 13):
        t = i / 12
        pts.append((xe + 55.0 * t, ze))
    bm = bmesh.new()
    rows = []
    for (x, z) in pts:
        rows.append((bm.verts.new((x, -length / 2, z)), bm.verts.new((x, length / 2, z))))
    for i in range(len(rows) - 1):
        a0, a1 = rows[i]
        b0, b1 = rows[i + 1]
        bm.faces.new((a0, b0, b1, a1))
    me = _mesh_from_bm(PREFIX + 'papyrus', bm, smooth=True)
    scroll = _obj('papyrus', me, coll, pap, room)
    sm = scroll.modifiers.new('thick', 'SOLIDIFY')
    sm.thickness = 0.35
    sm.offset = 0.0
    scroll.location = (340.0, 290.0, top_z + r1 + 0.35)
    scroll.rotation_euler = (0.0, 0.0, math.radians(-78.0))
    obs.append(scroll)
    # --- bronze dividers lying on the bench (two tapered legs, pivot boss)
    bronze = bpy.data.materials.get('AM_bronze') or simple_material('bronze_tool', (0.8, 0.6, 0.4), 0.35, metallic=1.0)
    bm = bmesh.new()
    for ang in (-11.0, 11.0):
        b2 = bmesh.new()
        _lathe_bm(b2, [(0.0, -2.0), (2.6, 0.0), (2.4, 20.0), (1.6, 80.0), (0.6, 118.0), (0.0, 121.0)], seg=16,
                  axis='X')
        m = Matrix.Rotation(math.radians(ang), 4, 'Z')
        for v in b2.verts:
            v.co = m @ v.co
        tmp = bpy.data.meshes.new('tmp')
        b2.to_mesh(tmp)
        b2.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    b2 = bmesh.new()
    _lathe_bm(b2, [(0.0, -3.2), (5.5, -3.2), (6.0, -1.5), (6.0, 1.5), (5.5, 3.2), (0.0, 3.2)], seg=32)
    tmp = bpy.data.meshes.new('tmp')
    b2.to_mesh(tmp)
    b2.free()
    bm.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    me = _mesh_from_bm(PREFIX + 'dividers', bm, smooth=True)
    div = _obj('dividers', me, coll, bronze, room)
    div.location = (210.0, 262.0, top_z + 2.7)
    div.rotation_euler = (0.0, 0.0, math.radians(-150.0))
    obs.append(div)
    for ob in obs:
        _hide_from_reflections(ob)
    return obs


# ----------------------------------------------------------------------------- lights
def _light(coll, key, kind, energy, kelvin, **kw):
    name = PREFIX + key
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.use_temperature = True
    ld.temperature = kelvin
    ld.color = (1.0, 1.0, 1.0)
    ld.use_shadow = True
    if kind == 'AREA':
        ld.shape = 'RECTANGLE'
        ld.size, ld.size_y = kw['size']
        ld.spread = math.pi
    elif kind == 'SUN':
        ld.angle = math.radians(kw.get('angle', SUN_ANGLE))
    ob = bpy.data.objects.new(name, ld)
    coll.objects.link(ob)
    ob.visible_camera = False
    ob['atl_only'] = kw.get('only', '')
    return ob


def _mirrored(M):
    """A light transform mirrored about z = MIRROR_Z (for the 'back' rig)."""
    S = Matrix.Identity(4)
    S[2][2] = -1.0
    S[2][3] = 2 * MIRROR_Z
    # a mirror flips handedness: flip the local X axis back so the matrix stays a rotation
    F = Matrix.Identity(4)
    F[0][0] = -1.0
    return S @ M @ F


def build_lights(coll, top_z):
    obs = {}
    sun_dir = _dir(SUN_AZ, SUN_EL)
    vc, zc = window_centre()
    # the sun through the window
    sun = _light(coll, 'sun', 'SUN', SUN_STRENGTH, SUN_K)
    sun.rotation_mode = 'QUATERNION'
    sun.rotation_quaternion = (-sun_dir).to_track_quat('-Z', 'Y')
    sun.rotation_mode = 'XYZ'
    obs['sun'] = sun
    # the sky seen through the opening: an area light filling the window, facing the room
    sky = _light(coll, 'window_sky', 'AREA', 0.0, SKY_K, size=(WIN_W - 10, WIN_H - 10))
    sky.location = room_to_world(WALL_U - 2.0, vc, zc)
    _look_at(sky, room_to_world(0.0, vc * 0.35, top_z))
    sky.data.energy = SKY_L * math.pi * sky.data.size * sky.data.size_y
    sky.data.specular_factor = SKY_SPEC        # the metal shows a glint of the window, not a flat sheet
    obs['window_sky'] = sky
    # warm bounce from the sunlit room behind the camera (large, soft, weak)
    bounce = _light(coll, 'bounce', 'AREA', 0.0, BOUNCE_K, size=(1600.0, 700.0))
    bounce.location = room_to_world(-900.0, -150.0, top_z + 380.0)
    _look_at(bounce, room_to_world(0.0, 0.0, MECH_Z))
    bounce.data.energy = BOUNCE_L * math.pi * 1600.0 * 700.0
    bounce.data.specular_factor = 0.0          # fills light wood, patina and labels, not the metal
    obs['bounce'] = bounce
    # the sunlit bench and floor bounce light onto the back wall (diffuse only, walls only)
    walls = bpy.data.collections.new(PREFIX + 'walls_only')
    for ob in coll.all_objects:
        if ob.name.startswith(PREFIX + 'wall_'):
            walls.objects.link(ob)
    wash = _light(coll, 'wall_wash', 'AREA', 0.0, 4000, size=(2600.0, 500.0))
    wash.location = room_to_world(-500.0, 0.0, top_z + 60.0)
    _look_at(wash, room_to_world(WALL_U, 0.0, top_z + 500.0))
    wash.data.energy = WASH_L * math.pi * 2600.0 * 500.0
    wash.data.specular_factor = 0.0
    wash.light_linking.receiver_collection = walls
    obs['wall_wash'] = wash
    # soft light from the (whitewashed) ceiling
    ceil = _light(coll, 'ceiling', 'AREA', 0.0, 5200, size=(1400.0, 1400.0))
    ceil.location = (CENTER.x, CENTER.y, top_z + 1100.0)
    _look_at(ceil, (CENTER.x, CENTER.y, 0.0), up=(0.0, 1.0, 0.0))
    ceil.data.energy = CEIL_L * math.pi * 1400.0 * 1400.0
    ceil.data.specular_factor = 0.0
    obs['ceiling'] = ceil
    # back rig: the same lights mirrored about z = MIRROR_Z (matrices must be evaluated first)
    bpy.context.view_layer.update()
    for key in [k for k in obs if k != 'wall_wash']:
        src = obs[key]
        ob = _light(coll, key + '_back', src.data.type, src.data.energy, src.data.temperature,
                    size=(getattr(src.data, 'size', 0), getattr(src.data, 'size_y', 0)),
                    angle=math.degrees(getattr(src.data, 'angle', math.radians(SUN_ANGLE))), only='back')
        ob.data.specular_factor = src.data.specular_factor
        ob.matrix_world = _mirrored(src.matrix_world)
        obs[key + '_back'] = ob
    for key, ob in obs.items():
        if not key.endswith('_back'):
            ob['atl_only'] = ob.get('atl_only', '') or 'front'
    return obs


# ----------------------------------------------------------------------------- world
def _lobe(N, L, vec_out, direction, deg_out, deg_in, gain, colour, base_out):
    """base + gain * colour * smoothstep(cos(deg_out), cos(deg_in), dot(d, direction))."""
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = Vector(direction).normalized()
    L.new(vec_out, dot.inputs[0])
    ss = N.new('ShaderNodeMapRange')
    ss.interpolation_type = 'SMOOTHSTEP'
    ss.inputs['From Min'].default_value = math.cos(math.radians(deg_out))
    ss.inputs['From Max'].default_value = math.cos(math.radians(deg_in))
    L.new(dot.outputs['Value'], ss.inputs['Value'])
    g = _math(N, 'MULTIPLY', None, gain)
    L.new(ss.outputs['Result'], g.inputs[0])
    return _mix_rgb(N, L, g.outputs[0], base_out, colour, blend='ADD')


# world radiances (linear) of the designed room, seen by reflections / world lighting only
W_BENCH = (0.050, 0.036, 0.024)
W_WALL = (0.300, 0.282, 0.252)      # v2 (bronze v2): x1.5, the darker saturated bronze reflects it
W_CEIL = (0.208, 0.190, 0.162)      # v2: x1.6 (the back views reflect the mirrored ceiling)
BACK_WORLD_GAIN = 1.3               # v2: reflected room x1.3 in the 'back' rig (node 'refl_gain')
W_WINDOW_BROAD = 0.14       # wide soft lobe around the window (gradient on flat bronze)
W_WINDOW_CORE = 0.5         # the bright opening itself
W_ROOM_BACK = 0.12          # sunlit part of the room behind the camera
W_CEIL_GLOW = 0.12          # ceiling above the sunlit bench (sun patch bounced upwards)


def build_world(scene, top_z):
    """Camera rays: plaster.  Other rays: a designed room around the bench (bright window in
    the direction of the real one, whitewashed walls in shade, dark wooden ceiling, bench
    below) so that the bronze reflects a daylight interior in both engines (the room geometry
    itself is invisible to glossy rays / sphere probes).  A value node 'mirror' (1 / -1)
    flips it in z for the back views."""
    w = bpy.data.worlds.new(PREFIX + 'world')
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    out = N.new('ShaderNodeOutputWorld')
    tc = N.new('ShaderNodeTexCoord')
    mirror = N.new('ShaderNodeValue')
    mirror.name = mirror.label = 'mirror'
    mirror.outputs[0].default_value = 1.0
    rot = N.new('ShaderNodeVectorRotate')          # direction in the room frame
    rot.rotation_type = 'Z_AXIS'
    rot.inputs['Angle'].default_value = -math.radians(ROOM_AZ)
    L.new(tc.outputs['Generated'], rot.inputs['Vector'])
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(rot.outputs['Vector'], sep.inputs['Vector'])
    zm = _math(N, 'MULTIPLY')
    L.new(sep.outputs['Z'], zm.inputs[0])
    L.new(mirror.outputs[0], zm.inputs[1])
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(sep.outputs['X'], comb.inputs['X'])
    L.new(sep.outputs['Y'], comb.inputs['Y'])
    L.new(zm.outputs[0], comb.inputs['Z'])
    zr = N.new('ShaderNodeMapRange')               # z in -1..1 -> 0..1
    zr.inputs['From Min'].default_value = -1.0
    zr.inputs['From Max'].default_value = 1.0
    L.new(zm.outputs[0], zr.inputs['Value'])
    walls = _ramp(N, [(0.0, W_BENCH), (0.47, W_BENCH), (0.53, W_WALL), (0.78, W_WALL), (0.92, W_CEIL),
                      (1.0, W_CEIL)])
    L.new(zr.outputs['Result'], walls.inputs['Fac'])
    vc, zc = window_centre()
    wd = (WALL_U, vc, zc - MECH_Z)
    c1 = _lobe(N, L, comb.outputs['Vector'], wd, 80.0, 8.0, W_WINDOW_BROAD, (1.0, 0.96, 0.90),
               walls.outputs['Color'])
    c2 = _lobe(N, L, comb.outputs['Vector'], wd, 25.0, 15.0, W_WINDOW_CORE, (0.95, 0.97, 1.0),
               c1.outputs['Result'])
    c3 = _lobe(N, L, comb.outputs['Vector'], (-0.85, -0.35, 0.15), 60.0, 15.0, W_ROOM_BACK,
               (1.0, 0.86, 0.66), c2.outputs['Result'])
    c4 = _lobe(N, L, comb.outputs['Vector'], (-0.18, -0.06, 0.98), 55.0, 8.0, W_CEIL_GLOW,
               (1.0, 0.86, 0.68), c3.outputs['Result'])
    gain = N.new('ShaderNodeValue')                 # 1 (front rig) or BACK_WORLD_GAIN (back rig)
    gain.name = gain.label = 'refl_gain'
    gain.outputs[0].default_value = 1.0
    scl = N.new('ShaderNodeVectorMath')
    scl.operation = 'SCALE'
    L.new(c4.outputs['Result'], scl.inputs[0])
    L.new(gain.outputs[0], scl.inputs['Scale'])
    bg_ref = N.new('ShaderNodeBackground')
    bg_ref.inputs['Strength'].default_value = 1.0
    L.new(scl.outputs['Vector'], bg_ref.inputs['Color'])
    bg_cam = N.new('ShaderNodeBackground')
    bg_cam.inputs['Color'].default_value = (*(c * 0.5 for c in PLASTER), 1.0)
    bg_cam.inputs['Strength'].default_value = 1.0
    lp = N.new('ShaderNodeLightPath')
    mix = N.new('ShaderNodeMixShader')
    L.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    L.new(bg_ref.outputs['Background'], mix.inputs[1])
    L.new(bg_cam.outputs['Background'], mix.inputs[2])
    L.new(mix.outputs['Shader'], out.inputs['Surface'])
    w.color = W_WALL
    _set(w, 'sun_threshold', 0.0)            # the real sun is a lamp
    _set(w, 'probe_resolution', '1024')
    old = scene.world
    if old is not None and not old.name.startswith(PREFIX):
        old.use_fake_user = True
    scene.world = w
    return w


# ----------------------------------------------------------------------------- render settings
def colour_management(scene):
    vs = scene.view_settings
    scene.display_settings.display_device = 'sRGB'
    vs.view_transform = VIEW_TRANSFORM
    try:
        vs.look = LOOK
    except TypeError:
        _log('look not available:', LOOK)
    vs.exposure = EXPOSURE
    vs.gamma = 1.0
    vs.use_curve_mapping = False
    scene.sequencer_colorspace_settings.name = 'sRGB'


def tune_eevee(scene, samples=EEVEE_SAMPLES):
    e = scene.eevee
    _set(e, 'taa_render_samples', samples)
    _set(e, 'taa_samples', 16)
    _set(e, 'use_taa_reprojection', True)
    _set(e, 'use_raytracing', True)
    _set(e, 'ray_tracing_method', 'SCREEN')
    rt = e.ray_tracing_options
    _set(rt, 'resolution_scale', '1')
    _set(rt, 'trace_max_roughness', 0.55)
    _set(rt, 'screen_trace_quality', 0.6)
    _set(rt, 'screen_trace_thickness', 2.0)
    _set(rt, 'use_denoise', True)
    _set(rt, 'denoise_spatial', True)
    _set(rt, 'denoise_temporal', True)
    _set(rt, 'denoise_bilateral', True)
    _set(e, 'use_fast_gi', True)
    _set(e, 'fast_gi_method', 'GLOBAL_ILLUMINATION')
    _set(e, 'fast_gi_resolution', '2')
    _set(e, 'fast_gi_step_count', 8)
    _set(e, 'fast_gi_ray_count', 2)
    _set(e, 'fast_gi_quality', 0.5)
    _set(e, 'fast_gi_distance', 120.0)
    _set(e, 'fast_gi_thickness_near', 3.0)
    _set(e, 'fast_gi_bias', 0.05)
    _set(e, 'use_shadows', True)
    _set(e, 'shadow_pool_size', '1024')
    _set(e, 'shadow_ray_count', 1)
    _set(e, 'shadow_step_count', 16)
    _set(e, 'shadow_resolution_scale', 1.0)
    _set(e, 'light_threshold', 0.01)
    _set(e, 'clamp_surface_indirect', 10.0)
    scene.render.filter_size = 1.5
    scene.render.film_transparent = False


def finish(scene, engine=None):
    if engine is None:
        engine = 'cycles' if scene.render.engine == 'CYCLES' else 'eevee'
    if engine == 'cycles':
        cy = scene.cycles
        _set(cy, 'sample_clamp_indirect', 10.0)
        _set(cy, 'blur_glossy', 1.0)
        scene.view_settings.exposure = EXPOSURE + CYCLES_EXPOSURE_OFFSET
    else:
        tune_eevee(scene)
        scene.view_settings.exposure = EXPOSURE


def bronze_look():
    """Polished, lightly aged bronze in daylight (v2).  AM_bronze is rebuilt in place (this file only;
    the master am.blend keeps the build's material): a warm golden-brown metal whose tone varies over
    ~2 cm (hand-finished alloy), roughness varying with fine polishing marks (sharp highlights on the
    polished areas), and a patina that grows with AM_Controller['patina'] from the cavities and a few
    blotches (dark cuprite brown, a little verdigris) instead of a uniform grey veil: at the daylight
    default 0.15 it is a light variation, at 1 (film chapter 1) the part is fully corroded.
    The 'patina' Value node and its driver (nodes["patina"], expression 'p') are kept."""
    mat = bpy.data.materials.get('AM_bronze')
    if mat is not None:
        nt = mat.node_tree
        N, L = nt.nodes, nt.links
        keep = {'patina', 'Material Output'}
        for n in list(N):
            if n.name not in keep:
                N.remove(n)
        pat = N.get('patina')
        out = N.get('Material Output')
        if pat is None:                         # (never happens on a build file: the driver needs it)
            pat = N.new('ShaderNodeValue')
            pat.name = pat.label = 'patina'
            pat.outputs[0].default_value = PATINA
        pat.location = (-1500, -500)
        out.location = (700, 0)
        tc = N.new('ShaderNodeTexCoord')
        tc.location = (-1900, 0)
        # tone of the metal
        n_tone = N.new('ShaderNodeTexNoise')
        n_tone.inputs['Scale'].default_value = 0.03
        n_tone.inputs['Detail'].default_value = 2.0
        n_tone.inputs['Roughness'].default_value = 0.55
        L.new(tc.outputs['Object'], n_tone.inputs['Vector'])
        tone = _ramp(N, [(0.30, BRONZE_DARK), (0.50, BRONZE_BASE), (0.72, BRONZE_LIGHT)])
        L.new(n_tone.outputs['Fac'], tone.inputs['Fac'])
        # polishing marks: roughness
        n_fine = N.new('ShaderNodeTexNoise')
        n_fine.inputs['Scale'].default_value = 0.15
        n_fine.inputs['Detail'].default_value = 2.0
        L.new(tc.outputs['Object'], n_fine.inputs['Vector'])
        rr = N.new('ShaderNodeMapRange')
        rr.inputs['From Min'].default_value = 0.3
        rr.inputs['From Max'].default_value = 0.7
        rr.inputs['To Min'].default_value = BRONZE_ROUGH[0]
        rr.inputs['To Max'].default_value = BRONZE_ROUGH[1]
        L.new(n_fine.outputs['Fac'], rr.inputs['Value'])
        metal = N.new('ShaderNodeBsdfPrincipled')
        metal.name = metal.label = 'bronze'
        metal.location = (0, 300)
        L.new(tone.outputs['Color'], metal.inputs['Base Color'])
        metal.inputs['Metallic'].default_value = BRONZE_METALLIC
        L.new(rr.outputs['Result'], metal.inputs['Roughness'])
        # patina
        n_blot = N.new('ShaderNodeTexNoise')
        n_blot.inputs['Scale'].default_value = 0.08
        n_blot.inputs['Detail'].default_value = 2.0
        n_blot.inputs['Roughness'].default_value = 0.5
        L.new(tc.outputs['Object'], n_blot.inputs['Vector'])
        ao = N.new('ShaderNodeAmbientOcclusion')
        ao.inputs['Distance'].default_value = PATINA_AO_DIST
        cav = _math(N, 'MULTIPLY_ADD', None, -PATINA_CAVITY)          # field = blot + k (1 - AO)
        cav.inputs[2].default_value = PATINA_CAVITY
        L.new(ao.outputs['AO'], cav.inputs[0])
        field = _math(N, 'ADD')
        L.new(n_blot.outputs['Fac'], field.inputs[0])
        L.new(cav.outputs[0], field.inputs[1])
        lo = _math(N, 'MULTIPLY_ADD', None, -PATINA_SPREAD)            # threshold = 1 - spread * p
        lo.inputs[2].default_value = 1.0
        L.new(pat.outputs[0], lo.inputs[0])
        hi = _math(N, 'ADD', None, PATINA_SOFT)
        L.new(lo.outputs[0], hi.inputs[0])
        mask = N.new('ShaderNodeMapRange')
        mask.interpolation_type = 'SMOOTHSTEP'
        mask.clamp = True
        L.new(field.outputs[0], mask.inputs['Value'])
        L.new(lo.outputs[0], mask.inputs['From Min'])
        L.new(hi.outputs[0], mask.inputs['From Max'])
        n_pc = N.new('ShaderNodeTexNoise')
        n_pc.inputs['Scale'].default_value = 0.25
        n_pc.inputs['Detail'].default_value = 5.0
        n_pc.inputs['Roughness'].default_value = 0.6
        L.new(tc.outputs['Object'], n_pc.inputs['Vector'])
        pcol = _ramp(N, [(0.30, PATINA_BROWN), (0.52, PATINA_MID), (0.75, PATINA_GREEN)])
        L.new(n_pc.outputs['Fac'], pcol.inputs['Fac'])
        crust = N.new('ShaderNodeBsdfPrincipled')
        crust.name = crust.label = 'patina_crust'
        crust.location = (0, -400)
        L.new(pcol.outputs['Color'], crust.inputs['Base Color'])
        crust.inputs['Metallic'].default_value = 0.15
        crust.inputs['Roughness'].default_value = 0.78
        # opacity of the patches: 0.45 at patina 0 .. 1 from patina 0.5 (a light variation by daylight,
        # a full crust in film chapter 1)
        amp = N.new('ShaderNodeMapRange')
        amp.clamp = True
        amp.inputs['From Min'].default_value = 0.0
        amp.inputs['From Max'].default_value = 0.5
        amp.inputs['To Min'].default_value = 0.45
        amp.inputs['To Max'].default_value = 1.0
        L.new(pat.outputs[0], amp.inputs['Value'])
        fac = _math(N, 'MULTIPLY')
        L.new(mask.outputs['Result'], fac.inputs[0])
        L.new(amp.outputs['Result'], fac.inputs[1])
        mix = N.new('ShaderNodeMixShader')
        mix.location = (400, 0)
        L.new(fac.outputs[0], mix.inputs['Fac'])
        L.new(metal.outputs['BSDF'], mix.inputs[1])
        L.new(crust.outputs['BSDF'], mix.inputs[2])
        L.new(mix.outputs['Shader'], out.inputs['Surface'])
    ctl = bpy.data.objects.get('AM_Controller')
    if ctl is not None:
        ctl['patina'] = PATINA


def engraving_look():
    """Engraved lines, scale ticks, cell marks and dial lettering (AM_engraving) read as a dark infill
    (wax / niello in the cut) on the bright bronze: near-black, matte, no metallic sheen."""
    mat = bpy.data.materials.get('AM_engraving')
    if mat is None:
        return
    pb = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if pb is not None:
        pb.inputs['Base Color'].default_value = (*ENGRAVE_INFILL, 1.0)
        pb.inputs['Metallic'].default_value = 0.0
        pb.inputs['Roughness'].default_value = 0.85
        pb.inputs['Specular IOR Level'].default_value = 0.25


def edge_bevels():
    """Rounded edges (Bevel modifier 'ATL_bevel', BEVEL_WIDTH, 3 segments, harden normals) on the
    visible non-gear bronze parts (plates, rings, pointers, bars, bosses): the edges catch the window
    and sun highlights.  Gears are left sharp (tooth tips, cost).  Removed and re-added on every run."""
    n = 0
    for ob in bpy.data.objects:
        for m in [m for m in ob.modifiers if m.name == 'ATL_bevel']:
            ob.modifiers.remove(m)
        if ob.type != 'MESH' or ob.name.startswith(PREFIX) or ob.name.startswith('STAGE_'):
            continue
        if int(ob.get('teeth', 0)) != 0 or ob.get('kind', '') != 'prism':
            continue
        if not any(s.material and s.material.name == 'AM_bronze' for s in ob.material_slots):
            continue
        md = ob.modifiers.new('ATL_bevel', 'BEVEL')
        md.width = BEVEL_WIDTH
        md.segments = 3
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(40.0)
        md.use_clamp_overlap = True
        md.harden_normals = True
        n += 1
    _log('edge bevels on %d parts' % n)
    return n


def _spec():
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'spec', 'antikythera.json')
    with open(path) as f:
        return json.load(f)


def groove_floors(coll):
    """The Metonic and Saros spiral grooves are slots through the back plate; seen from the back the
    lit slot walls and the gearing behind made them read as pale lines.  A dark floor inside each slot
    (z = GROOVE_FLOOR_Z, between the slider pin tip at -15.6 and the inner face -15.0; 1.6 wide, the
    parts beyond the 1.2 slot are hidden inside the plate) makes them read as engraved channels.
    Back faces are invisible (backface culling in EEVEE, transparent in Cycles).  Parent B_frame,
    same explode driver as the back plate; tagged atl_only = 'all' (every view)."""
    S = _spec()
    bp = bpy.data.objects.get('back_plate')
    frame = bpy.data.objects.get('B_frame')
    mat = bpy.data.materials.new(PREFIX + 'groove_floor')
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    pb = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    pb.inputs['Base Color'].default_value = (*GROOVE_FLOOR, 1.0)
    pb.inputs['Roughness'].default_value = 0.9
    pb.inputs['Specular IOR Level'].default_value = 0.2
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    geo = N.new('ShaderNodeNewGeometry')
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(geo.outputs['Backfacing'], mix.inputs['Fac'])
    L.new(pb.outputs['BSDF'], mix.inputs[1])
    L.new(tr.outputs['BSDF'], mix.inputs[2])
    L.new(mix.outputs['Shader'], out.inputs['Surface'])
    _set(mat, 'use_backface_culling', True)
    obs = []
    for which in ('metonic', 'saros'):
        d = S['dials']['back'][which]
        c = S['axes_world_xy'][d['centre']]
        r0, pitch, turns = d['r_start'], d['pitch'], d['turns']
        end = turns * 2 * math.pi
        n = int(math.ceil(end / math.radians(0.5)))

        def rho(psi):
            k = math.floor(psi / (2 * math.pi))
            phi = psi - 2 * math.pi * k
            Rk = r0 + k * pitch
            dd = pitch / 2
            if phi < math.pi:
                return Rk
            return dd * math.cos(phi) + math.sqrt((Rk + dd) ** 2 - dd * dd * math.sin(phi) ** 2)

        def uv(psi):
            r = rho(psi)
            return Vector((r * math.sin(psi), r * math.cos(psi)))

        pts = [uv(end * i / n) for i in range(n + 1)]
        ext = 0.8
        t0 = (pts[0] - pts[1]).normalized()
        t1 = (pts[-1] - pts[-2]).normalized()
        pts = [pts[0] + t0 * ext] + pts + [pts[-1] + t1 * ext]
        hw = GROOVE_FLOOR_W / 2
        bm = bmesh.new()
        prev = None
        for i, p in enumerate(pts):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            tng = (b - a).normalized()
            nrm = Vector((-tng.y, tng.x))
            row = []
            for s in (-1.0, 1.0):
                q = p + nrm * (hw * s)
                # back view (u, v) -> world (x, y) = (c.x - u, c.y + v)
                row.append(bm.verts.new((c[0] - q.x, c[1] + q.y, GROOVE_FLOOR_Z)))
            if prev is not None:
                f = bm.faces.new((prev[0], prev[1], row[1], row[0]))
            prev = row
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # face the back viewer (-z)
        for f in bm.faces:
            f.normal_update()
            if f.normal.z > 0:
                f.normal_flip()
        me = bpy.data.meshes.new(PREFIX + 'groove_floor_' + which)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        ob = bpy.data.objects.new(PREFIX + 'groove_floor_' + which, me)
        coll.objects.link(ob)
        if frame is not None:
            ob.parent = frame
            ob.matrix_parent_inverse.identity()
        ob['atl_only'] = 'all'
        # same explode motion as the back plate (a copy of its driver)
        K = float(bp.get('explode_K', 0.0)) if bp is not None else 0.0
        ctl = bpy.data.objects.get('AM_Controller')
        if ctl is not None and bp is not None and 'explode_K' in bp.keys():
            fc = ob.driver_add('delta_location', 2)
            dr = fc.driver
            dr.type = 'SCRIPTED'
            v = dr.variables.new()
            v.name = 'e'
            v.type = 'SINGLE_PROP'
            v.targets[0].id_type = 'OBJECT'
            v.targets[0].id = ctl
            v.targets[0].data_path = '["explode"]'
            dr.expression = 'e*%.4f' % K
            fc.keyframe_points.clear()
            for m in list(fc.modifiers):
                fc.modifiers.remove(m)
        obs.append(ob)
    return obs


# ----------------------------------------------------------------------------- cameras
CLOSE_CAMS = {
    # front dial: 22 deg off its normal, same azimuth as the hero (legend lower left), 85 mm,
    # DOF on the dial centre.  The polished plate shows what lies in its mirror direction: here
    # the plaster room (~0.3) plus the tail of the sun's highlight (~0.2), i.e. the same bronze
    # as the hero.  Rule for new close-ups: keep the mirror direction >= ~34 deg away from the
    # sun (half-vector >= 17 deg) or the sun's specular tail washes the dial out (measured)
    'CAM_front_close': dict(target=(0.0, 0.0, 44.0), az=-50.4, el=68.0, dist=760.0, lens=85.0,
                            fstop=5.6, up=(0.0, 0.0, 1.0)),
    # upper back dial (Metonic spiral + Games and Callippic dials), from below, upright (+y up),
    # same angle rule in the mirrored back rig
    'CAM_back_close': dict(target=(0.0, 60.0, -17.0), az=-70.0, el=-68.0, dist=760.0, lens=85.0,
                           fstop=5.6, up=(0.0, 1.0, 0.0)),
    # macro close-ups of the back (film chapters 5 and 6), same mirror-angle rule in the back rig.  At
    # this magnification any depth of field would blur half of the dial: DOF off, everything legible.
    # Games dial (centre O) with its four sectors (two festivals each)
    # rolled so that the Olympic-year sector (k = 1, bisector psi = 8 + 135 = 143 deg, world direction
    # (-sin 143, cos 143)) is at the top and reads upright when the pointer reaches it (crank 5.911)
    'CAM_games_close': dict(target=(-24.40035, 62.976, -16.5), az=-70.0, el=-74.0, dist=300.0, lens=120.0,
                            fstop=0.0, up=(-0.6018, -0.7986, 0.0), dof=False),
    # upper-left part of the Saros spiral seen from the back (psi ~ 290..360 deg, all four turns, cells
    # 101..112 of the film's chapter 6 and the pointer entering cell 112 at crank 8.975)
    'CAM_saros_close': dict(target=(26.0, -36.0, -16.5), az=-70.0, el=-74.0, dist=300.0, lens=120.0,
                            fstop=0.0, up=(0.0, 1.0, 0.0), dof=False),
}


def ensure_cameras(scene):
    coll = bpy.data.collections.get('AM_HELPERS') or scene.collection
    obs = {}
    for name, c in CLOSE_CAMS.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            cam = bpy.data.cameras.new(name)
            ob = bpy.data.objects.new(name, cam)
            coll.objects.link(ob)
        cam = ob.data
        cam.type = 'PERSP'
        cam.lens = c['lens']
        cam.clip_start = 1.0
        cam.clip_end = 10000.0
        tgt = Vector(c['target'])
        ob.location = tgt + _dir(c['az'], c['el']) * c['dist']
        _look_at(ob, tgt, up=c['up'])
        cam.dof.use_dof = c.get('dof', True)
        cam.dof.focus_distance = c['dist']
        if c['fstop'] > 0:
            cam.dof.aperture_fstop = c['fstop']
        cam.dof.aperture_blades = 7
        obs[name] = ob
    return obs


# ----------------------------------------------------------------------------- visibility
BACK_MODES = ('back', 'close_back')


def stage_visibility(mode):
    """'back' modes: bench, wall, props and battens hidden, mirrored bench shown, back rig on,
    world mirrored.  Other modes: the room and the front rig."""
    coll = bpy.data.collections.get(STAGE)
    if coll is None:
        return
    back = mode in BACK_MODES
    for ob in list(coll.all_objects):
        only = ob.get('atl_only', '')
        if only == 'all':
            hide = False
        elif only == 'back':
            hide = not back
        elif only == 'front':
            hide = back
        else:
            hide = back
        ob.hide_render = hide
        ob.hide_viewport = hide
    w = bpy.context.scene.world
    if w is not None and w.name.startswith(PREFIX):
        node = w.node_tree.nodes.get('mirror')
        if node is not None:
            node.outputs[0].default_value = -1.0 if back else 1.0
        node = w.node_tree.nodes.get('refl_gain')
        if node is not None:
            node.outputs[0].default_value = BACK_WORLD_GAIN if back else 1.0


# ----------------------------------------------------------------------------- entry point
def apply(scene=None, ground_z=None):
    scene = scene or bpy.context.scene
    remove_stage()
    hide_museum(scene)
    coll = bpy.data.collections.new(STAGE)
    scene.collection.children.link(coll)
    if ground_z is None:
        z_asm, z_exp = lowest_points(scene)
        ground_z = min(z_asm, z_exp) - GAP
        _log('lowest z assembled %.2f exploded %.2f -> bench top %.2f' % (z_asm, z_exp, ground_z))
    scene['am_atelier_bench_z'] = ground_z
    room_obs, oak, old = build_room(coll, ground_z)
    build_back_bench(coll, ground_z, oak)
    build_battens(coll, ground_z, wood_material('oak_batten', OAK_LIGHT, OAK_DARK, ring_mm=3.0,
                                                pith_depth=140.0, world_coords=True))
    build_props(coll, ground_z, room_obs['room'])
    build_lights(coll, ground_z)
    build_world(scene, ground_z)
    colour_management(scene)
    tune_eevee(scene)
    bronze_look()
    engraving_look()
    groove_floors(coll)
    edge_bevels()
    ensure_cameras(scene)
    stage_visibility('front34')
    bpy.context.view_layer.update()
    return coll


if __name__ == '__main__':
    apply(bpy.context.scene)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if '--save' in argv:
        bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath, compress=True)
        _log('saved', bpy.data.filepath)
