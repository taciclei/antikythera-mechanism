"""Géométrie de l'architecture : chaînes d'engrenages, placement, collisions (cylindres et tringles).

Un « item » est soit un cylindre {"kind": "cyl", "c": (x, y), "r", "z": (z0, z1)}, soit une
tringle {"kind": "rod", "p": (x, y), "q": (x, y), "r", "z": (z0, z1)} couchée dans le plan xy.
Deux items se heurtent si leurs intervalles z se recouvrent ET si leurs empreintes xy se
recouvrent (avec le jeu CLEAR), sauf si la paire est déclarée liée (même groupe ou liens).
"""
import math
from fractions import Fraction
from itertools import product


def wheel_outer_r(m, z, kind="external"):
    """Rayon extérieur d'encombrement d'une roue (tête de dent ; jante pour une couronne intérieure)."""
    m = float(m)
    return m * z / 2 + (3 * m if kind == "internal" else m)


def stage_cd(m, z1, z2, kind):
    m = float(m)
    if kind == "internal":
        return m * (z2 - z1) / 2
    return m * (z1 + z2) / 2


def train_arbors(shaft):
    """Arbres d'un train : rayons d'encombrement et entraxes entre arbres consécutifs."""
    st = shaft["stages"]
    mods = [Fraction(x) for x in shaft["modules_mm"]]
    n = len(st)
    env = [0.0] * (n + 1)
    cds = []
    for k, (z1, z2, kind) in enumerate(st):
        env[k] = max(env[k], wheel_outer_r(mods[k], z1))
        env[k + 1] = max(env[k + 1], wheel_outer_r(mods[k], z2, kind))
        cds.append(stage_cd(mods[k], z1, z2, kind))
    return env, cds


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


SHAFT_R = 2.0  # demi-diamètre d'un arbre de train


def nonadjacent_min(e1, e2):
    """Distance minimale entre deux arbres non consécutifs d'un train composé.

    Leurs roues sont dans des plans différents (le couple k est dans le plan k) : il suffit que
    la plus grande roue ne touche pas l'arbre de l'autre."""
    return max(e1, e2) + SHAFT_R + 0.5


def chain_shapes(env, cds, step_deg=15):
    """Formes de chaîne (positions relatives, arbre 0 à l'origine, premier entraxe selon +x).

    Contrainte : deux arbres non consécutifs respectent nonadjacent_min. Retourne les formes
    triées par rayon d'encombrement croissant (les plus compactes d'abord)."""
    n = len(cds)
    turns = [math.radians(a) for a in range(-180 + step_deg, 180, step_deg)]
    shapes = []
    for combo in product(turns, repeat=max(0, n - 1)):
        pts = [(0.0, 0.0), (cds[0], 0.0)]
        ang = 0.0
        for k in range(1, n):
            ang += combo[k - 1]
            x, y = pts[-1]
            pts.append((x + cds[k] * math.cos(ang), y + cds[k] * math.sin(ang)))
        ok = all(_dist(pts[i], pts[j]) >= nonadjacent_min(env[i], env[j])
                 for i in range(len(pts)) for j in range(i + 2, len(pts)))
        if not ok:
            continue
        cx = (min(p[0] - e for p, e in zip(pts, env)) + max(p[0] + e for p, e in zip(pts, env))) / 2
        cy = (min(p[1] - e for p, e in zip(pts, env)) + max(p[1] + e for p, e in zip(pts, env))) / 2
        rad = max(_dist(p, (cx, cy)) + e for p, e in zip(pts, env))
        shapes.append((rad, pts))
    shapes.sort(key=lambda s: s[0])
    out, seen = [], set()
    for rad, pts in shapes:
        key = round(rad, 1)
        if key in seen:
            continue
        seen.add(key)
        out.append((rad, pts))
    return out


def transform(pts, origin_idx, origin_xy, rot):
    """Place une forme : l'arbre origin_idx en origin_xy, rotation rot (rad)."""
    ox, oy = pts[origin_idx]
    c, s = math.cos(rot), math.sin(rot)
    return [(origin_xy[0] + c * (x - ox) - s * (y - oy), origin_xy[1] + s * (x - ox) + c * (y - oy))
            for x, y in pts]


def seg_point_dist(p, q, c):
    px, py = p
    qx, qy = q
    dx, dy = qx - px, qy - py
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((c[0] - px) * dx + (c[1] - py) * dy) / L2))
    return math.hypot(px + t * dx - c[0], py + t * dy - c[1])


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def seg_seg_dist(p1, q1, p2, q2):
    o1, o2 = _orient(p1, q1, p2), _orient(p1, q1, q2)
    o3, o4 = _orient(p2, q2, p1), _orient(p2, q2, q1)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return 0.0
    return min(seg_point_dist(p1, q1, p2), seg_point_dist(p1, q1, q2),
               seg_point_dist(p2, q2, p1), seg_point_dist(p2, q2, q1))


def z_overlap(a, b):
    return min(a[1], b[1]) - max(a[0], b[0]) > 1e-9


def xy_gap(a, b):
    """Distance libre entre empreintes xy (négative = recouvrement)."""
    if a["kind"] == "cyl" and b["kind"] == "cyl":
        return _dist(a["c"], b["c"]) - a["r"] - b["r"]
    if a["kind"] == "rod" and b["kind"] == "rod":
        return seg_seg_dist(a["p"], a["q"], b["p"], b["q"]) - a["r"] - b["r"]
    cyl, rod = (a, b) if a["kind"] == "cyl" else (b, a)
    return seg_point_dist(rod["p"], rod["q"], cyl["c"]) - rod["r"] - cyl["r"]


def in_hole(a, b, clear):
    """b est entièrement dans le trou central d'un anneau a (clé "r_in")."""
    if a["kind"] != "cyl" or not a.get("r_in"):
        return False
    if b["kind"] == "cyl":
        return _dist(a["c"], b["c"]) + b["r"] <= a["r_in"] - clear
    return max(_dist(a["c"], b["p"]), _dist(a["c"], b["q"])) + b["r"] <= a["r_in"] - clear


def linked(a, b):
    if a.get("group") and a.get("group") == b.get("group"):
        return True
    # liens par identifiant exact ; seules les parties d'un même axe de tour (axe_x, axe_x#haut, axe_x#tubeY…)
    # répondent au nom de base (revue N9)
    na = {a["id"], a.get("group")} | ({a["id"].split("#")[0]} if a["id"].startswith("axe_") else set())
    nb = {b["id"], b.get("group")} | ({b["id"].split("#")[0]} if b["id"].startswith("axe_") else set())
    na.discard(None)
    nb.discard(None)
    return bool(nb & set(a.get("links", ()))) or bool(na & set(b.get("links", ())))


def collisions(items, clear):
    bad = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if not z_overlap(a["z"], b["z"]) or linked(a, b) or in_hole(a, b, clear) or in_hole(b, a, clear):
                continue
            g = xy_gap(a, b)
            if g < clear:
                bad.append((a["id"], b["id"], round(g, 2)))
    return bad


def hits_any(new_items, items, clear):
    for a in new_items:
        for b in items:
            if (z_overlap(a["z"], b["z"]) and not linked(a, b) and not in_hole(a, b, clear)
                    and not in_hole(b, a, clear) and xy_gap(a, b) < clear):
                return True
    return False


def inside_plate(item, plate):
    (x0, x1), (y0, y1), mg = plate["x"], plate["y"], plate["margin"]
    if item["kind"] == "cyl":
        (x, y), r = item["c"], item["r"]
        return x - r >= x0 + mg - 1e-9 and x + r <= x1 - mg + 1e-9 and y - r >= y0 + mg - 1e-9 and y + r <= y1 - mg + 1e-9
    return all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in (item["p"], item["q"]))
