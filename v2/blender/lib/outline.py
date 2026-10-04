# copié de build/am/outline.py (v1) — aides nécessaires seulement (n_sides … translate, window, gear_windows),
# docstrings traduites en français, code inchangé ; gear_loops (liée à la spec v1) est réécrite dans parts.py.
"""Contours 2D : cercles, arcs, rectangles arrondis, fenêtres d'allègement.
Convention : loops[0] = bord extérieur (trigonométrique), loops[1:] = trous (horaires). Unités : mm."""
import math

import numpy as np

from .involute import dedupe

TWO_PI = 2.0 * math.pi


def n_sides(R, g, nmin=64):
    """Nombre de côtés d'un cercle polygonal face à un jeu radial g (règle de la spec v1)."""
    if g <= 0 or R <= 0:
        return nmin
    return max(nmin, int(math.ceil(math.pi / math.acos(R / (R + g)))) + 8)


def signed_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def ccw(p):
    return p if signed_area(p) > 0 else p[::-1].copy()


def cw(p):
    return p if signed_area(p) < 0 else p[::-1].copy()


def circle(cx, cy, r, n=64, start=0.0):
    a = start + np.arange(n) * TWO_PI / n
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)


def arc(cx, cy, r, a0, a1, step=math.radians(3.0), include_end=True):
    n = max(1, int(math.ceil(abs(a1 - a0) / step)))
    a = np.linspace(a0, a1, n + 1)
    if not include_end:
        a = a[:-1]
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)


def rect(x0, y0, x1, y1):
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float)


def rounded_rect(x0, y0, x1, y1, r, step=math.radians(10.0)):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -math.pi / 2), (x1 - r, y1 - r, 0.0),
                       (x0 + r, y1 - r, math.pi / 2), (x0 + r, y0 + r, math.pi)):
        pts.append(arc(cx, cy, r, a0, a0 + math.pi / 2, step))
    return dedupe(np.vstack(pts))


def stadium(x0, x1, hw, y=0.0, step=math.radians(10.0)):
    """Lumière selon x, de x0 à x1 (bouts ronds compris), demi-largeur hw. Sens trigonométrique."""
    c0, c1 = x0 + hw, x1 - hw
    a = arc(c1, y, hw, -math.pi / 2, math.pi / 2, step)
    b = arc(c0, y, hw, math.pi / 2, 3 * math.pi / 2, step)
    return dedupe(np.vstack([a, b]))


def rotate(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    return p @ np.array([[c, s], [-s, c]])


def translate(p, dx, dy):
    return p + np.array([dx, dy])


def window(Rh, Rr, a0, a1, h0, h1, step=math.radians(2.0)):
    """Fenêtre entre le bras à l'angle a0 (demi-largeur h0) et le bras à a1 > a0 (demi-largeur h1),
    radialement entre Rh et Rr. Renvoie une boucle horaire (trou) ou None si elle dégénère."""
    u0 = np.array([math.cos(a0), math.sin(a0)])
    n0 = np.array([-math.sin(a0), math.cos(a0)])
    u1 = np.array([math.cos(a1), math.sin(a1)])
    n1 = np.array([-math.sin(a1), math.cos(a1)])
    if h0 >= Rr or h1 >= Rr:
        return None
    o0, o1 = a0 + math.asin(h0 / Rr), a1 - math.asin(h1 / Rr)
    if o1 - o0 < 1e-3:
        return None
    outer = arc(0, 0, Rr, o0, o1, step)
    inner_ok = Rh > max(h0, h1) and (a1 - math.asin(h1 / Rh)) - (a0 + math.asin(h0 / Rh)) > 1e-3
    if inner_ok:
        inner = arc(0, 0, Rh, a1 - math.asin(h1 / Rh), a0 + math.asin(h0 / Rh), step)
        pts = np.vstack([outer, inner])
    else:
        # les deux bords décalés se coupent avant Rh : p = t0*u0 + h0*n0 = t1*u1 - h1*n1
        A = np.stack([u0, -u1], axis=1)
        t = np.linalg.solve(A, -h1 * n1 - h0 * n0)
        X = t[0] * u0 + h0 * n0
        if np.linalg.norm(X) >= Rr - 0.3:
            return None
        pts = np.vstack([outer, X[None, :]])
    return cw(dedupe(pts))


def gear_windows(r_hub, r_rim, n, widths, offset=0.0):
    """n fenêtres entre des bras aux angles offset + 2*pi*i/n (widths[i] = largeur totale du bras)."""
    out = []
    for i in range(n):
        a0 = offset + TWO_PI * i / n
        a1 = offset + TWO_PI * (i + 1) / n
        w = window(r_hub, r_rim, a0, a1, widths[i] / 2, widths[(i + 1) % n] / 2)
        if w is not None:
            out.append(w)
    return out
