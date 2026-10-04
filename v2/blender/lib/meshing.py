# copié de build/blender_scripts/meshing.py (v1) — sans sphere ni part_mesh (liés à la spec v1),
# docstrings traduites en français, code inchangé.
"""Construction de maillages (îlots extrudés, maillages triangulés) par foreach_set, et contrôles de maillage."""
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
    """Triangulation contrainte (CDT) d'un îlot (bord trigonométrique + trous horaires). Renvoie les triangles
    (indices dans les boucles empilées), trigonométriques. Lève MeshError si la CDT ajoute des sommets ou si le
    nombre de triangles est faux."""
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
    # aucune arête partagée par plus de 2 triangles
    e = np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    if cnt.max() > 2:
        raise MeshError('CDT edge used %d times' % cnt.max())
    return tris


class Builder:
    """Accumule sommets et polygones (de taille variable)."""

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
            # aire du contour sur les coordonnées stockées (float32), comme l'étendue en z (spec v1 5.5)
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
    """Fermé, variété, orienté de façon cohérente (par coque connexe), et volume (float64)."""
    bm = bmesh.new()
    bm.from_mesh(me)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    noncontig = sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    # coques
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
