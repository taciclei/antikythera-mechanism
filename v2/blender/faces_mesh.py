"""Anticythère 2.0 — module faces : constructeurs de maillages simples (solides fermés) et textes gravés.

Angle de cadran φ : 0 en haut (+Y), positif dans le sens trigonométrique autour de +Z ; point P(r, φ) = (−r sin φ, r cos φ).
Chaque générateur rend (sommets N×3, faces) dans un repère local où la hauteur est l'axe z local.
"""
import math

import bmesh
import bpy
import numpy as np

from faces_common import tag

TAU = 2.0 * math.pi


def P(r, phi):
    return (-r * math.sin(phi), r * math.cos(phi))


def _nseg(r):
    return int(min(360, max(24, 2.0 * r)))


def ring(r0, r1, h0, h1, n=None, a0=None, a1=None):
    """Couronne (r0 > 0), disque plein (r0 = 0) ou secteur de couronne [a0, a1] (angles de cadran)."""
    n = n or _nseg(r1)
    sector = a0 is not None
    if sector:
        ang = np.linspace(a0, a1, n + 1)
    else:
        ang = np.linspace(0.0, TAU, n, endpoint=False)
    m = len(ang)
    s, c = -np.sin(ang), np.cos(ang)
    if r0 <= 0 and not sector:
        v = np.concatenate([np.stack([r1 * s, r1 * c, np.full(m, h0)], 1), np.stack([r1 * s, r1 * c, np.full(m, h1)], 1)])
        f = [tuple(range(m - 1, -1, -1)), tuple(range(m, 2 * m))]
        f += [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
        return v, f
    r0 = max(r0, 1e-3)
    rings = [(r1, h0), (r1, h1), (r0, h1), (r0, h0)]  # ob, ot, it, ib
    v = np.concatenate([np.stack([r * s, r * c, np.full(m, h)], 1) for r, h in rings])
    f = []
    last = m - 1 if sector else m
    for k in range(4):
        a, b = k * m, ((k + 1) % 4) * m
        for i in range(last):
            j = (i + 1) % m
            f.append((a + i, a + j, b + j, b + i))
    if sector:
        f.append((0, m, 2 * m, 3 * m))
        e = m - 1
        f.append((e + 3 * m, e + 2 * m, e + m, e))
    return v, f


def prism(poly, h0, h1):
    """Extrusion d'un polygone plan (liste de points 2D, sens trigonométrique) entre h0 et h1."""
    m = len(poly)
    p = np.asarray(poly, float)
    v = np.concatenate([np.c_[p, np.full(m, h0)], np.c_[p, np.full(m, h1)]])
    f = [tuple(range(m - 1, -1, -1)), tuple(range(m, 2 * m))]
    f += [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
    return v, f


def bar(p, q, w0, w1, h0, h1):
    """Barre plane effilée de p (largeur w0) à q (largeur w1)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = q - p
    d /= np.linalg.norm(d)
    nrm = np.array([-d[1], d[0]])
    return prism([p - nrm * w0 / 2, q - nrm * w1 / 2, q + nrm * w1 / 2, p + nrm * w0 / 2], h0, h1)


def radial_bar(phi, r0, r1, w0, w1, h0, h1):
    return bar(P(r0, phi), P(r1, phi), w0, w1, h0, h1)


def box(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def sphere(r, nseg=24, nring=12):
    """Sphère UV, pôles sur z ; les méridiens 0 et nseg/2 sont dans le plan y = 0."""
    v = [(0.0, 0.0, -r)]
    for i in range(1, nring):
        t = math.pi * i / nring - math.pi / 2
        for j in range(nseg):
            a = TAU * j / nseg
            v.append((r * math.cos(t) * math.cos(a), r * math.cos(t) * math.sin(a), r * math.sin(t)))
    v.append((0.0, 0.0, r))
    top = len(v) - 1
    f = [(0, 1 + (j + 1) % nseg, 1 + j) for j in range(nseg)]
    for i in range(nring - 2):
        a, b = 1 + i * nseg, 1 + (i + 1) * nseg
        f += [(a + j, a + (j + 1) % nseg, b + (j + 1) % nseg, b + j) for j in range(nseg)]
    a = 1 + (nring - 2) * nseg
    f += [(a + j, a + (j + 1) % nseg, top) for j in range(nseg)]
    return np.array(v), f


def basis_z(d):
    """Matrice 3×3 dont la colonne z est la direction d."""
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    t = np.array([1.0, 0.0, 0.0]) if abs(d[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = np.cross(t, d)
    x /= np.linalg.norm(x)
    return np.stack([x, np.cross(d, x), d], 1)


def cyl_between(p, q, r, n=16):
    p, q = np.asarray(p, float), np.asarray(q, float)
    v, f = ring(0.0, r, 0.0, float(np.linalg.norm(q - p)), n=n)
    return v @ basis_z(q - p).T + p, f


def band(inner, outer, h0, h1):
    """Bande fermée entre deux boucles de même longueur (points 2D, sens trigonométrique)."""
    a, b = np.asarray(inner, float), np.asarray(outer, float)
    m = len(a)
    v = np.concatenate([np.c_[b, np.full(m, h0)], np.c_[b, np.full(m, h1)],
                        np.c_[a, np.full(m, h1)], np.c_[a, np.full(m, h0)]])
    f = []
    for k in range(4):
        s, t = k * m, ((k + 1) % 4) * m
        f += [(s + i, s + (i + 1) % m, t + (i + 1) % m, t + i) for i in range(m)]
    return v, f


def mat4(rot3=None, loc=(0.0, 0.0, 0.0)):
    M = np.eye(4)
    if rot3 is not None:
        M[:3, :3] = rot3
    M[:3, 3] = loc
    return M


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


class MeshBuf:
    """Accumulateur de solides fermés avec un matériau par solide."""

    def __init__(self):
        self.v, self.f, self.mi, self.keys, self.n = [], [], [], [], 0

    def add(self, geom, key, M=None):
        """Ajoute un solide ; `key` est une clé de matériau, ou une liste de clés (une par face)."""
        v, f = geom
        v = np.asarray(v, float)
        if M is not None:
            M = np.asarray(M, float)
            v = v @ M[:3, :3].T + (M[:3, 3] if M.shape == (4, 4) else 0.0)
        keys = key if isinstance(key, (list, tuple)) else [key] * len(f)
        for k in keys:
            if k not in self.keys:
                self.keys.append(k)
        self.v.append(v)
        self.f += [tuple(i + self.n for i in face) for face in f]
        self.mi += [self.keys.index(k) for k in keys]
        self.n += len(v)
        return self

    def to_object(self, name, coll, mats, loc=(0.0, 0.0, 0.0), parent=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(np.concatenate(self.v).tolist(), [], self.f)
        me.polygons.foreach_set("material_index", self.mi)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.validate()
        for k in self.keys:
            me.materials.append(mats[k])
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        ob.location = loc
        if parent is not None:
            ob.parent = parent
            ob.matrix_parent_inverse.identity()
        return ob


# ---------------------------------------------------------------- textes
def text_M(r, phi, h, back=False, upright=False):
    """Matrice d'un texte tangent au cercle r (haut du texte vers l'extérieur), lisible de face ou de dos."""
    x, y = P(r, phi)
    R = (np.eye(3) if upright else rz(phi)) @ (ry(math.pi) if back else np.eye(3))
    return mat4(R, (x, y, h))


def make_text(name, body, size, coll, mat, M, parent=None, extrude=0.03, align="CENTER", source=""):
    """Objet texte Blender (FONT) gravé, placé par la matrice locale M (repère du parent)."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.extrude = body, size, extrude
    cu.align_x, cu.align_y = align, "CENTER"
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse.identity()
    from mathutils import Matrix
    ob.matrix_basis = Matrix([list(row) for row in np.asarray(M)])
    tag(ob, "text", source=source, links=[parent.name] if parent is not None else [])
    return ob


def texts_into(buf, specs, key, extrude=0.03):
    """Grave une série de textes (corps, taille, M) dans le maillage `buf` (pour les échelles denses)."""
    tmp = []
    for i, (body, size, M) in enumerate(specs):
        cu = bpy.data.curves.new(f"_tmp_txt{i}", "FONT")
        cu.body, cu.size, cu.extrude = body, size, extrude
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        ob = bpy.data.objects.new(cu.name, cu)
        bpy.context.scene.collection.objects.link(ob)
        tmp.append((ob, M))
    dg = bpy.context.evaluated_depsgraph_get()
    for ob, M in tmp:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices):
            bm = bmesh.new()  # le maillage d'un texte a des sommets dupliqués aux arêtes : on les fusionne
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bm.verts.index_update()
            co = np.array([v.co[:] for v in bm.verts])
            faces = [tuple(v.index for v in fc.verts) for fc in bm.faces]
            bm.free()
            buf.add((co, faces), key, M)
        ev.to_mesh_clear()
    for ob, _ in tmp:
        cu = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)
    return buf
