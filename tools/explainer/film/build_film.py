"""Builds the film scene build/out/explainer/film/film.blend from am_atelier.blend and timeline.json (Blender 5.2).

    BL=/Applications/Blender.app/Contents/MacOS/Blender
    $BL -b build/out/am_atelier.blend --factory-startup --python-exit-code 1 -P tools/explainer/film/build_film.py
    $BL -b build/out/explainer/film/film.blend --factory-startup --python-exit-code 1 \
        -P tools/explainer/film/build_film.py -- --verify-only        # checks only (nothing saved)

am_atelier.blend is only read : the scene is saved under a new name (film.blend) and the script refuses to write over
am.blend or am_atelier.blend.  Then the checks run on the saved scene and are written to film/film_check.json
(exit code 1 if one fails).

What the scene contains (everything follows timeline.json ; frame f of the film = Blender frame f, 25 fps) :
  * one scene « Antikythera » over frames 1..frame_end, 1920 x 1080, EEVEE (render_frames.DEFAULTS) ;
  * AM_Controller["crank"], ["explode"], ["patina"] : the keys of timeline.controller with their interpolation and an
    EXPLICIT easing (Blender's AUTO is not EASE_IN_OUT) ; the frames[] values of timeline.json are the reference and
    are checked on every frame after keying (film_check.json) ;
  * one camera per shot (CAM_1_1 ... CAM_7_5, collection FILM_CAMERAS), baked on every frame of its shot from the
    pose list (target, az, el, dist, lens, up, shift, ease ; targets {anchor, crank} and {track: anchor} evaluated
    with anchors.Anchors), bound with timeline markers (one marker per rendered shot) ; the split shots keep the
    timeline's lens shift (x 0.25 : the machine in the left half) ; CAM_7_5 carries on under the end card ;
  * the 3.4 inset camera CAM_3_4_ball in a second scene FILM_inset_3_4 (same collections, 480 x 480) ;
  * staging per shot, keyed on hide_render / hide_viewport (CONSTANT) : mode case (closed wooden case AM_CASE on the
    bench), front / wide (atelier room + front rig), back (mirrored bench and rig, world node « mirror » = -1,
    « refl_gain » = BACK_WORLD_GAIN), front_to_back (switch when the orbit of 5.1 crosses el = 0) ; AM_LABELS only
    in the shots flagged labels ; non-3D shots keep the previous state ;
  * highlights : each target object gets its OWN copy of its materials (slot linked to the object), with an Add
    Shader (original surface + Emission) whose strength is a Value node keyed from timeline.highlights[].keys
    (LINEAR) ; « sweep » highlights multiply it by an angular window (width_deg) that turns with the keyed angle ;
  * FILM objects (collection FILM_OBJECTS, additive glow materials, no shadow) : FILM_b1_ghost (flat golden copy of
    b1 just above the dial, turning with B_b), FILM_games_wedge (sector ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ of the Games dial),
    FILM_phase_halo (ring around the phase ball, carried by the Moon), FILM_mars_trail (arc on Mars' ring from the
    smallest to the largest longitude reached since the start of the shot, 4.2 and 4.3), FILM_sunblind (panel with a
    vertical slit outside the window, visible to shadows only, shot 1.1 : the sunbeam slides over the lid).
"""
import json
import math
import pathlib
import sys
import time

import bpy
import bmesh
import numpy as np
from bpy_extras import anim_utils
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import filmlib as L  # noqa: E402

ROOT = L.ROOT
sys.path.insert(0, str(ROOT / 'tools' / 'explainer'))
sys.path.insert(0, str(ROOT / 'tools'))
import anchors as AN  # noqa: E402
import render_frames as RF  # noqa: E402
import staging_atelier as ST  # noqa: E402

FILM_BLEND = L.FILM / 'film.blend'
CHECK = L.FILM / 'film_check.json'
FORBIDDEN_OUT = {(ROOT / 'build' / 'out' / 'am.blend').resolve(), (ROOT / 'build' / 'out' / 'am_atelier.blend').resolve()}
MAIN_SCENE = 'Antikythera'
COLL_FILM = 'FILM_OBJECTS'
COLL_CAMS = 'FILM_CAMERAS'

# look of the highlights : emission strength = key value x gain (test frames : the sunlit bronze saturates to white
# above ~0.8 ; the engraved letters are dark and need more ; letters lying ON a glowing area stay dark to be read)
GAIN_DEFAULT = 0.35                       # planet spheres
GAIN_MATERIAL = {'AM_bronze': 0.3, 'AM_engraving': 0.45}
GAIN_OBJECT = {'txt_olympiad_1': 0.12, 'parapegma_lines_1': 0.06, 'parapegma_lines_2': 0.06,
               'FILM_b1_ghost': 0.7, 'FILM_games_wedge': 0.3, 'FILM_phase_halo': 0.35}
COLL_MAIN_ONLY = 'FILM_MAIN_ONLY'         # FILM objects not seen by the 3.4 inset camera (the phase-ball halo)
GHOST_Z = (5.35, 42.58, 0.04)            # b1 mid-plane z, ghost mid-plane z, thickness scale
WEDGE = (4.5, 17.6, -16.508)             # inner / outer radius (mm) of the Games wedge, z (just below the dial face)
HALO = (4.6, 0.28)                        # phase-ball halo : ring radius, tube radius
TRAIL = {'depth': 0.22, 'z_above_ring': 0.05, 'color': (1.0, 0.10, 0.03), 'strength': 0.9, 'step_deg': 0.25}
SUNBLIND = {'u_out': 40.0, 'half_w': 3000.0, 'half_h': 1600.0}


def log(*a):
    print('[film]', *a, flush=True)


# ----------------------------------------------------------------------------- animation helpers (Blender 5 actions)
def _channelbag(idb):
    ad = idb.animation_data or idb.animation_data_create()
    if ad.action is None:
        ad.action = bpy.data.actions.new('FILM_' + idb.name)
    if ad.action_slot is None:
        ad.action_slot = ad.action.slots.new(idb.id_type, idb.name)
    return anim_utils.action_ensure_channelbag_for_slot(ad.action, ad.action_slot)


def fcurve(idb, path, index=0):
    cb = _channelbag(idb)
    for fc in list(cb.fcurves):
        if fc.data_path == path and fc.array_index == index:
            cb.fcurves.remove(fc)
    return cb.fcurves.new(path, index=index)


def set_keys(fc, keys):
    """keys : [(frame, value, interpolation[, easing])] ; the interpolation of a key applies to the span after it."""
    kp = fc.keyframe_points
    kp.add(len(keys))
    kp.foreach_set('co', [float(c) for k in keys for c in (k[0], k[1])])
    for p, k in zip(kp, keys):
        p.interpolation = k[2]
        if len(k) > 3 and k[3]:
            p.easing = k[3]
    fc.update()
    return fc


def key_changes(idb, path, values, index=0, ipo='CONSTANT'):
    """values : list (frame 1..N) -> keys only where the value changes (CONSTANT)."""
    keys, prev = [], None
    for f, v in enumerate(values, start=1):
        if v != prev:
            keys.append((f, float(v), ipo))
            prev = v
    return set_keys(fcurve(idb, path, index), keys)


# ----------------------------------------------------------------------------- camera poses
def _dir(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def look_rotation(loc, target, up):
    """Same rule as staging_atelier._look_at : -Z towards the target, roll from the up vector."""
    f = (Vector(target) - loc).normalized()
    upv = Vector(up).normalized()
    if abs(f.dot(upv)) > 0.999:
        upv = Vector((0.0, 1.0, 0.0))
    r = f.cross(upv).normalized()
    u = r.cross(f)
    return Matrix((r, u, -f)).transposed()


def pose_params(poses, f, target_of):
    """Interpolated pose at frame f : (target, az, el, dist, lens, up, shift) ; the move from a pose to the next uses
    that pose's easing ; constant before the first / after the last pose."""
    def unpack(p):
        return (target_of(p['target'], f), p['az'], p['el'], p['dist'], p['lens'], Vector(p['up']),
                Vector(p['shift']))
    if f <= poses[0]['f']:
        return unpack(poses[0])
    if f >= poses[-1]['f']:
        return unpack(poses[-1])
    i = max(k for k in range(len(poses)) if poses[k]['f'] <= f)
    a, b = poses[i], poses[i + 1]
    w = L.ease01((f - a['f']) / (b['f'] - a['f']), a.get('ease', 'SINE_IN_OUT'))
    pa, pb = unpack(a), unpack(b)
    lerp = lambda x, y: x + (y - x) * w
    up = pa[5].lerp(pb[5], w)
    return (pa[0].lerp(pb[0], w), lerp(pa[1], pb[1]), lerp(pa[2], pb[2]), lerp(pa[3], pb[3]), lerp(pa[4], pb[4]),
            up.normalized() if up.length > 1e-9 else pa[5], pa[6].lerp(pb[6], w))


# ----------------------------------------------------------------------------- build
class Builder:
    def __init__(self, T):
        self.T = T
        self.N = T['frame_end']
        self.segs = {s['id']: s for s in T['segments']}
        self.sc = bpy.data.scenes.get(MAIN_SCENE) or bpy.context.scene
        self.ctl = bpy.data.objects['AM_Controller']
        self.report = {}

    # -------------------------------------------------------------- scene
    def scene_setup(self):
        sc = self.sc
        sc.frame_start, sc.frame_end = 1, self.N
        sc.frame_current = 1
        RF.apply_settings(sc)
        sc.timeline_markers.clear()
        ad = self.ctl.animation_data
        if ad and ad.action:
            log('controller action %s detached (replaced by FILM_controller)' % ad.action.name)
            ad.action = None
        self.ctl['crank'], self.ctl['explode'], self.ctl['patina'] = 0.0, 0.0, ST.PATINA
        for name in (COLL_FILM, COLL_CAMS, COLL_MAIN_ONLY):
            c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
            if c.name not in sc.collection.children:
                sc.collection.children.link(c)
        self.coll = bpy.data.collections[COLL_FILM]
        self.cams = bpy.data.collections[COLL_CAMS]
        self.main_only = bpy.data.collections[COLL_MAIN_ONLY]
        bpy.context.view_layer.update()

    # -------------------------------------------------------------- anchors, targets, per-frame pre-pass
    def prepass(self):
        """Everything that needs the machine at a given crank, before the controller is keyed : camera targets
        {anchor, crank}, tracked targets per frame, Mars' longitude per frame (trail)."""
        T = self.T
        self.A = AN.Anchors(T['anchors'])
        self.fixed_targets = {}
        track_frames = {}
        for s in T['segments']:
            for cam in (s.get('camera'), s.get('inset')):
                for p in (cam or {}).get('poses', []):
                    t = p['target']
                    if isinstance(t, dict) and 'crank' in t:
                        k = (t['anchor'], L.f32(t['crank']))
                        if k not in self.fixed_targets:
                            dg = AN.set_state(k[1], 0.0)
                            self.fixed_targets[k] = self.A.world(k[0], dg)
                    elif isinstance(t, dict) and 'track' in t:
                        for f in range(s['frames'][0], s['frames'][1] + 2):
                            track_frames.setdefault(min(f, self.N), set()).add(t['track'])
        self.tracked = {}
        mars_frames = [f for sid in ('4.2', '4.3') for f in range(self.segs[sid]['frames'][0],
                                                                  self.segs[sid]['frames'][1] + 1)]
        self.mars_lam, self.mars_r = {}, []
        marker = bpy.data.objects['marker_mars']
        bbc = sum((Vector(c) for c in marker.bound_box), Vector()) / 8.0
        for f in sorted(set(track_frames) | set(mars_frames)):
            x = T['frames'][f - 1]
            dg = AN.set_state(x['crank'], x['explode'])
            for a in track_frames.get(f, ()):
                self.tracked[(a, f)] = self.A.world(a, dg)
            if f in mars_frames:
                p = marker.evaluated_get(dg).matrix_world @ bbc
                self.mars_lam[f] = -math.degrees(math.atan2(p.y, p.x))
                self.mars_r.append(p.xy.length)
        dg = AN.set_state(0.0, 0.0)
        self.mars_ring_top = max((bpy.data.objects['ring_mars'].evaluated_get(dg).matrix_world @ Vector(c)).z
                                 for c in bpy.data.objects['ring_mars'].bound_box)
        log('prepass : %d fixed targets, %d tracked positions, Mars on %d frames (r %.2f mm)'
            % (len(self.fixed_targets), len(self.tracked), len(self.mars_lam), sum(self.mars_r) / len(self.mars_r)))

    def target_of(self, t, f):
        if isinstance(t, (list, tuple)):
            return Vector(t)
        if 'crank' in t:
            return self.fixed_targets[(t['anchor'], L.f32(t['crank']))].copy()
        return self.tracked[(t['track'], min(f, self.N))].copy()

    # -------------------------------------------------------------- controller
    def controller(self):
        C = self.T['controller']
        for name in ('crank', 'explode', 'patina'):
            keys = [(k['f'], k['v'], k['ipo'], k.get('ease', 'EASE_IN_OUT')) for k in C[name]]
            set_keys(fcurve(self.ctl, '["%s"]' % name), keys)
        self.ctl.animation_data.action.name = 'FILM_controller'
        log('controller keyed : %s' % {k: len(v) for k, v in C.items()})

    # -------------------------------------------------------------- staging per frame
    def switch_frame_5_1(self):
        s = self.segs['5.1']
        poses = s['camera']['poses']
        for f in range(s['frames'][0], s['frames'][1] + 1):
            if pose_params(poses, f, lambda t, fr: Vector((0, 0, 0)) if isinstance(t, dict) else Vector(t))[2] < 0.0:
                return f
        return s['frames'][1]

    def states(self):
        """Per frame (1..N) : (mode case|front|back, labels)."""
        sw = self.switch_frame_5_1()
        self.report['switch_front_to_back'] = sw
        out, prev = [], ('case', False)
        for x in self.T['frames']:
            s = self.segs[x['seg']]
            if s.get('render_3d'):
                mode = s['mode']
                if mode == 'front_to_back':
                    mode = 'front' if x['f'] < sw else 'back'
                elif mode == 'wide':
                    mode = 'front'
                prev = (mode, bool(s.get('labels')))
            out.append(prev)
        return out

    def visibility(self):
        st = self.states()
        self.frame_state = st
        modes = [m for m, _ in st]
        labels = [lb for _, lb in st]

        def key_hide(ob, hidden):
            key_changes(ob, 'hide_render', hidden)
            key_changes(ob, 'hide_viewport', hidden)

        n = 0
        for ob in bpy.data.collections[ST.STAGE].all_objects:
            only = ob.get('atl_only', '')
            if only == 'all':
                vis = [True] * len(modes)
            elif only == 'back':
                vis = [m == 'back' for m in modes]
            else:
                vis = [m != 'back' for m in modes]
            key_hide(ob, [not v for v in vis])
            n += 1
        for ob in [o for o in bpy.data.objects if o.name.startswith('case_')]:
            key_hide(ob, [m != 'case' for m in modes])
            n += 1
        for ob in bpy.data.collections['AM_LABELS'].objects:
            if ob.name.startswith('ANCHOR_'):
                continue
            key_hide(ob, [not lb for lb in labels])
            n += 1
        w = self.sc.world
        key_changes(w.node_tree, 'nodes["mirror"].outputs[0].default_value', [-1.0 if m == 'back' else 1.0
                                                                              for m in modes])
        key_changes(w.node_tree, 'nodes["refl_gain"].outputs[0].default_value',
                    [ST.BACK_WORLD_GAIN if m == 'back' else 1.0 for m in modes])
        log('visibility keyed on %d objects + world (mode changes at %s)'
            % (n, [f for f in range(2, self.N + 1) if modes[f - 1] != modes[f - 2]]))

    def key_visible_range(self, ob, ranges):
        """ob rendered only inside the inclusive frame ranges."""
        vis = [False] * self.N
        for a, b in ranges:
            for f in range(max(a, 1), min(b, self.N) + 1):
                vis[f - 1] = True
        key_changes(ob, 'hide_render', [not v for v in vis])
        key_changes(ob, 'hide_viewport', [not v for v in vis])

    # -------------------------------------------------------------- materials
    @staticmethod
    def _output(mat):
        outs = [n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL']
        act = [n for n in outs if n.is_active_output] or outs
        return act[0]

    def transparent_material(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        tr.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(tr.outputs[0], out.inputs['Surface'])
        m.surface_render_method = 'BLENDED'
        # additive glow : only the front-most layer (the flattened tooth walls of the ghost, both sides of the halo
        # tube would each add their emission and burn to white)
        m.use_transparency_overlap = False
        m.use_backface_culling = True
        m.use_transparent_shadow = True
        return m

    def add_emission(self, mat, hid, color, gain, sweep=None, width_deg=None):
        """Original surface + Emission(color, value x gain [x angular window]) ; returns the keyed Value node(s)."""
        nt = mat.node_tree
        N, Lk = nt.nodes, nt.links
        out = self._output(mat)
        src = out.inputs['Surface'].links[0].from_socket
        val = N.new('ShaderNodeValue')
        val.name = val.label = 'hl_' + hid
        val.outputs[0].default_value = 0.0
        em = N.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (*color, 1.0)
        mul = N.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        Lk.new(val.outputs[0], mul.inputs[0])
        mul.inputs[1].default_value = gain
        strength = mul.outputs[0]
        ang = None
        if sweep:
            geo = N.new('ShaderNodeNewGeometry')
            sep = N.new('ShaderNodeSeparateXYZ')
            Lk.new(geo.outputs['Position'], sep.inputs[0])
            at2 = N.new('ShaderNodeMath')
            at2.operation = 'ARCTAN2'
            Lk.new(sep.outputs['Y'], at2.inputs[0])
            Lk.new(sep.outputs['X'], at2.inputs[1])
            ang = N.new('ShaderNodeValue')
            ang.name = ang.label = 'hls_' + hid
            sub = N.new('ShaderNodeMath')
            sub.operation = 'SUBTRACT'
            Lk.new(at2.outputs[0], sub.inputs[0])
            Lk.new(ang.outputs[0], sub.inputs[1])
            wr = N.new('ShaderNodeMath')
            wr.operation = 'WRAP'
            Lk.new(sub.outputs[0], wr.inputs[0])
            wr.inputs[1].default_value = math.pi
            wr.inputs[2].default_value = -math.pi
            ab = N.new('ShaderNodeMath')
            ab.operation = 'ABSOLUTE'
            Lk.new(wr.outputs[0], ab.inputs[0])
            mr = N.new('ShaderNodeMapRange')
            mr.interpolation_type = 'SMOOTHSTEP'
            mr.clamp = True
            Lk.new(ab.outputs[0], mr.inputs['Value'])
            mr.inputs['From Min'].default_value = 0.0
            mr.inputs['From Max'].default_value = math.radians(width_deg / 2.0)
            mr.inputs['To Min'].default_value = 1.0
            mr.inputs['To Max'].default_value = 0.0
            m2 = N.new('ShaderNodeMath')
            m2.operation = 'MULTIPLY'
            Lk.new(strength, m2.inputs[0])
            Lk.new(mr.outputs['Result'], m2.inputs[1])
            strength = m2.outputs[0]
        Lk.new(strength, em.inputs['Strength'])
        add = N.new('ShaderNodeAddShader')
        Lk.new(src, add.inputs[0])
        Lk.new(em.outputs[0], add.inputs[1])
        Lk.new(add.outputs[0], out.inputs['Surface'])
        return val, ang

    def highlights(self):
        H = self.T['highlights']
        by_obj = {}
        for h in H:
            for t in h['targets']:
                by_obj.setdefault(t, []).append(h)
        copies = {}
        self.hl_nodes = {}
        ranges = {}
        for obname, hs in by_obj.items():
            ob = bpy.data.objects[obname]
            ids = tuple(h['id'] for h in hs)
            for slot in ob.material_slots:
                orig = slot.material
                if orig is None:
                    continue
                key = (ids, orig.name, obname if obname in GAIN_OBJECT else '')
                if key not in copies:
                    m = orig.copy()
                    m.name = 'FILMHL_%s_%s' % ('+'.join(ids), orig.name)
                    gain = GAIN_OBJECT.get(obname, GAIN_MATERIAL.get(orig.name, GAIN_DEFAULT))
                    for h in hs:
                        val, ang = self.add_emission(m, h['id'], h['color'], gain, h.get('sweep'), h.get('width_deg'))
                        set_keys(fcurve(m.node_tree, 'nodes["%s"].outputs[0].default_value' % val.name),
                                 [(k['f'], k['v'], 'LINEAR') for k in h['keys']])
                        if ang is not None:
                            set_keys(fcurve(m.node_tree, 'nodes["%s"].outputs[0].default_value' % ang.name),
                                     [(f, math.radians(a), 'LINEAR') for f, a in h['sweep']])
                        self.hl_nodes.setdefault(h['id'], []).append((m.name, val.name))
                    copies[key] = m
                slot.link = 'OBJECT'
                slot.material = copies[key]
            if obname.startswith('FILM_'):
                ranges[obname] = [(min(k['f'] for h in hs for k in h['keys']),
                                   max(k['f'] for h in hs for k in h['keys']))]
        for obname, rg in ranges.items():
            self.key_visible_range(bpy.data.objects[obname], rg)
        log('highlights : %d, %d material copies' % (len(H), len(copies)))
        self.report['highlight_materials'] = sorted(m.name for m in copies.values())

    # -------------------------------------------------------------- FILM objects
    def _link(self, ob, shadow=False, coll=None):
        (coll or self.coll).objects.link(ob)
        ob.visible_shadow = shadow
        ob.hide_probe_sphere = True
        ob.hide_probe_volume = True
        ob.hide_probe_plane = True
        return ob

    def _parent_keep(self, ob, parent, dg):
        """Parents ob (world matrix already right at crank 0) to parent, keeping its world transform."""
        W = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_parent_inverse = parent.evaluated_get(dg).matrix_world.inverted()
        ob.matrix_basis = Matrix.Identity(4)
        ob.matrix_parent_inverse = ob.matrix_parent_inverse @ W

    def film_objects(self):
        dg = AN.set_state(0.0, 0.0)
        base = self.transparent_material('FILM_additive_base')
        # --- ghost of b1 : b1's mesh, flattened, just above the dial, carried by B_b (rotation about the front axis)
        b1 = bpy.data.objects['b1']
        g = bpy.data.objects.get('FILM_b1_ghost') or bpy.data.objects.new('FILM_b1_ghost', b1.data)
        self._link(g)
        z0, z1, k = GHOST_Z
        Mz = Matrix.Translation((0, 0, z1)) @ Matrix.Diagonal((1.0, 1.0, k, 1.0)) @ Matrix.Translation((0, 0, -z0))
        g.matrix_world = Mz @ b1.evaluated_get(dg).matrix_world
        self._parent_keep(g, bpy.data.objects['B_b'], dg)
        g.material_slots[0].link = 'OBJECT'
        g.material_slots[0].material = base
        # --- Games wedge : sector of txt_olympiad_1 (ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ), ±45° around its direction from the dial centre
        cx, cy = self.T['anchors']['games_pointer']['axis']
        t1 = bpy.data.objects['txt_olympiad_1'].evaluated_get(dg)
        c1 = t1.matrix_world @ (sum((Vector(c) for c in t1.bound_box), Vector()) / 8.0)
        mid = math.atan2(c1.y - cy, c1.x - cx)
        r0, r1, zw = WEDGE
        bm = bmesh.new()
        n = 48
        inner, outer = [], []
        for i in range(n + 1):
            a = mid - math.pi / 4 + (math.pi / 2) * i / n
            inner.append(bm.verts.new((cx + r0 * math.cos(a), cy + r0 * math.sin(a), zw)))
            outer.append(bm.verts.new((cx + r1 * math.cos(a), cy + r1 * math.sin(a), zw)))
        for i in range(n):
            bm.faces.new((inner[i], inner[i + 1], outer[i + 1], outer[i]))
        me = bpy.data.meshes.new('FILM_games_wedge')
        bm.to_mesh(me)
        bm.free()
        me.materials.append(base)
        wdg = self._link(bpy.data.objects.new('FILM_games_wedge', me))
        self._parent_keep(wdg, bpy.data.objects['B_frame'], dg)
        self.report['games_wedge_mid_psi_deg'] = round((math.degrees(math.atan2(-(c1.x - cx), c1.y - cy))) % 360, 2)
        # --- halo around the phase ball, horizontal ring carried by the Moon (B_moon)
        pts = []
        for nm in ('phase_sphere_dark', 'phase_sphere_silver'):
            o = bpy.data.objects[nm].evaluated_get(dg)
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
        ball = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
        R, r = HALO
        bm = bmesh.new()
        seg, rs = 96, 12
        rings = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring = []
            for j in range(rs):
                b = 2 * math.pi * j / rs
                rr = R + r * math.cos(b)
                ring.append(bm.verts.new((ball.x + rr * math.cos(a), ball.y + rr * math.sin(a), ball.z + r * math.sin(b))))
            rings.append(ring)
        for i in range(seg):
            for j in range(rs):
                a0, a1 = rings[i], rings[(i + 1) % seg]
                bm.faces.new((a0[j], a1[j], a1[(j + 1) % rs], a0[(j + 1) % rs]))
        me = bpy.data.meshes.new('FILM_phase_halo')
        bm.to_mesh(me)
        bm.free()
        me.materials.append(base)
        halo = self._link(bpy.data.objects.new('FILM_phase_halo', me), coll=self.main_only)
        self._parent_keep(halo, bpy.data.objects['B_moon'], dg)
        self.report['phase_ball_centre'] = [round(v, 2) for v in ball]
        self.mars_trail(dg)
        self.sunblind()
        bpy.context.view_layer.update()

    def mars_trail(self, dg):
        lam = self.mars_lam
        frames = sorted(lam)
        # unwrap
        un, prev = {}, None
        for f in frames:
            v = lam[f]
            if prev is not None:
                v = prev + ((v - prev + 180.0) % 360.0 - 180.0)
            un[f] = prev = v
        lo_all, hi_all = min(un.values()) - 3.0, max(un.values()) + 3.0
        r = sum(self.mars_r) / len(self.mars_r)
        z = self.mars_ring_top + TRAIL['depth'] + TRAIL['z_above_ring']
        cu = bpy.data.curves.get('FILM_mars_trail') or bpy.data.curves.new('FILM_mars_trail', 'CURVE')
        cu.splines.clear()
        cu.dimensions = '3D'
        n = int(math.ceil((hi_all - lo_all) / TRAIL['step_deg'])) + 1
        sp = cu.splines.new('POLY')
        sp.points.add(n - 1)
        for i, p in enumerate(sp.points):
            a = math.radians(-(lo_all + (hi_all - lo_all) * i / (n - 1)))
            p.co = (r * math.cos(a), r * math.sin(a), z, 1.0)
        cu.bevel_mode = 'ROUND'
        cu.bevel_depth = TRAIL['depth']
        cu.bevel_resolution = 3
        cu.use_fill_caps = True
        cu.bevel_factor_mapping_start = 'SPLINE'
        cu.bevel_factor_mapping_end = 'SPLINE'
        m = self.transparent_material('FILM_mars_trail')
        self.add_emission(m, 'mars_trail', TRAIL['color'], 1.0)[0].outputs[0].default_value = TRAIL['strength']
        cu.materials.clear()
        cu.materials.append(m)
        ob = bpy.data.objects.get('FILM_mars_trail') or bpy.data.objects.new('FILM_mars_trail', cu)
        self._link(ob)
        ks, ke = [], []
        for sid in ('4.2', '4.3'):
            a, b = self.segs[sid]['frames']
            lo = hi = un[a]
            for f in range(a, b + 1):
                lo, hi = min(lo, un[f]), max(hi, un[f])
                ks.append((f, (lo - lo_all) / (hi_all - lo_all), 'CONSTANT'))
                ke.append((f, (hi - lo_all) / (hi_all - lo_all), 'CONSTANT'))
        set_keys(fcurve(cu, 'bevel_factor_start'), ks)
        set_keys(fcurve(cu, 'bevel_factor_end'), ke)
        self.key_visible_range(ob, [(self.segs['4.2']['frames'][0], self.segs['4.3']['frames'][1])])
        self.report['mars_trail'] = {'radius_mm': round(r, 3), 'z_mm': round(z, 3),
                                     'longitude_deg': [round(lo_all + 3, 2), round(hi_all - 3, 2)]}

    def sunblind(self):
        """Panel outside the window, a vertical slit of slit_mm : only the slit lets the sun in (shadows only).  The
        timeline's sunbeam keys give the slit centre in units of the window width, measured in the window's mid
        plane from the window centre (the window is centred on the sun ray through the mechanism)."""
        sb = self.segs['1.1']['sunbeam']
        slit = sb['slit_mm']
        vc, zc = ST.window_centre()
        s = ST._dir(ST.SUN_AZ - ST.ROOM_AZ, ST.SUN_EL)          # towards the sun, room frame (u, v, z)
        u_mid = ST.WALL_U + ST.WALL_T / 2.0
        u_p = ST.WALL_U + ST.WALL_T + SUNBLIND['u_out']
        dv = s.y * (u_p - u_mid) / s.x                            # v shift from the window mid plane to the panel
        hw, hh = SUNBLIND['half_w'], SUNBLIND['half_h']
        bm = bmesh.new()
        for y0, y1 in ((-hw, -slit / 2.0), (slit / 2.0, hw)):
            vs = [bm.verts.new((0.0, y, z)) for y, z in ((y0, -hh), (y1, -hh), (y1, hh), (y0, hh))]
            bm.faces.new(vs)
        me = bpy.data.meshes.new('FILM_sunblind')
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.get('FILM_sunblind') or bpy.data.objects.new('FILM_sunblind', me)
        self._link(ob, shadow=True)
        ob.visible_camera = False
        ob.visible_diffuse = False
        ob.visible_glossy = False
        ob.visible_transmission = False
        ob.visible_volume_scatter = False
        mat = bpy.data.materials.new('FILM_sunblind')
        mat.diffuse_color = (0.1, 0.1, 0.1, 1.0)
        me.materials.append(mat)
        room = bpy.data.objects[ST.PREFIX + 'room']
        ob.parent = room
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.location = (u_p, vc + dv, zc + s.z * (u_p - u_mid) / s.x)
        keys = [(f, vc + v * ST.WIN_W + dv, 'LINEAR') for f, v in sb['keys']]
        set_keys(fcurve(ob, 'location', 1), keys)
        s11 = self.segs['1.1']['frames']
        self.key_visible_range(ob, [tuple(s11)])
        self.report['sunblind'] = {'u_panel': u_p, 'v_keys': [[f, round(v, 1)] for f, v, _ in keys], 'slit_mm': slit}

    # -------------------------------------------------------------- cameras
    def make_camera(self, name, frames, poses):
        cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
        cd.type = 'PERSP'
        cd.sensor_fit = 'AUTO'
        cd.sensor_width = 36.0
        cd.clip_start = 1.0
        cd.clip_end = 30000.0
        cd.dof.use_dof = False
        ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
        if ob.name not in self.cams.objects:
            self.cams.objects.link(ob)
        ob.rotation_mode = 'XYZ'
        cols = {k: [] for k in ('lx', 'ly', 'lz', 'rx', 'ry', 'rz', 'lens', 'sx', 'sy')}
        prev = None
        info = []
        for f in frames:
            tgt, az, el, dist, lens, up, shift = pose_params(poses, f, self.target_of)
            loc = tgt + _dir(az, el) * dist
            R = look_rotation(loc, tgt, up)
            eul = R.to_euler('XYZ', prev) if prev is not None else R.to_euler('XYZ')
            prev = eul
            for k, v in zip(('lx', 'ly', 'lz'), loc):
                cols[k].append((f, v, 'LINEAR'))
            for k, v in zip(('rx', 'ry', 'rz'), eul):
                cols[k].append((f, v, 'LINEAR'))
            cols['lens'].append((f, lens, 'LINEAR'))
            cols['sx'].append((f, shift.x, 'LINEAR'))
            cols['sy'].append((f, shift.y, 'LINEAR'))
            info.append((f, el))
        for i, k in enumerate(('lx', 'ly', 'lz')):
            set_keys(fcurve(ob, 'location', i), cols[k])
        for i, k in enumerate(('rx', 'ry', 'rz')):
            set_keys(fcurve(ob, 'rotation_euler', i), cols[k])
        set_keys(fcurve(cd, 'lens'), cols['lens'])
        set_keys(fcurve(cd, 'shift_x'), cols['sx'])
        set_keys(fcurve(cd, 'shift_y'), cols['sy'])
        return ob

    def cameras(self):
        sc = self.sc
        made = {}
        for s in self.T['segments']:
            cam = s.get('camera')
            if not cam:
                continue
            a, b = s['frames']
            extra = [x for x in self.T['segments'] if x.get('bg_camera') == cam['name']]
            if extra:
                b = max(x['frames'][1] for x in extra)
            made[cam['name']] = self.make_camera(cam['name'], range(a, b + 1), cam['poses'])
        n = 0
        for s in self.T['segments']:
            if not s.get('render_3d'):
                continue
            name = (s.get('camera') or {}).get('name') or s.get('bg_camera')
            m = sc.timeline_markers.new('S' + s['id'], frame=s['frames'][0])
            m.camera = made[name]
            n += 1
        sc.camera = made[self.T['segments'][0]['camera']['name']]
        # inset of 3.4 : second scene sharing every collection
        s34 = self.segs['3.4']
        ins = s34['inset']
        icam = self.make_camera(ins['name'], range(s34['frames'][0], s34['frames'][1] + 1), ins['poses'])
        isc = bpy.data.scenes.get(RF.INSET_SCENE)
        if isc is not None:
            bpy.data.scenes.remove(isc)
        isc = bpy.data.scenes.new(RF.INSET_SCENE)
        for c in sc.collection.children:
            if c.name != COLL_MAIN_ONLY:
                isc.collection.children.link(c)
        for o in sc.collection.objects:
            isc.collection.objects.link(o)
        isc.world = sc.world
        isc.camera = icam
        isc.frame_start, isc.frame_end = s34['frames']
        isc.render.resolution_x, isc.render.resolution_y = ins['resolution']
        for attr in ('view_transform', 'look', 'exposure', 'gamma'):
            setattr(isc.view_settings, attr, getattr(sc.view_settings, attr))
        isc.display_settings.display_device = sc.display_settings.display_device
        RF.apply_settings(isc)
        excl = {lc.name for lc in bpy.context.view_layer.layer_collection.children if lc.exclude}
        ivl = isc.view_layers[0]
        ivl.update()                                  # creates the layer collections of the new scene
        for lc in ivl.layer_collection.children:
            lc.exclude = lc.name in excl
        log('cameras : %d baked, %d markers, inset scene %s (%dx%d)' % (len(made), n, isc.name, *ins['resolution']))

    # -------------------------------------------------------------- all
    def build(self):
        t0 = time.time()
        self.scene_setup()
        self.prepass()
        self.film_objects()
        self.highlights()
        self.controller()
        self.visibility()
        self.cameras()
        self.sc.frame_set(1)
        self.report['build_s'] = round(time.time() - t0, 1)
        return self.report


def save():
    out = FILM_BLEND.resolve()
    if out in FORBIDDEN_OUT:
        raise SystemExit('refus : ne jamais écrire %s' % out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0          # no film.blend1 backup
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True, relative_remap=True)
    log('saved', out, '(%.1f MB)' % (out.stat().st_size / 1e6))


# ============================================================================= checks
def _eval_fc(idb, path, index=0):
    ad = idb.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return next(fc for fc in cb.fcurves if fc.data_path == path and fc.array_index == index)


TAU = 2 * math.pi


def wrap(x):
    return (x + math.pi) % (2 * math.pi) - math.pi


def blender_state(dg):
    """Readings of the machine in Blender (same method as tools/explainer/validate_blend.py)."""
    ob = lambda n: bpy.data.objects[n].evaluated_get(dg)
    Mw = lambda n: np.array(ob(n).matrix_world)
    lam = {}
    for n, key in (('B_b', 'soleil_moyen'), ('B_moon', 'lune'), ('B_t_nodes', 'noeud_ascendant')):
        M = Mw(n)
        lam[key] = -math.atan2(M[1, 0], M[0, 0])
    for key, n in (('mars', 'marker_mars'), ('soleil_vrai', 'marker_trueSun')):
        o = ob(n)
        p = o.matrix_world @ (sum((Vector(c) for c in bpy.data.objects[n].bound_box), Vector()) / 8.0)
        lam[key] = -math.atan2(p.y, p.x)
    Mq, Mm = Mw('B_q'), Mw('B_moon')
    a_world = -Mq[:3, 2] / np.linalg.norm(Mq[:3, 2])
    a_moon = Mm[:3, :3].T @ a_world
    q = math.atan2(a_moon[1], -a_moon[2])
    k_vis = (1 + a_world[2]) / 2
    psi = {}
    for which, n in (('metonic', 'B_n'), ('saros', 'B_g'), ('olympiad', 'B_o'), ('exeligmos', 'B_i')):
        M = Mw(n)
        psi[which] = math.atan2(-M[0, 1], M[1, 1])
    sl = ob('saros_slider').matrix_world.translation
    return {'lam': lam, 'q': q, 'k_vis': float(k_vis), 'psi': psi, 'saros_slider': Vector(sl)}


def verify(T):
    import engine as E
    import verify_beats as VB
    M = E.get_machine(False)
    sc = bpy.data.scenes[MAIN_SCENE]
    ctl = bpy.data.objects['AM_Controller']
    res = {'checks': []}

    def check(name, ok, detail):
        res['checks'].append({'check': name, 'ok': bool(ok), 'detail': detail})
        print('%-4s %s : %s' % ('OK' if ok else 'FAIL', name, detail), flush=True)
        return ok

    N = T['frame_end']
    # 1. keys -> every frame (F-curve evaluation) and sample frames through the depsgraph
    fcs = {k: _eval_fc(ctl, '["%s"]' % k) for k in ('crank', 'explode', 'patina')}
    worst = {k: 0.0 for k in fcs}
    exact = 0
    bl_crank = {}
    for x in T['frames']:
        f = x['f']
        c = L.f32(fcs['crank'].evaluate(f))
        bl_crank[f] = c
        exact += c == x['crank']
        worst['crank'] = max(worst['crank'], abs(c - x['crank']))
        worst['explode'] = max(worst['explode'], abs(fcs['explode'].evaluate(f) - x['explode']))
        worst['patina'] = max(worst['patina'], abs(fcs['patina'].evaluate(f) - x['patina']))
    check('clés -> frames[] (toutes les images)', worst['crank'] <= 2e-6 and worst['explode'] < 2e-5 and
          worst['patina'] < 2e-5, '%d images : manivelle identique (float32) sur %d, écart max %.2e an ; explode '
          '%.1e, patina %.1e' % (N, exact, worst['crank'], worst['explode'], worst['patina']))
    sample = sorted({b['frame'] for b in T['beats']} | set(range(1, N + 1, 97)) |
                    {s['frames'][0] for s in T['segments']} | {s['frames'][1] for s in T['segments']})
    bad = []
    for f in sample:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = L.f32(ctl.evaluated_get(dg)['crank'])
        if abs(ce - T['frames'][f - 1]['crank']) > 2e-6:
            bad.append((f, ce, T['frames'][f - 1]['crank']))
    check('manivelle évaluée (depsgraph, échantillon)', not bad, '%d images échantillon (beats, bords de plans, 1 '
          'sur 97)%s' % (len(sample), '' if not bad else ' ; ÉCARTS %s' % bad[:5]))
    # 2. cameras bound by the markers
    segs = {s['id']: s for s in T['segments']}
    badcam = []
    for s in T['segments']:
        if not s.get('render_3d'):
            continue
        want = (s.get('camera') or {}).get('name') or s.get('bg_camera')
        for f in (s['frames'][0], (s['frames'][0] + s['frames'][1]) // 2, s['frames'][1]):
            sc.frame_set(f)
            if sc.camera is None or sc.camera.name != want:
                badcam.append((s['id'], f, sc.camera.name if sc.camera else None))
    check('caméras liées par les marqueurs', not badcam, 'caméra du plan au début, au milieu et à la fin de chaque plan '
          'rendu%s' % ('' if not badcam else ' ; %s' % badcam))
    # 3. staging per shot (hide_render F-curves)
    probes = {'case_cover_front': lambda m, lb: m == 'case', 'ATL_back_plank_0': lambda m, lb: m == 'back',
              'ATL_bench_plank_0': lambda m, lb: m != 'back', 'ATL_sun': lambda m, lb: m != 'back',
              'ATL_sun_back': lambda m, lb: m == 'back', 'LABEL_Mars': lambda m, lb: lb}
    fch = {n: _eval_fc(bpy.data.objects[n], 'hide_render') for n in probes}
    badvis = []
    sw = None
    for s in T['segments']:
        if not s.get('render_3d'):
            continue
        for f in range(s['frames'][0], s['frames'][1] + 1):
            mode = {'wide': 'front'}.get(s['mode'], s['mode'])
            if mode == 'front_to_back':
                vis_back = fch['ATL_sun_back'].evaluate(f) < 0.5
                if vis_back and sw is None:
                    sw = f
                mode = 'back' if vis_back else 'front'
            for n, rule in probes.items():
                if (fch[n].evaluate(f) < 0.5) != rule(mode, bool(s.get('labels'))):
                    badvis.append((s['id'], f, n))
    check('mise en scène par plan (boîtier, atelier, rig arrière, étiquettes)', not badvis,
          'boîtier fermé seulement en 1.1, rig arrière dans les plans du dos (bascule de 5.1 à l\'image %s), '
          'étiquettes des planètes en 1.2c et 4.1-4.3%s' % (sw, '' if not badvis else ' ; %s' % badvis[:8]))
    # 4. beats : angles read in Blender vs engine.py, and the reading each beat needs
    beats_out = []
    glyph = {c['case']: c['glyph'] for c in M.engraved_table()['cells']}
    olab = {k: bpy.data.objects['txt_olympiad_%d' % k] for k in range(4)}
    lon_keys = ('soleil_moyen', 'lune', 'noeud_ascendant', 'mars', 'soleil_vrai')     # blender_state = engine names
    for b in T['beats']:
        f = b['frame']
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        c = L.f32(ctl.evaluated_get(dg)['crank'])
        B = blender_state(dg)
        st = M.state(c)
        errs = [abs(wrap(B['lam'][k] - float(st['lon'][k]))) for k in lon_keys]
        errs.append(abs(wrap(B['q'] - float(st['local']['q']))))
        errs += [abs(wrap(B['psi'][k] - float(st['psi'][k]))) for k in B['psi']]
        emax = max(errs)
        deg = lambda r: math.degrees(r) % 360.0
        lm, ls, ln, lt = deg(B['lam']['lune']), deg(B['lam']['soleil_moyen']), deg(B['lam']['noeud_ascendant']), \
            deg(B['lam']['soleil_vrai'])
        elong = (lm - ls) % 360.0
        node_d = min(abs((lm - ln + 180) % 360 - 180), abs((lm - ln) % 360 - 180))
        zs = lambda d: E.zodiac_read(M.zodiac, d)
        read = {'crank': c, 'elongation_deg': round(elong, 3), 'boule_eclairee': round(B['k_vis'], 4),
                'lune': '%.2f° %s' % (zs(lm)['degre_dans_le_signe'], zs(lm)['signe_grec']),
                'aiguille_de_date': '%.2f° %s' % (zs(ls)['degre_dans_le_signe'], zs(ls)['signe_grec']),
                'sphere_doree': '%.2f° %s' % (zs(lt)['degre_dans_le_signe'], zs(lt)['signe_grec']),
                'lune_noeud_deg': round(node_d, 3)}
        ok = emax < 1e-4 and c == b['crank']
        p = b['params']
        ck = b['check']
        if ck == 'phase':
            ok &= abs(((elong - p['target_deg']) + 180) % 360 - 180) <= p['tol_deg']
            ok &= B['k_vis'] <= p.get('frac_max', 1.0) + 1e-3 and B['k_vis'] >= p.get('frac_min', 0.0) - 1e-3
            if 'moon_sign' in p:
                ok &= zs(lm)['signe_grec'] == p['moon_sign']
            if 'sun_sign' in p:
                ok &= zs(ls)['signe_grec'] == p['sun_sign'] and zs(lt)['signe_grec'] == p['sun_sign']
        elif ck == 'fraction':
            ok &= p['lo'] - 1e-3 <= B['k_vis'] <= p['hi'] + 1e-3
        elif ck == 'dragon':
            ok &= abs(elong - 180.0) <= 1.0 and node_d <= p['node_max_deg']
        elif ck in ('games', 'games_entry'):
            og = M.subsidiary['olympiad']
            tilt = math.radians(og.get('sector_tilt_deg', 0.0))
            sector = lambda ps: og['labels'][int(((ps - tilt) % TAU) // (TAU / og['sectors']))]
            po = B['psi']['olympiad']
            cxy = Vector(T['anchors']['games_pointer']['axis'])
            best = None
            for k, o in olab.items():
                oe = o.evaluated_get(dg)
                cc = oe.matrix_world @ (sum((Vector(q) for q in o.bound_box), Vector()) / 8.0)
                pk = math.atan2(-(cc.x - cxy.x), cc.y - cxy.y)
                d = abs(wrap(po - pk))
                if best is None or d < best[0]:
                    best = (d, o.data.body.replace('\n', ' '))
            read['secteur_jeux'] = sector(po)
            read['etiquette_gravee_sous_l_aiguille'] = best[1]
            read['aiguille_jeux_ecart_au_milieu_deg'] = round(math.degrees(best[0]), 2)
            ok &= sector(po) == p['label'] and best[1] == p['label'] and best[0] < math.radians(45.0)
            if ck == 'games_entry':
                sc.frame_set(f - 1)
                Bp = blender_state(bpy.context.evaluated_depsgraph_get())
                read['secteur_jeux_image_precedente'] = sector(Bp['psi']['olympiad'])
                ok &= sector(Bp['psi']['olympiad']) != p['label']
                sc.frame_set(f)
        elif ck == 'saros_entry':
            def cell_of(Bst, cr):
                ps_e = float(M.psi_spiral('saros', cr))
                ps = (Bst['psi']['saros'] % TAU) + TAU * math.floor(ps_e / TAU)
                ps += TAU * round((ps_e - ps) / TAU)             # same turn as the engine (radius checked below)
                rho_e = float(M.state(cr)['rho']['saros'])
                rho_b = (Bst['saros_slider'].xy - Vector(M.S['axes_world_xy']['G'])).length
                return min(int(ps / (4 * TAU) * 223), 222) + 1, abs(rho_b - rho_e)
            cell1, dr1 = cell_of(B, c)
            sc.frame_set(f - 1)
            Bp = blender_state(bpy.context.evaluated_depsgraph_get())
            cell0, dr0 = cell_of(Bp, bl_crank[f - 1])
            sc.frame_set(f)
            g = bpy.data.objects['txt_saros_glyph_%03d' % p['cell']].evaluated_get(dg)
            gc = g.matrix_world @ (sum((Vector(q) for q in g.bound_box), Vector()) / 8.0)
            sc_xy = Vector(M.S['axes_world_xy']['G'])
            sl = B['saros_slider']
            dpsi = abs(wrap(math.atan2(-(sl.x - sc_xy.x), sl.y - sc_xy.y) - math.atan2(-(gc.x - sc_xy.x),
                                                                                       gc.y - sc_xy.y)))
            dr = abs((sl.xy - sc_xy).length - (gc.xy - sc_xy).length)
            read['case_saros'] = [cell0, cell1]
            read['curseur_rayon_vs_moteur_mm'] = round(max(dr0, dr1), 4)
            read['curseur_vs_signe'] = {'dpsi_deg': round(math.degrees(dpsi), 2), 'dr_mm': round(dr, 2),
                                        'texte': g.data.body.replace('\n', ' ')}
            ok &= cell0 == p['cell'] - 1 and cell1 == p['cell'] and max(dr0, dr1) < 0.05
            # sanity : the slider is next to the engraved sign (the sign sits in the band beside the slider's
            # groove, half a pitch away ; the cell itself is read above from the pointer angle)
            ok &= math.degrees(dpsi) < 4.5 and dr < 0.75 * M.spirals['saros']['pitch']
            ok &= g.data.body.split() == p['glyph'].split()
            ok &= glyph[p['cell']] == p['glyph'] and all(not glyph[k] for k in p['empty'])
        elif ck == 'exeligmos':
            ok &= M.read_back(c)['exeligmos']['heures_a_ajouter'] == p['hours']
        elif ck in ('mars_station', 'mars_retro', 'mars_replay'):
            pass                                   # rates : below, with the controller detached
        elif ck == 'sun_sign':
            ok &= zs(ls)['signe_grec'] == p['sign'] and zs(lt)['signe_grec'] == p['sign']
            if 'deg_lo' in p:
                ok &= p['deg_lo'] <= zs(ls)['degre_dans_le_signe'] <= p['deg_hi']
        beats_out.append({'id': b['id'], 'frame': f, 'segment': b['segment'], 'check': ck, 'ok': bool(ok),
                          'max_err_blender_vs_engine_rad': emax, 'blender': read})
    # Mars rates measured in Blender (finite differences of the marker's longitude, controller detached)
    ad = ctl.animation_data
    act, slot = ad.action, ad.action_slot
    ad.action = None

    def mars_lam(cr):
        dg = AN.set_state(cr, 0.0)
        o = bpy.data.objects['marker_mars']
        pnt = o.evaluated_get(dg).matrix_world @ (sum((Vector(q) for q in o.bound_box), Vector()) / 8.0)
        return -math.atan2(pnt.y, pnt.x)

    def mars_rate(cr, h=2e-4):
        return wrap(mars_lam(cr + h) - mars_lam(cr - h)) / (2 * h)

    for bo, b in zip(beats_out, T['beats']):
        if b['check'] == 'mars_station':
            c0, c1 = bl_crank[b['frame'] - 1], bl_crank[b['frame']]
            r0, r1 = mars_rate(c0), mars_rate(c1)
            bo['blender']['mars_deg_par_an'] = [round(math.degrees(r0), 2), round(math.degrees(r1), 2)]
            bo['ok'] &= (r0 > 0 >= r1) if b['params']['n'] == 1 else (r0 < 0 <= r1)
        elif b['check'] == 'mars_retro':
            r = mars_rate(bl_crank[b['frame']])
            bo['blender']['mars_deg_par_an'] = round(math.degrees(r), 2)
            bo['ok'] &= r < 0
        elif b['check'] == 'mars_replay':
            s = segs['4.3']
            fr = range(s['frames'][0], s['frames'][1] + 1)
            rates = [mars_rate(bl_crank[x]) for x in fr]
            st_ = [x for x, r0, r1 in zip(list(fr)[1:], rates, rates[1:]) if (r0 > 0) != (r1 > 0)]
            bo['blender']['stations_images'] = st_
            bo['ok'] &= len(st_) == 2
    AN.set_state(0.0, 0.0)
    ad.action = act
    ad.action_slot = slot
    for bo in beats_out:
        check('beat %s (%s, image %d)' % (bo['id'], bo['segment'], bo['frame']), bo['ok'],
              'Blender vs moteur %.1e rad ; %s' % (bo['max_err_blender_vs_engine_rad'],
                                                   json.dumps(bo['blender'], ensure_ascii=False)))
    res['beats'] = beats_out
    # 5. the checks of verify_beats.py, run on the cranks Blender evaluates
    Tb = json.loads(json.dumps(T))
    for x in Tb['frames']:
        x['crank'] = bl_crank[x['f']]
    VB.RESULTS.clear()
    for b in Tb['beats']:
        b['crank'] = bl_crank[b['frame']]
        VB.check_beat(Tb, b)
    VB.check_blinks(Tb)
    n_bad = [r for r in VB.RESULTS if r['level'] == 'ERROR']
    check('verify_beats.py sur les valeurs de Blender', not n_bad, '%d contrôles (beats avec synchro et tenue, '
          'clignotements 6.1)%s' % (len(VB.RESULTS), '' if not n_bad else ' ; %s' % [r['check'] for r in n_bad]))
    res['verify_beats'] = VB.RESULTS[:]
    # 6. highlights keyed
    badhl = []
    for h in T['highlights']:
        peak = max(h['keys'], key=lambda k: k['v'])
        for t in h['targets']:
            ob = bpy.data.objects.get(t)
            if ob is None:
                badhl.append((h['id'], t, 'absent'))
                continue
            for slot_ in ob.material_slots:
                m = slot_.material
                node = m.node_tree.nodes.get('hl_' + h['id']) if m else None
                if node is None:
                    badhl.append((h['id'], t, 'pas de nœud'))
                    continue
                v = _eval_fc(m.node_tree, 'nodes["hl_%s"].outputs[0].default_value' % h['id']).evaluate(peak['f'])
                if abs(v - peak['v']) > 1e-5:
                    badhl.append((h['id'], t, v))
    check('surlignages', not badhl, '%d surlignages, matériaux propres à leurs cibles, valeur au sommet = clé%s'
          % (len(T['highlights']), '' if not badhl else ' ; %s' % badhl[:5]))
    shared = [s.material.name for s in bpy.data.objects['front_plate'].material_slots]
    check('matériaux partagés intacts', all(not n.startswith('FILMHL_') for n in shared) and
          'hl_crank' not in bpy.data.materials['AM_bronze'].node_tree.nodes,
          'AM_bronze et AM_engraving sans émission (seules les cibles ont une copie) : front_plate -> %s' % shared)
    res['ok'] = all(c['ok'] for c in res['checks'])
    CHECK.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print('[film] checks : %d OK, %d FAIL -> %s' % (sum(c['ok'] for c in res['checks']),
                                                     sum(not c['ok'] for c in res['checks']), CHECK), flush=True)
    return res['ok']


def main(argv):
    T = json.loads((L.FILM / 'timeline.json').read_text())
    if '--verify-only' not in argv:
        src = pathlib.Path(bpy.data.filepath).resolve()
        if src.name not in ('am_atelier.blend',):
            log('attention : fichier source %s (attendu am_atelier.blend)' % src)
        rep = Builder(T).build()
        log('report', json.dumps(rep, ensure_ascii=False))
        if '--no-save' not in argv:
            save()
    ok = verify(T)
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
