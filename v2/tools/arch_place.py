"""Placement roue par roue (version 2) : trains, tringles de moyeu, liaisons directes.

Chaque pièce est un objet : arbres (de la platine au pont), roues dans leur plan, pignons de moyeu,
couronnes d'arrivée, tringles. Les liens ne relient qu'une pièce à une pièce (engrènement, roue sur son
arbre) ; tout le reste est contrôlé par arch_geom.
"""
import itertools
import math

import arch_geom as G
import arch_layout as L
import arch_train as T


def cyl(iid, c, r, z, **kw):
    d = {"id": iid, "kind": "cyl", "c": (round(c[0], 3), round(c[1], 3)), "r": round(r, 3), "z": tuple(z)}
    d.update(kw)
    return d


def rod(iid, p, q, z, r=L.ROD_R, **kw):
    d = {"id": iid, "kind": "rod", "p": (round(p[0], 3), round(p[1], 3)), "q": (round(q[0], 3), round(q[1], 3)),
         "r": r, "z": tuple(z)}
    d.update(kw)
    return d


MIN_HUB_ROD = max(2 * L.HUB_R, 2 * L.HUB_PIN_AT + 2 * L.MITRE_R) + L.CLEAR


def plane_z(subz, plane):
    top = subz[1] - plane * L.PLANE_T
    return (top - L.PLANE_T, top)


def near(placed, c, R):
    out = []
    for it in placed:
        d = math.dist(it["c"], c) if it["kind"] == "cyl" else G.seg_point_dist(it["p"], it["q"], c)
        if d <= R + it["r"]:
            out.append(it)
    return out


def hub_rod(tid, hub_id, target, target_id, wheel=True):
    """Tringle de moyeu : pignon 24 sur la couronne 96 du moyeu → tringle → pignon 24 → couronne 96 à l'arrivée."""
    h = L.HUBS[hub_id]
    z = L.sub(h["floor"], h["layer"])
    hc = h["c"]
    d = math.dist(hc, target)
    u = ((target[0] - hc[0]) / d, (target[1] - hc[1]) / d)
    p0 = (hc[0] + u[0] * L.HUB_PIN_AT, hc[1] + u[1] * L.HUB_PIN_AT)
    p1 = (target[0] - u[0] * L.HUB_PIN_AT, target[1] - u[1] * L.HUB_PIN_AT)
    its = [cyl(f"{tid}#pin0", p0, L.MITRE_R, z, links=[hub_id, f"{tid}#rod"], wheel="renvoi"),
           rod(f"{tid}#rod", p0, p1, z, links=[f"{tid}#pin0", f"{tid}#pin1", hub_id, f"{tid}#cour"]),
           cyl(f"{tid}#pin1", p1, L.MITRE_R, z, links=[f"{tid}#rod", f"{tid}#cour"], wheel="renvoi")]
    if wheel:
        its.append(cyl(f"{tid}#cour", target, L.HUB_R, z, links=[f"{tid}#pin1", target_id], wheel="renvoi"))
    return its


def train_items(tid, M, pos, fid, subz, axis_idx=None, axis_id=None, spans=None, wheel_tag="train"):
    span = L.arbor_span(fid)
    spans = spans or {}
    items, wid = [], {i: f"{tid}#w{i}" for i in range(len(M["wheels"]))}
    partners = {}
    for a, b, _ in M["meshes"]:
        partners.setdefault(a, []).append(wid[b])
        partners.setdefault(b, []).append(wid[a])
    names = {}
    for k in range(len(M["arbors"])):
        names[k] = axis_id if (k == axis_idx and axis_id) else f"{tid}#{M['arbors'][k]}"
        if k == axis_idx and axis_id:
            continue
        own = [wid[i] for i, w in enumerate(M["wheels"]) if w["arbor"] == k]
        items.append(cyl(names[k], pos[k], L.SHAFT_R, spans.get(k, span), links=own))
    for i, w in enumerate(M["wheels"]):
        # une roue touche son arbre et engrène sa partenaire jusqu'au fond de dent (pignon taillé dans l'arbre)
        p_arb = [names[M["wheels"][wid_k]["arbor"]] for wid_k in
                 [int(x.split("#w")[1]) for x in partners.get(i, [])]]
        items.append(cyl(wid[i], pos[w["arbor"]], w["r"], plane_z(subz, w["plane"]),
                         links=[names[w["arbor"]]] + partners.get(i, []) + p_arb, wheel=wheel_tag, teeth=w["z"]))
    return items


def _blockers(its, obst):
    out = set()
    for a in its:
        for b in obst:
            if (G.z_overlap(a["z"], b["z"]) and not G.linked(a, b) and not G.in_hole(a, b, L.CLEAR)
                    and not G.in_hole(b, a, L.CLEAR) and G.xy_gap(a, b) < L.CLEAR):
                out.add(b["id"].split("#")[0])
    return out


def place_train(spec, sh, placed, stats=None, keep=1):
    """Meilleure configuration (ou les `keep` meilleures, triées) ; un point d'entrée peut être cherché sur un arc."""
    if spec.get("arc") and keep == 1:
        (cx, cy), rr, angs = spec["arc"]
        best = None
        for a in angs:
            sp = dict(spec, anchor=(cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))), arc=None)
            res = place_train(sp, sh, placed, stats)
            if res and (best is None or res[0] < best[0]):
                best = res
        return best
    sols = []
    fid, tid = spec["floor"], spec["shaft"]
    tower = spec["mode"] == "tower"
    best = None
    obst = near(placed, spec["anchor"], 200)
    modules = L.MODULE_OVERRIDE.get(tid, sh["modules_mm"])
    # reprise de Y par pignon fou (24 → fou → 24) : elle garde le sens (revue N1) ; le fou tourne sur un tenon de pont
    options = [("fou", z) for z in (16, 24, 32, 48, 64, 80, 96, 112)] if tower else [None]
    n0 = len(sh["stages"])
    perms, seen = [], set()
    for pm in itertools.permutations(range(n0)):
        key = tuple((tuple(sh["stages"][i]), str(modules[i])) for i in pm)
        if key not in seen:
            seen.add(key)
            perms.append(pm)
    configs = [(pm, ist, tcd) for pm in perms for ist in (range(n0) if sh.get("idler") else [0]) for tcd in options]
    for pm, ist, tcd in configs:
        M = T.model([sh["stages"][i] for i in pm], [modules[i] for i in pm], idler=sh.get("idler"), transfer=tcd,
                    idler_stage=ist)
        M["perm"] = pm
        n = M["n"]
        for sid in spec["subs"]:
            subz = L.sub(fid, sid)
            if M["planes"] * L.PLANE_T > subz[1] - subz[0] + 1e-9:
                continue
            static = []
            if tower:
                static = hub_rod(f"{tid}#bus", spec["hub"], spec["anchor"], f"axe_{spec['tower']}")
                if G.hits_any(static, obst, L.CLEAR):
                    if stats is not None:
                        stats["bus:" + ",".join(sorted(_blockers(static, obst)))] = stats.get("bus", 0) + 1
                    continue
            for pd in T.candidates(M, "tower" if tower else "rod", fixed_out=spec["anchor"]):
                pos = T.as_list(M, pd)
                if not T.internal_ok(M, pos, axis_idx=n if tower else None):
                    if stats is not None:
                        stats["_interne"] = stats.get("_interne", 0) + 1
                    continue
                spans, extra = {}, static
                for t_idx, top_plane in M.get("stud", {}).items():
                    spans[t_idx] = (plane_z(subz, top_plane)[0], L.arbor_span(fid)[1])
                if not tower:
                    h = L.HUBS[spec["hub"]]
                    if math.dist(pos[0], h["c"]) < MIN_HUB_ROD:
                        continue
                    spans[0] = (L.arbor_span(fid)[0], L.sub(h["floor"], h["layer"])[1])
                    if spec.get("out_back"):
                        spans[n] = (0.0, L.arbor_span(fid)[1])
                    if spec.get("out_down"):  # l'arbre de sortie descend dans le bloc de l'étage 5
                        spans[n] = (L.mid("E5", "meca"), L.arbor_span(fid)[1])
                    extra = hub_rod(f"{tid}#bus", spec["hub"], pos[0], f"{tid}#a0")
                score = math.dist(pos[0], L.HUBS[spec["hub"]]["c"]) if not tower else max(
                    math.dist(p, spec["anchor"]) for p in pos)
                if best and score >= best[0] and stats is None:
                    continue
                its = train_items(tid, M, pos, fid, subz, axis_idx=n if tower else None,
                                  axis_id=f"axe_{spec['tower']}" if tower else None, spans=spans)
                if spec.get("interface"):
                    out_ids = {f"{tid}#a{n}"} | {it["id"] for it in its if it["links"] and it["links"][0] == f"{tid}#a{n}"}
                    for it in its:
                        if it["id"] in out_ids:
                            it["links"] = list(it["links"]) + [spec["interface"]]
                            it["interface"] = spec["interface"]
                if tower:  # tube Y : du plan de reprise jusqu'aux ponts
                    its.append(cyl(f"axe_{spec['tower']}#tubeY", spec["anchor"], L.AXIS_R,
                                   (plane_z(subz, 0)[0], L.arbor_span(fid)[1]), group=f"tour_{spec['tower']}"))
                its += extra
                if any(not G.inside_plate(it, L.PLATE) for it in its) or G.hits_any(its, obst, L.CLEAR):
                    if stats is not None:
                        for b_ in _blockers(its, obst) or {"_hors"}:
                            stats[b_] = stats.get(b_, 0) + 1
                    continue
                best = (score, sid, its, pos, tcd, M)
                if keep > 1:
                    sols.append(best)
                    best = None
    if keep > 1:
        return sorted(sols, key=lambda x: x[0])[:keep]
    return best


def place_fixed(tid, stages, modules, mode, placed, fid, sid, fixed_in, fixed_out=None, ext=None, spans=None, idler=None,
                extra_fn=None, subz=None):
    """Train J → Y (bridge) ou couple de précession (in). ext : {indice d'arbre : objet existant}."""
    M = T.model(stages, modules, idler=idler)
    subz = subz or L.sub(fid, sid)
    obst = near(placed, fixed_in, 220)
    best = None
    for pd in T.candidates(M, mode, fixed_out=fixed_out, fixed_in=fixed_in):
        pos = T.as_list(M, pd)
        if not T.internal_ok(M, pos):
            continue
        its = train_items(tid, M, pos, fid, subz, spans=spans)
        rename = {f"{tid}#{M['arbors'][k]}": e for k, e in ext.items()}
        keep = []
        for it in its:
            if it["id"] in rename:
                continue  # l'arbre fixe existe déjà (axe_J, axe_Y, axe_neptune)
            it["links"] = [rename.get(x, x) for x in it["links"]]
            keep.append(it)
        if extra_fn:
            keep += extra_fn(pos)
        if any(not G.inside_plate(it, L.PLATE) for it in keep) or G.hits_any(keep, obst, L.CLEAR):
            continue
        score = sum(math.dist(pos[i], pos[i + 1]) for i in range(len(pos) - 1))
        if best is None or score < best[0]:
            best = (score, keep, pos, M)
    return best


def direct_link(link, block_c, block_r, block_id, placed):
    """Roue 64 sur la source → pignon fou 32 → roue 64 dans le bloc (même plan) : le sens est gardé."""
    z = L.sub(link["floor"], link["sub"])
    src, tid = link["from"], link["id"]
    best = None
    obst = near(placed, src, 130)
    for a in range(0, 360, 5):
        ip = (src[0] + 24 * math.cos(math.radians(a)), src[1] + 24 * math.sin(math.radians(a)))
        for b in range(0, 360, 5):
            bp = (ip[0] + 24 * math.cos(math.radians(b)), ip[1] + 24 * math.sin(math.radians(b)))
            if math.dist(bp, block_c) > block_r - 4 or math.dist(bp, src) < 33.5:
                continue
            its = [cyl(f"{tid}#src", src, 16.5, z, links=link["links"] + [f"{tid}#fou"], wheel="renvoi"),
                   cyl(f"{tid}#fou", ip, 8.5, z, links=[f"{tid}#src", f"{tid}#in", f"{tid}#arbre"], wheel="renvoi"),
                   cyl(f"{tid}#arbre", ip, L.SHAFT_R, L.arbor_span(link["floor"]), links=[f"{tid}#fou"]),
                   cyl(f"{tid}#in", bp, 16.5, z, links=[block_id, f"{tid}#fou"], wheel="renvoi", interface=block_id)]
            if G.hits_any(its, obst, L.CLEAR):
                continue
            sc = math.dist(bp, block_c)
            if best is None or sc < best[0]:
                best = (sc, its)
    return best
