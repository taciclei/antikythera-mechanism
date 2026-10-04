"""Fichiers Lean écrits à la main : lecture, contrôles, liste des théorèmes, copie dans le paquet de sortie.

`v2/lean/AnticythereV2/Mechanisms.lean` (identités exactes des mécanismes non linéaires : module vectoriel, ellipse
à deux bras, résolveur de Kepler, équant, Oldham, Hooke) est écrit à la main, comme `lean/Antikythera/PinSlot.lean`
en v1. Le générateur ne le réécrit jamais : il le lit dans v2/lean (source unique), refuse les échappatoires (sorry,
admit, native_decide, axiom, private, set_option…), exige une docstring par théorème, en dresse la liste pour
`Audit.lean` (qui vérifie chacun par son nom et relève le seuil) et l'importe dans la racine. Quand `--out` désigne
un autre paquet (test de mutation), le fichier y est recopié tel quel.
"""
import re
from pathlib import Path

from .common import NS

# Modules écrits à la main, dans l'ordre d'import (après les modules générés, avant Audit).
MODULES = ["Mechanisms"]
SRC = Path(__file__).resolve().parents[2] / "lean" / NS        # v2/lean/AnticythereV2

# Échappatoires refusées (cherchées hors commentaires) : preuve inachevée, axiome, évaluation native, nom privé
# (un nom privé échapperait au préfixe `AnticythereV2` de l'audit), options (warningAsError…), code non sûr.
FORBIDDEN = {
    "sorry": r"\bsorry\b",
    "admit": r"\badmit\b",
    "native_decide": r"\bnative_decide\b",
    "decide +native": r"\+native\b",
    "axiom": r"\baxiom\b",
    "private": r"\bprivate\b",
    "set_option": r"\bset_option\b",
    "unsafe": r"\bunsafe\b",
    "implemented_by": r"\bimplemented_by\b",
    "extern": r"\bextern\b",
    "opaque": r"\bopaque\b",
    "run_cmd/elab": r"\b(?:run_cmd|run_tac|run_meta|elab|macro|syntax|macro_rules|elab_rules)\b",
}
DECL = re.compile(r"^[ \t]*(?:@\[[^\]]*\]\s*)*(?:protected\s+)?(?:theorem|lemma)\s+([^\s:({\[⦃]+)", re.M)
DOC_DECL = re.compile(r"/--(?:(?!-/).)*?-/\s*(?:@\[[^\]]*\]\s*)*(?:protected\s+)?(?:theorem|lemma)\s+"
                      r"([^\s:({\[⦃]+)", re.S)


def strip_comments(text: str) -> str:
    """Remplace commentaires (`--`, `/- -/` imbriqués, docstrings) par des espaces, en gardant les sauts de ligne."""
    out, i, depth, n = [], 0, 0, len(text)
    while i < n:
        two = text[i:i + 2]
        if two == "/-":
            depth += 1
            out.append("  ")
            i += 2
        elif depth and two == "-/":
            depth -= 1
            out.append("  ")
            i += 2
        elif depth:
            out.append("\n" if text[i] == "\n" else " ")
            i += 1
        elif two == "--":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        else:
            out.append(text[i])
            i += 1
    if depth:
        raise SystemExit("commentaire non fermé")
    return "".join(out)


class HandFile:
    """Un module écrit à la main : chemin, texte, noms complets de ses théorèmes (tous documentés)."""

    def __init__(self, module: str, src_dir: Path = SRC):
        self.module = module
        self.path = src_dir / f"{module}.lean"
        if not self.path.exists():
            raise SystemExit(f"fichier écrit à la main introuvable : {self.path}")
        self.text = self.path.read_text(encoding="utf-8")
        code = strip_comments(self.text)
        where = f"{NS}/{module}.lean"
        for what, pat in FORBIDDEN.items():
            m = re.search(pat, code, re.M)
            if m:
                line = code.count("\n", 0, m.start()) + 1
                raise SystemExit(f"{where}:{line} : « {what} » interdit dans un fichier audité")
        ns = f"{NS}.{module}"
        spaces = re.findall(r"^\s*namespace\s+(\S+)", code, re.M)
        if spaces != [ns] or not re.search(rf"^end {re.escape(ns)}\s*\Z", code, re.M):
            raise SystemExit(f"{where} : un seul `namespace {ns}`, fermé par `end {ns}` en fin de fichier")
        names = DECL.findall(code)
        documented = DOC_DECL.findall(self.text)
        if len(set(names)) != len(names):
            raise SystemExit(f"{where} : théorème en double")
        if sorted(names) != sorted(documented):
            missing = sorted(set(names) - set(documented))
            raise SystemExit(f"{where} : théorèmes sans docstring (l'audit ne les compterait pas) : {missing}")
        if not names:
            raise SystemExit(f"{where} : aucun théorème")
        self.names = [f"{ns}.{x}" for x in names]

    def copy_to(self, out_dir: Path):
        """Recopie le fichier dans le paquet `out_dir` s'il n'est pas déjà la source (test de mutation)."""
        dest = out_dir / NS / f"{self.module}.lean"
        if dest.resolve() != self.path.resolve():
            dest.write_text(self.text, encoding="utf-8")


def load(src_dir: Path = SRC):
    return [HandFile(m, src_dir) for m in MODULES]
