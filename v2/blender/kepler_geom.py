"""Anticythère 2.0 — géométrie des pièces des tours de Kepler (phase K2) : formes 2D locales → maillages Blender.

Schéma des formes (v2/tools/kepler/CONTRACT.md § 5), en mm, dans le REPÈRE LOCAL de la pièce (origine au pivot,
θ = 0) : {"type": "polygon", "outer": [[x, y], ...], "holes": [[[x, y], ...], ...]} ou {"type": "circle",
"c": [x, y], "r": r} (un trou peut aussi être donné comme {"c": [x, y], "r": r}).
- Chaque forme devient un îlot (bord trigonométrique, trous horaires, points quasi confondus ou alignés retirés par
  parts.clean_loop), triangulé par CDT (lib/meshing.triangulate, trous compris) et extrudé entre −h/2 et +h/2
  (Builder.prism : variété fermée, normales sortantes). L'objet est posé au milieu de [z0, z1].
- Îlots qui se recouvrent (bras + moyeu donnés séparément, par exemple) : union booléenne EXACTE de l'objet avec
  lui-même (modificateur Boolean, `use_self`), appliquée ; sinon les coques imbriquées fausseraient la parité des
  rayons de check.py.
- Pièce « gear » : vraie roue à développante de 30° de parts.gear_loops (dent 0 sur +x local, jeu 0,03 mm, fenêtres
  d'allègement au-delà de r 12) ; ses formes (cercle de tête) ne servent qu'au rayon d'alésage (trou centré).
"""
import math

import bpy
import numpy as np

import parts as P
from lib.meshing import Builder, MeshError
from lib.outline import ccw, circle, cw

CIRCLE_STEP = 0.4        # corde des cercles (mm)


def circle_loop(cx, cy, r):
    """Cercle polygonal inscrit (corde ~0,4 mm, 32 à 256 côtés)."""
    return circle(float(cx), float(cy), float(r), P.n_circle(float(r), CIRCLE_STEP, 32, 256))


def _loop(pts):
    """Boucle 2D nettoyée (n × 2) depuis [[x, y], ...] ou {"c": [x, y], "r": r}."""
    if isinstance(pts, dict):
        c = pts.get('c', [0.0, 0.0])
        return circle_loop(c[0], c[1], pts['r'])
    lp = P.clean_loop(np.asarray(pts, float)[:, :2])
    if len(lp) < 3:
        raise MeshError('boucle dégénérée (%d points)' % len(lp))
    return lp


def shape_island(sh):
    """Îlot [bord trigonométrique, trous horaires...] d'une forme du schéma."""
    t = sh.get('type')
    if t == 'circle':
        c = sh.get('c', [0.0, 0.0])
        return [ccw(circle_loop(c[0], c[1], sh['r']))]
    if t == 'polygon':
        return [ccw(_loop(sh['outer']))] + [cw(_loop(h)) for h in sh.get('holes', []) or []]
    raise MeshError('forme inconnue %r' % (t,))


def _crossing(A, B):
    """Vrai si une arête du polygone fermé A coupe proprement une arête de B (vectorisé)."""
    a0, a1 = A[:, None, :], np.roll(A, -1, 0)[:, None, :]
    b0, b1 = B[None, :, :], np.roll(B, -1, 0)[None, :, :]

    def orient(p, q, r):
        return (q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0])
    d1, d2 = orient(a0, a1, b0), orient(a0, a1, b1)
    d3, d4 = orient(b0, b1, a0), orient(b0, b1, a1)
    return bool(np.any((d1 * d2 < 0) & (d3 * d4 < 0)))


def islands_overlap(islands):
    """Vrai si deux îlots (bords extérieurs) se recouvrent : boîtes qui se coupent, puis sommet de l'un dans l'autre
    ou arêtes sécantes. Prudent : un îlot logé dans le trou d'un autre compte aussi (l'union le traite bien)."""
    outs = [isl[0] for isl in islands]
    for i in range(len(outs)):
        for k in range(i + 1, len(outs)):
            A, B = outs[i], outs[k]
            if np.any(A.max(0) < B.min(0)) or np.any(B.max(0) < A.min(0)):
                continue
            if P._inside(A[0], B) or P._inside(B[0], A) or _crossing(A, B):
                return True
    return False


def union_self(me, name):
    """Union booléenne exacte d'un maillage avec lui-même (îlots qui se recouvrent) ; renvoie le nouveau maillage."""
    tmp = bpy.data.objects.new('_K_union_tmp', me)
    bpy.context.scene.collection.objects.link(tmp)
    empty = bpy.data.collections.new('_K_union_vide')
    try:
        mod = tmp.modifiers.new('union', 'BOOLEAN')
        mod.operation, mod.solver, mod.operand_type = 'UNION', 'EXACT', 'COLLECTION'
        mod.collection = empty
        mod.use_self = True
        dg = bpy.context.evaluated_depsgraph_get()
        out = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    finally:
        bpy.data.objects.remove(tmp)
        bpy.data.collections.remove(empty)
    bpy.data.meshes.remove(me)
    out.name = name
    return out


def shapes_mesh(name, shapes, h):
    """Maillage d'une pièce à formes : îlots extrudés sur l'épaisseur h (centrée en z = 0). Renvoie (maillage, info)."""
    if not shapes:
        raise MeshError('pièce sans forme')
    islands = [shape_island(s) for s in shapes]
    B = Builder()
    area = B.prism(islands, -h / 2.0, h / 2.0)
    me = B.to_mesh(name)
    merged = len(islands) > 1 and islands_overlap(islands)
    if merged:
        me = union_self(me, name)
    return me, {'islands': len(islands), 'union': merged, 'area': float(area)}


def centered_hole_radius(shapes, tol=0.05):
    """Rayon moyen du plus grand trou rond centré sur l'origine locale parmi les formes (None sinon)."""
    best = None
    for sh in shapes or []:
        holes = (sh.get('holes') or []) if sh.get('type') == 'polygon' else []
        for h in holes:
            if isinstance(h, dict):
                c, r = h.get('c', [0.0, 0.0]), float(h['r'])
                ok = math.hypot(c[0], c[1]) < tol
            else:
                p = np.asarray(h, float)[:, :2]
                d = np.hypot(p[:, 0], p[:, 1])
                ok, r = float(np.hypot(*p.mean(0))) < tol and float(d.max() - d.min()) < tol, float(d.mean())
            if ok and (best is None or r > best):
                best = r
    return best


def gear_mesh(name, gear, h, bore):
    """Roue à développante (parts.gear_loops) d'épaisseur h, dent 0 sur +x local. Renvoie (maillage, info)."""
    teeth, m = int(gear['teeth']), float(gear['m'])
    mk = gear.get('mesh') or ('internal' if gear.get('internal') else 'external')
    loops, info = P.gear_loops(teeth, m, bore, mk, gear.get('r_out'), float(gear.get('j', P.J_BACKLASH)))
    B = Builder()
    B.prism([loops], -h / 2.0, h / 2.0)
    return B.to_mesh(name), dict(info, teeth=teeth, m=m, mesh=mk)
