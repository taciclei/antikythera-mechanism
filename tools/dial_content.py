"""Dial content of the Blender scenes (Blender 5.2, 1 BU = 1 mm). Idempotent; reads spec/antikythera.json.

  games   am.blend AND am_atelier.blend.  The Games dial labels of spec dials.back.subsidiary[olympiad]:
          the historical pair of festivals of each year (Freeth et al. 2008 Nature + SI; Iversen 2017,
          Hesperia 86), two lines per sector, laid out by spec label_layout.  Made exactly like every other
          dial text of the build (build/blender_scripts/dials.py _text: FONT, built-in font, extrusion 0.025,
          material AM_engraving, parent B_frame, collection AM_DIALS, z = back face - extrusion) and given
          the explode driver of tools/exploded_setup.py (delta_location.z = e * K, K = 2 z).  The objects
          keep their names txt_olympiad_<k>.
  glyphs  am_atelier.blend ONLY.  The Saros eclipse glyphs COMPUTED BY OUR MODEL (spec
          dials.back.saros.glyphs_computed): build/out/explainer/glyphs.json, table modele_epoque_t0, rule
          'limits' (the table of the reviewed film script and of the web page).  Σ = lunar, Η = solar,
          'Σ Η' (two lines) when both.  One FONT per engraved cell, centred in the cell (spiral model of the
          spec, the band the cell marks span), same engraved style.  Collection AM_GLYPHS_COMPUTED,
          objects txt_saros_glyph_<cell>, custom property status = 'COMPUTED'.  Never in am.blend (the
          glyphs are model-derived; the master model keeps the spec's placeholders).
  sizes   am_atelier.blend ONLY.  Larger / clearer labels for the film close-ups: zodiac signs, Egyptian
          months, Games (2.4) and Exeligmos labels.

Usage
  BL=/Applications/Blender.app/Contents/MacOS/Blender
  $BL -b build/out/am.blend         -P tools/dial_content.py -- games --save
  $BL -b build/out/am_atelier.blend -P tools/dial_content.py -- games glyphs sizes --save
  (without --save: applied in memory only)
"""
import json
import math
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build', 'blender_scripts'))
import dials  # noqa: E402  (the build's text helper: same FONT settings as every dial text)

SPEC = json.load(open(os.path.join(ROOT, 'spec', 'antikythera.json')))
GLYPHS = os.path.join(ROOT, 'build', 'out', 'explainer', 'glyphs.json')
BACK_Z = -16.5                     # back face of the back plate (texts sit on it, read from -z)
EXPLODE_FACTOR = 3.0
GLYPH_COLL = 'AM_GLYPHS_COMPUTED'

# atelier sizes (build: zodiac 1.9 at r 66.2, months 1.7 at r 73.8, epagomenal 1.1, back labels 0.9)
ATL_ZODIAC = (3.0, 65.5)           # (size, radius): ring 62.5..70, minor ticks from 68.4
ATL_MONTH = (2.8, 73.4)            # ring 70..79, hole circle 76.94..77.74
ATL_EPAGOMENAL = (1.2, 73.8)       # 5-day sector: kept small
ATL_GAMES = (2.4, 10.5)
ATL_EXELIGMOS = (2.2, 14.6)        # dial r 17, pointer 15, sector ticks 15.3..17.5 at the boundaries


def _log(*a):
    print('[dials]', *a, flush=True)


def _explode_driver(ob, K=None):
    """tools/exploded_setup.py law: delta_location.z = e * K, K = (FACTOR - 1) * z (text origin)."""
    ctl = bpy.data.objects.get('AM_Controller')
    if ctl is None or 'explode' not in ctl.keys():
        return
    if K is None:
        bpy.context.view_layer.update()          # a new object's matrix_world is identity until evaluated
        K = (EXPLODE_FACTOR - 1.0) * ob.matrix_world.translation.z
    if ob.animation_data:
        for fc in list(ob.animation_data.drivers):
            if fc.data_path == 'delta_location' and fc.array_index == 2:
                ob.animation_data.drivers.remove(fc)
    ob.delta_location.z = 0.0
    fc = ob.driver_add('delta_location', 2)
    d = fc.driver
    d.type = 'SCRIPTED'
    v = d.variables.new()
    v.name = 'e'
    v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'OBJECT'
    v.targets[0].id = ctl
    v.targets[0].data_path = '["explode"]'
    d.expression = 'e*%.4f' % K
    fc.keyframe_points.clear()
    for m in list(fc.modifiers):
        fc.modifiers.remove(m)
    assert d.is_simple_expression, ob.name
    ob['explode_K'] = K


def _ctx():
    frame = bpy.data.objects['B_frame']
    mat = bpy.data.materials['AM_engraving']
    coll = bpy.data.collections['AM_DIALS']
    return frame, mat, coll


def _back_xy(centre, r, psi):
    """Back-dial point: world (x, y) = centre + r (-sin psi, cos psi) (spec view_frame)."""
    return centre[0] - r * math.sin(psi), centre[1] + r * math.cos(psi)


def _v_offset(body, size):
    """Offset (along text up) of the visual centre of an align-centre text block (built-in font): a line
    spans -0.30..+0.43 size; a two-line block -0.80..+0.93 size."""
    return 0.064 * size


# ----------------------------------------------------------------------------- Games dial
def games(size=None, r_centre=None):
    sd = next(s for s in SPEC['dials']['back']['subsidiary'] if s['id'] == 'olympiad')
    lay = sd['label_layout']
    size = lay['size'] if size is None else size
    r_centre = lay['r_centre'] if r_centre is None else r_centre
    frame, mat, coll = _ctx()
    for ob in [o for o in bpy.data.objects if o.name.startswith('txt_olympiad_')]:
        cu = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if cu.users == 0:
            bpy.data.curves.remove(cu)
    c = SPEC['axes_world_xy'][sd['centre']]
    z = BACK_Z - dials.EXTRUDE
    n = sd['sectors']
    made = []
    for k, lab in enumerate(sd['labels']):
        psi = math.radians(sd.get('sector_tilt_deg', 0.0) + 360.0 * (k + 0.5) / n)
        body = '\n'.join(lab.split())
        r = r_centre - _v_offset(body, size)
        x, y = _back_xy(c, r, psi)
        ob = dials._text('txt_olympiad_%d' % k, body, size, coll, frame, mat, (x, y, z), (0.0, math.pi, psi))
        ob['sources'] = 'spec dials.back.subsidiary[olympiad].labels (%s)' % ', '.join(sd['label_sources'])
        ob['year_of_olympiad'] = sd['label_years'][k]
        _explode_driver(ob)
        made.append(ob)
    _log('games: %d labels, size %.2f at r %.2f:' % (len(made), size, r_centre),
         ', '.join('%s=%r' % (o.name, o.data.body.replace('\n', ' ')) for o in made))
    return made


# ----------------------------------------------------------------------------- Saros glyphs
def _rho(psi, r_start, pitch):
    """Two-centre spiral of the spec (dials.back.spiral_model), psi >= 0."""
    k = math.floor(psi / (2 * math.pi))
    phi = psi - 2 * math.pi * k
    Rk = r_start + k * pitch
    d = pitch / 2
    if phi < math.pi:
        return Rk
    return d * math.cos(phi) + math.sqrt((Rk + d) ** 2 - d * d * math.sin(phi) ** 2)


def glyph_cells(table='modele_epoque_t0', rule='limits'):
    g = json.load(open(GLYPHS))
    cells = g[table][rule]['cells']
    return [(c['case'], c['glyph']) for c in cells if c['glyph']], g[table][rule]


def glyphs(table='modele_epoque_t0', rule='limits', size=None):
    sa = SPEC['dials']['back']['saros']
    gc = sa['glyphs_computed']
    size = gc['layout']['size'] if size is None else size
    frame, mat, _ = _ctx()
    coll = bpy.data.collections.get(GLYPH_COLL)
    if coll is None:
        coll = bpy.data.collections.new(GLYPH_COLL)
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):
        cu = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if cu is not None and cu.users == 0:
            bpy.data.curves.remove(cu)
    rows, tab = glyph_cells(table, rule)
    c = SPEC['axes_world_xy'][sa['centre']]
    ncell, turns = sa['cells'], sa['turns']
    end = turns * 2 * math.pi
    hw = sa['groove_width'] / 2
    margin, r_max, mark_w = 0.3, 71.0, 0.3                # as build/am/spiral.py cell_marks
    dpsi = end / ncell
    z = BACK_Z - dials.EXTRUDE
    made, layout = [], {}
    for j, gl in rows:
        psi = end * (j - 0.5) / ncell
        ra = _rho(psi, sa['r_start'], sa['pitch']) + hw + margin
        rb = r_max if psi + 2 * math.pi > end + 1e-9 else _rho(psi + 2 * math.pi, sa['r_start'], sa['pitch']) - hw - margin
        rb = min(rb, r_max)
        band = rb - ra
        r_mid = 0.5 * (ra + rb)
        w_avail = r_mid * dpsi - mark_w - 2 * margin
        both = 'Σ' in gl and 'Η' in gl
        if both:
            s_stack = min(size, (band - 0.3) / 1.73, w_avail / 0.57)
            s_line = min(size, (band - 0.3) / 0.75, w_avail / 1.55)
            if s_stack >= s_line:
                body, s = 'Σ\nΗ', s_stack
            else:
                body, s = 'Σ Η', s_line
        else:
            body, s = gl, min(size, (band - 0.3) / 0.75, w_avail / 0.6)
        s = max(s, 0.5)
        x, y = _back_xy(c, r_mid - _v_offset(body, s), psi)
        ob = dials._text('txt_saros_glyph_%03d' % j, body, s, coll, frame, mat, (x, y, z), (0.0, math.pi, psi))
        ob['status'] = 'COMPUTED'
        ob['role'] = 'Saros eclipse glyph COMPUTED BY OUR MODEL (not the original glyph); film working copy only'
        ob['sources'] = 'build/out/explainer/glyphs.json %s.%s (tools/explainer/engine.py); scheme: Freeth 2014' % (table, rule)
        ob['saros_cell'] = j
        ob['glyph'] = gl
        _explode_driver(ob)
        made.append(ob)
        layout[j] = (body.replace('\n', '/'), round(s, 2), round(band, 2))
    small = {j: v for j, v in layout.items() if v[1] < size - 1e-6}
    _log('glyphs: %d cells from %s.%s (%d Σ, %d Η), size %.2f; smaller in the narrow last-turn band: %s'
         % (len(made), table, rule, sum('Σ' in g for _, g in rows), sum('Η' in g for _, g in rows), size, small))
    return made


# ----------------------------------------------------------------------------- atelier label sizes
def _resize_ring(prefix, size, radius, only=None):
    n = 0
    for ob in bpy.data.objects:
        if not ob.name.startswith(prefix) or ob.type != 'FONT':
            continue
        if only is not None and not only(ob):
            continue
        x, y, z = ob.location
        a = math.atan2(y, x)
        ob.location = (radius * math.cos(a), radius * math.sin(a), z)
        ob.data.size = size
        n += 1
    return n


def sizes():
    nz = _resize_ring('txt_zodiac_', *ATL_ZODIAC)
    nm = _resize_ring('txt_month_', *ATL_MONTH, only=lambda o: o.name != 'txt_month_12')
    ne = _resize_ring('txt_month_12', *ATL_EPAGOMENAL)
    games(*ATL_GAMES)
    # Exeligmos: sectors of 120 deg, labels at mid-sector
    sd = next(s for s in SPEC['dials']['back']['subsidiary'] if s['id'] == 'exeligmos')
    c = SPEC['axes_world_xy'][sd['centre']]
    size, r_c = ATL_EXELIGMOS
    nx = 0
    for k, lab in enumerate(sd['labels']):
        ob = bpy.data.objects.get('txt_exeligmos_%d' % k)
        if ob is None:
            continue
        psi = math.radians(sd.get('sector_tilt_deg', 0.0) + 360.0 * (k + 0.5) / sd['sectors'])
        x, y = _back_xy(c, r_c - _v_offset(lab, size), psi)
        ob.location = (x, y, ob.location.z)
        ob.data.size = size
        nx += 1
    _log('sizes: zodiac %d -> %.1f @ r %.1f, months %d -> %.1f @ r %.1f, epagomenal %d -> %.1f, Games -> %.1f, '
         'Exeligmos %d -> %.1f @ r %.1f' % (nz, *ATL_ZODIAC, nm, *ATL_MONTH, ne, ATL_EPAGOMENAL[0], ATL_GAMES[0],
                                          nx, *ATL_EXELIGMOS))


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    is_master = os.path.basename(bpy.data.filepath) == 'am.blend'
    if is_master and ('glyphs' in argv or 'sizes' in argv):
        raise SystemExit('glyphs / sizes are for the film working copy (am_atelier.blend), never for am.blend')
    if 'games' in argv and 'sizes' not in argv:
        games()
    if 'sizes' in argv:
        sizes()
    if 'glyphs' in argv:
        glyphs()
    bpy.context.view_layer.update()
    if '--save' in argv:
        bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath, compress=True)
        _log('saved', bpy.data.filepath)
