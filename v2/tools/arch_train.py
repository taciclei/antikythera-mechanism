"""Trains roue par roue : modèle (arbres, plans, roues, engrènements), règles internes et placement.

Un train a des arbres A0…An (et un arbre de pignon fou « I » s'il y en a un, dans le plan du couple 1).
Le plan 0 est en haut. En mode « tour », le plan 0 porte le couple 1:1 qui reprend Y sur le tube de
l'axe ; les couples du train descendent ensuite, la roue finale (sur l'axe) est dans le plan le plus bas.
Ainsi l'arbre L de l'axe sort sous le tube Y, comme une minuterie d'horloge.
Règles internes : une roue ne touche aucun arbre sauf le sien et celui qu'elle mène ; deux roues d'un
même plan ne se touchent que si elles engrènent.
"""
import math
from fractions import Fraction

import arch_layout as L


def wr(m, z, kind="external"):
    m = float(m)
    return m * z / 2 + (3 * m if kind == "internal" else m)


def cdist(m, z1, z2, kind="external"):
    m = float(m)
    return m * (z2 - z1) / 2 if kind == "internal" else m * (z1 + z2) / 2


def model(stages, modules, idler=None, transfer=None, idler_stage=0):
    """Arbres, roues (arbre, plan, rayon) et engrènements (roue a, roue b, entraxe).
    transfer : None, ("direct", entraxe) ou ("fou", dents du pignon fou) pour la reprise 1:1 du tube Y."""
    n = len(stages)
    arb = [f"a{i}" for i in range(n + 1)] + (["I"] if idler else [])
    wheels, meshes = [], []
    off = 1 if transfer else 0
    tcd = None
    stud = {}
    if transfer and transfer[0] == "direct":
        tcd = transfer[1]
        r = tcd / 2 + 0.5
        wheels += [{"arbor": n, "plane": 0, "r": r, "z": int(2 * tcd)},
                   {"arbor": 0, "plane": 0, "r": r, "z": int(2 * tcd)}]
        meshes.append((0, 1, tcd))
    elif transfer:
        zi = transfer[1]
        arb.append("T")
        t_idx = len(arb) - 1
        ci = 0.5 * (24 + zi) / 2
        wheels += [{"arbor": n, "plane": 0, "r": 6.5, "z": 24}, {"arbor": t_idx, "plane": 0, "r": zi / 4 + 0.5, "z": zi},
                   {"arbor": 0, "plane": 0, "r": 6.5, "z": 24}]
        meshes += [(0, 1, ci), (1, 2, ci)]
        stud = {t_idx: 0}  # pignon fou sur un tenon porté par le pont : son arbre ne descend pas sous le plan 0
    for k, (z1, z2, kind) in enumerate(stages):
        m = Fraction(modules[k])
        p = off + k
        wd = len(wheels)
        wheels.append({"arbor": k, "plane": p, "r": wr(m, z1), "z": z1})
        wheels.append({"arbor": k + 1, "plane": p, "r": wr(m, z2, kind), "z": z2})
        if idler and k == idler_stage:
            wi = len(wheels)
            wheels.append({"arbor": n + 1, "plane": p, "r": wr(m, idler), "z": idler})
            meshes.append((wd, wi, cdist(m, z1, idler)))
            meshes.append((wi, wd + 1, cdist(m, idler, z2)))
        else:
            meshes.append((wd, wd + 1, cdist(m, z1, z2, kind)))
    return {"arbors": arb, "wheels": wheels, "meshes": meshes, "planes": off + n, "n": n, "idler": bool(idler),
            "idler_stage": idler_stage if idler else None, "transfer": transfer, "transfer_cd": tcd, "stud": stud}


def internal_ok(M, pos, axis_idx=None):
    """Règles internes. pos : liste ou dict {indice d'arbre : (x, y)} ; les arbres absents sont ignorés."""
    P = pos if isinstance(pos, dict) else dict(enumerate(pos))
    W, mesh = M["wheels"], M["meshes"]
    partner = M.setdefault("_partner", {})
    if not partner:
        for a, b, _ in mesh:
            partner.setdefault(a, set()).add(b)
            partner.setdefault(b, set()).add(a)
    for i, w in enumerate(W):
        pa = P.get(w["arbor"])
        if pa is None:
            continue
        stud = M.get("stud", {})
        for b, pb in P.items():
            if b == w["arbor"] or (b in stud and w["plane"] > stud[b]):
                continue
            if any(W[j]["arbor"] == b and W[j]["plane"] == w["plane"] for j in partner.get(i, ())):
                continue
            sr = L.AXIS_R if (b == axis_idx and w["plane"] == 0) else L.SHAFT_R
            if math.dist(pa, pb) < w["r"] + sr + L.CLEAR:
                return False
        for j in range(i + 1, len(W)):
            v = W[j]
            if v["plane"] != w["plane"] or v["arbor"] == w["arbor"] or j in partner.get(i, ()):
                continue
            pv = P.get(v["arbor"])
            if pv is not None and math.dist(pa, pv) < w["r"] + v["r"] + L.CLEAR:
                return False
    return True


def _circ(c1, r1, c2, r2):
    d = math.dist(c1, c2)
    if d == 0 or d > r1 + r2 or d < abs(r1 - r2):
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, r1 * r1 - a * a))
    mx, my = c1[0] + a * (c2[0] - c1[0]) / d, c1[1] + a * (c2[1] - c1[1]) / d
    return [(mx + s * h * (c2[1] - c1[1]) / d, my - s * h * (c2[0] - c1[0]) / d) for s in (1, -1)]


def _cd(M, a, b):
    """Entraxe imposé entre deux arbres (par un engrènement), sinon None."""
    for wa, wb, c in M["meshes"]:
        A, B = M["wheels"][wa]["arbor"], M["wheels"][wb]["arbor"]
        if {A, B} == {a, b}:
            return c
    return None


def chain_nodes(M):
    """Chaîne des arbres depuis la sortie An jusqu'à l'entrée A0 (pignon fou intercalé), avec les entraxes."""
    n = M["n"]
    nodes, edges = [n], []
    for k in range(n - 1, -1, -1):
        if M["idler"] and M["idler_stage"] == k:
            nodes.append(n + 1)
            edges.append(_cd(M, n + 1, k + 1))
            nodes.append(k)
            edges.append(_cd(M, k, n + 1))
        else:
            nodes.append(k)
            edges.append(_cd(M, k, k + 1))
    return nodes, edges


def candidates(M, mode, fixed_out=None, fixed_in=None, step_abs=10, step_rel=30):
    """Énumère les positions (élaguées par les règles internes). Modes : tower (fermeture par la reprise
    1:1 sur l'axe), rod (A0 libre), bridge (A0 et An fixes), in (A0 fixe, un seul couple)."""
    absA = [math.radians(a) for a in range(0, 360, step_abs)]
    relA = [math.radians(a) for a in range(-180 + step_rel, 180, step_rel)]
    if mode == "in":
        if M["idler"]:
            I = M["n"] + 1
            ca, cb = _cd(M, 0, I), _cd(M, I, 1)
            for a in absA:
                ip = (fixed_in[0] + ca * math.cos(a), fixed_in[1] + ca * math.sin(a))
                for db in relA:
                    p1 = (ip[0] + cb * math.cos(a + db), ip[1] + cb * math.sin(a + db))
                    q = {0: fixed_in, I: ip, 1: p1}
                    if internal_ok(M, q):
                        yield q
            return
        c = _cd(M, 0, 1)
        for a in absA:
            yield {0: fixed_in, 1: (fixed_in[0] + c * math.cos(a), fixed_in[1] + c * math.sin(a))}
        return
    if mode == "bridge":
        c01 = _cd(M, 0, 1)
        for a in absA:
            a1 = (fixed_in[0] + c01 * math.cos(a), fixed_in[1] + c01 * math.sin(a))
            for a2 in _circ(a1, _cd(M, 1, 2), fixed_out, _cd(M, 2, 3)):
                yield {0: fixed_in, 1: a1, 2: a2, 3: fixed_out}
        return
    nodes, edges = chain_nodes(M)
    axis_idx = M["n"] if mode == "tower" else None
    direct = mode == "tower" and M["transfer"][0] == "direct"

    def dfs(pos, i, ang_prev):
        node, prev = nodes[i], nodes[i - 1]
        c = edges[i - 1]
        if direct and i == len(nodes) - 1:
            for p in _circ(pos[prev], c, fixed_out, M["transfer_cd"]):
                q = dict(pos)
                q[node] = p
                if internal_ok(M, q, axis_idx):
                    yield q
            return
        for da in (absA if ang_prev is None else relA):
            ang = da if ang_prev is None else ang_prev + da
            p = (pos[prev][0] + c * math.cos(ang), pos[prev][1] + c * math.sin(ang))
            q = dict(pos)
            q[node] = p
            if not internal_ok(M, q, axis_idx):
                continue
            if i == len(nodes) - 1:
                if mode == "tower":
                    yield from _close_fou(M, q, fixed_out)
                else:
                    yield q
            else:
                yield from dfs(q, i + 1, ang)

    yield from dfs({nodes[0]: fixed_out}, 1, None)


def _close_fou(M, pos, axis):
    """Reprise par pignon fou : le fou est à l'intersection des cercles (axe, ci) et (A0, ci)."""
    t_idx = M["arbors"].index("T")
    ci = _cd(M, M["n"], t_idx)
    a0 = pos[0]
    if math.dist(a0, axis) > 2 * ci - 0.5:
        return
    for tp in _circ(axis, ci, a0, ci):
        q = dict(pos)
        q[t_idx] = tp
        if internal_ok(M, q, M["n"]):
            yield q


def as_list(M, pos):
    return [pos[i] for i in range(len(M["arbors"]))]
