"""Kinematics.lean : les 70 arbres, une loi de transmission moyenne par arbre, la table des vitesses déclarées.

Chaque loi vient de `shafts[]` de trains.json (dents des `stages`, `sign`, `terms`, pas à pas) ; la table `rate`
vient de `rate_turns_per_day` (valeurs déclarées). Lean vérifie que les deux concordent (`determined`,
`consistent`) : un nombre de dents faux dans `stages` fait échouer la compilation.
"""
from fractions import Fraction as F

from .common import LeanFile, doc, lit, plit, qlit, prod, omega, linear

KIND_FR = {"external": "ext", "internal": "int", "chain": "chaîne", "bevel": "conique"}


def stages_fr(sh):
    st = " · ".join(f"{a}:{b} ({KIND_FR.get(k, k)})" for a, b, k in sh["stages"])
    return st + (f", pignon fou de {sh['idler']}" if sh.get("idler") else "")


def build_fields(ctx):
    """{arbre: dict(eq=énoncé Lean, zero={arbre: coeff} pour « gauche − droite », doc=…)} ; J est l'entrée."""
    fields = {}
    for x in ctx.order:
        sh = ctx.S[x]
        k, name = sh["kind"], sh["name_fr"].rstrip(".")
        if k == "input":
            ctx.expect(x == "J" and ctx.rate[x] == 1, "l'entrée doit être J à 1 tour par jour")
            continue
        if k == "train":
            N = [a for a, _, _ in sh["stages"]]
            D = [b for _, b, _ in sh["stages"]]
            s = int(sh["sign"])
            nd, dd = F(1), F(1)
            for v in N:
                nd *= v
            for v in D:
                dd *= v
            rhs = prod(N) if s > 0 else (f"-({prod(N)})" if len(N) > 1 else f"-{N[0]}")
            eq = f"{prod(D)} * {omega(x)} = {rhs} * {omega(sh['src'])}"
            zero = {x: dd, sh["src"]: -s * nd}
            text = (f"`{x}` : {name}. Train {stages_fr(sh)} depuis `{sh['src']}`, signe {s:+d} : "
                    f"Π menées · ω {x} = signe · Π menantes · ω {sh['src']}.")
        elif k in ("diff", "unit"):
            terms = [(F(t["coeff"]), t["shaft"]) for t in sh["terms"]]
            eq = f"{omega(x)} = {linear(terms)}"
            zero = {x: F(1)}
            for c, t in terms:
                zero[t] = zero.get(t, F(0)) - c
            what = ("Différentiel" if k == "diff" else
                    f"Unité non linéaire ({sh.get('device', '')}) : un tour de sortie par tour d'entrée, donc "
                    "égalité des vitesses MOYENNES")
            text = f"`{x}` : {name}. {what}."
        elif k == "stepper":
            spt, msd = int(sh["steps_per_turn"]), F(sh["mean_steps_per_day"])
            ctx.expect(sh.get("src") in ("J", None), f"pas à pas {x} : source {sh.get('src')}")
            raw = str(sh["mean_steps_per_day"]).replace("/", " / ")   # tel qu'écrit dans le JSON
            ctx.expect(F(raw.replace(" ", "")) == msd, f"{x} : pas moyens")
            eq = f"{spt} * {omega(x)} = {raw} * {omega('J')}"
            zero = {x: F(spt), "J": -msd}
            text = (f"`{x}` : {name}. Pas à pas : {spt} pas par tour, {raw} pas par jour en moyenne "
                    "(jour = tour de J).")
        else:
            raise SystemExit(f"genre d'arbre inconnu : {k} ({x})")
        fields[x] = dict(eq=eq, zero={b: c for b, c in zero.items() if c != 0}, doc=text)
    return fields


def topo(ctx, fields):
    """Ordre de résolution depuis J ; contrôle que chaque vitesse déclarée suit de ses sources."""
    known, steps, pending = {"J"}, [], [x for x in ctx.order if x in fields]
    while pending:
        for x in pending:
            deps = [b for b in fields[x]["zero"] if b != x]
            if all(b in known for b in deps):
                z = fields[x]["zero"]
                val = -sum(c * ctx.rate[b] for b, c in z.items() if b != x) / z[x]
                ctx.expect(val == ctx.rate[x], f"vitesse de {x} : déclarée {ctx.rate[x]}, les dents donnent {val}")
                known.add(x)
                steps.append(x)
                pending.remove(x)
                break
        else:
            raise SystemExit(f"dépendances circulaires ou manquantes : {pending}")
    return steps


def generate(ctx):
    fields = build_fields(ctx)
    steps = topo(ctx, fields)
    ctx.fields = fields
    L = LeanFile(ctx, ["Mathlib"], "Anticythère 2.0 : cinématique moyenne des 70 arbres", [
        "`ω x` est la vitesse MOYENNE de l'arbre `x`, en tours par jour, signée dans le sens astronomique direct",
        "(`conventions.sign` de trains.json : + = longitudes croissantes) ; `J` est l'arbre-jour (entrée, 1 tour par",
        "jour solaire moyen). `Kinematics ω` réunit une loi par arbre, écrite depuis `shafts[]` : train (produit des",
        "dents), différentiel (combinaison exacte), unité non linéaire (un tour par tour : vitesses moyennes égales),",
        "pas à pas (croix de Malte). `rate` est la table des vitesses DÉCLARÉES (`rate_turns_per_day`).",
        "",
        "Résultats : `determined` (toute vitesse admissible vaut ω J · rate : la table déclarée découle des dents),",
        "`consistent` (la table vérifie toutes les lois, pour toute vitesse de J), `moves` (la machine peut tourner) et",
        "`one_dof` (les vitesses admissibles forment exactement une droite : un seul degré de liberté).",
        "Les sens physiques (`phys`) et la géométrie sont traités dans `Ratios` et `Architecture`."])
    L.raw("/-- Les 70 arbres de `trains.json` (`shafts[]`), dans l'ordre du fichier. -/", "inductive Shaft where")
    for x in ctx.order:
        L.raw(f"  | {x} -- {ctx.S[x]['kind']} : {doc(ctx.S[x]['name_fr'])}")
    L.raw("  deriving DecidableEq, Repr", "")
    L.raw("/-- Les lois de transmission moyennes, une par arbre (sauf l'entrée `J`). -/",
          "structure Kinematics (ω : Shaft → ℚ) : Prop where")
    for x in ctx.order:
        if x in fields:
            L.raw(f"  /-- {doc(fields[x]['doc'])} -/", f"  {x} : {fields[x]['eq']}")
    L.raw("", "/-- Vitesses déclarées par trains.json (`rate_turns_per_day`), en tours par jour, pour J = 1. -/",
          "def rate : Shaft → ℚ")
    for x in ctx.order:
        L.raw(f"  | .{x} => {lit(ctx.rate[x])}")
    L.raw("")
    L.theorem("consistent", "**Cohérence** : pour toute vitesse `t` de J, les vitesses `t · rate` vérifient les "
              f"{len(fields)} lois (aucune boucle surcontrainte).",
              "(t : ℚ) : Kinematics (fun x => t * rate x)", ["constructor <;> simp only [rate] <;> ring"])
    proof = ["have h_J : ω .J = ω .J * 1 := by ring"]
    for u in steps:
        z = fields[u]["zero"]
        au = z[u]
        parts = [f"h.{u}" if au == 1 else f"{qlit(1 / au)} * h.{u}"]
        parts += [f"{qlit(-c / au)} * h_{b}" for b, c in z.items() if b != u]
        proof += [f"have h_{u} : {omega(u)} = ω .J * {plit(ctx.rate[u])} := by",
                  f"  linear_combination {' + '.join(parts)}"]
    proof += ["intro x", "cases x"] + [f"· exact h_{x}" for x in ctx.order]
    L.theorem("determined", "**Détermination** : toute famille de vitesses qui vérifie les lois vaut ω J · rate ; "
              "la table déclarée découle donc des seuls nombres de dents et coefficients.",
              "(ω : Shaft → ℚ) (h : Kinematics ω) : ∀ x, ω x = ω .J * rate x", proof)
    L.theorem("moves", "**La machine peut tourner** : il existe des vitesses admissibles avec J à 1 tour par jour ; "
              "les hypothèses des autres théorèmes ne sont pas contradictoires.",
              ": ∃ ω : Shaft → ℚ, Kinematics ω ∧ ω .J = 1",
              ["exact ⟨fun x => 1 * rate x, consistent 1, by simp [rate]⟩"])
    L.theorem("one_dof", "**Un seul degré de liberté** : l'ensemble des vitesses admissibles est exactement la "
              "droite {t · rate} (une droite et non un point, puisque rate J = 1).",
              ": {ω : Shaft → ℚ | Kinematics ω} = Set.range (fun t : ℚ => fun x => t * rate x)",
              ["ext ω", "constructor", "· intro h", "  exact ⟨ω .J, funext fun x => (determined ω h x).symm⟩",
               "· rintro ⟨t, rfl⟩", "  exact consistent t"])
    return L.text()
