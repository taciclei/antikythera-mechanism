# copié de build/blender_scripts/meshing.py (v1) : mesh_arrays et check_mesh (adaptés) ; le reste est propre à la v2.
"""Outils géométriques du contrôle 3D de la v2 (utilisés par v2/blender/check.py).

`mesh_arrays` et `check_mesh` viennent de la v1 (adaptés : maillage évalué, arêtes isolées, faces dégénérées : aire
nulle ou épaisseur sous la précision float32, aire et épaisseur minimales). Le reste (BVH en repère monde, boîtes
englobantes, parité de rayons, jeu approché, angles) est propre à la v2. Aucune dépendance hors de bpy, bmesh,
mathutils et numpy.
"""
import math

import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ZERO_AREA = 1e-9      # mm² : en dessous, une face est considérée d'aire nulle
EPS32 = float(np.finfo(np.float32).eps)
THIN_ULPS = 4.0       # une face plus mince que 4 ulp float32 des coordonnées a ses sommets alignés (dégénérée)
THIN_MIN = 1e-6       # mm : plancher de cette épaisseur
RAY_DIRS = (Vector((0.5773, 0.6124, 0.5402)).normalized(), Vector((-0.6421, 0.3307, 0.6917)).normalized())


# ---------------------------------------------------------------- propriétés personnalisées
def as_list(v):
    """Liste de chaînes depuis une propriété (liste, tableau IDProperty, chaîne « a,b » ou None)."""
    if v is None:
        return []
    if isinstance(v, str):
        return [s.strip() for s in v.split(',') if s.strip()]
    if hasattr(v, 'to_list'):
        v = v.to_list()
    return [str(s) for s in v]


def as_vec(v, default=(0.0, 0.0, 1.0)):
    """Vecteur unitaire numpy depuis une propriété `axis` (ou la valeur par défaut)."""
    if v is None:
        v = default
    if hasattr(v, 'to_list'):
        v = v.to_list()
    a = np.asarray(v, float).ravel()
    n = np.linalg.norm(a)
    return a / n if a.size == 3 and n > 0 else np.asarray(default, float)


class Resolver:
    """Retrouve un objet par son nom, par ce nom avec « # » → « . » (nom d'objet de parts.py : obj_name), par ses
    propriétés `part_id` (parts.py) ou `id`, puis par `source` si elle est unique."""

    def __init__(self, objects):
        self.by_name = {o.name: o for o in objects}
        self.by_id = {}
        src = {}
        for o in objects:
            for k in ('part_id', 'id'):
                if k in o.keys():
                    self.by_id.setdefault(str(o[k]), o)
            if 'source' in o.keys():
                src.setdefault(str(o['source']), []).append(o)
        self.by_source = {k: v[0] for k, v in src.items() if len(v) == 1}

    def get(self, key):
        key = str(key)
        for k in (key, key.replace('#', '.')):
            o = self.by_name.get(k) or self.by_id.get(k)
            if o is not None:
                return o
        return self.by_source.get(key)


# ---------------------------------------------------------------- maillages (copié/adapté de meshing.py v1)
def mesh_arrays(me):
    """Sommets (float64, n×3, repère local) et triangles (m×3) d'un maillage."""
    V = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', V)
    if hasattr(me, 'calc_loop_triangles'):
        me.calc_loop_triangles()
    T = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get('vertices', T)
    return V.reshape(-1, 3).astype(np.float64), T.reshape(-1, 3)


def face_metrics(me, V):
    """(aire, épaisseur) de chaque face, en float64 : aire de Newell, épaisseur = 2·aire / plus grande arête (hauteur
    d'un triangle). Les sommets sont en float32 : des points alignés y gardent une aire résiduelle de l'ordre de
    arête × ulp(coordonnées), bien au-dessus de ZERO_AREA ; seule l'épaisseur les révèle."""
    n = len(me.polygons)
    if n == 0:
        return np.zeros(0), np.zeros(0)
    ls = np.empty(n, np.int64)
    lt = np.empty(n, np.int64)
    me.polygons.foreach_get('loop_start', ls)
    me.polygons.foreach_get('loop_total', lt)
    lv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get('vertex_index', lv)
    order = np.argsort(ls, kind='stable')
    ls, lt = ls[order], lt[order]
    starts = np.concatenate([[0], np.cumsum(lt)[:-1]])          # boucles de chaque face, mises bout à bout
    idx = np.arange(int(lt.sum())) + np.repeat(ls - starts, lt)
    nxt = np.arange(len(idx)) + 1
    nxt[starts + lt - 1] = starts
    P = V[lv[idx]]
    Q = P[nxt]
    area = 0.5 * np.linalg.norm(np.add.reduceat(np.cross(P, Q), starts, axis=0), axis=1)
    lmax = np.maximum.reduceat(np.linalg.norm(Q - P, axis=1), starts)
    thick = np.where(lmax > 0, 2.0 * area / np.where(lmax > 0, lmax, 1.0), 0.0)
    out_a, out_t = np.empty(n), np.empty(n)
    out_a[order], out_t[order] = area, thick
    return out_a, out_t


def thin_tolerance(V):
    """Épaisseur sous laquelle une face est dégénérée : quelques ulp float32 des coordonnées locales (≥ THIN_MIN)."""
    R = float(np.abs(V).max()) if len(V) else 0.0
    return max(THIN_MIN, THIN_ULPS * EPS32 * R)


def check_mesh(me):
    """Fermé, variété, orienté de façon cohérente, sans face dégénérée (aire nulle, ou épaisseur sous la précision
    float32 des sommets : points alignés), volume > 0 (float64)."""
    bm = bmesh.new()
    bm.from_mesh(me)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    noncontig = sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    wire = sum(1 for e in bm.edges if e.is_wire)
    bm.free()
    V, T = mesh_arrays(me)
    A, H = face_metrics(me, V)
    h_tol = thin_tolerance(V)
    zero = int(np.count_nonzero(A < ZERO_AREA))
    thin = int(np.count_nonzero((A >= ZERO_AREA) & (H < h_tol)))
    if len(T):
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        vol = float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0)
        tri_area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
        zero_tri = int(np.count_nonzero(tri_area < ZERO_AREA))
    else:
        vol, zero_tri = 0.0, 0
    # les triangles d'aire nulle de la triangulation interne d'un n-gone (points alignés) sont signalés seulement
    ok = (len(me.polygons) > 0 and nonman == 0 and noncontig == 0 and boundary == 0 and wire == 0
          and zero == 0 and thin == 0 and vol > 0)
    return {'non_manifold': nonman, 'non_contiguous': noncontig, 'boundary': boundary, 'wire': wire,
            'zero_area_faces': zero, 'thin_faces': thin, 'thin_tol_mm': h_tol, 'zero_area_tris': zero_tri,
            'min_face_area': float(A.min()) if len(A) else 0.0,
            'min_face_thickness': float(H.min()) if len(H) else 0.0, 'volume': vol,
            'verts': len(me.vertices), 'faces': len(me.polygons), 'ok': bool(ok)}


def evaluated_mesh_data(ob, dg, with_check=False):
    """(V local, T, rapport check_mesh ou None) du maillage évalué de l'objet (modificateurs compris)."""
    ob_e = ob.evaluated_get(dg)
    me = ob_e.to_mesh()
    try:
        V, T = mesh_arrays(me)
        rep = check_mesh(me) if with_check else None
    finally:
        ob_e.to_mesh_clear()
    return V, T, rep


# ---------------------------------------------------------------- repère monde, BVH, boîtes
def world_matrix(ob, dg):
    return np.array(ob.evaluated_get(dg).matrix_world, float)


def to_world(V, M):
    return V @ M[:3, :3].T + M[:3, 3]


def bvh(W, T):
    """BVHTree en repère monde depuis des sommets monde et des triangles (tableau ou liste déjà convertie)."""
    return BVHTree.FromPolygons(W.tolist(), T if isinstance(T, list) else T.tolist(), all_triangles=True)


def aabb(W):
    if len(W) == 0:
        return np.full(3, np.inf), np.full(3, -np.inf)
    return W.min(axis=0), W.max(axis=0)


def aabb_pairs(lo, hi, pad=1e-6):
    """Couples (i, j), i < j, dont les boîtes alignées (lo, hi : n×3) se coupent (marge `pad`)."""
    lo = np.asarray(lo) - pad
    hi = np.asarray(hi) + pad
    inter = np.ones((len(lo), len(lo)), bool)
    for k in range(3):
        inter &= (lo[:, None, k] <= hi[None, :, k]) & (hi[:, None, k] >= lo[None, :, k])
    i, j = np.nonzero(np.triu(inter, 1))
    return list(zip(i.tolist(), j.tolist()))


def aabb_inside(lo_a, hi_a, lo_b, hi_b):
    """Vrai si la boîte A est entièrement dans la boîte B."""
    return bool(np.all(lo_a >= lo_b) and np.all(hi_a <= hi_b))


def point_inside(tree, p, max_hits=256):
    """Parité de rayons (deux directions obliques) : vrai si le point est dans le solide fermé `tree`."""
    votes = []
    for d in RAY_DIRS:
        o = Vector(p)
        n = 0
        for _ in range(max_hits):
            loc, _nor, _idx, _dist = tree.ray_cast(o, d)
            if loc is None:
                break
            n += 1
            o = loc + d * 1e-6
        votes.append(n % 2 == 1)
    return all(votes)


def overlap_info(ta, tb, Wa, Ta):
    """(nombre de couples de triangles qui se coupent, point représentatif ou None)."""
    ov = ta.overlap(tb)
    if not ov:
        return 0, None
    pts = Wa[Ta[[i for i, _ in ov[:64]]]].reshape(-1, 3)
    return len(ov), [round(float(x), 4) for x in pts.mean(axis=0)]


def min_gap(Wa, tb, lo_b, hi_b, reach=2.0, cap=4000):
    """Distance minimale approchée (sommets de A → surface de B) pour les sommets de A proches de la boîte de B."""
    sel = np.all((Wa >= lo_b - reach) & (Wa <= hi_b + reach), axis=1)
    P = Wa[sel]
    if len(P) > cap:
        P = P[:: int(math.ceil(len(P) / cap))]
    best = math.inf
    for p in P:
        r = tb.find_nearest(Vector(p), reach)
        if r[0] is not None and r[3] < best:
            best = r[3]
    return best


# ---------------------------------------------------------------- angles
def wrap(a):
    """Angle ramené dans [−π, π)."""
    return (a + math.pi) % (2 * math.pi) - math.pi


def signed_rotation(R0, R1, axis):
    """Angle signé (radians) de la rotation R1·R0ᵀ autour de `axis` (vecteurs 3×3 orthonormés, repère monde)."""
    R = R1 @ R0.T
    c = max(-1.0, min(1.0, (np.trace(R) - 1.0) / 2.0))
    s_vec = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / 2.0
    return math.atan2(float(np.dot(s_vec, axis)), c)


def rot3(M):
    """Partie rotation (colonnes normalisées) d'une matrice 4×4."""
    R = np.array(M, float)[:3, :3]
    return R / np.linalg.norm(R, axis=0)
