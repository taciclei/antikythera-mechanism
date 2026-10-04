"""Anticythère 2.0 — module faces : briques des cadrans (faces gravées, aiguilles coaxiales, étiquettes).

Côté `side` : +1 face avant (les pièces s'empilent vers +Z), −1 face arrière (vers −Z). Hauteur locale h = z − z_face,
où z_face est la surface extérieure de la platine-cadran. Une face de cadran occupe |h| ∈ [0 ; 1] ; la gravure
dépasse de 0,06 mm ; les aiguilles occupent des étages de 0,8 mm au pas de 1,2 mm à partir de |h| = 1,6.
"""
import math

import numpy as np

from faces_common import tag
from faces_mesh import MeshBuf, make_text, prism, radial_bar, ring, text_M, P

FACE_T = 1.0
ENG = 0.06
START, THICK, PITCH = 1.6, 0.8, 1.2


def span(a, b, side):
    """Intervalle [a, b] (hauteurs comptées vers l'extérieur) converti en h croissant."""
    return (a, b) if side > 0 else (-b, -a)


def level(k, side):
    a = START + k * PITCH
    return span(a, a + THICK, side)


def radii(n, r_arbor=1.4, wall=0.6, gap=0.06):
    """Rayons (intérieur, extérieur) des tubes coaxiaux : l'étage le plus haut est l'arbre plein central."""
    out = [None] * n
    out[n - 1] = (0.0, r_arbor)
    for k in range(n - 2, -1, -1):
        ri = out[k + 1][1] + gap
        out[k] = (ri, ri + wall)
    return out


def hole_for(n, rad=None):
    """Rayon du trou central d'une face traversée par n tubes coaxiaux (rayons `rad` imposés, sinon radii(n))."""
    return (rad if rad is not None else radii(n))[0][1] + 0.3


def arch_r(arch, item_id, default):
    """Rayon d'une pièce `items[]` d'architecture.json (arbre qu'une aiguille prolonge), sinon `default`."""
    return next((float(i["r"]) for i in arch.get("items", []) if i.get("id") == item_id and "r" in i), default)


def pile_radii(arch, n):
    """Rayons de la pile centrale du grand cadran d'après architecture.json : l'arbre du Soleil prolonge
    `axe_soleil` (r 2,0) et le tube le plus extérieur atteint `blocs.pile.r` (9,2 : Ø 18,4 mm, 1,6 mm par tube)."""
    r_sun = arch_r(arch, "axe_soleil", 2.0)
    r_out = float(arch.get("blocs", {}).get("pile", {}).get("r") or r_sun + 0.8 * (n - 1))
    step = (r_out - r_sun) / (n - 1)
    gap = min(0.1, step / 4.0)
    return radii(n, r_arbor=r_sun, wall=step - gap, gap=gap)


def face_h(side):
    return span(0.0, FACE_T, side)


def eng_h(side):
    return span(FACE_T, FACE_T + ENG, side)


def text_h(side):
    return side * (FACE_T + 0.03)


def ticks(buf, phis, r0, r1, w, side, key="engrave"):
    h0, h1 = eng_h(side)
    for phi in phis:
        buf.add(radial_bar(phi, r0, r1, w, w, h0, h1), key)


def circle_line(buf, r, w, side, key="engrave", a0=None, a1=None):
    h0, h1 = eng_h(side)
    buf.add(ring(r - w / 2, r + w / 2, h0, h1, a0=a0, a1=a1), key)


def numbers_into(buf, items, side, key="engrave", upright=False):
    """items : (texte, taille, r, φ) gravés en un seul maillage (échelles denses)."""
    from faces_mesh import texts_into
    texts_into(buf, [(s, size, text_M(r, phi, text_h(side), back=side < 0, upright=upright))
                     for s, size, r, phi in items], key)


def label(name, body, size, coll, mats, parent, r, phi, side, upright=False, key="engrave", source=""):
    """Étiquette FONT enfant de `parent`, sur la face (repère local du parent)."""
    M = text_M(r, phi, text_h(side), back=side < 0, upright=upright)
    return make_text(name, body, size, coll, mats[key], M, parent=parent, source=source)


def label_at(name, body, size, coll, mats, parent, xy, side, key="engrave", source=""):
    """Étiquette droite (non tournée) au point xy du repère local du parent."""
    M = text_M(0.0, 0.0, text_h(side), back=side < 0, upright=True)
    M[0, 3], M[1, 3] = xy
    return make_text(name, body, size, coll, mats[key], M, parent=parent, source=source)


def fixed(name, buf, coll, mats, centre, z_face, kind="dial", source="", links=()):
    ob = buf.to_object(name, coll, mats, loc=(centre[0], centre[1], z_face))
    tag(ob, kind, source=source, links=links)
    return ob


def hand(name, coll, mats, centre, z_face, side, k, n, arms, key, mat="steel", scale=-1.0, extras=(),
         source="", links=(), collar=1.2, phase=0.0, lev=None, base=0.0, rad=None, **extra):
    """Aiguille k d'une pile de n aiguilles coaxiales : tube depuis la platine (ou depuis |h| = base pour un
    pivot posé sur une face), collet, bras. `lev` : étage en hauteur (par défaut k). `rad` : rayons (intérieur,
    extérieur) imposés de la pile (p. ex. ceux d'architecture.json), sinon radii(n).
    arms : (φ, r0, r1, w0, w1) ; r0 = None part du collet. extras : (géométrie, clé de matériau) locales.
    Pose de repos : l'aiguille montre φ = 0 (en haut) ; rotation = scale · valeur autour de +Z."""
    buf = MeshBuf()
    lev = k if lev is None else lev
    ri, ro = (rad if rad is not None else radii(n))[k]
    h0, h1 = level(lev, side)
    t0, t1 = span(base, START + lev * PITCH, side)
    buf.add(ring(ri, ro, t0, t1, n=32), mat)
    rc = ro + collar
    buf.add(ring(ri, rc, h0, h1, n=32), mat)
    for phi, r0, r1, w0, w1 in arms:  # un bras dépasse toujours le collet (jamais vers les tubes intérieurs)
        buf.add(radial_bar(phi, rc - 0.3 if r0 is None else r0, max(r1, rc + 1.0), w0, w1, h0, h1), mat)
    for geom, key_m in extras:
        buf.add(geom, key_m)
    ob = buf.to_object(name, coll, mats, loc=(centre[0], centre[1], z_face))
    tag(ob, "hand", key=key, scale=scale, axis=(0.0, 0.0, 1.0), phase=phase, source=source,
        links=list(links), **extra)
    return ob


def bead(r, phi, side, k, rad=2.6, grow=0.1):
    """Perle plate (disque) sur l'aiguille de l'étage k, au rayon r."""
    h0, h1 = level(k, side)
    x, y = P(r, phi)
    v, f = ring(0.0, rad, h0 - grow, h1 + grow, n=24)
    return v + np.array([x, y, 0.0]), f


def arrow_head(phi, r0, r1, w, side, k):
    """Pointe triangulaire à plat sur l'étage k."""
    h0, h1 = level(k, side)
    a, b = P(r0, phi), P(r1, phi)
    d = np.subtract(b, a)
    d /= np.linalg.norm(d)
    nrm = np.array([-d[1], d[0]]) * w / 2
    return prism([np.add(a, -nrm), b, np.add(a, nrm)], h0, h1)


def deg(x):
    return math.radians(x)
