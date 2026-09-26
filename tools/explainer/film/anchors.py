"""Callout anchors of the film, projected frame by frame (Blender 5.2) -> build/out/explainer/film/anchors.json.

    BL=/Applications/Blender.app/Contents/MacOS/Blender
    $BL -b build/out/explainer/film/film.blend --factory-startup --python-exit-code 1 \
        -P tools/explainer/film/anchors.py                    # every anchor, every frame where it is used
    $BL ... -P tools/explainer/film/anchors.py -- --frames 1300-1400 --out /tmp/a.json     # subset (tests)

film.blend is made by build_film.py and is only read (never saved).  The module is also imported by build_film.py:
the class Anchors gives the world position of any anchor of timeline.json at the current depsgraph state (camera
targets {anchor, crank} and {track: anchor}).

Anchor types (timeline.json anchors{}, positions in mm, world) :
  point    {object, world} : the world point given at crank 0 / explode 0, carried by the object ;
  center   {object}        : centre of the object's local bounding box, carried by the object ;
  radial   {object, radius, z} : direction of the object's centre seen from the front axis (0, 0), at that radius and
                             height (height follows the front plate when the machine explodes) ;
  tip      {object, axis [cx, cy], frac} : the vertex of the object farthest from the axis (found at crank 0), and the
                             point at frac of the way from the axis to it (same height as that vertex) ;
  at_crank {object, crank} : the object's bounding-box centre at that crank (explode 0), then fixed in the world.

Frames exported for an anchor = every frame of every rendered segment (kind 3d / split / card) where it is used : a
callout's anchor, a 2D line end (lines_2d), an overlay translated onto it, or a camera target {track}.  Rows :
[frame, x_px, y_px, depth_mm, in_frame, occluded] ; x, y in a 1920 x 1080 picture (origin top left, y down, the
camera shift of the split shots included) ; depth = distance along the view axis ; in_frame = in front of the camera
and inside the picture ; occluded = a ray from the camera meets another object more than 1.5 mm (+ 0.2 %) before
the anchor (the anchor's own object never occludes it).  For split shots the right half is covered by the diagram :
the rows say where the point is, the compositor decides.
"""
import json
import math
import pathlib
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import filmlib as L  # noqa: E402

OUT = L.FILM / 'anchors.json'
OCCLUSION_TOL = 1.5             # mm
W, H = L.WIDTH, L.HEIGHT


def _f32(x):
    return L.f32(x)


def set_state(crank, explode=0.0):
    """Sets AM_Controller directly (the controller must have no action assigned) and evaluates the scene."""
    ctl = bpy.data.objects['AM_Controller']
    ctl['crank'] = _f32(crank)
    ctl['explode'] = float(explode)
    ctl.update_tag()
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


class Anchors:
    """World positions of the anchors of timeline.json.  The reference state (crank 0, explode 0) is evaluated once at
    construction : the controller's action is detached for that and restored afterwards."""

    def __init__(self, defs):
        self.defs = defs
        ctl = bpy.data.objects['AM_Controller']
        ad = ctl.animation_data
        saved = (ad.action, ad.action_slot) if ad else (None, None)
        saved_vals = {k: ctl[k] for k in ('crank', 'explode')}
        if ad:
            ad.action = None
        dg = set_state(0.0, 0.0)
        self.local, self.fixed = {}, {}
        self.plate_z0 = bpy.data.objects['front_plate'].evaluated_get(dg).matrix_world.translation.z
        for name, d in defs.items():
            ob = bpy.data.objects[d['object']]
            oe = ob.evaluated_get(dg)
            M = oe.matrix_world.copy()
            t = d['type']
            if t == 'point':
                self.local[name] = M.inverted() @ Vector(d['world'])
            elif t in ('center', 'radial'):
                self.local[name] = sum((Vector(c) for c in oe.bound_box), Vector()) / 8.0
            elif t == 'tip':
                ax = Vector(d['axis'][:2])
                best = max(ob.data.vertices, key=lambda v: ((M @ v.co).xy - ax).length)
                self.local[name] = best.co.copy()
            elif t != 'at_crank':
                raise ValueError('anchor %s : type %s inconnu' % (name, t))
        for name, d in defs.items():
            if d['type'] == 'at_crank':
                dg = set_state(d['crank'], 0.0)
                oe = bpy.data.objects[d['object']].evaluated_get(dg)
                self.fixed[name] = oe.matrix_world @ (sum((Vector(c) for c in oe.bound_box), Vector()) / 8.0)
        ctl['crank'], ctl['explode'] = saved_vals['crank'], saved_vals['explode']
        if ad:
            ad.action = saved[0]
            if saved[0] is not None and saved[1] is not None:
                ad.action_slot = saved[1]
        bpy.context.view_layer.update()

    def world(self, name, dg):
        d = self.defs[name]
        t = d['type']
        if t == 'at_crank':
            return self.fixed[name].copy()
        M = bpy.data.objects[d['object']].evaluated_get(dg).matrix_world
        if t in ('point', 'center'):
            return M @ self.local[name]
        if t == 'radial':
            c = M @ self.local[name]
            a = math.atan2(c.y, c.x)
            dz = bpy.data.objects['front_plate'].evaluated_get(dg).matrix_world.translation.z - self.plate_z0
            return Vector((d['radius'] * math.cos(a), d['radius'] * math.sin(a), d['z'] + dz))
        p = M @ self.local[name]                                     # tip
        ax = Vector((d['axis'][0], d['axis'][1], p.z))
        return ax + d['frac'] * (p - ax)


def project(scene, cam_eval, p):
    """World point -> (x_px, y_px, depth_mm, in_frame) in the full-resolution picture (1920 x 1080)."""
    co = world_to_camera_view(scene, cam_eval, p)
    x, y = co.x * W, (1.0 - co.y) * H
    inside = co.z > 0.0 and 0.0 <= x <= W and 0.0 <= y <= H
    return x, y, co.z, inside


def occluded(scene, dg, cam_eval, p, own):
    o = cam_eval.matrix_world.translation
    v = p - o
    dist = v.length
    hit, loc, _n, _i, ob, _m = scene.ray_cast(dg, o, v.normalized(), distance=max(dist - OCCLUSION_TOL -
                                                                                 0.002 * dist, 0.0))
    if not hit:
        return False
    return ob is not None and ob.original.name != own


def usage(T):
    """{anchor: [segment ids]} : where each anchor is used in a rendered segment."""
    use = {}
    for s in T['segments']:
        if not s.get('render_3d'):
            continue
        names = {c['anchor'] for c in s.get('callouts', []) if c.get('anchor')}
        for ln in s.get('lines_2d', []):
            names |= {ln['from'], ln['to']}
        names |= {o['anchor'] for o in T['overlays'] if o['segment'] == s['id'] and o.get('anchor')}
        for cam in (s.get('camera'), s.get('inset')):
            for p in (cam or {}).get('poses', []):
                if isinstance(p['target'], dict) and 'track' in p['target']:
                    names.add(p['target']['track'])
        for n in names:
            use.setdefault(n, []).append(s['id'])
    return use


def main(argv):
    T = json.loads((L.FILM / 'timeline.json').read_text())
    out = pathlib.Path(argv[argv.index('--out') + 1]) if '--out' in argv else OUT
    rng = None
    if '--frames' in argv:
        a, _, b = argv[argv.index('--frames') + 1].partition('-')
        rng = (int(a), int(b or a))
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1.0
    A = Anchors(T['anchors'])
    use = usage(T)
    segs = {s['id']: s for s in T['segments']}
    per_frame = {}                                   # frame -> [anchors]
    for name, sids in use.items():
        for sid in sids:
            a, b = segs[sid]['frames']
            for f in range(a, b + 1):
                if rng is None or rng[0] <= f <= rng[1]:
                    per_frame.setdefault(f, []).append(name)
    rows = {n: [] for n in use}
    bad_cam = []
    for f in sorted(per_frame):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        seg = segs[T['frames'][f - 1]['seg']]
        want = (seg.get('camera') or {}).get('name') or seg.get('bg_camera')
        if sc.camera is None or sc.camera.name != want:
            bad_cam.append(f)
        cam = sc.camera.evaluated_get(dg)
        for name in per_frame[f]:
            p = A.world(name, dg)
            x, y, z, inside = project(sc, cam, p)
            occ = occluded(sc, dg, cam, p, T['anchors'][name]['object']) if inside else False
            rows[name].append([f, round(x, 1), round(y, 1), round(z, 1), int(inside), int(occ)])
    res = {'title': T['title'], 'resolution': [W, H], 'fps': T['fps'], 'frame_end': T['frame_end'],
           'source': 'build/out/explainer/film/film.blend (build_film.py) + timeline.json',
           'columns': ['frame', 'x_px', 'y_px', 'depth_mm', 'in_frame', 'occluded'],
           'conventions': {'pixels': 'image 1920 x 1080, origine en haut à gauche, y vers le bas ; décentrement des '
                                     'plans partagés inclus',
                           'frames': 'toutes les images des plans rendus (3d, split, card) où l\'ancre sert : '
                                     'callout, extrémité de trait (lines_2d), calque translaté (overlays.anchor), '
                                     'cible de caméra suivie',
                           'in_frame': 'devant la caméra et dans l\'image',
                           'occluded': 'un autre objet coupe le rayon caméra -> ancre (tolérance 1,5 mm + 0,2 %)',
                           'types': 'point, center, radial, tip, at_crank : voir tools/explainer/film/anchors.py'},
           'camera_mismatch_frames': bad_cam,
           'anchors': {n: dict(T['anchors'][n], segments=use[n], frames=rows[n]) for n in sorted(rows)}}
    out.write_text(json.dumps(res, ensure_ascii=False, separators=(',', ':')))
    n = sum(len(r) for r in rows.values())
    off = {k: sum(1 for r in v if not r[4]) for k, v in rows.items() if any(not r[4] for r in v)}
    print('[anchors] %d anchors, %d rows, %d frames -> %s' % (len(rows), n, len(per_frame), out))
    print('[anchors] out of frame (rows) :', off)
    print('[anchors] camera mismatch frames :', bad_cam[:20])
    return res


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
