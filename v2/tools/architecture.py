#!/usr/bin/env python3
"""Anticythère 2.0 — architecture (version 2) : assemble, place roue par roue, vérifie, écrit les sorties.

Usage : python3 v2/tools/architecture.py [--check]
Entrées : spec/trains.json, research/calc/*_results.json, tools/arch_layout.py, arch_routes.py, arch_faces.py.
Sorties : spec/architecture.json ; study/architecture.md (arch_doc.py). Code de sortie ≠ 0 si un contrôle échoue.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import arch_geom as G  # noqa: E402
import arch_layout as L  # noqa: E402
import arch_place as P  # noqa: E402
import arch_routes as R  # noqa: E402
import arch_train as T  # noqa: E402

TUBE_ORDER = ["node", "neptune", "uranus", "saturn", "jupiter", "mars", "venus", "mercury", "moon"]  # arrière → avant


def load():
    with open(os.path.join(V2, "spec", "trains.json")) as f:
        trains = json.load(f)
    with open(os.path.join(V2, "research", "calc", "modules_results.json")) as f:
        mods = json.load(f)["modules"]
    return trains, {s["id"]: s for s in trains["shafts"]}, mods


def laplace_block(S):
    rads = {k: G.chain_shapes(*G.train_arbors(S[k]))[0][0] for k in ("ganymede", "nu", "callisto")}
    r = round(max(rads.values()) + 4.0, 1)
    x0, y0, mg = L.PLATE["x"][0], L.PLATE["y"][0], L.PLATE["margin"]
    return (x0 + mg + r + 0.5, y0 + mg + r + 0.5), r, rads


def block_items(mods, S):
    lc, lr, _ = laplace_block(S)
    L.BLOCKS["laplace"]["c"], L.BLOCKS["laplace"]["r"] = lc, lr
    items = []
    for bid, b in L.BLOCKS.items():
        r = b["r"] if b["r"] is not None else mods[b["tower"]]["module_radius_mm"] + L.MODULE_FRAME
        z = (L.sub(b["floor"], b["subs"][0])[0], L.sub(b["floor"], b["subs"][-1])[1])
        it = P.cyl(bid, b["c"], r, z, block=True)
        for k in ("r_in", "links"):
            if b.get(k):
                it[k] = b[k]
        if b.get("tower"):
            it["group"] = f"tour_{b['tower']}"
        items.append(it)
    return items


def axis_items():
    items = []
    e4 = L.FLOORS["E4"]["z"][0]
    for p, c in L.TOWERS.items():
        # arbre L (Ø 4) dans les plans des trains ; le tube Y (Ø 8) au-dessus (voir place_train pour sa partie basse)
        items.append(P.cyl(f"axe_{p}", c, L.SHAFT_R, (e4, L.arbor_span("E4")[1]), group=f"tour_{p}"))
        items.append(P.cyl(f"axe_{p}#haut", c, L.AXIS_R, (L.arbor_span("E4")[1], L.sub("E2", "mod")[0]),
                           group=f"tour_{p}"))
    items.append(P.cyl("axe_soleil", L.CENTRE, L.ARBOR_R, (L.mid("E3", "uak"), L.Z_FRONT),
                       links=["terre_maitre", "pile", "axe_Y"]))
    items.append(P.cyl("axe_Y", L.CENTRE, L.ARBOR_R, (L.arbor_span("E5")[0], L.mid("E3", "uak")),
                       links=["y_arbre", "Y5", "Y4a", "Y4b", "terre_maitre", "axe_soleil"]))
    items.append(P.cyl("axe_J", L.J_DAY, L.ARBOR_R, (L.arbor_span("E5")[0], L.arbor_span("E4")[1]),
                       links=["jour", "J5"]))
    for hid, h in L.HUBS.items():
        items.append(P.cyl(hid, h["c"], L.HUB_R, L.sub(h["floor"], h["layer"]),
                           links=["axe_Y" if h["src"] == "Y" else "axe_J"], wheel="renvoi"))
    return items


def _hub_point(route, other):
    h = L.HUBS[route["hub"]]
    d = math.dist(h["c"], other)
    return (h["c"][0] + (other[0] - h["c"][0]) * L.HUB_PIN_AT / d, h["c"][1] + (other[1] - h["c"][1]) * L.HUB_PIN_AT / d)


def _touch(a, b):
    """Deux pièces d'un même renvoi se touchent à une jonction (même point, ou bout de tringle)."""
    pa = [a["c"]] if a["kind"] == "cyl" else [a["p"], a["q"]]
    pb = [b["c"]] if b["kind"] == "cyl" else [b["p"], b["q"]]
    return any(math.dist(x, y) < 0.6 for x in pa for y in pb)


def route_items(route, car=None, takeoff=None, zr=None):
    """Pièces d'un renvoi. Liens : blocs déclarés aux extrémités, puis pièce à pièce aux jonctions (revue N9)."""
    rid, items = route["id"], []
    base = list(route.get("links", []))
    if route.get("chain"):  # prise par roue, pignon fou et roue (λ_T sur l'UAK maîtresse)
        ch = route["chain"]
        uz = L.sub(ch["floor"], ch["sub"])
        pz = (uz[1] - L.PLANE_T, uz[1])
        a, b = ch["from"], ch["to"]
        d = math.dist(a, b)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        r_i = d / 2 - (ch["r_end"] - 0.5) + 0.5
        base_c = base + ([route["interface"]] if route.get("interface") else [])
        items += [P.cyl(f"{rid}#c0", a, ch["r_end"], pz, links=base_c + [f"{rid}#c1"], wheel="renvoi"),
                  P.cyl(f"{rid}#c1", mid, r_i, pz, links=[f"{rid}#c0", f"{rid}#c2", f"{rid}#c1a"] + base_c[-1:],
                        wheel="renvoi", interface=route.get("interface")),
                  P.cyl(f"{rid}#c1a", mid, L.SHAFT_R, uz, links=[f"{rid}#c1"]),
                  P.cyl(f"{rid}#c2", b, ch["r_end"], pz, links=[f"{rid}#c1"], wheel="renvoi")]
    for k, seg in enumerate(route["segs"]):
        if seg[0] == "z":
            _, c, a, b = seg
            z0, z1 = sorted((L.mid(*a), L.mid(*b)))
            it = P.cyl(f"{rid}#z{k}", c, L.ARBOR_R, (z0, z1), links=list(base))
            if route.get("interface"):
                it["interface"] = route["interface"]
            items.append(it)
            continue
        _, p, q, (fid, lay) = seg[:4]
        z = zr or L.sub(fid, lay)
        if p == "prise":
            p, q = takeoff["start"], (takeoff["start"][0], R.TOP)
            items += [P.cyl(f"{rid}#prise_axe", takeoff["axis"], takeoff["r"], z, wheel="renvoi",
                            links=base + [f"{rid}#prise"]),
                      P.cyl(f"{rid}#prise", takeoff["start"], takeoff["r"], z, wheel="renvoi",
                            links=[f"{rid}#prise_axe"])]
        if q == "carrousel":
            q = car
        if p == "hub":
            p = _hub_point(route, q)
        if q == "hub":
            q = _hub_point(route, p)
        items.append(P.rod(f"{rid}#r{k}", p, q, z, links=base + ([route["hub"]] if route.get("hub") else [])))
        for e, pt in (("p", p), ("q", q)):
            if route.get("exit") == e:
                continue
            at_hub = bool(route.get("hub")) and math.dist(pt, L.HUBS[route["hub"]]["c"]) < L.HUB_PIN_AT + 1
            r_end = L.MITRE_R
            if route.get("hub") and not at_hub and route.get("exit") != "p":
                r_end = L.HUB_R  # au bout d'une tringle de moyeu (1:4), une couronne 4:1
            items.append(P.cyl(f"{rid}#m{k}{e}", pt, r_end, z, wheel="renvoi",
                               links=base + ([route["hub"]] if at_hub else [])))
    for x in items:  # jonctions internes au renvoi
        for y in items:
            if x is not y and _touch(x, y) and y["id"] not in x["links"]:
                x["links"].append(y["id"])
    return items


def takeoff_for(route):
    t = route.get("tower")
    cd, side = L.TAKEOFF[t]
    axis, aid = (L.CENTRE, "axe_soleil") if t == "earth" else (L.TOWERS[t], f"axe_{t}")
    route["links"] = list(dict.fromkeys(list(route.get("links", [])) + [aid]))
    return {"axis": axis, "start": (axis[0] + side * cd, axis[1]), "r": cd / 2 + 0.5}


def carousel(sources, placed, routes=()):
    """Neuf arbres intermédiaires à 40° les uns des autres ; ordre et décalage choisis sans collision."""
    names = sorted(sources, key=lambda n: math.atan2(sources[n][1], sources[n][0]))
    pz = L.sub("E1", "pile")
    lev_h = (pz[1] - pz[0]) / len(TUBE_ORDER)
    z_t1 = L.sub("E1", "T1")
    obst = [it for it in placed if G.z_overlap(it["z"], (z_t1[0], pz[1]))]
    best = None
    for rot in range(len(names)):
        for off in range(0, 40, 2):
            pos, its = {}, []
            for k, nm in enumerate(names[rot:] + names[:rot]):
                a = math.radians(off + 40 * k)
                pos[nm] = (L.CAROUSEL_R * math.cos(a), L.CAROUSEL_R * math.sin(a))
            length = sum(math.dist(sources[n], pos[n]) for n in names)
            if best and length >= best[0]:
                continue
            for nm, c in pos.items():
                lv = TUBE_ORDER.index(nm)
                zl = (pz[0] + lv * lev_h, pz[0] + (lv + 1) * lev_h)
                own = [f"car_{nm}", f"car_{nm}#roue", f"car_{nm}#mitre", f"tube_{nm}"]
                its += [P.cyl(f"car_{nm}", c, L.ARBOR_R, (L.mid("E1", "T1"), zl[1]), links=own),
                        P.cyl(f"car_{nm}#mitre", c, L.MITRE_R, z_t1, links=own, wheel="renvoi"),
                        P.cyl(f"car_{nm}#roue", c, L.CAROUSEL_WHEEL_R, zl, links=own, wheel="renvoi"),
                        P.cyl(f"tube_{nm}", L.CENTRE, L.CAROUSEL_WHEEL_R, zl, links=own + ["pile", "axe_soleil"],
                              wheel="renvoi")]
            rods = []
            for r in routes:
                rr = dict(r, links=list(r.get("links", [])) + [f"car_{r['car']}", f"car_{r['car']}#mitre"])
                rods += [it for it in route_items(rr, car=pos[r["car"]]) if "#z" not in it["id"]]
            if G.collisions(its + rods, L.CLEAR) or G.hits_any(its + rods, obst, L.CLEAR):
                continue
            best = (length, pos, its)
    return best


def place_precession(items, report):
    """Couple 10:131 sous la platine P4 (revues N3, N7). L'arbre L de Neptune descend dans la couche T2 de l'étage 5 ;
    en bas de T2, un coq de 2 mm porte les deux arbres ; au-dessus, le plan du couple (3 mm) ; plus haut, la tringle
    qui finit sur l'arbre prec_avant. Cet arbre monte au pignon de l'anneau tropique et descend dans le bloc du
    temps, qui y prend la précession par son couple 15:179."""
    ne = L.TOWERS["neptune"]
    t2 = L.sub("E5", "T2")
    plane = (t2[0] + 2.0, t2[0] + 5.0)
    rod_z = (t2[0] + 5.0, t2[1])
    items.append(P.cyl("axe_neptune#bas", ne, L.SHAFT_R, (t2[0], L.FLOORS["E4"]["z"][0]), group="tour_neptune"))

    end = (0.0, -65.6)  # l'arbre prec_avant, qui monte à l'anneau tropique et sert le bloc du temps

    def rod_to_time(pos):
        a1 = pos[1]
        its = route_items({"id": "prec_bas", "links": ["prec#a1", "temps", "prec_avant#z0"],
                           "segs": [("rod", a1, end, ("E5", "T2"))]}, zr=rod_z)
        return its

    for pm, zi in [(m, z) for m in ("1/2", "2/5") for z in (None, 20, 30, 40)]:
        pr = P.place_fixed("prec", [[10, 131, "external"]], [pm], "in", items, "E5", "T2", ne,
                           ext={0: "axe_neptune"}, idler=zi, spans={1: (t2[0], t2[1]), 2: (t2[0], t2[1])},
                           extra_fn=rod_to_time, subz=plane)
        if pr:
            break
    else:
        report["failed"].append("precession_ring")
        return
    items += pr[1]
    report["placed"]["precession_ring"] = {
        "floor": "E5", "sub": "T2 (coq + plan + tringle)", "idler": zi, "module": pm,
        "arbors": [[round(v, 2) for v in p] for p in pr[2]],
        "note": f"couple 10:131 (m {pm}) sous la platine P4, sur l'arbre L de Neptune prolongé, porté par un coq ; "
                f"pignon fou : {zi or 'aucun'} ; 15:179 à l'avant et dans le bloc du temps"}


def place_lune_entries(items, report):
    """Revue N2 : L, Ω et ϖ ramenés sur l'axe M par des couples 40 → pignon fou → 40 (même sens, rapport 1:1)."""
    M = L.M_MOON
    blk = next(it for it in items if it["id"] == "lune")
    out = []
    for key, sh in (("L", "moon_L"), ("Ω", "moon_node"), ("ϖ", "moon_perigee")):
        p = report["placed"].get(sh)
        if not p:
            report["failed"].append(f"entrée {key}")
            continue
        n = len(p["ordre_couples"]) if p.get("ordre_couples") else 2
        src, sid = tuple(p["arbors"][n]), f"{sh}#a{n}"
        arb = next(it for it in items if it["id"] == sid)
        lo, hi = max(arb["z"][0], blk["z"][0]), min(arb["z"][1], blk["z"][1])
        done = None
        z_top = hi
        while z_top - L.PLANE_T >= lo - 1e-9 and not done:
            pz = (z_top - L.PLANE_T, z_top)
            for zi in (24, 32, 40, 48, 56, 64, 72, 80, 96):
                ci = 0.25 * (40 + zi)
                for tp in T._circ(src, ci, M, ci):
                    tid = f"lune_entree_{sh}"
                    its = [P.cyl(f"{tid}#w1", src, 10.5, pz, links=[sid, f"{tid}#fou", "lune"], wheel="renvoi", interface="lune"),
                           P.cyl(f"{tid}#fou", tp, zi / 4 + 0.5, pz, links=[f"{tid}#w1", f"{tid}#w2", f"{tid}#tenon", "lune"],
                                 wheel="renvoi", interface="lune"),
                           P.cyl(f"{tid}#tenon", tp, L.SHAFT_R, (pz[0], min(pz[1] + 3.0, blk["z"][1])),
                                 links=[f"{tid}#fou", "lune"]),
                           P.cyl(f"{tid}#w2", M, 10.5, pz, links=[f"{tid}#fou", "lune"], wheel="renvoi", interface="lune")]
                    if not G.hits_any(its, [x for x in items if x["id"] != "lune"], L.CLEAR):
                        done = (its, zi, pz)
                        break
                if done:
                    break
            z_top -= L.PLANE_T
        if done:
            items += done[0]
            out.append({"entree": key, "fou": done[1], "plan_z": [round(v, 1) for v in done[2]]})
        else:
            report["failed"].append(f"entrée {key}")
    report["lune_entrees"] = out


def assemble(S, mods):
    report = {"placed": {}, "failed": []}
    items = block_items(mods, S) + axis_items()
    geo = [r for r in R.ROUTES if r.get("kind") == "geo"]
    for r in R.ROUTES:
        if r.get("kind") == "geo":
            items += [it for it in route_items(r, car=(0.0, 0.0)) if "#z" in it["id"]]
            continue
        items += route_items(r, takeoff=takeoff_for(r) if r["segs"][0][1] == "prise" else None)
    for link in R.DIRECT_LINKS:
        b = L.BLOCKS[link["to_block"]]
        res = P.direct_link(link, b["c"], b["r"], link["to_block"], items)
        if res is None:
            report["failed"].append(link["id"])
        else:
            items += res[1]
    for fid, sid in L.Y_TRAIN_OPTIONS:
        br = P.place_fixed("ytrain", L.Y_TRAIN_STAGES, ["1/2"] * 3, "bridge", items, fid, sid, L.J_DAY, L.CENTRE,
                           ext={0: "axe_J", 3: "axe_Y"})
        if br:
            items += br[1]
            report["placed"]["Y"] = {"floor": fid, "sub": sid, "arbors": [[round(v, 2) for v in p] for p in br[2]]}
            break
    else:
        report["failed"].append("Y")
    for spec in sorted(L.PLACED_TRAINS, key=lambda t: L.PLACE_ORDER.index(t["shaft"])):
        res = P.place_train(spec, S[spec["shaft"]], items)
        if res is None:
            report["failed"].append(spec["shaft"])
            continue
        score, sid, its, pos, tcd, M = res
        items += its
        if spec["shaft"] == "neptune_L":
            place_precession(items, report)
        report["placed"][spec["shaft"]] = {"floor": spec["floor"], "sub": sid, "hub": spec["hub"], "mode": spec["mode"],
                                           "reprise": list(tcd) if tcd else None, "idler_stage": M["idler_stage"],
                                           "ordre_couples": [S[spec["shaft"]]["stages"][i][:2] for i in M["perm"]],
                                           "arbors": [[round(v, 2) for v in p] for p in pos]}
    place_lune_entries(items, report)
    car = carousel({r["car"]: r["segs"][0][1] for r in geo}, items, geo)
    if car is None:
        report["failed"].append("carrousel")
    else:
        items += car[2]
        report["carousel_deg"] = {n: round(math.degrees(math.atan2(p[1], p[0])), 1) for n, p in car[1].items()}
        for r in geo:
            r["links"] = list(r.get("links", [])) + [f"car_{r['car']}", f"car_{r['car']}#mitre"]
            items += [it for it in route_items(r, car=car[1][r["car"]]) if "#z" not in it["id"]]
    return items, report


EXITS = {r["id"] for r in R.ROUTES if r.get("exit")}


def main():
    import arch_build
    out = arch_build.build(write="--check" not in sys.argv)
    c = out["verifications"]
    print(f"objets : {c['objets']}  trains placés : {c['trains_places']}  échecs : {c['echecs_placement']}")
    print(f"collisions : {len(c['collisions'])}  hors platine : {c['hors_platine']}")
    for x in c["collisions"][:40]:
        print("   ", x)
    print(f"interfaces déclarées : {len(c['interfaces'])}  roues : {out['roues']['total']}  masse : {out['masse']['total_kg']} kg  "
          f"caisse : {out['masse']['box_mm']} mm")
    print("OK" if c["ok"] else "ÉCHEC")
    if "--check" not in sys.argv:
        import arch_doc
        arch_doc.write(out)
    return 0 if c["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
