"""Outils communs du générateur Lean v2 : littéraux exacts, rendu des formes linéaires, fichiers Lean, contexte.

Tout est en Python pur (bibliothèque standard) pour tourner tel quel dans la CI (`python3`).
"""
import json
import re
from fractions import Fraction as F
from pathlib import Path

HEADER = ("-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.\n"
          "-- Ne pas éditer à la main : relancer le générateur.\n")
NS = "AnticythereV2"
LEAN_KEYWORDS = {"at", "by", "do", "end", "fun", "have", "if", "in", "let", "match", "show", "then", "else",
                 "where", "with", "from", "open", "namespace", "section", "theorem", "def", "structure", "λ"}


def fr(s) -> F:
    """Fraction exacte depuis « 589/215136 », « 1e-06 », « 0.001 » ou un entier."""
    if isinstance(s, F):
        return s
    if isinstance(s, int):
        return F(s)
    return F(str(s).strip())


def lit(q) -> str:
    """Littéral Lean d'une fraction : « 7 », « -5 », « 589 / 215136 », « -4123 / 28009512 »."""
    q = fr(q)
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator} / {q.denominator}"


def plit(q) -> str:
    """Littéral parenthésé (pour servir de facteur)."""
    s = lit(q)
    return s if re.fullmatch(r"\d+", s) else f"({s})"


def qlit(q) -> str:
    """Littéral typé dans ℚ, p. ex. « (589 / 215136 : ℚ) »."""
    return f"({lit(q)} : ℚ)"


def prod(ints) -> str:
    """Produit de nombres de dents, p. ex. « 31 * 19 * 10 »."""
    return " * ".join(str(int(v)) for v in ints)


def dec(x: float) -> str:
    """Littéral décimal exact d'une coordonnée (telle qu'écrite dans le JSON), p. ex. « -125.618 »."""
    s = repr(float(x))
    if "e" in s or "E" in s:
        raise ValueError(f"coordonnée en notation exponentielle : {x}")
    return s


def omega(sh: str) -> str:
    return f"ω .{sh}"


def linear(terms) -> str:
    """Rendu de Σ c·ω s : terms = [(Fraction, arbre), ...] → « ω .a - 3 * ω .b + 1 / 61 * ω .c »."""
    out = []
    for c, sh in terms:
        c = fr(c)
        mag, neg = abs(c), c < 0
        body = omega(sh) if mag == 1 else f"{lit(mag)} * {omega(sh)}"
        if not out:
            out.append(f"-{body}" if neg and mag == 1 else (f"-({lit(mag)}) * {omega(sh)}" if neg else body))
        else:
            out.append(f"{'-' if neg else '+'} {body}")
    return " ".join(out) if out else "0"


def ident(s: str) -> str:
    """Identifiant Lean sûr à partir d'un id du JSON (« venus_L#w3 » → « venus_L_w3 »)."""
    v = re.sub(r"[^A-Za-z0-9_]", "_", s)
    if not re.match(r"[A-Za-z_]", v) or v in LEAN_KEYWORDS:
        raise ValueError(f"identifiant Lean impossible : {s!r}")
    return v


def doc(s: str) -> str:
    """Texte de docstring sans fermeture accidentelle de commentaire."""
    return s.replace("-/", "- /").replace("/-", "/ -").strip()


class LeanFile:
    """Un fichier Lean généré : en-tête, imports, docstring de module, espace de noms, théorèmes comptés."""

    def __init__(self, ctx, imports, title, intro_lines):
        self.ctx = ctx
        self.lines = [HEADER] + [f"import {m}" for m in imports] + [""]
        self.lines += ["/-!", f"# {title}", ""] + [doc(x) if x else "" for x in intro_lines] + ["-/", ""]
        self.lines += [f"namespace {NS}", ""]
        self.count = 0

    def raw(self, *lines):
        self.lines += list(lines)

    def theorem(self, name, docstring, signature, proof_lines):
        """`signature` : « (ω : Shaft → ℚ) (h : Kinematics ω) :\n    énoncé » ; `proof_lines` sans indentation."""
        if name in self.ctx.names:
            raise ValueError(f"théorème en double : {name}")
        self.ctx.names.add(name)
        self.lines.append(f"/-- {doc(docstring)} -/")
        self.lines.append(f"theorem {name} {signature} := by")
        self.lines += [f"  {p}" for p in proof_lines]
        self.lines.append("")
        self.count += 1
        self.ctx.n_theorems += 1

    def text(self):
        return "\n".join(self.lines + [f"end {NS}", ""])


class Ctx:
    """Données des deux spécifications et état partagé de la génération."""

    def __init__(self, trains_path: Path, arch_path: Path, check: bool = True):
        self.T = json.loads(Path(trains_path).read_text(encoding="utf-8"))
        self.A = json.loads(Path(arch_path).read_text(encoding="utf-8"))
        self.check = check
        self.S = {s["id"]: s for s in self.T["shafts"]}
        self.order = [s["id"] for s in self.T["shafts"]]
        self.rate = {k: fr(s["rate_turns_per_day"]) for k, s in self.S.items()}
        self.names = set()
        self.n_theorems = 0
        self.problems = []
        for k in self.order:
            ident(k)

    def expect(self, cond, msg):
        """Contrôle de cohérence côté Python : bloquant en mode normal, simple note avec --no-check
        (le test de mutation laisse alors Lean seul juge)."""
        if not cond:
            if self.check:
                raise SystemExit(f"incohérence : {msg}")
            self.problems.append(msg)
        return bool(cond)


def rw_proof(shafts, closing, extra_rw=()):
    """Preuve type : réécrire chaque vitesse par `determined` (vitesse = ω J · rate), déplier `rate`, conclure."""
    seen = []
    for s in shafts:
        if s != "J" and s not in seen:
            seen.append(s)
    rws = [f"determined ω h .{s}" for s in seen] + list(extra_rw)
    lines = [f"rw [{', '.join(rws)}]"] if rws else []
    return lines + closing


def lc_proof(ctx, goals):
    """Preuve par combinaisons linéaires explicites.

    `goals` : liste de conjoints, chacun (gauche, droite) en formes linéaires [(c, arbre)], ou None pour un conjoint
    purement numérique (`norm_num`). On pose r_s : ω s = ω J · (vitesse déclarée) — instance de `determined`,
    acceptée par dépliage de `rate` — puis chaque conjoint est Σ (coefficient de ω s) · r_s, vérifié par `ring1`.
    """
    zs = []
    for g in goals:
        if g is None:
            zs.append(None)
            continue
        z = {}
        for sgn, side in ((1, g[0]), (-1, g[1])):
            for c, s in side:
                z[s] = z.get(s, F(0)) + sgn * fr(c)
        zs.append({s: c for s, c in z.items() if c != 0})
    need = []
    for z in zs:
        for s in (z or {}):
            if s != "J" and s not in need:
                need.append(s)
    lines = [f"have r_{s} : {omega(s)} = ω .J * {plit(ctx.rate[s])} := determined ω h .{s}" for s in need]
    tac = []
    for z in zs:
        if z is None:
            tac.append("norm_num")
            continue
        parts = [f"r_{s}" if c == 1 else f"{qlit(c)} * r_{s}" for s, c in z.items() if s != "J"]
        tac.append(f"linear_combination {' + '.join(parts)}" if parts else "ring")
    if len(tac) == 1:
        return lines + tac
    return lines + [f"refine ⟨{', '.join('?_' for _ in tac)}⟩"] + [f"· {t}" for t in tac]


TERM_RE = re.compile(r"\(([-0-9/]+)\)·ω (\w+)")
FREE_RE = re.compile(r"([+-]?)\s*(\d+(?:/\d+)?)?\s*ω\s+(\w+)")


def parse_terms(s: str):
    """« (1)·ω Y + (-1)·ω precession_ring » → [(1, 'Y'), (-1, 'precession_ring')]."""
    terms = [(fr(c), sh) for c, sh in TERM_RE.findall(s)]
    if not terms or TERM_RE.sub("", s).replace("+", "").strip():
        raise ValueError(f"forme linéaire illisible : {s!r}")
    return terms


def parse_free(s: str):
    """« ω io − 3 ω europa + 2 ω ganymede » ou « (ω moon_L − ω Y) » → [(1,'io'), (-3,'europa'), (2,'ganymede')]."""
    s = s.replace("−", "-").strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    terms = [(fr(c or 1) * (-1 if sg == "-" else 1), sh) for sg, c, sh in FREE_RE.findall(s)]
    if not terms or FREE_RE.sub("", s).strip():
        raise ValueError(f"forme linéaire illisible : {s!r}")
    return terms
