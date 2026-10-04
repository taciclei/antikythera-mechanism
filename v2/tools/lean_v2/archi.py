"""Architecture.lean : identités de l'architecture placée (architecture.json), confrontées à trains.json.

- `place_*` : chaque train placé roue par roue (bus, reprise, couples dans l'ordre réel, pignons fous) a le même
  rapport que trains.json et le bon sens physique ;
- `reprise_*`, `bus_ratio`, `moon_input_*`, `precession_ratio`, `module_*` : identités de la CONTRACT.md § 6 ;
- `entraxe_*` : chaque couple engrené est à l'entraxe m (z₁ + z₂)/2, à TOL près.
"""
import re
from fractions import Fraction as F

from .common import LeanFile, fr, lit, plit, prod, dec, ident

TOL = F(3, 2000)   # 1,5 µm : centres arrondis au µm (3 décimales) → erreur sur la distance ≤ √2 · 10⁻³ mm
ALIAS = {"Y": "ytrain", "precession_ring": "prec"}   # nom du train dans `items` quand il diffère de trains.json


def tidy(q: F) -> str:
    """Décimale finie si possible (43.45), sinon fraction."""
    q = F(q)
    d = q.denominator
    while d % 2 == 0:
        d //= 2
    while d % 5 == 0:
        d //= 5
    if d != 1:
        return lit(q)
    s = f"{float(q):.10f}".rstrip("0").rstrip(".")
    assert F(s) == q
    return s


def centre(ctx, m, z1, z2, c1, c2, what):
    """Énoncé Lean (m(z₁+z₂)/2 − TOL)² < d² < (m(z₁+z₂)/2 + TOL)², contrôlé en Python."""
    a = F(m) * (z1 + z2) / 2
    d2 = sum((fr(dec(u)) - fr(dec(v))) ** 2 for u, v in zip(c1, c2))
    ctx.expect((a - TOL) ** 2 < d2 < (a + TOL) ** 2, f"entraxe {what} : {float(d2) ** 0.5} ≠ {float(a)}")
    D = " + ".join(f"(({dec(u)}) - ({dec(v)}) : ℚ) ^ 2" for u, v in zip(c1, c2))
    A = f"{plit(F(m))} * ({z1} + {z2}) / 2"
    return f"(({A}) - {lit(TOL)} : ℚ) ^ 2 < {D} ∧\n    {D} < (({A}) + {lit(TOL)} : ℚ) ^ 2", a


def stages_of(items, alias):
    """Couples placés d'un train, dans l'ordre des étages : [(menante, menée, fou ou None)], et la reprise."""
    st, rep = {}, {}
    for it in items:
        if it.get("train") != alias or not it.get("teeth"):
            continue
        if it["stage"] is None:
            rep.setdefault(it["role"], []).append(it)
        else:
            st.setdefault(it["stage"], {})[it["role"]] = it
    return [(s["menante"], s["menee"], s.get("fou")) for _, s in sorted(st.items())], rep


def bus_teeth(ctx):
    rows = " | ".join(r[0] for r in ctx.A["roues"]["rows"])
    hub = re.search(r"couronnes des (\d+) moyeux \((\d+) dents\)", rows)
    rod = re.search(r"tringles de bus vers (\d+) trains \(pignon (\d+), pignon (\d+), couronne (\d+)\)", rows)
    ctx.expect(int(hub.group(1)) == len(ctx.A["moyeux"]), "nombre de moyeux")
    ctx.expect(hub.group(2) == rod.group(4), "couronne des moyeux ≠ couronne d'arrivée")
    return int(hub.group(2)), int(rod.group(2)), int(rod.group(3)), int(rod.group(4)), int(rod.group(1))


def sens_entry(ctx, prefix):
    e = next(s for s in ctx.A["sens"] if s["renvoi"].startswith(prefix))
    a, b = (int(v) for v in re.match(r"(\d+) → fou → (\d+)", e["chaine"]).groups())
    return a, b, (1 if e["sens_fixe"] == "+" else -1)


def generate(ctx):
    A, items = ctx.A, ctx.A["items"]
    by_id = {it["id"]: it for it in items}
    L = LeanFile(ctx, ["Mathlib"], "Architecture placée : rapports, sens et entraxes", [
        "Identités de `architecture.json` confrontées à trains.json. Rapports physiques signés (Willis) :",
        "engrènement extérieur −a/b, intérieur +a/b, pignon fou par deux engrènements extérieurs. HYPOTHÈSE : le bus",
        "(couronne de moyeu → pignon → tringle → pignon → couronne) est compté de même sens ; comme pour les renvois",
        "coniques de `sens` (« côté d'engrènement d'une conique »), c'est un réglage de montage (face des couronnes,",
        "côté des pignons), et CONTRACT.md § 3 fait tourner les couronnes de moyeu au taux signé de la source. Les",
        "items du bus n'ont pas de dents dans architecture.json : 96 et 24 sont lus dans `roues.rows`. Entraxes :",
        f"centres des roues en mm, à {lit(TOL)} mm près (coordonnées arrondies au µm)."])
    h_cr, p0, p1, a_cr, n_rods = bus_teeth(ctx)
    bus = f"({h_cr} / {p0}) * ({p1} / {a_cr})"
    rods = [it["id"].split("#")[0] for it in items if it["id"].endswith("#bus#rod")]
    ctx.expect(len(rods) == n_rods, f"{len(rods)} tringles de bus au lieu de {n_rods}")
    for t in rods:
        hub = next(l for l in by_id[f"{t}#bus#pin0"]["links"] if l in A["moyeux"])
        ctx.expect(A["moyeux"][hub]["src"] == ctx.S[t]["src"], f"bus de {t} : moyeu {hub} ≠ source")
    L.theorem("bus_ratio", f"Bus des moyeux : la couronne de {h_cr} mène un pignon de {p0}, la tringle tourne "
              f"{F(h_cr, p0)} fois plus vite ; à l'arrivée un pignon de {p1} mène une couronne de {a_cr} : rapport 1. "
              f"{n_rods} tringles : {', '.join(rods)} (moyeu = source de trains.json).",
              f": ({h_cr} / {p0} : ℚ) = {F(h_cr, p0)} ∧ ({bus} : ℚ) = 1", ["norm_num"])
    r_a, r_b, r_sens = sens_entry(ctx, "reprises")
    for key, tp in A["trains_places"].items():
        alias = ALIAS.get(key, key)
        placed, rep = stages_of(items, alias)
        spec = ctx.S[key]
        if tp.get("ordre_couples"):
            ctx.expect([[a["teeth"], b["teeth"]] for a, b, _ in placed] == tp["ordre_couples"], f"{key} : ordre")
        left = [(a, b, k) for a, b, k in spec["stages"]]
        for a, b, _ in placed:
            hit = next((s for s in left if (s[0], s[1]) == (a["teeth"], b["teeth"])), None)
            if ctx.expect(hit is not None, f"{key} : couple {a['teeth']}:{b['teeth']} absent de trains.json"):
                left.remove(hit)
        f = [bus] if tp.get("hub") else []
        if rep:
            (w0, w2), fou = rep["reprise"], rep["reprise_fou"][0]
            f.append(f"(-{w0['teeth']} / {fou['teeth']}) * (-{fou['teeth']} / {w2['teeth']})")
            ctx.expect((w0["teeth"], w2["teeth"]) == (r_a, r_b), f"{key} : reprise ≠ {r_a} → fou → {r_b}")
            L.theorem(f"reprise_{key}", f"Reprise de Y dans la tour de `{key}` : {w0['teeth']} → pignon fou "
                      f"{fou['teeth']} → {w2['teeth']}, rapport 1 et sens {r_sens:+d} (deux engrènements extérieurs).",
                      f": (-({w0['teeth']} : ℚ) / {fou['teeth']}) * (-{fou['teeth']} / {w2['teeth']}) = {r_sens}",
                      ["norm_num"])
        for a, b, fo in placed:
            ctx.expect(a["mesh_kind"] == "external" == b["mesh_kind"], f"{key} : engrènement non extérieur")
            f.append(f"(-{a['teeth']} / {b['teeth']})" if fo is None else
                     f"(-{a['teeth']} / {fo['teeth']}) * (-{fo['teeth']} / {b['teeth']})")
        f += [f"({'-' if k == 'external' else ''}{a} / {b})" for a, b, k in left]
        N, D = [a for a, _, _ in spec["stages"]], [b for _, b, _ in spec["stages"]]
        px, ps = int(spec["phys"]), int(ctx.S[spec["src"]]["phys"])
        lhs = f"({' * '.join(f)} : ℚ)"
        order = " · ".join(f"{a['teeth']}:{b['teeth']}" + (f" (fou {fo['teeth']})" if fo else "") for a, b, fo in placed)
        L.theorem(f"place_{key}", f"Train `{key}` placé ({tp.get('mode', 'direct')}"
                  f"{', bus ' + tp['hub'] + ' supposé de même sens' if tp.get('hub') else ''}"
                  f"{', reprise' if rep else ''}) : couples dans "
                  f"l'ordre réel {order}{' + ' + ', '.join(f'{a}:{b} hors items' for a, b, _ in left) if left else ''}"
                  f" ; même produit que trains.json ({' · '.join(f'{a}:{b}' for a, b, _ in spec['stages'])}) et sens "
                  f"phys {px:+d} depuis `{spec['src']}` (phys {ps:+d}).",
                  f":\n    {lhs} =\n    ({px}) * ({ps}) * ({prod(N)} / {prod(D) if len(D) == 1 else '(' + prod(D) + ')'})",
                  ["norm_num"])
    l_a, l_b, l_sens = sens_entry(ctx, "entrées du bloc Lune")
    for sh in ("moon_L", "moon_node", "moon_perigee"):
        w1, fo, w2 = (by_id[f"lune_entree_{sh}#{s}"] for s in ("w1", "fou", "w2"))
        m = 2 * fr(dec(w1["r"])) / (l_a + 2)
        zf = 2 * fr(dec(fo["r"])) / m - 2
        ctx.expect(zf.denominator == 1 and 2 * fr(dec(w2["r"])) / m - 2 == l_b, f"entrée {sh} : dents")
        c1, _ = centre(ctx, m, l_a, int(zf), w1["c"], fo["c"], f"{sh} w1~fou")
        c2, _ = centre(ctx, m, int(zf), l_b, fo["c"], w2["c"], f"{sh} fou~w2")
        L.theorem(f"moon_input_{sh}", f"Entrée de `{sh}` dans le bloc Lune : {l_a} → pignon fou {zf} → {l_b} "
                  f"(module {m}), rapport 1, sens {l_sens:+d}, aux entraxes théoriques.",
                  f":\n    (-({l_a} : ℚ) / {zf}) * (-{zf} / {l_b}) = {l_sens} ∧\n    {c1} ∧\n    {c2}",
                  ["refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> norm_num"])
    pr = ctx.S["precession_ring"]
    (a1, b1, k1), (a2, b2, k2) = pr["stages"]
    ctx.expect([(w["teeth"], v["teeth"]) for w, v, _ in stages_of(items, "prec")[0]] == [(a1, b1)], "couple prec")
    L.theorem("precession_ratio", f"Précession : couple {a1}:{b1} ({k1}, placé sous P4) puis {a2}:{b2} ({k2}, bloc "
              f"du temps) : {a1}/{b1} · {a2}/{b2} = {abs(F(pr['ratio']))}.",
              f": ({a1} / {b1} : ℚ) * ({a2} / {b2}) = {lit(abs(F(pr['ratio'])))}", ["norm_num"])
    for t, mods in A["modules_changes"].items():
        for i, mm in enumerate(mods):
            if fr(mm) == F(1, 2):
                continue
            a, b, _ = ctx.S[t]["stages"][i]
            w = next(((x, y) for x, y, _ in stages_of(items, ALIAS.get(t, t))[0]
                      if (x["teeth"], y["teeth"]) == (a, b)), None)
            if not ctx.expect(w is not None and fr(dec(w[0]["m"])) == fr(mm), f"module changé {t} {i}"):
                continue
            c, val = centre(ctx, fr(mm), a, b, w[0]["c"], w[1]["c"], f"module {t}")
            L.theorem(f"module_{t}_{i}", f"Module changé de `{t}`, couple {a}:{b} : m = {mm} mm, entraxe "
                      f"{tidy(val)} mm, tenu par les centres placés.",
                      f":\n    {plit(fr(mm))} * ({a} + {b}) / 2 = ({tidy(val)} : ℚ) ∧\n    {c}",
                      ["refine ⟨?_, ?_, ?_⟩ <;> norm_num"])
    seen, idx = set(), {x["id"]: i for i, x in enumerate(items)}
    for it in items:
        if not it.get("teeth"):
            continue
        for p in it["partners"]:
            key = tuple(sorted((it["id"], p), key=idx.__getitem__))
            if key in seen:
                continue
            seen.add(key)
            u, v = by_id[key[0]], by_id[key[1]]
            c, val = centre(ctx, fr(dec(u["m"])), u["teeth"], v["teeth"], u["c"], v["c"], f"{u['id']}~{v['id']}")
            t0, t1 = u["id"].split("#")[0], v["id"].split("#")
            nm = f"entraxe_{ident(u['id'])}_{ident(t1[1]) if t1[0] == t0 else ident(v['id'])}"
            L.theorem(nm, f"{u['id']} ({u['teeth']} dents) ~ {v['id']} ({v['teeth']} dents), module {u['m']} : "
                      f"même module et entraxe {tidy(val)} mm à {lit(TOL)} mm près.",
                      f":\n    ({dec(u['m'])} : ℚ) = {dec(v['m'])} ∧\n    {c}", ["refine ⟨?_, ?_, ?_⟩ <;> norm_num"])
    return L.text()
