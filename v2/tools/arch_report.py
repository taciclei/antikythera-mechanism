"""Bilans de l'architecture (version 2) : couverture, faces, couvercle, interfaces, roues, masse, jeu, sens."""
import math
from fractions import Fraction

import arch_faces as F
import arch_geom as G
import arch_layout as L
import arch_routes as R

RHO_BRASS = 8.47e-3   # g/mm³ (laiton CuZn39Pb3)
RHO_ALU = 2.70e-3     # g/mm³ (6061)
RHO_OAK = 0.70e-3     # g/mm³
JN = 0.03             # jeu normal entre dents, mm (version de précision)


def coverage(trains, report):
    ids = [s["id"] for s in trains["shafts"]]
    where = {}
    for bid, b in L.BLOCKS.items():
        for sh in b.get("contenu", []):
            where.setdefault(sh, []).append(f"bloc {bid}")
    for sh in report["placed"]:
        where.setdefault(sh, []).append("train placé roue par roue")
    for r in R.ROUTES:
        if r.get("shaft"):
            where.setdefault(r["shaft"], []).append(f"renvoi {r['id']}")
    for sh, loc in F.OPTIONS_PLACE.items():
        where.setdefault(sh, []).append(loc)
    missing = [i for i in ids if i not in where]
    wheel_level = [i for i in ids if any("train placé" in w for w in where.get(i, []))]
    return {"n_shafts": len(ids), "assigned": len(ids) - len(missing), "missing": missing,
            "placed_wheel_level": len(wheel_level), "where": {i: where.get(i, []) for i in ids}}


def faces_check():
    out = {"front": [], "back": [], "ok": True}
    (x0, x1), (y0, y1), mg = L.PLATE["x"], L.PLATE["y"], L.PLATE["margin"]
    for side, dials in (("front", F.FRONT), ("back", F.BACK)):
        names = list(dials)
        for n in names:
            (x, y), rr = dials[n]["c"], dials[n]["R"]
            inside = x - rr >= x0 + mg and x + rr <= x1 - mg and y - rr >= y0 + mg and y + rr <= y1 - mg
            out[side].append({"cadran": n, "inside": inside})
            out["ok"] &= inside
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = dials[names[i]], dials[names[j]]
                gap = math.dist(a["c"], b["c"]) - a["R"] - b["R"]
                if gap < 2:
                    out[side].append({"chevauchement": [names[i], names[j]], "gap_mm": round(gap, 1)})
                    out["ok"] = False
    return out


def lid_check(items):
    exits = {r["id"] for r in R.ROUTES if r.get("exit") == "q"}
    tops = sorted((it["q"][0], it["id"].split("#")[0]) for it in items
                  if it["kind"] == "rod" and it["id"].split("#")[0] in exits)
    gaps = [b[0] - a[0] for a, b in zip(tops, tops[1:])] or [0.0]
    need = 2 * L.MITRE_R + L.CLEAR
    z_lo, z_hi = L.BACK_DOOR_Z[0], L.FRONT_COVER_Z[1]
    half = (z_hi - z_lo) / 2
    rmax = max(F.ORRERY["rayons"].values()) + F.ORRERY["tellurion"]["globe_r"]
    return {"emergences_x": [(round(x, 1), rid) for x, rid in tops], "min_gap_mm": round(min(gaps), 1),
            "need_mm": round(need, 1), "ok_spacing": min(gaps) >= need, "orrery_centre_z": round((z_lo + z_hi) / 2, 1),
            "half_depth_mm": round(half, 1), "r_max_mm": rmax, "ok_fit": rmax + 5 <= half}


def interfaces(items):
    """Pièces déclarées à l'interface d'un bloc : profondeur dont elles entrent dans l'enveloppe du bloc."""
    blocks = {it["id"]: it for it in items if it.get("block")}
    out = []
    for it in items:
        targets = []
        if it.get("interface") in blocks:
            targets.append(it["interface"])
        if it.get("block") and L.BLOCKS.get(it["id"], {}).get("interface"):
            targets += [b for b in it.get("links", []) if b in blocks]
        for bid in targets:
            b = blocks[bid]
            depth = it["r"] + b["r"] - math.dist(it["c"], b["c"])
            if depth > 0 and G.z_overlap(it["z"], b["z"]):
                out.append({"piece": it["id"], "bloc": bid, "entre_de_mm": round(min(depth, 2 * it["r"]), 1)})
    return out


def wheel_count(trains, report):
    """Roues : trains.json (sans son estimation de renvois) + renvois de l'architecture + roues internes."""
    inv = trains["inventory"]
    base = inv["total_estimate"] - inv["transfer_wheels_estimate"]
    rows = [("trains, différentiels et pas à pas de trains.json", base),
            (f"couronnes des {len(L.HUBS)} moyeux (96 dents)", len(L.HUBS))]
    bus = sum(1 for p in report["placed"].values() if p.get("hub"))
    rows.append((f"tringles de bus vers {bus} trains (pignon 24, pignon 24, couronne 96)", 3 * bus))
    tr = [p["reprise"] for p in report["placed"].values() if p.get("reprise")]
    rows.append((f"reprises 1:1 du tube Y dans les {len(tr)} tours (couple, ou couple et pignon fou)",
                 sum(2 if t[0] == "direct" else 3 for t in tr)))
    for r in R.ROUTES:
        rows.append((f"renvoi {r['id']}", r.get("roues", 0) + r.get("interne", 0)))
    rows.append(("renvoi prec_bas (2 couples coniques)", 4))
    ent = report.get("lune_entrees", [])
    rows.append((f"entrées du bloc Lune : {len(ent)} couples 40 → fou → 40 (L, Ω, ϖ)", 3 * len(ent)))
    rows += [x for x in R.INTERNAL_WHEELS if x[1]]
    return {"rows": rows, "total": sum(n for _, n in rows)}


def _disc(r, t=2.0):
    return math.pi * r * r * t * (0.55 if r > 15 else 1.0) * RHO_BRASS


def mass(trains, wheels_total):
    g_trains = 0.0
    for s in trains["shafts"]:
        if s["subsystem"] == "options":
            continue
        for k, (z1, z2, kind) in enumerate(s.get("stages", [])):
            m = float(Fraction(s["modules_mm"][k]))
            g_trains += _disc(m * z1 / 2 + m) + _disc(m * z2 / 2 + m)
        rz = s.get("realisation") or {}
        for (z1, z2), mm in zip(rz.get("post_pairs", []), rz.get("post_modules_mm", ["1/2"] * 9)):
            m = float(Fraction(mm))
            g_trains += _disc(m * z1 / 2 + m)
            if s["id"] == "cal_sum" and z2 >= 150:  # anneau des dates : couronne de 200 dents, largeur 12 mm
                ro = m * z2 / 2 + 6 * m + 12
                g_trains += math.pi * (ro ** 2 - (m * z2 / 2 - m) ** 2) * 2.5 * RHO_BRASS
            else:
                g_trains += _disc(m * z2 / 2 + m)
    inv = trains["inventory"]
    g_diff = inv["diff_wheels"] * _disc(10.5)
    n_transfer = wheels_total - (inv["total_estimate"] - inv["transfer_wheels_estimate"])
    n_crowns = len(L.HUBS) + 11 + sum(1 for r in R.ROUTES if r.get("hub") and r.get("exit") != "p")
    g_transfer = (n_transfer - n_crowns) * _disc(9.0) + n_crowns * _disc(20.0)
    w, h = L.PLATE["x"][1] - L.PLATE["x"][0], L.PLATE["y"][1] - L.PLATE["y"][0]
    plate = w * h
    g_inner_brass = 4 * plate * L.PLATE_T * 0.5 * RHO_BRASS
    g_inner_alu = 4 * plate * L.PLATE_T * 0.5 * RHO_ALU
    g_dials = 2 * plate * L.DIAL_T * 0.85 * RHO_BRASS
    depth = L.FRONT_COVER_Z[1] - L.BACK_DOOR_Z[0]
    W, H = w + 2 * 4 + 2 * L.WALL, h + 2 * 4 + 2 * L.WALL
    g_box = (2 * W * depth + 2 * H * depth + W * H) * L.WALL * RHO_OAK
    g_glass = W * H * 2.0 * 2.5e-3
    parts = {"roues des trains (trains.json, sans les options)": g_trains, "roues des différentiels": g_diff,
             "roues de renvoi et roues internes (architecture)": g_transfer,
             "platines intérieures (laiton, ajourées 50 %)": g_inner_brass,
             "platines-cadrans avant et arrière (laiton 3 mm)": g_dials, "caisse en chêne 6 mm et porte arrière": g_box,
             "verre avant 2 mm": g_glass, "arbres, tubes, ponts, goupilles, ressorts": 1800.0,
             "UAK, modules, cascade, coulisses": 1500.0, "orrery et tellurion": 1200.0}
    total = sum(parts.values())
    return {"parts_g": {k: round(v) for k, v in parts.items()}, "total_kg": round(total / 1000, 1),
            "total_kg_alu_inner": round((total - g_inner_brass + g_inner_alu) / 1000, 1),
            "box_mm": [round(W), round(H), round(depth)]}


def backlash():
    """Jeu ramené à l'aiguille par les renvois en aval du suiveur (2 couples coniques m 0,4 et le couple 64:64)."""
    rp = L.BEVEL_M * 24 / 2
    return {"jn_mm": JN, "aval_suiveur_deg": round(math.degrees(JN / rp + JN / rp + JN / 16.0), 2),
            "sorties_non_monotones": ["7 aiguilles planétaires (stations de rétrogradation)", "équation du temps",
                                      "lunette de Jupiter", "coulisse d'éclipse γ", "aiguille d'ombre"],
            "remede": "coniques précontraintes par un ressort axial (le pignon est poussé dans la denture) et couples "
                      "64:64 à ciseaux (une demi-roue de plus par tube) ; jeu résiduel ≈ 0"}


def signs():
    """Tableau des sens : produit des engrènements fixes ; réglable si la chaîne contient un renvoi conique."""
    rows = []
    for r in R.ROUTES + [{"id": "prec_bas", "chaine": ["con", "con"]}]:
        ch = r.get("chaine", [])
        fixed = 1
        for e in ch:
            if e in ("ext", "fou"):
                fixed = -fixed
        adj = "con" in ch
        rows.append({"renvoi": r["id"], "chaine": " → ".join(ch), "sens_fixe": "+" if fixed > 0 else "−",
                     "reglage": "côté d'engrènement d'une conique" if adj else
                     ("aucun (même sens)" if fixed > 0 else "pignon fou à ajouter")})
    rows.append({"renvoi": "reprises de Y dans les tours", "chaine": "24 → fou → 24 (2 engrènements)", "sens_fixe": "+",
                 "reglage": "aucun : la reprise par pignon fou garde le sens, la planète et la copie de la Terre "
                            "tournent comme dans trains.json"})
    rows.append({"renvoi": "entrées du bloc Lune (L, Ω, ϖ)", "chaine": "40 → fou → 40 (2 engrènements)",
                 "sens_fixe": "+", "reglage": "aucun : le sens est gardé"})
    return rows


def block_budgets(items):
    """Revue N5 : la hauteur de chaque bloc suffit-elle à ses plans ?"""
    out = []
    for bid, (planes, note) in L.BLOCK_PLANES.items():
        b = next(it for it in items if it["id"] == bid)
        h = b["z"][1] - b["z"][0]
        out.append({"bloc": bid, "plans": planes, "besoin_mm": planes * L.PLANE_T, "hauteur_mm": round(h, 1),
                    "ok": planes * L.PLANE_T <= h + 1e-9, "detail": note})
    return out
