"""Mesh construction (extruded islands, crowns, spheres) with foreach_set, and mesh checks."""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt


class MeshError(Exception):
    pass


def signed_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def triangulate(loops):
    """CDT of one island (outer CCW + holes CW). Returns triangles (indices into the stacked
    loops), CCW. Raises if the CDT adds vertices or the triangle count is wrong."""
    pts = np.vstack(loops)
    n = len(pts)
    faces, off = [], 0
    for l in loops:
        faces.append(list(range(off, off + len(l))))
        off += len(l)
    vs = [Vector((float(x), float(y))) for x, y in pts]
    r = delaunay_2d_cdt(vs, [], faces, 3, 1e-9)
    if len(r[0]) != n:
        raise MeshError('CDT added/merged vertices (%d -> %d): self-intersecting contour' % (n, len(r[0])))
    idx = np.empty(n, np.int64)
    for i, o in enumerate(r[3]):
        if len(o) != 1:
            raise MeshError('CDT merged vertices')
        idx[i] = o[0]
    tris = np.array([[idx[i] for i in f] for f in r[2]], np.int64)
    if tris.ndim != 2 or tris.shape[1] != 3:
        raise MeshError('CDT returned non-triangles')
    expect = n + 2 * (len(loops) - 1) - 2
    if len(tris) != expect:
        raise MeshError('CDT triangle count %d != %d' % (len(tris), expect))
    a, b, c = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    ar = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    flip = ar < 0
    tris[flip] = tris[flip][:, ::-1]
    # no edge used by more than 2 triangles
    e = np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    if cnt.max() > 2:
        raise MeshError('CDT edge used %d times' % cnt.max())
    return tris


class Builder:
    """Accumulates vertices and polygons (variable size)."""

    def __init__(self):
        self.V = []
        self.P = []
        self.nv = 0

    def add_verts(self, v):
        self.V.append(np.asarray(v, float))
        base = self.nv
        self.nv += len(v)
        return base

    def add_polys(self, polys, base=0):
        for p in polys:
            self.P.append([int(i) + base for i in p])

    def prism(self, islands, z0, z1, axis='z'):
        area = 0.0
        for loops in islands:
            loops = [np.asarray(l, float) for l in loops]
            tris = triangulate(loops)
            pts = np.vstack(loops)
            n = len(pts)
            # contour area on the stored (float32) coordinates, like the z range (spec 5.5)
            area += sum(signed_area(l.astype(np.float32).astype(np.float64)) for l in loops)
            lo = np.column_stack([pts, np.full(n, z0)])
            hi = np.column_stack([pts, np.full(n, z1)])
            V = np.vstack([lo, hi])
            if axis == 'x':
                V = V[:, [2, 0, 1]]
            base = self.add_verts(V)
            self.add_polys((tris + n).tolist(), base)
            self.add_polys(tris[:, ::-1].tolist(), base)
            off = 0
            walls = []
            for l in loops:
                L = len(l)
                for i in range(L):
                    a, b = off + i, off + (i + 1) % L
                    walls.append((a, b, b + n, a + n))
                off += L
            self.add_polys(walls, base)
        return area

    def trimesh(self, V, T):
        base = self.add_verts(V)
        self.add_polys(np.asarray(T).tolist(), base)

    def sphere(self, c, r, n_lon=48, n_lat=24, half=0):
        """Closed UV sphere (half=0) or hemisphere (half=+1 upper z, -1 lower) with a flat cap."""
        c = np.asarray(c, float)
        if half == 0:
            lats = np.linspace(-math.pi / 2, math.pi / 2, n_lat + 1)[1:-1]
        else:
            lats = np.linspace(0.0, math.pi / 2, n_lat // 2 + 1)[:-1] * half
        lon = np.arange(n_lon) * 2 * math.pi / n_lon
        rings = [np.column_stack([r * math.cos(la) * np.cos(lon), r * math.cos(la) * np.sin(lon),
                                  np.full(n_lon, r * math.sin(la))]) for la in lats]
        nr = len(rings)
        last = (nr - 1) * n_lon
        extra = []
        P = []
        for k in range(nr - 1):
            for i in range(n_lon):
                j = (i + 1) % n_lon
                a, b = k * n_lon + i, k * n_lon + j
                cc, d = (k + 1) * n_lon + j, (k + 1) * n_lon + i
                P.append((a, b, cc, d) if half >= 0 else (d, cc, b, a))
        e0 = nr * n_lon
        if half == 0:
            extra = [[0, 0, r], [0, 0, -r]]
            top, bot = e0, e0 + 1
            for i in range(n_lon):
                j = (i + 1) % n_lon
                P.append((last + i, last + j, top))
                P.append((j, i, bot))
        elif half > 0:
            extra = [[0, 0, r], [0, 0, 0]]
            top, ctr = e0, e0 + 1
            for i in range(n_lon):
                j = (i + 1) % n_lon
                P.append((last + i, last + j, top))
                P.append((j, i, ctr))
        else:
            extra = [[0, 0, -r], [0, 0, 0]]
            bot, ctr = e0, e0 + 1
            for i in range(n_lon):
                j = (i + 1) % n_lon
                P.append((last + j, last + i, bot))
                P.append((i, j, ctr))
        V = np.vstack(rings + [np.array(extra, float)]) + c
        base = self.add_verts(V)
        self.add_polys(P, base)

    def to_mesh(self, name):
        V = np.vstack(self.V) if self.V else np.zeros((0, 3))
        me = bpy.data.meshes.new(name)
        me.vertices.add(len(V))
        me.vertices.foreach_set('co', V.astype(np.float32).ravel())
        tot = np.array([len(p) for p in self.P], np.int32)
        start = np.concatenate([[0], np.cumsum(tot)[:-1]]).astype(np.int32)
        flat = np.concatenate([np.asarray(p, np.int32) for p in self.P])
        me.loops.add(len(flat))
        me.loops.foreach_set('vertex_index', flat)
        me.polygons.add(len(self.P))
        me.polygons.foreach_set('loop_start', start)
        me.polygons.foreach_set('loop_total', tot)
        me.update(calc_edges=True)
        if me.validate():
            raise MeshError('mesh %s needed validation fixes' % name)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(30))
        return me


def mesh_arrays(me):
    V = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', V)
    me.calc_loop_triangles()
    T = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get('vertices', T)
    return V.reshape(-1, 3).astype(np.float64), T.reshape(-1, 3)


def check_mesh(me):
    """Closed, manifold, consistently oriented (per connected shell) and volume (float64)."""
    bm = bmesh.new()
    bm.from_mesh(me)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    noncontig = sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    # shells
    bm.verts.ensure_lookup_table()
    seen = set()
    shells = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        shells += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            x = stack.pop()
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
    bm.free()
    V, T = mesh_arrays(me)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    vol = float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0)
    return {'non_manifold': nonman, 'non_contiguous': noncontig, 'boundary': boundary,
            'shells': shells, 'volume': vol, 'verts': len(me.vertices), 'faces': len(me.polygons),
            'ok': nonman == 0 and noncontig == 0 and boundary == 0 and vol > 0}


def part_mesh(spec, p, shrink=0.0, name=None):
    """Mesh of one catalogue part (model units). shrink = crown flank shrink (print backlash/2)."""
    from am import crown as CR
    from am.outline import circle, ccw
    B = Builder()
    area = None
    if p['kind'] == 'prism':
        area = B.prism(p['islands'], p['z'][0], p['z'][1], p['axis'])
    elif p['kind'] == 'crown':
        w = p['extra']['crown']
        V, T, z, nv = CR.crown_teeth(spec, w, shrink=shrink)
        B.trimesh(V, T)
        c = spec.crowns[w]
        rng = c['disc']['x'] if w == 'a1' else c['disc']['u']
        B.prism([[ccw(circle(0.0, 0.0, c['disc']['r_out'], 256))]], rng[0], rng[1], 'x')
    elif p['kind'] == 'sphere':
        B.sphere(p['extra']['center'], p['extra']['radius'])
    elif p['kind'] == 'hemisphere':
        B.sphere(p['extra']['center'], p['extra']['radius'], half=p['extra']['up'])
    me = B.to_mesh(name or p['name'])
    return me, area
