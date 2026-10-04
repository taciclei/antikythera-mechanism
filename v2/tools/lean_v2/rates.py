"""Rates.lean : les 20 candidats `mean_rate` et les 26 candidats `bound` (dérive en degrés par siècle, en ℚ)."""
import re
from fractions import Fraction as F

from .common import LeanFile, NS, fr, lit, plit, omega, linear, parse_terms, parse_free, rw_proof, lc_proof

MEAN_RE = re.compile(r"^ω (\w+) = (.+)$")
BOUND_RE = re.compile(r"^\|(.+) − cible\| · 360 · 36525 < ([0-9.e+-]+)\s+\(cible = (-?\d+/\d+) tr/j")


def ceil2(q: F) -> F:
    """Majorant exact de q ≥ 0 à deux chiffres significatifs (1.04e-08 → 11/10⁹ ; 0 → 0)."""
    if q <= 0:
        return F(0)
    e = 0
    while q >= F(10) ** (e + 1):
        e += 1
    while q < F(10) ** e:
        e -= 1
    s = F(10) ** (1 - e)                      # q · s ∈ [10, 100)
    n = -(-(q * s).numerator // (q * s).denominator)
    return F(n) / s


def sci(q: F) -> str:
    """Écriture courte d'un majorant décimal pour les docstrings : 11/10⁹ → « 1.1e-08 »."""
    return f"{float(q):.2g}"


def generate(ctx):
    L = LeanFile(ctx, [f"{NS}.Kinematics"], "Vitesses moyennes et précision", [
        "`mean_*` : les unités non linéaires (Kepler, modules vectoriels, cascade lunaire, joint de Hooke…) font un",
        "tour de sortie par tour d'entrée ; leur vitesse MOYENNE est donc la combinaison exacte de leurs entrées, et",
        "vaut `rate_vs_J` tours par tour de J.",
        "",
        "`bound_*` : pour J = 1 tour par jour, l'écart entre la vitesse de la machine et la cible (décimale exacte de",
        "constants.json, éphémérides JPL 2000–2100) multiplié par 360 · 36525 (degrés par siècle julien) est sous la",
        "borne du candidat (énoncé exact de trains.json) ; l'erreur relative |machine − cible| / |cible| est en outre",
        "majorée (CONTRACT.md § 6), par un majorant à deux chiffres significatifs. Les cibles sont indépendantes des",
        "dents : un nombre de dents faux (même avec des vitesses déclarées recalculées) fait échouer ces théorèmes."])
    n_mean = n_bound = 0
    for c in ctx.T["lean_candidates"]:
        if c["kind"] == "mean_rate":
            m = MEAN_RE.match(c["statement"])
            x, terms = m.group(1), parse_terms(m.group(2))
            sh = ctx.S[x]
            ctx.expect(sh["kind"] == "unit" and terms == [(F(t["coeff"]), t["shaft"]) for t in sh["terms"]],
                       f"mean_rate {x} : termes")
            r = F(c["rate_vs_J"])
            ctx.expect(r == ctx.rate[x], f"mean_rate {x} : rate_vs_J {r} ≠ {ctx.rate[x]}")
            stmt = (f"(ω : Shaft → ℚ) (h : Kinematics ω) :\n"
                    f"    {omega(x)} = {linear(terms)} ∧ {omega(x)} = {plit(r)} * ω .J")
            L.theorem(f"mean_{x}", f"`{x}` ({sh['name_fr'].rstrip('.')}) : {c['statement']} en moyenne "
                      f"({sh.get('device', 'unité')}) ; {r} tour par tour de J.", stmt,
                      lc_proof(ctx, [([(1, x)], terms), ([(1, x)], [(r, "J")])]))
            n_mean += 1
        elif c["kind"] == "bound":
            m = BOUND_RE.match(c["statement"])
            if not m:
                raise SystemExit(f"énoncé bound illisible : {c['statement']!r}")
            key, terms, lim, target = c["shaft"], parse_free(m.group(1)), fr(m.group(2)), fr(m.group(3))
            tkey = ctx.S[key].get("target", key) if key in ctx.S else key
            if tkey in ctx.T["targets"]:
                ctx.expect(fr(ctx.T["targets"][tkey]["turns_per_day"]) == target, f"bound {key} : cible")
            val = sum(cf * ctx.rate[s] for cf, s in terms) - target
            deg = abs(val) * 360 * 36525
            ctx.expect(deg < lim, f"bound {key} : {float(deg)} °/siècle ≥ {lim}")
            ctx.expect(target != 0, f"bound {key} : cible nulle")
            # Erreur relative (CONTRACT § 6) : |machine − cible| ≤ r · |cible|, r majorant à 2 chiffres de |val/cible|.
            r = ceil2(abs(val / target)) if target else F(0)
            ctx.expect(abs(val) <= r * abs(target), f"bound {key} : erreur relative")
            lhs = f"|{linear(terms)} - {plit(target)}|"
            stmt = (f"(ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :\n"
                    f"    {lhs} * 360 * 36525 < {lit(lim)} ∧\n"
                    f"    {lhs} ≤ {plit(r)} * {plit(abs(target))}")
            name = ctx.T["targets"].get(tkey, {}).get("name_fr", key)
            rel = float(val / target) if target else 0.0
            L.theorem(f"bound_{key}",
                      f"Précision de `{key}` ({name}) : dérive {float(deg):.3g}°/siècle < {lim} et erreur relative "
                      f"|machine − cible| / |cible| ≤ {sci(r)} (valeur {rel:.3g}) ; cible {target} tr/j.", stmt,
                      rw_proof([s for _, s in terms],
                               ["refine ⟨?_, ?_⟩ <;> "
                                f"norm_num [rate, {'abs_of_neg' if val < 0 else 'abs_of_nonneg'}]"],
                               extra_rw=["hJ"]))
            n_bound += 1
    ctx.expect((n_mean, n_bound) == (20, 26), f"{n_mean} mean_rate et {n_bound} bound au lieu de 20 et 26")
    return L.text()
