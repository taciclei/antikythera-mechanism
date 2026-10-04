"""Ratios.lean : les 36 candidats `ratio` (produit des couples = rapport exact) et le sens physique des trains."""
import re
from fractions import Fraction as F

from .common import LeanFile, NS, lit, plit, prod, omega, lc_proof

RATIO_RE = re.compile(r"^ω (\w+) = \((-?)([\d·]+) / ([\d·]+)\) · ω (\w+)$")
SIGNED = {"external": -1, "internal": 1, "chain": 1}


def coef(neg, N, D):
    """Rapport signé écrit avec les dents : « 31 * 19 * 10 / (180 * 144 * 83) », « -(12 * 21) / (43 * 109) »."""
    num = prod(N) if not neg else (f"-({prod(N)})" if len(N) > 1 else f"-{N[0]}")
    den = prod(D) if len(D) == 1 else f"({prod(D)})"
    return f"{num} / {den}"


def generate(ctx):
    L = LeanFile(ctx, [f"{NS}.Kinematics"], "Rapports exacts des trains d'engrenages", [
        "Pour chaque train de trains.json (candidats `ratio`) : la vitesse de sortie vaut le produit des menantes",
        "sur le produit des menées (avec le signe du train) fois la vitesse de la source, ce produit vaut le rapport",
        "exact réduit (`ratio`), et la vitesse rapportée à l'arbre-jour J vaut `rate_vs_J`. Les théorèmes",
        "`sens_*` vérifient le sens physique (`phys`, + = horaire vu de face) : le rapport de Willis signé",
        "(engrènement extérieur −a/b, intérieur ou chaîne +a/b, pignon fou −1) vaut phys(sortie) · phys(source) ·",
        "|rapport|."])
    n = 0
    for c in ctx.T["lean_candidates"]:
        if c["kind"] != "ratio":
            continue
        m = RATIO_RE.match(c["statement"])
        if not m:
            raise SystemExit(f"énoncé ratio illisible : {c['statement']!r}")
        x, neg, N, D, src = m.group(1), m.group(2) == "-", m.group(3).split("·"), m.group(4).split("·"), m.group(5)
        N, D = [int(v) for v in N], [int(v) for v in D]
        sh = ctx.S[x]
        ctx.expect(x == c["shaft"] and sh["kind"] == "train", f"candidat ratio {x}")
        ctx.expect(src == sh["src"], f"{x} : source {src} ≠ {sh['src']}")
        ctx.expect([a for a, _, _ in sh["stages"]] == N and [b for _, b, _ in sh["stages"]] == D,
                   f"{x} : dents de l'énoncé ≠ stages")
        ctx.expect((-1 if neg else 1) == int(sh["sign"]), f"{x} : signe")
        r, ratio = F(c["rate_vs_J"]), F(sh["ratio"])
        k = coef(neg, N, D)
        stmt = (f"(ω : Shaft → ℚ) (h : Kinematics ω) :\n"
                f"    {omega(x)} = ({k}) * {omega(src)} ∧ {omega(x)} = {plit(r)} * ω .J ∧\n"
                f"    ({k} : ℚ) = {lit(ratio)}")
        L.theorem(f"ratio_{x}",
                  f"`{x}` ({sh['name_fr'].rstrip('.')}) : {c['statement']} ; rapport exact {ratio}, soit "
                  f"{r} tour par tour de J.", stmt,
                  lc_proof(ctx, [([(1, x)], [(ratio, src)]), ([(1, x)], [(r, "J")]), None]))
        n += 1
    ctx.expect(n == 36, f"{n} candidats ratio au lieu de 36")
    for x in ctx.order:
        sh = ctx.S[x]
        if sh["kind"] != "train" or sh.get("phys") is None or ctx.S[sh["src"]].get("phys") is None:
            continue
        if any(k not in SIGNED for _, _, k in sh["stages"]):
            continue
        factors = [f"({'-' if SIGNED[k] < 0 else ''}{a} / {b}{' : ℚ' if i == 0 else ''})"
                   for i, (a, b, k) in enumerate(sh["stages"])]
        if sh.get("idler"):
            factors.append("(-1)")
        px, ps = int(sh["phys"]), int(ctx.S[sh["src"]]["phys"])
        n_ext = sum(1 for _, _, k in sh["stages"] if k == "external") + (1 if sh.get("idler") else 0)
        ctx.expect(n_ext == sh.get("n_reversals", n_ext), f"{x} : n_reversals")
        stmt = f":\n    {' * '.join(factors)} = ({px}) * ({ps}) * {plit(abs(F(sh['ratio'])))}"
        L.theorem(f"sens_{x}",
                  f"Sens physique de `{x}` : {n_ext} inversion(s) (engrènements extérieurs"
                  f"{', pignon fou' if sh.get('idler') else ''}) depuis `{sh['src']}` (phys {ps:+d}) donnent "
                  f"phys {px:+d}, avec |rapport| = {abs(F(sh['ratio']))}.", stmt, ["norm_num"])
    return L.text()
