"""Identities.lean : les 14 candidats `identity` et les 2 candidats `decide` (calendrier grégorien, semaine)."""
import re
from fractions import Fraction as F

from .common import LeanFile, NS, fr, plit, omega, linear, parse_terms, parse_free, lc_proof

LIN_RE = re.compile(r"^ω (\w+) = (\(.+)$")
WEEK_RE = re.compile(r"^(\d+) = (\d+) · (\d+)$")


def identity_theorems(ctx, L):
    n = 0
    for c in ctx.T["lean_candidates"]:
        if c["kind"] != "identity":
            continue
        x, st = c["shaft"], c["statement"]
        name = f"identity_{x}"
        m = LIN_RE.match(st)
        if m and "rate_vs_J" in c:
            terms = parse_terms(m.group(2))
            sh = ctx.S[m.group(1)]
            ctx.expect(sh["kind"] == "diff" and terms == [(F(t["coeff"]), t["shaft"]) for t in sh["terms"]],
                       f"identity {x} : termes")
            r = F(c["rate_vs_J"])
            ctx.expect(r == ctx.rate[x], f"identity {x} : rate_vs_J")
            stmt = (f"(ω : Shaft → ℚ) (h : Kinematics ω) :\n"
                    f"    {omega(x)} = {linear(terms)} ∧ {omega(x)} = {plit(r)} * ω .J")
            goals = [([(1, x)], terms), ([(1, x)], [(r, "J")])]
            text = f"`{x}` ({sh['name_fr'].rstrip('.')}) : {st} ; {r} tour par tour de J."
        else:
            if st.startswith("vitesse moyenne"):
                lhs, rhs, name = [(F(1), x)], [], f"{name}_mean_zero"
            else:
                core = re.sub(r"\s*\([^()]*\)\s*$", "", st)
                left, right = core.split("=")
                lhs, rhs = parse_free(left), (parse_free(right) if right.strip() != "0" else [])
                name += "_laplace" if "Laplace" in st else "_sum"
            ctx.expect(sum(c_ * ctx.rate[s] for c_, s in lhs) == sum(c_ * ctx.rate[s] for c_, s in rhs),
                       f"identité fausse : {st}")
            stmt = f"(ω : Shaft → ℚ) (h : Kinematics ω) :\n    {linear(lhs)} = {linear(rhs)}"
            goals = [(lhs, rhs)]
            text = f"{st}."
        L.theorem(name, text, stmt, lc_proof(ctx, goals))
        n += 1
    ctx.expect(n == 14, f"{n} identités au lieu de 14")


def calendar(ctx, L, cand):
    """Cames du calendrier lues le 28 février : saute(n) ↔ ¬ bissextile(2000 + n), pour tout n."""
    gs = ctx.T["gregorian_simulation"]
    P, r = int(gs["positions"]), int(gs["reading_position"])
    ctx.expect("C4 ∨ (C100 ∧ C400)" in ctx.S["cal_cross_skip"].get("note", ""), "logique de saut")
    chain, cum, cams = [("C4", "cal_prog4"), ("C100", "cal_prog100"), ("C400", "cal_prog400")], F(1), []
    prev = "cal_sum"
    for cam, sid in chain:
        sh = ctx.S[sid]
        ctx.expect(sh["src"] == prev, f"{sid} : source {sh['src']}")
        cum *= F(sh["ratio"])
        prev = sid
        D = F(P) / cum
        lo, hi = (fr(v) for v in gs["arcs_turns"][cam])
        ctx.expect(D.denominator == 1 and (lo * D).denominator == 1 and (hi * D).denominator == 1,
                   f"came {cam} : arcs non entiers")
        D, a, b = int(D), int(lo * D), int(hi * D)
        ctx.expect((P * 400) % D == 0, f"came {cam} : période ≠ 400 ans")
        cams.append((cam, sid, D, a, b, cum))
    p = f"({P} * n + {r})"
    L.raw("/-- Année bissextile du calendrier grégorien (règle civile). -/",
          "def leap (y : ℕ) : Bool := y % 4 == 0 && (y % 100 != 0 || y % 400 == 0)", "")
    for cam, sid, D, a, b, cum in cams:
        test = (f"decide ({a} ≤ {p} % {D}) && decide ({p} % {D} ≤ {b})" if a <= b else
                f"decide ({a} ≤ {p} % {D}) || decide ({p} % {D} ≤ {b})")
        L.raw(f"/-- Came {cam} sur `{sid}` ({cum} tour par tour de l'anneau des dates) : à la lecture du 28 février "
              f"de l'année 2000 + n (anneau à n + {r}/{P} tours), elle est à {p}/{D} de tour ; levée sur "
              f"[{a}/{D}, {b}/{D}] (arc `{cam}` de `gregorian_simulation`). -/",
              f"def cam{cam} (n : ℕ) : Bool := {test}", "")
    L.raw("/-- La croix de saut avance (on saute le 29 février) si C4 ∨ (C100 ∧ C400). -/",
          "def skipFeb29 (n : ℕ) : Bool := camC4 n || (camC100 n && camC400 n)", "")
    L.theorem("calendar_400", "Les 400 années 2000…2399 : la croix de saut avance exactement les années communes.",
              ": ∀ n < 400, skipFeb29 n = !leap (2000 + n)", ["decide +kernel"])
    skips = sum(1 for n in range(400) if not ((2000 + n) % 4 == 0 and ((2000 + n) % 100 != 0 or (2000 + n) % 400 == 0)))
    leaps = 400 - skips
    msd = F(ctx.S["cal_cross_skip"]["mean_steps_per_day"])
    ctx.expect(msd == F(skips, 400 * 365 + leaps), f"pas moyens de la croix de saut {msd}")
    L.theorem("skips_400", f"En 400 ans la croix de saut fait {skips} pas pendant {400 * 365 + leaps} jours : "
              f"c'est le `mean_steps_per_day` = {msd} de `cal_cross_skip` utilisé dans `Kinematics`.",
              f": ((List.range 400).filter skipFeb29).length = {skips} ∧\n"
              f"    400 * 365 + ((List.range 400).filter (fun n => leap (2000 + n))).length = {400 * 365 + leaps}",
              ["decide +kernel"])
    spt = int(ctx.S["cal_cross_skip"]["steps_per_turn"])
    days = 400 * 365 + leaps
    L.theorem("skip_rate", f"Lien Lean entre les cames et `Kinematics` : les {skips} pas comptés sur les cames en "
              f"400 ans, divisés par les {days} jours, sont la vitesse moyenne de la croix de saut `cal_cross_skip` "
              f"dans `Kinematics` ({spt} pas par tour).",
              f"(ω : Shaft → ℚ) (h : Kinematics ω) :\n"
              f"    (((List.range 400).filter skipFeb29).length : ℚ) * ω .J =\n"
              f"    ((400 * 365 + ((List.range 400).filter (fun n => leap (2000 + n))).length : ℕ) : ℚ) *\n"
              f"      ({spt} * ω .cal_cross_skip)",
              ["rw [skips_400.1, skips_400.2]", "push_cast",
               f"linear_combination (-{days} : ℚ) * h.cal_cross_skip"])
    hs = []
    for cam, sid, D, a, b, cum in cams:
        hs.append(f"have h{cam} : ({P} * (n + 400) + {r}) % {D} = {p} % {D} := by")
        hs.append(f"  rw [show {P} * (n + 400) + {r} = {P} * n + {r} + {P * 400 // D} * {D} by ring, "
                  "Nat.add_mul_mod_self_right]")
    L.theorem("skip_periodic", "Les trois cames reviennent à la même position tous les 400 ans (366 · 400 est un "
              "multiple des trois périodes).", "(n : ℕ) : skipFeb29 (n + 400) = skipFeb29 n",
              hs + [f"simp only [skipFeb29, {', '.join('cam' + c[0] for c in cams)}, "
                    f"{', '.join('h' + c[0] for c in cams)}]"])
    hl = []
    for k, mul in ((4, 100), (100, 4), (400, 1)):
        hl += [f"have h{k} : (2000 + (n + 400)) % {k} = (2000 + n) % {k} := by",
               f"  rw [show 2000 + (n + 400) = 2000 + n + {mul} * {k} by ring, Nat.add_mul_mod_self_right]"]
    L.theorem("leap_periodic", "La règle grégorienne est périodique de 400 ans.",
              "(n : ℕ) : leap (2000 + (n + 400)) = leap (2000 + n)", hl + ["simp only [leap, h4, h100, h400]"])
    L.theorem("calendar", f"**Calendrier** ({cand['statement']}) : pour TOUT n, la machine saute le 29 février "
              "l'année 2000 + n si et seulement si elle n'est pas bissextile (400 cas par `decide`, puis "
              "périodicité de 400 ans des trois cames).",
              "(n : ℕ) : skipFeb29 n = true ↔ ¬ leap (2000 + n) = true",
              ["have key : skipFeb29 n = !leap (2000 + n) := by",
               "  induction n using Nat.strong_induction_on with",
               "  | _ n ih =>",
               "    rcases Nat.lt_or_ge n 400 with hn | hn",
               "    · exact calendar_400 n hn",
               "    · obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le' hn",
               "      rw [skip_periodic, leap_periodic]",
               "      exact ih k (Nat.lt_add_of_pos_right (by norm_num))",
               "rw [key]", "cases leap (2000 + n) <;> decide"])
    gearing(ctx, L, P, spt, cams, days)


def gearing(ctx, L, P, spt, cams, days):
    """Prémisses du modèle des cames, prouvées depuis `Kinematics` : chaque pas d'une croix avance l'anneau d'une
    de ses P positions, la came Cx fait 1/D tour par position, l'anneau fait 400 tours en 400 années grégoriennes."""
    ctx.expect(all(int(ctx.S[s]["steps_per_turn"]) == spt for s in ("cal_cross_main", "cal_cross_skip")),
               "croix : nombre de fentes")
    goals = [([(P, "cal_sum")], [(spt, "cal_cross_main"), (spt, "cal_cross_skip")])]
    conj = [f"{P} * ω .cal_sum = {spt} * ω .cal_cross_main + {spt} * ω .cal_cross_skip"]
    for cam, sid, D, a, b, cum in cams:
        goals.append(([(D, sid)], [(P, "cal_sum")]))
        conj.append(f"{D} * ω .{sid} = {P} * ω .cal_sum")
    goals.append(([(days, "cal_sum")], [(400, "J")]))
    conj.append(f"{days} * ω .cal_sum = 400 * ω .J")
    for lhs, rhs in goals:
        ctx.expect(sum(c * ctx.rate[s] for c, s in lhs) == sum(c * ctx.rate[s] for c, s in rhs),
                   f"calendrier : {lhs} ≠ {rhs}")
    L.theorem("calendar_gearing", f"Prémisses du modèle des cames, tirées des dents (`Kinematics`) : un pas de "
              f"l'une ou l'autre croix ({spt} fentes) avance l'anneau des dates d'une de ses {P} positions ; les "
              f"cames {', '.join(c[0] for c in cams)} tournent de 1/{', 1/'.join(str(c[2]) for c in cams)} de tour "
              f"par position (les modules des définitions `cam*`) ; l'anneau fait 400 tours en {days} jours.",
              "(ω : Shaft → ℚ) (h : Kinematics ω) :\n    " + " ∧\n    ".join(conj),
              lc_proof(ctx, goals))


def week(ctx, L, cand):
    m = WEEK_RE.match(cand["statement"])
    days, k, weeks = (int(v) for v in m.groups())
    ctx.expect(F(ctx.rate["W"]) == F(1, k), "la roue de la semaine doit faire 1 tour en 7 jours")
    L.theorem("week_400", f"{cand['statement']} : les {days} jours de 400 années grégoriennes font {weeks} semaines "
              "entières ; le jour de la semaine se répète donc tous les 400 ans.",
              f": ({days} : ℕ) = {k} * {weeks} ∧\n"
              f"    400 * 365 + ((List.range 400).filter (fun n => leap (2000 + n))).length = {days}",
              ["decide +kernel"])
    L.theorem("week_wheel", f"La roue de la semaine `W` fait exactement {weeks} tours en {days} jours (tours de J).",
              f"(ω : Shaft → ℚ) (h : Kinematics ω) :\n    {days} * {omega('W')} = {weeks} * ω .J",
              lc_proof(ctx, [([(days, "W")], [(weeks, "J")])]))


def generate(ctx):
    L = LeanFile(ctx, [f"{NS}.Kinematics"], "Identités exactes et calendrier", [
        "Différentiels (évection, temps sidéral, Laplace des satellites de Jupiter, anneau des dates…) : chaque",
        "identité de trains.json est vraie pour TOUTE famille de vitesses admissibles, et donne `rate_vs_J`.",
        "Calendrier : les cames C4, C100, C400 des roues-programmes, lues le 28 février, font sauter le 29 février",
        "exactement les années communes, pour toute année à partir de 2000 ; 400 années grégoriennes font un nombre",
        "entier de semaines. Les prémisses du modèle (positions de l'anneau, périodes des cames, vitesse moyenne de",
        "la croix de saut) sont prouvées depuis `Kinematics` (`calendar_gearing`, `skip_rate`)."])
    identity_theorems(ctx, L)
    dec = [c for c in ctx.T["lean_candidates"] if c["kind"] == "decide"]
    ctx.expect([c["shaft"] for c in dec] == ["calendar", "W"], "candidats decide")
    calendar(ctx, L, dec[0])
    week(ctx, L, dec[1])
    return L.text()
